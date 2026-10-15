# French public-sector "rules as code" projects that publish rules AND test cases (status October 2026)

Method: I shallow-cloned each public repository on 2026-10-15 (`git clone --depth 1`) and counted files and test cases with grep/find. All volumes below come from those clones unless marked otherwise. The GitHub REST API was not reachable from this session, so stars and contributor counts are missing. "Last commit" means the date of the HEAD commit on the default branch at clone time. Licences were read from the LICENSE file in each repo, cross-checked against package.json where one exists.

## Q1. OpenFisca-France, openfisca-paris, openfisca-france-local (and LexImpact)

### Takeaway
OpenFisca-France is the largest French corpus of paired rules and tests, and it is very active in 2026. It has about 3,180 Python `Variable` classes and about 4,060 YAML parameter files, plus 843 YAML test files holding roughly 1,900–2,600 test cases. Each case has `name / description / period / input / output`, so it maps almost one-to-one onto Gherkin. The licence is **AGPL-3.0**, which is copyleft; check whether it is compatible with your training-data distribution model.

### Cited Findings
- Repo: https://github.com/openfisca/openfisca-france. Licence file `LICENSE.AGPL.txt` (GNU AGPL v3). Last commit 2026-10-01 ("Fixe le smic de référence de la réduction générale au 1er janvier 2026 (#2810)"), so it is actively maintained. — [openfisca-france repo](https://github.com/openfisca/openfisca-france)
- The README says the repo "contient la modélisation du système social et fiscal français" and that "the working language here is French". There is a public Web API at https://api.fr.openfisca.org/latest/ with Swagger at https://legislation.fr.openfisca.org/swagger, and endpoints for parameters (e.g. `marche_travail.salaire_minimum.smic.smic_b_horaire`) and variables (e.g. `af_base`). — [README](https://github.com/openfisca/openfisca-france/blob/master/README.md)
- Volumes from my clone:
  - 843 `.yaml` test files under `tests/`.
  - 1,867 test cases that start with `- name:`, and 2,628 `output:` blocks. The true number of cases is between those two figures, because some files hold a single case with no list.
  - 3,183 `class …(Variable)` declarations, of which 478 carry a `reference = ` line (a legal URL).
  - 4,064 parameter YAML files.
  — [tests/](https://github.com/openfisca/openfisca-france/tree/master/tests)
- Test directories include `formulas` (164 entries, e.g. `af.yaml`, `aah`, `aeeh.yaml`, `aides_logement*.yaml`, `agepi.yaml`, `allegement_general.yaml`, `asf`, `asi.yaml`, `arrco.yaml`…), `impot_revenu`, `calculateur_impots`, `fiches_de_paie`, `cotisations_sociales_simulateur_IPP.yaml`, `prestations`, `chomage`, `capital`, `patrimoine`, `leximpact`, `mes-aides.gouv.fr`, `embauche.sgmap.fr`. Domains covered: income tax (IR), social contributions and payroll (cotisations, allègements, fiches de paie), family benefits (AF, ASF, AEEH), minimum incomes (RSA, AAH, ASI), housing aid (APL/AL), unemployment, pensions (Arrco), local aids. — [tests/formulas](https://github.com/openfisca/openfisca-france/tree/master/tests/formulas)
- Actual test structure, from `tests/formulas/af_2018_01.yaml`:
  ```yaml
  - name: Allocations familiales - Cas N°1
    description: Montant AF
    period: 2018-01
    absolute_error_margin: 0.02
    input:
      famille: {parents: [parent1, parent2], enfants: [enfant1, enfant2]}
      individus:
        parent1: {age: 38, revenu_assimile_salaire: {2015: 40000, ..., 2018: 40000}}
        parent2: {age: 35, revenu_assimile_salaire: {...: 20000}}
        enfant1: {age: 12}
        enfant2: {age: 10}
    output:
      af: 129.86 / (1 - 0.005)
  ```
  — [af_2018_01.yaml](https://github.com/openfisca/openfisca-france/blob/master/tests/formulas/af_2018_01.yaml)
- Parameter files are YAML with a French `description` and dated `values`. For example, `parameters/prestations_sociales/prestations_familiales/bmaf/bmaf.yaml` has `description: Base mensuelle de calcul des allocations familiales (BMAF)` and values from 1946 onwards. Variables are Python classes with a French `label` (e.g. `af_base`: `label = 'Allocations familiales - allocation de base'`, `definition_period = MONTH`, `entity = Famille`). — [bmaf.yaml](https://github.com/openfisca/openfisca-france/tree/master/openfisca_france/parameters/prestations_sociales/prestations_familiales/bmaf); [af.py](https://github.com/openfisca/openfisca-france/blob/master/openfisca_france/model/prestations/prestations_familiales/af.py)
- openfisca-paris (Ville de Paris aids): licence AGPL-3.0 (`LICENSE.AGPL.txt`). Last commit 2026-08-05, which was a dependency bump; the repo also has a `sources_du_droit/` folder. Counts: 26 test YAML files, 122 `- name:` cases, 69 variables. — [openfisca-paris](https://github.com/openfisca/openfisca-paris)
- openfisca-france-local (local aids from departments, regions and communes): licence AGPL-3.0. Last commit 2026-08-05. It has `sources_du_droit/` and `test_data/` folders. Counts: 86 test YAML files, 251 `- name:` cases, 170 variables. — [openfisca-france-local](https://github.com/openfisca/openfisca-france-local)

### Inferences
- Mapping to Gherkin: `name` becomes `Scénario`, `period` becomes "Étant donné la période 2018-01", each `input` entity attribute becomes an "Étant donné"/"Et" step (e.g. "Et parent1 a 38 ans et un revenu assimilé salaire de 40 000 €"), the calculation becomes "Quand on calcule af", and `output` becomes "Alors af vaut 129,86 / 0,995 (marge 0,02)". Specification text for the pair can be built from the variable's `label` + `reference` URL + formula docstring + parameter `description`. The result is a (spec → Gherkin) pair whose rule text is semi-generated.
- Files with several cases (e.g. Cas N°1…N) map naturally onto `Plan du scénario` + `Exemples`.
- Weakness: inputs use technical variable names (e.g. `revenu_assimile_salaire`), so the dataset needs a verbalisation step (label lookup through the Web API `/variable/{name}`) to get natural French.
- AGPL-3.0 is a software licence. Whether model weights trained on it count as derivative works is legally unsettled. Record it per sample.

### Gaps
- I did not clone or verify LexImpact repos (e.g. `leximpact-socio-fiscal-api`) or the openfisca-france `tests/leximpact` directory contents. LexImpact (Assemblée nationale) status in 2026 is unverified.
- I have no exact count of test cases that use the non-list YAML form.
- Other OpenFisca countries (Tunisia, Senegal, etc.) were not checked.

## Q2. Catala (Inria; DGFiP, CNAF, ASP)

### Takeaway
Catala is literate programming: Légifrance article text (with LEGIARTI identifiers) sits interleaved with ```catala code blocks, and `#[test]` scopes carry assertions. That is close to an ideal "spec + rule + test" triplet, all in French (`.catala_fr`). The catala-examples repo is **Apache-2.0**, except `impot_revenu/`, which is **CeCILL 2.1** and "Copyright DGFiP 2023-2024". The volume is small but very high quality: about 64 French source files and about 87 test scopes.

### Cited Findings
- Compiler repo https://github.com/CatalaLang/catala: Apache-2.0 (`LICENSE.txt`), with release 1.3.0 on 2026-10-01 (very active). The compiler test suite has 294 `.catala_*` files, which are language tests rather than law. — [catala](https://github.com/CatalaLang/catala)
- Examples repo https://github.com/CatalaLang/catala-examples: Apache-2.0 `LICENSE.txt`, last commit 2026-09-18. Its README lists `allocations_familiales/` ("French family benefits, based on the Code de la sécurité sociale") and `aides_logement` ("French housing benefits, based on the Code de la construction et de l'habitation… the biggest and most ambitious for Catala so far"). It says tests go in `foo/tests/` as test scopes run with `clerk test`. — [catala-examples README](https://github.com/CatalaLang/catala-examples)
- Folder inventory from my clone (files / lines / `#[test]` scopes):
  - `aides_logement`: 17 / 28,212 / 33
  - `impot_revenu`: 16 / 15,040 / 27
  - `asp` (Agence de services et de paiement): 11 / 4,845 / 7, with subfolders `aide_fibre` (fibre-optic connection works aid), `bcae7` (CAP conditionality: crop rotation, with official PDF fiches techniques 2023/2024/2025 in `specifications/`) and `fonpeps` (aid for live-performance employment)
  - `allocations_familiales`: 10 / 2,623 / 15
  - `prestations_familiales`: 5 / 319 / 1
  - `droit_successions`: 2 / 252 / 4
  - `smic`: 1 / 490 / 0
  - `base_mensuelle_allocations_familiales`: 1 / 113 / 0
  - `prologue_france`: 1 / 40 / 0
  - non-French: `us_tax_code` (catala_en), `polish_taxes` (catala_pl), `NSW_community_gaming`
  — [catala-examples tree](https://github.com/CatalaLang/catala-examples)
- `impot_revenu/LICENSE` is "CONTRAT DE LICENCE DE LOGICIEL LIBRE CeCILL Version 2.1". The headers in `impot_revenu.catala_fr` say "Copyright DGFiP 2023-2024. Contributeurs : Caroline Flori <…@dgfip.finances.gouv.fr>, Denis Merigoux <…@inria.fr>, Louis Gesbert <…@inria.fr>" and describe a program "servant à calculer le montant de l'impôt sur le revenu à partir des données de la déclaration de revenus". The folder also contains `oracles.catala_fr` and `vérifications.catala_fr`. — [impot_revenu](https://github.com/CatalaLang/catala-examples/tree/master/impot_revenu)
- Literate source sample, from `allocations_familiales/securite_sociale_L.catala_fr`:
  ```
  ###### Article L521-1|LEGIARTI000029963006
  Les allocations familiales sont dues à partir du deuxième enfant à charge.
  ```catala
  champ d'application AllocationsFamiliales:
    règle droit_ouvert_base
    sous condition nombre de enfants_à_charge_droit_ouvert_prestation_familiale >= 2
    conséquence rempli
  ```
  ```
  — [securite_sociale_L.catala_fr](https://github.com/CatalaLang/catala-examples/blob/master/allocations_familiales/securite_sociale_L.catala_fr)
- Test sample, from `allocations_familiales/tests/tests_allocations_familiales.catala_fr`:
  ```
  #[test]
  déclaration champ d'application Test1:
    f champ d'application AF.InterfaceAllocationsFamiliales
    données champ d'application Données
  champ d'application Test1:
    définition f.i_enfants égal à [ données.enfant1; données.enfant2; données.enfant3; données.enfant4 ]
    définition f.i_ressources_ménage égal à 30 000 €
    définition f.i_date_courante égal à |2020-05-01|
    définition f.i_résidence égal à Métropole
    règle f.i_personne_charge_effective_permanente_est_parent rempli
    assertion f.i_montant_versé = 351,54€
  ```
  Other cases in the file: Test3 is Guyane, 1 enfant, 63,540 € → 24,37 €; Test4 is Métropole, 2 enfants, 67,250 € → 99,46 €. — [tests_allocations_familiales.catala_fr](https://github.com/CatalaLang/catala-examples/blob/master/allocations_familiales/tests/tests_allocations_familiales.catala_fr)
- CNAF–Inria partnership agreement to use Catala for benefit calculation: signed 3 June according to Acteurs Publics, announced 8 June according to Solutions Numériques (the two dates conflict). Catala has been developed by Inria (Apollo programme) since 2019. The Caf network pays about €110 bn/year to more than 13.6 M households. — [Acteurs Publics](https://acteurspublics.fr/articles/la-cnaf-fait-le-pari-de-l-open-source-pour-reprendre-la-main-sur-le-calcul-des-allocations/); [Solutions Numériques](https://www.solutions-numeriques.com/la-cnaf-et-inria-misent-sur-lopen-source-pour-fiabiliser-le-calcul-des-prestations-sociales/)
- The Catala consortium led by Denis Merigoux received the 2026 Scientific Interdisciplinarity Award (Université Paris-Saclay). — [Paris-Saclay](https://www.universite-paris-saclay.fr/en/news/catala-project-receives-scientific-interdisciplinarity-award)
- The catala-examples README says the generated OCaml/JS/Python artifacts are published in https://github.com/CatalaLang/french-law. — [catala-examples README](https://github.com/CatalaLang/catala-examples)

### Inferences
- Best format for (spec → Gherkin) pairs: the article text is the specification, and each `#[test]` scope becomes a Scénario. `définition x égal à v` maps to "Étant donné x = v", `règle … rempli` maps to "Et <condition> est vraie", and `assertion f.o = v` maps to "Alors o vaut v". Test identifiers are terse (Test1…), so scenario titles must be synthesised.
- The ASP `bcae7` folder pairs official PDF specs (fiches techniques) with Catala code and tests. That is a rare real "cahier des charges → règles → tests" triplet. Check that the PDFs are reusable (official ASP/ministry documents).
- The impot_revenu part is CeCILL 2.1 (GPL-compatible copyleft), so track it separately from the Apache-2.0 parts.

### Gaps
- catala-lang.org did not render, so I have no primary statement on the DGFiP or CNAF production go-live date or scope. The DGFiP's production use of Catala for IR is not confirmed beyond the copyright header. Which CNAF benefits will be migrated, and the timeline, is not found.
- I did not verify the state of `CatalaLang/french-law` in 2026.

## Q3. Publicodes ecosystem (beta.gouv, URSSAF, ADEME, SocialGouv)

### Takeaway
Publicodes models are French YAML rules ("`règle . sous-règle:`") with `titre`, `description`, `question`, `note` and `références` (legal URLs) fields. They are almost all **MIT**. The most valuable for Gherkin is **Code du travail numérique**: 48 conventions collectives, each with publicodes YAML rules carrying Légifrance article references, and 560 `*.spec.ts` files of `{situation → expectedResult + expectedReferences}`. Next is **mon-entreprise** (41 Vitest files, about 390 `it/test` cases written as French `describe/it` sentences, already near-BDD).

### Cited Findings
- Publicodes engine: https://github.com/publicodes/publicodes, MIT ("Copyright (c) 2018-2021 beta.gouv.fr"), last commit 2026-10-14. — [publicodes](https://github.com/publicodes/publicodes)
- mon-entreprise (URSSAF / beta.gouv): https://github.com/betagouv/mon-entreprise, MIT, last commit 2026-10-05 (LODEOM refactor). Models:
  - `modele-social` (salarié, entreprise, cotisations): 61 `.publicodes` files, about 657 top-level rules (my rough regex count)
  - `modele-ti` (indépendants): 42 files, about 222 rules
  - `modele-as` (assimilé salarié): 14 files, about 90 rules
  - `modele-commun`: 12 files, about 82 rules
  - each model's package.json says `"license": "MIT"`
  — [mon-entreprise](https://github.com/betagouv/mon-entreprise)
- Rule sample, from `modele-social/règles/entreprise/catégorie-juridique.publicodes`: `entreprise . catégorie juridique:` with `question: Quelle est la catégorie juridique de l'entreprise ?`, `note: On se base ici sur les catégories juridiques définies par l'INSEE`, `références: Liste des catégories juridique de l'INSEE: https://www.insee.fr/fr/information/2028129` and `une possibilité: [EI, SARL, SAS, …]`. — [modele-social/règles](https://github.com/betagouv/mon-entreprise/tree/master/modele-social/r%C3%A8gles)
- Tests: `site/test/` has 41 `*.test.ts` files (≈390 `it(`/`test(` calls). They include `modele-social/salarié/{apprentissage,RGDU,coefficientT,lodeom,professionnalisation}.test.ts` and snapshot regressions in `site/test/regressions/`. Sample from `apprentissage.test.ts`:
  ```ts
  describe('En contrat d'apprentissage', () => {
   describe('la rémunération minimale', () => { describe('la 1ère année', () => {
    const situation = {'salarié . contrat': "'apprentissage'", "salarié . contrat . date d'embauche": '18/02/2026'}
    it('est de 27% du Smic pour les apprenti⋅es de moins de 18 ans', () => {
      const e = engine.setSituation({...situation, 'salarié . contrat . apprentissage . âge': "'moins de 18'"})
      expect(e).toEvaluate('salarié . contrat . apprentissage . rémunération minimale', Math.round(0.27 * Smic))
  ```
  — [site/test](https://github.com/betagouv/mon-entreprise/tree/master/site/test)
- Code du travail numérique (SocialGouv / Ministère du Travail): https://github.com/SocialGouv/code-du-travail-numerique, last commit 2026-10-13. Licence conflict: the root `LICENSE` file is **Apache-2.0**, but the root `package.json` says `"license": "MIT"`. The package `packages/code-du-travail-modeles` has publicodes engines for préavis de démission/licenciement/retraite, indemnité de licenciement/précarité/retraite/départ, rupture conventionnelle and heures de recherche d'emploi. Counts: 371 YAML rule files, 612 test files under `src`, 48 convention-collective folders (e.g. `1597_batiment_employes_ouvriers_bis/` with `preavis-demission.yaml`, `indemnite-licenciement.yaml`, … and `__tests__/<simulateur>/calculate.spec.ts`), and 560 `.spec.ts` files under `conventions/`. — [code-du-travail-modeles](https://github.com/SocialGouv/code-du-travail-numerique/tree/master/packages/code-du-travail-modeles)
- CDTN rule sample (`1597_…/preavis-demission.yaml`):
  ```yaml
  contrat salarié . convention collective . batiment ouvriers employés bis . ancienneté:
    titre: Ancienneté
    description: L'ancienneté du salarié est habituellement mentionnée sur le <strong>bulletin de salaire</strong>.
    question: Quelle est l'ancienneté du salarié ?
  … . ancienneté Plus de 3 mois . résultat conventionnel:
    valeur: 2 semaines
    remplace: contrat salarié . préavis de démission . résultat conventionnel
    références:
      "Article 10.1": https://www.legifrance.gouv.fr/affichIDCCArticle.do?...idArticle=KALIARTI000005776855...
  ```
  The matching test (`__tests__/preavis-demission/calculate.spec.ts`) is a `test.each([{ situation: {"…ancienneté": "'Plus de 3 mois'"}, expectedResult: {expectedValue: 2, unit: "semaines"}, expectedReferences: [{article: "Article 10.1", url: …}], expectedNotifications: [] }, …])`. — [1597 folder](https://github.com/SocialGouv/code-du-travail-numerique/tree/master/packages/code-du-travail-modeles/src/modeles/conventions/1597_batiment_employes_ouvriers_bis)
- Nos Gestes Climat (ADEME, incubateur-ademe): https://github.com/incubateur-ademe/nosgestesclimat, MIT (2024 Nos Gestes Climat), version 4.17.3 committed 2026-10-13. It has 102 publicodes/YAML files in `data/` (actions, empreinte, i18n, ui, utilisateur). Its tests are scripts (`testPersonas.mjs`, `testBornes.mjs`, `testSituationCoverage.mjs`…). `personas/personas-fr.yaml` has 10 personas, each a French narrative `description` plus a `situation` map (e.g. Yoram: "quarante ans, il habite Paris… végétalien…"). The domain is carbon footprint, not law. — [nosgestesclimat](https://github.com/incubateur-ademe/nosgestesclimat)
- Mes Aides Réno (renovation aids such as MaPrimeRénov'): https://github.com/betagouv/reno, MIT, last commit 2025-12-18. My clone has 53 publicodes/YAML files and **0** `*.test.*`/`*.spec.*` files. — [betagouv/reno](https://github.com/betagouv/reno); licence also listed as MIT at [ecosystem.code.gouv.fr](https://ecosystem.code.gouv.fr/hosts/GitHub/repositories/betagouv%2Freno)
- Mes Aides Vélo: https://github.com/mquandalle/mesaidesvelo (personal account, not an official org), **AGPL-3.0**, last commit 2026-05-26. It has only 1 YAML file and 1 Playwright navigation spec. Its aid data is generated from aides-jeunes (`data/benefits/aides-velo-generator.ts` in aides-jeunes). — [mesaidesvelo](https://github.com/mquandalle/mesaidesvelo)
- Agir (ADEME / beta.gouv): the repos `betagouv/agir-back` and `betagouv/agir-front` exist (confirmed with `git ls-remote`). I did not inspect them.

### Inferences
- CDTN is the best Gherkin source in the Publicodes family. Each spec item (question + rule + legal article) has an explicit expected result with unit and legal reference. Example: "Étant donné la convention collective 1597… Et une ancienneté de plus de 3 mois / Quand je calcule le préavis de démission / Alors le préavis est de 2 semaines / Et la référence est l'Article 10.1". With 48 CCs × about 7 simulators, the pairs number in the thousands.
- mon-entreprise `describe/it` strings are already French "Alors" sentences (e.g. "est de 27% du Smic pour les apprenti⋅es de moins de 18 ans"), so conversion is near-mechanical.
- The Publicodes `question` field yields natural Given-step phrasing ("Quelle est l'ancienneté du salarié ?" becomes "Étant donné que l'ancienneté du salarié est …").

### Gaps
- I have no precise rule count; the regex is approximate. Publicodes "tests in YAML" (if the project uses a dedicated test format) were not checked.
- I did not check Agir contents, licence or tests, nor other publicodes models (France Chaleur Urbaine, `betagouv/france-chaleur-urbaine`, exists).
- The CDTN licence conflict (Apache-2.0 vs MIT) is not resolved; check `packages/code-du-travail-modeles/package.json` (its licence field was not found by my grep).

## Q4. DGFiP calculette (M language), Mlang, aides-jeunes, others

### Takeaway
DGFiP publishes the M-language income-tax rules on Adullact under **CeCILL**. Mlang (GPL-3.0) ships `.irj` test files (inputs → expected results), but almost all of them (about 2,840 of 2,848) are random fuzzing cases, with only a handful of real ones. That corpus has poor natural-language value. aides-jeunes (1jeune1solution, AGPL-3.0) has 431 benefit YAML files, each pairing French natural-language `conditions` with structured `conditions_generales`. That is spec-like data, but without input→output test cases.

### Cited Findings
- Mlang: https://github.com/MLanguage/mlang, **GPL-3.0** (`LICENSE.txt`), last commit 2026-01-16 ("Réparation du build statique"). Its submodule `ir-calcul` points to https://gitlab.adullact.net/dgfip/ir-calcul.git. The README says Mlang was formalised from the codebase "previously released by the DGFiP on Adullact forge", and that "the system passes all the private DGFiP tests as of Sept. 2022". — [mlang](https://github.com/MLanguage/mlang)
- Mlang tests: 2,848 `.irj` files under `tests/{2018,2019,2020,2022,2023}` (mostly `fuzzing/`). Only 7 are not fuzzing (e.g. `2023/corr`). The format uses sections `#NOM`, `#ENTREES-PRIMITIF`, `#CONTROLES-PRIMITIF`, `#RESULTATS-PRIMITIF`, `#ENTREES-CORRECTIF`, `#CONTROLES-CORRECTIF` and `#RESULTATS-CORRECTIF`, with lines like `1CP/141065910` (tax-form box code / value). — [mlang/tests](https://github.com/MLanguage/mlang/tree/master/tests)
- ir-calcul: catalogued as "règles du moteur de calcul de l'impôt sur le revenu et de l'impôt sur la fortune immobilière" with licence **CeCILL-1.0** (catalog metadata), last pushed about a year before the snapshot. The DGFiP's own page says it publishes IR and PAS-rate source code for 2010–2024 incomes, ISF for 2011–2017 and IFI for 2018–2024. Related repo: `dgfip/impots-nationaux-revenu-patrimoine-particuliers/calculette-ir` (also CeCILL per catalog). — [ecosystem.code.gouv.fr ir-calcul](https://ecosystem.code.gouv.fr/hosts/gitlab.adullact.net/repositories/dgfip%2Fir-calcul); [impots.gouv.fr open data](https://www.impots.gouv.fr/ouverture-des-donnees-publiques-de-la-dgfip); [calculette-ir](https://data.code.gouv.fr/hosts/gitlab.adullact.net/repositories/dgfip%2Fimpots-nationaux-revenu-patrimoine-particuliers%2Fcalculette-ir/dependencies)
- The Adullact project page `gitlab.adullact.net/api/v4/projects/dgfip%2Fir-calcul` returned 404 in my test; the web URL returned 301. The repo may have moved; unverified.
- aides-jeunes (1jeune1solution, formerly Mes Aides lineage): https://github.com/betagouv/aides-jeunes, **AGPL-3.0** (LICENSE.md and package.json `"AGPL-3.0"`). Last commit 2026-10-07 (veille on a permis-de-conduire aid), so it is very active. It has 552 benefit YAML files in `data/benefits` (431 in `javascript/`, plus `openfisca/`, `dynamic/`, `additional-attributes`). It computes OpenFisca-based benefits through an `openfisca/` API wrapper. Tests are `tests/unit`, `tests/integration` (e.g. `caf-benefits.spec.ts`, `schema-validation-benefits-javascript.spec.ts`) and Cypress e2e. Sample benefit YAML:
  ```yaml
  label: aide au BAFA pour une session d'approfondissement ou de qualification
  institution: caf_haute_savoie
  description: L'aide au BAFA … est une aide locale mise à disposition par la CAF de la Haute-Savoie …
  conditions:
    - Avoir commencé une formation pour obtenir le brevet d'aptitude à la fonction d'animateur … (BAFA).
  montant: 109
  conditions_generales:
    - {type: age, operator: ">=", value: 16}
    - {type: departements, values: ["74"]}
  ```
  — [aides-jeunes](https://github.com/betagouv/aides-jeunes)

### Inferences
- aides-jeunes `conditions_generales` can be expanded synthetically into Gherkin boundary scenarios (age 15 → not eligible, 16 → eligible; département 74 vs other). The French `description`/`conditions` serve as the specification text. With 431 or more aids this is a large, clean source of eligibility rules, but the expected outputs must be generated, not read.
- The Mlang `.irj` files are cryptic (box codes, random values), so they are not useful for natural-language Gherkin unless mapped to the "brochure pratique" box labels.

### Gaps
- Not researched: France Travail (ex Pôle emploi) open-source rules, Info Retraite / M@rel simulator openness, the Etalab/DINUM "rules as code" programme, and Assemblée nationale LexImpact 2026 status. I found no evidence either way within the tool budget.
- The real (non-fuzzing) DGFiP test cases appear private ("private DGFiP tests"). Public test corpora for the M calculette are not confirmed.

## Q5. Summary inventory (for the report writer)

### Takeaway
Ranked by value for (specification → Gherkin) pairs:
1. CDTN publicodes + spec.ts (Apache-2.0/MIT, conflict)
2. Catala examples (Apache-2.0; IR part CeCILL-2.1)
3. OpenFisca-France YAML tests (AGPL-3.0)
4. mon-entreprise Vitest (MIT)
5. aides-jeunes benefit YAML (AGPL-3.0, rules without tests)
6. openfisca-paris / openfisca-france-local (AGPL-3.0)
7. Nos Gestes Climat personas (MIT, non-legal)
8. Mlang/DGFiP M (GPL-3.0 / CeCILL, low-value fuzz tests)
9. Mes Aides Réno (MIT, no tests)

### Cited Findings
| Project | Owner | Domain | Rule format | Test format | Volume (my clone) | Licence | Last commit |
|---|---|---|---|---|---|---|---|
| [openfisca-france](https://github.com/openfisca/openfisca-france) | OpenFisca community (IPP, Etalab, beta.gouv contributors) | tax, payroll, social benefits, housing aid | Python Variables + YAML parameters | YAML (`name/period/input/output`) | 843 test files, ~1.9–2.6k cases, 3,183 variables | AGPL-3.0 | 2026-10-01 |
| [openfisca-france-local](https://github.com/openfisca/openfisca-france-local) | OpenFisca / beta.gouv | local aids | same | same | 86 files, 251 cases | AGPL-3.0 | 2026-08-05 |
| [openfisca-paris](https://github.com/openfisca/openfisca-paris) | Ville de Paris / OpenFisca | Paris aids | same | same | 26 files, 122 cases | AGPL-3.0 | 2026-08-05 |
| [catala-examples](https://github.com/CatalaLang/catala-examples) | Inria + DGFiP, CNAF, ASP | AF, aides logement, IR, ASP aids, SMIC, successions | Catala literate `.catala_fr` with Légifrance text | `#[test]` scopes with `assertion` | ~64 FR files, ~87 test scopes, ~52k lines | Apache-2.0; impot_revenu CeCILL-2.1 | 2026-09-18 |
| [mon-entreprise](https://github.com/betagouv/mon-entreprise) | URSSAF / beta.gouv | cotisations, salaires, indépendants | Publicodes YAML | Vitest `describe/it` + snapshots | ~130 publicodes files, 41 test files (~390 cases) | MIT | 2026-10-05 |
| [code-du-travail-numerique](https://github.com/SocialGouv/code-du-travail-numerique) | SocialGouv / Min. Travail | labour law: préavis, indemnités, 48 CCs | Publicodes YAML + Légifrance refs | Jest `test.each` situation → result + refs | 371 YAML, 612 test files | Apache-2.0 (LICENSE) vs MIT (package.json) | 2026-10-13 |
| [nosgestesclimat](https://github.com/incubateur-ademe/nosgestesclimat) | ADEME | carbon footprint | Publicodes | personas + scripts | 102 files, 10 personas | MIT | 2026-10-13 |
| [reno (Mes Aides Réno)](https://github.com/betagouv/reno) | beta.gouv / Anah | renovation aids | Publicodes | none | 53 files | MIT | 2025-12-18 |
| [aides-jeunes](https://github.com/betagouv/aides-jeunes) | 1jeune1solution / beta.gouv | youth/local aids | YAML benefit descriptors + OpenFisca | unit/integration/Cypress | 552 benefit YAML | AGPL-3.0 | 2026-10-07 |
| [mlang](https://github.com/MLanguage/mlang) + [ir-calcul](https://ecosystem.code.gouv.fr/hosts/gitlab.adullact.net/repositories/dgfip%2Fir-calcul) | Inria / DGFiP | IR, IFI | M language | `.irj` | 2,848 irj (≈7 non-fuzz) | GPL-3.0 / CeCILL (catalog) | 2026-01-16 |
| [mesaidesvelo](https://github.com/mquandalle/mesaidesvelo) | individual (M. Quandalle) | bike aids | from aides-jeunes | Playwright nav | small | AGPL-3.0 | 2026-05-26 |

### Inferences
- All corpora are in French. Only Catala and CDTN embed or cite the legal article itself; OpenFisca has references on about 15% of variables (478 of 3,183).
- For permissive-licence-only training: Catala examples (Apache-2.0, excluding impot_revenu), mon-entreprise (MIT), Nos Gestes Climat (MIT), Mes Aides Réno (MIT) and probably CDTN.

### Gaps
- No stars or contributor stats (the GitHub API was blocked in this session).
- No information on any public Gherkin/`.feature` files in these repos. None were seen, but I did not systematically grep for them.
