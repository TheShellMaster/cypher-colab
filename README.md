# Cypher · Colab

Serveur **OpenAI-compatible** sur une VM Google Colab gratuite (GPU T4), avec tunnel Cloudflare, pour brancher **OpenCode** sur les modèles Cypher et exécuter des tâches agentiques réelles.

Inclut une interface **Open WebUI** (chat dans le navigateur) sur le même modèle.

Adapté de [enescingoz/colab-llm](https://github.com/enescingoz/colab-llm) (Ollama + Cloudflare Tunnel), avec les modèles publics du compte `TheShellMaster`.

## Pourquoi ce montage

Les Spaces Hugging Face en ZeroGPU gratuit donnent environ **90 secondes de GPU par jour** : 4 à 6 appels de modèle, alors qu'une tâche agentique en demande 10 à 40. Colab fournit une T4 pendant plusieurs heures, sans ce plafond.

## Modèles disponibles

Tous publics sur `huggingface.co/TheShellMaster`, en Q5_K_M.

| Clé | Dépôt | Taille | VRAM | Remarque |
|---|---|---|---|---|
| `coder-7b` | `cypher-Qwen2.5-Coder-7B-Instruct-abliterated` | 5,4 Go | ~6 Go | excellent pour l'agentique (code) |
| `qwen35-9b` *(défaut)* | `cypher-Huihui-Qwen3.5-9B-abliterated` | 6,5 Go | ~6,7 Go | le plus capable, **supporte les outils nativement** |
| `vl-8b` | `cypher-Huihui-Qwen3-VL-8B-Instruct-abliterated` | 5,9 Go | ~6 Go | vision + texte |
| `qwen35-4b` | `cypher-Huihui-Qwen3.5-4B-abliterated` | 3,1 Go | ~3,3 Go | rapide |
| `vl-4b` | `cypher-Huihui-Qwen3-VL-4B-Instruct-abliterated` | 2,9 Go | ~3 Go | vision, rapide |
| `qwen35-2b` | `cypher-Huihui-Qwen3.5-2B-abliterated` | 1,4 Go | ~1,5 Go | le plus léger |

Pour changer de modèle, modifie une seule ligne dans la première cellule du notebook :

```python
CHOIX = "qwen35-9b"
```

## Démarrage rapide (Colab)

1. Ouvre **[cypher_colab.ipynb](https://colab.research.google.com/github/TheShellMaster/cypher-colab/blob/main/cypher_colab.ipynb)**
2. `Exécution → Modifier le type d'exécution → T4 GPU`
3. `Exécution → Tout exécuter`
4. Copie l'URL `https://xxx.trycloudflare.com` affichée à l'étape "Tunnel public"

Le notebook installe Ollama, télécharge le GGUF, crée un alias court (OpenCode refuse les noms contenant `:`), charge le modèle en VRAM, ouvre le tunnel et installe Open WebUI.

## Brancher OpenCode

Le notebook affiche un `opencode.json` complet à l'étape "Configuration pour OpenCode". Place-le dans ton dossier de travail, puis :

```bash
opencode
```

Ou en une commande :

```bash
opencode run --model cypher/qwen35-9b "Explique ce dépôt"
```

La clé du provider est `cypher`, le `baseURL` est `https://<ton-url>.trycloudflare.com/v1`.

## Interface web (Open WebUI)

Le notebook installe aussi **Open WebUI** sur le port 8080 avec un second tunnel Cloudflare. Il génère automatiquement :

- un identifiant : `admin@cypher.local`
- un mot de passe aléatoire (affiché dans les logs du notebook)

Tu peux alors discuter avec le modèle depuis n'importe quel navigateur. Les inscriptions sont fermées après la création du compte admin.

## Tâches agentiques vérifiées

Trois tâches réelles (lire, éditer, créer + exécuter), vérifiées automatiquement :

```bash
python3 run_tasks.py --base-url https://<ton-url>.trycloudflare.com/v1
```

| # | Tâche | Outils attendus | Vérification |
|---|---|---|---|
| 1 | Lire `notes.txt` et trouver le port | `read` | la réponse contient `8090` |
| 2 | Corriger un bug dans `calc.py` | `read`, `edit` | `addition(2,3) == 5` |
| 3 | Créer `total.py` et l'exécuter | `write`, `bash` | `resultat.txt` contient `306.49` |

Sortie typique :

```
=== tâche 1 — lecture de fichier ===
[PASS] le port 8090 apparaît dans la réponse
=== tâche 2 — correction de bug ===\n[PASS] addition(2,3)=5 et multiplication(4,5)=20\n=== tâche 3 — création et exécution de script ===\n[PASS] resultat.txt contient 306.49\n\nrésultat : 3/3 tâches réussies
```

Options : `--only 1 2 3`, `--timeout 1200`, `--keep` (conserve les dossiers de travail).

## Sur Kaggle

Le notebook s'ouvre aussi sur Kaggle (GPU T4) : `Nouveau notebook → Importer depuis GitHub → TheShellMaster/cypher-colab → cypher_colab.ipynb`, puis active l'accélérateur GPU et exécute toutes les cellules.

## Sécurité

Le tunnel Cloudflare est **public et sans authentification** : toute personne qui possède l'URL peut interroger le modèle. L'URL change à chaque lancement et meurt avec la VM. Ne laisse pas tourner la session inutilement et arrête-la (`colab stop -s cypher`) après tes tests.

## Fichiers

```
cypher_colab.ipynb   notebook Colab (Ollama + tunnel + Open WebUI)
run_tasks.py         lanceur de tâches agentiques + vérifications
README.md            ce fichier
.gitignore
```

## Crédits

Structure du notebook et logique de tunnel issues de [enescingoz/colab-llm](https://github.com/enescingoz/colab-llm).
