# CanTraceDiag

[![CI](https://github.com/Jilanos/CanTraceDiag/actions/workflows/ci.yml/badge.svg)](https://github.com/Jilanos/CanTraceDiag/actions/workflows/ci.yml)

**CanTraceDiag transforme une trace CANalyzer `.asc` et ses DBC en poste de diagnostic local : import, décodage, graphes synchronisés, curseurs A/B, vue trace filtrable et reprise de session.**

L'objectif est simple : explorer hors véhicule des acquisitions CAN réelles, sans serveur distant, sans outil propriétaire ouvert en permanence, et sans charger toute la trace dans le navigateur.

![Workspace CanTraceDiag](docs/assets/cantracediag-workspace.png)

## Ce que fait l'outil

- **Import ASC + DBC** depuis le navigateur ou par chemin serveur.
- **Décodage DBC multi-fichiers** avec détection des IDs ambigus.
- **Graphes empilés** par signal, zoom, pan, grille et curseurs A/B.
- **Mesures instantanées** : valeurs au curseur et delta temps/valeur.
- **Trace table** paginée, filtrable, avec colonnes configurables.
- **Inspecteur de trame** : payload brut, message décodé et signaux physiques.
- **Bibliothèque DBC locale** pour réutiliser les bases sans re-upload.
- **Reprise de session** au redémarrage via workspace local hors dépôt.
- **Lancement 1 clic Windows + WSL** avec raccourci Bureau.

## Aperçu

### Graphes et curseurs

Les signaux sélectionnés sont tracés en escaliers, avec un axe temps commun. Les curseurs A/B se placent au clic, se déplacent au drag, et alimentent les mesures sous le graphe.

![Curseurs A/B](docs/assets/cantracediag-cursors.png)

### Colonnes de trace

La vue trace est pensée pour l'inspection répétée : filtres, pagination, statut de décodage, sélection de trame, ordre/largeur/format de colonnes persistés localement.

![Colonnes de trace](docs/assets/cantracediag-columns.png)

### Bibliothèque DBC

Les DBC importés sont conservés dans le workspace utilisateur, dédupliqués par contenu, et réutilisables au prochain chargement.

![Bibliothèque DBC](docs/assets/cantracediag-library.png)

## Installation développeur

Prérequis : Python 3.11+.

```bash
cd /home/paul/dev/CanTraceDiag
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,api]"
pytest
```

Validation locale recommandée :

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

## Lancer l'interface

Depuis l'environnement virtuel :

```bash
cantracediag serve --open
```

Depuis les sources sans script installé :

```bash
PYTHONPATH=src python -m cantracediag.cli serve --open
```

Par défaut, l'UI est disponible sur :

```text
http://127.0.0.1:8000
```

Si le port demandé est déjà pris, `serve` choisit un port libre. Si une instance CanTraceDiag tourne déjà sur ce port, la commande rouvre simplement le navigateur au lieu de démarrer un second serveur.

## Lancement 1 clic sous Windows + WSL

Une installation par poste suffit. Depuis PowerShell Windows :

```powershell
cd "\\wsl.localhost\Ubuntu\home\paul\dev\CanTraceDiag"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-shortcut.ps1
```

Le script crée :

- `CanTraceDiag.local.cmd` à la racine du dépôt, avec le chemin WSL du clone ;
- un raccourci **CanTraceDiag** sur le Bureau Windows ;
- l'icône dédiée du projet sur ce raccourci.

Ensuite, un double-clic démarre le serveur dans WSL et ouvre l'UI dans le navigateur Windows. Relancer le script après un déplacement du dépôt ou après une mise à jour de l'icône.

## Tester rapidement

Les fixtures synthétiques permettent de vérifier le flux complet sans données client :

```bash
cantracediag info tests/fixtures/sample.asc --dbc tests/fixtures/sample.dbc
cantracediag signals tests/fixtures/sample.dbc
cantracediag serve --open
```

Dans l'UI :

1. Cliquer **Trace** et choisir `tests/fixtures/sample.asc`.
2. Cliquer **DBC files** et choisir `tests/fixtures/sample.dbc`.
3. Cliquer **Load**.
4. Cocher des signaux dans le panneau **Signals**.
5. Tester zoom, pan, curseurs A/B, filtres de trace, **Columns...**, **Library** et **Clear cache**.

Depuis le navigateur Windows, le dépôt WSL est visible via un chemin de ce type :

```text
\\wsl.localhost\Ubuntu\home\paul\dev\CanTraceDiag\tests\fixtures
```

## Workflow utilisateur

1. **Importer** une trace `.asc` et un ou plusieurs fichiers `.dbc`.
2. **Résoudre les conflits DBC** si plusieurs bases déclarent le même arbitration ID avec des messages non équivalents.
3. **Sélectionner les signaux** présents dans la trace ou disponibles dans la DBC.
4. **Explorer les graphes** avec zoom, pan, grille et curseurs A/B.
5. **Inspecter la trace** avec filtres, pagination, détails de trames et signaux décodés.
6. **Rouvrir plus tard** : le workspace restaure la dernière analyse et la bibliothèque DBC.

## Ligne de commande

```bash
# Résumer un import
cantracediag info /chemin/trace.asc --dbc systeme.dbc --dbc annexe.dbc

# Lister messages et signaux d'une ou plusieurs DBC
cantracediag signals systeme.dbc

# Lancer l'UI locale
cantracediag serve --port 8000 --open
```

## API locale

CanTraceDiag expose une API FastAPI locale utilisée par l'UI :

- `POST /api/import-files` : import via upload navigateur ;
- `POST /api/import` : import par chemins serveur ;
- `POST /api/resolve` : résolution de conflits DBC ;
- `GET /api/status` : état de session ;
- `GET /api/signals` : catalogue de signaux ;
- `GET /api/series` : séries fenêtrées/downsamplées ;
- `GET /api/cursor` : valeur la plus proche d'un curseur ;
- `GET /api/trace` : vue trace paginée et filtrée ;
- `GET /api/frame-signals` : signaux décodés pour une trame ;
- `GET /api/dbc-library` : bibliothèque DBC ;
- `POST /api/workspace-purge` : purge cache + dernière analyse.

## Workspace local

En mode normal, les données persistantes sont stockées hors dépôt sous :

```text
~/.local/share/cantracediag/
```

Variables utiles :

- `CANTRACEDIAG_DATA_DIR` : changer le dossier de workspace ;
- `CANTRACEDIAG_DBC_CAP` : nombre maximum de DBC conservés, défaut `20` ;
- `CANTRACEDIAG_EPHEMERAL=1` : désactiver la persistance, utilisé par les tests.

Le dépôt ignore les traces, DBC réels et caches pour éviter de versionner des données véhicule ou client.

## Architecture

```text
src/cantracediag/
├── api.py          # FastAPI + static UI
├── cli.py          # commandes info, signals, serve
├── dbc.py          # chargement multi-DBC + conflits
├── decode.py       # décodage signaux physiques
├── formats/asc.py  # lecteur CANalyzer ASCII
├── pipeline.py     # import ASC -> index
├── store.py        # DuckDB + requêtes fenêtrées
├── workspace.py    # bibliothèque DBC + reprise de session
└── web/            # UI locale, favicon, assets statiques
```

Le backend garde l'index DuckDB côté local et ne renvoie au navigateur que des fenêtres utiles : séries downsamplées, pages de trace, détails de trame. Ce choix garde l'interface fluide même quand les traces grossissent.

## Captures README

Les captures sont générées depuis l'application réelle :

```bash
.venv/bin/python scripts/capture-readme-screenshots.py
```

Le script démarre un serveur éphémère, importe une trace synthétique décodable, pilote Chromium avec Playwright et met à jour `docs/assets/`.

## État actuel

Livré aujourd'hui :

- import ASC ;
- décodage DBC ;
- index DuckDB ;
- UI locale avec graphes, trace, inspecteur et curseurs ;
- workspace persistant ;
- bibliothèque DBC ;
- raccourci Windows + WSL ;
- favicon et icône de raccourci.

Limites connues :

- BLF/MF4 non complets ;
- pas de replay temps réel ;
- pas de packaging Windows natif ;
- pas encore de budget CI représentatif de grosses traces autour de 150 Mo.
