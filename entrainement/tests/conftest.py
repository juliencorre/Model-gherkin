import sys
from pathlib import Path

import pytest

# Permet `from tiny_model import ...` dans les tests.
sys.path.insert(0, str(Path(__file__).parent))


class _TorchChunkedLogProb:
    """Équivalent PyTorch (non optimisé) du noyau Triton de TRL qui calcule les log-probabilités des labels.

    TRL >= 1.x branche ce noyau sur le modèle pendant l'entraînement ; Triton n'existe qu'avec un GPU. Sur la
    RTX 5080, c'est le vrai noyau qui tourne ; ce remplacement sert uniquement aux tests sur CPU.
    """

    @staticmethod
    def apply(hidden, weight, bias, targets, temperature, chunk_size, softcap=None, logit_scale=1.0, outputs=()):
        import torch

        logits = hidden.float() @ weight.float().t()
        if bias is not None:
            logits = logits + bias.float()
        logits = logits * logit_scale
        if softcap:
            logits = softcap * torch.tanh(logits / softcap)
        logp = torch.log_softmax(logits / temperature, dim=-1)
        log_probs = logp.gather(-1, targets[:, None]).squeeze(-1)
        entropy = -(logp.exp() * logp).sum(-1) if "entropy" in outputs else None
        is_top1 = (logits.argmax(-1) == targets) if "is_top1" in outputs else None
        return log_probs, entropy, None, None, is_top1


@pytest.fixture(autouse=True)
def _cpu_logprob_kernel(monkeypatch):
    try:
        import trl.trainer.utils as trl_utils
    except ImportError:
        return
    if getattr(trl_utils, "_ChunkedLogProbFunction", 1) is None:
        monkeypatch.setattr(trl_utils, "_ChunkedLogProbFunction", _TorchChunkedLogProb)
