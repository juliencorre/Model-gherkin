"""Génération par lots avec le modèle de chat."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import torch


@dataclass
class GenerationParams:
    max_new_tokens: int = 2048
    batch_size: int = 8
    do_sample: bool = False
    temperature: float = 0.1
    top_p: float = 1.0
    repetition_penalty: float = 1.0


def chat_token_ids(tokenizer, messages: list[dict], add_generation_prompt: bool = False) -> list[int]:
    out = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=add_generation_prompt)
    if isinstance(out, Mapping):
        out = out["input_ids"]
    return list(out)


@torch.no_grad()
def generate(model, tokenizer, conversations: list[list[dict]], params: GenerationParams) -> list[tuple[str, bool]]:
    """Génère une réponse par conversation. Renvoie (texte, terminé_par_EOS) dans l'ordre d'entrée."""
    was_training = model.training
    model.eval()
    padding_side = tokenizer.padding_side
    tokenizer.padding_side = "left"
    prompts = [tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=True) for c in conversations]
    # Lots de longueurs voisines pour limiter le remplissage.
    order = sorted(range(len(prompts)), key=lambda i: len(prompts[i]), reverse=True)
    results: list[tuple[str, bool] | None] = [None] * len(prompts)
    eos_ids = model.generation_config.eos_token_id
    eos_ids = set(eos_ids if isinstance(eos_ids, list) else [eos_ids if eos_ids is not None else tokenizer.eos_token_id])
    gen_kwargs = {
        "max_new_tokens": params.max_new_tokens,
        "do_sample": params.do_sample,
        "repetition_penalty": params.repetition_penalty,
        "pad_token_id": tokenizer.pad_token_id,
        "use_cache": True,
    }
    if params.do_sample:
        gen_kwargs.update(temperature=params.temperature, top_p=params.top_p)
    else:
        gen_kwargs.update(temperature=None, top_p=None, top_k=None)
    try:
        for start in range(0, len(order), params.batch_size):
            idx = order[start : start + params.batch_size]
            # Le modèle de chat ajoute déjà le token de début <s>.
            enc = tokenizer([prompts[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False)
            enc = {k: v.to(model.device) for k, v in enc.items()}
            out = model.generate(**enc, **gen_kwargs)
            new_tokens = out[:, enc["input_ids"].shape[1] :]
            for row, i in zip(new_tokens, idx):
                ids = row.tolist()
                finished = any(t in eos_ids for t in ids)
                results[i] = (tokenizer.decode(ids, skip_special_tokens=True).strip() + "\n", finished)
    finally:
        tokenizer.padding_side = padding_side
        if was_training:
            model.train()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return results  # type: ignore[return-value]
