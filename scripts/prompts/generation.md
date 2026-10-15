# Consignes de génération : unité source → spécification + Gherkin français

Tu produis des paires (spécification de règle de gestion → scénarios Gherkin en français) pour un corpus d'entraînement d'un petit modèle. La qualité prime sur la quantité : chaque paire sera contrôlée automatiquement (parseur Gherkin officiel, traçabilité des nombres) puis auditée par échantillon.

## Entrée et sortie
- Entrée : un fichier JSONL d'unités (champs : id, type, domaine, article, source, texte_loi, code_catala).
- Sortie : un fichier JSONL, une ligne par unité, avec exactement les champs `id`, `specification`, `gherkin`, `notes`. Écris-le avec un script Python et json.dumps(ensure_ascii=False). Traite TOUTES les unités du lot.
- Avant de terminer, lance `python3 -I /home/user/Model-gherkin/scripts/valider_gherkin.py <sortie>` (module gherkin-official installé) et corrige les paires en KO. Ne modifie aucun autre fichier.

## Contenu de chaque paire
1. `specification` : la règle reformulée en règle de gestion de logiciel, en français, claire et testable (2 à 6 phrases ou puces), fondée UNIQUEMENT sur la source. N'ajoute aucune règle, aucun chiffre ni aucune exception absents de la source. Garde les conditions, seuils, délais, bornes et cas d'exception de la source.
2. `gherkin` : fichier Gherkin français valide : `# language: fr`, `Fonctionnalité:`, `Contexte:` si utile, `Scénario:`, `Plan du scénario:` + `Exemples:`, `Étant donné`, `Quand`, `Alors`, `Et`, `Mais`.
   - 2 à 6 scénarios : au moins un `@nominal`, puis un `@limite` (borne de date, seuil, montant, âge, durée) et un `@négatif` (hors périmètre, refus, exception) quand la règle le permet. Si une règle n'admet ni limite ni cas négatif, fais 2 scénarios nominaux distincts et explique-le dans `notes`.
   - Style déclaratif métier : pas de détails d'interface, un scénario = une intention. Utilise des termes métier en français courant, jamais les identifiants techniques (« a . b . c »).
   - Chaque scénario est précédé d'une ligne de tags : `@<id de l'unité>` puis `@nominal`, `@limite` ou `@négatif` (ex : `@SP-00012 @limite`).
   - `Plan du scénario` + `Exemples` pour les variantes de valeurs. Titres de scénarios précis, tous différents dans un même fichier.
3. `notes` : hypothèses, valeurs de test fictives, ambiguïtés, interprétation des bornes (« au plus », « au moins », « à compter du »), points non couverts. Chaîne vide si rien.

## Règles de véracité (contrôlées par script)
- Les RÉSULTATS ATTENDUS (étapes `Alors`, colonnes de sortie des `Exemples`) doivent venir de la source ou se calculer à partir de nombres de la source et des données d'entrée du même scénario (somme, produit, pourcentage, différence). Ne devine jamais un montant, un taux, un délai ni une date légaux.
- Si une valeur est définie ailleurs (règle ou barème non fourni), n'en teste pas la valeur ; teste le comportement qualitatif (« le plafond applicable est utilisé ») ou pose une donnée d'entrée de test fictive et déclare-la dans `notes`.
- Les données d'entrée (âge, revenu, date) peuvent être choisies librement, mais de façon plausible.
- Si le code et le texte de loi divergent, aligne-toi sur le texte, ne teste pas le cas divergent et signale-le dans `notes`.

## Défauts constatés à l'audit indépendant : à éviter absolument
1. **Spécification qui perd une condition** : montant sans sa périodicité (« 200 € par mois » ≠ « 200 € »), restriction de public (degré de parenté, filière, année d'études, date d'effet), exception, outre-mer / territoire. Relis la source phrase par phrase et vérifie que chacune est reprise.
2. **Scénario nominal sans toutes les conditions de la source** : si la source pose deux conditions cumulatives (« revenus modestes » ET âge), le scénario nominal doit établir les deux. Ne déclare jamais une personne éligible sans la condition de ressources posée par la source.
3. **Fausses étiquettes** : `@limite` uniquement pour une vraie borne de la source (jour exact, seuil exact, âge exact, avec le côté inclusif / exclusif de la source) ; `@négatif` uniquement pour un refus ou une exclusion que la source énonce. Ne répète pas un autre scénario.
4. **Conséquence supposée** : ne prends pas comme résultat attendu une conséquence que la source ne dit pas (ex : « sans réponse, la demande est refusée », « cumul sur 3 jours »). Teste seulement ce qui est écrit.
5. **Conversions non fournies** : ne convertis pas des mois en jours, un mensuel en annuel ou un taux en montant sans que la source donne la règle de conversion ; n'invente pas de proratisation. Pour un plafond proratisé ou réduit, la base de calcul est celle que la source indique.
6. **Contradictions** : un `Étant donné` du scénario ne doit pas contredire le `Contexte`.
7. **Français et style** : accords et articles corrects (« un couple », « n'est pas une résidence principale »), dates écrites « 1er janvier 2024 » ou « 15 mars 2024 » (pas de format technique AAAA-MM-JJ dans les étapes), montants « 1 250 € » sans guillemets ni décimales inutiles, pas d'annotation « (valeur fictive) » dans les étapes (elle va dans `notes`), pas de terme absent de la source (marque, sigle, catégorie), `Plan du scénario` seulement avec au moins 2 lignes d'exemples.

## Relecture obligatoire avant d'écrire la sortie
Pour chaque paire, relis-la comme un auditeur sévère en 5 points : (a) chaque phrase de la source est reprise ou volontairement écartée ; (b) chaque résultat attendu est dans la source ou se recalcule ; (c) chaque `@limite` / `@négatif` est mérité ; (d) aucune conséquence supposée ; (e) français correct. Corrige avant d'écrire. Mentionne dans `notes` ce que tu n'as pas pu couvrir.

## Particularités selon le type d'unité
- `catala` / `catala_reste` : `texte_loi` = article de loi ; `code_catala` précise valeurs et bornes.
- `publicodes` / `publicodes_reste` : `texte_loi` = règle YAML complète ; les règles qu'elle référence ne sont pas fournies.
- `service_public` : `texte_loi` = extrait d'une fiche pratique de service-public.fr. Retiens les règles vérifiables du texte (conditions, montants, délais, exceptions) ; ignore les généralités, adresses et liens. Si l'extrait ne contient aucune règle testable, fais quand même 2 scénarios sur la règle la plus nette.
- `legi` / `legi_2` : `texte_loi` = article d'un code en vigueur (Légifrance). Retiens ses règles vérifiables (conditions, montants, délais, exceptions) ; l'article cite parfois d'autres articles que tu n'as pas : n'en invente pas le contenu.
- `service_public_2` : comme `service_public` (extrait de fiche pratique), avec parfois une seule règle chiffrée : fais alors 2 à 3 scénarios nets sur cette règle et ses exceptions éventuelles.
- `openfisca` : `texte_loi` = fichier de cas de test YAML (name, period, input, output). Rédige la règle observée (ce que les cas montrent), sans inventer d'article de loi. Chaque cas de test devient un exemple dont les valeurs d'entrée et de sortie sont reprises telles quelles ; regroupe-les en `Plan du scénario` quand ils ne diffèrent que par les valeurs. Les noms de variables techniques sont reformulés en français courant.
- `cdtn` : `texte_loi` = fichier de tests TypeScript (situation → expectedResult, références d'articles). Reprends les valeurs attendues et les références d'articles telles quelles dans la spécification.
- `aides_jeunes` : `texte_loi` = fiche YAML d'une aide (description, conditions). Écris des scénarios d'éligibilité (éligible / non éligible) à partir des conditions ; ne devine aucun seuil absent.
