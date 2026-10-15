"""Évaluation par génération : le modèle écrit le Gherkin de chaque paire d'évaluation, puis on mesure
la qualité de sa sortie (contrôles de `quality.py`) et sa proximité avec la référence (chrF)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from statistics import mean

from .data import Pair
from .generation import GenerationParams, generate
from .prompts import build_prompt_messages
from .quality import SCORE_WEIGHTS, analyze_gherkin, quality_score, score_components

log = logging.getLogger(__name__)

try:  # chrF : complément facultatif, la mesure principale reste le score de qualité
    from sacrebleu.metrics import CHRF

    _CHRF = CHRF()
except ImportError:  # pragma: no cover
    _CHRF = None


def score_prediction(pair: Pair, prediction: str, finished: bool, expected_language: str | None) -> dict:
    a = analyze_gherkin(prediction, pair.id, pair.specification, expected_language)
    ref = analyze_gherkin(pair.gherkin, pair.id, pair.specification, expected_language)
    row = {
        "id": pair.id,
        "group": pair.group,
        "score": quality_score(a, pair.id),
        "score_reference": quality_score(ref, pair.id),
        "criteres": score_components(a, pair.id),
        "termine": finished,
        "analyse": a.to_dict(),
        "scenarios_reference": ref.n_scenarios,
        "prediction": prediction,
        "reference": pair.gherkin,
        "specification": pair.specification,
    }
    if _CHRF is not None:
        row["chrf"] = round(_CHRF.sentence_score(prediction, [pair.gherkin]).score, 2)
    return row


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    n = len(rows)

    def rate(pred) -> float:
        return round(sum(1 for r in rows if pred(r)) / n, 4)

    numbers_total = sum(r["analyse"]["numbers_total"] for r in rows)
    metrics = {
        "n": n,
        "score_qualite": round(mean(r["score"] for r in rows), 4),
        "score_reference": round(mean(r["score_reference"] for r in rows), 4),
        "syntaxe_ok": rate(lambda r: r["analyse"]["syntax_ok"]),
        "langue_ok": rate(lambda r: r["analyse"]["language_ok"]),
        "tronque": rate(lambda r: not r["termine"]),
        "bloc_markdown": rate(lambda r: r["analyse"]["has_markdown_fence"]),
        "scenarios_moyens": round(mean(r["analyse"]["n_scenarios"] for r in rows), 2),
        "scenarios_reference": round(mean(r["scenarios_reference"] for r in rows), 2),
        "plusieurs_quand": rate(lambda r: r["analyse"]["multi_action_scenarios"] > 0),
        "chiffres_ancres": round(sum(r["analyse"]["numbers_grounded"] for r in rows) / numbers_total, 4)
        if numbers_total
        else None,
    }
    for key in SCORE_WEIGHTS:
        metrics[f"critere_{key}"] = round(mean(r["criteres"][key] for r in rows), 4)
    if _CHRF is not None:
        metrics["chrf"] = round(
            _CHRF.corpus_score([r["prediction"] for r in rows], [[r["reference"] for r in rows]]).score, 2
        )
    return metrics


def predict(model, tokenizer, pairs: list[Pair], system_prompt: str, user_template: str | None, params: GenerationParams):
    conversations = [build_prompt_messages(p.id, p.specification, system_prompt, user_template) for p in pairs]
    return generate(model, tokenizer, conversations, params)


def evaluate_pairs(
    model,
    tokenizer,
    pairs: list[Pair],
    system_prompt: str,
    user_template: str | None,
    params: GenerationParams,
    expected_language: str | None = "fr",
    out_dir: str | Path | None = None,
    label: str = "",
) -> dict:
    log.info("Évaluation par génération sur %d paires...", len(pairs))
    outputs = predict(model, tokenizer, pairs, system_prompt, user_template, params)
    rows = [score_prediction(p, text, done, expected_language) for p, (text, done) in zip(pairs, outputs)]
    metrics = aggregate(rows)
    metrics["label"] = label
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "predictions.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "rapport.md").write_text(render_report(metrics, rows), encoding="utf-8")
        log.info("Résultats écrits dans %s", out)
    return metrics


def probe(model, tokenizer, pairs: list[Pair], system_prompt: str, user_template: str | None,
          params: GenerationParams, expected_language: str | None) -> dict:
    """Mesure courte pendant l'entraînement (sous-ensemble des paires d'évaluation)."""
    outputs = predict(model, tokenizer, pairs, system_prompt, user_template, params)
    rows = [score_prediction(p, text, done, expected_language) for p, (text, done) in zip(pairs, outputs)]
    m = aggregate(rows)
    return {k: m[k] for k in ("score_qualite", "syntaxe_ok", "tronque", "critere_limite", "critere_negatif")}


METRIC_LABELS = {
    "n": "Paires évaluées",
    "score_qualite": "Score qualité moyen (0-1)",
    "score_reference": "Score qualité des références",
    "syntaxe_ok": "Syntaxe valide (parseur officiel)",
    "langue_ok": "Langue attendue",
    "tronque": "Sorties tronquées (max_new_tokens atteint)",
    "bloc_markdown": "Sorties entourées d'un bloc markdown",
    "scenarios_moyens": "Scénarios par sortie",
    "scenarios_reference": "Scénarios par référence",
    "plusieurs_quand": "Sorties avec un scénario à plusieurs Quand",
    "chiffres_ancres": "Nombres présents dans la spécification",
    "critere_tag_regle": "Critère : tag de règle sur les scénarios",
    "critere_nominal": "Critère : cas @nominal",
    "critere_limite": "Critère : cas @limite",
    "critere_negatif": "Critère : cas @négatif",
    "critere_structure": "Critère : ordre Étant donné / Quand / Alors",
    "critere_plans": "Critère : cohérence des plans de scénario",
    "critere_volume": "Critère : au moins 3 scénarios",
    "chrf": "chrF vs référence (corpus)",
}


def render_report(metrics: dict, rows: list[dict], worst: int = 10) -> str:
    lines = [f"# Évaluation {metrics.get('label', '')}".rstrip(), "", "| Mesure | Valeur |", "|---|---|"]
    for key, label in METRIC_LABELS.items():
        if key in metrics and metrics[key] is not None:
            lines.append(f"| {label} | {metrics[key]} |")
    lines += ["", f"## Les {min(worst, len(rows))} sorties les plus faibles", ""]
    for r in sorted(rows, key=lambda r: r["score"])[:worst]:
        a = r["analyse"]
        problems = []
        if not a["syntax_ok"]:
            problems.append(f"syntaxe : {a['error']}")
        elif not a["language_ok"]:
            problems.append(f"langue : {a['language']}")
        missing = [t for t in ("nominal", "limite", "negatif") if t not in a["case_types"]]
        if a["syntax_ok"] and missing:
            problems.append("types absents : " + ", ".join(missing))
        problems += a["structure_errors"][:3] + a["outline_errors"][:3]
        if not r["termine"]:
            problems.append("sortie tronquée")
        lines.append(f"- **{r['id']}** (score {r['score']}, référence {r['score_reference']}) : "
                     + ("; ".join(problems) or "—"))
    return "\n".join(lines) + "\n"


def compare(metric_files: list[str]) -> str:
    """Tableau comparatif de plusieurs metrics.json (ex. modèle de base vs modèle affiné)."""
    runs = [json.loads(Path(f).read_text(encoding="utf-8")) for f in metric_files]
    names = [r.get("label") or Path(f).parent.name for r, f in zip(runs, metric_files)]
    lines = ["| Mesure | " + " | ".join(names) + " |", "|---|" + "---|" * len(runs)]
    for key, label in METRIC_LABELS.items():
        if any(key in r for r in runs):
            lines.append(f"| {label} | " + " | ".join(str(r.get(key, "")) for r in runs) + " |")
    return "\n".join(lines) + "\n"
