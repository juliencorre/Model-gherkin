#!/usr/bin/env bash
# Installation de l'environnement d'entraînement sur Ubuntu (22.04 / 24.04) avec une RTX 5080 (Blackwell, sm_120).
#
# Prérequis : pilote NVIDIA >= 570 avec les modules noyau « open » (obligatoires pour Blackwell).
#   sudo ubuntu-drivers list               # pilotes disponibles
#   sudo apt install nvidia-driver-580-open  # ou la version -open la plus récente proposée
#   sudo reboot
# Le toolkit CUDA système n'est pas nécessaire : les roues PyTorch embarquent leur runtime CUDA.
#
# Usage : bash entrainement/install_ubuntu_rtx5080.sh [dossier_venv]   (défaut : entrainement/.venv)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${1:-$HERE/.venv}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi introuvable : installez d'abord le pilote NVIDIA (voir l'en-tête de ce script)." >&2
    exit 1
fi
DRIVER="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n1)"
DRIVER_MAJOR="${DRIVER%%.*}"
GPU="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)"
echo "GPU : $GPU — pilote $DRIVER"

# Choix de l'index PyTorch selon le pilote : CUDA 13.0 demande un pilote >= 580, CUDA 12.8 un pilote >= 570.
if [ "$DRIVER_MAJOR" -ge 580 ]; then
    TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu130}"
elif [ "$DRIVER_MAJOR" -ge 570 ]; then
    TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu128}"
else
    echo "Pilote $DRIVER trop ancien pour une carte Blackwell : 570 minimum (modules -open)." >&2
    exit 1
fi
if ! grep -qi "open" /proc/driver/nvidia/version 2>/dev/null; then
    echo "Attention : les modules noyau « open » ne semblent pas chargés ; ils sont requis pour les RTX 50xx." >&2
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "Installation de uv (gestionnaire d'environnements Python)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uv venv --python "$PYTHON_VERSION" "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "Installation de PyTorch depuis $TORCH_INDEX"
uv pip install torch --index-url "$TORCH_INDEX"
uv pip install -e "$HERE[gpu,dev]"

echo
python -m gherkin_ft check-env
echo
echo "Environnement prêt. Activez-le avec : source $VENV/bin/activate"
