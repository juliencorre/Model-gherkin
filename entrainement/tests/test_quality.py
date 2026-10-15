import json
from pathlib import Path

from gherkin_ft.quality import analyze_gherkin, extract_gherkin, quality_score, score_components

FIXTURE = Path(__file__).parent / "fixtures" / "paires.jsonl"


def first_pair():
    return json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])


def test_reference_fixture_is_perfect():
    p = first_pair()
    a = analyze_gherkin(p["gherkin"], p["id"], p["specification"])
    assert a.syntax_ok and a.language_ok
    assert a.n_scenarios == 3 and a.n_outlines == 1 and a.n_example_rows == 2
    assert a.case_types == ["limite", "negatif", "nominal"]
    assert a.scenarios_with_rule_tag == 3 and a.rule_tag_on_feature
    assert not a.outline_errors and not a.structure_errors
    assert quality_score(a, p["id"]) == 1.0
    assert a.numbers_total > 0 and a.numbers_grounded > 0


def test_syntax_error_gives_zero():
    text = "# language: fr\nFonctionnalité: x\n  Scénario: y\n    Quand a\n      | a | b |\n      | c |\n    Alors d\n"
    a = analyze_gherkin(text, "RG-1")
    assert not a.syntax_ok and "inconsistent cell count" in a.error
    assert quality_score(a, "RG-1") == 0.0
    # Sans scénario, le texte est syntaxiquement valide mais ne vaut rien.
    assert quality_score(analyze_gherkin("# language: fr\nFonctionnalité: x\n")) == 0.0


def test_scenario_without_steps_fails_structure():
    a = analyze_gherkin("# language: fr\nFonctionnalité: x\n  Du texte libre.\n  Scénario: y\n    Truc\n")
    assert a.syntax_ok and a.scenarios_with_structure_error == 1


def test_free_text_before_feature_is_invalid():
    a = analyze_gherkin("Voici le Gherkin :\n# language: fr\nFonctionnalité: x\n  Scénario: y\n    Quand a\n    Alors b\n")
    assert not a.syntax_ok


def test_wrong_language_is_gated():
    text = "Feature: x\n  @nominal\n  Scenario: y\n    When a\n    Then b\n"
    a = analyze_gherkin(text, expected_language="fr")
    assert a.syntax_ok and not a.language_ok
    assert quality_score(a) == 0.0
    assert analyze_gherkin(text, expected_language=None).language_ok


def test_outline_inconsistencies():
    text = """# language: fr
Fonctionnalité: x
  @nominal
  Plan du scénario: y
    Étant donné une valeur <a>
    Quand on calcule
    Alors le résultat est <b>

    Exemples:
      | a | c |
      | 1 | 2 |
"""
    a = analyze_gherkin(text)
    assert any("['b']" in e and "absent" in e for e in a.outline_errors)
    assert any("['c']" in e and "inutilisée" in e for e in a.outline_errors)


def test_placeholder_without_examples():
    text = "# language: fr\nFonctionnalité: x\n  Scénario: y\n    Étant donné <a>\n    Quand b\n    Alors c\n"
    assert analyze_gherkin(text).outline_errors


def test_comparison_signs_are_not_placeholders():
    text = ("# language: fr\nFonctionnalité: x\n  Scénario: y\n    Étant donné un revenu < 100 et > 50\n"
            "    Quand on calcule\n    Alors le résultat attendu est <résultat attendu>\n")
    errors = analyze_gherkin(text).outline_errors
    assert len(errors) == 1 and "résultat attendu" in errors[0]


def test_structure_errors_and_multi_when():
    text = """# language: fr
Fonctionnalité: x
  Scénario: sans quand
    Étant donné a
    Alors b
  Scénario: désordre
    Étant donné a
    Alors b
    Quand c
  Scénario: deux actions
    Étant donné a
    Quand b
    Et c
    Alors d
"""
    a = analyze_gherkin(text)
    assert a.scenarios_with_structure_error == 2
    assert a.multi_action_scenarios == 1  # « deux actions » (Quand ... Et ...)
    assert score_components(a)["structure"] == 1 - 2 / 3


def test_tags_inherited_from_rule_and_unaccented_case_tags():
    text = """# language: fr
@RG-9
Fonctionnalité: x
  Contexte:
    Étant donné un contexte
  @negatif
  Règle: r
    @Nominal
    Scénario: a
      Quand b
      Alors c
    Scénario: d
      Quand e
      Alors f
"""
    a = analyze_gherkin(text, "RG-9")
    assert a.n_rules == 1 and a.has_background
    assert a.scenarios_with_rule_tag == 2
    assert a.case_types == ["negatif", "nominal"]
    assert not a.structure_errors  # le Contexte fournit l'étape Étant donné


def test_markdown_fence_is_tolerated_and_flagged():
    p = first_pair()
    a = analyze_gherkin("```gherkin\n" + p["gherkin"] + "```\n", p["id"])
    assert a.syntax_ok and a.has_markdown_fence


def test_extract_gherkin_from_chatty_answer():
    p = first_pair()
    chatty = "Voici les scénarios :\n\n```gherkin\n" + p["gherkin"] + "```\nN'hésitez pas !"
    assert extract_gherkin(chatty).startswith("# language: fr")
    assert analyze_gherkin(extract_gherkin(chatty), p["id"]).syntax_ok
