## task_002_ameliorer_le_mvp_cantracediag_pour_l_analyse_diagnostic - Améliorer le MVP CanTraceDiag pour l'analyse diagnostic
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Definition of Done (DoD)
- [ ] The backlog scope is implemented.
- [ ] Acceptance criteria are covered.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

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

# Report
- Not implemented yet. This task is ready for implementation.

# AI Context
- Summary: Implement the first post-MVP diagnostic improvement wave for CanTraceDiag: English four-zone UI, collapsible explorer/inspector, A/B cursors, graph/trace synchronization, filters, DBC conflict popup, persistence, and server-side series safeguards.
- Keywords: cantracediag, implementation, frontend, fastapi, duckdb, ab-cursors, graph-trace-sync, dbc-conflicts, downsampling, local-storage
- Use when: Actively implementing or validating the improved diagnostic UI and API behavior.
- Skip when: Work is only product discovery, BLF/MF4 import, replay controls, or packaging.

# Links
- Request: `req_001_ameliorer_mvp_cantracediag_analyse_diagnostic`
- Product brief(s): `prod_002_product_brief_cantracediag_mvp`
- Architecture decision(s): `adr_002_adr_architecture_cantracediag_mvp`
