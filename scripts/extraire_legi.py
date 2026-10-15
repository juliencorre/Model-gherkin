#!/usr/bin/env python3
"""Extrait des articles de codes en vigueur (jeu AgentPublic/legi, Licence Ouverte 2.0) vers data/unites/legi.jsonl.

Usage: extraire_legi.py <dossier des parquet> <sortie.jsonl> [plafond_par_code=500]
Filtre : article en vigueur, 250 à 2200 caractères, au moins une valeur chiffrée avec unité et au moins deux
marqueurs de condition ; dédoublonné ; au plus `plafond_par_code` articles par code (échantillon régulier).
"""
import json, re, sys
from pathlib import Path

import pyarrow.parquet as pq

dossier, sortie = Path(sys.argv[1]), Path(sys.argv[2])
plafond = int(sys.argv[3]) if len(sys.argv) > 3 else 500
val = re.compile(r"\d[\d  ]*(?:,\d+)?\s*(?:€|euros?|%|pour cent|jours?|mois|ans|semaines|heures|fois)", re.I)
cond = re.compile(r"\b(si|lorsque|sauf|à condition|doit|doivent|peut|ne peut pas|au plus|au moins|maximum|minimum|plafond|délai|obligatoire|interdit|est égal|est fixé|ne peuvent)\b", re.I)
norm = lambda t: re.sub(r"\W+", " ", t).lower()
deja = set()
for f in ("data/pilote/regles_20.jsonl", "data/lot2/regles_200.jsonl"):
    p = Path(__file__).resolve().parents[1] / f
    deja |= {norm(json.loads(l)["texte_loi"]) for l in open(p, encoding="utf-8")}
rows, vus = [], set(deja)
for f in sorted(dossier.glob("*.parquet")):
    t = pq.read_table(f, columns=["doc_id", "status", "title", "number", "text", "subtitles"]).to_pylist()
    cands = []
    for r in t:
        x = r["text"] or ""
        if (r["status"] == "VIGUEUR" and 250 <= len(x) <= 2200 and len(val.findall(x)) >= 1
                and len(cond.findall(x)) >= 2 and norm(x) not in vus):
            vus.add(norm(x))
            cands.append(r)
    cands.sort(key=lambda r: r["doc_id"])
    pas = max(1, len(cands) // plafond)
    choisis = cands[::pas][:plafond]
    print(f.stem, len(cands), "->", len(choisis))
    for r in choisis:
        rows.append({"domaine": (r["title"] or f.stem).replace("Code ", "Code ", 1), "article": f"Article {r['number']}",
                     "id_legifrance": r["doc_id"], "source": f"https://www.legifrance.gouv.fr/codes/article_lc/{r['doc_id']}",
                     "texte_loi": f"{r['title']} — Article {r['number']}\n{r['text']}".strip(), "code_catala": "",
                     "type": "legi", "licence_source": "Licence Ouverte 2.0 (DILA / Etalab)", "redistribuable": True})
for i, r in enumerate(rows, start=1):
    r["id"] = f"LG-{i:05d}"
rows = [{"id": r["id"], **{k: v for k, v in r.items() if k != "id"}} for r in rows]
sortie.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
print(len(rows), "unités")
