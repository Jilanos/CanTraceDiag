## item_019_moteur_local_asc_dbc_pour_pwa_local_first - Moteur local ASC DBC pour PWA local-first
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
Le jalon 0.1 a prouvé la lecture ASC chunkée côté navigateur. Le jalon 0.2 doit
transformer ce spike en moteur local exploitable : parser ASC, indexer
frames/events, charger les DBC, décoder à la demande et fournir une façade de
requêtes que l'UI peut consommer sans FastAPI. Le backlog reste borné à une
parité fixture/workflow minimal, pas à une PWA complète prête à déployer.

# Scope
- In:
  - Porter le parser ASC utile en TypeScript avec tests de parité sur fixtures.
  - Définir une façade `LocalPwaBackend` ou équivalent pour remplacer les appels
    `/api/*` dans un chemin expérimental.
  - Choisir et documenter le stockage de l'incrément : IndexedDB, OPFS,
    DuckDB-WASM ou combinaison justifiée.
  - Indexer frames/events par batch sans retenir toutes les frames en mémoire.
  - Charger les DBC de fixtures, extraire messages/signaux et détecter les
    conflits simples d'arbitration ID.
  - Décoder les signaux nécessaires aux fixtures et aux séries sélectionnées.
  - Fournir status, signals, trace paginée, trace-locate, series, cursor,
    frame-signals, import job et purge côté navigateur.
  - Adapter une UI minimale ou le spike existant pour exercer le workflow
    trace + DBC sans backend.
  - Enregistrer les mesures, décisions de stockage et limites restantes.
- Out:
  - Packaging PWA/offline complet.
  - Export/import workspace portable final.
  - Support complet BLF/MF4.
  - Parité exhaustive avec toutes les subtilités `cantools`.
  - Optimisation définitive des très grosses traces au-delà du workflow mesuré.
  - Suppression de l'architecture FastAPI existante.

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

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1 requires TypeScript ASC parser parity.
- request-AC2 -> This backlog slice. Proof: AC2 requires a local browser query facade.
- request-AC3 -> This backlog slice. Proof: AC3 requires batched local indexing without retained full-trace objects.
- request-AC4 -> This backlog slice. Proof: AC4 requires storage decision evidence.
- request-AC5 -> This backlog slice. Proof: AC5 requires DBC load/decode fixture coverage and conflict handling.
- request-AC6 -> This backlog slice. Proof: AC6 requires a minimal no-backend UI workflow.
- request-AC7 -> This backlog slice. Proof: AC7 requires Python parity checks on fixtures.
- request-AC8 -> This backlog slice. Proof: AC8 requires documented remaining limits before 0.3.

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
- Request: `req_009_moteur_local_asc_dbc_pwa_local_first`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Primary task(s): `task_019_moteur_local_asc_dbc_pour_pwa_local_first`

# AI Context
- Summary: Backlog slice for roadmap milestone 0.2, building a browser-local
  ASC/DBC diagnostic engine with local query facade and fixture parity after the
  successful 500 MiB scan spike.
- Keywords: backlog-groom, pwa, local-first, asc, dbc, decode, indexeddb, opfs,
  duckdb-wasm, local backend, parity, trace, series, worker
- Use when: Implementing or reviewing the 0.2 local engine milestone.
- Skip when: Working on the 0.3 static PWA/offline deployment shell.

# Priority
- Priority: High
- Rationale: This is the next gating increment after the successful 0.1 spike;
  it determines whether the PWA path can preserve the diagnostic workflow.

# Notes
- Hybrid rationale: Derived from request `req_009_moteur_local_asc_dbc_pwa_local_first` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_009_moteur_local_asc_dbc_pwa_local_first.md`.
- Generated locally by logics-manager.
- Task `task_019_moteur_local_asc_dbc_pour_pwa_local_first` was finished via `logics-manager flow finish task` on 2026-07-22.

# Tasks
- `task_019_moteur_local_asc_dbc_pour_pwa_local_first`
