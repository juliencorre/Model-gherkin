"""Vérification de l'environnement (GPU Blackwell RTX 50xx, CUDA, versions des bibliothèques)."""

from __future__ import annotations

import importlib.metadata
import platform
import sys

MIN_VERSIONS = {
    "torch": "2.7.0",  # première version stable compilée pour sm_120 (Blackwell grand public)
    "transformers": "5.0.0",  # Ministral 3 (mistral3 / ministral3)
    "trl": "1.0.0",
    "peft": "0.18.0",
    "accelerate": "1.10.0",
    "datasets": "4.0.0",
    "gherkin-official": "29.0.0",
}
OPTIONAL = ("bitsandbytes", "tensorboard", "sacrebleu")


def _version(pkg: str) -> str | None:
    try:
        return importlib.metadata.version(pkg)
    except importlib.metadata.PackageNotFoundError:
        return None


def _ge(v: str, ref: str) -> bool:
    from packaging.version import Version

    return Version(v.split("+")[0]) >= Version(ref)


def check_environment(test_4bit: bool = True) -> bool:
    ok = True

    def line(status: str, msg: str) -> None:
        print(f"[{status}] {msg}")

    line("info", f"Python {sys.version.split()[0]} ({platform.platform()})")
    for pkg, ref in MIN_VERSIONS.items():
        v = _version(pkg)
        if v is None:
            line("ERREUR", f"{pkg} absent (>= {ref} requis)")
            ok = False
        elif not _ge(v, ref):
            line("ERREUR", f"{pkg} {v} < {ref}")
            ok = False
        else:
            line("ok", f"{pkg} {v}")
    for pkg in OPTIONAL:
        v = _version(pkg)
        line("ok" if v else "info", f"{pkg} {v or 'absent (optionnel)'}")

    import torch

    if not torch.cuda.is_available():
        line("ERREUR", "CUDA indisponible : vérifiez le pilote NVIDIA (nvidia-smi) et la roue PyTorch (index cu128/cu130).")
        return False
    props = torch.cuda.get_device_properties(0)
    cap = torch.cuda.get_device_capability(0)
    line("ok", f"GPU : {props.name}, capacité {cap[0]}.{cap[1]}, {props.total_memory / 2**30:.1f} Gio, CUDA {torch.version.cuda}")
    arch = f"sm_{cap[0]}{cap[1]}"
    arch_list = torch.cuda.get_arch_list()
    if arch not in arch_list and f"compute_{cap[0]}{cap[1]}" not in arch_list:
        line("ERREUR", f"PyTorch n'est pas compilé pour {arch} ({arch_list}). Installez une roue cu128 ou plus récente.")
        ok = False
    if cap[0] >= 12 and torch.version.cuda and not _ge(torch.version.cuda, "12.8"):
        line("ERREUR", f"Blackwell (sm_120) exige CUDA >= 12.8 ; PyTorch est compilé pour CUDA {torch.version.cuda}.")
        ok = False
    line("ok" if torch.cuda.is_bf16_supported() else "ERREUR", f"bf16 supporté : {torch.cuda.is_bf16_supported()}")
    free, total = torch.cuda.mem_get_info()
    line("info", f"Mémoire GPU libre : {free / 2**30:.1f} / {total / 2**30:.1f} Gio")
    if total < 15 * 2**30:
        line("attention", "Moins de 16 Gio : utilisez la config QLoRA ou réduisez max_length / batch.")
    try:
        a = torch.randn(1024, 1024, device="cuda", dtype=torch.bfloat16)
        torch.cuda.synchronize()
        _ = (a @ a).float().sum().item()
        line("ok", "Calcul bf16 sur GPU")
    except Exception as e:  # noqa: BLE001
        line("ERREUR", f"Calcul bf16 sur GPU impossible : {e}")
        ok = False
    # TRL calcule la perte avec un noyau Triton (tête LM par morceaux) : il doit compiler pour ce GPU.
    try:
        import triton
        from trl.kernels import ChunkedLogProbFunction

        h = torch.randn(8, 64, device="cuda", dtype=torch.bfloat16, requires_grad=True)
        w = torch.randn(1000, 64, device="cuda", dtype=torch.bfloat16)
        t = torch.randint(0, 1000, (8,), device="cuda")
        logp = ChunkedLogProbFunction.apply(h, w, None, t, 1.0, 256, None, 1.0, ("log_probs",))[0]
        logp.sum().backward()
        torch.cuda.synchronize()
        line("ok", f"Noyau Triton de TRL fonctionnel (triton {triton.__version__})")
    except Exception as e:  # noqa: BLE001
        line("ERREUR", f"Noyau Triton de TRL indisponible ({type(e).__name__}: {e}) : l'entraînement échouera.")
        ok = False
    if test_4bit and _version("bitsandbytes"):
        try:
            import bitsandbytes as bnb

            layer = bnb.nn.Linear4bit(256, 256, compute_dtype=torch.bfloat16, quant_type="nf4").cuda()
            _ = layer(torch.randn(4, 256, device="cuda", dtype=torch.bfloat16)).sum().item()
            line("ok", "bitsandbytes 4 bits (QLoRA) fonctionnel")
        except Exception as e:  # noqa: BLE001
            line("attention", f"bitsandbytes 4 bits indisponible ({e}) : la config LoRA bf16 reste utilisable.")
    print("\nEnvironnement prêt." if ok else "\nEnvironnement incomplet : corrigez les erreurs ci-dessus.")
    return ok
