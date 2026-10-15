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

## Particularités selon le type d'unité
- `catala` / `catala_reste` : `texte_loi` = article de loi ; `code_catala` précise valeurs et bornes.
- `publicodes` / `publicodes_reste` : `texte_loi` = règle YAML complète ; les règles qu'elle référence ne sont pas fournies.
- `service_public` : `texte_loi` = extrait d'une fiche pratique de service-public.fr. Retiens les règles vérifiables du texte (conditions, montants, délais, exceptions) ; ignore les généralités, adresses et liens. Si l'extrait ne contient aucune règle testable, fais quand même 2 scénarios sur la règle la plus nette.
- `openfisca` : `texte_loi` = fichier de cas de test YAML (name, period, input, output). Rédige la règle observée (ce que les cas montrent), sans inventer d'article de loi. Chaque cas de test devient un exemple dont les valeurs d'entrée et de sortie sont reprises telles quelles ; regroupe-les en `Plan du scénario` quand ils ne diffèrent que par les valeurs. Les noms de variables techniques sont reformulés en français courant.
- `cdtn` : `texte_loi` = fichier de tests TypeScript (situation → expectedResult, références d'articles). Reprends les valeurs attendues et les références d'articles telles quelles dans la spécification.
- `aides_jeunes` : `texte_loi` = fiche YAML d'une aide (description, conditions). Écris des scénarios d'éligibilité (éligible / non éligible) à partir des conditions ; ne devine aucun seuil absent.
