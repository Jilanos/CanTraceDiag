const fileInput = document.querySelector("#trace");
const chunkInput = document.querySelector("#chunkSize");
const startBtn = document.querySelector("#start");
const cancelBtn = document.querySelector("#cancel");
const statusEl = document.querySelector("#status");
const progressEl = document.querySelector("#progress");
const metricsEl = document.querySelector("#metrics");
const logEl = document.querySelector("#log");

let worker = null;

startBtn.addEventListener("click", () => {
  const file = fileInput.files?.[0];
  if (!file) {
    setStatus("Choose an ASC file first.");
    return;
  }
  const chunkMiB = Number(chunkInput.value || 8);
  const chunkSize = Math.max(1, Math.min(chunkMiB, 64)) * 1024 * 1024;
  startScan(file, chunkSize);
});

cancelBtn.addEventListener("click", () => {
  worker?.postMessage({ type: "cancel" });
  setStatus("Cancelling...");
});

function startScan(file, chunkSize) {
  stopWorker();
  worker = new Worker(new URL("./asc-worker.mjs", import.meta.url), { type: "module" });
  progressEl.value = 0;
  metricsEl.textContent = "";
  logEl.textContent = "";
  startBtn.disabled = true;
  cancelBtn.disabled = false;
  setStatus(`Scanning ${file.name} (${formatBytes(file.size)}) with ${formatBytes(chunkSize)} chunks.`);

  worker.onmessage = (event) => {
    const { type, payload, error } = event.data || {};
    if (type === "progress") {
      renderProgress(payload);
      return;
    }
    if (type === "done") {
      renderProgress({ ...payload, size: file.size, percent: payload.offset / file.size });
      const message = payload.cancelled ? "Scan cancelled." : "Scan complete.";
      setStatus(`${message} ${file.name} (${formatBytes(file.size)}).`);
      appendLog(message);
      finish();
      return;
    }
    if (type === "error") {
      appendLog(`Error: ${error}`);
      finish();
    }
  };

  worker.onerror = (event) => {
    appendLog(`Worker error: ${event.message}`);
    finish();
  };

  worker.postMessage({ type: "scan", file, chunkSize });
}

function renderProgress(payload) {
  const percent = Math.max(0, Math.min(1, payload.percent ?? 0));
  progressEl.value = percent;
  metricsEl.textContent = [
    `Read: ${formatBytes(payload.offset)} / ${formatBytes(payload.size ?? payload.offset)}`,
    `Progress: ${(percent * 100).toFixed(1)}%`,
    `Chunks: ${payload.chunks}`,
    `Lines: ${payload.lines.toLocaleString()}`,
    `Frames: ${payload.frames.toLocaleString()}`,
    `Events: ${payload.events.toLocaleString()}`,
    `Throughput: ${payload.throughputMBps.toFixed(1)} MiB/s`,
    `Elapsed: ${(payload.elapsedMs / 1000).toFixed(2)} s`,
    `Time range: ${formatMaybeNumber(payload.firstTimestamp)} .. ${formatMaybeNumber(payload.lastTimestamp)} s`,
  ].join("\n");
}

function finish() {
  startBtn.disabled = false;
  cancelBtn.disabled = true;
  stopWorker();
}

function stopWorker() {
  if (worker) worker.terminate();
  worker = null;
}

function setStatus(message) {
  statusEl.textContent = message;
}

function appendLog(message) {
  logEl.textContent += `${new Date().toISOString()} ${message}\n`;
}

function formatBytes(bytes) {
  const units = ["B", "KiB", "MiB", "GiB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function formatMaybeNumber(value) {
  return typeof value === "number" ? value.toFixed(6) : "-";
}
