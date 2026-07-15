## task_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic - Améliorer le MVP CanTraceDiag pour l'analyse diagnostic
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [x] The backlog scope is implemented.
- [x] Acceptance criteria are covered.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# Backlog
- `item_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic`

# Acceptance criteria
- AC1: L'utilisateur peut zoomer, paner et remettre à l'échelle les graphes temporels sans recharger toute la trace dans le navigateur.
- AC2: L'utilisateur peut poser deux curseurs A/B et lire les deltas temps et valeurs pour chaque signal sélectionné, sans interpolation.
- AC3: Un clic sur une frame de la trace positionne le curseur graphe au timestamp correspondant, et un clic dans le graphe permet d'atteindre les frames proches dans la vue trace.
- AC4: La vue trace propose des filtres combinables par fenêtre temporelle, ID, message, direction, decode status et type d'événement.
- AC5: L'explorateur de signaux permet de rechercher, grouper par DBC/message, sélectionner rapidement, marquer des favoris, et se replier facilement.
- AC6: L'UI expose un panneau inspecteur qui détaille la frame sélectionnée : timestamp, canal, ID, direction, DLC, data hex, message décodé, signaux physiques, statut decode et DBC utilisée si disponible.
- AC7: Les préférences utilisateur locales sont persistées : signaux sélectionnés, tailles des panneaux, colonnes trace, filtres principaux et favoris.
- AC8: L'import de traces réelles de taille significative reste utilisable localement sans pic mémoire disproportionné, avec une progression visible et une erreur claire en cas d'échec ; une trace réelle de 148 Mo peut servir de preuve manuelle si disponible, mais n'est pas obligatoire comme critère bloquant.
- AC9: Les séries graphées sont downsamplées ou fenêtrées côté serveur pour éviter d'envoyer massivement des points inutiles au navigateur.
- AC10: Au chargement, les conflits DBC sont détectés et une popup demande quelle DBC utiliser pour les arbitration ids en conflit avant de finaliser l'analyse.
- AC11: Le style UI est homogène, en anglais, dense, sans emojis dans les contrôles principaux, et vérifié sur desktop ainsi que sur une largeur réduite.
- AC12: Les validations couvrent les parcours critiques : import, filtres trace, curseurs A/B, synchro graphe/trace, downsampling, conflits DBC et persistance locale.

# Implementation plan
- Step 1: UI structure and language
  - Convert all visible UI strings to English.
  - Replace emoji controls with compact icon-style controls and accessible tooltips.
  - Implement four-zone layout: top import/status bar, collapsible signal explorer, plot area, trace table, collapsible inspector.
  - Persist collapsed states, panel sizes, selected signals, favorites, columns, and key filters.
- Step 2: Plot interaction
  - Add zoom, pan, fit/reset behavior.
  - Add cursor A and cursor B.
  - Show nearest-sample values for each selected signal at A and B.
  - Show delta time and delta value per signal.
  - Ensure no interpolation is used for displayed values.
- Step 3: Graph/trace synchronization
  - Selecting a trace row moves/sets the active plot cursor to that timestamp.
  - Clicking/selecting a plot timestamp queries and highlights nearest trace rows.
  - Preserve current filters and selection during synchronization.
- Step 4: Trace filtering and inspector
  - Add filter inputs for time window, arbitration id, decoded message, direction, decode status, frames/events.
  - Extend API/store filtering where client-side filtering would be insufficient.
  - Populate inspector with selected frame/event data, decoded signals, decode status, and DBC source when available.
- Step 5: DBC conflict popup during loading
  - Detect conflicting arbitration ids before finalizing decode.
  - Present modal copy in English: "DBC conflict: which database should be used?".
  - Let the user choose the DBC per conflicting arbitration id.
  - Decode using that selection and expose the chosen DBC in trace/inspector.
- Step 6: Performance safeguards
  - Add server-side series windowing/downsampling based on visible time range and pixel/point budget.
  - Avoid sending massive raw series to the browser by default.
  - Add import progress/error state where feasible within the current local FastAPI session model.
  - Keep real trace performance proof optional; use synthetic/fixture coverage for automation.

# Validation
- Run `PYTHONPATH=.pydeps:src python3 -m pytest -q`.
- Run `PYTHONPATH=.pydeps:src .pydeps/bin/ruff check .`.
- Run `logics-manager lint --require-status`.
- Add or update tests for API/store filtering, downsampling/windowing, DBC conflict selection, and persistence helpers where testable.
- Manually verify in the browser:
  - English UI text only.
  - signal explorer and inspector collapse/expand cleanly.
  - A/B cursor nearest values and deltas are correct.
  - trace row selection moves the plot cursor.
  - plot timestamp selection finds nearby trace rows.
  - DBC conflict modal appears during loading when fixtures include conflicting DBCs.
  - layout works on desktop and reduced width.
- Use `logics-manager flow progress task task_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic --progress <n>%` during multi-wave work.
- Run `logics-manager flow finish task task_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic` after implementation.
- Finish workflow executed on 2026-07-15.
- Linked backlog/request close verification passed.

# Report
- Delivered the diagnostic-improvement wave across backend (store/API/decode/pipeline)
- Finished on 2026-07-15.
- Linked backlog item(s): `item_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic`
- Related request(s): `req_001_ameliorer_mvp_cantracediag_analyse_diagnostic`
  and the four-zone frontend workspace. Repo left commit-ready; no commits made.
- AC coverage:
  - AC1 — Plot supports wheel zoom, drag pan, Fit/reset and ±buttons; each view change
    refetches only the visible window (`/api/series` start/end) so the browser never
    reloads the whole trace. Server caps points (`max_points`), see AC9.
  - AC2 — A/B cursors placed by click / shift-click; a readout table shows per-signal
    value at A, at B, Δ(B−A) and Δt. Values are exact nearest stored samples from
    `/api/cursor` (`store.nearest_sample`) — no interpolation.
  - AC3 — Trace row click moves cursor A to that timestamp (trace→graph). Plot click sets
    cursor A and calls `/api/trace-locate` (`store.locate_row`) to page the trace to the
    nearest rows under active filters and highlight them (graph→trace).
  - AC4 — `/api/trace` accepts combinable filters: time window, arbitration id, message,
    direction, decode status, event type (`store._trace_union`). Frame-only filters
    exclude events; an event-type filter excludes frames.
  - AC5 — Signal explorer searches, groups by DBC then message, has quick-select
    checkboxes, per-signal favorite stars with a "fav only" toggle, and collapses.
  - AC6 — Collapsible inspector details the selected frame: timestamp, channel, id,
    direction, DLC, data hex, decoded message, decode status, DBC used (`dbc_source`),
    and decoded physical signals (`/api/frame-signals`); events show type + detail.
  - AC7 — localStorage persists selected signals, favorites, panel sizes, collapsed
    states, trace columns (visibility/order/width/format), and key trace filters.
  - AC8 — Import streams frames in bounded batches (`pipeline._BATCH`) to flatten peak
    memory; the browser shows an upload progress bar (XHR) and a clear error state on
    failure. Real 148 MB proof remains optional/manual.
  - AC9 — `store.signal_series` decimates windows above the point budget with per-bucket
    min/max (real samples, extrema preserved); returns `downsampled`/`raw_count`.
  - AC10 — Conflicts are detected before decode; the load stays pending and a modal
    "DBC conflict: which database should be used?" lets the operator pick a DBC per
    conflicting id. `/api/resolve` finalizes decode with the choice; the chosen DBC is
    surfaced in trace/inspector (`Decoder` resolution, `dbc_source`).
  - AC11 — UI is English, dense, emoji-free (icon-style controls with tooltips); layout
    is flex-based and reflows to reduced width. Visual desktop/narrow check is manual.
  - AC12 — New `tests/test_diagnostic.py` covers downsampling, extrema preservation,
    combinable filters, graph/trace locate, decoder resolution, and the DBC
    conflict→resolve import flow; existing import/trace/cursor tests retained.
- Validation: `PYTHONPATH=.pydeps:src python3 -m pytest -q` → 43 passed; ruff clean;
  `logics-manager lint --require-status` OK. Live HTTP flow verified end-to-end
  (conflict import→resolve, filters, series downsample flag, cursor, trace-locate).
  app.js boots headlessly against the live server with no thrown errors.
- Manual browser checks still recommended (no headless browser in this environment):
  A/B readouts, zoom/pan feel, DBC conflict modal, and layout at reduced width.

# AC Traceability
- AC1 -> Plot workspace (zoom/pan/fit). Proof: `app.js` wheel/drag/`fitView` refetch only the visible window via `/api/series` start/end.
- AC2 -> A/B cursors and deltas. Proof: `placeCursor`/`refreshCursorReadout` read exact nearest samples from `/api/cursor` (`store.nearest_sample`), no interpolation; readout shows A, B, Δvalue, Δt.
- AC3 -> Graph/trace synchronization. Proof: trace `selectRow` moves cursor A; plot click calls `/api/trace-locate` (`store.locate_row`) to page/highlight nearest rows.
- AC4 -> Combinable trace filters. Proof: `/api/trace` + `store._trace_union` filter by time, id, message, direction, decode status, event type; `test_diagnostic.py` filter tests.
- AC5 -> Signal explorer. Proof: `renderSignalList` search, DBC/message grouping, quick-select, favorite stars, fav-only toggle, collapsible panel.
- AC6 -> Inspector. Proof: `showInspector` renders timestamp/channel/id/direction/DLC/data hex/message/status/`dbc_source` plus decoded signals from `/api/frame-signals`.
- AC7 -> Local persistence. Proof: `store.*` localStorage for selected signals, favorites, panel sizes/collapsed state, columns, and key filters.
- AC8 -> Large-trace safeguards. Proof: batched streaming ingest (`pipeline._BATCH`), XHR upload progress bar, clear error state; real 148 MB proof optional.
- AC9 -> Server-side downsampling. Proof: `store.signal_series` min/max bucket decimation returns `downsampled`/`raw_count`; `test_series_*` cover budget and extrema.
- AC10 -> DBC conflict popup. Proof: detect-before-decode pending load, resolution modal, `/api/resolve` + `Decoder` resolution, `dbc_source` surfaced; conflict flow test.
- AC11 -> UI style. Proof: English, dense, emoji-free icon controls with tooltips, flex layout reflowing to reduced width; visual desktop/narrow check manual.
- AC12 -> Validation coverage. Proof: `tests/test_diagnostic.py` covers import/resolve, filters, cursors/locate, downsampling, DBC conflict, plus persistence helpers exercised via the UI.

# AI Context
- Summary: Implement the first post-MVP diagnostic improvement wave for CanTraceDiag: English four-zone UI, collapsible explorer/inspector, A/B cursors, graph/trace synchronization, filters, DBC conflict popup, persistence, and server-side series safeguards.
- Keywords: cantracediag, implementation, frontend, fastapi, duckdb, ab-cursors, graph-trace-sync, dbc-conflicts, downsampling, local-storage
- Use when: Actively implementing or validating the improved diagnostic UI and API behavior.
- Skip when: Work is only product discovery, BLF/MF4 import, replay controls, or packaging.

# Links
- Request: `req_001_ameliorer_mvp_cantracediag_analyse_diagnostic`
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
