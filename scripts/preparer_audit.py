#!/usr/bin/env python3
"""Prépare un échantillon d'audit stratifié par type de source : data/audit_prive/echantillon_<k>.jsonl.

Usage: preparer_audit.py <paires_par_type=12> <paires_par_fichier=24> [graine=1]
Chaque ligne : id de paire, type, texte source (+ code), spécification, gherkin, notes. L'échantillon est
indépendant du filtrage des niveaux : toutes les paires (A, B, C, D) peuvent être tirées.
"""
import json, random, sys
from collections import defaultdict
from pathlib import Path

racine = Path(__file__).resolve().parents[1]
n_type, n_fichier = int(sys.argv[1]), int(sys.argv[2])
graine = int(sys.argv[3]) if len(sys.argv) > 3 else 1
dossier = racine / "data/audit_prive"
dossier.mkdir(parents=True, exist_ok=True)
vus = set()
for f in dossier.glob("echantillon_*.jsonl"):  # ne jamais réauditer une paire
    vus |= {json.loads(l)["paire"] for l in open(f, encoding="utf-8")}
regles = {}
for ficher in list((racine / "data/unites").glob("*.jsonl")) + [racine / "data/pilote/regles_20.jsonl", racine / "data/lot2/regles_200.jsonl"]:
    for l in open(ficher, encoding="utf-8"):
        r = json.loads(l)
        regles[(ficher.stem, r["id"])] = r
par_type = defaultdict(list)
for k in ("train", "val", "test", "a_relire"):
    for l in open(racine / f"data/corpus_prive/{k}.jsonl", encoding="utf-8"):
        p = json.loads(l)
        if p["id"] not in vus:
            par_type[p["source_type"]].append(p)
rng = random.Random(graine)
choix = []
for t, ps in sorted(par_type.items()):
    rng.shuffle(ps)
    choix += ps[:n_type]
rng.shuffle(choix)
lignes = []
for p in choix:
    rid = p["id"].split("-", 1)[1]
    cand = [r for (stem, i), r in regles.items() if i == rid and r.get("type", "catala") == p["source_type"] and r.get("source", "") == p["source"]
            and r.get("article", "") == p["reference"]]
    r = cand[0] if cand else None
    if not r:
        continue
    lignes.append({"paire": p["id"], "type": p["source_type"], "niveau": p["niveau"], "source_texte": r["texte_loi"],
                   "source_code": r.get("code_catala", ""), "specification": p["specification"],
                   "gherkin": p["gherkin"], "notes": p["notes"]})
for k in range(0, len(lignes), n_fichier):
    nom = dossier / f"echantillon_{len(list(dossier.glob('echantillon_*.jsonl'))):02d}.jsonl"
    nom.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lignes[k:k + n_fichier]) + "\n", encoding="utf-8")
    print(nom, len(lignes[k:k + n_fichier]))
