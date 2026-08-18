# Tharos Core — Moteur de Migration & Résolution de Dette Technique

Tharos Core est une usine logicielle agentique conçue pour automatiser la modernisation de bases de code legacy (WinDev/WLanguage, Cobol) vers des architectures modernes (FastAPI, React, PostgreSQL).

Plutôt que d'effectuer une traduction textuelle aveugle, Tharos extrait l'Arbre de Syntaxe Abstraite (AST), construit un graphe de dépendances fonctionnel et orchestre un pipeline d'agents locaux et distants pour générer un code cible validé par des tests d'équivalence.

## Fonctionnalités

- **Parsing AST Déterministe :** Extraction de la logique métier sans dépendre d'un LLM pour éviter toute hallucination.
- **Pipeline Hybride :** Utilisation de LLM distants pour la traduction haute couche et de modèles locaux (TRM / Qwen) pour les boucles de correction à coût zéro.
- **Sandboxing Docker :** Validation automatique des comportements via l'exécution de tests `pytest` isolés.
- **Mode Offline / On-Premise :** Exécution 100 % locale sur matériel dédié (NVIDIA RTX 5090 / vLLM / Ollama).

## Stack Technique

- **Langage :** Python 3.12+
- **Parsing :** Tree-sitter / Parsers AST dédiés
- **Inférence IA :** vLLM, Ollama, API Anthropic/OpenAI
- **Environnement :** Docker / Pytest

## Démarrage Rapide

```bash
# Cloner le dépôt
git clone [https://github.com/TharosIA/tharos-core.git](https://github.com/TharosIA/tharos-core.git)
cd tharos-core

# Installer les dépendances avec uv
uv sync

# Lancer le parsing d'un fichier WinDev
python -m tharos.cli parse --input ./tests/samples/facturation.wdw
```
