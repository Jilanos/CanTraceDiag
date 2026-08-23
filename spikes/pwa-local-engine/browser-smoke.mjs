import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const chromePath = resolveChromePath();
const port = Number(process.env.CTD_ENGINE_PORT || 9880);
const debuggingPort = Number(process.env.CTD_ENGINE_DEBUG_PORT || 9230);
// Default to the generated site: the delivered artifact is what CI and release
// validation must exercise, not the historical spike shell.
const root = path.resolve(process.env.CTD_ENGINE_ROOT || "spikes/pwa-local-engine/site");
const tracePath = path.resolve(process.env.CTD_ENGINE_TRACE || "tests/fixtures/sample.asc");
const dbcPath = path.resolve("tests/fixtures/sample.dbc");
const expectedTraceRows = Number(process.env.CTD_ENGINE_EXPECT_TRACE_ROWS || 8);
const expectedReportText = (process.env.CTD_ENGINE_EXPECT_REPORT_TEXT || "")
  .split("|")
  .filter(Boolean);

/* Chromium discovery must not depend on one developer's cache layout: CI
 * installs Playwright's Chromium, and a workstation may have any revision of
 * it or a distro browser. Honour CHROME_PATH first, then search in a stable
 * order so the same command works on a runner and locally. */
function resolveChromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const candidates = [];
  const playwrightRoots = [
    process.env.PLAYWRIGHT_BROWSERS_PATH,
    path.join(os.homedir(), ".cache", "ms-playwright"),
    "/ms-playwright",
  ].filter(Boolean);
  for (const browsersRoot of playwrightRoots) {
    if (!fs.existsSync(browsersRoot)) continue;
    const revisions = fs.readdirSync(browsersRoot)
      .filter((entry) => entry.startsWith("chromium-"))
      // Highest revision first: a stale one may predate the tested behavior.
      .sort((a, b) => Number(b.split("-")[1]) - Number(a.split("-")[1]));
    for (const revision of revisions) {
      for (const layout of ["chrome-linux64/chrome", "chrome-linux/chrome", "chrome-mac/Chromium.app/Contents/MacOS/Chromium"]) {
        candidates.push(path.join(browsersRoot, revision, layout));
      }
    }
  }
  candidates.push("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser");
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) {
    throw new Error(`Chromium not found. Set CHROME_PATH or install Playwright Chromium. Looked at:\n${candidates.join("\n")}`);
  }
  return found;
}

async function main() {
  if (!fs.existsSync(chromePath)) throw new Error(`Chromium not found: ${chromePath}`);
  const server = await startStaticServer(root, port);
  const profileDir = path.resolve("tmp", `ctd-engine-chrome-${Date.now()}`);
  fs.mkdirSync(profileDir, { recursive: true });
  const chrome = spawn(chromePath, [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    `--user-data-dir=${profileDir}`,
    `--remote-debugging-port=${debuggingPort}`,
    `http://127.0.0.1:${port}/index.html`,
  ], { stdio: ["ignore", "ignore", "pipe"] });

  chrome.stderr.on("data", (chunk) => {
    const text = String(chunk);
    if (!text.includes("DevTools listening")) process.stderr.write(text);
  });

  try {
    await waitForDebug(debuggingPort);
    const targets = await fetchJson(`http://127.0.0.1:${debuggingPort}/json/list`);
    const page = targets.find((target) => target.type === "page" && target.webSocketDebuggerUrl);
    if (!page) throw new Error("No debuggable page target found.");
    const cdp = await CdpClient.connect(page.webSocketDebuggerUrl);
    await cdp.call("Page.enable");
    await cdp.call("DOM.enable");
    await cdp.call("Runtime.enable");
    const browserEvents = [];
    cdp.on("Runtime.exceptionThrown", (event) => browserEvents.push({ kind: "exception", event }));
    cdp.on("Runtime.consoleAPICalled", (event) => browserEvents.push({ kind: "console", event }));
    await cdp.call("Page.addScriptToEvaluateOnNewDocument", {
      source: `
        window.__ctdNetworkCalls = [];
        const originalFetch = window.fetch;
        window.fetch = function(input, init) {
          const url = typeof input === 'string' ? input : input && input.url;
          window.__ctdNetworkCalls.push({ kind: 'fetch', url: String(url || '') });
          return originalFetch.apply(this, arguments);
        };
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
          window.__ctdNetworkCalls.push({ kind: 'xhr', url: String(url || '') });
          return originalOpen.apply(this, arguments);
        };
      `,
    });
    await cdp.call("Page.navigate", { url: `http://127.0.0.1:${port}/index.html` });
    await waitForLoad(cdp);
    await waitForServiceWorker(cdp, browserEvents);

    const { root: documentRoot } = await cdp.call("DOM.getDocument", {});
    await setFile(cdp, documentRoot.nodeId, "#traceFile", tracePath);
    await setFile(cdp, documentRoot.nodeId, "#dbcFiles", dbcPath);
    await cdp.call("Runtime.evaluate", {
      expression: `
        document.querySelector('#traceFile').dispatchEvent(new Event('change', { bubbles: true }));
        document.querySelector('#dbcFiles').dispatchEvent(new Event('change', { bubbles: true }));
        document.querySelector('#loadBtn').click();
      `,
    });

    let snapshot = null;
    for (let i = 0; i < 80; i += 1) {
      await delay(100);
      snapshot = await cdp.call("Runtime.evaluate", {
        expression: `({
          summary: document.querySelector('#summary').textContent,
          signals: document.querySelector('#signalList').textContent,
          trace: document.querySelector('#traceTable').textContent,
          pageInfo: document.querySelector('#pageInfo').textContent,
          led: document.querySelector('#statusLedText').textContent
        })`,
        returnByValue: true,
      });
      const value = snapshot.result.value;
      if (value.summary.includes("6") && value.summary.includes("decoded") && value.signals.includes("EngineSpeed")) break;
    }
    const value = snapshot.result.value;
    if (!value.summary.includes("decoded")) throw new Error(`UI did not load trace: ${value.summary}`);
    if (!value.signals.includes("EngineSpeed")) throw new Error(`Signals missing EngineSpeed: ${value.signals}`);
    if (!value.trace.includes("EngineData")) throw new Error(`Trace missing EngineData: ${value.trace}`);
    if (!value.pageInfo.includes(`of ${expectedTraceRows}`)) throw new Error(`Trace pagination missing expected total: ${value.pageInfo}`);
    if (value.led !== "INDEXED") throw new Error(`Status LED did not switch to INDEXED: ${value.led}`);

    await cdp.call("Runtime.evaluate", {
      expression: `
        const rows = [...document.querySelectorAll('.sig')];
        const speed = rows.find((row) => row.textContent.includes('EngineSpeed'));
        if (speed) speed.querySelector('input').click();
      `,
    });
    const plotState = await waitForExpression(cdp, `({
      hint: document.querySelector('#plotHint').style.display,
      selected: document.querySelectorAll('.sig.on').length,
      measure: document.querySelector('#viewHint').textContent
    })`, (result) => result.selected > 0 && result.hint === "none");

    const explorer = await cdp.call("Runtime.evaluate", {
      expression: `(() => {
        const header = document.querySelector('.grp');
        const body = document.getElementById(header.getAttribute('aria-controls'));
        header.click();
        const collapsed = body.hidden && header.getAttribute('aria-expanded') === 'false';
        header.click();
        document.querySelector('#dispOnly').click();
        const shown = {
          checked: document.querySelector('#dispOnly').checked,
          rows: document.querySelectorAll('.sig').length,
          selected: document.querySelectorAll('.sig.on').length,
        };
        document.querySelector('#dispOnly').click();
        return { collapsed, ...shown };
      })()`,
      returnByValue: true,
    });
    const explorerValue = explorer.result.value;
    if (!explorerValue.collapsed) throw new Error(`DBC group did not collapse: ${JSON.stringify(explorerValue)}`);
    if (!explorerValue.checked || explorerValue.rows !== 1 || explorerValue.selected !== 1) {
      throw new Error(`Shown filter did not retain only the plotted signal: ${JSON.stringify(explorerValue)}`);
    }

    const workspace = await cdp.call("Runtime.evaluate", {
      expression: `
        window.__ctd.placeCursor(0, 'a', false);
        window.__ctd.placeCursor(0.02, 'b', false);
        Promise.resolve(window.__ctd.refreshCursorReadout()).then(() => {
          document.querySelector('#viewSplit').click();
          const split = {
            view: document.querySelector('#center').dataset.view,
            plotHidden: document.querySelector('#plotArea').hidden,
            traceHidden: document.querySelector('#traceWrap').hidden,
            readout: document.querySelector('#cursorReadout').textContent
          };
          document.querySelector('#viewReport').click();
          return new Promise((resolve) => setTimeout(resolve, 50)).then(() => {
            const report = document.querySelector('#reportBody').textContent;
            document.querySelector('#viewPlots').click();
            document.querySelector('#exportBtn').click();
            document.querySelector('#exportScope').value = 'between_ab';
            document.querySelector('#exportFormat').value = 'csv_wide';
            document.querySelector('#exportRun').click();
            return new Promise((resolve) => setTimeout(() => resolve({
              split,
              report,
              exportDialogOpen: document.querySelector('#exportDialog').open,
              exportError: document.querySelector('#exportError').hidden ? '' : document.querySelector('#exportError').textContent
            }), 50));
          });
        })`,
      awaitPromise: true,
      returnByValue: true,
    });
    const workspaceValue = workspace.result.value;
    if (workspaceValue.split.view !== "split") throw new Error(`Workspace split view did not activate: ${JSON.stringify(workspaceValue)}`);
    if (workspaceValue.split.plotHidden || workspaceValue.split.traceHidden) throw new Error(`Split view did not show plot + trace: ${JSON.stringify(workspaceValue)}`);
    if (!workspaceValue.split.readout.includes("Range analysis A–B")) throw new Error(`Unified measurement table missing range analysis: ${workspaceValue.split.readout}`);
    if (!workspaceValue.split.readout.toLowerCase().includes("mean") || !workspaceValue.split.readout.toLowerCase().includes("rms")) {
      throw new Error(`Measurement table missing mean/rms stats: ${workspaceValue.split.readout}`);
    }
    if (!workspaceValue.report.includes("6") || !workspaceValue.report.includes("decoded")) throw new Error(`Report view missing diagnostic summary: ${workspaceValue.report}`);
    for (const expected of expectedReportText) {
      if (!workspaceValue.report.includes(expected)) {
        throw new Error(`Report view missing expected text '${expected}': ${workspaceValue.report}`);
      }
    }
    if (workspaceValue.exportDialogOpen || workspaceValue.exportError) throw new Error(`CSV export did not complete cleanly: ${JSON.stringify(workspaceValue)}`);

    const pwa = await cdp.call("Runtime.evaluate", {
      expression: `Promise.all([
        fetch('./manifest.webmanifest').then((r) => r.json()),
        navigator.serviceWorker.ready.then((registration) => Boolean(registration.active)),
        caches.keys()
      ]).then(([manifest, serviceWorkerActive, cacheKeys]) => ({
        manifestName: manifest.name,
        display: manifest.display,
        iconSizes: manifest.icons.map((icon) => icon.sizes).sort(),
        serviceWorkerActive,
        shellCache: cacheKeys.find((key) => key.startsWith('cantracediag-pwa-shell-')) || null,
        quotaAvailable: Boolean(navigator.storage && navigator.storage.estimate)
      }))`,
      awaitPromise: true,
      returnByValue: true,
    });
    const pwaValue = pwa.result.value;
    if (pwaValue.manifestName !== "CanTraceDiag Local PWA") throw new Error("Manifest was not loaded.");
    if (pwaValue.display !== "standalone") throw new Error("Manifest display is not standalone.");
    if (!pwaValue.iconSizes.includes("192x192") || !pwaValue.iconSizes.includes("512x512")) {
      throw new Error(`Manifest PNG icons missing: ${JSON.stringify(pwaValue.iconSizes)}`);
    }
    if (!pwaValue.serviceWorkerActive) throw new Error("Service worker is not active.");
    if (!pwaValue.shellCache) throw new Error("App shell cache missing.");

    const fullscreen = await exerciseFullscreen(cdp);

    const network = await cdp.call("Runtime.evaluate", {
      expression: `window.__ctdNetworkCalls.filter((entry) => entry.url.includes('/api/'))`,
      returnByValue: true,
    });
    const apiCalls = network.result.value || [];
    if (apiCalls.length) throw new Error(`Static PWA made API network calls: ${JSON.stringify(apiCalls)}`);

    const libraryText = await cdp.call("Runtime.evaluate", {
      expression: `
        document.querySelector('#pickLibBtn').click();
        const text = document.querySelector('#libList').textContent;
        document.querySelector('#libDialog').close();
        text;
      `,
      returnByValue: true,
    });
    if (!String(libraryText.result.value).includes("sample.dbc")) throw new Error(`DBC library missing uploaded fixture: ${libraryText.result.value}`);

    console.log(JSON.stringify({ ok: true, root, chromePath, tracePath, dbcPath, snapshot: value, plotState, explorer: explorerValue, workspace: workspaceValue, pwa: pwaValue, fullscreen, apiCalls }, null, 2));
    await cdp.close();
  } finally {
    chrome.kill("SIGTERM");
    server.close();
    // Chromium can still be flushing its profile just after SIGTERM. Retry the
    // cleanup briefly so the smoke check never leaves an untracked `tmp/` tree.
    for (let attempt = 0; attempt < 5; attempt += 1) {
      try {
        fs.rmSync(profileDir, { recursive: true, force: true, maxRetries: 2, retryDelay: 50 });
        break;
      } catch (error) {
        if (attempt === 4) throw error;
        await delay(100);
      }
    }
  }
}

/* The delivered fullscreen control is the defect this smoke exists to catch:
 * a bundle that omits `fullscreen.js` leaves a visible button with no listener
 * and no console error. Headless Chromium may enter fullscreen or refuse it, so
 * assert on the contract instead of on one outcome: after a user-gesture click
 * the control must either be in fullscreen or show a refusal note, and
 * `aria-pressed` must mirror the native state either way. */
async function exerciseFullscreen(cdp) {
  const before = await evaluateValue(cdp, fullscreenStateExpression());
  if (!before.present) throw new Error("Fullscreen control is missing from the delivered site.");
  if (before.pressed !== "false") throw new Error(`Fullscreen control did not start unpressed: ${JSON.stringify(before)}`);

  await cdp.call("Runtime.evaluate", {
    expression: "document.querySelector('#fullscreenBtn').click()",
    userGesture: true,
    awaitPromise: false,
  });

  const after = await waitForExpression(
    cdp,
    fullscreenStateExpression(),
    (state) => state.fullscreen || Boolean(state.note),
  );
  if (after.pressed !== String(after.fullscreen)) {
    throw new Error(`Fullscreen aria-pressed did not follow the native state: ${JSON.stringify(after)}`);
  }

  let restored = after;
  if (after.fullscreen) {
    await cdp.call("Runtime.evaluate", {
      expression: "document.querySelector('#fullscreenBtn').click()",
      userGesture: true,
    });
    restored = await waitForExpression(cdp, fullscreenStateExpression(), (state) => !state.fullscreen);
    if (restored.pressed !== "false") throw new Error(`Fullscreen control stayed pressed after exit: ${JSON.stringify(restored)}`);
  }
  return { before, after, restored };
}

function fullscreenStateExpression() {
  return `(() => {
    const btn = document.querySelector('#fullscreenBtn');
    const note = document.querySelector('#fullscreenNote');
    return {
      present: Boolean(btn),
      pressed: btn ? btn.getAttribute('aria-pressed') : null,
      label: btn ? btn.getAttribute('aria-label') : null,
      fullscreen: Boolean(document.fullscreenElement),
      note: note && !note.hidden ? note.textContent.trim() : ''
    };
  })()`;
}

async function evaluateValue(cdp, expression) {
  const result = await cdp.call("Runtime.evaluate", { expression, returnByValue: true });
  return result.result.value;
}

async function setFile(cdp, rootNodeId, selector, filePath) {
  const { nodeId } = await cdp.call("DOM.querySelector", { nodeId: rootNodeId, selector });
  await cdp.call("DOM.setFileInputFiles", { nodeId, files: [filePath] });
}

async function waitForText(cdp, selector, expected) {
  for (let i = 0; i < 80; i += 1) {
    await delay(100);
    const result = await cdp.call("Runtime.evaluate", {
      expression: `document.querySelector(${JSON.stringify(selector)}).textContent`,
      returnByValue: true,
    });
    const text = result.result.value || "";
    if (text.includes(expected)) return text;
  }
  throw new Error(`Timed out waiting for ${expected} in ${selector}`);
}

async function waitForExpression(cdp, expression, predicate) {
  let value = null;
  for (let i = 0; i < 80; i += 1) {
    await delay(100);
    const result = await cdp.call("Runtime.evaluate", { expression, returnByValue: true });
    value = result.result.value;
    if (predicate(value)) return value;
  }
  throw new Error(`Timed out waiting for expression: ${JSON.stringify(value)}`);
}

function startStaticServer(directory, listenPort) {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://127.0.0.1:${listenPort}`);
    const requested = path.normalize(decodeURIComponent(url.pathname)).replace(/^(\.\.[/\\])+/, "");
    const file = path.join(directory, requested === "/" ? "index.html" : requested);
    if (!file.startsWith(directory) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404);
      res.end("not found");
      return;
    }
    res.writeHead(200, { "Content-Type": contentType(file) });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(listenPort, "127.0.0.1", () => resolve(server));
  });
}

async function waitForDebug(debugPort) {
  for (let i = 0; i < 100; i += 1) {
    try {
      await fetchJson(`http://127.0.0.1:${debugPort}/json/list`);
      return;
    } catch {
      await delay(100);
    }
  }
  throw new Error("Timed out waiting for Chromium debugging endpoint.");
}

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function waitForLoad(cdp) {
  for (let i = 0; i < 100; i += 1) {
    const state = await cdp.call("Runtime.evaluate", { expression: "document.readyState", returnByValue: true });
    if (state.result.value === "complete") return;
    await delay(100);
  }
  throw new Error("Timed out waiting for page load.");
}

function contentType(file) {
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  if (file.endsWith(".css")) return "text/css; charset=utf-8";
  if (file.endsWith(".mjs") || file.endsWith(".js") || file.endsWith(".ts")) return "text/javascript; charset=utf-8";
  if (file.endsWith(".webmanifest")) return "application/manifest+json; charset=utf-8";
  if (file.endsWith(".svg")) return "image/svg+xml";
  if (file.endsWith(".png")) return "image/png";
  return "application/octet-stream";
}

async function waitForServiceWorker(cdp, browserEvents = []) {
  for (let i = 0; i < 80; i += 1) {
    const result = await cdp.call("Runtime.evaluate", {
      expression: `Promise.race([
        navigator.serviceWorker.ready.then(() => true).catch(() => false),
        new Promise((resolve) => setTimeout(() => resolve(false), 100))
      ])`,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.result.value === true) return;
    await delay(100);
  }
  const state = await cdp.call("Runtime.evaluate", {
    expression: `Promise.all([
      navigator.serviceWorker.getRegistrations().then((regs) => regs.map((r) => ({
        scope: r.scope,
        active: Boolean(r.active),
        installing: Boolean(r.installing),
        waiting: Boolean(r.waiting)
      }))).catch((error) => ({ error: String(error) })),
      caches.keys().catch((error) => ({ error: String(error) }))
    ]).then(([registrations, cacheKeys]) => ({ registrations, cacheKeys }))`,
    awaitPromise: true,
    returnByValue: true,
  });
  throw new Error(`Timed out waiting for service worker: ${JSON.stringify({ state: state.result.value, browserEvents }, null, 2)}`);
}

class CdpClient {
  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });
    return new CdpClient(socket);
  }

  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.method) {
        for (const handler of this.listeners.get(message.method) || []) handler(message.params);
      }
      if (!message.id) return;
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message));
      else pending.resolve(message.result);
    });
  }

  call(method, params = {}) {
    const id = this.nextId;
    this.nextId += 1;
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }

  on(method, handler) {
    if (!this.listeners.has(method)) this.listeners.set(method, []);
    this.listeners.get(method).push(handler);
  }

  close() {
    this.socket.close();
    return Promise.resolve();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
