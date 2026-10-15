# Jeu d'affinage supervisé (instruction → réponse)

Généré par `python3 scripts/convertir_sft.py` à partir de `data/corpus/` (sources redistribuables uniquement, niveaux A, B et C). `python3 scripts/convertir_sft.py --prive` produit la version complète dans `data/sft_prive/` (non versionnée), qui inclut OpenFisca, le Code du travail numérique et aides-jeunes.

| Fichier | Paires |
|---|---|
| `train.jsonl` | 2 052 |
| `val.jsonl` | 93 |
| `test.jsonl` | 99 |

## Format

Une ligne JSON par paire : `{"id", "messages": [system, user, assistant], "meta": {source_type, domaine, niveau, licence_source, scenarios}}`.

- `system` : rôle d'expert BDD pour l'administration française, règles de fidélité et de tags.
- `user` : « Spécification : … » suivie de la consigne de rédiger le fichier Gherkin en français.
- `assistant` : le fichier Gherkin (`# language: fr`, scénarios taggés `@nominal`, `@limite`, `@négatif`).

Le format `messages` est celui attendu par la plupart des outils d'affinage (TRL `SFTTrainer`, Axolotl, Unsloth). Il suffit de choisir le modèle et son gabarit de conversation.

## Traitements appliqués

- Retrait des tags d'identifiant d'unité (`@SP-00012`, `@RG-21`…) et des mentions `(RG-01)` : ce sont des artefacts de production que le modèle ne doit pas apprendre à recopier.
- Indentation canonique de tous les fichiers (Fonctionnalité 0, scénarios et tags 2, étapes 4, tables 6).
- Revalidation avec le parseur officiel `cucumber/gherkin` (langue `fr`, au moins 2 scénarios, `@nominal` présent).
- Les paires de niveau D (`a_relire`) ne sont jamais converties.

## Avant d'entraîner

Lire `data/corpus/README.md` et `data/corpus/BILAN.md` : aucune paire n'a été relue par un humain, le domaine est surtout droit social et fiscal, et plusieurs points juridiques sont à valider.
Évaluer sur `test.jsonl` : validité syntaxique, couverture des règles de la spécification, relecture manuelle d'une centaine de sorties, et comparaison avec le modèle de départ non affiné.
