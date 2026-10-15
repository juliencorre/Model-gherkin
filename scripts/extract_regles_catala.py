#!/usr/bin/env python3
"""Extrait des unités (article de loi + code Catala) depuis sources/regles-as-code/catala-examples.

Usage: extract_regles_catala.py <catala-examples-dir> <sortie.jsonl>
Sélection déterministe: 6 Smic, 5 allocations familiales, 5 aides au logement, jusqu'à 3 prestations familiales (dédoublonnées), 1 successions, 2 ASP.
"""
import json, re, sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
QUOTA = [
    ("smic", ["smic/Smic.catala_fr"], 6),
    ("allocations_familiales", ["allocations_familiales/securite_sociale_L.catala_fr",
                                 "allocations_familiales/securite_sociale_D.catala_fr",
                                 "allocations_familiales/securite_sociale_R.catala_fr"], 5),
    ("aides_logement", ["aides_logement/code_sécurité_sociale.catala_fr",
                        "aides_logement/code_construction_reglementaire.catala_fr",
                        "aides_logement/arrete_2019-09-27.catala_fr"], 5),
    ("prestations_familiales", ["prestations_familiales/sécurité_sociale_L.catala_fr",
                                "prestations_familiales/sécurité_sociale_R.catala_fr"], 3),
    ("droit_successions", ["droit_successions/droit_successions.catala_fr"], 1),
    ("asp", ["asp/fonpeps/fonpeps.catala_fr", "asp/aide_fibre/Aide_travaux_raccordement_fibre_optique.catala_fr"], 2),
]
HEAD = re.compile(r"^###+ (Article .*?)\s*(?:\|\s*(\S+))?\s*$", re.M)
BLOCK = re.compile(r"```catala\n(.*?)```", re.S)

def units(path):
    text = path.read_text(encoding="utf-8")
    heads = list(HEAD.finditer(text))
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[h.end():end]
        code = BLOCK.findall(body)
        prose = BLOCK.sub("", body).strip()
        prose = re.sub(r"^#+ .*$", "", prose, flags=re.M).strip()
        if code and 250 <= len(prose) <= 1800 and 150 <= sum(map(len, code)) <= 2500:
            yield {"article": h.group(1).strip(), "id_legifrance": h.group(2),
                   "source": str(path.relative_to(root)), "texte_loi": prose,
                   "code_catala": "\n".join(c.strip() for c in code)}

rows, vus = [], set()

def cle(u):  # dédoublonnage sur le texte de loi et sur le code
    norm = lambda t: re.sub(r"\W+", " ", t).lower()
    if re.match(r"Article [LRD] ?\d", u["article"]):  # même article dans deux fichiers = même règle
        return (u["article"].replace(" ", ""),)
    return (norm(u["texte_loi"]), norm(u["code_catala"]))

for domaine, files, n in QUOTA:
    cands = []
    for f in files:
        if not (root / f).exists():
            continue
        for u in units(root / f):
            if cle(u) not in vus and cle(u) not in {cle(c) for c in cands}:
                cands.append(u)
    step = max(1, len(cands) // n)
    for u in cands[::step][:n]:
        vus.add(cle(u))
        rows.append({"id": f"RG-{len(rows)+1:02d}", "domaine": domaine, **u})
out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
print(len(rows), "unités écrites dans", out)
