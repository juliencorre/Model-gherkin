#!/usr/bin/env python3
"""Valide les paires (specification, gherkin) avec le parseur officiel cucumber/gherkin.

Usage: valider_gherkin.py <fichier.jsonl>...
Contrôles : syntaxe (parseur officiel, langue fr), langue déclarée, tag de règle présent,
nombre de scénarios, présence d'un cas négatif et d'un cas limite.
Code de sortie 1 si au moins une paire est invalide.
"""
import json
import re
import sys

from gherkin.parser import Parser
from gherkin.errors import CompositeParserException


def analyser(gherkin: str, rid: str) -> dict:
    res = {"syntaxe_ok": False, "erreur": "", "scenarios": 0, "tags": set()}
    try:
        doc = Parser().parse(gherkin)
    except CompositeParserException as e:
        res["erreur"] = "; ".join(x.args[0].splitlines()[0] for x in e.errors)[:300]
        return res
    except Exception as e:  # noqa: BLE001
        res["erreur"] = str(e).splitlines()[0][:300]
        return res
    feature = doc.get("feature")
    if not feature:
        res["erreur"] = "aucune fonctionnalité"
        return res
    res["syntaxe_ok"] = feature.get("language") == "fr"
    if not res["syntaxe_ok"]:
        res["erreur"] = f"langue = {feature.get('language')}"
    for child in feature["children"]:
        sc = child.get("scenario")
        if sc:
            res["scenarios"] += 1
            res["tags"].update(t["name"] for t in sc.get("tags", []))
    return res


def main(paths):
    total = ok = 0
    for path in paths:
        for ligne in open(path, encoding="utf-8"):
            r = json.loads(ligne)
            total += 1
            a = analyser(r["gherkin"], r["id"])
            problemes = []
            if not a["syntaxe_ok"]:
                problemes.append("syntaxe: " + a["erreur"])
            else:
                if f"@{r['id']}" not in a["tags"]:
                    problemes.append(f"tag @{r['id']} absent")
                if a["scenarios"] < 3:
                    problemes.append(f"{a['scenarios']} scénario(s) (<3)")
                for t in ("@négatif", "@limite", "@nominal"):
                    if t not in a["tags"]:
                        problemes.append(f"{t} absent")
            if not r.get("specification", "").strip():
                problemes.append("spécification vide")
            statut = "OK " if not problemes else "KO "
            ok += not problemes
            print(f"{statut}{r['id']} scénarios={a['scenarios']} {'; '.join(problemes)}")
    print(f"\n{ok}/{total} paires valides")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
