## task_019_moteur_local_asc_dbc_pour_pwa_local_first - Moteur local ASC DBC pour PWA local-first
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_019_moteur_local_asc_dbc_pour_pwa_local_first`

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

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_019_moteur_local_asc_dbc_pour_pwa_local_first.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_019_moteur_local_asc_dbc_pour_pwa_local_first.md` after implementation.
- Implemented PWA local ASC/DBC engine under spikes/pwa-local-engine. Validation passed: node spikes/pwa-local-engine/build-browser.mjs; node --test spikes/pwa-local-engine/tests/*.test.ts; CTD_ENGINE_PORT=9881 CTD_ENGINE_DEBUG_PORT=9231 node spikes/pwa-local-engine/browser-smoke.mjs. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Known limits documented for 0.3.
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.

# Report
- Finished on 2026-07-22.
- Linked backlog item(s): `item_019_moteur_local_asc_dbc_pour_pwa_local_first`
- Related request(s): `req_009_moteur_local_asc_dbc_pwa_local_first`
- Implemented the roadmap 0.2 local engine milestone under
  `spikes/pwa-local-engine`.
- Delivered a TypeScript ASC parser, DBC fixture parser, decoder, columnar
  batched store, local query facade, browser build, minimal no-backend UI, tests
  and Chromium smoke coverage.
- Evidence and known limits are recorded in
  `spikes/pwa-local-engine/results-2026-07-22.md`.

# AI Context
- Summary: Task for roadmap milestone 0.2: implement the browser-local ASC/DBC
  engine, local query facade, fixture parity checks, storage decision, and
  minimal no-backend diagnostic workflow.
- Keywords: task, pwa, local-first, asc, dbc, decode, indexeddb, opfs,
  duckdb-wasm, local backend, fixture parity, trace, series
- Use when: Starting or closing the 0.2 local engine implementation.
- Skip when: Only planning 0.3 static deployment/offline packaging.

# Links
- Request: `req_009_moteur_local_asc_dbc_pwa_local_first`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC2 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC3 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC4 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC5 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC6 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC7 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
- request-AC8 -> This task. Proof: PWA local ASC/DBC engine implemented and measured: TypeScript ASC parser, local query facade, columnar batched store, DBC fixture parser/decode, no-backend UI, fixture parity tests and Chromium smoke. Evidence recorded in spikes/pwa-local-engine/results-2026-07-22.md. Source: `spikes/pwa-local-engine/results-2026-07-22.md`
