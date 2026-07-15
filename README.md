# CanTraceDiag

CanTraceDiag est un projet d'analyse et de relecture de traces CAN issues de Vector CANalyzer.

Objectif principal : rejouer et explorer hors véhicule des acquisitions CAN enregistrées en conditions réelles, avec les DBC associées, afin de visualiser les signaux au cours du temps et d'inspecter les messages bruts échangés.

## Besoin cible

- Import de traces CANalyzer au format ASCII (`.asc` dans un premier temps).
- Chargement d'une ou plusieurs bases DBC.
- Décodage des messages CAN en signaux physiques.
- Vue graphes avec sélection des variables disponibles.
- Un ou deux curseurs temporels avec valeurs instantanées et deltas.
- Vue trace pour parcourir les trames échangées.
- Base technique extensible vers des traces volumineuses, BLF/MF4, exports Parquet, et usage local ou serveur.

## Choix recommandé pour le MVP

Le MVP recommandé est une application web locale :

- Backend Python : ingestion, décodage DBC, indexation temporelle.
- Stockage intermédiaire : Parquet/DuckDB pour des traces grandes sans tout garder en mémoire UI.
- Frontend web : graphes interactifs, panneau de signaux, table de traces virtualisée.

Ce choix garde Python pour l'écosystème CAN (`python-can`, `cantools`) tout en laissant une interface utilisateur fluide pour les curseurs, deltas et tableaux volumineux.

Voir [docs/besoin-et-choix.md](docs/besoin-et-choix.md) pour l'analyse complète.

## Structure initiale

```text
.
├── docs/
│   ├── besoin-et-choix.md
│   └── roadmap.md
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

- Un extrait de trace ASCII CANalyzer.
- Les DBC utilisées pendant l'acquisition.
- Les contraintes de volume typiques : durée, taille fichier, nombre de bus, nombre de signaux.
- Le comportement attendu pour les signaux multiplexés, invalides, absents ou non décodables.
