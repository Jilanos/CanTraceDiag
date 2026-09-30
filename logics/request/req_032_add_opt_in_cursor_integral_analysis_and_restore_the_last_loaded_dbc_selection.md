## req_032_add_opt_in_cursor_integral_analysis_and_restore_the_last_loaded_dbc_selection - Add opt-in cursor integral analysis and restore the last loaded DBC selection
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Optional signal analysis and repeat import usability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.
> Indicators reviewed: 2026-09-30 13:57:05

# AI Context
Keep optional analysis ephemeral, but persist import defaults. Full-resolution integral semantics and content-based DBC history are specified in the linked backlog slices; prioritize the deployed PWA while retaining server compatibility.

# Needs
- Let an operator explicitly calculate the time integral of one chosen numeric signal between cursors A and B.
- Keep integral analysis disabled and its result absent by default.
- Preselect the library DBCs chosen for the last successful load so the next load only requires choosing a new trace, while preserving manual selection.

# Context
- The shared plot UI already combines cursor values and range statistics; integral computation is not implemented.
- The current canvas plots use sample-and-hold steps; the chosen trapezoidal analysis method must be made explicit to avoid confusing a numerical estimate with the drawn step area.
- The shared import UI currently preselects library entries by last-session display names and retries defaulting whenever the selected set is empty.
- The local product backend stores the DBC library persistently but keeps lastSessionDbcs only in memory, so browser reload loses the previous chosen set.
- The server workspace manifest already records DBC digests; its library endpoint currently exposes last_session as basenames.
- The deployed product is the local PWA; server UI compatibility remains supported. Existing PWA relocation work may move referenced modules: implement in their current canonical locations without duplicating the engine.

# Acceptance criteria
- AC1: Integral mode is off on initial load and on each new trace; no integral result, placeholder column, or integral-specific computation/request appears until explicit activation for a chosen signal. A compact accessible opt-in action remains discoverable.
- AC2: An operator can enable integral analysis for a selected numeric signal, move either cursor, switch the target signal, and disable analysis; missing cursors or unavailable data show a clear reason only while the mode is enabled. Cursor placement and other statistics keep working.
- AC3: Integral calculation follows the documented signed trapezoidal full-resolution contract, boundary interpolation, duplicate handling, unavailable cases, and unit semantics identically in the PWA and server engine.
- AC4: After a successful load and browser/application restart, the next import prechecks precisely the still-available library DBC content identities from that load, including uploaded and reused entries, and permits loading with only a new trace selected.
- AC5: Manual selection changes, including uncheck-all, survive picker reopen and refresh; same-name content, failed/cancelled/unresolved imports, absent history, library removal, legacy history, and purge behave according to the documented persistence contract.
- AC6: Automated numeric, persistence, and browser checks prove the new behavior in the local PWA and supported server UI, including zero integral work while disabled and unchanged existing cursor/import interactions.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_015_optional_cursor_integration_and_reusable_dbc_import_defaults`
- Architecture decision(s): (none yet)

# References
- src/cantracediag/web/js/plot.js
- src/cantracediag/web/js/core.js
- src/cantracediag/web/js/import.js
- src/cantracediag/web/js/main.js
- src/cantracediag/web/index.html
- src/cantracediag/api.py
- src/cantracediag/store.py
- src/cantracediag/workspace.py
- spikes/pwa-local-engine/src/store.ts
- spikes/pwa-local-engine/src/local-backend.ts
- spikes/pwa-local-engine/src/product-backend.ts
- spikes/pwa-local-engine/browser-smoke.mjs
- spikes/pwa-local-engine/tests/store.test.ts
- tests/test_workspace.py
- tests/test_e2e_ui.py

# Backlog
- `item_054_compute_exact_range_numeric_signal_integrals_in_local_and_server_stores`
- `item_055_expose_per_signal_cursor_integral_analysis_only_after_explicit_activation`
- `item_056_persist_and_preselect_the_exact_last_successful_dbc_load_set`
