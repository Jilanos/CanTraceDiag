# Static PWA BLF capability decision — 2026-08-28

Context: `req_031` / `item_053` / `task_046`. The server-backed product now
imports Vector BLF. The static browser PWA ships the same HTML shell, so its
BLF boundary had to be decided rather than inherited.

## Decision

**The static PWA does not import BLF.** It rejects `.blf` explicitly, before the
file is read, and points the operator at the server-backed app. ASC and text TRC
support is unchanged.

## Why not a bundled binary reader

The alternative in scope was a reviewable BLF reader bundled into the static
site. Two constraints ruled it out for this delivery:

- **Memory.** The browser-local engine has no DuckDB to spill to. It reads a
  trace fully into a JS string and keeps every frame and event in
  `LocalTraceStore` arrays. BLF is a zlib container, so a local import would add
  the decompressed object stream on top of the frames it produces — the peak
  would be worse than the ASC path that already sets the PWA's practical file
  size ceiling.
- **Bundle surface.** A BLF reader means the LOGG header, `LOBJ` object walking,
  per-container inflate, and the classic-CAN object structs — a binary parser
  reviewed and maintained in a second language, for the format most likely to
  arrive corrupt. The Python adapter concentrates that risk in one place behind
  `python-can`; duplicating it in the bundle doubles it.

Neither is permanent. If the PWA gains a spillable store, this decision is worth
revisiting; the boundary is one exported function, so reversing it is local.

## How the decision is enforced

It is enforced in two places, because the first one is advisory:

| Layer | Mechanism | Test |
| --- | --- | --- |
| Picker | `build-browser.mjs` rewrites the shared shell's `accept` and button title to drop BLF, and fails the build if the source shell stops matching | `product-bundle.test.ts` — "does not offer BLF in the static picker the bundle cannot read" |
| Runtime | `localTraceRejection()` in `src/local-backend.ts`, called by `product-backend.ts` before the file is read | `local-backend.test.ts` — "Browser-local BLF capability boundary" |

The picker's `accept` filter is a hint: an operator can pick "All files". The
runtime check is what actually holds, and it runs before `File.text()` so a
binary container is never decoded as UTF-8.

## What stays true

- The static PWA still imports ASC and text TRC locally, asserted by the same
  test block.
- The server-backed app imports BLF, including through the browser upload path,
  so no recording is unreachable — only the offline bundle is narrower.

## Addendum 2026-10-01 — MF4 import and raw ASC export

Context: `req_033` / `item_059` / `task_048`. The server-backed product now
imports raw-CAN MDF4 (`.mf4`) and saves any loaded trace's raw frames as ASC.
Both stay server-only, for the same reasons as BLF plus one more:

- **MF4** is a binary container like BLF, and recovering an *unfinalized*
  recording relies on finalizing a disposable on-disk copy, which the
  browser-local engine has no place for.
- **Raw ASC export** reads the server store's `frames` table in
  `(timestamp_s, seq)` order from a sibling DuckDB cursor; the local engine has
  no equivalent bounded iterator, and offering the option only to fail would be
  misleading.

| Layer | Mechanism | Test |
| --- | --- | --- |
| Shell | `build-browser.mjs` drops `.mf4` from the picker and removes the `asc_raw` export option (guarded by `replaceOnce`) | `product-bundle.test.ts` — "does not offer BLF or MF4 …", "does not offer the server-only raw ASC export …" |
| Capabilities | server `/api/status` advertises `capabilities`; the local backend advertises none, so the shared UI withdraws raw ASC | `local-backend.test.ts` — "advertises no server capability and refuses raw ASC export" |
| Runtime | `localTraceRejection()` refuses `.mf4` before reading, naming server mode; the local backend rejects `/api/export-asc` explicitly | `local-backend.test.ts` — "rejects an MF4 selection before reading the file" |
