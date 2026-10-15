"""Fusion de l'adaptateur LoRA dans le modèle de base (pour vLLM, llama.cpp/GGUF, Ollama...)."""

from __future__ import annotations

import logging
from pathlib import Path

import torch

from .modeling import RUN_INFO_FILE, load_tokenizer, read_run_info, write_run_info

log = logging.getLogger(__name__)


def merge_adapter(adapter_dir: str, output_dir: str, base: str | None = None, device: str = "auto") -> Path:
    """Fusionne en bf16. Le modèle de base est rechargé en pleine précision : ne jamais fusionner sur un
    modèle 4 bits (perte de précision). `device="cpu"` évite d'occuper le GPU (~8 Go de RAM nécessaires)."""
    from peft import PeftModel
    from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForImageTextToText

    info = read_run_info(adapter_dir)
    base = base or info.get("base_model")
    if base is None:
        raise ValueError("Modèle de base inconnu : indiquez --model")
    config = AutoConfig.from_pretrained(base, revision=info.get("base_revision"))
    auto_cls = AutoModelForImageTextToText if hasattr(config, "vision_config") else AutoModelForCausalLM
    device_map = {"": 0} if device == "auto" and torch.cuda.is_available() else {"": "cpu"}
    log.info("Chargement de %s pour fusion (%s)", base, device_map)
    model = auto_cls.from_pretrained(base, dtype=torch.bfloat16, device_map=device_map,
                                     revision=info.get("base_revision"))
    model = PeftModel.from_pretrained(model, adapter_dir).merge_and_unload()
    out = Path(output_dir)
    model.save_pretrained(out, safe_serialization=True)
    try:  # fichiers du processeur multimodal, utiles à vLLM et aux convertisseurs
        from transformers import AutoProcessor

        AutoProcessor.from_pretrained(base, revision=info.get("base_revision")).save_pretrained(out)
    except Exception as e:  # noqa: BLE001
        log.info("Processeur non copié (%s)", e)
    load_tokenizer(adapter_dir if Path(adapter_dir, "tokenizer_config.json").exists() else base).save_pretrained(out)
    if info:
        write_run_info(out, {**info, "merged_from": str(adapter_dir)})
    log.info("Modèle fusionné écrit dans %s (%s inclus)", out, RUN_INFO_FILE if info else "sans infos de run")
    return out
