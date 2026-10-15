"""Configuration (fichier YAML + surcharges `--set section.clé=valeur`)."""

from __future__ import annotations

import dataclasses
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .prompts import DEFAULT_SYSTEM_PROMPT

# Couches linéaires du modèle de langage seulement : la tour de vision et le projecteur multimodal
# de Ministral 3 (Mistral3ForConditionalGeneration) restent gelés.
DEFAULT_LORA_TARGETS = (
    r"^(?!.*(?:vision_tower|multi_modal_projector)).*\.(?:q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$"
)


@dataclass
class ModelConfig:
    # Les poids par défaut de `mistralai/Ministral-3-3B-Instruct-2512` sont en FP8 : on entraîne sur la version BF16.
    name_or_path: str = "mistralai/Ministral-3-3B-Instruct-2512-BF16"
    revision: str | None = None
    load_in_4bit: bool = False  # QLoRA (bitsandbytes NF4)
    attn_implementation: str = "sdpa"
    dtype: str = "bfloat16"


@dataclass
class LoraSettings:
    r: int = 32
    alpha: int = 64
    dropout: float = 0.05
    target_modules: str | list[str] = DEFAULT_LORA_TARGETS
    use_rslora: bool = False
    use_dora: bool = False


@dataclass
class DataConfig:
    # Jeu d'affinage du dépôt (format `messages`, déjà découpé en train / val / test).
    train_files: list[str] = field(default_factory=lambda: ["data/sft/train.jsonl"])
    eval_files: list[str] = field(default_factory=lambda: ["data/sft/val.jsonl"])
    # Jeu de test : réservé à l'évaluation finale (jamais utilisé pour choisir le checkpoint).
    test_files: list[str] = field(default_factory=lambda: ["data/sft/test.jsonl"])
    # Avec des fichiers d'évaluation dédiés : retirer de l'entraînement les paires d'un groupe présent dans
    # l'évaluation. Utile si l'évaluation est faite de dispositifs à part ; à laisser désactivé quand les groupes
    # sont des domaines larges partagés par le découpage fourni (cas de data/sft).
    drop_train_groups_in_eval: bool = False
    # Fichiers joints par `id` pour compléter les champs manquants (ex. `domaine` des fichiers regles_*.jsonl).
    metadata_files: list[str] = field(default_factory=list)
    # Renommage des champs : {"specification": "ma_colonne", "gherkin": "...", "id": "..."}.
    fields: dict[str, str] = field(default_factory=dict)
    # Champs définissant le groupe (dispositif) pour un découpage train/eval sans fuite.
    group_by: list[str] = field(default_factory=lambda: ["dispositif", "domaine", "groupe", "source"])
    eval_ratio: float = 0.1
    split_manifest: str | None = None  # manifest.json d'un run précédent pour figer le jeu d'évaluation
    require_valid_gherkin: bool = True
    min_reference_score: float = 0.0
    expected_language: str = "fr"
    max_length: int = 2048  # prompt + réponse, en tokens ; les paires plus longues sont écartées
    train_limit: int | None = None  # sous-échantillon d'entraînement (courbe d'apprentissage)
    seed: int = 42


@dataclass
class PromptConfig:
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    user_template: str | None = None


@dataclass
class TrainingConfig:
    output_dir: str = "entrainement/runs/ministral3b-gherkin-lora"
    num_train_epochs: float = 3.0
    max_steps: int = -1
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    learning_rate: float = 1.0e-4
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.05
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    optim: str = "adamw_torch_fused"
    gradient_checkpointing: bool = True
    logging_steps: int = 10
    eval_steps: int = 50
    save_total_limit: int = 3
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    early_stopping_patience: int | None = 3
    report_to: list[str] = field(default_factory=lambda: ["tensorboard"])
    seed: int = 42
    dataloader_num_workers: int = 2
    resume_from_checkpoint: str | None = None  # chemin, ou "last" pour le dernier checkpoint du run
    # Arguments supplémentaires transmis tels quels à trl.SFTConfig.
    extra_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalConfig:
    batch_size: int = 8
    max_new_tokens: int = 2048
    do_sample: bool = False
    temperature: float = 0.1
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    max_samples: int | None = None
    # Sonde qualité pendant l'entraînement : génère N exemples d'évaluation à chaque évaluation (0 = désactivée).
    probe_samples: int = 16
    probe_max_new_tokens: int = 1536
    run_after_training: bool = True


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    lora: LoraSettings = field(default_factory=LoraSettings)
    data: DataConfig = field(default_factory=DataConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _coerce(value: Any, hint: Any) -> Any:
    """Convertit les chaînes numériques : YAML lit « 2e-4 » comme une chaîne (il exige « 2.0e-4 »)."""
    if not isinstance(value, str):
        return value
    types = typing.get_args(hint) or (hint,)
    for t in (int, float):
        if t in types:
            try:
                return t(value)
            except ValueError:
                continue
    return value


def _build(cls, values: dict, path: str = ""):
    if not isinstance(values, dict):
        raise ValueError(f"Section « {path or 'racine'} » : un dictionnaire est attendu, reçu {values!r}")
    hints = typing.get_type_hints(cls)
    known = {f.name for f in dataclasses.fields(cls)}
    unknown = set(values) - known
    if unknown:
        raise ValueError(f"Clé(s) inconnue(s) dans « {path or 'racine'} » : {sorted(unknown)}. Clés valides : {sorted(known)}")
    kwargs = {}
    for name, value in values.items():
        hint = hints[name]
        if dataclasses.is_dataclass(hint):
            kwargs[name] = _build(hint, value or {}, f"{path}.{name}".lstrip("."))
        else:
            kwargs[name] = _coerce(value, hint)
    return cls(**kwargs)


def _parse_value(raw: str) -> Any:
    return yaml.safe_load(raw)


def apply_overrides(data: dict, overrides: list[str]) -> dict:
    """Applique des surcharges `section.clé=valeur` (valeur lue en YAML : 1e-4, true, [a, b]...)."""
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Surcharge invalide « {item} » : format attendu section.clé=valeur")
        key, raw = item.split("=", 1)
        parts = key.strip().split(".")
        node = data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = _parse_value(raw)
    return data


def load_config(path: str | Path | None = None, overrides: list[str] | None = None) -> Config:
    data: dict = {}
    if path:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    data = apply_overrides(data, overrides or [])
    return _build(Config, data)


def save_config(cfg: Config, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.to_dict(), f, allow_unicode=True, sort_keys=False, width=120)
