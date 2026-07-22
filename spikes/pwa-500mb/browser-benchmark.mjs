import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const filePath = path.resolve(process.argv[2] || "");
const chunkMiB = Number(process.argv[3] || 8);
const chromePath = process.env.CHROME_PATH
  || "/home/paul/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome";
const port = Number(process.env.CTD_SPIKE_PORT || 9876);
const debuggingPort = Number(process.env.CTD_CHROME_DEBUG_PORT || 9223);
const root = path.resolve("spikes/pwa-500mb");

async function main() {
  if (!filePath || !fs.existsSync(filePath)) {
    console.error("Usage: node spikes/pwa-500mb/browser-benchmark.mjs <trace.asc> [chunkMiB]");
    process.exit(2);
  }
  if (!fs.existsSync(chromePath)) {
    console.error(`Chromium not found: ${chromePath}`);
    process.exit(2);
  }

  const server = await startStaticServer(root, port);
  const profileDir = path.resolve("tmp", `ctd-chrome-${Date.now()}`);
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
  if (!page) throw new Error("No debuggable Chromium page target found.");
  const cdp = await CdpClient.connect(page.webSocketDebuggerUrl);
  await cdp.call("Page.enable");
  await cdp.call("DOM.enable");
  await cdp.call("Runtime.enable");
  await cdp.call("Page.navigate", { url: `http://127.0.0.1:${port}/index.html` });
  await waitForLoad(cdp);

  const { root: documentRoot } = await cdp.call("DOM.getDocument", {});
  const { nodeId } = await cdp.call("DOM.querySelector", {
    nodeId: documentRoot.nodeId,
    selector: "#trace",
  });
  await cdp.call("DOM.setFileInputFiles", { nodeId, files: [filePath] });
  await cdp.call("Runtime.evaluate", {
    expression: `
      document.querySelector('#chunkSize').value = ${JSON.stringify(String(chunkMiB))};
      document.querySelector('#start').click();
    `,
  });

  const started = Date.now();
  let snapshot = null;
  while (Date.now() - started < 10 * 60 * 1000) {
    await delay(500);
    snapshot = await pageSnapshot(cdp);
    process.stderr.write(
      `progress=${(Number(snapshot.progress || 0) * 100).toFixed(1)}% `
      + `status=${snapshot.status}\r`,
    );
    if (snapshot.log.includes("Scan complete.") || snapshot.log.includes("Error:")) break;
  }
  process.stderr.write("\n");

  const memory = await cdp.call("Runtime.evaluate", {
    expression: `performance.memory ? {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
    } : null`,
    returnByValue: true,
  });

  console.log(JSON.stringify({
    filePath,
    fileMiB: fs.statSync(filePath).size / 1024 / 1024,
    chunkMiB,
    chromePath,
    snapshot,
    memory: memory.result.value,
  }, null, 2));
  await cdp.close();
  } finally {
    chrome.kill("SIGTERM");
    server.close();
  }
}

async function pageSnapshot(cdp) {
  const result = await cdp.call("Runtime.evaluate", {
    expression: `({
      status: document.querySelector('#status').textContent,
      progress: document.querySelector('#progress').value,
      metrics: document.querySelector('#metrics').textContent,
      log: document.querySelector('#log').textContent,
      done: document.querySelector('#cancel').disabled
    })`,
    returnByValue: true,
  });
  return result.result.value;
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
      await fetchJson(`http://127.0.0.1:${debugPort}/json/version`);
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
    const state = await cdp.call("Runtime.evaluate", {
      expression: "document.readyState",
      returnByValue: true,
    });
    if (state.result.value === "complete") return;
    await delay(100);
  }
  throw new Error("Timed out waiting for page load.");
}

function contentType(file) {
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  if (file.endsWith(".css")) return "text/css; charset=utf-8";
  if (file.endsWith(".mjs") || file.endsWith(".js")) return "text/javascript; charset=utf-8";
  return "application/octet-stream";
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
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
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
    const payload = JSON.stringify({ id, method, params });
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(payload);
    });
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
