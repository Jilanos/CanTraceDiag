# Product MVP Inventory - 2026-07-22

Scope: `task_021_migrer_l_ui_produit_vers_la_pwa_local_first_avec_parite_mvp`

This inventory separates the current product MVP surface from the earlier
technical spike UI.

## Must-Have For MVP Parity

- Product visual shell from `src/cantracediag/web/index.html`: must-have.
  Current PWA status: migrated into the static build.
- Trace file picker and DBC file picker: must-have.
  Current PWA status: migrated through the existing UI controls.
- DBC folder picker: must-have for desktop Chromium parity.
  Current PWA status: UI preserved; broad folder parity still needs smoke
  coverage beyond single-file fixture import.
- DBC library dialog: must-have.
  Current PWA status: local browser DBC library implemented for uploaded DBCs.
- Import progress and cancellation controls: must-have.
  Current PWA status: progress path works for local synchronous fixture import;
  real worker-backed cancellation remains open.
- DBC conflict resolution: must-have.
  Current PWA status: local backend exposes conflict payload and resolution
  endpoint shape; browser smoke for conflict resolution remains open.
- Status summary and LED: must-have.
  Current PWA status: migrated and smoke-tested.
- Signal explorer, favorites, filtering and selection: must-have.
  Current PWA status: migrated and smoke-tested for `EngineSpeed`.
- Canvas plot, fit/zoom/pan/grid/cursors: must-have.
  Current PWA status: migrated and smoke-tested at smoke level only.
- Cursor readout: must-have.
  Current PWA status: local cursor endpoint is implemented; deeper smoke remains
  open.
- Trace table, filters, columns and pagination: must-have.
  Current PWA status: table/pagination smoke-tested; full filter matrix remains
  open.
- Trace locate from cursor: must-have.
  Current PWA status: local endpoint shape implemented; deeper smoke remains
  open.
- Inspector and frame signals: must-have.
  Current PWA status: local endpoint implemented; deeper smoke remains open.
- Workspace purge: must-have.
  Current PWA status: local DBC library and active analysis purge implemented.
- Export: must-have if kept in MVP.
  Current PWA status: not yet represented in the product UI migration.

## Deferred Or Not Yet Product-Ready

- Durable large trace/index persistence in OPFS or IndexedDB.
- Worker-backed chunk parsing integrated into the product import path.
- 500 MiB product-path import smoke after semantic indexing.
- Full DBC parity with Python `cantools`.
- Cross-browser validation beyond local Chromium.
- Migration of existing FastAPI workspaces to browser-local workspaces.

## Obsolete For Static PWA Path

- Uploading files to a Python server via XHR.
- Server-side DuckDB as the required default runtime for the static PWA path.
- Localhost FastAPI requirement for the hosted PWA MVP path.
