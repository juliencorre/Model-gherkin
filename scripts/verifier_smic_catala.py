#!/usr/bin/env python3
"""Vérifie avec le compilateur Catala les montants du SMIC annoncés par les scénarios Gherkin RG-01..RG-06.

Usage: verifier_smic_catala.py <répertoire catala-examples (copie de travail)> <fichier.jsonl>... [--rapport sortie.json]
Prérequis: environnement opam avec catala 1.3.0 (clerk dans le PATH).
Pour chaque scénario non négatif, chaque ligne d'exemples est développée en cas concret
(date, résidence, montant attendu). Le cas est exécuté dans Catala (scope Smic.Smic) et comparé.
"""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from gherkin.parser import Parser

MOIS = {m: i + 1 for i, m in enumerate(
    "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split())}
RESIDENCES = [  # (motif, valeur de l'énumération France.Collectivité)
    ("saint-pierre-et-miquelon", "SaintPierreEtMiquelon"), ("saint-barthélemy", "SaintBarthélemy"),
    ("saint-martin", "SaintMartin"), ("guadeloupe", "Guadeloupe"), ("guyane", "Guyane"),
    ("martinique", "Martinique"), ("la réunion", "LaRéunion"), ("mayotte", "Mayotte"),
    ("métropole", "Métropole"),
]
IDS = {f"RG-{i:02d}" for i in range(1, 7)}


def norm(t):
    return unicodedata.normalize("NFC", t).lower()


def trouver_date(t):
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", t)
    if m:
        return f"{m[3]}-{m[2]}-{m[1]}"
    m = re.search(r"\b(1er|\d{1,2}) (" + "|".join(MOIS) + r") (\d{4})\b", norm(t))
    if m:
        return f"{m[3]}-{MOIS[m[2]]:02d}-{1 if m[1] == '1er' else int(m[1]):02d}"
    return None


def trouver_residence(t):
    t = norm(t)
    for motif, valeur in RESIDENCES:
        if motif in t:
            return valeur
    return None


def cas_concrets(rid, gherkin):
    doc = Parser().parse(gherkin)
    for child in doc["feature"]["children"]:
        sc = child.get("scenario")
        if not sc:
            continue
        tags = {t["name"] for t in sc["tags"]}
        if "@négatif" in tags:
            continue
        lignes = [{}]
        if sc.get("examples"):
            lignes = []
            for ex in sc["examples"]:
                cols = [c["value"] for c in ex["tableHeader"]["cells"]]
                for row in ex["tableBody"]:
                    lignes.append(dict(zip(cols, [c["value"] for c in row["cells"]])))
        for ligne in lignes:
            steps = []
            for s in sc["steps"]:
                txt = s["text"]
                for k, v in ligne.items():
                    txt = txt.replace(f"<{k}>", v)
                steps.append((s["keyword"].strip(), txt))
            donnees = " ".join(t for k, t in steps if k != "Alors")
            alors = " ".join(t for k, t in steps if k == "Alors")
            montant = re.search(r"(\d+(?:,\d+)?) ?€", alors)
            yield {"id": rid, "scenario": sc["name"], "date": trouver_date(donnees),
                   "residence": trouver_residence(donnees),
                   "attendu": montant[1] if montant else None}


def main():
    args = sys.argv[1:]
    rapport = None
    if "--rapport" in args:
        i = args.index("--rapport")
        rapport = Path(args[i + 1])
        del args[i:i + 2]
    work, fichiers = Path(args[0]), args[1:]

    cas = []
    for f in fichiers:
        for ligne in open(f, encoding="utf-8"):
            r = json.loads(ligne)
            if r["id"] in IDS:
                cas.extend(cas_concrets(r["id"], r["gherkin"]))
    exec_ = [c for c in cas if c["date"] and c["residence"] and c["attendu"]]
    ignores = [c for c in cas if c not in exec_]

    scopes = ["> Usage de France", "> Usage de Smic", "", "# Vérification", "", "```catala",
              "#[test]", "déclaration champ d'application Grille:"]
    for i in range(len(exec_)):
        scopes += [f"  s{i} champ d'application Smic.Smic", f"  résultat m{i} contenu argent"]
    scopes += ["", "champ d'application Grille:"]
    for i, c in enumerate(exec_):
        scopes += [f"  définition s{i}.date_courante égal à |{c['date']}|",
                   f"  définition s{i}.résidence égal à France.Collectivité.{c['residence']}",
                   f"  définition m{i} égal à s{i}.brut_horaire"]
    scopes.append("```")
    (work / "verif").mkdir(exist_ok=True)
    (work / "verif" / "verif_smic.catala_fr").write_text("\n".join(scopes), encoding="utf-8")

    sortie = subprocess.run(["clerk", "run", "verif/verif_smic.catala_fr", "-s", "Grille"],
                            cwd=work, capture_output=True, text=True)
    texte = sortie.stdout + sortie.stderr
    valeurs = {}
    for m in re.finditer(r"│ m(\d+) = ([^\n]+)", texte):
        valeurs[int(m[1])] = m[2].strip()
    if not valeurs:
        print(texte[-3000:])
        sys.exit("aucun résultat Catala lu")

    def en_nombre(s):
        s = s.replace(" ", "").replace("\xa0", "").replace(" ", "")
        m = re.search(r"\d+(?:[.,]\d+)?", s)
        return float(m[0].replace(",", ".")) if m else None

    ok = ko = 0
    detail = []
    for i, c in enumerate(exec_):
        calc = valeurs.get(i)
        bon = calc is not None and en_nombre(calc) == en_nombre(c["attendu"])
        ok += bon
        ko += not bon
        detail.append({**c, "catala": calc, "conforme": bon})
        if not bon:
            print(f"KO {c['id']} {c['date']} {c['residence']}: Gherkin {c['attendu']} €, Catala {calc}")
    print(f"{ok} cas conformes, {ko} écarts, {len(ignores)} cas ignorés (date, résidence ou montant introuvable)")
    for c in ignores:
        print("ignoré", c)
    if rapport:
        rapport.write_text(json.dumps({"conformes": ok, "ecarts": ko, "ignores": len(ignores),
                                       "detail": detail}, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
