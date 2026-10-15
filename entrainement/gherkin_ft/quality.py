"""Contrôles qualité d'un texte Gherkin.

Les contrôles s'appuient sur le parseur officiel cucumber/gherkin (`gherkin-official`) et portent sur :
- la syntaxe et la langue (`# language: fr`) ;
- la présence du tag de la règle (`@RG-xx`) sur les scénarios (tags hérités compris) ;
- la couverture des types de cas : `@nominal`, `@limite`, `@négatif` ;
- la structure des étapes (au moins un Quand et un Alors, ordre Étant donné → Quand → Alors) ;
- la cohérence des plans de scénario (chaque `<paramètre>` a sa colonne dans `Exemples`, et inversement) ;
- l'ancrage des nombres : part des nombres du Gherkin présents dans la spécification (indicateur seulement).

Le score de qualité (`quality_score`) agrège ces contrôles entre 0 et 1. Il ne vérifie pas l'exactitude métier
des valeurs attendues : seule une relecture ou un oracle (Catala, OpenFisca...) le peut.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser

# `<résultat attendu>` est un paramètre, pas « < 100 et > » (comparaisons dans le texte d'une étape).
PLACEHOLDER_RE = re.compile(r"<([^<>\s](?:[^<>\n]*[^<>\s])?)>")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
THOUSANDS_RE = re.compile(r"(?<=\d)[   ](?=\d{3}(?!\d))")
FENCE_RE = re.compile(r"^\s*```[\w-]*[ \t]*\n(.*?)\n?```\s*$", re.S)

CASE_TYPES = ("nominal", "limite", "negatif")

# Poids des critères du score de qualité (somme = 1).
SCORE_WEIGHTS = {
    "tag_regle": 0.15,
    "nominal": 0.15,
    "limite": 0.15,
    "negatif": 0.15,
    "structure": 0.15,
    "plans": 0.15,
    "volume": 0.10,
}


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def normalize_tag(tag: str) -> str:
    """`@Négatif` -> `negatif` : minuscules, sans accent ni `@`."""
    return _strip_accents(tag.lstrip("@")).lower()


def strip_markdown_fence(text: str) -> tuple[str, bool]:
    """Retire un bloc ```gherkin ... ``` englobant. Renvoie (texte, bloc_présent)."""
    m = FENCE_RE.match(text)
    if m:
        return m.group(1), True
    return text, False


FEATURE_START_RE = re.compile(r"^\s*(?:@|Fonctionnalité\s*:|Caractéristique\s*:|Feature\s*:)", re.I)


def extract_gherkin(text: str, language: str | None = "fr") -> str:
    """Extrait le Gherkin d'une réponse bavarde : retire le bloc markdown et le texte avant le Gherkin.

    Si l'en-tête `# language:` manque, il est ajouté (sans lui, le parseur lit les mots-clés en anglais).
    Réservé à la commande `generate` : l'évaluation mesure la sortie brute du modèle."""
    text, _ = strip_markdown_fence(text.strip())
    if "```" in text:  # bloc au milieu d'un texte explicatif
        parts = text.split("```")
        if len(parts) >= 3:
            text = re.sub(r"^[\w-]*[ \t]*\n", "", parts[1])
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("# language:"):
            return "\n".join(lines[i:]).strip() + "\n"
    start = next((i for i, line in enumerate(lines) if FEATURE_START_RE.match(line)), 0)
    body = "\n".join(lines[start:]).strip()
    return (f"# language: {language}\n" if language else "") + body + "\n"


def _numbers(text: str) -> list[str]:
    text = THOUSANDS_RE.sub("", text)
    return [n.replace(",", ".") for n in NUMBER_RE.findall(text)]


@dataclass
class GherkinAnalysis:
    syntax_ok: bool = False
    error: str = ""
    language: str | None = None
    language_ok: bool = False
    has_markdown_fence: bool = False
    n_scenarios: int = 0
    n_outlines: int = 0
    n_example_rows: int = 0
    n_rules: int = 0
    has_background: bool = False
    rule_tag_on_feature: bool = False
    scenarios_with_rule_tag: int = 0
    scenarios_with_case_tag: int = 0
    case_types: list[str] = field(default_factory=list)
    outline_errors: list[str] = field(default_factory=list)
    structure_errors: list[str] = field(default_factory=list)
    scenarios_with_structure_error: int = 0
    multi_action_scenarios: int = 0
    max_steps: int = 0
    duplicate_names: int = 0
    numbers_total: int = 0
    numbers_grounded: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _iter_scenarios(feature: dict):
    """Renvoie (scénario, tags hérités, étapes du contexte) en descendant dans les `Règle:`."""
    feature_tags = [t["name"] for t in feature.get("tags", [])]
    feature_bg: list[dict] = []
    for child in feature.get("children", []):
        if "background" in child and child["background"]:
            feature_bg = child["background"].get("steps", [])
        elif "scenario" in child and child["scenario"]:
            yield child["scenario"], feature_tags, feature_bg
        elif "rule" in child and child["rule"]:
            rule = child["rule"]
            rule_tags = feature_tags + [t["name"] for t in rule.get("tags", [])]
            rule_bg = list(feature_bg)
            for sub in rule.get("children", []):
                if "background" in sub and sub["background"]:
                    rule_bg = feature_bg + sub["background"].get("steps", [])
                elif "scenario" in sub and sub["scenario"]:
                    yield sub["scenario"], rule_tags, rule_bg


def _check_structure(name: str, steps: list[dict], background: list[dict]) -> tuple[list[str], int]:
    """Contrôle l'ordre Contexte → Action → Résultat. Renvoie (erreurs, nombre d'actions)."""
    errors = []
    resolved = []
    previous = "Context" if background else None
    for step in steps:
        kind = step.get("keywordType", "Unknown")
        if kind in ("Conjunction", "Unknown"):
            kind = previous or "Context"
        resolved.append(kind)
        previous = kind
    n_actions = resolved.count("Action")
    if "Outcome" not in resolved:
        errors.append(f"« {name} » : aucune étape Alors")
    if "Action" not in resolved:
        errors.append(f"« {name} » : aucune étape Quand")
    seen_action = seen_outcome = False
    for kind in resolved:
        if kind == "Context" and (seen_action or seen_outcome):
            errors.append(f"« {name} » : étape Étant donné après Quand/Alors")
            break
        if kind == "Action" and seen_outcome:
            errors.append(f"« {name} » : étape Quand après Alors")
            break
        seen_action |= kind == "Action"
        seen_outcome |= kind == "Outcome"
    return errors, n_actions


def _step_texts(steps: list[dict]) -> list[str]:
    texts = []
    for step in steps:
        texts.append(step.get("text", ""))
        doc = step.get("docString")
        if doc:
            texts.append(doc.get("content", ""))
        table = step.get("dataTable")
        if table:
            texts.extend(cell["value"] for row in table.get("rows", []) for cell in row.get("cells", []))
    return texts


def _check_outline(scenario: dict) -> list[str]:
    name = scenario.get("name", "")
    used = set()
    for text in [name] + _step_texts(scenario.get("steps", [])):
        used.update(PLACEHOLDER_RE.findall(text))
    examples = scenario.get("examples", [])
    if not examples:
        return [f"« {name} » : paramètre(s) {sorted(used)} sans tableau Exemples"] if used else []
    errors = []
    for ex in examples:
        header = ex.get("tableHeader")
        if not header:
            errors.append(f"« {name} » : tableau Exemples sans en-tête")
            continue
        columns = {c["value"] for c in header.get("cells", [])}
        if not ex.get("tableBody"):
            errors.append(f"« {name} » : tableau Exemples sans ligne")
        missing = used - columns
        unused = columns - used
        if missing:
            errors.append(f"« {name} » : paramètre(s) {sorted(missing)} absent(s) des Exemples")
        if unused:
            errors.append(f"« {name} » : colonne(s) {sorted(unused)} inutilisée(s)")
    return errors


def analyze_gherkin(
    text: str,
    rule_id: str | None = None,
    specification: str | None = None,
    expected_language: str | None = "fr",
) -> GherkinAnalysis:
    """Analyse un texte Gherkin. `rule_id` (ex. `RG-01`) active le contrôle du tag de règle."""
    a = GherkinAnalysis()
    text, a.has_markdown_fence = strip_markdown_fence(text)
    try:
        doc = Parser().parse(text)
    except CompositeParserException as e:
        a.error = "; ".join(str(x).splitlines()[0] for x in e.errors)[:300]
        return a
    except Exception as e:  # noqa: BLE001 - le parseur lève plusieurs types d'erreurs
        a.error = (str(e).splitlines() or [type(e).__name__])[0][:300]
        return a
    feature = doc.get("feature")
    if not feature:
        a.error = "aucune Fonctionnalité"
        return a
    a.syntax_ok = True
    a.language = feature.get("language")
    a.language_ok = expected_language is None or a.language == expected_language
    rule_tag = f"@{rule_id}" if rule_id else None
    a.rule_tag_on_feature = bool(rule_tag) and rule_tag in {t["name"] for t in feature.get("tags", [])}
    a.n_rules = sum(1 for c in feature.get("children", []) if c.get("rule"))
    a.has_background = any(c.get("background") for c in feature.get("children", []))

    case_types: set[str] = set()
    names: list[str] = []
    gherkin_texts: list[str] = []
    for scenario, inherited, background in _iter_scenarios(feature):
        a.n_scenarios += 1
        names.append(scenario.get("name", "").strip())
        tags = inherited + [t["name"] for t in scenario.get("tags", [])]
        if rule_tag and rule_tag in tags:
            a.scenarios_with_rule_tag += 1
        found = {normalize_tag(t) for t in tags} & set(CASE_TYPES)
        # tags posés sur un tableau Exemples
        for ex in scenario.get("examples", []):
            found |= {normalize_tag(t["name"]) for t in ex.get("tags", [])} & set(CASE_TYPES)
            a.n_example_rows += len(ex.get("tableBody") or [])
            for row in ex.get("tableBody") or []:
                gherkin_texts.extend(c["value"] for c in row.get("cells", []))
        if found:
            a.scenarios_with_case_tag += 1
            case_types |= found
        if scenario.get("examples"):
            a.n_outlines += 1
        steps = scenario.get("steps", [])
        a.max_steps = max(a.max_steps, len(steps))
        errors, n_actions = _check_structure(scenario.get("name", ""), steps, background)
        if errors:
            a.scenarios_with_structure_error += 1
            a.structure_errors.extend(errors)
        if n_actions > 1:
            a.multi_action_scenarios += 1
        a.outline_errors.extend(_check_outline(scenario))
        gherkin_texts.extend(PLACEHOLDER_RE.sub("", t) for t in _step_texts(steps))

    a.case_types = sorted(case_types)
    a.duplicate_names = len(names) - len(set(names))
    if specification is not None:
        spec_numbers = set(_numbers(specification))
        numbers = [n for t in gherkin_texts for n in _numbers(t)]
        a.numbers_total = len(numbers)
        a.numbers_grounded = sum(1 for n in numbers if n in spec_numbers)
    return a


def score_components(a: GherkinAnalysis, rule_id: str | None = None) -> dict[str, float]:
    """Valeur (0 à 1) de chaque critère du score. Tout vaut 0 si la syntaxe ou la langue est fausse."""
    if not a.syntax_ok or not a.language_ok or a.n_scenarios == 0:
        return {k: 0.0 for k in SCORE_WEIGHTS}
    n = a.n_scenarios
    return {
        "tag_regle": (a.scenarios_with_rule_tag / n) if rule_id else 1.0,
        "nominal": float("nominal" in a.case_types),
        "limite": float("limite" in a.case_types),
        "negatif": float("negatif" in a.case_types),
        "structure": 1.0 - a.scenarios_with_structure_error / n,
        "plans": max(0.0, 1.0 - len(a.outline_errors) / n),
        "volume": 1.0 if n >= 3 else (0.5 if n == 2 else 0.0),
    }


def quality_score(a: GherkinAnalysis, rule_id: str | None = None) -> float:
    comps = score_components(a, rule_id)
    return round(sum(SCORE_WEIGHTS[k] * v for k, v in comps.items()), 4)
