## item_018_spike_navigateur_500_mo_pour_pwa_local_first - Spike navigateur 500 Mo pour PWA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
La migration PWA/SPA local-first ne doit pas commencer par une réécriture large.
Le premier risque est la capacité réelle du navigateur à parcourir des traces ASC
volumineuses sans pic mémoire incontrôlé. Ce backlog isole donc un spike de
lecture et scan chunkés, avec preuves mesurées, avant de décider si le jalon 0.2
peut démarrer.

# Scope
- In:
  - Créer ou utiliser la branche `feat/pwa-local-first`.
  - Construire un spike frontend minimal avec sélection de fichier ASC local.
  - Lire le fichier par chunks via `File.slice()` et `TextDecoder` streaming.
  - Gérer correctement les lignes coupées entre deux chunks.
  - Exécuter le scan dans un Web Worker.
  - Afficher progression, débit, annulation et synthèse de résultat.
  - Mesurer 50 Mo et 150 Mo, puis 500 Mo quand une fixture locale représentative
    est disponible.
  - Produire un rapport go/no-go pour la suite de la roadmap.
- Out:
  - Porter le parser DBC.
  - Réécrire les graphes ou la table trace complète.
  - Choisir définitivement OPFS, IndexedDB ou DuckDB-WASM pour tout le produit.
  - Supprimer ou modifier l'architecture FastAPI actuelle.

# Acceptance criteria
- AC1: Une branche `feat/pwa-local-first` existe ou est explicitement utilisée
  pour isoler le spike du flux principal.
- AC2: Le spike lit un fichier ASC via `File.slice()` par chunks configurables,
  sans appeler de backend applicatif.
- AC3: Le parsing s'exécute dans un Web Worker et l'UI reste responsive pendant
  l'import, avec progression et annulation.
- AC4: Les lignes coupées entre deux chunks sont reconstruites correctement et
  couvertes par au moins un test ou fixture dédié.
- AC5: Les mesures couvrent au minimum 50 Mo et 150 Mo ; 500 Mo est mesuré dès
  qu'une fixture locale représentative est disponible.
- AC6: Le rapport de sortie documente temps de scan, taille de chunk retenue,
  observations mémoire, limites navigateur et décision go/no-go pour le jalon
  0.2.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1 requires the dedicated branch for the spike.
- request-AC2 -> This backlog slice. Proof: AC2 requires chunked `File.slice()` ASC reading.
- request-AC3 -> This backlog slice. Proof: AC3 requires Web Worker execution, responsive UI, progress, and cancel.
- request-AC4 -> This backlog slice. Proof: AC4 requires chunk-boundary line reconstruction coverage.
- request-AC5 -> This backlog slice. Proof: AC5 requires 50/150 MB measurements and 500 MB when fixture exists.
- request-AC6 -> This backlog slice. Proof: AC6 requires a measured go/no-go report for milestone 0.2.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_008_spike_navigateur_500_mo_pwa_local_first`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Primary task(s): `task_018_spike_navigateur_500_mo_pour_pwa_local_first`

# AI Context
- Summary: Backlog slice for roadmap milestone 0.1, proving browser-side
  chunked ASC scanning up to the 500 MB target before continuing the
  PWA/local-first migration.
- Keywords: backlog-groom, pwa, local-first, spike, asc, 500 mb, chunks,
  file.slice, textdecoder, web worker, memory, go-no-go
- Use when: Implementing or reviewing the 0.1 feasibility spike.
- Skip when: Working on DBC parity, local workspace persistence, or static PWA
  deployment after the spike.

# Priority
- Priority: High
- Rationale: This is the gating evidence for the whole PWA/local-first roadmap;
  without it, later migration work may be wasted.

# Notes
- Hybrid rationale: Derived from request `req_008_spike_navigateur_500_mo_pwa_local_first` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_008_spike_navigateur_500_mo_pwa_local_first.md`.
- Generated locally by logics-manager.
- Task `task_018_spike_navigateur_500_mo_pour_pwa_local_first` was finished via `logics-manager flow finish task` on 2026-07-22.

# Tasks
- `task_018_spike_navigateur_500_mo_pour_pwa_local_first`
