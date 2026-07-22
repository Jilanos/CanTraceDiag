import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const chromePath = process.env.CHROME_PATH
  || "/home/paul/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome";
const port = Number(process.env.CTD_ENGINE_PORT || 9880);
const debuggingPort = Number(process.env.CTD_ENGINE_DEBUG_PORT || 9230);
const root = path.resolve(process.env.CTD_ENGINE_ROOT || "spikes/pwa-local-engine");
const tracePath = path.resolve("tests/fixtures/sample.asc");
const dbcPath = path.resolve("tests/fixtures/sample.dbc");

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
    if (!value.pageInfo.includes("of 8")) throw new Error(`Trace pagination missing expected total: ${value.pageInfo}`);
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

    console.log(JSON.stringify({ ok: true, root, tracePath, dbcPath, snapshot: value, plotState, workspace: workspaceValue, pwa: pwaValue, apiCalls }, null, 2));
    await cdp.close();
  } finally {
    chrome.kill("SIGTERM");
    server.close();
  }
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
