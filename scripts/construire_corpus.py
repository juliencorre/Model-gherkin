#!/usr/bin/env python3
"""Construit le corpus d'entraînement (data/corpus/) à partir des lots de paires générées.

Usage: construire_corpus.py [--racine /home/user/Model-gherkin]

Entrées (déclarées dans LOTS) : fichiers de règles (id, type, domaine, texte_loi, ...) et fichiers de
paires (id, specification, gherkin, notes). Sortie :
  data/corpus/pairs/<lot>.jsonl   toutes les paires enrichies (métadonnées, contrôles, niveau)
  data/corpus/train.jsonl, val.jsonl, test.jsonl   découpage par groupe de source (jamais par scénario)
  data/corpus/STATS.json          comptages par source, niveau, licence, contrôle
  data/corpus/rejets.jsonl        paires écartées et motif

Niveaux de qualité :
  A  valeurs attendues vérifiées par un moteur exécutable (Catala, tests OpenFisca/Publicodes) ;
  B  contrôles automatiques passés : syntaxe, tags, tous les nombres traçables à la source (ou déclarés fictifs) ;
  D  résultats attendus non vérifiables automatiquement (à relire) : conservées, hors entraînement par défaut ;
  C  texte seul (aucune exécution possible) : contrôles automatiques passés, sans vérification de valeur.
"""
import glob
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser

RACINE = Path(sys.argv[sys.argv.index("--racine") + 1]) if "--racine" in sys.argv else Path(__file__).resolve().parents[1]

# (nom du lot, fichier de règles, motif des fichiers de paires, métadonnées par type de source)
LOTS = [
    ("pilote", "data/pilote/regles_20.jsonl", "data/pilote/gherkin_fr_lot?.jsonl"),
    ("lot2", "data/lot2/regles_200.jsonl", "data/lot2/gherkin_fr_lot?.jsonl"),
]
# Les lots suivants ajoutent leurs entrées ici ou via data/corpus/lots_supplementaires.json
extra = RACINE / "data/corpus/lots_supplementaires.json"
if extra.exists():
    LOTS += [tuple(x) for x in json.loads(extra.read_text(encoding="utf-8"))]

LICENCES = {  # (type de source, domaine) -> (licence de la source, redistribuable)
    "catala": ("Apache-2.0", True),
    "publicodes": ("MIT", True),
}
# Niveau A : ids dont les valeurs ont été vérifiées par exécution (rapports de vérification).
VERIFIES = set()
for rapport in glob.glob(str(RACINE / "data/**/verification_*.json"), recursive=True):
    for d in json.loads(Path(rapport).read_text(encoding="utf-8")).get("detail", []):
        if d.get("conforme"):
            VERIFIES.add(d["id"])


def valeurs(t):
    """Nombres du texte, en flottants (« 10 000,5 » -> 10000.5). Les chiffres des dates sont lus à part."""
    t = t.replace("\u202f", " ").replace("\xa0", " ")
    out = set()
    for m in re.finditer(r"\d+(?: \d{3})*(?:[,.]\d+)?", t):
        out.add(float(m[0].replace(" ", "").replace(",", ".")))
    return out


def derivable(n, base):
    """Vrai si n est une année voisine d'une année de la source, ou s'il se déduit de deux nombres
    de la source par une opération simple (a+k*b, a-k*b, a*k, a*b, a*b/100, a/b) avec k entier 1..12."""
    if 1900 <= n <= 2100 and any(1900 <= b <= 2100 and abs(n - b) <= 2 for b in base):
        return True
    tol = 0.011
    for a in base:
        for b in base:
            cands = [a + b, a - b, a * b, a * b / 100]
            if b:
                cands.append(a / b)
            cands += [a + k * b for k in range(1, 13)] + [a - k * b for k in range(1, 13)]
            cands += [a * k for k in range(1, 13)]
            if any(abs(n - c) <= tol for c in cands):
                return True
    return False


def analyser(gherkin):
    try:
        doc = Parser().parse(gherkin)
    except CompositeParserException as e:
        return None, "syntaxe: " + "; ".join(x.args[0].splitlines()[0] for x in e.errors)[:200]
    except Exception as e:  # noqa: BLE001
        return None, "syntaxe: " + str(e).splitlines()[0][:200]
    f = doc.get("feature")
    if not f or f.get("language") != "fr":
        return None, "langue ≠ fr"
    scen, tags, scenarios = 0, set(), []
    for c in f["children"]:
        s = c.get("scenario")
        if s:
            scen += 1
            tags |= {t["name"] for t in s.get("tags", [])}
            scenarios.append(s)
    return {"scenarios": scen, "tags": tags, "liste": scenarios}, ""


def sorties_non_verifiees(scenarios, base):
    """Nombres des résultats attendus (étapes « Alors » et colonnes d'exemples qui les alimentent)
    qui ne se déduisent ni de la source, ni des données d'entrée du même scénario."""
    suspects = set()
    for sc in scenarios:
        entrees, sorties, type_courant = [], [], None
        cols_sortie = set()
        for st in sc["steps"]:
            kt = st.get("keywordType")
            if kt in ("Context", "Action", "Outcome"):
                type_courant = kt
            (sorties if type_courant == "Outcome" else entrees).append(st["text"])
            if type_courant == "Outcome":
                cols_sortie |= set(re.findall(r"<([^>]+)>", st["text"]))
        nums_in, nums_out = set(), set()
        for t in entrees:
            nums_in |= valeurs(re.sub(r"<[^>]+>", " ", t))
        for t in sorties:
            nums_out |= valeurs(re.sub(r"<[^>]+>", " ", t))
        for ex in sc.get("examples", []):
            cols = [c["value"] for c in ex["tableHeader"]["cells"]]
            for row in ex["tableBody"]:
                for col, cell in zip(cols, row["cells"]):
                    (nums_out if col in cols_sortie else nums_in).update(valeurs(cell["value"]))
        pool = set(base) | nums_in
        for n in nums_out:
            if n > 20 and n not in pool and not derivable(n, pool):
                suspects.add(n)
    return sorted(suspects)


def controler(pid, regle, paire):
    """Retourne (controles, motif_rejet)."""
    g, notes, spec = paire["gherkin"], paire.get("notes", "") or "", paire.get("specification", "")
    info, err = analyser(g)
    if err:
        return None, err
    if not spec.strip():
        return None, "spécification vide"
    if f"@{pid}" not in info["tags"]:
        return None, f"tag @{pid} absent"
    if "@nominal" not in info["tags"] or info["scenarios"] < 2:
        return None, "moins de 2 scénarios ou aucun @nominal"
    if re.search(r"\b(Given|When|Then|Scenario|Feature)\b", g):
        return None, "mot-clé anglais"
    source = regle["texte_loi"] + " " + regle.get("code_catala", "") + " " + spec
    base = valeurs(source)
    hors = sorties_non_verifiees(info["liste"], base)
    tracable = not hors
    return {
        "syntaxe_ok": True,
        "scenarios": info["scenarios"],
        "a_limite": "@limite" in info["tags"],
        "a_negatif": "@négatif" in info["tags"],
        "sorties_non_verifiees": hors[:15],
        "valeurs_tracables": tracable,
    }, ""


def niveau(nom, pid, regle, ctl):
    if not ctl["valeurs_tracables"]:
        return "D"  # résultats attendus non vérifiables : conservée, exclue de l'entraînement par défaut
    if nom == "pilote" and pid in VERIFIES:  # rapports de vérification Catala du pilote (RG-01..06)
        return "A"
    return "C" if regle["type"] in ("service_public",) else "B"


def groupe(regle):
    return f"{regle['type']}:{regle['domaine']}:{regle.get('source', '')}"


def main():
    sortie = RACINE / "data/corpus"
    (sortie / "pairs").mkdir(parents=True, exist_ok=True)
    rejets, vus_spec, toutes = [], set(), []
    for nom, f_regles, motif in LOTS:
        regles = {}
        for l in open(RACINE / f_regles, encoding="utf-8"):
            r = json.loads(l)
            r.setdefault("type", "catala")
            regles[r["id"]] = r
        paires = []
        for fp in sorted(glob.glob(str(RACINE / motif))):
            for l in open(fp, encoding="utf-8"):
                p = json.loads(l)
                r = regles.get(p["id"])
                if not r:
                    rejets.append({"lot": nom, "id": p["id"], "motif": "règle source inconnue"})
                    continue
                ctl, err = controler(p["id"], r, p)
                if err:
                    rejets.append({"lot": nom, "id": p["id"], "motif": err})
                    continue
                niv = niveau(nom, p["id"], r, ctl)
                cle = re.sub(r"\W+", " ", p["specification"]).lower()
                if cle in vus_spec:
                    rejets.append({"lot": nom, "id": p["id"], "motif": "spécification en double"})
                    continue
                vus_spec.add(cle)
                licence, redistrib = LICENCES.get(r["type"], r.get("licence", ("inconnue", False))
                                                  if isinstance(r.get("licence"), tuple) else ("inconnue", False))
                if r.get("licence_source"):
                    licence, redistrib = r["licence_source"], r.get("redistribuable", False)
                paires.append({
                    "id": f"{nom}-{p['id']}", "lot": nom, "langue": "fr",
                    "source_type": r["type"], "domaine": r["domaine"], "source": r.get("source", ""),
                    "reference": r.get("article", ""), "id_legifrance": r.get("id_legifrance"),
                    "licence_source": licence, "redistribuable": redistrib,
                    "specification": p["specification"], "gherkin": p["gherkin"], "notes": p.get("notes", ""),
                    "controles": ctl, "niveau": niv, "relu_humain": False,
                    "groupe": groupe(r),
                })
        with open(sortie / "pairs" / f"{nom}.jsonl", "w", encoding="utf-8") as fh:
            for p in paires:
                fh.write(json.dumps(p, ensure_ascii=False) + "\n")
        toutes += paires

    # Découpage par groupe de source : ~5 % des groupes en test, ~5 % en validation
    def tranche(g):
        h = int(hashlib.sha256(g.encode()).hexdigest(), 16) % 100
        return "test" if h < 5 else "val" if h < 10 else "train"

    parts = {"train": [], "val": [], "test": []}
    for p in toutes:
        p["split"] = tranche(p["groupe"]) if p["niveau"] != "D" else "a_relire"
        if p["split"] in parts:
            parts[p["split"]].append(p)
    for k, v in parts.items():
        with open(sortie / f"{k}.jsonl", "w", encoding="utf-8") as fh:
            for p in v:
                fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(sortie / "rejets.jsonl", "w", encoding="utf-8") as fh:
        for r in rejets:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = {
        "total": len(toutes), "rejets": len(rejets),
        "par_niveau": Counter(p["niveau"] for p in toutes),
        "par_source": Counter(p["source_type"] for p in toutes),
        "par_domaine": Counter(f"{p['source_type']}/{p['domaine']}" for p in toutes),
        "par_licence": Counter(p["licence_source"] for p in toutes),
        "redistribuables": sum(p["redistribuable"] for p in toutes),
        "par_split": {**{k: len(v) for k, v in parts.items()}, "a_relire": sum(p["niveau"] == "D" for p in toutes)},
        "scenarios_total": sum(p["controles"]["scenarios"] for p in toutes),
        "motifs_rejet": Counter(r["motif"].split(":")[0] for r in rejets),
    }
    (sortie / "STATS.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
