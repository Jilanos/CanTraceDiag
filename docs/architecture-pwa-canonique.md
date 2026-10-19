# Architecture PWA canonique

CanTraceDiag has two supported execution modes, but one production product:

- the static PWA generated from `spikes/pwa-local-engine/` is the canonical
  production artifact and the only artifact published by the Docker image;
- the Python/FastAPI application remains the local desktop and API reference
  implementation for development, diagnostics, and compatibility tests.

The PWA local adapter is the production transport boundary. It owns trace and
DBC import, decoding, workspace persistence, filtering, statistics, reports,
and exports in the browser. It must not silently call the FastAPI service.

Changes to the product must be validated against the PWA path with Node 22:

```bash
npx -y node@22 --experimental-strip-types --test spikes/pwa-local-engine/tests/*.test.ts
npx -y node@22 spikes/pwa-local-engine/build-browser.mjs
```

The PWA test suite covers real ASC/DBC data, malformed input, DBC conflicts,
empty or unknown results, quota errors, workspace lifecycle, and bounded
large-trace operations. The FastAPI suite remains a compatibility suite and is
not evidence that the deployed static artifact works.

The directory name `spikes/` is retained for repository compatibility during
the migration. New production code must be added behind the PWA modules and
the generated site is the release source of truth.

## Windows local delivery (standalone executable)

The Python/FastAPI application is also delivered, unchanged in behaviour, as a
portable Windows x64 executable for operators whose traces exceed what the
browser engine can hold (ASC up to an inclusive 1 GiB). It is a separate
delivery path, not a replacement of the canonical web artifact:

- the hosted static PWA and its Docker image are built, validated and deployed
  exactly as before; nothing routes the PWA to a server;
- the executable runs the FastAPI service on loopback and serves the local UI
  (`src/cantracediag/web/`) to the operator's own browser;
- it is fetched by `CanTraceDiag.cmd` from the GitHub release that matches the
  checkout, verified by SHA-256 and provenance, and never committed to Git;
- `.github/workflows/windows.yml` builds and smoke-tests that exact file on every
  push; the tag release publishes it without depending on the web deployment.

See [ADR 0008](adr/0008-livraison-windows-autonome.md) and the README section
"Windows Standalone".
