#!/usr/bin/env python3
"""Extrait des unités sources (une règle ou un groupe de cas = une future paire) vers data/unites/<type>.jsonl.

Usage: extraire_unites.py <racine du dépôt> <parquet service-public>
Schéma commun : id, type, domaine, article, source, texte_loi, code_catala, licence_source, redistribuable.
Sélection déterministe. Les unités déjà utilisées (pilote, lot2) sont exclues.
Types : catala_reste, publicodes_reste (permissifs), service_public (Licence Ouverte 2.0),
        openfisca (AGPL-3.0), cdtn (licence à clarifier), aides_jeunes (AGPL-3.0).
Les types sous copyleft ou licence incertaine sont marqués redistribuable=false.
"""
import glob
import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq
import yaml

racine, parquet = Path(sys.argv[1]), sys.argv[2]
sortie = racine / "data/unites"
sortie.mkdir(parents=True, exist_ok=True)
norm = lambda t: re.sub(r"\W+", " ", t).lower()

deja = set()
for f in ("data/pilote/regles_20.jsonl", "data/lot2/regles_200.jsonl"):
    for l in open(racine / f, encoding="utf-8"):
        deja.add(norm(json.loads(l)["texte_loi"]))


def ecrire(nom, prefixe, rows, licence, redistribuable):
    for i, r in enumerate(rows, start=1):
        r.update({"id": f"{prefixe}-{i:05d}", "type": nom, "licence_source": licence, "redistribuable": redistribuable})
    rows = [{"id": r["id"], **{k: v for k, v in r.items() if k != "id"}} for r in rows]
    (sortie / f"{nom}.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"{nom}: {len(rows)} unités")


# --- Catala (reste) -----------------------------------------------------------------------
HEAD = re.compile(r"^###+ (Article .*?)\s*(?:\|\s*(\S+))?\s*$", re.M)
BLOCK = re.compile(r"```catala\n(.*?)```", re.S)
vus, rows = set(deja), []
base = racine / "sources/regles-as-code/catala-examples"
for f in sorted(glob.glob(str(base / "**/*.catala_fr"), recursive=True)):
    if "/tests/" in f:
        continue
    rel = Path(f).relative_to(base)
    t = Path(f).read_text(encoding="utf-8")
    hs = list(HEAD.finditer(t))
    for i, h in enumerate(hs):
        body = t[h.end(): hs[i + 1].start() if i + 1 < len(hs) else len(t)]
        code = BLOCK.findall(body)
        prose = re.sub(r"^#+ .*$", "", BLOCK.sub("", body), flags=re.M).strip()
        k = norm(prose)
        if code and 150 <= len(prose) <= 2200 and 100 <= sum(map(len, code)) <= 3000 and k not in vus:
            vus.add(k)
            rows.append({"domaine": rel.parts[0], "article": h.group(1).strip(), "id_legifrance": h.group(2),
                         "source": str(rel), "texte_loi": prose, "code_catala": "\n".join(c.strip() for c in code)})
ecrire("catala_reste", "CA", rows, "Apache-2.0", True)

# --- Publicodes mon-entreprise (reste) -------------------------------------------------------
rows = []
base = racine / "sources/regles-as-code/mon-entreprise"
for f in sorted(glob.glob(str(base / "**/*.publicodes"), recursive=True)):
    rel = Path(f).relative_to(base)
    for b in re.split(r"\n(?=[^\s#][^\n]*:\s*\n)", Path(f).read_text(encoding="utf-8")):
        k = norm(b)
        if (re.search(r"^\s+(description|note):", b, re.M)
                and re.search(r"^\s+(valeur|formule|somme|produit|variations|applicable si|non applicable si|taux|barème|plafond)", b, re.M)
                and 150 <= len(b) <= 2500 and k not in vus):
            vus.add(k)
            rows.append({"domaine": rel.parts[0], "article": b.split(":", 1)[0].strip(), "id_legifrance": None,
                         "source": str(rel), "texte_loi": b.strip(), "code_catala": ""})
ecrire("publicodes_reste", "PU", rows, "MIT", True)

# --- Service-public.fr (fiches, Licence Ouverte 2.0) ---------------------------------------------
pat = re.compile(r"\d[\d  ]*(?:,\d+)?\s*(?:€|euros?|%|jours?|mois|ans|semaines|heures)", re.I)
cond = re.compile(r"\b(si|lorsque|sauf|à condition|doit|doivent|peut|ne peut pas|au plus|au moins|maximum|minimum|plafond|délai|obligatoire|interdit)\b", re.I)
chunks = pq.read_table(parquet, columns=["doc_id", "chunk_index", "title", "theme", "text", "url", "audience"]).to_pylist()
par_doc, rows = {}, []
for c in chunks:
    t = c["text"]
    if 250 <= len(t) <= 2500 and len(pat.findall(t)) >= 2 and len(cond.findall(t)) >= 3:
        par_doc.setdefault(c["doc_id"], []).append(c)
for doc in sorted(par_doc):
    for c in par_doc[doc][:2]:  # au plus 2 extraits par fiche
        theme = (c["theme"] or "divers").split(",")[0].strip()
        rows.append({"domaine": theme, "article": c["title"], "id_legifrance": None, "source": c["url"],
                     "texte_loi": f"{c['title']}\n{c['text']}".strip(), "code_catala": ""})
ecrire("service_public", "SP", rows, "Licence Ouverte 2.0 (Etalab)", True)

# --- OpenFisca-France (tests YAML, AGPL-3.0) -----------------------------------------------------
rows = []
base = racine / "sources_local/openfisca-france"
for f in sorted(glob.glob(str(base / "**/*.y*ml"), recursive=True)):
    txt = Path(f).read_text(encoding="utf-8")
    try:
        d = yaml.safe_load(txt)
    except Exception:  # noqa: BLE001
        continue
    items = d if isinstance(d, list) else [d]
    cas = [i for i in items if isinstance(i, dict) and "output" in i and "input" in i]
    if len(cas) >= 2 and 400 <= len(txt) <= 6000:
        rel = Path(f).relative_to(base)
        rows.append({"domaine": rel.parts[1] if len(rel.parts) > 2 else rel.parts[0], "article": cas[0].get("name", rel.stem),
                     "id_legifrance": None, "source": str(rel), "texte_loi": txt.strip(), "code_catala": ""})
ecrire("openfisca", "OF", rows, "AGPL-3.0", False)

# --- Code du travail numérique (tests de modèles, licence à clarifier) ----------------------------
rows = []
base = racine / "sources_local/code-du-travail-numerique"
for f in sorted(glob.glob(str(base / "**/*.spec.ts"), recursive=True)):
    txt = Path(f).read_text(encoding="utf-8")
    txt = re.sub(r"url: \"https?://[^\"]+\"", 'url: "…"', txt)
    if "expectedResult" in txt and 600 <= len(txt) <= 6000:
        rel = Path(f).relative_to(base)
        conv = re.search(r"conventions/([^/]+)/", str(rel))
        rows.append({"domaine": conv.group(1) if conv else "code_du_travail", "article": rel.parts[-3] if len(rel.parts) > 3 else rel.stem,
                     "id_legifrance": None, "source": str(rel), "texte_loi": txt.strip(), "code_catala": ""})
ecrire("cdtn", "CD", rows, "À clarifier (Apache-2.0 ou MIT)", False)

# --- aides-jeunes (fiches d'aides, AGPL-3.0) -----------------------------------------------------
rows = []
base = racine / "sources_local/aides-jeunes/data/benefits"
for f in sorted(glob.glob(str(base / "**/*.yml"), recursive=True)):
    txt = Path(f).read_text(encoding="utf-8")
    try:
        d = yaml.safe_load(txt)
    except Exception:  # noqa: BLE001
        continue
    if isinstance(d, dict) and d.get("conditions") and d.get("description") and 250 <= len(txt) <= 3500:
        rel = Path(f).relative_to(base)
        rows.append({"domaine": rel.parts[0], "article": d.get("label", rel.stem), "id_legifrance": None,
                     "source": str(rel), "texte_loi": txt.strip(), "code_catala": ""})
ecrire("aides_jeunes", "AJ", rows, "AGPL-3.0", False)
