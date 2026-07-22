# Static PWA Results - 2026-07-22

Roadmap milestone: `0.3 - PWA statique deployable`

This implementation packages the local ASC/DBC engine as a deployable static
PWA:

- Reproducible static build output in `spikes/pwa-local-engine/site/`.
- PWA manifest, SVG icon, service worker, and app-shell cache.
- Service worker caches only application shell files, not user ASC/DBC traces or
  workspace exports.
- Static UI workflow for local ASC + DBC import, status, signals, trace rows,
  first decoded series, and purge.
- Browser-local workspace lifecycle using origin storage: save, list, reopen,
  delete, purge, JSON export, and JSON import.
- Storage quota display plus simulated quota-exceeded unit coverage with a
  recovery message.
- Caddy/static hosting notes for `cantracediag.paulmondou.fr` in
  `spikes/pwa-local-engine/static-deploy.md`.

## Validation

Commands:

```bash
node spikes/pwa-local-engine/build-browser.mjs
node --test spikes/pwa-local-engine/tests/*.test.ts
CTD_ENGINE_ROOT=spikes/pwa-local-engine/site CTD_ENGINE_PORT=9883 CTD_ENGINE_DEBUG_PORT=9233 node spikes/pwa-local-engine/browser-smoke.mjs
```

Results:

- Static build: passed. `site/` contains HTML, CSS, manifest, service worker,
  icon asset, and browser modules.
- Unit/local tests: 9 passed, 0 failed.
- Browser smoke: passed from `spikes/pwa-local-engine/site/` without FastAPI.
- Smoke fixture output included:
  - `loaded: true`
  - 6 frames, 2 events, 5 decoded frames, 3 unique ids
  - signals including `EngineData.EngineSpeed`
  - trace rows including `EngineData`
  - first series values `[1024, 2048, 3072, 4096] rpm`
  - saved workspace `Smoke workspace` for `sample.asc`
  - manifest name `CanTraceDiag Local PWA`
  - manifest display mode `standalone`
  - active service worker
  - app-shell cache `cantracediag-pwa-shell-v1`
  - available `navigator.storage.estimate`

## Remaining Adoption Limits

- The DBC parser is still a fixture-focused subset, not `cantools` parity.
- Large durable indexes are not yet stored in OPFS/IndexedDB; the workspace
  proof stores fixture-sized trace text and DBC text in origin storage.
- 500 MiB scanning was validated in milestone 0.1, but the 0.3 workspace export
  path should not be treated as the final strategy for uncommon 500 MiB traces.
- Query/index performance still needs a product-scale benchmark after semantic
  indexing is moved to durable browser storage.
- Browser support has been validated with local Chromium only.
- The production FastAPI UI has not been migrated; this PWA remains an isolated
  spike until the adapter boundary and DBC coverage are promoted.
