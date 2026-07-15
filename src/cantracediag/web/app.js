"use strict";
/* CanTraceDiag local UI: stacked signal plots + configurable trace view. */

const SERIES_COLORS = ["--s0","--s1","--s2","--s3","--s4","--s5","--s6","--s7"];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

const state = {
  signals: [],
  selected: [],        // {message, signal, unit, color, t:[], v:[]}
  trace: { offset: 0, limit: 200, total: 0 },
  cursorX: null,       // canvas x of crosshair
};

/* ---- column model for the trace view (AC7) ------------------------------ */
const DEFAULT_COLUMNS = [
  { key: "timestamp_s", label: "Time", visible: true, width: 110, format: "s" },
  { key: "channel",     label: "Ch",   visible: true, width: 44,  format: "text" },
  { key: "kind",        label: "Kind", visible: true, width: 60,  format: "text" },
  { key: "id_hex",      label: "ID",   visible: true, width: 90,  format: "text" },
  { key: "name",        label: "Name", visible: true, width: 160, format: "text" },
  { key: "direction",   label: "Dir",  visible: true, width: 44,  format: "text" },
  { key: "dlc",         label: "DLC",  visible: true, width: 44,  format: "text" },
  { key: "data_hex",    label: "Data", visible: true, width: 200, format: "text" },
  { key: "decode_status", label: "Status", visible: true, width: 100, format: "status" },
  { key: "detail",      label: "Detail", visible: true, width: 240, format: "text" },
];
function loadColumns() {
  try {
    const saved = JSON.parse(localStorage.getItem("ctd.columns"));
    if (Array.isArray(saved) && saved.length) return saved;
  } catch (_) {}
  return structuredClone(DEFAULT_COLUMNS);
}
let columns = loadColumns();
const saveColumns = () => localStorage.setItem("ctd.columns", JSON.stringify(columns));

/* ---- API helpers -------------------------------------------------------- */
async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

/* ---- import ------------------------------------------------------------- */
const $ = (id) => document.getElementById(id);

// Files chosen through the native picker, awaiting upload.
const picked = { trace: null, dbcs: [] };

function refreshPicked() {
  const parts = [];
  if (picked.trace) parts.push(`<b>${picked.trace.name}</b>`);
  if (picked.dbcs.length) parts.push(`${picked.dbcs.length} DBC`);
  $("picked").innerHTML = parts.join(" · ") || "no files selected";
  $("loadBtn").disabled = !picked.trace;
}

async function doLoad() {
  if (!picked.trace) return;
  const fd = new FormData();
  fd.append("trace", picked.trace, picked.trace.name);
  for (const f of picked.dbcs) fd.append("dbcs", f, f.name);

  $("loadBtn").disabled = true;
  $("summary").textContent = "Uploading & indexing…";
  try {
    const r = await api("/api/import-files", { method: "POST", body: fd });
    renderSummary(r);
    state.selected = [];
    await loadSignals();
    renderPlot();
    await loadTrace(0);
  } catch (e) {
    $("summary").innerHTML = `<span class="warn">${e.message}</span>`;
  } finally {
    $("loadBtn").disabled = !picked.trace;
  }
}

function renderSummary(r) {
  const s = r.summary;
  let html = `<b>${s.frames}</b> frames · <b>${s.decoded_frames}</b> decoded · ` +
    `<b>${s.events}</b> events · <b>${s.unique_ids}</b> ids · ` +
    `${fmtTime(s.start_s)}–${fmtTime(s.end_s)}`;
  const amb = Object.keys(r.ambiguous_ids || {});
  if (amb.length) {
    html += ` · <span class="warn">⚠ ${amb.length} ambiguous id(s): ` +
      amb.map((k) => `${k} (${r.ambiguous_ids[k].join(", ")})`).join("; ") + "</span>";
  }
  $("summary").innerHTML = html;
}

/* ---- signal catalog ----------------------------------------------------- */
async function loadSignals() {
  const r = await api("/api/signals");
  state.signals = r.signals;
  renderSignalList();
}

function renderSignalList() {
  const filter = $("filter").value.toLowerCase();
  const list = $("signalList");
  list.innerHTML = "";
  for (const sig of state.signals) {
    const key = `${sig.message_name}.${sig.signal_name}`;
    if (filter && !key.toLowerCase().includes(filter)) continue;
    const sel = state.selected.find((s) => s.message === sig.message_name && s.signal === sig.signal_name);
    const row = document.createElement("label");
    row.className = "sig";
    row.innerHTML =
      `<input type="checkbox" ${sel ? "checked" : ""}/>` +
      `<span class="name">${sig.message_name}.<b>${sig.signal_name}</b></span>` +
      `<span class="unit">${sig.unit || ""}</span>`;
    row.querySelector("input").addEventListener("change", (e) => {
      toggleSignal(sig, e.target.checked);
    });
    list.appendChild(row);
  }
}

async function toggleSignal(sig, on) {
  if (on) {
    const color = css(SERIES_COLORS[state.selected.length % SERIES_COLORS.length]);
    const entry = { message: sig.message_name, signal: sig.signal_name, unit: sig.unit, color, t: [], v: [] };
    state.selected.push(entry);
    await fetchSeries(entry);
  } else {
    state.selected = state.selected.filter((s) => !(s.message === sig.message_name && s.signal === sig.signal_name));
  }
  renderPlot();
}

async function fetchSeries(entry) {
  const r = await api(`/api/series?message=${encodeURIComponent(entry.message)}&signal=${encodeURIComponent(entry.signal)}`);
  entry.t = r.t; entry.v = r.v; entry.unit = r.unit || entry.unit; entry.truncated = r.truncated;
}

/* ---- stacked plots (canvas) -------------------------------------------- */
const canvas = $("plot");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = Math.max(1, Math.floor(w * dpr));
  canvas.height = Math.max(1, Math.floor(h * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function timeBounds() {
  let lo = Infinity, hi = -Infinity;
  for (const s of state.selected) {
    if (s.t.length) { lo = Math.min(lo, s.t[0]); hi = Math.max(hi, s.t[s.t.length - 1]); }
  }
  if (!isFinite(lo)) return null;
  if (lo === hi) hi = lo + 1;
  return [lo, hi];
}

const PAD_L = 66, PAD_R = 12, PAD_T = 8, PAD_B = 22;

function renderPlot() {
  $("plotHint").style.display = state.selected.length ? "none" : "flex";
  resizeCanvas();
  const W = canvas.clientWidth, H = canvas.clientHeight;
  ctx.clearRect(0, 0, W, H);
  const bounds = timeBounds();
  if (!bounds || !state.selected.length) return;
  const [t0, t1] = bounds;
  const n = state.selected.length;
  const plotW = W - PAD_L - PAD_R;
  const bandH = (H - PAD_T - PAD_B) / n;
  const xOf = (t) => PAD_L + ((t - t0) / (t1 - t0)) * plotW;

  ctx.font = "11px system-ui, sans-serif";
  state.selected.forEach((s, i) => {
    const top = PAD_T + i * bandH;
    const bot = top + bandH - 6;
    drawBand(s, i, top, bot, xOf, plotW);
  });
  drawTimeAxis(t0, t1, H, plotW);
  if (state.cursorX != null) drawCursor(t0, t1, bandH, n, xOf, plotW);
}

function drawBand(s, i, top, bot, xOf, plotW) {
  let lo = Infinity, hi = -Infinity;
  for (const v of s.v) { if (v < lo) lo = v; if (v > hi) hi = v; }
  if (!isFinite(lo)) { lo = 0; hi = 1; }
  if (lo === hi) { lo -= 1; hi += 1; }
  const yOf = (v) => bot - ((v - lo) / (hi - lo)) * (bot - top);

  // frame + grid
  ctx.strokeStyle = css("--line");
  ctx.strokeRect(PAD_L, top, plotW, bot - top);
  ctx.fillStyle = css("--muted");
  ctx.textAlign = "right";
  ctx.fillText(fmtNum(hi), PAD_L - 5, top + 9);
  ctx.fillText(fmtNum(lo), PAD_L - 5, bot - 1);

  // label
  ctx.textAlign = "left";
  ctx.fillStyle = s.color;
  const unit = s.unit ? ` [${s.unit}]` : "";
  ctx.fillText(`${s.message}.${s.signal}${unit}${s.truncated ? " (truncated)" : ""}`, PAD_L + 4, top + 11);

  // step line (sample-and-hold; no interpolation between samples)
  ctx.strokeStyle = s.color;
  ctx.lineWidth = 1.25;
  ctx.beginPath();
  let started = false, prevY = 0;
  for (let k = 0; k < s.t.length; k++) {
    const x = xOf(s.t[k]), y = yOf(s.v[k]);
    if (!started) { ctx.moveTo(x, y); started = true; }
    else { ctx.lineTo(x, prevY); ctx.lineTo(x, y); }
    prevY = y;
  }
  ctx.stroke();
  s._yOf = yOf; s._top = top; s._bot = bot;
}

function drawTimeAxis(t0, t1, H, plotW) {
  ctx.fillStyle = css("--muted");
  ctx.textAlign = "center";
  const ticks = 6;
  for (let i = 0; i <= ticks; i++) {
    const t = t0 + (i / ticks) * (t1 - t0);
    const x = PAD_L + (i / ticks) * plotW;
    ctx.fillText(fmtTime(t), x, H - 6);
  }
}

function drawCursor(t0, t1, bandH, n, xOf, plotW) {
  const x = state.cursorX;
  if (x < PAD_L || x > PAD_L + plotW) return;
  const t = t0 + ((x - PAD_L) / plotW) * (t1 - t0);
  ctx.strokeStyle = css("--accent");
  ctx.setLineDash([4, 3]);
  ctx.beginPath(); ctx.moveTo(x, PAD_T); ctx.lineTo(x, PAD_T + n * bandH); ctx.stroke();
  ctx.setLineDash([]);

  ctx.font = "11px system-ui";
  state.selected.forEach((s) => {
    const idx = nearestIndex(s.t, t);         // nearest sample; no interpolation (AC5)
    if (idx < 0) return;
    const vx = xOf(s.t[idx]), vy = s._yOf(s.v[idx]);
    ctx.fillStyle = s.color;
    ctx.beginPath(); ctx.arc(vx, vy, 3, 0, 2 * Math.PI); ctx.fill();
    const label = `${fmtNum(s.v[idx])}${s.unit ? " " + s.unit : ""} @ ${fmtTime(s.t[idx])}`;
    ctx.textAlign = x > PAD_L + plotW / 2 ? "right" : "left";
    const lx = x > PAD_L + plotW / 2 ? x - 6 : x + 6;
    ctx.fillText(label, lx, s._top + 22);
  });
}

function nearestIndex(arr, t) {
  if (!arr.length) return -1;
  let lo = 0, hi = arr.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] < t) lo = mid + 1; else hi = mid;
  }
  // lo is first >= t; compare with previous for true nearest
  if (lo > 0 && Math.abs(arr[lo - 1] - t) <= Math.abs(arr[lo] - t)) return lo - 1;
  return lo;
}

canvas.addEventListener("mousemove", (e) => {
  const rect = canvas.getBoundingClientRect();
  state.cursorX = e.clientX - rect.left;
  renderPlot();
});
canvas.addEventListener("mouseleave", () => { state.cursorX = null; renderPlot(); });

/* ---- trace table -------------------------------------------------------- */
async function loadTrace(offset) {
  const frames = $("showFrames").checked, events = $("showEvents").checked;
  const r = await api(`/api/trace?offset=${offset}&limit=${state.trace.limit}&frames=${frames}&events=${events}`);
  state.trace.offset = r.offset; state.trace.total = r.total;
  renderTable(r.rows);
  const from = r.total ? r.offset + 1 : 0;
  const to = Math.min(r.offset + state.trace.limit, r.total);
  $("pageInfo").textContent = `${from}–${to} of ${r.total}`;
  $("prevBtn").disabled = r.offset <= 0;
  $("nextBtn").disabled = to >= r.total;
}

function renderTable(rows) {
  const thead = $("traceTable").querySelector("thead");
  const tbody = $("traceTable").querySelector("tbody");
  const vis = columns.filter((c) => c.visible);
  thead.innerHTML = "<tr>" + vis.map((c) => `<th style="min-width:${c.width}px">${c.label}</th>`).join("") + "</tr>";
  tbody.innerHTML = "";
  for (const row of rows) {
    const tr = document.createElement("tr");
    const isFrame = row.kind === "frame";
    tr.className = isFrame ? "frame" : "event";
    if (isFrame && row.decode_status !== "ok") tr.classList.add("err");
    tr.innerHTML = vis.map((c) => `<td>${fmtCell(c, row[c.key])}</td>`).join("");
    if (isFrame && row.id_hex) {
      tr.classList.add("expandable");
      tr.addEventListener("click", () => toggleDetail(tr, row));
    }
    tbody.appendChild(tr);
  }
}

async function toggleDetail(tr, row) {
  if (tr.nextSibling && tr.nextSibling.classList && tr.nextSibling.classList.contains("detail")) {
    tr.nextSibling.remove(); return;
  }
  const id = parseInt(row.id_hex, 16);
  const r = await api(`/api/frame-signals?at=${row.timestamp_s}&id=${id}`);
  const det = document.createElement("tr");
  det.className = "detail";
  const span = columns.filter((c) => c.visible).length;
  const sigs = r.signals.length
    ? r.signals.map((s) => `${s.signal_name}=${s.value_num ?? s.value_text}${s.unit ? " " + s.unit : ""}`).join("  ·  ")
    : "no decoded signals";
  det.innerHTML = `<td colspan="${span}">${sigs}</td>`;
  tr.after(det);
}

function fmtCell(col, value) {
  if (value === null || value === undefined) return "";
  if (col.format === "s") return `<span>${fmtTime(value)}</span>`;
  if (col.format === "status") return `<span class="st ${value}">${value}</span>`;
  return String(value);
}

/* ---- column config dialog ---------------------------------------------- */
function renderColDialog() {
  const list = $("colList");
  list.innerHTML = "";
  columns.forEach((col, i) => {
    const row = document.createElement("div");
    row.className = "col-row";
    row.draggable = true;
    row.dataset.index = i;
    row.innerHTML =
      `<span class="grab">⠿</span>` +
      `<label style="flex:1"><input type="checkbox" ${col.visible ? "checked" : ""}/> ${col.label}</label>` +
      `<input type="number" value="${col.width}" style="width:60px" title="width px"/>` +
      (col.key === "timestamp_s"
        ? `<select><option value="s">s</option><option value="ms">ms</option><option value="hms">h:m:s</option></select>`
        : "");
    row.querySelector('input[type=checkbox]').addEventListener("change", (e) => {
      col.visible = e.target.checked; saveColumns(); loadTrace(state.trace.offset);
    });
    row.querySelector('input[type=number]').addEventListener("change", (e) => {
      col.width = Math.max(20, parseInt(e.target.value) || col.width); saveColumns(); loadTrace(state.trace.offset);
    });
    const sel = row.querySelector("select");
    if (sel) { sel.value = col.format; sel.addEventListener("change", (e) => { col.format = e.target.value; saveColumns(); loadTrace(state.trace.offset); }); }
    row.addEventListener("dragstart", (e) => e.dataTransfer.setData("i", i));
    row.addEventListener("dragover", (e) => e.preventDefault());
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      const from = +e.dataTransfer.getData("i"), to = i;
      const [m] = columns.splice(from, 1); columns.splice(to, 0, m);
      saveColumns(); renderColDialog(); loadTrace(state.trace.offset);
    });
    list.appendChild(row);
  });
}

/* ---- formatting --------------------------------------------------------- */
function fmtTime(t) {
  if (t === null || t === undefined) return "—";
  const col = columns.find((c) => c.key === "timestamp_s");
  const fmt = col ? col.format : "s";
  if (fmt === "ms") return (t * 1000).toFixed(3) + " ms";
  if (fmt === "hms") {
    const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
    return `${h}:${String(m).padStart(2, "0")}:${s.toFixed(3).padStart(6, "0")}`;
  }
  return t.toFixed(6) + " s";
}
function fmtNum(v) {
  if (v === null || v === undefined) return "—";
  if (Math.abs(v) >= 1000 || (v !== 0 && Math.abs(v) < 0.01)) return v.toPrecision(4);
  return (Math.round(v * 1000) / 1000).toString();
}

/* ---- events / bootstrap ------------------------------------------------- */
// Native file pickers: buttons open the OS dialog, change events collect files.
$("pickTraceBtn").addEventListener("click", () => $("traceFile").click());
$("pickDbcBtn").addEventListener("click", () => $("dbcFiles").click());
$("pickDbcDirBtn").addEventListener("click", () => $("dbcDir").click());
$("traceFile").addEventListener("change", (e) => {
  picked.trace = e.target.files[0] || null; refreshPicked();
});
$("dbcFiles").addEventListener("change", (e) => {
  picked.dbcs = [...e.target.files].filter((f) => f.name.toLowerCase().endsWith(".dbc"));
  refreshPicked();
});
$("dbcDir").addEventListener("change", (e) => {
  // A whole folder: keep only the .dbc files inside it.
  picked.dbcs = [...e.target.files].filter((f) => f.name.toLowerCase().endsWith(".dbc"));
  refreshPicked();
});
$("loadBtn").addEventListener("click", doLoad);
$("filter").addEventListener("input", renderSignalList);
$("showFrames").addEventListener("change", () => loadTrace(0));
$("showEvents").addEventListener("change", () => loadTrace(0));
$("prevBtn").addEventListener("click", () => loadTrace(Math.max(0, state.trace.offset - state.trace.limit)));
$("nextBtn").addEventListener("click", () => loadTrace(state.trace.offset + state.trace.limit));
$("colBtn").addEventListener("click", () => { renderColDialog(); $("colDialog").showModal(); });
$("colClose").addEventListener("click", () => $("colDialog").close());
window.addEventListener("resize", renderPlot);

// vertical resize between plot and trace
(function () {
  const divider = $("divider"), traceWrap = $("traceWrap");
  let dragging = false;
  divider.addEventListener("mousedown", () => { dragging = true; document.body.style.userSelect = "none"; });
  window.addEventListener("mouseup", () => { dragging = false; document.body.style.userSelect = ""; });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const total = document.getElementById("content").clientHeight;
    const fromTop = e.clientY - document.getElementById("content").getBoundingClientRect().top;
    const h = Math.min(Math.max(total - fromTop, 80), total - 120);
    traceWrap.style.height = h + "px";
    renderPlot();
  });
})();

// restore last state if the server already has a trace loaded
(async function init() {
  refreshPicked();
  try {
    const st = await api("/api/status");
    if (st.loaded) {
      renderSummary(st);
      await loadSignals();
      await loadTrace(0);
    }
  } catch (_) {}
})();
