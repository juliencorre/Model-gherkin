# Spécifications de l'administration française avec règles de gestion numérotées (corpus Gherkin, état octobre 2026)

Périmètre : spécifications publiques françaises (État, opérateurs, organismes mandatés) qui contiennent des règles de gestion, contrôles ou exigences numérotés et testables. Recherche faite le 15/10/2026. Limites :
- impots.gouv.fr était en maintenance au moment de la recherche (« documentation indisponible »). Le contenu des archives de facturation électronique n'a donc pas été ouvert directement.
- Le dépôt GitHub de la FNFE-MPE n'était pas accessible depuis cette session.
- Les éléments non vérifiés sont signalés comme tels dans les rubriques Inférences ou Lacunes.

---

## Q1. Inventaire des sources : éditeur, titre, URL, format, volume, numérotation, exemples, langue, licence, formulation des règles

### Takeaway
Les sources les plus riches et les plus directement « gherkinisables » sont au nombre de quatre :
1. **Facturation électronique 2026.** DGFiP/AIFE : spécifications externes V3.2 du 30/04/2026, archive .zip avec dossier, annexes Excel de règles de gestion, exemples, XSD et swaggers. S'y ajoutent les normes AFNOR XP Z12-012/013/014 (gratuites) et les Schematrons FNFE-MPE BR-FR-CTC v1.4.0 sur GitHub.
2. **DSN.** Net-entreprises : cahier technique 2026.1.2 et 2027.1.2, avec un tableau Excel des « catégories, contrôles, datatypes et usages ».
3. **Référentiel INS de l'ANS.** Guide d'implémentation v3.0 avec des exigences [EXI] et des recommandations [RECO].
4. **RGAA 4.1.2.** 106 critères et leurs tests, disponibles en JSON sur GitHub DISIC/RGAA.

Viennent ensuite PES V2 / Hélios (XSD 5.30, liste des anomalies), Chorus Pro (règles G1.xx, G2.xx, G8.xx), le RGESN 2024 (78 critères) et les volets CI-SIS de l'ANS (exemples et outil de validation sur GitHub ansforge). SESAM-Vitale est derrière un espace industriels avec signature de licence, donc peu exploitable.

### Cited Findings

**A. Facturation électronique B2B 2026-2027 (DGFiP / AIFE / AFNOR / FNFE-MPE)**
- **Page officielle.** Version 3.2 des spécifications externes (BtoB, GtoB, BtoG) datée du 30/04/2026. Elle est listée comme la plus récente, devant les versions 3.1 et 3.0. — [impots.gouv.fr – Spécifications externes B2B](https://www.impots.gouv.fr/specifications-externes-b2b) (via résultats de recherche, la page n'ayant pas pu être lue pendant la maintenance)
- **Contenu de l'archive .zip.** Le téléchargement regroupe « Dossier de spécifications externes de la facturation électronique, annexes, exemples, XSD et swaggers (.zip) ». — [impots.gouv.fr](https://www.impots.gouv.fr/specifications-externes-b2b)
- **Versions antérieures.** Celles d'avant la V3.2, qui traitaient l'ensemble des flux, restent consultables. Selon une fiche FNFE-MPE, la v3.1 (specifications-externes-v3.1.zip) peut servir de référence complémentaire pour l'e-reporting, mais pas de référence pour la facture électronique. — [FNFE-MPE Fiche Flash documentation](https://fnfe-mpe.org/wp-content/uploads/2026/04/Fiche_Flash-Utilisation_documentation.new_.pdf)
- **Date contradictoire.** L'AIFE mentionne une nouvelle version publiée le 31/10/2025 qui fixe les attendus du démarrage au 01/09/2026. Cette date est à réconcilier avec la V3.2 du 30/04/2026. — [AIFE – Facturation électronique interentreprises](https://aife.economie.gouv.fr/nos-applications/facturation-electronique-b2b/)
- **« Annexe 7 – Règles de gestion ».** Fichier .xlsx avec un onglet « Règles de gestion PPF » (règles spécifiques françaises), un onglet « Règles de la norme EN16931 » et un onglet de versions. Une version 1.6 datée du 19/06/2024 circule (titre « 20240619-Annexe-7-Regles-de-Gestion-V1-6 »). Source secondaire (Scribd), contenu non vérifié directement. — [Scribd – Annexe 7 Règles de gestion V1.6](https://fr.scribd.com/document/831278060/20240619-Annexe-7-Regles-de-Gestion-V1-6)
- **Version plus ancienne.** Un dossier de spécifications externes « Cas d'usage » v2.3 (31/07/2023) existe en PDF. — [vatupdate (copie)](https://www.vatupdate.com/wp-content/uploads/2023/08/2023-07-31-Dossier-de-specifications-externes-de-la-facturation-electronique-Cas-dusage_v2.3.pdf)
- **Norme AFNOR XP Z12-012.** Elle porte sur les formats, profils et CDAR (cycle de vie), dans sa version de mai 2025. Elle est hébergée en PDF sur impots.gouv.fr. Un document associé contient un onglet « Règles de gestion 3.0 » et une section sur les règles applicables aux messages CDAR du cycle de vie. — [XP Z12-012 (impots.gouv.fr)](https://www.impots.gouv.fr/sites/default/files/media/1_metier/2_professionnel/EV/2_gestion/290_facturation_electronique/specification_externes_b2b/afnor/norme-afnor-factures.pdf) ; [impots.gouv.fr – factures norme afnor](https://www.impots.gouv.fr/factures-norme-afnor)
- **Annexes AFNOR.**
  - XP Z12-012 : Annexe A (Excel des formats/profils, règles de gestion, listes de codes) et Annexe B (exemples de factures et de CDAR).
  - XP Z12-013 : Swagger (V1.3) Flux et Annuaire, diagrammes de séquence.
  - XP Z12-014 : Annexe A avec 44 cas d'usage B2B, Annexe B avec des exemples de factures et de cycle de vie.
  - Les normes sont décrites comme gratuites (« allez chercher votre version gratuite » sur le site AFNOR).
  - Sources : [FNFE-MPE – Ressources](https://fnfe-mpe.org/ressources/) ; [e-invoicing-france.eu – V3.2 doc applicable (site non officiel)](https://www.e-invoicing-france.eu/documentation/specifications-externes-v3-2/Specification-externe-Version-3.2-7-documentation-applicable)
- **Schematrons FNFE-MPE v1.4.0** (correctif fix04 du 4 septembre 2026, fichier 2026_09_04_FNFE_SCHEMATRONS_FR_CTC_V1.4.0.04.zip). Ils couvrent :
  - les règles BR-FR-CTC en UBL et en CII ;
  - les CDAR (messages de cycle de vie) ;
  - les profils EN16931 et EXTENDED-CTC-FR.

  Ils sont publiés sur GitHub https://github.com/fnfempe/France_RFE (releases). — [FNFE-MPE – Ressources](https://fnfe-mpe.org/ressources/) ; v1.4.0 publiée le 30/06/2026 selon [vatupdate](https://www.vatupdate.com/?p=356943)
- **Schematrons EN 16931 européens.** Ils sont publiés sur GitHub ConnectingEurope/eInvoicing-EN16931, packages CII/UBL 1.3.14. Ils contiennent les règles BR-xx de la norme. Un projet tiers affiche par exemple « BR-29 (BT-74 ≥ BT-73) ». — [FNFE-MPE – Ressources](https://fnfe-mpe.org/ressources/) ; [hex.pm facturx README](https://repo.hex.pm/preview/facturx/0.5.0/README.md)
- **Validateur en ligne FNFE-MPE.** Disponible sur services.fnfe-mpe.org. La page ressources ne liste aucun fichier d'exemple Factur-X. — [FNFE-MPE – Ressources](https://fnfe-mpe.org/ressources/)
- **Licences.**
  - impots.gouv.fr : contenu sous « licence etalab-2.0 », sauf droits de propriété intellectuelle de tiers explicitement mentionnés. Les normes AFNOR hébergées sont probablement concernées par cette exception.
  - FNFE-MPE : la page ressources n'indique aucune licence.
  - Sources : [impots.gouv.fr (pied de page)](https://www.impots.gouv.fr/actualite/facturation-electronique-nouvelle-version-des-specifications-externes) ; [FNFE-MPE – Ressources](https://fnfe-mpe.org/ressources/)

**B. Chorus Pro (AIFE)**
- **Dossier de spécifications externes « Solution portail » V3.27 (30/06/2017).** Il est publié sur la Communauté Chorus Pro et les règles y sont numérotées par famille. Exemples :
  - modification de la longueur maximale du nom d'un tiers (G2.08) ;
  - création de G2.29 sur les caractères autorisés dans un « code service » ;
  - G8.49, et suppression de G8.44 dans le format E3.
  - Source : [communaute.chorus-pro.gouv.fr – DSE V3.27](https://communaute.chorus-pro.gouv.fr/wp-content/uploads/2017/08/20170630_Solution-portail_Dossier_Specifications_Externes_V3.27.pdf)
- **Version plus récente.** Un projet open source cite « External Specifications EDI Appendix V4.10 » (2018) comme source. — [docs.gobl.org](https://docs.gobl.org/addons/fr-choruspro-v1.md)

**C. DSN – Déclaration sociale nominative (GIP-MDS / net-entreprises)**
- **Norme 2026 en production :**
  - Cahier technique 2026.1.2 du 24/12/2025 (PDF) ;
  - JMN 2026.1.2 (PDF) ;
  - note différentielle CT2025.1.3 → CT2026.1.2 (PDF) ;
  - « Tableau des catégories, contrôles, datatypes et usages » (Excel) ;
  - « Tableau des usages DSN » (Excel).
  - Source : [net-entreprises – Norme et documentation DSN](https://www.net-entreprises.fr/declaration/norme-et-documentation-dsn)
- **Norme 2027 à venir.** Cahier technique 2027.1.2 du 09/09/2026, JMN, note différentielle et les mêmes tableaux Excel. Aucune étape de connexion n'est mentionnée pour le téléchargement. — [net-entreprises](https://www.net-entreprises.fr/declaration/norme-et-documentation-dsn)
- **Note différentielle CT2024.1 → CT2026.1.** Le CT2026.1.0 a été publié en avril 2025. — [net-entreprises – note différentielle](https://net-entreprises.fr/media/documentation/neores/dsn-note-differentielle-CT2024.1-CT2026.1.pdf)
- **Sémantique des contrôles.**
  - Un contrôle de cohérence CCH en erreur suffit à rejeter la DSN (Bilan d'anomalies).
  - Les contrôles SIG sont non bloquants.
  - Sans anomalie, la DSN reçoit un Certificat de conformité.
  - L'outil DSN-Val vérifie le cahier technique et le JMN.
  - Sources : [net-entreprises – outils de contrôle DSN-Val](https://www.net-entreprises.fr/declaration/outils-de-controle-dsn-val/) ; [JMN DSN 2026](https://www.net-entreprises.fr/media/documentation/jmn-dsn-2026.pdf)
- **Antécédent DADS-U.** Un document de contrôles « DADSU-CTL V01X16 » est publié en PDF. — [net-entreprises DADSU CTL](https://www.net-entreprises.fr/media/2022/01/DADSU-CTL-V01X16.pdf)
- **Licence et fiches consignes.** La page ne mentionne ni licence ni conditions de réutilisation, ni fiches consignes (base de connaissances : guide d'utilisation et tableau de concordance seulement). — [net-entreprises](https://www.net-entreprises.fr/declaration/norme-et-documentation-dsn)

**D. Secteur public local – PES V2 / Hélios (DGFiP, collectivites-locales.gouv.fr)**
- **Documents PES V2 :**
  - Schéma XSD 5.30 ;
  - « Dossier technique 5.30 » ;
  - « Guichet XML – Limites logicielles » ;
  - « Guichet XML – Liste des anomalies » ;
  - renvoi vers « les règles de gestion Hélios » en annexe.
  - Source : [collectivites-locales.gouv.fr – Le PES](https://www.collectivites-locales.gouv.fr/gerer-les-finances-publiques-locales/dematerialisation-des-comptes-locaux-et-open-data/dematerialisation-comptable-et-budgetaire/le-protocole-dechange-standard-pes)
- **Contrôle et base juridique.** Le guichet XML vérifie le respect du cahier des charges et de normes du référentiel. Le PES V2 est défini par l'arrêté du 27/06/2007 (art. D.1617-23 CGCT). — [collectivites-locales.gouv.fr](https://www.collectivites-locales.gouv.fr/node/1876)
- **Cahier des charges ASAP ORMC XML V2.** Ce format est autorisé à partir de Hélios 5.26 (juillet 2025). — [Cahier des charges ASAP ORMC XML V2](https://www.collectivites-locales.gouv.fr/files/files/2.%20Gérer%20les%20finances%20publiques%20locales/6.%20La%20dématérialisation%20des%20comptes%20locaux%20et%20l%27open%20data/Démat%20comptable/Le%20PES/Cahier%20des%20charges_ASAP_ORMC_XML-V2.pdf)
- **Instruction M57.** Tome III « protocoles informatiques » (2023) et Tome 3 2025. — [M57 Tome 3 2025](https://collectivites-locales.gouv.fr/files/finances_locales/M57/M57_Tome_3_2025_vdef.pdf)

**E. Santé – ANS / GIE SESAM-Vitale**
- **Guide d'implémentation INS v3.0 (décembre 2024).** Statut « validé », classé public, il accompagne le Référentiel INS v2.1 (arrêté JO du 13/12/2024).
  - Il est décrit comme des « spécifications fonctionnelles détaillées des modalités d'appels au téléservice INS ».
  - Les règles sont classées en exigences [EXI] et recommandations [RECO]. Certaines RECO sont devenues des EXI et le degré de criticité a été supprimé.
  - Règles citées : interdiction de pré-remplir par défaut les champs obligatoires ; le code INSEE du lieu de naissance inconnu ne doit « en aucun cas » être renseigné automatiquement par « 99999 » ; interdiction de présélectionner un type de dispositif de validation d'identité.
  - Sources : [ANS Guide Implémentation INS V3.0 (PDF)](https://industriels.esante.gouv.fr/sites/default/files/media/document/ANS_Guide-Implementation-INS_V3.0.pdf) ; [esante.gouv.fr – nouvelle version référentiel INS](https://esante.gouv.fr/actualites/nouvelle-version-referentiel-ins-etape-cle-gestion-donnees-sante)
- **CI-SIS (ANS).**
  - Le dépôt GitHub `ansforge/interop-exemples-xdm` contient des archives d'exemples IHE_XDM pour tous les volets CDA du CI-SIS.
  - `ansforge/interop-outil-cda-testcontenucda2.41-…` est un outil XSLT de conformité d'un document CDA R2 à son volet.
  - Seul `ansforge/IG-doctrine-ci-sis` affiche une licence (MIT) selon un agrégateur.
  - Sources : [data.code.gouv.fr – ansforge](https://data.code.gouv.fr/hosts/GitHub/repositories/ansforge%2FIG-doctrine-ci-sis) ; [repos.data.code.gouv.fr – topic example](https://repos.data.code.gouv.fr/topics/example)
- **SESAM-Vitale.** L'Espace Industriels est gratuit mais soumis à des CGU. L'accès aux derniers packages des API Lecture Vitale (v6.31) exige de signer un protocole et une licence d'exploitation. Un « cahier de tests » existe sur l'espace industriels. — [CGU espace industriels](https://industriels.sesam-vitale.fr/documents/d/global/cgu-1) ; [PDT-INF-400 API Lecture Vitale 6.31](https://sesam-vitale.fr/documents/20182/54782/PDT-INF-400-API_Lecture_Vitale_6.31.pdf)

**F. Référentiels à critères testables (DINUM / Arcep)**
- **RGAA 4.1.2.**
  - Organisation en thèmes, critères et tests numérotés.
  - Exemple de critère 1.1 : « Chaque image porteuse d'information a-t-elle une alternative textuelle ? ». Le test 1.1.1 commence par « Chaque image (balise `<img>` ou balise possédant l'attribut WAI-ARIA `role="img"`) … ».
  - Le thème 1 compte à lui seul 59 tests (1.1 en a 8, 1.3 en a 9, 1.6 en a 10).
  - Source : [accessibilite.numerique.gouv.fr – critères et tests](https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/)
- **Nombre de critères du RGAA 4.1.2 : 106.** Information tirée d'un article secondaire. — [journaldunet](https://www.journaldunet.com/seo/1549745-accessibilite-web-un-nouveau-defi-pour-le-seo/)
- **Données machine du RGAA.** Les fichiers `criteres.json` et `glossaire.json` sont publiés sur le dépôt GitHub DISIC/RGAA. Le Luxembourg (RAWeb) en a dérivé une adaptation sous CC-BY 3.0 LU. — [accessibilite.public.lu – licence](https://accessibilite.public.lu/en/licence.html)
- **Licence des documents DINUM.** Les documents de déclaration d'accessibilité DINUM sont sous Licence Ouverte 2.0. La licence propre du dépôt RGAA n'a pas été confirmée. — [exemple de déclaration RGAA4](https://accessibilite.numerique.gouv.fr/doc/rgaa4-2019-exemple-declaration.pdf)
- **RGESN v2 (17/05/2024).**
  - Publié par l'Arcep et l'Arcom avec l'ADEME, la DINUM, la CNIL et l'Inria.
  - 78 critères répartis en 9 thèmes. Chaque critère a trois attributs (difficulté, priorité, applicabilité) et une fiche de mise en œuvre et de vérification.
  - La version 2021 (environ 80 critères) était sous licence ouverte.
  - Sources : [ISIT wiki – RGESN](https://en.wiki.isit-europe.org/nr/RGESN) ; [data.gouv.fr – réutilisation RGESN](https://data.gouv.fr/en/reuses/consultation-web-du-referentiel-general-decoconception-de-services-numeriques-rgesn)

### Inferences
- **Meilleur rapport qualité / gherkinisabilité : la facturation électronique.** Elle réunit dans un même paquet :
  - des règles identifiées (BR-xx EN16931, BR-FR-xx / BR-FR-CTC françaises) ;
  - des règles de cycle de vie CDAR ;
  - des Schematrons exécutables ;
  - des exemples XML (Annexes B de Z12-012/014) ;
  - 44 cas d'usage B2B rédigés.

  On peut donc produire des paires (règle → scénario « Étant donné une facture … Quand … Alors rejet BR-FR-xx ») et les valider mécaniquement avec le Schematron. Le volume est de l'ordre de quelques centaines de règles : environ 200 BR EN16931 plus plusieurs dizaines de BR-FR, d'après la structure de l'annexe 7. Ce comptage est une estimation, non vérifiée.
- **Machine-readable par excellence : la DSN.** Le « Tableau des catégories, contrôles, datatypes et usages » en Excel est probablement la meilleure source tabulaire. Les contrôles CCH bloquants et SIG non bloquants donnent directement deux types d'issue « Alors » (rejet / signalement). Je n'ai pas pu vérifier le nombre de lignes, mais un cahier technique DSN compte typiquement plusieurs centaines de pages.
- **Formulation des règles.** Le RGAA et le RGESN, formulés en question et test, sont convertibles en scénarios d'audit (« Étant donné une page contenant une image porteuse d'information, Quand … Alors l'image a une alternative textuelle »). Ils relèvent plutôt du test d'interface que des règles métier. Le guide INS (EXI) est formulé en exigences « le logiciel doit / ne doit pas », bien adaptées au Gherkin.
- **Chorus Pro.** Les règles Gx.yy sont numérotées, mais les documents trouvés sont anciens (2017-2018). La facturation électronique 2026 les remplace largement.

### Gaps
- **Facturation électronique :**
  - contenu exact et nombre de règles BR-FR dans l'annexe 7 V3.2 non vérifiés (site impots.gouv.fr en maintenance) ;
  - aucune citation verbatim d'une règle BR-FR n'a pu être obtenue ;
  - licence du dépôt GitHub fnfempe/France_RFE non vérifiée (accès GitHub refusé dans cette session).
- **DSN :**
  - numérotation exacte des contrôles (format CCH-xx / SIG-xx) et formulation verbatim non vérifiées ;
  - licence des documents net-entreprises inconnue ;
  - existence de fichiers DSN d'exemple valides/invalides publics non confirmée.
- **Sources non couvertes faute de temps** (nombre de requêtes limité) : EDI-TVA, EDI-TDFC, EFI, API Impôt particulier, API Particulier/Entreprise, FranceConnect/ProConnect, Parcoursup, BAN, Sirene, CNAF/MSA/CNAV/Agirc-Arrco, France Travail, RGI/RGS/DSFR, Ségur/DMP, CCTP publiés sur BOAMP/PLACE et projets Adullact.
- **Volets CI-SIS :** formulation des règles et licence des dépôts d'exemples non vérifiées.

---

## Q2. Téléchargement libre et licences ouvertes

### Takeaway
La plupart des sources clés se téléchargent sans compte : impots.gouv.fr, net-entreprises, collectivites-locales.gouv.fr, esante.gouv.fr, accessibilite.numerique.gouv.fr, FNFE-MPE et GitHub.
- **Licence explicite et confirmée :** seul impots.gouv.fr déclare l'Etalab 2.0 au niveau du site (avec une réserve sur les droits de tiers).
- **Réserve AFNOR :** les normes AFNOR sont gratuites mais sous droits AFNOR.
- **Exception notable :** SESAM-Vitale exige la signature d'une licence d'exploitation.

### Cited Findings
- **impots.gouv.fr.** Contenu sous « licence etalab-2.0 », sauf propriété intellectuelle de tiers explicitement mentionnée. — [impots.gouv.fr](https://www.impots.gouv.fr/actualite/facturation-electronique-nouvelle-version-des-specifications-externes)
- **Normes AFNOR XP Z12-012/013/014.** Versions gratuites sur le site AFNOR, et une copie de Z12-012 est hébergée sur impots.gouv.fr. — [FNFE-MPE – Ressources](https://fnfe-mpe.org/ressources/) ; [XP Z12-012 sur impots.gouv.fr](https://www.impots.gouv.fr/sites/default/files/media/1_metier/2_professionnel/EV/2_gestion/290_facturation_electronique/specification_externes_b2b/afnor/norme-afnor-factures.pdf)
- **net-entreprises (DSN).** Liens directs vers les fichiers, sans connexion mentionnée. Aucune licence indiquée. — [net-entreprises](https://www.net-entreprises.fr/declaration/norme-et-documentation-dsn)
- **Guide INS v3.0.** Classé « public ». — [ANS Guide INS v3.0](https://industriels.esante.gouv.fr/sites/default/files/media/document/ANS_Guide-Implementation-INS_V3.0.pdf)
- **SESAM-Vitale.** Les CGU valent engagement, et la signature d'une licence d'exploitation est requise pour les packages API Lecture Vitale. — [CGU](https://industriels.sesam-vitale.fr/documents/d/global/cgu-1) ; [PDT-INF-400](https://sesam-vitale.fr/documents/20182/54782/PDT-INF-400-API_Lecture_Vitale_6.31.pdf)
- **RGAA.** Données JSON sur GitHub DISIC/RGAA. Une réutilisation dérivée (Luxembourg) est sous CC-BY 3.0 LU, ce qui implique que la source autorise la réutilisation. — [accessibilite.public.lu](https://accessibilite.public.lu/en/licence.html)
- **RGESN 2021.** Sous licence ouverte. — [ISIT wiki](https://en.wiki.isit-europe.org/nr/RGESN)
- **Dépôt ansforge/IG-doctrine-ci-sis.** Sous licence MIT selon un agrégateur. — [data.code.gouv.fr](https://data.code.gouv.fr/hosts/GitHub/repositories/ansforge%2FIG-doctrine-ci-sis)

### Inferences
- **Conditions de réutilisation.** Pour un corpus d'entraînement, le risque juridique est faible pour :
  - les spécifications externes DGFiP (Etalab 2.0) ;
  - le RGAA et le RGESN (licence ouverte) ;
  - les dépôts GitHub sous licence explicite.

  Il est incertain pour la DSN (pas de licence affichée, documents publics d'un GIP) et pour les annexes AFNOR (droits AFNOR). Il est élevé pour SESAM-Vitale (licence contractuelle).
- **Code des relations entre le public et l'administration.** Les documents administratifs publiés sont en principe réutilisables (art. L321-1 et suivants). Ce point, qui relève du cadre juridique général, n'a pas été vérifié dans cette recherche.

### Gaps
- **Licence non confirmée :** licences des dépôts GitHub DISIC/RGAA et fnfempe/France_RFE, et licence du RGESN 2024.
- **Mentions légales non consultées :** pages de mentions légales de net-entreprises et d'esante.gouv.fr.

---

## Q3. Règles lisibles par machine et fichiers de test

### Takeaway
Les sources directement exploitables pour générer et valider des scénarios Gherkin sont :
- **facturation électronique :** XSD, Schematrons BR-FR-CTC / EN16931, Excel de règles, exemples XML, swaggers ;
- **DSN :** Excel des contrôles, outil DSN-Val ;
- **PES V2 :** XSD 5.30, liste des anomalies du guichet XML ;
- **RGAA :** criteres.json ;
- **CI-SIS :** exemples XDM, outil XSLT de validation.

### Cited Findings
- **Facturation électronique.**
  - L'archive V3.2 contient des annexes, des exemples, des XSD et des swaggers. — [impots.gouv.fr](https://www.impots.gouv.fr/specifications-externes-b2b)
  - Les Schematrons BR-FR-CTC (UBL/CII), CDAR et EXTENDED-CTC-FR sont publiés en v1.4.0. — [FNFE-MPE](https://fnfe-mpe.org/ressources/)
  - Les Schematrons EN16931 1.3.14 sont sur GitHub ConnectingEurope. — [FNFE-MPE](https://fnfe-mpe.org/ressources/)
- **DSN.**
  - Le tableau Excel des contrôles existe pour les normes 2026 et 2027. — [net-entreprises](https://www.net-entreprises.fr/declaration/norme-et-documentation-dsn)
  - DSN-Val est l'outil d'autocontrôle. — [DSN-Val](https://www.net-entreprises.fr/declaration/outils-de-controle-dsn-val/)
- **PES V2.** XSD 5.30 et « Guichet XML – Liste des anomalies ». — [collectivites-locales.gouv.fr](https://www.collectivites-locales.gouv.fr/gerer-les-finances-publiques-locales/dematerialisation-des-comptes-locaux-et-open-data/dematerialisation-comptable-et-budgetaire/le-protocole-dechange-standard-pes)
- **RGAA.** `criteres.json` et `glossaire.json` sur GitHub. — [accessibilite.public.lu](https://accessibilite.public.lu/en/licence.html)
- **CI-SIS.** Exemples IHE_XDM pour tous les volets CDA et outil XSLT de validation. — [repos.data.code.gouv.fr](https://repos.data.code.gouv.fr/topics/example)
- **SESAM-Vitale.** Un cahier de tests existe, mais il est réservé. — [PDT-INF-400](https://sesam-vitale.fr/documents/20182/54782/PDT-INF-400-API_Lecture_Vitale_6.31.pdf)

### Inferences
- **Pipeline envisageable : génération de cas de test.** Muter des exemples XML valides de facturation électronique pour violer une règle BR-FR précise, puis utiliser le Schematron comme oracle. On obtient ainsi un triplet (règle, scénario Gherkin, fichier de test) vérifié automatiquement.
- **Pipeline envisageable : sources tabulaires.** L'Excel des contrôles DSN et la liste des anomalies PES se prêtent à une extraction ligne par ligne, une règle donnant un Scenario Outline.

### Gaps
- **DSN :** aucun jeu de fichiers DSN valides/invalides publics n'a été trouvé.
- **Facturation électronique :** le nombre exact d'exemples dans l'archive V3.2 n'a pas été vérifié.

---

## Q4. Volume réaliste à collecter

### Takeaway
L'ordre de grandeur réaliste se situe entre quelques milliers de règles ou critères identifiables et plusieurs milliers de pages. Cette estimation est en grande partie inférée, faute d'avoir pu ouvrir les archives.

### Cited Findings
- **RGAA 4.1.2 :** 106 critères, et le seul thème 1 compte 59 tests. — [journaldunet](https://www.journaldunet.com/seo/1549745-accessibilite-web-un-nouveau-defi-pour-le-seo/) ; [accessibilite.numerique.gouv.fr](https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/)
- **RGESN 2024 :** 78 critères. — [ISIT wiki](https://en.wiki.isit-europe.org/nr/RGESN)
- **XP Z12-014 :** 44 cas d'usage B2B. — [FNFE-MPE](https://fnfe-mpe.org/ressources/)
- **DSN :** deux normes publiées en parallèle (2026.1.2 et 2027.1.2), chacune avec son Excel de contrôles. — [net-entreprises](https://www.net-entreprises.fr/declaration/norme-et-documentation-dsn)

### Inferences
Estimation non vérifiée :

| Source | Volume estimé |
|---|---|
| RGAA | environ 250 tests (106 critères) |
| RGESN | 78 critères |
| Facturation électronique (EN16931 + BR-FR + CDAR) | 300 à 500 règles |
| DSN | plusieurs centaines de contrôles CCH/SIG |
| INS | quelques dizaines à une centaine d'EXI/RECO |
| PES V2 | plusieurs centaines d'anomalies probables |
| **Total** | **environ 1 500 à 3 000 règles numérotées** |

Les versions successives (DSN 2026/2027, facturation électronique V3.0/3.1/3.2) apportent en plus des paires de règles modifiées, utiles pour l'apprentissage.

### Gaps
- Aucun comptage officiel n'a été vérifié pour les contrôles DSN, les règles BR-FR, les EXI de l'INS ou les anomalies PES.
