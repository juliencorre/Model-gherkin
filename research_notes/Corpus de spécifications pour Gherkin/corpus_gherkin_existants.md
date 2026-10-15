# Corpus Gherkin/BDD existants et jeux de données exigence→Gherkin (focus FR et secteur public), état octobre 2026

Méthode : recherche de code GitHub (API de recherche de code via le connecteur GitHub, 15/10/2026), API Hugging Face (listes de datasets/modèles et arborescences de fichiers), arXiv, Zenodo, Mendeley, recherche web. Les « total_count » de la recherche de code GitHub sont des comptes de **fichiers correspondants sur la branche par défaut indexée**. Ce sont des estimations : les doublons et les forks sont possibles, et les requêtes sur une seule chaîne (ex. « language: fr ») attrapent aussi du bruit.

---

## 1. Dépôts open source du secteur public (France et francophonie) contenant des .feature en français

### Takeaway
On trouve sur GitHub un petit noyau (~600 à 700 fichiers) de Gherkin français de très bonne qualité issu de l'administration française. Il est concentré dans 6 à 8 dépôts : MTES-MCT/potentiel, etalab/data_pass, france-connect/sources, ProgrammeVitam/vitam-itests, betagouv/aplypro, betagouv/acces-cible, proconnect-gouv, numerique-gouv/oots-france. Aucun n'associe formellement chaque scénario à une user story. Les règles métier sont pourtant explicites dans les titres de Fonctionnalité/Scénario, et le dépôt `potentiel` est le meilleur candidat « règles métier administratives ». Je n'ai trouvé aucun résultat chez SocialGouv ni pass-culture.

### Cited Findings
**Inventaire des dépôts (comptes = fichiers .feature correspondants, recherche de code GitHub du 15/10/2026)**

| Dépôt | Propriétaire / contexte | Langue | Taille approx. | Couplé à spec ? | Qualité / notes | Licence | Statut |
|---|---|---|---|---|---|---|---|
| [MTES-MCT/potentiel](https://github.com/MTES-MCT/potentiel) | Ministère de la Transition écologique (beta.gouv). Parcours administratif des projets EnR lauréats d'appels d'offres CRE | FR (`# language: fr`) | 121 fichiers contenant « Fonctionnalité » pour toute l'org MTES-MCT, presque tous dans `packages/specifications/src/**` de potentiel. Plusieurs scénarios par fichier, soit plusieurs centaines de scénarios | Non (pas de user story liée). Le titre de la Fonctionnalité porte le cas d'usage et les scénarios « Impossible de … si … » encodent les règles métier | Excellente. Style déclaratif métier (« Etant donné le projet lauréat … », « Alors le porteur devrait être informé que "Le cahier des charges de ce projet ne permet pas ce changement" »), tables de données, Contexte, tags (@délai). Organisation DDD par agrégat (abandon, délai, recours, garanties financières, raccordement…) | AGPL-3.0 | Actif (push 14/10/2026) |
| [etalab/data_pass](https://github.com/etalab/data_pass) | DINUM/Etalab. Habilitations d'accès aux API/données | FR | 142 fichiers « Fonctionnalité » pour l'org etalab, presque tous data_pass | Non | Bonne. Style UI/impératif (connexion, FAQ, session expirée, accessibilité) | Pas de licence détectée par l'API GitHub (`None`). À vérifier dans le dépôt | Actif (14/10/2026) |
| [france-connect/sources](https://github.com/france-connect/sources) | DINUM/FranceConnect. Fédération d'identité | FR | 131 fichiers « Fonctionnalité » (`quality/fcp/…`, `quality/partners/…`, tests Cypress) | Non | Bonne mais technique (API token/userinfo, RNIPP, fraude, idp_hint). Beaucoup de steps techniques | NOASSERTION (licence non standard, à lire) | Actif (12/10/2026) |
| [ProgrammeVitam/vitam-itests](https://github.com/ProgrammeVitam/vitam-itests) (+ vitam-itests-OLD) | Programme interministériel Vitam (archivage numérique) | FR | 111 fichiers contenant « Scénario » | Non | Tests d'intégration métier archivage (ingest, audit, DIP, profils, stockage) | Pas de licence détectée (`None`). Vitam est publié sous CeCILL 2.1 en général, à vérifier pour ce dépôt | Actif (01/10/2026) |
| [betagouv/aplypro](https://github.com/betagouv/aplypro) | beta.gouv / MENJ-MASA. Allocation des lycéens pro (PFMP, paiements ASP) | FR | ~35 des 53 fichiers « Fonctionnalité » de l'org betagouv | Non, mais les règles de calcul sont explicites (ex. « rémunérée à 10 euros par jour et plafonnée à 100 euros par an », scénarios montant original/plafonné) | Très bonne pour des règles métier chiffrées. Mot-clé « Sachant que », « Et que » | MIT | Actif (09/10/2026) |
| [betagouv/acces-cible](https://github.com/betagouv/acces-cible) | beta.gouv. Contrôle d'accessibilité des sites publics | FR | ~12 fichiers | Non | Bonne (vérification de déclaration d'accessibilité, schéma pluriannuel, CSV) | MIT | Actif |
| betagouv/standards, standards-front, doc.incubateur.net-communaute, betagouv-cucumber-steps, omniauth-proconnect-demo | beta.gouv | FR | quelques fichiers chacun | Non | `vérification-des-standards.feature` décrit les standards beta.gouv en Gherkin. betagouv-cucumber-steps = bibliothèque de steps FR réutilisables | non vérifié | — |
| [proconnect-gouv/proconnect-espace-partenaires](https://github.com/proconnect-gouv/proconnect-espace-partenaires), proconnect-gouv/federation, proconnect-test-client | DINUM/ProConnect | FR | 58 fichiers « Scénario » pour l'org | Non | Tests e2e UUV/Cypress (404, accueil, docs, recherche) | NOASSERTION | Actif |
| [numerique-gouv/oots-france](https://github.com/numerique-gouv/oots-france) | DINUM. Interfaçage avec le système européen OOTS (Once-Only) | FR | 17 fichiers « Scénario » | Non | Bon (prévisualisation de pièces justificatives) | Apache-2.0 | Actif |
| MTES-MCT/verseau2 | MTES | FR | quelques fichiers e2e (dépôt, authentification) | Non | — | non vérifié | — |
| PDP-Libre/PA_Communautaire | Communauté « plateforme agréée » facturation électronique (contexte réforme e-invoicing FR) | FR | ~6 fichiers sous `docs/briques/…` (ESB, routage Peppol, gestion cycle de vie) | Gherkin intégré à la doc des briques | Intéressant : Gherkin utilisé comme spécification | non vérifié | — |
| [MieuxVoter/mv-api-features-fr](https://github.com/MieuxVoter/mv-api-features-fr) | Association (jugement majoritaire) | FR | plusieurs fichiers | Liées à une spec OpenAPI | Spécification d'API en Gherkin FR | pas de licence détectée | push 02/2026 |
| [Hypertopic/Porphyry](https://github.com/Hypertopic/Porphyry), Hypertopic/HyperGlosae | Université de technologie de Troyes (recherche) | FR | ~25 et ~20 fichiers | Non | Bonne. User-centric, très lisible | Porphyry : AGPL-3.0 | Porphyry inactif depuis 2023 |
| [e2e-test-quest/uuv](https://github.com/e2e-test-quest/uuv) | Outil e2e (Cypress/Playwright) avec dictionnaire de steps FR, RGAA | FR + EN | ~15 fichiers fr-* | Non | Steps génériques UI/accessibilité. Utile pour le vocabulaire, pas pour les règles métier | MIT | Actif |

— comptes et chemins : recherche de code GitHub (`"Fonctionnalité" extension:feature org:<org>`, `"Scénario" extension:feature org:<org>`, `"language: fr" extension:feature`). Licences et dates de push : API GitHub search/repositories (15/10/2026).

- `"Fonctionnalité" extension:feature org:betagouv` → 53 fichiers. `org:MTES-MCT` → 121. `org:etalab` → 142. `org:france-connect` → 131. `org:SocialGouv` → 0 — [GitHub code search](https://github.com/search?type=code&q=%22Fonctionnalit%C3%A9%22+extension%3Afeature)
- `"Scénario" extension:feature`, repo ProgrammeVitam/vitam-itests → 111. Org numerique-gouv → 17. Org proconnect-gouv → 58. Org pass-culture → 0. Org demarches-simplifiees → 0 (résultat marqué « incomplete ») — [GitHub code search](https://github.com/search?type=code&q=%22Sc%C3%A9nario%22+extension%3Afeature)
- Extrait vérifié de potentiel (`demanderDélai.feature`) : `# language: fr`, `@délai`, Contexte avec table, 5 scénarios dont 4 scénarios de rejet encodant une règle métier — [potentiel/demanderDélai.feature](https://github.com/MTES-MCT/potentiel/blob/main/packages/specifications/src/projet/lauréat/délai/demanderDélai.feature)
- Extrait vérifié d'aplypro (`calcul_des_montants.feature`) : règle « 10 euros par jour et plafonnée à 100 euros par an » déclinée en scénarios montant original / plafonné / plafonné par une autre PFMP — [aplypro/calcul_des_montants.feature](https://github.com/betagouv/aplypro/blob/main/features/calcul_des_montants.feature)

### Inferences
- Les meilleurs exemples « règles métier administratives → Gherkin » sont potentiel (AGPL, déclaratif, règles de rejet), aplypro (MIT, règles de calcul) et oots-france (Apache-2.0). data_pass et FranceConnect relèvent davantage du test UI/API.
- On peut fabriquer une paire (spec → Gherkin) par rétro-ingénierie : rédiger ou faire générer la règle métier à partir des titres de scénario, puis la faire valider par un humain. Une autre voie consiste à exploiter les docs, issues ou PR liées, non vérifié ici.
- Licences pour l'entraînement : MIT et Apache-2.0 posent peu de problèmes (attribution). AGPL-3.0 (potentiel, Porphyry) : l'usage en entraînement est juridiquement débattu. Si le modèle ou le corpus est redistribué, il vaut mieux tracer la provenance et consulter un juriste. NOASSERTION ou absence de licence (data_pass, FranceConnect, vitam-itests, proconnect) : à vérifier dépôt par dépôt avant tout usage.
- Volume du noyau public FR : de l'ordre de 600 à 700 fichiers, soit probablement 2 000 à 4 000 scénarios. C'est une estimation non mesurée.

### Gaps
- Je n'ai pas compté les scénarios exacts par dépôt : il faudrait cloner les dépôts et les parser avec gherkin-official.
- Je n'ai pas exploré gitlab.adullact.net, la forge de France Travail, le GitLab de La Suite numérique ni les dépôts belges, suisses ou québécois. La recherche de code GitHub ne couvre pas GitLab, et le temps a manqué.
- code.gouv.fr ne permet pas de filtrer par présence de .feature. Je n'ai pas fait d'analyse croisée.
- Démarches simplifiées / demarche.numerique.gouv.fr : la recherche était incomplète. Le projet utilise RSpec/Capybara, sans Gherkin connu, ce qui reste non confirmé.
- La licence de data_pass et de vitam-itests n'est pas détectée par GitHub : il faut lire LICENSE ou le README.

---

## 2. Volume global du Gherkin français sur GitHub, dans The Stack (v1/v2) et Software Heritage

### Takeaway
Le Gherkin français reste un marché de niche. Sur GitHub, on compte environ 850 fichiers contenant « Étant donné » et environ 2 800 contenant « language: fr », bruit compris, contre environ 668 000 .feature contenant « Scenario ». Le français pèse donc moins de 1 % du total. The Stack v1 et sa version dédupliquée incluent un sous-ensemble `data/cucumber`, et The Stack v2 un sous-ensemble `data/Gherkin`. Les deux sont gated sur Hugging Face, et on pourrait y extraire le FR en filtrant sur `# language: fr`.

### Cited Findings
- `"language: fr" extension:feature` → 2 808 fichiers. Cela inclut des exemples i18n de cucumber-ruby, behave et sonar-gherkin-plugin, et beaucoup de projets étudiants ou personnels — [GitHub code search](https://github.com/search?type=code&q=%22language%3A+fr%22+extension%3Afeature)
- `"Étant donné" extension:feature` → 854 fichiers. Ce compte n'inclut pas les variantes « Etant donné » sans accent ni « Soit » / « Sachant que », qui sont très fréquentes : potentiel utilise « Etant donné », aplypro « Sachant que » — [GitHub code search](https://github.com/search?type=code&q=%22%C3%89tant+donn%C3%A9%22+extension%3Afeature)
- `"Scenario" extension:feature` → 667 648 fichiers, ce qui donne l'ordre de grandeur pour l'anglais — [GitHub code search](https://github.com/search?type=code&q=%22Scenario%22+extension%3Afeature)
- The Stack (v1) et The Stack dedup contiennent un répertoire `data/cucumber`. C'est un fichier parquet d'environ 91,5 Mo (the-stack) et d'environ 94,7 Mo (the-stack-dedup), mesuré via l'API tree Hugging Face. Les datasets sont gated (« gated: auto ») — [bigcode/the-stack-dedup](https://huggingface.co/datasets/bigcode/the-stack-dedup), [bigcode/the-stack](https://huggingface.co/datasets/bigcode/the-stack)
- The Stack v2 contient un répertoire `data/Gherkin`, un parquet d'environ 126,4 Mo. Dans v2, ces parquets contiennent des métadonnées et des identifiants Software Heritage, et le contenu se télécharge à part depuis Software Heritage, conformément à la conception de v2. Le dataset est gated et je n'ai pas pu en compter les lignes — [bigcode/the-stack-v2](https://huggingface.co/datasets/bigcode/the-stack-v2)
- The Stack v1 ne retient que des fichiers sous licences permissives, détectées au niveau du dépôt, et propose un mécanisme d'opt-out (« Am I in The Stack ») — [Kocetkov et al., The Stack, arXiv:2211.15533](https://arxiv.org/abs/2211.15533)

### Inferences
- Les AGPL (potentiel) sont exclus de The Stack v1, qui ne garde que les licences permissives. Le corpus public FR le plus riche doit donc être collecté directement sur GitHub. The Stack v1 offre en revanche une base anglaise et multilingue déjà filtrée par licence, utilisable pour un pré-entraînement ou une adaptation au format.
- Pour estimer la part FR de The Stack, il faut accepter les conditions sur HF puis filtrer `content` sur `^#\s*language:\s*fr` ou sur les mots-clés FR de gherkin-languages.json.

### Gaps
- Je n'ai pas obtenu le nombre de fichiers ni de fichiers FR dans les sous-ensembles cucumber et Gherkin de The Stack (accès gated, pyarrow indisponible ici).
- Je n'ai pas fait de requête Software Heritage directe (archive.softwareheritage.org n'a pas de recherche plein texte par extension accessible simplement).

---

## 3. Datasets et benchmarks existants (exigence / user story → Gherkin ; exigences en général)

### Takeaway
Il n'existe pas de benchmark public de référence en français. Côté anglais, on trouve trois choses : des datasets synthétiques sur Hugging Face, le plus gros étant gherkin-english-100k (100k paires, Apache-2.0, synthétique) ; le dataset SelfBehave (Zenodo, CC BY 4.0) ; et des corpus d'exigences sans Gherkin (PURE, user stories de Dalpiaz, TAWOS). Le dataset industriel de 500 triplets user story / description / scénario (arXiv 2603.04729) n'a pas de mise à disposition publique annoncée.

### Cited Findings
**Hugging Face – datasets Gherkin (API HF, 15/10/2026)**

| Dataset | Langue | Taille | Paires spec→Gherkin ? | Licence | Notes |
|---|---|---|---|---|---|
| [KavinduHansaka/gherkin-english-100k](https://huggingface.co/datasets/KavinduHansaka/gherkin-english-100k) | EN | 100 000 (5 shards JSONL × 20k) | Oui : `input_text` (paragraphe d'exigence) → `gherkin` (Feature, Rule/Background optionnels, 2 à 4 Scenarios ou Scenario Outline + Examples), plus `tags` | Apache-2.0 | **Synthétique**, généré « GPT-5 style », anonymisé. MAJ 10/2025, 28 téléchargements |
| [Ghaythfd/gherkin-scenarios](https://huggingface.co/datasets/Ghaythfd/gherkin-scenarios) | EN | moins de 1K | Oui (instruction → réponse, format ShareGPT) | Apache-2.0 | Domaines entreprise : import/export CSV/JSON/Excel, navigation, API REST/SOAP, ordonnancement, IBOR (finance). MAJ 12/2025. Un LoRA associé existe : Ghaythfd/gherkin-deepseek-lora |
| [ethanker/gherkin-agent-trajectories](https://huggingface.co/datasets/ethanker/gherkin-agent-trajectories) | EN | moins de 1K | Feature → code de steps Python, plus validation pytest | non indiquée | Extrait de vrais dépôts (champs repo_url, feature_text, python_files). Utile pour les steps, pas pour spec→Gherkin |
| [yashpalsharma/UserStoryToTestScenarios](https://huggingface.co/datasets/yashpalsharma/UserStoryToTestScenarios) | EN | moins de 1K (train/test CSV) | User story → scénarios de test | Apache-2.0 | Petit |
| [romanmarcu/bdd_gherkin_data](https://huggingface.co/datasets/romanmarcu/bdd_gherkin_data) | ? | ? | ? | Apache-2.0 | Carte vide |
| [OussamaFajrE/GherkinSyntax](https://huggingface.co/datasets/OussamaFajrE/GherkinSyntax) | ? | moins de 1K | ? | MIT | Carte vide (2023) |
| [damladalyanci/gherkin-test-dataset](https://huggingface.co/datasets/damladalyanci/gherkin-test-dataset) | EN | 5 exemples | scenario/steps | non indiquée | Négligeable |
| [udaykiran19491/user-stories-from-tawos-for-llm-fine-tuning](https://huggingface.co/datasets/udaykiran19491/user-stories-from-tawos-for-llm-fine-tuning) | EN | 10K à 100K | User stories seules (TAWOS, issues Jira open source) | Apache-2.0 (déclarée par l'uploader) | Pas de Gherkin |

— source : [API HF datasets?search=gherkin](https://huggingface.co/api/datasets?search=gherkin), [?search=user-stor](https://huggingface.co/api/datasets?search=user-stor) ; cartes README consultées.

**Modèles fine-tunés « gherkin » sur HF (signal sur les tailles utilisées)** : nalmeida/zephyr-7b-beta-gherkin (+ GGUF), nalmeida/Zephyr-Gherkin-Mistral-Instruct(-v2), IntissarJr/llama2-7b-qlora-gherkin, Minhhuyz/StarCoderBase-1b-Edit-LoRA-Gherkin, Smit1208/gherkin-generator (+ variante T5-LoRA, GGUF par mradermacher), Ghaythfd/gherkin-deepseek-lora, metindeder/Llama-3-Gherkin-QA-Expert, mrchrislau/feedback-to-gherkin-lora — [API HF models?search=gherkin](https://huggingface.co/api/models?search=gherkin). Tous ont peu de téléchargements (0 à 28) et aucun n'est en français.

**Datasets académiques**
- **SelfBehave** (Galloy, Balfroid, Vanderose, Devroey – Univ. Namur, ICSTW 2025 / A-MOST). Dataset BDD synthétique produit par SELF-INSTRUCT à partir de deux jeux de 175 scénarios seeds (l'un conforme aux critères de qualité, l'autre non). Le package de réplication fait 267,4 Mo, licence **CC BY 4.0**. Le code est sur GitHub snail-unamur/self-instruct — [SNAIL page](https://snail.info.unamur.be/publication/galloy-2025/), [Zenodo 14054404](https://zenodo.org/records/14054404)
- **Dataset Rathnayake, Shahin, Abaei (arXiv 2603.04729, mars 2026)** : 500 triplets user story / description d'exigence / scénario BDD, issus de 4 produits propriétaires d'une même entreprise. Les auteurs affirment ne connaître aucun dataset public de scénarios BDD pour évaluer les LLM. Aucune publication du dataset n'est indiquée — [arXiv 2603.04729](https://arxiv.org/abs/2603.04729)
- **PURE** (Ferrari, Spagnolo, Gnesi, RE 2017) : 79 documents d'exigences publics, 34 268 phrases, sans Gherkin. La licence CC BY 4.0 n'est indiquée que par Google Dataset Search, avec un avertissement du curateur sur les droits — [Zenodo 1414117](https://zenodo.org/records/1414117)
- **User stories de Dalpiaz** : 22 datasets de plus de 50 user stories chacun, v2 du 19/12/2024, DOI 10.17632/7zbk8zsd8y.2. Le curateur déclare ne connaître aucune licence ni droit de propriété intellectuelle, les données ayant été collectées sur le web, et il retire sur demande. Une version détaillée existe sur Zenodo 13880060. Pas de Gherkin — [Mendeley](https://data.mendeley.com/datasets/7zbk8zsd8y/2)
- Autres corpus de user stories : User Story NeoDataset (Mendeley), UStAI (arXiv 2504.00513) — [Mendeley NeoDataset](https://data.mendeley.com/datasets/skk2wn9j86), [UStAI](https://arxiv.org/pdf/2504.00513)
- Étude UFCG (Brésil, SBES 2025) : corpus de 1 286 descriptions de tests en texte libre, dont 10 échantillonnées pour comparer 7 LLM — [SBC SBES 2025](https://sol.sbc.org.br/index.php/sbes/article/view/36996)

### Inferences
- Aucune ressource ne fournit de paires FR spec→Gherkin. Le corpus cible devra être construit de trois façons : (1) le Gherkin public FR comme sorties, avec des spécifications reconstituées ; (2) des paires synthétiques FR inspirées de gherkin-english-100k et de SelfBehave ; (3) éventuellement la traduction de paires EN Apache-2.0.
- gherkin-english-100k est synthétique : il risque de transmettre le style et les biais du générateur. Il vaut mieux l'utiliser pour l'adaptation au format et réserver le Gherkin réel au fine-tuning final et à l'évaluation.

### Gaps
- Je n'ai pas ouvert Kaggle et Papers with Code (ce dernier est fermé et redirigé vers HF depuis 2025, non vérifié ici). Je n'ai pas trouvé de dataset Kaggle Gherkin notable dans les recherches.
- Je n'ai trouvé aucun dataset d'exigences en français (cahiers des charges publics annotés) dans les sources consultées. Il resterait à explorer data.gouv.fr et les CCTP publics.
- Je n'ai pas vérifié le contenu exact (nombre de scénarios générés, modèle) du zip SelfBehave.

---

## 4. Résultats académiques et industriels sur la génération de Gherkin par LLM ou petit modèle (2024-2026)

### Takeaway
La littérature 2024-2026 évalue surtout de grands LLM propriétaires en prompting. La validité syntaxique est presque toujours élevée (environ 99 à 100 %). Les vraies difficultés sont la complétude, les cas négatifs, les hallucinations et le principe « un scénario = une intention ». La qualité de l'entrée (description détaillée de la règle plutôt qu'une user story seule) compte plus que la technique de prompt. Le fine-tuning de petits modèles (1B à 7B, LoRA/QLoRA/DoRA) apparaît dans des mémoires et des modèles HF, mais il manque encore une publication de référence comparative.

### Cited Findings
- **Rathnayake, Shahin, Abaei (arXiv 2603.04729, 03/2026)** : 500 user stories, GPT-4, Claude 3 et Gemini, avec DeepSeek comme évaluateur LLM. GPT-4 obtient la meilleure similarité textuelle et sémantique, mais Claude 3 est préféré par les experts humains et par le juge LLM. Le juge DeepSeek corrèle mieux avec les humains que les métriques de similarité. Le meilleur prompt dépend du modèle (zero-shot pour GPT-4, CoT pour Claude 3, few-shot pour Gemini). Les **descriptions détaillées d'exigences seules donnent des scénarios de haute qualité, les user stories seules de faible qualité**. Les meilleurs réglages sont température 0 et top_p 1.0 — [arXiv 2603.04729](https://arxiv.org/abs/2603.04729)
- **Hassani, Sabetzadeh, Amyot, « From Law to Gherkin » (arXiv 2508.20744, accepté à IST, v2 03/2026)** : Gherkin produit par Claude et Llama à partir de réglementations de sécurité alimentaire. Les 60 spécifications ont été évaluées par 10 participants (120 évaluations) : pertinence 95 %, clarté 100 %, complétude 94,2 %, singularité 93,4 %, gain de temps 91,7 %. Aucune différence significative entre les LLM. Les auteurs relèvent des omissions, des hallucinations et des intentions mélangées, et concluent que « omissions and hallucinations require systematic human review ». C'est le cas le plus proche du besoin (texte normatif → Gherkin) — [arXiv 2508.20744](https://arxiv.org/abs/2508.20744)
- **Siddeeq et al., « Epic-Organized vs. Requirement-Aligned Gherkin » (arXiv 2607.01980, SEET 2026)** : 107 exigences issues de 4 documents PURE. Le pipeline « Timeless » (organisation par épopée, sortie JSON contrainte) atteint 100 % de validité structurelle, contre 99 % pour la baseline zero-shot. La couverture sémantique des exigences est de 94,3 % contre 92,9 %. Les experts le préfèrent sur la correction (4,61 contre 4,14), l'exécutabilité (4,61 contre 4,07) et la complétude (4,31 contre 3,50). TF-IDF sous-estime la couverture des sorties paraphrasées — [arXiv 2607.01980](https://arxiv.org/abs/2607.01980)
- **Industriel (arXiv 2504.07244, 2025)** : GPT-4 Turbo génère des tests d'acceptation Gherkin évalués par des product owners. Une expérience antérieure sur 50 user stories ne relève qu'un seul fichier .feature avec une erreur de syntaxe. Pour l'étape Gherkin → Cypress, le fine-tuning a été jugé inutile, le prompting suffisant — [arXiv 2504.07244](https://arxiv.org/pdf/2504.07244)
- **LLM-as-a-Judge pour la couverture de tests (arXiv 2512.01232)** : Gherkin généré par GPT-4.1 à partir de 100 tickets Jira rédigés à la main, puis couverture évaluée par un juge LLM — [arXiv 2512.01232](https://www.arxiv.org/pdf/2512.01232)
- **SelfBehave (ICSTW 2025)** : la qualité des seeds n'influence pas significativement la complétude ni le caractère essentiel des scénarios générés. Elle influence en revanche le respect du principe « une action, un résultat » et des règles syntaxiques Gherkin. Les évaluateurs s'accordent sur la qualité globale mais divergent critère par critère, d'où le besoin de critères plus faciles à appliquer — [SNAIL](https://snail.info.unamur.be/publication/galloy-2025/)
- **Étude comparative UFCG (SBES 2025)** : 7 modèles (GPT-4 Turbo, LLaMA 3, Phi-3, Gemini, DeepSeek R1…). Le zero-shot simple fait aussi bien que le one-shot et le few-shot, et Gemini offre le meilleur compromis précision/stabilité — [SBES 2025](https://sol.sbc.org.br/index.php/sbes/article/view/36996)
- **Autre comparatif BDD** (cité dans les résultats de recherche) : GPT-4 obtient la meilleure validité syntaxique et tous les modèles peinent sur les scénarios négatifs — [Scitepress 2025](https://www.scitepress.org/Papers/2025/136836/136836.pdf)
- **Petits modèles** : un mémoire de master du NCI (Irlande) évalue StarCoder, DeepSeekCoder, Phi et TinyLlama avec DoRA et LoRA hybride pour générer du BDD — [NCI thesis](https://norma.ncirl.ie/9315/1/shruthichandrababu.pdf). Une étude empirique sur le fine-tuning LoRA pour la génération de cas de test (arXiv 2604.06946) rapporte que Llama s'améliore sur presque tous les critères après LoRA, y compris la justesse de format — [arXiv 2604.06946](https://arxiv.org/pdf/2604.06946)
- Les modèles HF existants confirment les tailles employées par la communauté : environ 1B (StarCoderBase-1b LoRA), T5 LoRA, 7B (Zephyr/Mistral, Llama-2 QLoRA), Llama-3 — [API HF models](https://huggingface.co/api/models?search=gherkin)

### Inferences
- Pour un petit modèle FR, la validité syntaxique ne suffira pas à différencier les candidats : il faut l'automatiser avec le parser officiel. L'évaluation doit plutôt porter sur la couverture des règles (une règle donnant au moins un scénario positif et un négatif), sur la singularité des scénarios et sur l'absence d'hallucination. Un juge LLM calibré sur un échantillon humain est préférable à BLEU/ROUGE.
- Le fait que les descriptions détaillées l'emportent sur les user stories favorise des entrées de type « règle de gestion » (textes réglementaires, fiches de règle). Cela correspond bien au contexte administratif FR.
- Je n'ai pas trouvé de travail publié sur la génération de Gherkin en français par LLM : le sujet est inédit.

### Gaps
- Je n'ai pas lu en détail le mémoire NCI ni arXiv 2604.06946 (tailles exactes, métriques).
- Je n'ai pas trouvé de publication ICSE/RE 2025-2026 spécifiquement consacrée à un SLM fine-tuné pour Gherkin, avec chiffres. La recherche n'est pas exhaustive (pas d'accès Google Scholar).

---

## 5. Outils pour construire et valider le corpus (parser, lint, frameworks FR)

### Takeaway
Le parser officiel Cucumber `gherkin` (MIT, v42.0.1, maintenu activement) gère 80 langues, dont le français et ses nombreux synonymes. Il permet la validation syntaxique, la normalisation et l'extraction structurée (AST/pickles) du corpus. gherkin-lint (ISC) et gherlint (MIT) ajoutent des règles de style.

### Cited Findings
- `gherkin-languages.json` contient 80 langues. Mots-clés `fr` : feature « Fonctionnalité » ; rule « Règle » ; background « Contexte » ; scenario « Exemple », « Scénario » ; scenarioOutline « Plan du scénario », « Plan du Scénario » ; examples « Exemples » ; given « Soit », « Sachant que/qu'/ », « Etant donné(e)(s) (que/qu') », « Étant donné(e)(s) (que/qu') » ; when « Quand », « Lorsque », « Lorsqu' » ; then « Alors », « Donc » ; and « Et », « Et que », « Et qu' » ; but « Mais », « Mais que », « Mais qu' » ; plus « * » — [cucumber/gherkin gherkin-languages.json](https://github.com/cucumber/gherkin/blob/main/gherkin-languages.json)
- cucumber/gherkin : licence MIT, dernier push le 14/10/2026. Paquets `@cucumber/gherkin` npm 42.0.1 (MIT) et `gherkin-official` PyPI 42.0.1 — [GitHub](https://github.com/cucumber/gherkin), [npm](https://www.npmjs.com/package/@cucumber/gherkin), [PyPI](https://pypi.org/project/gherkin-official/)
- gherkin-official prend aussi en charge le format Gherkin-in-Markdown (MDG) — [Tessl registry doc](https://tessl.io/registry/tessl/pypi-gherkin-official/files/docs/stream-processing.md)
- Linters : gherkin-lint 4.2.4 (npm, ISC) et gherlint 0.5.0 (PyPI, MIT) — [npm gherkin-lint](https://www.npmjs.com/package/gherkin-lint), [PyPI gherlint](https://pypi.org/project/gherlint/)
- Behat documente la localisation des mots-clés Gherkin — [Behat docs](https://docs.behat.org/en/latest/user_guide/gherkin.html). Behave a un test i18n FR (issue0597.feature) et cucumber-ruby fournit des exemples `examples/i18n/fr` — [GitHub code search](https://github.com/search?type=code&q=%22language%3A+fr%22+extension%3Afeature)
- Steps FR réutilisables : betagouv/betagouv-cucumber-steps et le dictionnaire FR d'UUV (MIT, Cypress/Playwright, steps RGAA et accessibilité) — [uuv](https://github.com/e2e-test-quest/uuv)
- Plugin SonarQube Gherkin (racodond/sonar-gherkin-plugin) avec cas de test FR — [GitHub code search](https://github.com/search?type=code&q=%22language%3A+fr%22+extension%3Afeature)

### Inferences
- Pipeline de corpus suggéré : collecte, puis parse avec gherkin-official (rejet des fichiers invalides). Viennent ensuite la normalisation des synonymes FR (« Etant donné » / « Étant donné » / « Soit » / « Sachant que ») si l'on veut un style de sortie homogène, la déduplication (forks, i18n d'exemple) et la lint (gherkin-lint, règles « un Quand par scénario », pas de scénario vide). Il faut enfin conserver la licence et le dépôt d'origine par exemple.
- La même pipeline sert de métrique automatique de validité syntaxique pour l'évaluation du modèle.

### Gaps
- Je n'ai pas vérifié en détail le support FR de SpecFlow/Reqnroll et de Karate. Reqnroll et SpecFlow reposent sur le parser Gherkin officiel, donc en principe sur les mêmes mots-clés, ce qui reste non vérifié. Karate n'utilise que les mots-clés anglais, également non vérifié.
- Je n'ai pas vérifié si gherkin-lint gère correctement `# language: fr` dans sa version 4.2.4.
