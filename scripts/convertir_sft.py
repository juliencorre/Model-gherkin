#!/usr/bin/env python3
"""Convertit le corpus en jeu d'affinage supervisé (instruction -> réponse) : data/sft/{train,val,test}.jsonl.

Usage: convertir_sft.py [--prive]
- Entrée : data/corpus/{train,val,test}.jsonl (sources redistribuables) ; avec --prive : data/corpus_prive/ (toutes les sources,
  sortie dans data/sft_prive/, non versionnée).
- Les paires de niveau D (a_relire) ne sont jamais converties.
- Les tags d'identifiant d'unité (@SP-00012, @RG-21, ...) et les mentions « (RG-01) » sont retirés du Gherkin : ils sont
  des artefacts de production que le modèle ne doit pas apprendre à recopier. Les tags @nominal, @limite, @négatif sont conservés.
- Le Gherkin converti est revalidé avec le parseur officiel (langue fr, au moins 2 scénarios) ; une paire qui échoue est écartée.
Format de sortie : {"id", "messages": [system, user, assistant], "meta": {...}}.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser

RACINE = Path(__file__).resolve().parents[1]
PRIVE = "--prive" in sys.argv
ENTREE = RACINE / ("data/corpus_prive" if PRIVE else "data/corpus")
SORTIE = RACINE / ("data/sft_prive" if PRIVE else "data/sft")

SYSTEME = (
    "Tu es un expert en tests d'acceptation (BDD) pour les systèmes d'information de l'administration française. "
    "À partir d'une spécification contenant des règles de gestion, tu rédiges des scénarios Gherkin en français, "
    "fidèles à la spécification : tu n'inventes ni règle, ni montant, ni délai. "
    "Chaque scénario est précédé d'un tag @nominal, @limite (borne) ou @négatif (refus, exclusion, hors périmètre). "
    "Tu utilises « Plan du scénario » avec « Exemples » pour les variantes de valeurs."
)
CONSIGNE = "Spécification :\n{spec}\n\nRédige le fichier Gherkin (en français) qui teste cette spécification."

TAG_ID = re.compile(r"@(?:RG|SP|S2|LG|L2|CA|PU|OF|CD|AJ)-\d+\b")
MENTION_ID = re.compile(r"\s*\((?:RG|SP|S2|LG|L2|CA|PU|OF|CD|AJ)-\d+\)")


def nettoyer(gherkin: str) -> str:
    g = MENTION_ID.sub("", gherkin)
    lignes = []
    for ligne in g.split("\n"):
        if TAG_ID.search(ligne):
            indentation = re.match(r"\s*", ligne).group(0)
            reste = re.sub(r"\s+", " ", TAG_ID.sub("", ligne.strip())).strip()
            if not reste:
                continue  # la ligne ne contenait que le tag d'identifiant
            ligne = indentation + reste
        lignes.append(ligne.rstrip())
    # Indentation des lignes de tags : alignée sur la ligne qui suit (Scénario, Plan du scénario, Fonctionnalité...)
    for i, ligne in enumerate(lignes):
        if ligne.strip().startswith("@"):
            j = i + 1
            while j < len(lignes) and (not lignes[j].strip() or lignes[j].strip().startswith("@")):
                j += 1
            if j < len(lignes):
                lignes[i] = re.match(r"\s*", lignes[j]).group(0) + ligne.strip()
    g = "\n".join(lignes)
    return re.sub(r"\n{3,}", "\n\n", g).strip() + "\n"


ETAPE = re.compile(r"(?:Étant donné|Etant donné|Soit|Sachant|Quand|Lorsque|Alors|Donc|Et|Mais)\b")


def indenter(gherkin: str) -> str:
    """Indentation canonique : Fonctionnalité 0 ; Contexte, Scénario, Plan, Règle, tags 2 ; étapes et Exemples 4 ; tables 6."""
    sortie, vu_fonctionnalite = [], False
    for ligne in gherkin.split("\n"):
        t = ligne.strip()
        if not t:
            sortie.append("")
        elif t.startswith("# language"):
            sortie.append(t)
        elif t.startswith("Fonctionnalité"):
            vu_fonctionnalite = True
            sortie.append(t)
        elif t.startswith("@"):
            sortie.append(("  " if vu_fonctionnalite else "") + t)
        elif re.match(r"(?:Contexte|Scénario|Plan du scénario|Règle|Exemple)\s*:", t):
            sortie.append("  " + t)
        elif re.match(r"Exemples\s*:", t):
            sortie.append("    " + t)
        elif t.startswith("|"):
            sortie.append("      " + t)
        elif ETAPE.match(t):
            sortie.append("    " + t)
        else:
            sortie.append(ligne.rstrip())  # description libre : inchangée
    return "\n".join(sortie)


def valide(gherkin: str):
    try:
        doc = Parser().parse(gherkin)
    except CompositeParserException as e:
        return None, "syntaxe: " + "; ".join(x.args[0].splitlines()[0] for x in e.errors)[:120]
    except Exception as e:  # noqa: BLE001
        return None, "syntaxe: " + str(e).splitlines()[0][:120]
    f = doc.get("feature")
    if not f or f.get("language") != "fr":
        return None, "langue ≠ fr"
    sc = [c["scenario"] for c in f["children"] if c.get("scenario")]
    if len(sc) < 2:
        return None, "moins de 2 scénarios"
    etiquettes = {t["name"] for s in sc for t in s.get("tags", [])}
    if "@nominal" not in etiquettes:
        return None, "@nominal absent après nettoyage"
    if re.search(r"@(?:RG|SP|S2|LG|L2|CA|PU|OF|CD|AJ)-\d+", gherkin):
        return None, "tag d'identifiant résiduel"
    return len(sc), ""


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    bilan = {}
    for split in ("train", "val", "test"):
        entree = ENTREE / f"{split}.jsonl"
        if not entree.exists():
            continue
        ecrites, ecartees = 0, Counter()
        sources = Counter()
        with open(SORTIE / f"{split}.jsonl", "w", encoding="utf-8") as sortie:
            for ligne in open(entree, encoding="utf-8"):
                p = json.loads(ligne)
                if p["niveau"] == "D":
                    ecartees["niveau D"] += 1
                    continue
                g = indenter(nettoyer(p["gherkin"]))
                n, err = valide(g)
                if err:
                    ecartees[err.split(":")[0]] += 1
                    continue
                spec = p["specification"].strip()
                sortie.write(json.dumps({
                    "id": p["id"],
                    "messages": [
                        {"role": "system", "content": SYSTEME},
                        {"role": "user", "content": CONSIGNE.format(spec=spec)},
                        {"role": "assistant", "content": g},
                    ],
                    "meta": {"source_type": p["source_type"], "domaine": p["domaine"], "niveau": p["niveau"],
                             "licence_source": p["licence_source"], "scenarios": n},
                }, ensure_ascii=False) + "\n")
                ecrites += 1
                sources[p["source_type"]] += 1
        bilan[split] = {"paires": ecrites, "ecartees": dict(ecartees), "par_source": dict(sources)}
    (SORTIE / "STATS.json").write_text(json.dumps(bilan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(bilan, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
