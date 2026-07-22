## road_001_architecture_pwa_spa_local_first - Architecture PWA SPA local-first
> Date: 2026-07-22
> Status: Proposed
> Related product: (none yet)
> Related request: `req_007_passer_cantracediag_en_pwa_spa_local_first`
> Reminder: Update status, milestone scope, linked refs, risks, and success signals when you edit this doc.

# Summary
Plan the migration path for a dedicated branch that explores whether
CanTraceDiag can become a static, local-first SPA/PWA. The target model is that
the hosted site ships only frontend assets while traces, DBC files, derived
indexes, caches, and workspaces stay in each user's browser storage.

Planned branch:
- `feat/pwa-local-first`

Primary decision:
- Validate browser-side handling of uncommon but possible 500 MB ASC files
  before committing to a full rewrite of the Python-backed analysis engine.

Non-goals for the first exploration:
- Do not remove the existing FastAPI/Python architecture from `main`.
- Do not promise mobile support for large acquisitions.
- Do not require a public backend for the local-first workflow.

# Milestones
## 0.1 - Spike navigateur 500 Mo
- Goal: Prove or reject the feasibility of reading and scanning large ASC files
  inside a desktop browser without loading the whole file into memory.
- Workflow:
  - Request: `req_008_spike_navigateur_500_mo_pwa_local_first`
  - Backlog: `item_018_spike_navigateur_500_mo_pour_pwa_local_first`
  - Task: `task_018_spike_navigateur_500_mo_pour_pwa_local_first`
- Scope:
  - Create the `feat/pwa-local-first` branch.
  - Add a minimal isolated browser spike that uses `File.slice()` and
    `TextDecoder` streaming.
  - Parse chunk boundaries safely by preserving incomplete trailing lines.
  - Run parsing in a Web Worker so the UI remains responsive.
  - Track progress, cancellation, throughput, and approximate memory pressure.
  - Test with representative file sizes: 50 MB, 150 MB, and 500 MB when a
    suitable local fixture is available.
- Exit signal:
  - A 500 MB ASC file can be scanned line-by-line on Chrome/Edge desktop without
    browser tab failure or multi-GB object retention.
  - The spike records measured import time, peak memory observations, and the
    selected chunk size range.
  - If the result is negative, the roadmap stops before parser and DBC rewrite.
- Result 2026-07-22:
  - Completed by `task_018_spike_navigateur_500_mo_pour_pwa_local_first`.
  - Chromium headless measurements passed for 50 MiB, 150 MiB, and 500 MiB
    synthetic ASC fixtures with 8 MiB chunks.
  - Evidence: `spikes/pwa-500mb/results-2026-07-22.md`.
  - Decision: go for milestone 0.2 with Web Worker parsing and no retained
    per-frame JavaScript objects during import.

## 0.2 - Moteur local ASC DBC
- Goal: Replace the backend-dependent import/query flow with a local browser
  engine that preserves the current diagnostic workflow.
- Workflow:
  - Request: `req_009_moteur_local_asc_dbc_pwa_local_first`
  - Backlog: `item_019_moteur_local_asc_dbc_pour_pwa_local_first`
  - Task: `task_019_moteur_local_asc_dbc_pour_pwa_local_first`
- Scope:
  - Port the ASC scanner semantics from Python to TypeScript with fixture parity
    tests.
  - Choose the persistence stack after the 0.1 measurements:
    - OPFS for large local files/index artifacts when available.
    - IndexedDB for workspace metadata and preferences.
    - DuckDB-WASM only if query benchmarks justify the complexity.
  - Store frames/events/index data in batches; never materialize the whole trace
    as JavaScript objects.
  - Define a workspace schema for trace metadata, imported DBC files, indexes,
    signal caches, UI preferences, and schema version.
  - Evaluate DBC support:
    - Prefer a maintained JavaScript/WASM DBC parser if it covers required
      decoding behavior.
    - Otherwise port the required subset of the current Python DBC/decode logic.
  - Implement arbitration ID conflict detection and operator resolution.
  - Implement local equivalents for current API concepts: status, signals,
    series, cursor, trace, trace locate, frame signals, import job, and purge.
  - Decode selected signals on demand and cache series windows progressively.
- Exit signal:
  - Existing synthetic fixtures pass parity checks for ASC parsing, DBC loading,
    frame description, signal decode, trace pagination, and selected series.
  - The UI can import a local trace, select signals, inspect rows, and restore a
    workspace without a running FastAPI server.
- Result 2026-07-22:
  - Completed by `task_019_moteur_local_asc_dbc_pour_pwa_local_first`.
  - Implemented under `spikes/pwa-local-engine`.
  - Validation passed for TypeScript ASC parser parity, DBC fixture loading,
    local decode, columnar store queries, local API facade, browser build, and
    Chromium smoke import of `sample.asc` + `sample.dbc` without FastAPI.
  - Evidence: `spikes/pwa-local-engine/results-2026-07-22.md`.
  - Remaining production limits before 0.3 are documented in
    `spikes/pwa-local-engine/storage-decision-2026-07-22.md` and the result
    report.

## 0.3 - PWA statique deployable
- Goal: Ship the local-first app as static assets that can be hosted behind the
  existing `paulmondou.fr` deployment model.
- Workflow:
  - Request: `req_010_pwa_statique_deployable_local_first`
  - Backlog: `item_020_pwa_statique_deployable_local_first`
  - Task: `task_020_pwa_statique_deployable_local_first`
- Scope:
  - Convert the frontend into a SPA build pipeline if needed, likely Vite or an
    equivalent minimal toolchain.
  - Add PWA manifest and service worker for app shell offline availability.
  - Add workspace list, workspace resume, workspace delete, and portable export
    or import.
  - Add storage quota checks and user-facing recovery paths for quota exhaustion.
  - Keep a backend abstraction during migration so the current FastAPI path can
    remain available until the local engine reaches parity.
  - Document static hosting through Caddy under either `paulmondou.fr` or a
    dedicated subdomain.
  - Add CI checks for TypeScript, browser unit tests, and at least one Playwright
    import smoke test with a bounded fixture.
- Exit signal:
  - A production static build works from a local file server and behind Caddy.
  - The default workflow requires no backend for import, analysis, persistence,
    or reload.
  - Deployment instructions clearly distinguish the new static PWA from the
    existing Python/FastAPI local server.
- Result 2026-07-22:
  - Completed by `task_020_pwa_statique_deployable_local_first`.
  - Implemented a reproducible static build under
    `spikes/pwa-local-engine/site/` with manifest, icon, service worker and
    cached app shell.
  - Added minimal browser-local workspaces: save, list, reopen, delete, purge,
    JSON export/import and quota error recovery coverage.
  - Chromium smoke passed from the static build without FastAPI, including
    manifest, service worker, app-shell cache and workspace save checks.
  - Evidence: `spikes/pwa-local-engine/pwa-results-2026-07-22.md`.
  - Remaining adoption limits are DBC parity, durable large indexes,
    product-scale benchmarks, cross-browser support and migration of the
    production UI.

## 0.4 - Migration UI produit et parite MVP
- Goal: Turn the technical PWA proof into a product-shaped MVP by migrating the
  current UI workflows and proving no-FastAPI parity from the static build.
- Workflow:
  - Request: `req_011_migrer_ui_produit_pwa_local_first_parite_mvp`
  - Backlog: `item_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`
  - Task: `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`
- Scope:
  - Inventory the current MVP surface from `src/cantracediag/web/app.js`,
    `src/cantracediag/web/index.html` and `src/cantracediag/api.py`.
  - Classify each workflow as `must-have`, `deferred` or `obsolete` before
    implementation so MVP completion is measurable.
  - Preserve the main visual structure and operator ergonomics of the current
    UI instead of keeping the minimal spike layout.
  - Add a `BackendPort` boundary and migrate the PWA path from `/api/...` calls
    to `LocalPwaBackend`.
  - Complete local equivalents for the MVP endpoints: import, conflict
    resolution, status, import job/progress/cancel, signals, series, cursor,
    trace, trace locate, frame signals, purge and export.
  - Move large trace/index persistence away from `localStorage` toward
    OPFS/IndexedDB or an equivalent browser-local strategy validated by tests.
  - Add parity tests against the Python backend oracle on representative
    fixtures.
  - Add a Chromium MVP smoke that fails on any remaining application fetch to
    `/api/...` in the static PWA build.
- Exit signal:
  - The static PWA build exercises the MVP workflow without FastAPI running.
  - The visual product path is close enough to the current UI that the operator
    can judge the same MVP, not a separate technical demo.
  - Remaining gaps are explicit, bounded, and not hidden behind the word
    "MVP".
- Progress 2026-07-22:
  - First implementation wave completed under
    `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`.
  - The static PWA build now uses the current product UI shell and a generated
    `product-app.mjs` with FastAPI network helpers replaced by a browser-local
    adapter.
  - Chromium smoke from `spikes/pwa-local-engine/site/` validates fixture import
    through the product UI, signal selection, trace pagination, manifest,
    service worker, app-shell cache and zero `/api/...` network calls.
  - Evidence:
    `spikes/pwa-local-engine/product-migration-results-2026-07-22.md`.
  - Remaining before exit: worker/chunk product import, OPFS/IndexedDB
    trace/index persistence, deeper DBC parity, conflict/filter/cursor/inspector
    smoke coverage, export and product-scale benchmarks.
  - Recovery prerequisite opened under
    `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
    after comparing with `origin/main`: the first PWA product wave missed the
    July 18/19 diagnostic UI features for A/B stats, unified measurements,
    report/export, workspace views and cache freshness.

# Sequencing
- Deliver milestones in ascending version order unless dependencies force a documented exception.
- Keep each increment independently reviewable and linked to concrete workflow docs.
- Make the 0.1 spike a hard gate. A negative 500 MB browser result should pivot
  the product back to a multi-session server architecture rather than continue a
  costly local-first rewrite.
- Preserve the existing Python implementation as the correctness oracle during
  parser and decoder migration.
- Prefer an adapter boundary for query operations so the UI can move gradually
  from `ApiBackend` to `LocalPwaBackend`.
- Treat every migration step that changes user-facing behavior as a separate
  backlog/task slice before implementation.

# Risks
- Browser memory expansion: 500 MB of ASC text can become several GB if parsed
  into retained JavaScript objects.
- Storage quota variance: OPFS/IndexedDB quotas differ by browser, device, free
  disk, and persistence grants.
- DBC parity risk: Python `cantools` behavior may be difficult to match exactly
  with a JavaScript parser.
- WASM complexity: DuckDB-WASM can help query performance but adds packaging,
  worker, persistence, and browser compatibility complexity.
- Performance variability: acceptable desktop Chrome/Edge performance does not
  imply Safari, mobile, or locked-down enterprise browser support.
- Product drift: a full local-first rewrite can consume effort that might be
  better spent on multi-session FastAPI deployment if the 0.1 results are weak.

# References
- Product brief(s): (none yet)
- Request(s): `req_007_passer_cantracediag_en_pwa_spa_local_first`, `req_008_spike_navigateur_500_mo_pwa_local_first`, `req_009_moteur_local_asc_dbc_pwa_local_first`, `req_010_pwa_statique_deployable_local_first`, `req_011_migrer_ui_produit_pwa_local_first_parite_mvp`, `req_012_rattraper_commits_ui_diagnostic_18_19_juillet_pwa`
- Backlog item(s): `item_017_passer_cantracediag_en_pwa_spa_local_first`, `item_018_spike_navigateur_500_mo_pour_pwa_local_first`, `item_019_moteur_local_asc_dbc_pour_pwa_local_first`, `item_020_pwa_statique_deployable_local_first`, `item_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`, `item_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
- Task(s): `task_017_passer_cantracediag_en_pwa_spa_local_first`, `task_018_spike_navigateur_500_mo_pour_pwa_local_first`, `task_019_moteur_local_asc_dbc_pour_pwa_local_first`, `task_020_pwa_statique_deployable_local_first`, `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`, `task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`
- Current local-server architecture: `src/cantracediag/api.py`
- Current streaming ASC import: `src/cantracediag/pipeline.py`
- Current ASC scanner: `src/cantracediag/formats/asc.py`
- Current DuckDB-backed store: `src/cantracediag/store.py`

# AI Context
- Summary: Roadmap for migrating CanTraceDiag toward a static PWA/SPA
  local-first architecture on branch `feat/pwa-local-first`, gated first by a
  browser-side 500 MB ASC chunking spike.
- Keywords: roadmap, pwa, spa, local-first, asc, dbc, opfs, indexeddb,
  duckdb-wasm, worker, chunks, 500 mb
- Use when: Planning the PWA/local-first branch, splitting implementation
  slices, or deciding whether to continue after browser performance evidence.
- Skip when: Executing the current FastAPI local-server roadmap or deploying the
  existing backend architecture without browser-local storage.
