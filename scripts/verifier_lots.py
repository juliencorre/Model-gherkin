#!/usr/bin/env python3
"""Vérifie que chaque data/lots/<type>/sortie_N.jsonl correspond exactement à lot_N.jsonl (mêmes ids, sans doublon)
et qu'aucune paire n'est dupliquée entre sorties. Code de sortie 1 en cas d'anomalie."""
import glob, json, re, sys
from collections import Counter
from pathlib import Path

racine = Path(__file__).resolve().parents[1]
anomalies = 0
spec_vues = {}
for s in sorted(glob.glob(str(racine / "data/lots/*/sortie_*.jsonl"))):
    p = Path(s)
    lot = p.with_name(p.name.replace("sortie_", "lot_"))
    if not lot.exists():
        print("SANS LOT", p); anomalies += 1; continue
    ids_lot = [json.loads(l)["id"] for l in open(lot, encoding="utf-8")]
    sortie = [json.loads(l) for l in open(p, encoding="utf-8")]
    ids_out = [r["id"] for r in sortie]
    if Counter(ids_out) != Counter(ids_lot):
        manque = set(ids_lot) - set(ids_out); en_trop = set(ids_out) - set(ids_lot)
        print(f"ANOMALIE {p.parent.name}/{p.name}: manquants={sorted(manque)[:5]} en_trop={sorted(en_trop)[:5]} doublons={[i for i, c in Counter(ids_out).items() if c > 1][:5]}")
        anomalies += 1
    for r in sortie:
        k = re.sub(r"\W+", " ", r["specification"]).lower()
        if k in spec_vues and spec_vues[k] != (p.name, r["id"]):
            print("SPEC EN DOUBLE", r["id"], p.name, spec_vues[k]); anomalies += 1
        spec_vues[k] = (p.name, r["id"])
print("sorties vérifiées:", len(glob.glob(str(racine / 'data/lots/*/sortie_*.jsonl'))), "anomalies:", anomalies)
sys.exit(1 if anomalies else 0)
