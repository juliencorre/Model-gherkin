# Entraînement de Ministral 3 3B Instruct pour écrire du Gherkin

Ce dossier contient le programme d'affinage (LoRA ou QLoRA) de **Ministral 3 3B Instruct** : à partir d'une
spécification fonctionnelle, le modèle doit écrire une fonctionnalité Gherkin en français, de qualité
(tags de règle, cas nominaux, limites et négatifs, plans de scénario cohérents). Il consomme les paires
préparées dans `data/` (format ci-dessous) et vise une **RTX 5080 (16 Go) sous Ubuntu**.

Commandes disponibles (`gherkin-ft --help`) :

| Commande | Rôle |
|---|---|
| `check-env` | Vérifie pilote, CUDA, sm_120, bf16, noyau Triton de TRL, bitsandbytes et versions |
| `prepare` | Charge, filtre et découpe les données, sans entraîner (statistiques de longueur, rejets) |
| `train` | Entraîne l'adaptateur LoRA / QLoRA, puis l'évalue par génération |
| `evaluate` | Fait écrire le Gherkin du jeu d'évaluation et mesure sa qualité (modèle de base ou affiné) |
| `compare` | Tableau comparatif de plusieurs `metrics.json` |
| `generate` | Écrit le Gherkin d'une spécification (nouvel essai si la sortie est invalide) |
| `merge` | Fusionne l'adaptateur dans le modèle de base (bf16), pour vLLM ou une conversion GGUF |

## 1. Installation (Ubuntu 22.04 / 24.04, RTX 5080)

Prérequis : pilote NVIDIA **570 ou plus récent, en version « open »** (les modules noyau open sont obligatoires
pour les cartes Blackwell). Le toolkit CUDA système n'est pas nécessaire : les roues PyTorch embarquent le leur.

```bash
sudo ubuntu-drivers list                  # pilotes proposés
sudo apt install nvidia-driver-580-open   # ou la version -open la plus récente
sudo reboot
```

Puis, depuis la racine du dépôt :

```bash
bash entrainement/install_ubuntu_rtx5080.sh   # crée entrainement/.venv (Python 3.12, uv)
source entrainement/.venv/bin/activate
gherkin-ft check-env
```

Le script choisit la roue PyTorch selon le pilote : CUDA 13.0 (`cu130`) si pilote ≥ 580, CUDA 12.8 (`cu128`)
si pilote 570-579. Les deux contiennent le code pour sm_120 (RTX 50xx). `check-env` vérifie en plus que le noyau
Triton utilisé par TRL pour la perte compile sur la carte, et que bitsandbytes (QLoRA) fonctionne.

## 2. Données

Fichiers JSONL, une paire par ligne, au format produit par la préparation du corpus :

```json
{"id": "RG-01", "specification": "Le SMIC brut horaire est…", "gherkin": "# language: fr\n@RG-01\nFonctionnalité: …", "notes": "…"}
```

- **Champs reconnus** : `id`, `specification` (ou `spec`, `exigence`, `input`), `gherkin` (ou `feature`,
  `output`, `completion`). Autres noms : `data.fields: {specification: ma_colonne}`.
  `notes` et les autres métadonnées courtes (source, licence…) sont conservées mais jamais montrées au modèle.
- **Découpage train / évaluation par groupe** (dispositif juridique), jamais par scénario, pour éviter les
  fuites : le groupe vient du premier champ non vide parmi `dispositif`, `domaine`, `groupe`, `source`.
  Les paires pilotes n'ont pas de domaine : `data.metadata_files` les joint par `id` aux fichiers
  `regles_*.jsonl`. Sans aucun groupe, le découpage se fait paire par paire, avec un avertissement.
- **Jeu d'évaluation fourni** : `data.eval_files` (ex. les 300 paires revues à la main) ou un champ
  `split: "eval"` dans les paires. Les paires d'entraînement d'un groupe présent dans l'évaluation sont retirées.
- **Filtres** : Gherkin invalide pour le parseur officiel (`require_valid_gherkin`), score de qualité de la
  référence sous un seuil (`min_reference_score`), spécifications en double, paires de plus de `max_length`
  tokens (écartées plutôt que tronquées, pour ne pas apprendre des Gherkin coupés).

`gherkin-ft prepare -c entrainement/configs/ministral3b_lora.yaml` écrit dans `<output_dir>/data/` :
`train.jsonl`, `eval.jsonl`, `manifest.json` (identifiants et groupes de chaque côté) et `rapport.json`
(rejets et longueurs). Sur les 20 paires pilotes : 17 en entraînement, 3 en évaluation (domaines `asp` et
`prestations_familiales`), de 605 à 1 336 tokens par exemple.

## 3. Entraîner et évaluer

Toutes les commandes se lancent depuis la racine du dépôt (les chemins des configs en dépendent).

```bash
CFG=entrainement/configs/ministral3b_lora.yaml

# Référence : le modèle de base, avec le même prompt, sur le jeu d'évaluation
gherkin-ft prepare  -c $CFG
gherkin-ft evaluate -c $CFG --data entrainement/runs/ministral3b-gherkin-lora/data/eval.jsonl \
                    --out entrainement/runs/eval-base --label base

# Entraînement (évaluation par génération incluse à la fin)
gherkin-ft train -c $CFG
tensorboard --logdir entrainement/runs/ministral3b-gherkin-lora/checkpoints   # suivi en direct

# Comparaison base / affiné
gherkin-ft compare entrainement/runs/eval-base/metrics.json \
                   entrainement/runs/ministral3b-gherkin-lora/eval/metrics.json
```

Toute valeur de la config se surcharge en ligne de commande :
`--set training.learning_rate=2e-4 --set data.train_limit=1000 --set training.output_dir=entrainement/runs/essai`.
Reprise après interruption : `--set training.resume_from_checkpoint=last`.

Contenu d'un run (`entrainement/runs/<nom>/`) :

| Chemin | Contenu |
|---|---|
| `adapter/` | Adaptateur LoRA, tokenizer, `gherkin_ft.json` (modèle de base, prompt système, gabarit) |
| `checkpoints/` | Points de contrôle et journaux TensorBoard |
| `data/` | Découpage utilisé (`manifest.json`, `train.jsonl`, `eval.jsonl`, `rapport.json`) |
| `eval/` | `metrics.json`, `predictions.jsonl` (sortie, analyse, score par paire), `rapport.md` |
| `config.yaml`, `train.log`, `metrics_entrainement.json` | Config résolue, journal, pertes finales |

**Courbe d'apprentissage** (500, 1 000, 2 000 paires puis tout, même jeu d'évaluation figé) :
`bash entrainement/scripts/courbe_apprentissage.sh`, résultat dans `entrainement/runs/courbe/comparaison.md`.

## 4. Utiliser le modèle

```bash
# Depuis un fichier (ou l'entrée standard), sortie dans un .feature
gherkin-ft generate --adapter entrainement/runs/ministral3b-gherkin-lora/adapter \
                    --id RG-42 -f spec_rg42.txt -o RG-42.feature

# Modèle autonome fusionné (bf16, ~8 Go), pour vLLM ou une conversion GGUF (llama.cpp → Ollama, LM Studio)
gherkin-ft merge --adapter entrainement/runs/ministral3b-gherkin-lora/adapter \
                 --out entrainement/runs/ministral3b-gherkin-fusionne
```

`generate` extrait le Gherkin d'une réponse éventuellement bavarde, le valide avec le parseur officiel et refait
jusqu'à `--retries` essais (échantillonnés) si la sortie est invalide ou tronquée. Le prompt système enregistré avec
l'adaptateur est réutilisé : le modèle voit exactement le prompt de son entraînement.

## 5. Mesure de la qualité

`evaluate` (et la sonde lancée à chaque évaluation pendant l'entraînement, sur `eval.probe_samples` paires)
analyse chaque sortie avec le parseur officiel `gherkin-official` :

| Critère du score (poids) | Contrôle |
|---|---|
| Syntaxe et langue (condition) | Parseur officiel, `# language: fr` ; sinon le score vaut 0 |
| Tag de règle (0,15) | Part des scénarios portant `@<id>` (tags hérités compris) |
| `@nominal`, `@limite`, `@négatif` (0,15 chacun) | Présence de chaque type de cas (accents et casse ignorés) |
| Structure (0,15) | Au moins un Quand et un Alors, ordre Étant donné → Quand → Alors |
| Plans de scénario (0,15) | Chaque `<paramètre>` a sa colonne dans `Exemples`, aucune colonne inutilisée |
| Volume (0,10) | Au moins 3 scénarios |

S'y ajoutent des indicateurs : sorties tronquées, blocs markdown, scénarios à plusieurs Quand (style BRIEF),
part des nombres du Gherkin présents dans la spécification, et chrF par rapport à la référence.
**Ces contrôles ne vérifient pas l'exactitude métier des valeurs attendues** : seule une relecture, ou un
oracle comme le compilateur Catala, le peut.

## 6. Choix techniques

- **Poids BF16** : `mistralai/Ministral-3-3B-Instruct-2512` est publié en FP8, inadapté à la LoRA ; on utilise
  `mistralai/Ministral-3-3B-Instruct-2512-BF16` (le programme refuse le dépôt FP8 avec un message clair).
- **Architecture** : Ministral 3 est un modèle vision-langage (`Mistral3ForConditionalGeneration`, 3,85 G de
  paramètres dont 0,42 G pour la vision). Il est chargé tel quel, mais la LoRA ne cible que les projections
  du modèle de langage : 49,4 M de paramètres entraînables (1,28 %) pour r = 32, aucun dans la vision.
  L'adaptateur s'applique donc directement au modèle officiel.
- **Perte sur la réponse seule** : format « prompt-completion » de TRL ; le prompt (jusqu'à `[/INST]`) est
  masqué, la cible commence à `# language: fr` et inclut le `</s>` final, pour que le modèle apprenne à s'arrêter.
- **Prompt système explicite** : le modèle de chat de Ministral insère son prompt « Le Chat » par défaut si
  aucun n'est fourni ; le nôtre décrit les règles de rédaction et est enregistré avec l'adaptateur.
- **Tokenizer** : chargé avec `fix_mistral_regex=True`, comme le demande transformers pour les tokenizers Mistral.
- **Pile logicielle** : transformers ≥ 5 (support de Ministral 3), TRL ≥ 1.0, PEFT, attention SDPA de PyTorch
  (pas de dépendance à flash-attention), bf16, TF32, gradient checkpointing.

## 7. Mémoire et réglages sur RTX 5080 (16 Go)

| Config | Poids | Réglages par défaut |
|---|---|---|
| `ministral3b_lora.yaml` (recommandée) | bf16, ~8 Go | batch 2 × accumulation 8, lr 1e-4, r 32, 3 époques, `max_length` 2048 |
| `ministral3b_qlora.yaml` | NF4, ~3 Go | batch 4 × accumulation 4, lr 2e-4, `paged_adamw_8bit`, `max_length` 3072 |

En cas de « CUDA out of memory » : `--set training.per_device_train_batch_size=1 --set
training.gradient_accumulation_steps=16`, baisser `data.max_length`, réduire `eval.batch_size` (la sonde
génère pendant l'entraînement) ou passer en QLoRA. Fermer les applications qui utilisent le GPU (navigateur,
session graphique sur la même carte) libère aussi de la mémoire.

Ces valeurs n'ont pas été mesurées sur une RTX 5080 (l'environnement de développement n'a pas de GPU) :
ce sont des estimations à confirmer au premier lancement (`nvidia-smi` pendant l'entraînement).

## 8. Tests

```bash
cd entrainement && python -m pytest -q
```

Les tests couvrent les contrôles qualité, le chargement et le découpage des données, la configuration, et une
chaîne complète sur CPU (entraînement, évaluation, comparaison, fusion, génération) avec un Ministral 3
miniature à poids aléatoires (`tests/tiny_model.py`, même architecture que le vrai). Sur CPU, le noyau Triton
de TRL est remplacé dans les tests par un équivalent PyTorch ; sur GPU, c'est le vrai noyau qui tourne.
