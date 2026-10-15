#!/usr/bin/env python3
"""Extrait 200 règles supplémentaires (hors pilote) depuis sources/regles-as-code.

Usage: extraire_regles_lot2.py <dossier regles-as-code> <regles_20.jsonl> <sortie.jsonl>
- Catala (90): article de loi + code Catala, mêmes filtres que le pilote, dédoublonnés,
  hors règles du pilote ; plafonds par domaine pour éviter la surreprésentation des aides au logement.
- Publicodes mon-entreprise (110): règle YAML avec description et calcul.
Sélection déterministe (échantillon régulier trié par fichier).
"""
import glob, json, re, sys
from pathlib import Path

base, pilote, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
norm = lambda t: re.sub(r"\W+", " ", t).lower()
deja = {norm(json.loads(l)["texte_loi"]) for l in open(pilote, encoding="utf-8")}

HEAD = re.compile(r"^###+ (Article .*?)\s*(?:\|\s*(\S+))?\s*$", re.M)
BLOCK = re.compile(r"```catala\n(.*?)```", re.S)
catala = {}
for f in sorted(glob.glob(str(base / "catala-examples/**/*.catala_fr"), recursive=True)):
    if "/tests/" in f:
        continue
    rel = Path(f).relative_to(base / "catala-examples")
    domaine = rel.parts[0]
    t = Path(f).read_text(encoding="utf-8")
    hs = list(HEAD.finditer(t))
    for i, h in enumerate(hs):
        body = t[h.end(): hs[i + 1].start() if i + 1 < len(hs) else len(t)]
        code = BLOCK.findall(body)
        prose = re.sub(r"^#+ .*$", "", BLOCK.sub("", body), flags=re.M).strip()
        if code and 150 <= len(prose) <= 2200 and 100 <= sum(map(len, code)) <= 3000:
            k = norm(prose)
            if k in deja or any(k == norm(u["texte_loi"]) for us in catala.values() for u in us):
                continue
            catala.setdefault(domaine, []).append({
                "type": "catala", "domaine": domaine, "article": h.group(1).strip(),
                "id_legifrance": h.group(2), "source": str(rel), "texte_loi": prose,
                "code_catala": "\n".join(c.strip() for c in code)})

QUOTA_CATALA = {"allocations_familiales": 16, "smic": 4, "droit_successions": 3, "aides_logement": 67}
rows = []
for dom, n in QUOTA_CATALA.items():
    c = catala.get(dom, [])
    step = max(1, len(c) // n)
    rows += c[::step][:n]

pub = {}
for f in sorted(glob.glob(str(base / "mon-entreprise/**/*.publicodes"), recursive=True)):
    rel = Path(f).relative_to(base / "mon-entreprise")
    domaine = rel.parts[0]
    t = Path(f).read_text(encoding="utf-8")
    for b in re.split(r"\n(?=[^\s#][^\n]*:\s*\n)", t):
        if (re.search(r"^\s+(description|note):", b, re.M)
                and re.search(r"^\s+(valeur|formule|somme|produit|variations|applicable si|non applicable si|taux|barème|plafond)", b, re.M)
                and 150 <= len(b) <= 2500):
            pub.setdefault(domaine, []).append({
                "type": "publicodes", "domaine": domaine, "article": b.split(":", 1)[0].strip(),
                "id_legifrance": None, "source": str(rel), "texte_loi": b.strip(), "code_catala": ""})
QUOTA_PUB = {"modele-social": 65, "modele-ti": 25, "modele-as": 15, "modele-commun": 10}
for dom, n in QUOTA_PUB.items():
    c = pub.get(dom, [])
    step = max(1, len(c) // n)
    rows += c[::step][:n]

for i, r in enumerate(rows, start=21):
    r["id"] = f"RG-{i}"
rows = [{"id": r["id"], **{k: v for k, v in r.items() if k != "id"}} for r in rows]
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
import collections
print(len(rows), "règles;", dict(collections.Counter((r["type"], r["domaine"]) for r in rows)))
