import sys
from pathlib import Path

import pytest

# Permet `from tiny_model import ...` dans les tests.
sys.path.insert(0, str(Path(__file__).parent))

from cpu_kernel import TorchChunkedLogProb  # noqa: E402


@pytest.fixture(autouse=True)
def _cpu_logprob_kernel(monkeypatch):
    """Sur CPU, remplace le noyau Triton de TRL par son équivalent PyTorch (voir cpu_kernel.py)."""
    try:
        import trl.trainer.utils as trl_utils
    except ImportError:
        return
    if getattr(trl_utils, "_ChunkedLogProbFunction", 1) is None:
        monkeypatch.setattr(trl_utils, "_ChunkedLogProbFunction", TorchChunkedLogProb)
