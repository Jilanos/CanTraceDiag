# PWA 500 MB ASC Spike

This isolated spike supports roadmap milestone
`0.1 - Spike navigateur 500 Mo` for the `feat/pwa-local-first` branch.

It checks whether a browser-local workflow can scan large ASC files without a
backend and without materializing every frame as a retained JavaScript object.

## Browser Spike

Serve the directory from the repository root:

```bash
python3 -m http.server 8765 --directory spikes/pwa-500mb
```

Open:

```text
http://127.0.0.1:8765
```

Choose a local `.asc` file, keep the default 8 MiB chunk size, and start the
scan. The worker reports progress, throughput, frame/event counts, elapsed time,
and cancellation behavior.

## Synthetic Fixtures

Large synthetic ASC files are generated outside Git:

```bash
node spikes/pwa-500mb/generate-asc-fixture.mjs 50 tmp/ctd-50mib.asc
node spikes/pwa-500mb/generate-asc-fixture.mjs 150 tmp/ctd-150mib.asc
node spikes/pwa-500mb/generate-asc-fixture.mjs 500 tmp/ctd-500mib.asc
```

## Validation

Core boundary handling is covered with Node's built-in test runner:

```bash
node --test spikes/pwa-500mb/scanner-core.test.mjs
```

A local non-browser throughput check is available for quick comparisons:

```bash
node spikes/pwa-500mb/benchmark-node.mjs tmp/ctd-50mib.asc 8
```

Headless Chromium evidence can be collected through the Chrome DevTools Protocol
without adding a package dependency:

```bash
node spikes/pwa-500mb/browser-benchmark.mjs tmp/ctd-50mib.asc 8
CTD_SPIKE_PORT=9877 CTD_CHROME_DEBUG_PORT=9224 \
  node spikes/pwa-500mb/browser-benchmark.mjs tmp/ctd-500mib.asc 8
```

The script defaults to the Chromium binary cached under
`~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`. Override it with
`CHROME_PATH=/path/to/chrome` when needed.
