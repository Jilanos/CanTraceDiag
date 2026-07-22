## task_018_spike_navigateur_500_mo_pour_pwa_local_first - Spike navigateur 500 Mo pour PWA local-first
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
- `item_018_spike_navigateur_500_mo_pour_pwa_local_first`

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

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Use `python3 -m logics_manager flow progress task task_018_spike_navigateur_500_mo_pour_pwa_local_first.md --progress <n>%` during multi-wave work.
- Run `python3 -m logics_manager flow finish task task_018_spike_navigateur_500_mo_pour_pwa_local_first.md` after implementation.
- Implemented isolated PWA 500 MB ASC spike under spikes/pwa-500mb. Validation passed: node --test spikes/pwa-500mb/scanner-core.test.mjs; Chromium CDP browser benchmarks passed for 50 MiB, 150 MiB, and 500 MiB synthetic ASC fixtures with 8 MiB chunks. Evidence recorded in spikes/pwa-500mb/results-2026-07-22.md. Decision: go for roadmap milestone 0.2 with worker/chunk constraints.
- Finish workflow executed on 2026-07-22.
- Linked backlog/request close verification passed.

# Report
- Finished on 2026-07-22.
- Linked backlog item(s): `item_018_spike_navigateur_500_mo_pour_pwa_local_first`
- Related request(s): `req_008_spike_navigateur_500_mo_pwa_local_first`
- Implemented an isolated static browser spike under `spikes/pwa-500mb`.
- Browser evidence covers 50 MiB, 150 MiB, and 500 MiB synthetic ASC fixtures
  with 8 MiB chunks. Results are recorded in
  `spikes/pwa-500mb/results-2026-07-22.md`.
- Decision: go for roadmap milestone 0.2, while keeping parsing in a Web Worker
  and avoiding retained per-frame JavaScript objects during import.

# AI Context
- Summary: Task for the first PWA/local-first milestone: implement and measure a
  browser-side chunked ASC scanning spike with Web Worker execution and 50/150
  MB evidence, extending to 500 MB when a representative fixture is available.
- Keywords: task, pwa, local-first, asc, 500 mb, chunks, file.slice,
  textdecoder, web worker, memory, benchmark, go-no-go
- Use when: Starting or closing the roadmap 0.1 feasibility spike.
- Skip when: Implementing DBC parsing, local workspace persistence, or static
  deployment after the go/no-go decision.

# Links
- Request: `req_008_spike_navigateur_500_mo_pwa_local_first`
- Roadmap: `road_001_architecture_pwa_spa_local_first`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Proof: PWA 500 MB spike implemented and measured: branch feat/pwa-local-first, static browser worker scanner, chunked File.slice import, boundary tests, Chromium CDP benchmarks for 50/150/500 MiB, and go decision for milestone 0.2. Source: `spikes/pwa-500mb/results-2026-07-22.md`
- request-AC2 -> This task. Proof: PWA 500 MB spike implemented and measured: branch feat/pwa-local-first, static browser worker scanner, chunked File.slice import, boundary tests, Chromium CDP benchmarks for 50/150/500 MiB, and go decision for milestone 0.2. Source: `spikes/pwa-500mb/results-2026-07-22.md`
- request-AC3 -> This task. Proof: PWA 500 MB spike implemented and measured: branch feat/pwa-local-first, static browser worker scanner, chunked File.slice import, boundary tests, Chromium CDP benchmarks for 50/150/500 MiB, and go decision for milestone 0.2. Source: `spikes/pwa-500mb/results-2026-07-22.md`
- request-AC4 -> This task. Proof: PWA 500 MB spike implemented and measured: branch feat/pwa-local-first, static browser worker scanner, chunked File.slice import, boundary tests, Chromium CDP benchmarks for 50/150/500 MiB, and go decision for milestone 0.2. Source: `spikes/pwa-500mb/results-2026-07-22.md`
- request-AC5 -> This task. Proof: PWA 500 MB spike implemented and measured: branch feat/pwa-local-first, static browser worker scanner, chunked File.slice import, boundary tests, Chromium CDP benchmarks for 50/150/500 MiB, and go decision for milestone 0.2. Source: `spikes/pwa-500mb/results-2026-07-22.md`
- request-AC6 -> This task. Proof: PWA 500 MB spike implemented and measured: branch feat/pwa-local-first, static browser worker scanner, chunked File.slice import, boundary tests, Chromium CDP benchmarks for 50/150/500 MiB, and go decision for milestone 0.2. Source: `spikes/pwa-500mb/results-2026-07-22.md`
