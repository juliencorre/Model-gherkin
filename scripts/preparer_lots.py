#!/usr/bin/env python3
"""Découpe un fichier d'unités en lots de N unités : data/lots/<type>/lot_<NNNN>.jsonl.

Usage: preparer_lots.py <type> <début> <nombre_de_lots> [taille=25] [--aleatoire graine]
Sélection : unités triées par id, ou mélangées de façon reproductible avec --aleatoire.
Crée aussi data/corpus/lots_supplementaires.json pour construire_corpus.py.
"""
import json, random, sys
from pathlib import Path

racine = Path(__file__).resolve().parents[1]
type_, debut, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
taille = int(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else 25
unites = [json.loads(l) for l in open(racine / f"data/unites/{type_}.jsonl", encoding="utf-8")]
if "--aleatoire" in sys.argv:
    random.Random(int(sys.argv[sys.argv.index("--aleatoire") + 1])).shuffle(unites)
dossier = racine / f"data/lots/{type_}"
dossier.mkdir(parents=True, exist_ok=True)
for k in range(debut, debut + n):
    morceau = unites[k * taille:(k + 1) * taille]
    if not morceau:
        break
    (dossier / f"lot_{k:04d}.jsonl").write_text("\n".join(json.dumps(u, ensure_ascii=False) for u in morceau) + "\n", encoding="utf-8")
    print(dossier / f"lot_{k:04d}.jsonl", len(morceau), "unités")
