"""Chargement du tokenizer, du modèle de base et de l'adaptateur LoRA."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForImageTextToText, AutoTokenizer

from .config import ModelConfig

log = logging.getLogger(__name__)

RUN_INFO_FILE = "gherkin_ft.json"
VISION_MODULES = ("vision_tower", "multi_modal_projector")


def resolve_dtype(name: str) -> torch.dtype:
    if not torch.cuda.is_available():
        # Sur CPU, bf16 divise la mémoire par deux (rapide sur les CPU AMX / AVX512-BF16) ; sinon float32.
        return torch.bfloat16 if name in ("bfloat16", "bf16") else torch.float32
    if name in ("bfloat16", "bf16", "auto"):
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        log.warning("GPU sans support bf16 : passage en float16")
        return torch.float16
    return {"float16": torch.float16, "fp16": torch.float16, "float32": torch.float32}[name]


def load_tokenizer(name_or_path: str, revision: str | None = None, padding_side: str = "right"):
    # Les tokenizers Mistral publiés sur le Hub ont une regex de pré-découpage erronée : transformers
    # demande `fix_mistral_regex=True` (sans effet sur les autres tokenizers). Le tokenizer enregistré avec
    # l'adaptateur contient la regex corrigée.
    tokenizer = AutoTokenizer.from_pretrained(name_or_path, revision=revision, fix_mistral_regex=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.unk_token or tokenizer.eos_token
    tokenizer.padding_side = padding_side
    if tokenizer.chat_template is None:
        raise ValueError(f"Le tokenizer de {name_or_path} n'a pas de modèle de chat (chat_template).")
    return tokenizer


def _check_not_fp8(config, name: str) -> None:
    quant = getattr(config, "quantization_config", None)
    method = quant.get("quant_method") if isinstance(quant, dict) else getattr(quant, "quant_method", None)
    if str(method).lower().endswith("fp8"):
        raise ValueError(
            f"{name} est publié en FP8, ce qui ne convient pas à l'entraînement LoRA. "
            "Utilisez la version BF16 : mistralai/Ministral-3-3B-Instruct-2512-BF16."
        )


def load_base_model(mcfg: ModelConfig, training: bool):
    """Charge le modèle de base (bf16 ou 4 bits). Ministral 3 est un modèle vision-langage : on charge
    Mistral3ForConditionalGeneration et on n'utilise que la partie texte."""
    config = AutoConfig.from_pretrained(mcfg.name_or_path, revision=mcfg.revision)
    _check_not_fp8(config, mcfg.name_or_path)
    is_vlm = hasattr(config, "vision_config")
    auto_cls = AutoModelForImageTextToText if is_vlm else AutoModelForCausalLM
    dtype = resolve_dtype(mcfg.dtype)
    kwargs = {"dtype": dtype, "revision": mcfg.revision, "attn_implementation": mcfg.attn_implementation}
    if torch.cuda.is_available():
        kwargs["device_map"] = {"": torch.cuda.current_device()}
    if mcfg.load_in_4bit:
        if not torch.cuda.is_available():
            raise RuntimeError("QLoRA (load_in_4bit) nécessite un GPU CUDA.")
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
            llm_int8_skip_modules=[*VISION_MODULES, "lm_head"],
        )
    log.info("Chargement de %s (%s, dtype=%s, 4 bits=%s)", mcfg.name_or_path, auto_cls.__name__, dtype, mcfg.load_in_4bit)
    model = auto_cls.from_pretrained(mcfg.name_or_path, **kwargs)
    for name, param in model.named_parameters():
        if any(m in name for m in VISION_MODULES):
            param.requires_grad_(False)
    if training:
        model.config.use_cache = False
        model.config.get_text_config().use_cache = False
    return model


def count_parameters(model) -> tuple[int, int]:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total


def read_run_info(adapter_dir: str | Path) -> dict:
    path = Path(adapter_dir) / RUN_INFO_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_run_info(adapter_dir: str | Path, info: dict) -> None:
    Path(adapter_dir, RUN_INFO_FILE).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


def load_for_inference(base: str | None, adapter: str | None, load_in_4bit: bool = False, merge: bool = True):
    """Charge (modèle, tokenizer, infos du run) pour la génération.

    - `adapter` seul : le modèle de base est lu dans `gherkin_ft.json` (ou adapter_config.json).
    - `base` seul : modèle de base ou modèle fusionné.
    """
    info = read_run_info(adapter) if adapter else {}
    if base is None and adapter:
        base = info.get("base_model")
        if base is None:
            cfg_path = Path(adapter) / "adapter_config.json"
            base = json.loads(cfg_path.read_text(encoding="utf-8"))["base_model_name_or_path"]
    if base is None:
        raise ValueError("Indiquez --model (modèle de base ou fusionné) ou --adapter.")
    if not info and Path(base, RUN_INFO_FILE).exists():  # modèle fusionné par `gherkin-ft merge`
        info = read_run_info(base)
    model = load_base_model(ModelConfig(name_or_path=base, load_in_4bit=load_in_4bit), training=False)
    tok_source = adapter if adapter and Path(adapter, "tokenizer_config.json").exists() else base
    tokenizer = load_tokenizer(tok_source, padding_side="left")
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter)
        if merge and not load_in_4bit:
            model = model.merge_and_unload()
    model.eval()
    return model, tokenizer, info
