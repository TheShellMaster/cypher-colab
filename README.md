# Cypher · Colab

Serveur **OpenAI-compatible** sur une VM Google Colab gratuite (GPU T4), avec
tunnel Cloudflare, pour brancher **OpenCode** sur les modèles Cypher et exécuter
des tâches agentiques réelles.

Adapté de **[enescingoz/colab-llm](https://github.com/enescingoz/colab-llm)**
(Ollama + Cloudflare Tunnel), avec les modèles publics du compte `TheShellMaster`
et un jeu de tâches vérifiées.

## Pourquoi ce montage

Les Spaces Hugging Face en ZeroGPU gratuit donnent environ **90 secondes de GPU
par jour** : 4 à 6 appels de modèle, alors qu'une tâche agentique en demande 10 à
40. Colab fournit une T4 pendant plusieurs heures, sans ce plafond.

## Démarrage

1. Ouvre **[cypher_colab.ipynb](https://colab.research.google.com/github/TheShellMaster/cypher-colab/blob/main/cypher_colab.ipynb)**
2. `Exécution → Modifier le type d'exécution → T4 GPU`
3. `Exécution → Tout exécuter`
4. Copie l'URL `https://xxx.trycloudflare.com` affichée à l'étape 6

Le notebook installe Ollama, télécharge le GGUF, ouvre le tunnel et affiche
directement le `opencode.json` à copier.

## Modèles disponibles

Tous publics sur `huggingface.co/TheShellMaster`, en Q5_K_M.

| Clé | Dépôt | Taille | Remarque |
|---|---|---|---|
| `coder-7b` *(défaut)* | `cypher-Qwen2.5-Coder-7B-Instruct-abliterated` | 5,4 Go | le meilleur pour les tâches agentiques |
| `qwen35-9b` | `cypher-Huihui-Qwen3.5-9B-abliterated` | 6,5 Go | le plus capable, un peu juste sur T4 |
| `vl-8b` | `cypher-Huihui-Qwen3-VL-8B-Instruct-abliterated` | 5,9 Go | vision + texte |
| `qwen35-4b` | `cypher-Huihui-Qwen3.5-4B-abliterated` | 3,1 Go | rapide |
| `vl-4b` | `cypher-Huihui-Qwen3-VL-4B-Instruct-abliterated` | 2,9 Go | vision, rapide |
| `qwen35-2b` | `cypher-Huihui-Qwen3.5-2B-abliterated` | 1,4 Go | le plus léger |

Pour changer de modèle, modifie une seule ligne dans la première cellule :

```python
CHOIX = "coder-7b"
```

## Brancher OpenCode

Le notebook imprime un `opencode.json` complet (étape 8). Place-le dans ton
dossier de travail, puis :

```bash
opencode
```

Ou en une commande :

```bash
opencode run --model cypher/coder-7b "Explique ce dépôt"
```

## Tâches agentiques vérifiées

```bash
python3 run_tasks.py --base-url https://xxx.trycloudflare.com/v1
```

| # | Tâche | Outils attendus | Vérification |
|---|---|---|---|
| 1 | Lire `notes.txt` et trouver le port | `read` | la réponse contient `8090` |
| 2 | Corriger un bug dans `calc.py` | `read`, `edit` | `addition(2,3) == 5` |
| 3 | Créer `total.py` et l'exécuter | `write`, `bash` | `resultat.txt` contient `306.49` |

```
=== tâche 1 — lecture de fichier ===
[PASS] le port 8090 apparaît dans la réponse
=== tâche 2 — correction de bug ===
[PASS] addition(2,3)=5 et multiplication(4,5)=20
=== tâche 3 — création et exécution de script ===
[PASS] resultat.txt contient 306.49

résultat : 3/3 tâches réussies
```

Options : `--only 2 3`, `--timeout 1800`, `--keep`.

## Sécurité

Le tunnel Cloudflare est **public et sans authentification** : toute personne qui
possède l'URL peut interroger le modèle. L'URL change à chaque lancement et meurt
avec la VM. Ne laisse pas tourner la session inutilement.

## Dépannage

| Symptôme | Piste |
|---|---|
| `ollama pull` échoue | le notebook bascule automatiquement sur un téléchargement direct du GGUF |
| Pas d'URL Cloudflare | relancer la cellule 6 |
| Réponses lentes | choisir `qwen35-4b` ou `qwen35-2b` |
| `CUDA out of memory` | choisir un modèle plus petit |

## Crédits

Structure du notebook et logique de tunnel issues de
[enescingoz/colab-llm](https://github.com/enescingoz/colab-llm).
