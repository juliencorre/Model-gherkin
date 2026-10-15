# Bilan de l'essai pilote : 20 règles → spécification + Gherkin français

Date : 2026-10-15. Sources : 20 unités (article de loi + code Catala) extraites de `sources/regles-as-code/catala-examples` par `scripts/extract_regles_catala.py` (`regles_20.jsonl`). Génération : 4 lots de 5 règles (`gherkin_fr_lot1..4.jsonl`) par un grand modèle (Claude), un lot par agent. Validation : `scripts/valider_gherkin.py` (parseur officiel cucumber/gherkin, langue `fr`).

## Résultats

| Mesure | Résultat |
|---|---|
| Paires produites | 20 sur 20 |
| Erreurs de syntaxe (parseur officiel) | 0 |
| Scénarios au total | 94 (de 2 à 6 par règle) |
| Paires passant tous les contrôles automatiques | 19 sur 20 |
| Contrôle échoué | RG-17 : 2 scénarios et pas de cas limite. Le modèle l'explique dans `notes` (la règle ne porte que sur une liste de résidences, aucune borne n'existe). Le contrôle est trop strict pour ce cas. |

## Vérification manuelle

Relues à la main : RG-01 (SMIC 2019), RG-10 (plafonds de ressources), RG-11 (plafond de rémunération), RG-17 (régime outre-mer).
- Les montants calculés de RG-10 et RG-11 sont exacts (55 950 + n × 5 595 ; 55 % × SMIC × 169).
- Les 16 autres paires n'ont subi que les contrôles automatiques. Elles ne sont pas relues à la main.

Un contrôle par script a signalé 42 nombres des scénarios absents du texte de loi, du code et de la spécification. Examen des cas : années voisines (bornes), valeurs d'entrée fictives déclarées, ou résultats calculés (RG-10, RG-11 vérifiés). Les autres (RG-14, RG-16, RG-20) ne sont pas vérifiés un par un.

## Limites constatées

- **Valeurs fictives** : RG-11 et RG-20 posent un SMIC fictif (10 €, 12 €), RG-14 des plafonds fictifs, car aucune valeur n'est dans le code. Ces scénarios testent la formule, pas un montant légal.
- **Règles sans code formalisé** : RG-13, RG-15 et RG-16 reposent sur le texte de loi seul. Leurs résultats attendus n'ont aucune vérification par le code.
- **Bornes ambiguës** (interprétation du modèle, à valider) : « au bout d'un an » (RG-13) et « au moins cinq ans » (RG-15) lus comme inclusifs ; « ne peut être inférieur » (RG-14) lu comme le plus élevé des deux plafonds ; l'âge de 20 ans n'est pas testé le jour de l'anniversaire (RG-11) ; divergences entre texte et code sur RG-19 et RG-20.
- **Résidences négatives non vérifiées** : RG-17 donne Mayotte et Saint-Pierre-et-Miquelon comme résidences hors champ ; leur existence comme valeurs du modèle n'est pas vérifiée.
- **Spécification reformulée par le même modèle que le Gherkin** : la spécification et les scénarios partagent les mêmes erreurs d'interprétation éventuelles. Une relecture humaine est indispensable avant tout entraînement.
- **Domaine étroit** : loi sociale (SMIC, prestations familiales, aides au logement, ASP, successions). Les autres domaines ne sont pas testés.
- **Vérification Catala partielle** : seules les 6 règles SMIC (RG-01 à RG-06) sont vérifiées par le compilateur (voir ci-dessous). Pour les 14 autres, les valeurs attendues viennent de la lecture du code.

## Vérification par le compilateur Catala (2026-10-15)

- Installation : Catala 1.3.0 compilé avec opam (`opam init --bare` sur le miroir `https://opam.ocaml.org`, `opam switch create catala ocaml-system`, `opam install catala.1.3.0`). Les archives GitHub étant bloquées dans cet environnement, ce miroir est indispensable.
- Contrôle de l'installation : les 32 tests officiels de `smic` et `allocations_familiales` passent (100 %), sur une copie de travail hors dépôt.
- Vérification des règles SMIC : `scripts/verifier_smic_catala.py` développe les exemples des scénarios non négatifs de RG-01 à RG-06 en 78 cas concrets (date, résidence, montant attendu), les exécute dans le scope `Smic.Smic` et compare. Résultat : **78 cas conformes, 0 écart** (`verification_catala_smic.json`).
- Non vérifié : les scénarios `@négatif` des règles SMIC (ils portent sur la règle seule, pas sur le module), et les règles RG-07 à RG-20. Leur vérification demande d'écrire des scopes de test avec des structures de données complètes (enfants, ménages, logements). RG-13, RG-15 et RG-16 n'ont pas de code Catala calculé.

## Suite possible

1. Relire les 16 paires restantes avec un juriste ou un expert métier.
2. Étendre la vérification Catala aux règles RG-07 à RG-20 (scopes de test à écrire règle par règle).
3. Générer les spécifications avec un modèle et les scénarios avec un autre, pour limiter les erreurs communes.
4. Passer à l'échelle (centaines de règles) seulement après ces corrections.
