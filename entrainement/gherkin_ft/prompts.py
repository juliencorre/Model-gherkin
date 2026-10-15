"""Construction des messages (system / user / assistant) vus par le modèle.

Le même prompt doit servir à l'entraînement et à l'inférence : il est enregistré avec l'adaptateur
(`gherkin_ft.json`) et relu par les commandes `evaluate` et `generate`.
"""

from __future__ import annotations

DEFAULT_SYSTEM_PROMPT = """\
Tu es un analyste QA expert en BDD. À partir d'une spécification fonctionnelle, tu rédiges une \
fonctionnalité Gherkin en français, exécutable par Cucumber.
Règles de rédaction :
- Première ligne : # language: fr. Mots-clés : Fonctionnalité, Contexte, Règle, Scénario, \
Plan du scénario, Exemples, Étant donné, Quand, Alors, Et, Mais.
- Tag de la règle sur la fonctionnalité et sur chaque scénario, plus un tag de type : @nominal, @limite ou @négatif.
- Couvre le cas nominal, les valeurs limites (de part et d'autre de chaque borne) et les cas négatifs.
- Un comportement par scénario : un seul Quand, des Alors vérifiables avec des valeurs concrètes.
- Regroupe les variations de données dans un Plan du scénario avec un tableau Exemples.
- Style déclaratif, vocabulaire métier, pas de détail d'interface.
- N'invente aucune règle absente de la spécification.
Réponds uniquement par le Gherkin, sans explication ni bloc markdown."""

DEFAULT_USER_TEMPLATE = "Règle : {id}\n\nSpécification :\n{specification}"
DEFAULT_USER_TEMPLATE_NO_ID = "Spécification :\n{specification}"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


def build_user_prompt(rule_id: str | None, specification: str, template: str | None = None, **extra: str) -> str:
    """Message utilisateur. `template` accepte `{id}`, `{specification}` et tout champ passé dans `extra`."""
    if template is None:
        template = DEFAULT_USER_TEMPLATE if rule_id else DEFAULT_USER_TEMPLATE_NO_ID
    values = _SafeDict(extra, id=rule_id or "", specification=specification.strip())
    return template.format_map(values).strip()


def build_prompt_messages(
    rule_id: str | None, specification: str, system_prompt: str, template: str | None = None, **extra: str
) -> list[dict]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": build_user_prompt(rule_id, specification, template, **extra)})
    return messages


def build_training_example(
    rule_id: str | None, specification: str, gherkin: str, system_prompt: str, template: str | None = None
) -> dict:
    """Exemple au format « prompt-completion conversationnel » de TRL : la perte ne porte que sur le Gherkin."""
    return {
        "prompt": build_prompt_messages(rule_id, specification, system_prompt, template),
        "completion": [{"role": "assistant", "content": gherkin}],
    }
