# PWA Local ASC/DBC Engine Spike

This directory implements roadmap milestones `0.2 - Moteur local ASC DBC`,
`0.3 - PWA statique deployable`, and the first implementation wave of
`0.4 - Migration UI produit et parite MVP`.

## Validate

```bash
node --test spikes/pwa-local-engine/tests/*.test.ts
node spikes/pwa-local-engine/build-browser.mjs
CTD_ENGINE_ROOT=spikes/pwa-local-engine/site node spikes/pwa-local-engine/browser-smoke.mjs
```

The build step writes browser-executable modules to `browser/` and the
deployable static PWA to `site/` by stripping TypeScript types with Node's
built-in `stripTypeScriptTypes`.

The deployable `site/` artifact now uses the current product UI from
`src/cantracediag/web/index.html`; the build replaces its FastAPI network
helpers with a browser-local adapter.

## Run The Minimal UI

```bash
python3 -m http.server 8770 --bind 127.0.0.1 --directory spikes/pwa-local-engine/site
```

Open:

```text
http://127.0.0.1:8770
```

Use `tests/fixtures/sample.asc` and `tests/fixtures/sample.dbc` to exercise the
no-backend import workflow.

## Current Scope

- ASC fixture parity.
- DBC fixture subset.
- Local query facade for the current API concepts.
- Columnar in-browser store for the milestone.
- Static PWA shell with manifest, service worker, and offline app-shell cache.
- Minimal browser-local workspace lifecycle: save, list, reopen, delete, purge,
  export, import, and quota error recovery.
- Product UI shell migration with local adapter for the MVP endpoint shapes
  exercised by the smoke test.

Full DBC parity, large durable indexes in OPFS/IndexedDB, cross-browser quota
policy, and migration of the production FastAPI UI remain intentionally
incomplete. See `product-mvp-inventory-2026-07-22.md` and
`product-migration-results-2026-07-22.md`.
