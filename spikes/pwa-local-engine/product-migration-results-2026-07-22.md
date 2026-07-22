# Product UI PWA Migration Results - 2026-07-22

Roadmap milestone: `0.4 - Migration UI produit et parite MVP`

Implemented in this wave:

- The deployable PWA build now uses the product UI from
  `src/cantracediag/web/index.html` instead of the minimal spike page.
- `product-app.mjs` is generated from the existing product `app.js` with the
  network helpers replaced by a local PWA adapter.
- `product-backend.ts` maps the existing MVP endpoint shapes to
  `LocalPwaBackend` in the browser.
- The static build no longer requires FastAPI for fixture import, status,
  signals, series, trace table, cursor, trace locate, frame signals, DBC library
  or purge paths exercised by the migrated UI.
- The old minimal `app.mjs` is excluded from the deployable `site/` artifact.
- Manifest, app icon and service worker target the product PWA shell.

Validation:

```bash
node spikes/pwa-local-engine/build-browser.mjs
node --test spikes/pwa-local-engine/tests/*.test.ts
CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9885 CTD_ENGINE_DEBUG_PORT=9235 node spikes/pwa-local-engine/browser-smoke.mjs
```

Observed smoke result:

- Product UI summary: `6 frames`, `5 decoded`, `2 events`, `3 ids`.
- Signal explorer includes `EngineData.EngineSpeed`.
- Trace table includes `EngineData` and reports `1-8 of 8`.
- Selecting `EngineSpeed` hides the plot placeholder and renders a selected
  signal.
- Status LED reaches `INDEXED`.
- Manifest name is `CanTraceDiag Local PWA`.
- Service worker is active and app-shell cache exists.
- No window `fetch` or XHR request to `/api/...` was observed during the static
  PWA smoke.

Not complete yet:

- The product import path still reads fixture files through `File.text()`; it
  has not yet integrated the 0.1 worker/chunk parser.
- Large trace/index persistence is not yet OPFS/IndexedDB-backed in the product
  path.
- The DBC parser remains the 0.2 subset.
- Conflict-resolution, filter-matrix, cursor-readout and inspector behavior need
  deeper browser smoke coverage.
- The July 18/19 parity recovery is documented in
  `spikes/pwa-local-engine/parity-recovery-results-2026-07-22.md`.
- Export CSV long/wide, unified measurements, report and workspace views are now
  covered in the static PWA recovery smoke; Parquet remains deferred for browser
  packaging reasons.
- The FastAPI code remains intentionally present as oracle/fallback.
