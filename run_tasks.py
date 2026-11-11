#!/usr/bin/env python3
"""Exécute des tâches agentiques concrètes via OpenCode sur le serveur Colab.

Chaque tâche est un dossier isolé avec ses fichiers, une configuration OpenCode
et une vérification automatique du résultat. Le script affiche PASS ou FAIL.

    python3 run_tasks.py --base-url https://xxxx.trycloudflare.com/v1

Options :
    --model     nom du modèle (défaut: cypher-coder)
    --only      ne lancer que certaines tâches (ex: --only 2 3)
    --timeout   délai par tâche en secondes (défaut: 900)
    --keep      conserve les dossiers de travail
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

OPENCODE_CONFIG = {
    "$schema": "https://opencode.ai/config.json",
    "permission": "allow",
    "providers": {
        "cypher": {
            "name": "Cypher Colab",
            "package": "@opencode/ai/providers/openai-compatible",
            "settings": {
                "baseURL": "",
                "apiKey": "ollama",
                "headerTimeout": 300000,
                "chunkTimeout": 300000,
            },
            "models": {},
        }
    },
}

DEFAULT_MODEL = "cypher-qwen35-4b"


NOTES = """\
# Notes d'exploitation

- Le cache est vidé toutes les 6 heures.
- Le serveur applicatif écoute sur le port 8090.
- La base de données tourne sur le port 5432.
- Les journaux sont écrits dans /var/log/app.
"""

CALC = """\
def addition(a, b):
    return a - b


def multiplication(a, b):
    return a * b
"""

VENTES = """\
produit,quantite,prix
clavier,3,25.50
souris,2,15.00
ecran,1,199.99
"""

TOTAL_ATTENDU = "306.49"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check_port(task_dir, output):
    if "8090" in output:
        return True, "le port 8090 apparaît dans la réponse"
    return False, "le port 8090 est absent de la réponse"


def check_calc(task_dir, output):
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import calc; print(calc.addition(2, 3)); print(calc.multiplication(4, 5))",
        ],
        cwd=task_dir,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, f"calc.py ne s'exécute pas: {proc.stderr.strip()[:200]}"
    lines = proc.stdout.split()
    if lines[:2] != ["5", "20"]:
        return False, f"addition(2,3)={lines[0]}, multiplication(4,5)={lines[1]}"
    return True, "addition(2,3)=5 et multiplication(4,5)=20"


def check_total(task_dir, output):
    result = task_dir / "resultat.txt"
    if not result.exists():
        return False, "resultat.txt n'a pas été créé"
    content = result.read_text(encoding="utf-8").strip()
    if TOTAL_ATTENDU in content:
        return True, f"resultat.txt contient {TOTAL_ATTENDU}"
    return False, f"resultat.txt contient {content[:80]!r} au lieu de {TOTAL_ATTENDU}"


TASKS = [
    {
        "id": 1,
        "name": "lecture de fichier",
        "prompt": (
            "Lis le fichier notes.txt du dossier courant. "
            "Sur quel port écoute le serveur applicatif ? "
            "Réponds uniquement par le numéro, sans phrase."
        ),
        "files": {"notes.txt": NOTES},
        "check": check_port,
    },
    {
        "id": 2,
        "name": "correction de bug",
        "prompt": (
            "Le fichier calc.py contient un bug : la fonction addition() soustrait "
            "au lieu d'additionner. Corrige-la avec l'outil edit. "
            "Ne modifie pas multiplication()."
        ),
        "files": {"calc.py": CALC},
        "check": check_calc,
    },
    {
        "id": 3,
        "name": "création et exécution de script",
        "prompt": (
            "Écris un script total.py qui lit ventes.csv (colonnes produit,quantite,prix) "
            "et écrit dans resultat.txt le total quantité×prix arrondi à 2 décimales, "
            "suivi d'un saut de ligne. Exécute-le ensuite avec l'outil bash "
            "(python3 total.py) pour produire le fichier."
        ),
        "files": {"ventes.csv": VENTES},
        "check": check_total,
    },
]


def build_config(task_dir, base_url, model):
    config = json.loads(json.dumps(OPENCODE_CONFIG))
    provider = config["providers"]["cypher"]
    provider["settings"]["baseURL"] = base_url
    provider["models"] = {
        model: {
            "modelID": model,
            "name": f"Cypher · {model.rsplit('/', 1)[-1]}",
            "capabilities": {"tools": True, "input": ["text"], "output": ["text"]},
            "limit": {"context": 16384, "output": 2048},
            "compatibility": {"maxTokensField": "max_tokens", "streamUsage": False},
        }
    }
    config["model"] = f"cypher/{model}"
    write(task_dir / "opencode.json", json.dumps(config, indent=2, ensure_ascii=False))


def run_task(task, workroot, base_url, model, timeout):
    task_dir = workroot / f"tache{task['id']}"
    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True)
    for name, content in task["files"].items():
        write(task_dir / name, content)
    build_config(task_dir, base_url, model)

    # --standalone force la lecture de l'opencode.json local. On ne touche pas à
    # XDG_CONFIG_HOME : OpenCode tente alors de re-télécharger son catalogue de
    # modèles et se bloque.
    # OpenCode résout le dossier du projet via la variable PWD, pas via le
    # répertoire courant du processus : sans elle, il ignore l'opencode.json
    # local et répond « Model unavailable ».
    env = {
        **os.environ,
        "PWD": str(task_dir),
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
    }

    # Au tout premier lancement dans un dossier neuf, OpenCode répond
    # « Model unavailable » le temps d'indexer la configuration. Un appel
    # `opencode models` amorce ce cache avant la vraie exécution.
    subprocess.run(
        ["opencode", "models"],
        cwd=task_dir,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )

    command = [
        "opencode",
        "run",
        "--standalone",
        "--model",
        f"cypher/{model}",
        task["prompt"],
    ]
    try:
        proc = subprocess.run(
            command,
            cwd=task_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = f"TIMEOUT après {timeout}s\n{exc.stdout or ''}"
        code = -1

    ok, detail = task["check"](task_dir, output)
    return {
        "id": task["id"],
        "name": task["name"],
        "ok": ok,
        "detail": detail,
        "code": code,
        "output": output,
        "dir": task_dir,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="URL .../v1 du serveur Colab")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="nom exact du modèle dans Ollama (voir `ollama list`)",
    )
    parser.add_argument("--only", nargs="*", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    if shutil.which("opencode") is None:
        sys.exit("opencode est introuvable dans le PATH")

    selected = [t for t in TASKS if args.only is None or t["id"] in args.only]
    if not selected:
        sys.exit("aucune tâche sélectionnée")

    workroot = Path(
        tempfile.mkdtemp(prefix="cypher-agent-") if not args.keep else "./agent-runs"
    )
    if args.keep:
        workroot.mkdir(parents=True, exist_ok=True)

    print(f"serveur : {args.base_url}")
    print(f"modèle  : cypher/{args.model}")
    print(f"dossier : {workroot.resolve()}\n", flush=True)

    results = []
    for task in selected:
        print(f"=== tâche {task['id']} — {task['name']} ===", flush=True)
        result = run_task(
            task, workroot, args.base_url, args.model, args.timeout
        )
        results.append(result)
        status = "PASS" if result["ok"] else "FAIL"
        print(f"[{status}] {result['detail']}")
        if not result["ok"]:
            print("--- sortie d'OpenCode ---")
            print(result["output"][-2500:])
        print("", flush=True)

    passed = sum(1 for r in results if r["ok"])
    print(f"résultat : {passed}/{len(results)} tâches réussies")
    if args.keep:
        print(f"fichiers conservés dans {workroot.resolve()}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
