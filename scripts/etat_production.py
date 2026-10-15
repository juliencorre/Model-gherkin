#!/usr/bin/env python3
"""État de la production : unités disponibles, traitées et restantes par type de source."""
import glob, json
from pathlib import Path

racine = Path(__file__).resolve().parents[1]
tot_dispo = tot_traite = 0
for f in sorted((racine / "data/unites").glob("*.jsonl")):
    t = f.stem
    unites = [json.loads(l)["id"] for l in open(f, encoding="utf-8")]
    traite = set()
    for s in glob.glob(str(racine / f"data/lots/{t}/sortie_*.jsonl")):
        traite |= {json.loads(l)["id"] for l in open(s, encoding="utf-8")}
    lots = len(glob.glob(str(racine / f"data/lots/{t}/lot_*.jsonl")))
    reste = len(unites) - len(traite)
    tot_dispo += len(unites); tot_traite += len(traite)
    print(f"{t:18} unités={len(unites):5} traitées={len(traite):5} restantes={reste:5} lots_préparés={lots}")
print(f"{'TOTAL':18} unités={tot_dispo:5} traitées={tot_traite:5} restantes={tot_dispo - tot_traite:5}")
print("(+ 220 paires hors unités : pilote et lot2)")
