"""Préparation des données et entraînement LoRA / QLoRA avec TRL (SFTTrainer)."""

from __future__ import annotations

import importlib.util
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import torch

from .config import Config, save_config
from .data import (
    DataReport,
    Pair,
    build_manifest,
    filter_by_length,
    length_stats,
    load_dataset_splits,
    subsample,
    write_jsonl,
)
from .evaluation import evaluate_pairs, probe
from .generation import GenerationParams, chat_token_ids
from .modeling import count_parameters, load_base_model, load_tokenizer, write_run_info
from .progress import DONE, ERROR, STOPPED, ProgressWriter, make_callback
from .prompts import build_training_example

log = logging.getLogger(__name__)


def add_file_logging(path: Path) -> None:
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def to_examples(pairs: list[Pair], cfg: Config) -> list[dict]:
    """Format prompt-completion. Les paires au format `messages` gardent leur propre prompt."""
    return [
        {"prompt": p.prompt, "completion": [{"role": "assistant", "content": p.gherkin}]} if p.prompt else
        build_training_example(p.id, p.specification, p.gherkin, cfg.prompt.system_prompt, cfg.prompt.user_template)
        for p in pairs
    ]


def prompt_info(cfg: Config, report: DataReport) -> dict:
    """Prompt à réutiliser à l'inférence : celui des données s'il existe, sinon celui de la configuration."""
    return report.prompt_template or {"system_prompt": cfg.prompt.system_prompt,
                                      "user_template": cfg.prompt.user_template}


def token_lengths(examples: list[dict], tokenizer) -> list[int]:
    return [len(chat_token_ids(tokenizer, ex["prompt"] + ex["completion"])) for ex in examples]


def prepare_data(cfg: Config, tokenizer, out_dir: Path) -> tuple[list[Pair], list[Pair], DataReport]:
    """Charge, filtre et découpe les paires ; écrit train.jsonl, eval.jsonl, manifest.json et rapport.json."""
    train, evals, report = load_dataset_splits(cfg.data, apply_limit=False)
    stats = {}
    for name in ("train", "eval"):
        pairs = train if name == "train" else evals
        lengths = token_lengths(to_examples(pairs, cfg), tokenizer)
        stats[name] = length_stats(lengths)
        kept = filter_by_length(pairs, lengths, cfg.data.max_length, report)
        if name == "train":
            train = kept
        else:
            evals = kept
    # Limite appliquée après le filtre de longueur : on obtient bien le nombre de paires demandé.
    available = len(train)
    train = subsample(train, cfg.data.train_limit, cfg.data.seed)
    if cfg.data.train_limit and cfg.data.train_limit > available:
        report.warn(f"{cfg.data.train_limit} paires demandées, {available} disponibles : toutes sont utilisées.")
    data_dir = out_dir / "data"
    write_jsonl(train, data_dir / "train.jsonl")
    write_jsonl(evals, data_dir / "eval.jsonl")
    if report.test_pairs:
        write_jsonl(report.test_pairs, data_dir / "test.jsonl")
    manifest = build_manifest(train, evals, report)
    (data_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "train": len(train),
        "train_disponibles": available,
        "eval": len(evals),
        "test": len(report.test_pairs),
        "prompt": prompt_info(cfg, report),
        "longueurs_tokens": stats,
        "groupes_train": len(manifest["train_groups"]),
        "groupes_eval": manifest["eval_groups"],
        **report.to_dict(),
    }
    (data_dir / "rapport.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(
        "Données : %d paires d'entraînement, %d d'évaluation, %d de test (découpage %s) ; rejets : %s ; longueurs : %s",
        len(train), len(evals), len(report.test_pairs), report.split_method, dict(report.dropped) or "aucun", stats,
    )
    if not train:
        raise ValueError("Aucune paire d'entraînement après filtrage : voir data/rapport.json")
    return train, evals, report


def _report_to(requested: list[str]) -> list[str]:
    available = []
    for name in requested:
        module = {"tensorboard": "tensorboard", "wandb": "wandb", "mlflow": "mlflow"}.get(name, name)
        if name == "none" or importlib.util.find_spec(module) is not None:
            available.append(name)
        else:
            log.warning("Suivi « %s » demandé mais le paquet n'est pas installé : ignoré", name)
    return available or ["none"]


def build_sft_config(cfg: Config, out_dir: Path, has_eval: bool):
    from trl import SFTConfig

    t = cfg.training
    cuda = torch.cuda.is_available()
    bf16 = torch.cuda.is_bf16_supported() if cuda else cfg.model.dtype in ("bfloat16", "bf16")
    optim = t.optim
    if not cuda and any(k in optim for k in ("paged", "8bit", "bnb")):
        log.warning("Optimiseur %s indisponible sans GPU : adamw_torch", optim)
        optim = "adamw_torch"
    best_metric = t.metric_for_best_model
    kwargs = dict(
        output_dir=str(out_dir / "checkpoints"),
        num_train_epochs=t.num_train_epochs,
        max_steps=t.max_steps,
        per_device_train_batch_size=t.per_device_train_batch_size,
        per_device_eval_batch_size=t.per_device_eval_batch_size,
        gradient_accumulation_steps=t.gradient_accumulation_steps,
        learning_rate=t.learning_rate,
        lr_scheduler_type=t.lr_scheduler_type,
        warmup_steps=t.warmup_ratio,  # flottant < 1 : fraction des pas d'entraînement
        weight_decay=t.weight_decay,
        max_grad_norm=t.max_grad_norm,
        optim=optim,
        use_cpu=not cuda,  # requis par transformers pour le bf16 sur CPU
        bf16=bf16,
        fp16=cuda and not bf16,
        tf32=True if cuda and torch.cuda.get_device_capability()[0] >= 8 else None,
        gradient_checkpointing=t.gradient_checkpointing,
        logging_steps=t.logging_steps,
        eval_strategy="steps" if has_eval else "no",
        eval_steps=t.eval_steps,
        save_strategy="steps",
        save_steps=t.eval_steps,
        save_total_limit=t.save_total_limit,
        load_best_model_at_end=has_eval and t.load_best_model_at_end,
        metric_for_best_model=best_metric if has_eval else None,
        greater_is_better=("loss" not in best_metric) if has_eval else None,
        report_to=_report_to(t.report_to),
        seed=t.seed,
        data_seed=cfg.data.seed,
        dataloader_num_workers=t.dataloader_num_workers,
        # Spécifique TRL : la perte ne porte que sur la réponse (Gherkin), jamais sur le prompt.
        max_length=cfg.data.max_length,
        completion_only_loss=True,
        packing=False,
    )
    kwargs.update(t.extra_args)
    return SFTConfig(**kwargs)


def build_lora_config(cfg: Config):
    from peft import LoraConfig

    lc = cfg.lora
    return LoraConfig(
        r=lc.r,
        lora_alpha=lc.alpha,
        lora_dropout=lc.dropout,
        target_modules=lc.target_modules,
        use_rslora=lc.use_rslora,
        use_dora=lc.use_dora,
        bias="none",
        task_type="CAUSAL_LM",
    )


def make_trainer_class():
    from trl import SFTTrainer

    class GherkinSFTTrainer(SFTTrainer):
        """SFTTrainer qui ajoute, à chaque évaluation, une mesure de qualité sur des Gherkin générés."""

        def __init__(self, *args, quality_probe=None, progress: ProgressWriter | None = None, **kwargs):
            super().__init__(*args, **kwargs)
            self.quality_probe = quality_probe
            self.progress = progress

        def evaluate(self, eval_dataset=None, ignore_keys=None, metric_key_prefix="eval"):
            if self.progress:
                self.progress.phase(f"évaluation (pas {self.state.global_step})")
            metrics = super().evaluate(eval_dataset=eval_dataset, ignore_keys=ignore_keys,
                                       metric_key_prefix=metric_key_prefix)
            if self.quality_probe is not None and metric_key_prefix == "eval":
                if self.progress:
                    self.progress.phase(f"sonde qualité : génération (pas {self.state.global_step})")
                extra = {f"{metric_key_prefix}_{k}": v for k, v in self.quality_probe(self.model).items()}
                self.log(extra)
                metrics.update(extra)
            if self.progress:
                self.progress.phase("entraînement")
            return metrics

    return GherkinSFTTrainer


def run_training(cfg: Config) -> Path:
    """Entraîne et évalue. L'avancement est écrit dans `<output_dir>/progress.json` (lu par l'interface)."""
    out_dir = Path(cfg.training.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    progress = ProgressWriter(out_dir)
    try:
        adapter_dir, stopped = _train(cfg, out_dir, progress)
    except KeyboardInterrupt:
        progress.finish(STOPPED, error="interrompu")
        raise
    except BaseException as e:
        progress.finish(ERROR, error=f"{type(e).__name__}: {e}")
        raise
    progress.finish(STOPPED if stopped else DONE)
    return adapter_dir


def _train(cfg: Config, out_dir: Path, progress: ProgressWriter) -> tuple[Path, bool]:
    from datasets import Dataset
    from transformers import EarlyStoppingCallback, set_seed

    add_file_logging(out_dir / "train.log")
    save_config(cfg, out_dir / "config.yaml")
    set_seed(cfg.training.seed)
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    progress.phase("préparation des données")
    tokenizer = load_tokenizer(cfg.model.name_or_path, cfg.model.revision)
    train_pairs, eval_pairs, report = prepare_data(cfg, tokenizer, out_dir)
    test_pairs = report.test_pairs
    progress.update(train_pairs=len(train_pairs), eval_pairs=len(eval_pairs), test_pairs=len(test_pairs))
    has_eval = bool(eval_pairs)
    train_ds = Dataset.from_list(to_examples(train_pairs, cfg))
    eval_ds = Dataset.from_list(to_examples(eval_pairs, cfg)) if has_eval else None

    progress.phase("chargement du modèle (téléchargement au premier lancement)")
    model = load_base_model(cfg.model, training=True)
    sft_config = build_sft_config(cfg, out_dir, has_eval)

    quality_probe = None
    if has_eval and cfg.eval.probe_samples > 0:
        probe_pairs = eval_pairs[: cfg.eval.probe_samples]
        probe_params = GenerationParams(max_new_tokens=cfg.eval.probe_max_new_tokens, batch_size=cfg.eval.batch_size)

        def quality_probe(m):
            return probe(m, tokenizer, probe_pairs, cfg.prompt.system_prompt, cfg.prompt.user_template,
                         probe_params, cfg.data.expected_language)

    progress_callback = make_callback(progress)
    callbacks = [progress_callback]
    if has_eval and cfg.training.early_stopping_patience and sft_config.load_best_model_at_end:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=cfg.training.early_stopping_patience))

    progress.phase("préparation de l'entraînement (tokenisation)")
    trainer = make_trainer_class()(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        peft_config=build_lora_config(cfg),
        callbacks=callbacks,
        quality_probe=quality_probe,
        progress=progress,
    )
    trainable, total = count_parameters(trainer.model)
    log.info("Paramètres entraînables : %s / %s (%.2f %%)", f"{trainable:,}", f"{total:,}", 100 * trainable / total)

    resume = cfg.training.resume_from_checkpoint
    train_result = trainer.train(resume_from_checkpoint=True if resume == "last" else resume)
    stopped = progress_callback.stopped

    progress.phase("enregistrement de l'adaptateur")
    adapter_dir = out_dir / "adapter"
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    write_run_info(adapter_dir, {
        "base_model": cfg.model.name_or_path,
        "base_revision": cfg.model.revision,
        **prompt_info(cfg, report),
        "expected_language": cfg.data.expected_language,
        "max_length": cfg.data.max_length,
        "train_pairs": len(train_pairs),
        "eval_pairs": len(eval_pairs),
        "test_pairs": len(test_pairs),
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "stopped_early": stopped,
        "git_commit": _git_commit(),
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    metrics = {"train": train_result.metrics}
    # Après une demande d'arrêt, on enregistre l'adaptateur sans lancer les évaluations finales.
    if has_eval and not stopped:
        metrics["eval"] = trainer.evaluate()
    (out_dir / "metrics_entrainement.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    log.info("Adaptateur enregistré dans %s", adapter_dir)

    # Évaluation finale sur le jeu de test s'il existe (jamais vu), sinon sur le jeu d'évaluation.
    final_pairs, final_set = (test_pairs, "test") if test_pairs else (eval_pairs, "évaluation")
    if final_pairs and cfg.eval.run_after_training and not stopped:
        e = cfg.eval
        eval_subset = final_pairs[: e.max_samples] if e.max_samples else final_pairs
        progress.phase(f"évaluation finale : génération sur {len(eval_subset)} paires ({final_set})")
        params = GenerationParams(e.max_new_tokens, e.batch_size, e.do_sample, e.temperature, e.top_p,
                                  e.repetition_penalty)
        final = evaluate_pairs(trainer.model, tokenizer, eval_subset, cfg.prompt.system_prompt,
                               cfg.prompt.user_template, params, cfg.data.expected_language,
                               out_dir / "eval", label=f"{out_dir.name} ({final_set})")
        log.info("Évaluation finale : %s", {k: final[k] for k in ("score_qualite", "syntaxe_ok", "tronque")})
    return adapter_dir, stopped
