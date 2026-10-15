#!/usr/bin/env bash
# Courbe d'apprentissage : même jeu d'évaluation figé, entraînements sur 500, 1000, 2000 paires puis sur tout,
# et comparaison avec le modèle de base. À lancer depuis la racine du dépôt, environnement activé.
#
# Variables : CONFIG (config YAML), BASE (dossier des runs), SIZES (tailles, 0 = toutes les paires).
set -euo pipefail

CONFIG="${CONFIG:-entrainement/configs/ministral3b_lora.yaml}"
BASE="${BASE:-entrainement/runs/courbe}"
SIZES="${SIZES:-500 1000 2000 0}"

# 1. Découpage figé : le même jeu d'évaluation sert à tous les runs.
gherkin-ft prepare -c "$CONFIG" --set training.output_dir="$BASE/prep"
MANIFEST="$BASE/prep/data/manifest.json"

# 2. Référence : le modèle de base, avec le même prompt.
gherkin-ft evaluate -c "$CONFIG" --data "$BASE/prep/data/eval.jsonl" --out "$BASE/base" --label base

metrics=("$BASE/base/metrics.json")
for n in $SIZES; do
    if [ "$n" = 0 ]; then name="tout"; limit="null"; else name="n$n"; limit="$n"; fi
    gherkin-ft train -c "$CONFIG" \
        --set training.output_dir="$BASE/$name" \
        --set data.split_manifest="$MANIFEST" \
        --set data.train_limit="$limit"
    metrics+=("$BASE/$name/eval/metrics.json")
done

gherkin-ft compare "${metrics[@]}" | tee "$BASE/comparaison.md"
