# Catalogue des sources versionnées

Sources copiées dans ce dépôt par `scripts/fetch_sources.sh vendored`. Seules les sources sous licence permissive (MIT, Apache-2.0, CC BY 4.0) sont incluses. Chaque dossier contient le fichier de licence d'origine et `SOURCE_COMMIT` (commit relevé lors de la copie, le 2026-10-15).

La note de recherche `research_notes/Corpus de spécifications pour Gherkin/` détaille les sources non copiées ici (AGPL, EUPL, CeCILL, licence floue ou absente), que `scripts/fetch_sources.sh local` récupère dans `sources_local/` (ignoré par git).

| Dossier | Origine | Licence | Contenu | Usage prévu |
|---|---|---|---|---|
| `regles-as-code/catala-examples` | github.com/CatalaLang/catala-examples | Apache-2.0 (dossier `impot_revenu` exclu : CeCILL 2.1, copyright DGFiP) | Textes de loi français (Légifrance) avec leur code Catala et des scopes de test : aides au logement, allocations familiales, ASP, SMIC, successions | Règle → scénario |
| `regles-as-code/mon-entreprise` | github.com/betagouv/mon-entreprise | MIT | Règles Publicodes (cotisations, indépendants, assimilés salariés) avec descriptions et références | Règle → scénario |
| `gherkin-fr/aplypro` | github.com/betagouv/aplypro | MIT | Fichiers `.feature` en français, règles de calcul explicites | Exemples de sortie, jeu de style |
| `gherkin-fr/acces-cible` | github.com/betagouv/acces-cible | MIT | Fichiers `.feature` en français | Exemples de sortie |
| `gherkin-fr/oots-france` | github.com/numerique-gouv/oots-france | Apache-2.0 | Fichiers `.feature` en français | Exemples de sortie |
| `ue/eudi-arf` | github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework (`docs/annexes`) | CC BY 4.0 (à confirmer dans le fichier `LICENCE`) | Exigences « SHALL » numérotées, en anglais | Exigence → scénario |
| `ue/dcc-business-rules` | github.com/eu-digital-green-certificates/dgc-business-rules-testdata | Apache-2.0 | Règles du certificat COVID UE (JSON-logic) et jeux de tests par pays, en anglais | Règle + test → scénario |

## Points à vérifier

- Les dépôts versionnés peuvent contenir des fichiers qui n'appartiennent pas à leur auteur (par exemple des textes de loi dans les exemples Catala, ou des données de tiers). Les textes de loi sont réutilisables (Légifrance), mais cela reste à faire valider par un juriste.
- Le fichier `LICENCE` du dépôt ARF doit être relu pour confirmer CC BY 4.0, et l'attribution doit être conservée.
- Les sources en anglais (ARF, DCC) servent surtout à la diversité des types de règles. Le corpus d'entraînement vise le français.
