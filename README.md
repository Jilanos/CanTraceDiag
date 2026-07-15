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
│   ├── models.py        # frames, événements, échantillons, catalogue signaux
│   ├── dbc.py           # chargement multi-DBC + détection d'IDs ambigus
│   ├── decode.py        # décodage trames -> signaux physiques
│   ├── store.py         # index DuckDB local + requêtes fenêtrées
│   ├── pipeline.py      # orchestration import ASC -> décodage -> index
│   ├── api.py           # API de requêtes + hôte de l'UI (FastAPI)
│   ├── cli.py           # CLI (info, signals, serve)
│   ├── formats/
│   │   └── asc.py       # lecteur CANalyzer ASCII
│   └── web/             # interface web locale (index.html, app.js)
├── tests/
│   ├── fixtures/        # ASC + DBC synthétiques (anonymisés)
│   ├── test_asc.py
│   ├── test_dbc_decode.py
│   ├── test_store_pipeline.py
│   └── test_api.py
├── pyproject.toml
└── README.md
```

## Installation développeur

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,api]"
pytest
```

## État livré

CanTraceDiag sait aujourd'hui importer des traces ASC, charger plusieurs DBC,
détecter les conflits DBC non équivalents, indexer l'analyse dans DuckDB local,
afficher des graphes empilés et parcourir une vue trace paginée. Les imports
via l'API web utilisent un fichier DuckDB temporaire hors dépôt ; les fichiers
ASC/DBC réels et caches restent exclus de Git.

Les limites connues restent : pas de BLF/MF4 complet, pas de replay temps réel,
pas de collaboration multi-utilisateur, pas de packaging Windows natif et pas
encore de budget de performance CI représentatif de 150 Mo.

Validation locale actuelle :

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

Dernière preuve enregistrée : 54 tests passés et 1 warning Starlette connu.

## Utilisation du MVP

Le MVP fournit une chaîne complète : import ASC, chargement de DBC, décodage,
indexation locale (DuckDB) et une interface web locale (graphes empilés + vue
trace configurable). Les traces et DBC réelles restent hors du dépôt.

### Ligne de commande

```bash
# Résumé d'un import (frames, décodage, événements, ambiguïtés d'ID)
cantracediag info /chemin/trace.asc --dbc systeme.dbc --dbc annexe.dbc

# Lister messages et signaux d'une ou plusieurs DBC
cantracediag signals systeme.dbc

# Lancer l'interface web locale (localhost par défaut)
cantracediag serve --port 8000
```

Depuis les sources sans installation :

```bash
PYTHONPATH=src python -m cantracediag.cli serve
```

### Interface web

Ouvrir `http://127.0.0.1:8000`, choisir les fichiers via l'explorateur natif du
système (boutons **Trace .asc…**, **DBC files…** pour une sélection multiple, ou
**DBC folder…** pour tout un dossier — seuls les `.dbc` sont retenus), puis
**Load**. Le navigateur téléverse le contenu des fichiers ; cela fonctionne donc
même quand le backend tourne sous WSL et le navigateur sous Windows. Ensuite :

- **Panneau signaux** : cocher les signaux à tracer ; la recherche couvre
  message, signal, ID, unité et DBC, avec distinction des signaux présents dans
  la trace et des signaux seulement disponibles dans la DBC.
- **Graphes empilés** : un sous-graphe par signal, axe temporel partagé, tracé
  en escalier (échantillonné-maintenu, sans interpolation). Le curseur affiche
  la valeur de l'échantillon le plus proche.
- **Vue trace** : trames brutes + messages/signaux décodés + événements non-data
  (`ErrorFrame`, `Status`), paginée. Clic sur une trame pour voir ses signaux.
  Bouton **Columns…** pour la visibilité, l'ordre, la largeur et le format des
  colonnes (persistés localement).

### API locale

`POST /api/import-files` (téléversement depuis le navigateur),
`POST /api/import` (chemin serveur, pour le CLI ; accepte les chemins
Windows/UNC), `GET /api/signals`, `/api/series`, `/api/cursor`, `/api/trace`,
`/api/frame-signals`, `/api/status`, `/api/import-job`, `/api/import-cancel`.
