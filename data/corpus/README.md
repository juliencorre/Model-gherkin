# Corpus spécification → Gherkin (français, administration française)

Paires (spécification de règle de gestion → scénarios Gherkin en français) pour affiner un petit modèle à générer des tests BDD.
Les chiffres exacts et à jour sont dans `STATS.json` (régénéré par `scripts/construire_corpus.py`) et les résultats d'audit dans `AUDIT.json`.

## Contenu

| Fichier | Rôle |
|---|---|
| `train.jsonl`, `val.jsonl`, `test.jsonl` | Paires de niveaux A, B ou C, **sources redistribuables uniquement**, découpées par groupe de source |
| `a_relire.jsonl` | Paires de niveau D (résultats attendus non vérifiables automatiquement) : **hors entraînement** tant qu'elles ne sont pas relues |
| `pairs/<lot>.jsonl` | Toutes les paires publiques d'un lot, avec leurs contrôles |
| `rejets.jsonl` | Paires écartées à la construction, avec le motif |
| `STATS.json` | Comptages par niveau, source, licence, découpage |
| `AUDIT.json` | Résultats de l'audit indépendant par échantillon |
| `lots_supplementaires.json` | Déclaration des lots pris en compte par le constructeur |

Un dossier `data/corpus_prive/` (non versionné) contient en plus les paires issues de sources non redistribuables (AGPL, licence à clarifier) : OpenFisca-France, Code du travail numérique, aides-jeunes.

## Schéma d'une paire

`id`, `lot`, `langue` (`fr`), `source_type`, `domaine`, `source` (fichier ou URL), `reference` (article ou règle), `id_legifrance`, `licence_source`, `redistribuable`, `specification`, `gherkin`, `notes`, `controles`, `niveau`, `relu_humain` (toujours `false` à ce jour), `groupe`, `split`.

Les scénarios portent un tag `@<id de l'unité>` et un tag de type : `@nominal`, `@limite`, `@négatif`.

## Niveaux de qualité

- **A** : résultats attendus issus de cas de test exécutés par le moteur de la source (OpenFisca, Code du travail numérique) ou vérifiés par le compilateur Catala (règles du SMIC). Seules les paires Catala sont publiques.
- **B** : source avec code ou règle formelle (Catala, Publicodes) ; syntaxe valide, tags présents, tous les résultats attendus déductibles de la source et des données d'entrée du scénario.
- **C** : source en texte seul (fiches service-public.fr, articles des codes sur Légifrance, aides-jeunes) ; mêmes contrôles que B, sans exécution possible.
- **D** : résultats attendus non vérifiables automatiquement ; conservées, hors entraînement.

Contrôles automatiques par paire : parseur officiel `cucumber/gherkin` (langue `fr`), tag de la règle, au moins 2 scénarios dont un `@nominal`, absence de mots-clés anglais, spécification non vide, non dupliquée, et traçabilité numérique des résultats attendus.

## Audit

Un modèle indépendant du générateur (Opus) a relu 166 paires tirées au hasard par type de source (84 avec les consignes initiales, 82 avec les consignes finales) : voir `AUDIT.json`. Avec les consignes finales, 62 paires sont bonnes, 17 ont un défaut mineur et 3 un défaut majeur sur 82 (3,7 %, intervalle de confiance à 95 % de 1,3 à 10,2 %). **Aucune paire n'a été relue par un humain.**

## Sources et licences

| Source | Licence | Redistribuable |
|---|---|---|
| Catala-examples (Inria, DGFiP, CNAF) | Apache-2.0 (dossier `impot_revenu` exclu : CeCILL 2.1) | oui |
| mon-entreprise (URSSAF, beta.gouv) | MIT | oui |
| service-public.fr (jeu AgentPublic/service-public) | Licence Ouverte 2.0 | oui, avec attribution |
| Articles des codes (jeu AgentPublic/legi, DILA) | Licence Ouverte 2.0 | oui, avec attribution |
| OpenFisca-France | AGPL-3.0 | non (corpus privé) |
| Code du travail numérique | Apache-2.0 ou MIT (fichiers contradictoires) | non (corpus privé) |
| aides-jeunes | AGPL-3.0 | non (corpus privé) |

La spécification et le Gherkin de chaque paire ont été rédigés par un modèle de langage à partir de la source ; la licence indiquée est celle de la source. Les conditions d'utilisation du modèle générateur, l'effet des licences copyleft sur un modèle entraîné et la réutilisation des textes de loi sont à faire valider par un juriste.

## Limites connues

- Domaine : surtout droit social, fiscal et aides ; justice, éducation, urbanisme, marchés publics et immigration sont peu représentés.
- Valeurs fictives : lorsque la source ne donne pas une valeur (SMIC, plafond), le scénario utilise une donnée de test déclarée dans `notes` ; il teste la formule, pas un montant légal.
- Les spécifications sont des reformulations par le même modèle que les scénarios : les erreurs d'interprétation éventuelles sont corrélées.
- Défauts les plus fréquents constatés à l'audit : cas négatifs ou limites manquants, étiquettes `@limite`/`@négatif` mal posées, scénarios qui répètent la règle sans rien vérifier, conditions de la source omises dans les « Étant donné ».
- Les articles de loi extraits de Légifrance peuvent contenir des tableaux dégradés.

## Reconstruction

```
scripts/fetch_sources.sh vendored          # sources permissives dans sources/
python3 scripts/extraire_unites.py . <parquet service-public>
python3 scripts/extraire_legi.py <dossier parquet LEGI> data/unites/legi.jsonl
python3 scripts/extraire_unites_elargies.py . <parquet service-public> <dossier parquet LEGI>
python3 scripts/preparer_lots.py <type> <début> <n> 25 --aleatoire 7
# génération : consignes dans scripts/prompts/generation.md
python3 scripts/verifier_lots.py && python3 scripts/construire_corpus.py
```
