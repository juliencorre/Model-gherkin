# Specifications with explicit business rules: Belgium, Switzerland, Luxembourg, Québec/Canada, EU (as of Oct. 2026)

Scope: real-world specs with testable, ideally numbered business rules, preferably in French and openly licensed, for a Gherkin (Étant donné / Quand / Alors) training corpus. France excluded. Research date: 2026-10-15. These are about 16 tool calls of research, so the EU GitHub sources were checked in depth (licence files and rule text downloaded). Several national sources (BE, LU, CA) could only be checked at the surface level; see Gaps.

## Key question 1: Which sources provide machine-readable rules plus test files (Schematron + examples, JSON-logic + test cases, certification scenarios)?

### Takeaway
The best open sources pairing rules with tests are on the EU side:
- **CEN/TC 434 EN 16931 Schematron** (EUPL 1.2; about 200 numbered BR-xx rules plus example invoices).
- **EU DCC business rules / CertLogic** (Apache 2.0; JSON-logic rules with per-rule tests, though frozen since 2023).
- **EUDI Wallet ARF** (CC BY 4.0; 725 numbered SHALL requirements in a CSV, but no test cases in the ARF itself).

National payroll and tax certification test scenarios exist but are behind partner portals (Revenu Québec SW-7x series; Swissdec ELM). They are not usable as an open corpus.

### Cited Findings

**EU – CEN/TC 434 EN 16931 validation artefacts (ConnectingEurope/eInvoicing-EN16931)**
- The repo holds the official Schematron EN 16931 artefacts for CEN/TC 434 and does not contain CIUS rules. The latest release is UBL & CII **v1.3.17 (2026-10-09)**. Earlier releases: v1.3.16 (2026-04-10) and v1.3.15 (2025-10-20). EDIFACT is still at v1.0.0 (2018). There are folders `ubl`, `cii` and `edifact`. — [README](https://github.com/ConnectingEurope/eInvoicing-EN16931)
- **Licence:** "Licensed under European Union Public Licence (EUPL) version 1.2", described as a derivative of v1.2.3, which was Apache 2.0. — [LICENSE.txt](https://raw.githubusercontent.com/ConnectingEurope/eInvoicing-EN16931/master/LICENSE.txt), [README](https://github.com/ConnectingEurope/eInvoicing-EN16931)
- **Size:** the abstract model Schematron `ubl/schematron/abstract/EN16931-model.sch` contains **201 `assert` ids prefixed BR-** (BR-01…, BR-CO-xx, BR-S-xx, BR-AE-xx, etc.; counted by grep). Compiled XSLT is also published. — [EN16931-model.sch](https://github.com/ConnectingEurope/eInvoicing-EN16931/blob/master/ubl/schematron/abstract/EN16931-model.sch)
- **Example invoices exist**, e.g. `ubl/examples/ubl-tc434-example1.xml` (21 KB) and `cii/examples/CII_example1.xml` (34 KB). — [repo ubl/examples](https://github.com/ConnectingEurope/eInvoicing-EN16931/tree/master/ubl/examples)
- **Rule phrasing (verbatim, English only):**
  - `[BR-01]-An Invoice shall have a Specification identifier (BT-24).` (fatal)
  - `[BR-16]-An Invoice shall have at least one Invoice line (BG-25)`
  - `[BR-CO-10]-Sum of Invoice line net amount (BT-106) = Σ Invoice line net amount (BT-131).`
  - `[BR-S-08]-For each different value of VAT category rate (BT-119) where the VAT category code (BT-118) is "Standard rated", the VAT category taxable amount (BT-116) … shall equal the sum of Invoice line net amounts …`

  Source: [EN16931-model.sch](https://github.com/ConnectingEurope/eInvoicing-EN16931/blob/master/ubl/schematron/abstract/EN16931-model.sch)
- Code lists are in the Digital Europe "Registry of supporting artefacts to implement EN16931". — [EC DBB registry](https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/Registry+of+supporting+artefacts+to+implement+EN16931)

**EU/International – Peppol BIS Billing 3.0 (OpenPeppol)**
- The current online version is **3.0.21**. The publisher is OpenPeppol AISBL, Post-Award Coordinating Community. — [docs.peppol.eu BIS Billing 3.0](https://docs.peppol.eu/poacc/billing/3.0/bis/)
- **Copyright (restrictive):** "This Peppol BIS document may not be modified, re-distribute, sold or repackaged in any other way" without prior consent of OpenPeppol AISBL, which holds the copyright. — [docs.peppol.eu](https://docs.peppol.eu/poacc/billing/3.0/bis/)
- **Rule numbering:** rules carry IDs and a fatal or warning flag. There are country rules (DE-R-xxx, DK-R-xxx, GR-R-xxx, IS-R-xxx) and syntax rules UBL-CR-001…UBL-CR-598, in addition to the PEPPOL-EN16931-Rxxx rules and the EN BR-xx rules. Examples:
  - `DK-R-002 (fatal): "Danish suppliers MUST provide legal entity (CVR-number)"`
  - `UBL-CR-001 (warning): "A UBL invoice should not include extensions"`

  Source: [docs.peppol.eu](https://docs.peppol.eu/poacc/billing/3.0/bis/)
- The document has chapters "Transaction validation rules" and "Appendix E – Example files". — [docs.peppol.eu](https://docs.peppol.eu/poacc/billing/3.0/bis/)

**EU – EU Digital COVID Certificate business rules / CertLogic**
- **ehn-dcc-development/eu-dcc-business-rules** contains:
  - CertLogic: a specification, reference implementations (JS, Kotlin, Dart) and a **test suite**;
  - a validation tool;
  - an HTML renderer.
- The project was handed over to WHO on 2023-07-01 and the repo is **frozen/archival**. — [README](https://github.com/ehn-dcc-development/eu-dcc-business-rules)
- **Licence:** Apache License 2.0, "Copyright (c) 2021 Dutch Ministry of Health, Science, and Sports, and all other contributors". — [README / LICENSE](https://github.com/ehn-dcc-development/eu-dcc-business-rules)
- **Rule phrasing example** (prose, then formula, then CertLogic JSON):
  - Natural-language checks: "Whether this vaccination is against COVID-19 … Whether the number of doses is sufficient … Whether this vaccination happened at least 14 days ago, and no more than 365 days ago"
  - Formula: `dt + 14 days <= now <= dt + 365 days`
  - Source: [example.adoc](https://github.com/ehn-dcc-development/eu-dcc-business-rules/blob/main/documentation/example.adoc)
- **eu-digital-green-certificates/dgc-business-rules-testdata** holds country business rules plus their tests. Every rule's JSON is validated against the gateway's validation-rule JSON Schema, and its `Logic` field is validated as CertLogic. Tests run automatically on each PR. The rules are described as "unofficial", with the official ones on the DCC Gateway. **Licence:** Apache 2.0. — [README](https://github.com/eu-digital-green-certificates/dgc-business-rules-testdata), [LICENSE](https://raw.githubusercontent.com/eu-digital-green-certificates/dgc-business-rules-testdata/master/LICENSE)
- The underlying EU spec is "eu-dcc_validation-rules_en.pdf" (EC eHealth Network). — [EC PDF](https://ec.europa.eu/health/sites/default/files/ehealth/docs/eu-dcc_validation-rules_en.pdf)

**EU – EUDI Wallet Architecture and Reference Framework (ARF)**
- **Licence:** "The ARF is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0)". The authoritative version is the latest tagged release, versioned with SemVer. — [README](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework)
- Since ARF 2.7.0, all high-level requirements are in a machine-readable **CSV** (`hltr/high-level-requirements.csv`). That CSV is authoritative over the generated .md files (by-topic and by-category views). — [Annex 2.01](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/blob/main/docs/annexes/annex-2/annex-2.01-high-level-requirements.md)
- **Size:** I downloaded and parsed the CSV: **725 requirements**, semicolon-delimited. The columns are Harmonized_ID, Part, Category, Topic, Topic_Number, Topic_Title, Subsection, Index, Requirement_specification and Notes. Examples:
  - `EW-PIO-01-001 / OIA_01`: "For proximity presentation flows, a Wallet Unit SHALL support the transmission mechanism specified in [ISO/IEC 18013-5] …"
  - `EW-DM-03-02 / PID_02`: "A PID Provider SHALL issue any PID in both the format specified in ISO/IEC 18013-5 and the format specified in [SD-JWT VC]."
  - `AS-WP-09-010 / WUA_09`: "A KA SHALL contain one or more public keys, and the corresponding private keys SHALL be generated by and stored in the WSCA/WSCD …"

  Source: [high-level-requirements.csv](https://raw.githubusercontent.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/refs/heads/main/hltr/high-level-requirements.csv)
- The annexes also include the PID Rulebook (3.01), the mDL Rulebook (3.02), flow diagrams for 12 scenarios (Annex 4.x PDFs, e.g. "issuing mDL", "remote QES enrolment") and Annex 6 Certification Requirements. — [Annexes README](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/blob/main/docs/annexes/README.md)

**Québec – Revenu Québec certification (rules + test cases, restricted)**
- **WEB-SRM (sales recording systems, restaurant and paid passenger transportation sectors):**
  - Certification is mandatory, and you must be a registered partner.
  - The process is the Certification Process SW-79-V.
  - The features to certify are defined in the Guide for Adapting an SRS, SW-73-V.
  - **Test cases are generated from the features you select.** It is a three-phase process: registration/adaptation, test execution, certification application.

  Source: [Revenu Québec – Certification of SRSs (WEB-SRM)](https://www.revenuquebec.ca/en/partners/product-developers/fields-of-activity/developers-mandatory-billing-cloud-solution/certified-srss-designed-to-communicate-with-the-web-srm/)
- A third-party integrator guide says mandatory test cases in SW-78-V run in DEV, then scenarios in SW-77-V run in the ESSAI environment. This is secondary, non-official information. — [RetailForce support](https://support.retailforce.cloud/hc/en-gb/articles/39047600531345)
- **Similar certification paths:**
  - corporate tax software, IN-417 — [RQ impôt des sociétés](https://www.revenuquebec.ca/fr/partenaires/concepteurs-de-produits/domaines-dactivite/impot-concepteurs-de-produits/information-pour-nos-partenaires-impot-des-societes/autorisation-et-certification/)
  - individual tax software, IN-413 — [RQ impôt des particuliers](https://www.revenuquebec.ca/fr/partenaires/concepteurs-de-produits/domaines-dactivite/impot-concepteurs-de-produits/impot-des-particuliers/autorisation-et-certification/)
  - relevés (RL slips) — [RQ relevés](https://www.revenuquebec.ca/fr/partenaires/concepteurs-de-produits/domaines-dactivite/releves/autorisation-et-certification/)
  - electronic banking transactions — [RQ TBE](https://www.revenuquebec.ca/fr/partenaires/concepteurs-de-produits/domaines-dactivite/transactions-bancaires-electroniques/certification-des-produits/)
  - IQEE certification, SW-209 — [RQ SW-209](https://www.revenuquebec.ca/fr/partenaires/documents-pour-nos-partenaires/documents/details-courant/part/sw-209)
- The detailed specification and test-case documents appear to sit behind the partner portal. This was reported by the search synthesis and not verified page by page.

**Switzerland – Swissdec ELM (payroll)**
- Swissdec certification requires several conditions:
  - all mandatory criteria of the standard are met;
  - the planned test cases have been completed successfully;
  - the firm passes technical and functional acceptance.

  Tools named are the Quality-Tool, Viewgen and Transmitter Samples, and minor versions can be self-certified via the QualityTool. — [swissdec.ch document](https://swissdec.ch/document/share/244/05bb883c-6f6e-4b7f-bfa1-17135509f836)
- Dated ELM 5.0 certifications: Abacus Lohn was reported as the first ELM 5.0-certified payroll system (2022-01-28) — [BDO](https://www.bdo.ch/de-ch/publikationen/newsletter/abacus-newsletter/abacus-lohn-nach-elm-5-zertifiziert). bexio was certified in June 2024 — [bexio](https://www.bexio.com/de-CH/product-news/news-4).

### Inferences
- Of all sources checked, only **EN 16931 Schematron + examples**, **DCC CertLogic rules + tests** and **ARF CSV** are directly usable as a downloadable, openly licensed and numbered rule corpus.
- EN 16931 and the DCC rules give natural "rule → valid/invalid instance" pairs. A Schematron `assert` translates almost mechanically into a Gherkin scenario: Étant donné une facture où BT-24 est absent / Quand elle est validée / Alors l'erreur fatale BR-01 est levée. Each BR could be augmented by mutating the example invoices.
- ARF requirements are SHALL statements with no tests, which suits a "requirement → scenario" generation task. The EUDI reference implementation repos under the same GitHub org may contain tests, but I did not verify this.
- Payroll and tax certification scenarios (Revenu Québec, Swissdec) would be ideal in form but are not openly redistributable as far as could be verified. Treat them as excluded unless a licence is obtained.

### Gaps
- I did not verify the exact Peppol validation artefact repo, test files or licence on GitHub (OpenPEPPOL/peppol-bis-invoice-3). GitHub API access was blocked in this session, and the raw LICENSE/README fetch returned nothing. The docs page copyright is restrictive, but the Schematron files may carry a different (possibly MPL/Apache-style) licence. **Check this before use.**
- The EN 16931 standard text itself (CEN, paywalled, with national FR versions from NBN/AFNOR/SNV) is not openly licensed. Only the Schematron rule messages and examples under EUPL are open.
- I did not check whether the ARF reference implementations or conformance test suites (EUDI "ITB" / interoperability test bed) provide Gherkin-like scenarios.
- No open Swissdec ELM test-case files were found. The Swissdec licence terms were not found.
- I did not research OOTS, SEMIC Core Vocabularies, EESSI or ViDA in this pass. From memory (unverified): SEMIC is on GitHub under CC BY 4.0; OOTS technical design documents are on the EC Digital Building Blocks wiki; EESSI specs are not public.

## Key question 2: Which are available in French?

### Takeaway
French is the weak point of the open EU sources: EN 16931 Schematron messages, Peppol BIS, DCC rules documentation and the ARF are English-only, as checked. The strongest French-native sources are **eCH (Switzerland)** standards, which have French PDFs and French-annotated XSDs, and **Revenu Québec** specifications, which are French-first but restricted. Belgian federal specs are FR/NL bilingual, but I did not verify them in this pass.

### Cited Findings
- **eCH-0020 v4.1.0**, "Norme d'interface Motifs d'annonce Registre des personnes":
  - Approved 16 May 2025 (decision 29 April 2025), status "Approuvé/Déployé".
  - Main document PDF in French, plus XSDs `eCH-0020-5-0.xsd` and `eCH-0020-5-0f.xsd`.
  - The site is available in DE/FR/IT/EN.

  Source: [ech.ch eCH-0020](https://www.ech.ch/fr/ech/ech-0020)
- eCH publishes French documents across the catalogue. Examples:
  - eCH-0011 V8.1 "Norme concernant les données Données personnelles" (French addendum, 2019) — [ech.ch](https://ech.ch/sites/default/files/docvers/beilagen/Addendum_f_2019-05-16_eCH-0011_V8.1_Norme%20concernant%20les%20donn%C3%A9es%20Donn%C3%A9es%20personnelles.pdf)
  - eCH-0010 V7.0 Adresse postale — [ech.ch](https://www.ech.ch/sites/default/files/docvers/beilagen/Addendum_f_2019-06-21_eCH-0010_V7.0_Norme_concernant_les%20donne%20es_Adresse_postaledocx.pdf)
  - eCH-0086 UPI Compare Interface (FR, 2017) — [ech.ch](https://www.ech.ch/sites/default/files/dosvers/hauptdokument/2017-04-11_f_eCH-0086_UPI%20Compare%20Interface.pdf)
  - eCH-0105 V2.0 overview of person/notification standards — [ech.ch](https://ech.ch/sites/default/files/dosvers/hauptdokument/AUXI_f_NUL_2016-01-11_eCH-0105%20_V2.0_Vue%20d%27ensemble%20des%20normes%20personnes%20syst%C3%A8mes%20d%27annonce.pdf)
  - eCH-0236 V2.0.0 "Norme de processus Hôpital stationnaire" (2024) — [ech.ch](https://www.ech.ch/sites/default/files/imce/eCH-Dossier/eCH-Dossier_PDF_Publikationen/Beilagen/Addendum_f_DEF_2024-07-01_eCH-0236_V2.0.0_Norme_de_processus_Ho%CC%82pital_stationnaire_0.pdf)
  - eCH-0253 V1.0.0 "Norme de processus Ambulatoire" (2024) — [ech.ch](https://www.ech.ch/sites/default/files/imce/eCH-Dossier/eCH-Dossier_PDF_Publikationen/Beilagen/Addendum_f_DEF_2024-12-17_eCH-0253_V1.0.0_Norme_de_processus_Ambulatoire.pdf)
- Revenu Québec developer pages are in French, e.g. "Autorisation et certification – Relevés". — [RQ](https://www.revenuquebec.ca/fr/partenaires/concepteurs-de-produits/domaines-dactivite/releves/autorisation-et-certification/)
- The EN 16931 Schematron rule messages are English-only, as seen in the source file. — [EN16931-model.sch](https://github.com/ConnectingEurope/eInvoicing-EN16931/blob/master/ubl/schematron/abstract/EN16931-model.sch)
- **Belgium:** the B2B e-invoicing mandate has applied since 2026-01-01, based on Peppol BIS Billing 3.0 (UBL), with a tolerance until end of March 2026 and e-reporting planned for 2028. These come from secondary sources (vendor blogs); one says royal decree of 29 July 2025, another 14 July 2025, so there is **a conflict to verify in the Moniteur belge**. — [ClearTax BE](https://www.cleartax.com/be/fr/belgian-e-invoice-format), [Forum for the Future](https://blog.forumforthefuture.be/fr/article/facturation-electronique-obligatoire-en-belgique-des-janvier-2026-arrete-royal-du-14-juillet-2025/27862), [B2Brouter](https://www.b2brouter.net/be/international/belgium/)

### Inferences
- For French-language rules, eCH is the best open candidate. It has structured "norme d'interface" documents with notification types ("motifs d'annonce") and conditions, plus XSDs.
- Rule density in eCH is lower than in EN 16931, and rules are mostly in prose tables rather than numbered BR-style rules. Expect manual extraction.
- An English → French translation or adaptation step for EN 16931 BR-xx rules is plausible. The BT/BG semantic terms have official French labels in the French national version of EN 16931 (France, out of scope) and in Belgian/Swiss/Luxembourg FR versions, but none of these were checked here.

### Gaps
- Belgian official specs were not verified in this pass: eHealth cookbooks, BCSS/KSZ, ONSS DmfA "instructions administratives" and glossaries, BOSA Peppol/Mercurius guidance, and FPS Finance validation rules. They are likely FR/NL and freely downloadable, but their licence is unknown.
- Luxembourg (CTIE, eCDF, Peppol LU) was not researched.
- CRA T4/T4A XML specifications (bilingual, Canada.ca) were not verified. From memory, Canada.ca content generally falls under Canada.ca terms and conditions rather than OGL-Canada; this was not confirmed.
- I did not verify whether the DCC country rules carry French "Description" entries.

## Key question 3: What are the licence/reuse conditions?

### Takeaway
Licences of the sources checked, most open first:

| Source | Licence | Notes |
|---|---|---|
| ARF | CC BY 4.0 | |
| EN 16931 Schematron | EUPL 1.2 | Copyleft; fine for internal training, but be aware for redistribution of derived files |
| DCC rules / testdata | Apache 2.0 | |
| eCH | Free use "gratuitement et sans restriction" | Must mention the eCH author or rights holder; third-party referenced material is excluded |
| OpenFisca country packages | AGPL-3.0 | Senegal verified |
| Peppol BIS docs | Restrictive OpenPeppol copyright | No modification or redistribution |
| Revenu Québec certification documents and Swissdec test material | Restricted | Partner-only, so not usable |

### Cited Findings
- EN 16931 artefacts: EUPL v1.2. — [LICENSE.txt](https://raw.githubusercontent.com/ConnectingEurope/eInvoicing-EN16931/master/LICENSE.txt)
- DCC rules and CertLogic: Apache 2.0. — [eu-dcc-business-rules LICENSE](https://raw.githubusercontent.com/ehn-dcc-development/eu-dcc-business-rules/master/LICENSE); [dgc-business-rules-testdata LICENSE](https://raw.githubusercontent.com/eu-digital-green-certificates/dgc-business-rules-testdata/master/LICENSE)
- EUDI ARF: CC BY 4.0. — [README](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework)
- Peppol BIS: "may not be modified, re-distribute, sold or repackaged in any other way" without OpenPeppol consent. — [docs.peppol.eu](https://docs.peppol.eu/poacc/billing/3.0/bis/)
- eCH copyright clause (French addenda), as found in eCH addenda through the search synthesis and not read in full:
  - "Les normes élaborées par les groupes de spécialistes peuvent, moyennant mention des auteurs eCH respectifs, être utilisées, développées et déployées gratuitement et sans restriction."
  - Authors keep their intellectual property.
  - Referenced third-party documents may be protected by trademark, copyright or patent law.
  - The standards only have the value of recommendations.

  Sources: [eCH-0011 addendum](https://ech.ch/sites/default/files/docvers/beilagen/Addendum_f_2019-05-16_eCH-0011_V8.1_Norme%20concernant%20les%20donn%C3%A9es%20Donn%C3%A9es%20personnelles.pdf), [eCH-0236 addendum 2024](https://www.ech.ch/sites/default/files/imce/eCH-Dossier/eCH-Dossier_PDF_Publikationen/Beilagen/Addendum_f_DEF_2024-07-01_eCH-0236_V2.0.0_Norme_de_processus_Ho%CC%82pital_stationnaire_0.pdf)
- OpenFisca Senegal: GNU AGPL v3 (LICENSE file read). — [openfisca-senegal LICENSE](https://raw.githubusercontent.com/openfisca/openfisca-senegal/master/LICENSE). OpenFisca Tunisia exists (README in Arabic/French) — [openfisca-tunisia](https://github.com/openfisca/openfisca-tunisia). I did not read its licence; OpenFisca core is AGPL — [Interoperable Europe – OpenFisca](https://interoperable-europe.ec.europa.eu/collection/justice-law-and-security/solution/openfisca).
- **Canada Rules as Code:**
  - The Canada School of Public Service has experimented with RaC since 2019, initially with OpenFisca, and found that approach hard to sustain. — [OECD-OPSI "Rules as Code in Canada" (2024)](https://oecd-opsi.org/wp-content/uploads/2024/04/Rules-as-Code-in-Canada.pdf)
  - A repo `DTS-STN/openfisca-canada-dts` exists, described as a jumping-off point for Canada's use of OpenFisca. Its licence was not verified.
  - I found no verified "Policy Difference Engine" repo (the search surfaced only France's LexImpact for that term).

### Inferences
- For an AI training corpus:
  - CC BY 4.0 and Apache 2.0 are the cleanest choices (attribution only).
  - EUPL 1.2 is copyleft for distributed derivative "works". Training use is arguably fine, but redistributing a dataset containing the Schematron text should carry EUPL.
  - eCH's clause is permissive with attribution.
  - Peppol BIS text should be excluded or used only with permission.
  - AGPL OpenFisca YAML tests (input → expected output) are usable, but redistributed derivatives would inherit the AGPL.
- OpenFisca country packages (Tunisia, Senegal) include YAML test files that pair inputs with expected outputs, a good fit for "Exemples" tables in Gherkin. Their French-language parameter descriptions are likely but not verified here.

### Gaps
- I did not obtain the licence or terms of use of Revenu Québec developer documents (© Gouvernement du Québec; partner terms), Swissdec, Belgian eHealth/BCSS/ONSS, the Luxembourg CTIE, or Canada CRA specs.
- Whether OGL-Canada applies to any Canadian spec dataset (e.g. on open.canada.ca) was not checked.
- I did not find the actual (if any) Peppol validation-artefact licence.
