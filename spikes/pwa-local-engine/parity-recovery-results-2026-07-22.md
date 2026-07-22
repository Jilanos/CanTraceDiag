# PWA Parity Recovery Results - 2026-07-22

Roadmap milestone: `0.4 - Migration UI produit et parite MVP`

Logics task:
`task_022_rattraper_les_commits_ui_diagnostic_du_18_19_juillet_dans_la_pwa`

Recovered source commits:

- `7a83002` - `feat(diagnostic): add report statistics and exports`.
- `84ac5c0` - `feat(ui): workspace views with split layout and unified measurements`.
- `57b9fb1` - `fix(web): cache-bust static assets so a fresh shell never loads stale JS`.

Implemented in the PWA path:

- The static PWA build now consumes the modular product UI:
  `core.js`, `import.js`, `signals.js`, `plot.js`, `report.js`, `trace.js`,
  `inspector.js` and `main.js`.
- `build-browser.mjs` generates one `product-app.mjs` module by concatenating
  the product modules in browser order and replacing network helpers with the
  local adapter.
- The static PWA artifact keeps product workspace views:
  `Plots`, `Plots + trace`, `Trace` and `Report`.
- The unified cursor measurement panel now works in the PWA and includes
  cursor A/B values plus range analysis A-B.
- `LocalPwaBackend` now exposes local equivalents for:
  - `/api/cursors`
  - `/api/signal-stats`
  - `/api/report`
  - export CSV long
  - export CSV wide
- The local stats path supports numeric range metrics:
  `count`, `min`, `max`, `mean`, `std`, `rms`.
- Text/enum-style stats return an ordered distribution payload.
- The static export dialog no longer performs `fetch("/api/export")`; it builds
  a local `Blob` from the browser-local backend and downloads it directly.
- The service worker shell cache now includes the product CSS.

Parquet:

- Parquet is explicitly deferred in the static browser PWA.
- Reason: the Python implementation uses `pyarrow`; browser support would need
  a separate Parquet/WASM writer and packaging/performance validation.
- CSV long and CSV wide are implemented locally.

Validation:

```bash
node spikes/pwa-local-engine/build-browser.mjs
node --test spikes/pwa-local-engine/tests/*.test.ts
CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9891 CTD_ENGINE_DEBUG_PORT=9241 node spikes/pwa-local-engine/browser-smoke.mjs
```

Observed smoke coverage:

- Fixture import from the static product PWA.
- Signal selection and plot rendering.
- Workspace view `Plots + trace` shows plot and trace together.
- Unified measurement table shows `Range analysis A-B`, `mean` and `rms`.
- Report view renders the diagnostic summary.
- CSV wide export from the static PWA completes without an export error.
- Manifest loads and service worker reaches active state.
- App-shell cache exists.
- No window `fetch` or XHR request to `/api/...` was observed.

Python backend note:

- The commits also brought the Python report/export/cache-busting code and its
  tests into the branch.
- Targeted Python tests were attempted with `.venv/bin/python`, but existing
  tests are not yet token-aware for the newer `SecurityConfig` guard and fail
  on unauthorized mutating requests.
- This does not affect the static PWA validation above because the PWA bundle
  bypasses network fetches and uses `LocalPwaBackend`.

Remaining limits:

- Product import still uses `File.text()` in the product adapter; worker/chunk
  import from milestone 0.1 is still a separate follow-up.
- OPFS/IndexedDB large trace/index persistence is still not integrated into the
  product-shaped PWA path.
- DBC support remains the local subset from milestone 0.2.
- Parquet browser export remains deferred.
