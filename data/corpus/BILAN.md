# Bilan du corpus (arrêt décidé par le commanditaire le 2026-10-15)

Objectif initial : 10 000 paires de qualité. **Production arrêtée à 3 012 paires** sur décision du commanditaire (coût en jetons). Les chiffres exacts sont dans `STATS.json`.

## Chiffres

| | Paires |
|---|---|
| Produites | 3 012 (11 700 scénarios) |
| Niveau A (résultats vérifiés par un moteur) | 295 |
| Niveau B (source formelle, contrôles passés) | 462 |
| Niveau C (source en texte, contrôles passés) | 1 901 |
| **Niveaux A + B + C (qualité contrôlée)** | **2 658** |
| Niveau D (à relire, hors entraînement) | 354 |
| **A + B + C, sources redistribuables (jeu public)** | **2 244** |

Jeu public : `train.jsonl` 2 052, `val.jsonl` 93, `test.jsonl` 99 ; `a_relire.jsonl` 350 paires de niveau D. Les 414 paires de niveaux A, B et C issues de sources non redistribuables (OpenFisca, Code du travail numérique, aides-jeunes) sont dans `data/corpus_prive/`, non versionné.

Le découpage train / val / test se fait par groupe de source, jamais par scénario, pour éviter les fuites.

## Qualité mesurée

Audit indépendant (Opus, `AUDIT.json`) sur 166 paires tirées au hasard : avec les consignes finales, 62 paires bonnes, 17 mineures, 3 majeures sur 82 (3,7 %, intervalle de confiance à 95 % de 1,3 à 10,2 %). Aucune paire n'a été relue par un humain. L'audit ne porte pas sur les lots produits après lui (par exemple une partie des lots LEGI et service-public) : leur taux d'erreurs est supposé proche mais n'est pas mesuré.

Comparaison Haiku / Sonnet (même 12 règles, audit en aveugle) : Sonnet 12 bonnes sur 12 ; Haiku 7 bonnes, 4 mineures, 1 majeure, et 1,7 fois plus de jetons consommés. Sonnet a été conservé.

## Ce qui reste à faire avant un entraînement sérieux

1. Faire relire par un expert métier un échantillon des niveaux B et C, et les paires de niveau D.
2. Faire valider par un juriste : l'effet des licences AGPL et CeCILL, les conditions d'utilisation du modèle générateur, la réutilisation des textes de loi, et les sources à licence contradictoire (Code du travail numérique).
3. Étendre la vérification par moteur : seules les règles du SMIC sont vérifiées par le compilateur Catala (78 cas).
4. Compléter les domaines absents : justice, éducation, urbanisme, marchés publics, immigration.
5. Si le volume est insuffisant après un premier affinage, reprendre la production : 13 000 unités sources restent prêtes (`scripts/etat_production.py`), ainsi que les consignes (`scripts/prompts/generation.md`).

## Reprise

Les lots non traités sont préparés dans `data/lots/<type>/lot_NNNN.jsonl`. Pour en traiter un, appliquer `scripts/prompts/generation.md` sur ce lot, puis `scripts/verifier_lots.py` et `scripts/construire_corpus.py`.
