"""Modèle Ministral 3 miniature (poids aléatoires) et tokenizer jouet, pour tester la chaîne sans GPU ni réseau.

Même architecture que le vrai modèle (Mistral3ForConditionalGeneration : tour de vision Pixtral + modèle de
langage ministral3), en quelques centaines de milliers de paramètres.
"""

from __future__ import annotations

import json
from pathlib import Path

# Mêmes identifiants que le vrai tokenizer pour les premiers tokens spéciaux ([IMG] = 10, <pad> = 11).
SPECIAL_TOKENS = [
    "<unk>", "<s>", "</s>", "[INST]", "[/INST]", "[AVAILABLE_TOOLS]", "[/AVAILABLE_TOOLS]", "[TOOL_RESULTS]",
    "[/TOOL_RESULTS]", "[TOOL_CALLS]", "[IMG]", "<pad>", "[IMG_BREAK]", "[IMG_END]", "[PREFIX]", "[MIDDLE]",
    "[SUFFIX]", "[SYSTEM_PROMPT]", "[/SYSTEM_PROMPT]",
]

# Version réduite du modèle de chat de Ministral 3 (même rendu pour system/user/assistant).
CHAT_TEMPLATE = (
    "{{- bos_token }}"
    "{%- for message in messages %}"
    "{%- if message['role'] == 'system' %}{{- '[SYSTEM_PROMPT]' + message['content'] + '[/SYSTEM_PROMPT]' }}"
    "{%- elif message['role'] == 'user' %}{{- '[INST]' + message['content'] + '[/INST]' }}"
    "{%- elif message['role'] == 'assistant' %}{{- message['content'] + eos_token }}"
    "{%- endif %}{%- endfor %}"
)


def build_tokenizer(corpus: list[str], vocab_size: int = 800):
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast

    tok = Tokenizer(models.BPE(unk_token="<unk>"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=vocab_size, special_tokens=SPECIAL_TOKENS,
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    tok.train_from_iterator(corpus, trainer)
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, bos_token="<s>", eos_token="</s>", unk_token="<unk>",
                                   pad_token="<pad>", additional_special_tokens=SPECIAL_TOKENS[3:])
    fast.chat_template = CHAT_TEMPLATE
    return fast


def build_tiny_ministral3(out_dir: str | Path, corpus: list[str]) -> Path:
    import torch
    from transformers import AutoModelForImageTextToText, Mistral3Config

    out = Path(out_dir)
    tokenizer = build_tokenizer(corpus)
    config = Mistral3Config(
        text_config={
            "model_type": "ministral3", "vocab_size": len(tokenizer), "hidden_size": 64, "intermediate_size": 128,
            "num_hidden_layers": 2, "num_attention_heads": 4, "num_key_value_heads": 2, "head_dim": 16,
            "max_position_embeddings": 4096, "tie_word_embeddings": True, "rms_norm_eps": 1e-5,
            "rope_parameters": {"rope_type": "yarn", "rope_theta": 1e6, "factor": 16.0, "beta_fast": 32.0,
                                "beta_slow": 1.0, "mscale": 1.0, "mscale_all_dim": 1.0,
                                "original_max_position_embeddings": 256, "llama_4_scaling_beta": 0.1},
            "bos_token_id": 1, "eos_token_id": 2, "pad_token_id": 11,
        },
        vision_config={
            "model_type": "pixtral", "hidden_size": 32, "intermediate_size": 64, "num_hidden_layers": 1,
            "num_attention_heads": 2, "head_dim": 16, "image_size": 56, "patch_size": 14,
        },
        image_token_index=10,
        spatial_merge_size=2,
        tie_word_embeddings=True,
    )
    torch.manual_seed(0)
    model = AutoModelForImageTextToText.from_config(config)  # classe de Ministral 3 (vision + texte)
    model.generation_config.eos_token_id = 2
    model.generation_config.pad_token_id = 11
    model.save_pretrained(out)
    tokenizer.save_pretrained(out)
    return out


def corpus_from_jsonl(path: str | Path) -> list[str]:
    from gherkin_ft.prompts import DEFAULT_SYSTEM_PROMPT

    texts = [DEFAULT_SYSTEM_PROMPT]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        texts += [r["specification"], r["gherkin"]]
    return texts
