#!/usr/bin/env python3
"""Extraction élargie (filtres plus souples) : service_public_2 et legi_2 -> data/unites/<type>.jsonl.

Usage: extraire_unites_elargies.py <racine> <parquet service-public> <dossier des parquet LEGI> [plafond_legi_par_code=400]
Exclut les unités déjà extraites par extraire_unites.py / extraire_legi.py (même texte).
Filtre souple : au moins une valeur chiffrée avec unité et au moins une (LEGI) ou deux (service-public)
marqueurs de condition ; 4 extraits par fiche service-public au plus.
"""
import json, re, sys
from pathlib import Path
import pyarrow.parquet as pq

racine, sp_parquet, dossier = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
plafond = int(sys.argv[4]) if len(sys.argv) > 4 else 400
norm = lambda t: re.sub(r"\W+", " ", t).lower()
val = re.compile(r"\d[\d  ]*(?:,\d+)?\s*(?:€|euros?|%|pour cent|jours?|mois|ans|semaines|heures|fois)", re.I)
cond = re.compile(r"\b(si|lorsque|sauf|à condition|doit|doivent|peut|ne peut pas|au plus|au moins|maximum|minimum|plafond|délai|obligatoire|interdit|est égal|est fixé|ne peuvent)\b", re.I)
sortie = racine / "data/unites"

def deja(*fichiers):
    s = set()
    for f in fichiers:
        p = racine / f
        if p.exists():
            s |= {norm(json.loads(l)["texte_loi"]) for l in open(p, encoding="utf-8")}
    return s

def ecrire(nom, prefixe, rows):
    for i, r in enumerate(rows, start=1):
        r["id"] = f"{prefixe}-{i:05d}"
    rows = [{"id": r["id"], **{k: v for k, v in r.items() if k != "id"}} for r in rows]
    (sortie / f"{nom}.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(nom, len(rows), "unités")

# --- service-public, filtre souple ---
vus = deja("data/unites/service_public.jsonl", "data/pilote/regles_20.jsonl", "data/lot2/regles_200.jsonl")
chunks = pq.read_table(sp_parquet, columns=["doc_id", "title", "theme", "text", "url"]).to_pylist()
par_doc, rows = {}, []
for c in chunks:
    t = c["text"] or ""
    k = norm(f"{c['title']}\n{t}")
    if 200 <= len(t) <= 3000 and len(val.findall(t)) >= 1 and len(cond.findall(t)) >= 2 and k not in vus and par_doc.get(c["doc_id"], 0) < 4:
        par_doc[c["doc_id"]] = par_doc.get(c["doc_id"], 0) + 1
        vus.add(k)
        theme = (c["theme"] or "divers").split(",")[0].strip()
        rows.append({"type": "service_public_2", "domaine": theme, "article": c["title"], "id_legifrance": None, "source": c["url"],
                     "texte_loi": f"{c['title']}\n{t}".strip(), "code_catala": "",
                     "licence_source": "Licence Ouverte 2.0 (Etalab)", "redistribuable": True})
rows.sort(key=lambda r: r["source"])
ecrire("service_public_2", "S2", rows)

# --- LEGI, filtre souple, tous les codes téléchargés ---
vus = deja("data/unites/legi.jsonl", "data/pilote/regles_20.jsonl", "data/lot2/regles_200.jsonl")
rows = []
for f in sorted(dossier.glob("*.parquet")):
    try:
        t = pq.read_table(f, columns=["doc_id", "status", "title", "number", "text"]).to_pylist()
    except Exception as e:  # noqa: BLE001
        print("illisible", f.name, e); continue
    cands = []
    for r in t:
        x = r["text"] or ""
        if (r["status"] == "VIGUEUR" and 200 <= len(x) <= 2500 and len(val.findall(x)) >= 1
                and len(cond.findall(x)) >= 1 and norm(x) not in vus):
            vus.add(norm(x))
            cands.append(r)
    cands.sort(key=lambda r: r["doc_id"])
    choisis = cands[::max(1, len(cands) // plafond)][:plafond]
    print(f.stem, len(cands), "->", len(choisis))
    for r in choisis:
        rows.append({"type": "legi_2", "domaine": r["title"] or f.stem, "article": f"Article {r['number']}", "id_legifrance": r["doc_id"],
                     "source": f"https://www.legifrance.gouv.fr/codes/article_lc/{r['doc_id']}",
                     "texte_loi": f"{r['title']} — Article {r['number']}\n{r['text']}".strip(), "code_catala": "",
                     "licence_source": "Licence Ouverte 2.0 (DILA / Etalab)", "redistribuable": True})
ecrire("legi_2", "L2", rows)
