# CanTraceDiag

CanTraceDiag est un projet d'analyse et de relecture de traces CAN issues de Vector CANalyzer.

Objectif principal : explorer hors véhicule des acquisitions CAN enregistrées en conditions réelles, avec les DBC associées, afin de visualiser les signaux au cours du temps et d'inspecter les messages bruts échangés.

## Besoin cible

- Import de traces CANalyzer au format ASCII (`.asc`) dans le MVP.
- Architecture préparée pour ajouter d'autres formats plus tard (`.blf`, `.mf4`, autres exports).
- Chargement d'une ou plusieurs bases DBC.
- Décodage des messages CAN en signaux physiques.
- Vue graphes avec sélection des variables disponibles.
- Curseur temporel basé sur la valeur la plus proche, puis double curseur avec deltas.
- Vue trace configurable pour parcourir les trames et événements.
- Base technique extensible vers des traces volumineuses, BLF/MF4, exports Parquet, et usage local ou serveur.

## Choix recommandé pour le MVP

Le MVP recommandé est une application web locale, sans replay temps réel :

- Backend Python : ingestion, décodage DBC, indexation temporelle.
- Stockage intermédiaire : Parquet/DuckDB pour des traces grandes sans tout garder en mémoire UI.
- Frontend web : graphes interactifs en subplots partageant l'axe temporel, panneau de signaux, table de traces virtualisée.

Ce choix garde Python pour l'écosystème CAN (`python-can`, `cantools`) tout en laissant une interface utilisateur fluide pour les curseurs, deltas et tableaux volumineux. L'usage cible est local sous WSL dans un premier temps, avec une trajectoire compatible Windows/Linux.

Voir [docs/besoin-et-choix.md](docs/besoin-et-choix.md) pour l'analyse complète.

## Structure initiale

```text
.
├── docs/
│   ├── adr/
│   ├── besoin-et-choix.md
│   ├── product-backlog.md
│   ├── product-brief.md
│   └── roadmap.md
├── logics/
│   ├── architecture/
│   ├── product/
│   └── request/
├── src/cantracediag/
│   ├── __init__.py
│   ├── models.py
│   └── formats/
│       └── __init__.py
├── tests/
│   └── test_imports.py
├── pyproject.toml
└── README.md
```

## Installation développeur

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Prochaines entrées attendues

Pour implémenter le premier import réel, il faudra fournir :

- Un ou plusieurs extraits courts anonymisables de trace ASCII CANalyzer pour tests unitaires.
- Une sélection de DBC de test, conservées hors dépôt si elles ne doivent pas être publiées.
- La liste des signaux prioritaires à valider dans les premiers graphes.
- Les colonnes CANalyzer indispensables pour la première vue trace.
