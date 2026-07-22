## req_009_moteur_local_asc_dbc_pwa_local_first - Moteur local ASC DBC pour PWA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: General
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Construire le premier moteur local de diagnostic pour la PWA : importer une
  trace ASC, charger un ou plusieurs DBC, indexer les frames/events côté
  navigateur, exposer des requêtes locales équivalentes aux principaux endpoints
  FastAPI, et permettre une exploration minimale sans backend.
- S'appuyer sur le résultat positif du jalon 0.1 : lecture ASC par chunks en Web
  Worker avec preuve 500 MiB.
- Garder l'implémentation Python actuelle comme oracle de parité tant que le
  moteur navigateur n'a pas couvert les fixtures synthétiques et les workflows
  principaux.

# Context
- Le spike 0.1 a validé que le navigateur peut scanner 50 MiB, 150 MiB et
  500 MiB par chunks de 8 MiB sans retenir toutes les frames en objets
  JavaScript. Le prochain risque n'est donc plus la lecture brute, mais la
  structuration locale : parser ASC, stockage/index, DBC, décodage, requêtes et
  parité UI.
- L'architecture actuelle expose les responsabilités via `/api/status`,
  `/api/signals`, `/api/series`, `/api/trace`, `/api/trace-locate`,
  `/api/cursor`, `/api/frame-signals`, import job et purge. Le jalon 0.2 doit
  définir une façade locale équivalente, même si certaines réponses restent
  limitées aux fixtures et à un workflow minimal.
- Le choix de stockage doit rester guidé par preuve : IndexedDB/OPFS pour
  métadonnées et artefacts persistants, DuckDB-WASM seulement si les benchmarks
  justifient son coût.

# Acceptance criteria
- AC1: Le parser ASC TypeScript couvre les semantics utiles du parser Python sur
  les fixtures synthétiques existantes et respecte le traitement streaming par
  chunks.
- AC2: Un backend local navigateur expose une façade de requêtes pour `status`,
  `signals`, `trace`, `trace-locate`, `series`, `cursor`, `frame-signals`,
  import job et purge, sans serveur FastAPI.
- AC3: Le stockage/index local écrit les frames et events par batch, sans
  matérialiser toute la trace en objets JavaScript retenus.
- AC4: Le jalon choisit et documente le stockage retenu pour l'incrément :
  IndexedDB, OPFS, DuckDB-WASM ou combinaison, avec justification par mesures.
- AC5: Le chargement DBC et le décodage couvrent au minimum les fixtures de test
  du dépôt, y compris conflits simples d'arbitration ID et résolution opérateur.
- AC6: Une UI minimale peut importer une trace et un DBC locaux, afficher le
  statut, la liste de signaux, une trace paginée, au moins une série sélectionnée
  et des détails de frame, sans backend.
- AC7: La parité avec l'implémentation Python est vérifiée sur les fixtures
  synthétiques pour parsing ASC, description frames, signaux décodés et trace
  paginée.
- AC8: Les limites restantes avant le jalon 0.3 sont documentées : persistance
  workspace complète, packaging PWA/offline, export/import workspace,
  performance gros fichiers complète et compatibilité navigateurs.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Roadmap(s): `road_001_architecture_pwa_spa_local_first`

# References
- `logics/roadmap/road_001_architecture_pwa_spa_local_first.md`
- `spikes/pwa-500mb/results-2026-07-22.md`
- `src/cantracediag/api.py`
- `src/cantracediag/pipeline.py`
- `src/cantracediag/formats/asc.py`
- `src/cantracediag/dbc.py`
- `src/cantracediag/decode.py`
- `src/cantracediag/store.py`
- `tests/fixtures/sample.asc`
- `tests/fixtures/sample.dbc`
- `tests/fixtures/sample_conflict.dbc`
- `tests/fixtures/sample_dec.asc`

# AI Context
- Summary: Request for roadmap milestone 0.2: build the browser-local ASC/DBC
  diagnostic engine after the 500 MiB chunking spike, preserving Python parity
  on fixtures and exposing local equivalents of the current API concepts.
- Keywords: request-draft, pwa, local-first, asc, dbc, decode, indexeddb, opfs,
  duckdb-wasm, local backend, parity, worker, trace, series
- Use when: Starting or reviewing the local ASC/DBC engine milestone after the
  successful 0.1 spike.
- Skip when: Only working on static PWA deployment/offline shell or the existing
  FastAPI backend.

# Backlog
- `item_019_moteur_local_asc_dbc_pour_pwa_local_first`
