"use strict";
/* CanTraceDiag local diagnostic workspace.
 * Four zones: signal explorer, stacked plot workspace, trace table, inspector.
 * All heavy queries stay server-side (windowed/downsampled) so the browser
 * never loads a whole acquisition. */

const SERIES_COLORS = ["--ch1","--ch2","--ch3","--ch4","--ch5","--ch6","--ch7","--ch8"];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

/* Resolved palette read once from the CSS custom properties so the canvas
 * render loop never calls getComputedStyle per frame (design charter: tokens
 * are the single source of truth; the loop reads this snapshot). */
const theme = {};
function refreshTheme() {
  for (const k of ["bg-deep", "line", "line-soft", "grid", "muted", "faint", "fg",
                   "accent", "ch2", "ch4"]) {
    theme[k] = css("--" + k);
  }
  theme.curA = theme.ch4;      // cursor A — green
  theme.curB = theme.accent;   // cursor B — amber
}
refreshTheme();
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#39;");

/* ---- local persistence (AC7) ------------------------------------------- */
const store = {
  get(key, fallback) {
    try { const v = JSON.parse(localStorage.getItem("ctd." + key)); return v === null ? fallback : v; }
    catch (err) { console.debug("Ignoring invalid local preference", key, err); return fallback; }
  },
  set(key, value) { localStorage.setItem("ctd." + key, JSON.stringify(value)); },
};

const state = {
  signals: [],                      // catalog entries
  selected: [],                     // {message, signal, unit, color, t:[], v:[], downsampled}
  favorites: new Set(store.get("favorites", [])),
  bounds: null,                     // [t0, t1] full data extent
  view: null,                       // [t0, t1] visible window
  cursor: { a: null, b: null, arm: "a" },
  trace: { limit: 200, total: 0, rows: [], selectedTs: null, startIndex: 0, nextCursor: null, prevCursor: null },
  seriesToken: 0,
  grid: store.get("grid", true),
  pendingConflicts: null,
};

/* ---- column model for the trace view ----------------------------------- */
const DEFAULT_COLUMNS = [
  { key: "timestamp_s", label: "Time", visible: true, width: 110, format: "s" },
  { key: "channel",     label: "Ch",   visible: true, width: 44,  format: "text" },
  { key: "kind",        label: "Kind", visible: true, width: 56,  format: "text" },
  { key: "id_hex",      label: "ID",   visible: true, width: 84,  format: "hex" },
  { key: "name",        label: "Name", visible: true, width: 150, format: "text" },
  { key: "direction",   label: "Dir",  visible: true, width: 44,  format: "text" },
  { key: "dlc",         label: "DLC",  visible: true, width: 44,  format: "dec" },
  { key: "data_hex",    label: "Data", visible: true, width: 190, format: "hex" },
  { key: "decode_status", label: "Status", visible: true, width: 96, format: "status" },
  { key: "dbc_source",  label: "DBC",  visible: false, width: 120, format: "text" },
  { key: "detail",      label: "Detail", visible: true, width: 220, format: "text" },
];
function loadColumns() {
  const saved = store.get("columns", null);
  if (Array.isArray(saved) && saved.length) {
    // Merge in any columns added since the saved layout (e.g. dbc_source).
    const known = new Set(saved.map((c) => c.key));
    for (const def of DEFAULT_COLUMNS) if (!known.has(def.key)) saved.push(structuredClone(def));
    return saved;
  }
  return structuredClone(DEFAULT_COLUMNS);
}
let columns = loadColumns();
const saveColumns = () => store.set("columns", columns);

/* ---- API helpers -------------------------------------------------------- */
// Per-process session token embedded by the server in the page shell (AC10).
// Sent on every request so mutations (local mode) and all endpoints (LAN mode)
// authenticate; cross-origin pages cannot read it.
const CTD_TOKEN = document.querySelector('meta[name="ctd-token"]')?.content || "";
function withToken(opts = {}) {
  const headers = new Headers(opts.headers || {});
  if (CTD_TOKEN) headers.set("X-CTD-Token", CTD_TOKEN);
  return { ...opts, headers };
}

async function api(path, opts) {
  const res = await fetch(path, withToken(opts));
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    throw new Error(detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

function reportError(err, context) {
  console.error(context, err);
  $("summary").innerHTML = `<span class="err">${esc(err.message || String(err))}</span>`;
}

// Upload with progress (AC8): XHR exposes upload.onprogress; fetch does not.
function uploadWithProgress(url, formData, onProgress, onUploadComplete) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    if (CTD_TOKEN) xhr.setRequestHeader("X-CTD-Token", CTD_TOKEN);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(e.loaded / e.total); };
    xhr.upload.onload = () => { onProgress(1); if (onUploadComplete) onUploadComplete(); };
    xhr.onload = () => {
      let body = {};
      try { body = JSON.parse(xhr.responseText); }
      catch (err) { console.debug("Import response was not JSON", err); }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body);
      else reject(new Error(body.detail || `${xhr.status} ${xhr.statusText}`));
    };
    xhr.onerror = () => reject(new Error("Network error during upload."));
    xhr.send(formData);
  });
}

/* ---- import ------------------------------------------------------------- */
const picked = { trace: null, dbcs: [], library: new Set() };
let libraryEntries = [];   // [{digest, name, last_used}] from the server
let lastSessionDbcs = [];  // DBC display names from the restored/last analysis

function refreshPicked() {
  const parts = [];
  if (picked.trace) parts.push(`<b>${esc(picked.trace.name)}</b>`);
  const dbcCount = picked.dbcs.length + picked.library.size;
  if (dbcCount) parts.push(`${dbcCount} DBC${picked.library.size ? ` (${picked.library.size} from library)` : ""}`);
  $("picked").innerHTML = parts.join(" · ") || "no files selected";
  $("loadBtn").disabled = !picked.trace;
}

/* ---- DBC library (workspace reuse) -------------------------------------- */
async function loadLibrary() {
  try {
    const r = await api("/api/dbc-library");
    libraryEntries = r.dbcs || [];
    lastSessionDbcs = r.last_session || [];
    // Pre-select library files that belong to the last session, so reusing
    // them needs no extra click (the trace is the only thing to pick again).
    const lastNames = new Set(lastSessionDbcs);
    if (picked.library.size === 0) {
      for (const e of libraryEntries) if (lastNames.has(e.name)) picked.library.add(e.digest);
    }
    refreshPicked();
  } catch (err) {
    console.debug("DBC library unavailable", err);
  }
}

function renderLibrary() {
  const list = $("libList");
  list.innerHTML = "";
  if (!libraryEntries.length) {
    list.innerHTML = `<div class="lib-empty">No DBC files cached yet. Import some and they will appear here.</div>`;
    return;
  }
  for (const e of libraryEntries) {
    const row = document.createElement("label");
    row.className = "lib-row";
    const when = (e.last_used || "").replace("T", " ").replace(/(\+.*|Z)$/, "");
    row.innerHTML =
      `<input type="checkbox" ${picked.library.has(e.digest) ? "checked" : ""}/>` +
      `<span class="lname">${esc(e.name)}</span>` +
      `<span class="lmeta">${esc(when)}</span>`;
    row.querySelector("input").addEventListener("change", (ev) => {
      if (ev.target.checked) picked.library.add(e.digest); else picked.library.delete(e.digest);
      refreshPicked();
    });
    list.appendChild(row);
  }
}

async function purgeWorkspace() {
  try {
    await api("/api/workspace-purge", { method: "POST" });
    picked.library.clear();
    libraryEntries = [];
    lastSessionDbcs = [];
    renderLibrary();
    refreshPicked();
    $("summary").innerHTML = `<span class="ok">Workspace cache cleared.</span>`;
  } catch (err) {
    reportError(err, "Clearing the workspace cache failed");
  }
}

// Instrument status LED. "idle" (no analysis), "importing" (during an import),
// "indexed" (a trace is loaded and queryable).
const LED_TEXT = { idle: "IDLE", importing: "IMPORTING", indexed: "INDEXED" };
function setLed(kind) {
  const led = $("statusLed");
  led.classList.remove("idle", "importing", "indexed");
  led.classList.add(kind);
  $("statusLedText").textContent = LED_TEXT[kind] || "IDLE";
}

function setProgress(frac) {
  const wrap = $("progressWrap");
  if (frac === null) { wrap.classList.remove("on"); return; }
  wrap.classList.add("on");
  $("progressBar").style.width = Math.round(frac * 100) + "%";
}

let importPollTimer = null;

function stopImportPolling() {
  if (importPollTimer !== null) clearInterval(importPollTimer);
  importPollTimer = null;
}

async function pollImportJob() {
  try {
    const job = await api("/api/import-job");
    if (typeof job.progress === "number") setProgress(job.progress);
    if (job.phase && job.phase !== "idle") {
      $("summary").innerHTML = esc(job.detail || job.phase.replaceAll("_", " "));
    }
    $("cancelImportBtn").disabled = !job.cancellable;
    if (!job.cancellable) stopImportPolling();
  } catch (err) {
    reportError(err, "Import job polling failed");
    stopImportPolling();
  }
}

function startImportPolling() {
  if (importPollTimer !== null) return;
  pollImportJob();
  importPollTimer = setInterval(pollImportJob, 500);
}

async function doLoad() {
  if (!picked.trace) return;
  const fd = new FormData();
  fd.append("trace", picked.trace, picked.trace.name);
  for (const f of picked.dbcs) fd.append("dbcs", f, f.name);
  for (const digest of picked.library) fd.append("library", digest);

  $("loadBtn").disabled = true;
  $("cancelImportBtn").hidden = false;
  $("cancelImportBtn").disabled = false;
  $("summary").innerHTML = "Uploading…";
  setLed("importing");
  setProgress(0);
  try {
    const r = await uploadWithProgress("/api/import-files", fd, (frac) => {
      setProgress(frac);
      $("summary").innerHTML = frac >= 1 ? "Indexing…" : `Uploading ${Math.round(frac * 100)}%`;
      if (frac >= 1) startImportPolling();
    }, startImportPolling);
    stopImportPolling();
    setProgress(null);
    if (r.needs_resolution) {
      await onLoaded(r);
      openConflictDialog(r.conflicts);
      return;
    }
    await onLoaded(r);
  } catch (e) {
    stopImportPolling();
    setProgress(null);
    setLed(state.bounds ? "indexed" : "idle");
    reportError(e, "Import failed");
  } finally {
    $("loadBtn").disabled = !picked.trace;
    $("cancelImportBtn").hidden = true;
  }
}

async function onLoaded(r) {
  renderSummary(r);
  setLed("indexed");
  populateEventFilter(r.summary && r.summary.event_types);
  state.bounds = r.summary ? [r.summary.start_s, r.summary.end_s] : null;
  state.view = state.bounds ? [...state.bounds] : null;
  state.cursor = { a: null, b: null, arm: "a" };
  await loadSignals();
  await restoreSelected();
  renderPlot();
  await loadTrace(null);
  clearInspector();
  loadLibrary();   // a fresh import may have added DBCs to the library
}

function renderSummary(r) {
  const s = r.summary;
  if (!s) { $("summary").textContent = "No trace loaded."; return; }
  const st = s.decode_status || {};
  let html = `<b>${s.frames}</b> frames · <b>${s.decoded_frames}</b> decoded · ` +
    `<b>${s.events}</b> events · <b>${s.unique_ids}</b> ids · ` +
    `${fmtTime(s.start_s)}–${fmtTime(s.end_s)}`;
  const problems = [];
  if (st.unknown_id) problems.push(`${st.unknown_id} unknown id`);
  if (st.ambiguous_id) problems.push(`${st.ambiguous_id} ambiguous id`);
  if (st.decode_error) problems.push(`${st.decode_error} decode error`);
  if (problems.length) html += ` · <span class="warn">${problems.join(" · ")}</span>`;
  const res = r.resolution && Object.keys(r.resolution).length;
  if (res) html += ` · <span class="ok">${res} DBC conflict(s) resolved</span>`;
  $("summary").innerHTML = html;
}

/* ---- DBC conflict modal (AC10) ----------------------------------------- */
function openConflictDialog(conflicts) {
  state.pendingConflicts = conflicts;
  $("resolveConflictsBtn").hidden = false;
  const list = $("conflictList");
  list.innerHTML = "";
  for (const c of conflicts) {
    const row = document.createElement("div");
    row.className = "conflict-row";
    const opts = c.options
      .map((o, i) => `<option value="${esc(o.database)}" ${i === 0 ? "selected" : ""}>${esc(o.database)} → ${esc(o.message)}</option>`)
      .join("");
    row.innerHTML = `<span class="cid">${esc(c.id_hex)}</span> ` +
      `<select data-id="${esc(c.id_hex)}">${opts}</select>`;
    list.appendChild(row);
  }
  $("summary").innerHTML = `<span class="warn">DBC conflict — resolution required</span>`;
  $("conflictDialog").showModal();
}

async function applyConflictResolution() {
  const resolution = {};
  for (const sel of $("conflictList").querySelectorAll("select")) {
    resolution[sel.dataset.id] = sel.value;
  }
  $("conflictDialog").close();
  $("summary").innerHTML = "Indexing…";
  try {
    const r = await api("/api/resolve", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolution }),
    });
    state.pendingConflicts = null;
    $("resolveConflictsBtn").hidden = true;
    await onLoaded(r);
  } catch (e) {
    reportError(e, "DBC conflict resolution failed");
  }
}

/* ---- signal explorer (AC5) --------------------------------------------- */
async function loadSignals() {
  try {
    const r = await api("/api/signals");
    state.signals = r.signals;
    renderSignalList();
  } catch (err) {
    state.signals = [];
    renderSignalList();
    reportError(err, "Signal list failed to load");
  }
}

function favKey(sig) { return `${sig.message_name}.${sig.signal_name}`; }

function renderSignalList() {
  const filter = $("sigFilter").value.toLowerCase();
  const favOnly = $("favOnly").checked;
  const list = $("signalList");
  list.innerHTML = "";

  // Group by DBC database, then by message.
  const groups = new Map();
  for (const sig of state.signals) {
    const key = favKey(sig);
    const haystack = [
      sig.message_name, sig.signal_name, sig.id_hex, sig.unit,
      ...(sig.databases || []),
    ].join(" ").toLowerCase();
    if (filter && !haystack.includes(filter)) continue;
    if (favOnly && !state.favorites.has(key)) continue;
    const db = (sig.databases && sig.databases[0]) || "(no DBC)";
    if (!groups.has(db)) groups.set(db, []);
    groups.get(db).push(sig);
  }

  for (const [db, sigs] of [...groups.entries()].sort()) {
    const head = document.createElement("div");
    head.className = "grp";
    head.textContent = db;
    list.appendChild(head);
    sigs.sort((a, b) => favKey(a).localeCompare(favKey(b)));
    for (const sig of sigs) list.appendChild(signalRow(sig));
  }
  if (!list.children.length) {
    const empty = document.createElement("div");
    empty.className = "grp";
    empty.textContent = state.signals.length ? "No matching signals." : "No signals (load a DBC).";
    list.appendChild(empty);
  }
}

function signalRow(sig) {
  const key = favKey(sig);
  const sel = state.selected.find((s) => s.message === sig.message_name && s.signal === sig.signal_name);
  const row = document.createElement("label");
  row.className = "sig";
  if (sig.present === false) row.classList.add("absent");
  if (sel) { row.classList.add("on"); row.style.setProperty("--sw", sel.color); }
  const swatch = sel ? `<span class="swatch" style="background:${sel.color}"></span>` : `<span class="swatch"></span>`;
  row.innerHTML =
    `<span class="star ${state.favorites.has(key) ? "on" : ""}" title="Favorite">★</span>` +
    `<input type="checkbox" ${sel ? "checked" : ""}/>` +
    swatch +
    `<span class="name">${esc(sig.message_name)}.<b>${esc(sig.signal_name)}</b></span>` +
    `<span class="unit">${esc(sig.unit || "")}${sig.present === false ? " · DBC" : ""}</span>`;
  row.querySelector(".star").addEventListener("click", (e) => {
    e.preventDefault(); e.stopPropagation();
    if (state.favorites.has(key)) state.favorites.delete(key); else state.favorites.add(key);
    store.set("favorites", [...state.favorites]);
    renderSignalList();
  });
  row.querySelector("input").addEventListener("change", (e) => toggleSignal(sig, e.target.checked));
  return row;
}

function persistSelected() {
  store.set("selected", state.selected.map((s) => ({ message: s.message, signal: s.signal })));
}

async function toggleSignal(sig, on) {
  if (on) {
    if (state.selected.find((s) => s.message === sig.message_name && s.signal === sig.signal_name)) return;
    const color = css(SERIES_COLORS[state.selected.length % SERIES_COLORS.length]);
    const entry = { message: sig.message_name, signal: sig.signal_name, unit: sig.unit, color, t: [], v: [] };
    state.selected.push(entry);
    try {
      await fetchSeries(entry);
    } catch (err) {
      state.selected = state.selected.filter((s) => s !== entry);
      reportError(err, `Series failed to load: ${entry.message}.${entry.signal}`);
    }
  } else {
    state.selected = state.selected.filter((s) => !(s.message === sig.message_name && s.signal === sig.signal_name));
    // Reassign colors so bands stay stable and distinct.
    state.selected.forEach((s, i) => { s.color = css(SERIES_COLORS[i % SERIES_COLORS.length]); });
  }
  persistSelected();
  renderSignalList();
  await refreshCursorReadout();
  renderPlot();
}

async function restoreSelected() {
  const saved = store.get("selected", []);
  state.selected = [];
  for (const item of saved) {
    const sig = state.signals.find((s) => s.message_name === item.message && s.signal_name === item.signal);
    if (!sig) continue;
    const color = css(SERIES_COLORS[state.selected.length % SERIES_COLORS.length]);
    const entry = { message: sig.message_name, signal: sig.signal_name, unit: sig.unit, color, t: [], v: [] };
    state.selected.push(entry);
  }
  const results = await Promise.allSettled(state.selected.map((s) => fetchSeries(s)));
  state.selected = state.selected.filter((_, i) => {
    if (results[i].status === "fulfilled") return true;
    reportError(results[i].reason, "Persisted series failed to restore");
    return false;
  });
  renderSignalList();
}

const pointBudget = () => Math.min(20000, Math.max(500, Math.round(($("plot").clientWidth || 900) * 2)));

async function fetchSeries(entry) {
  const [s, e] = state.view || [null, null];
  const params = new URLSearchParams({ message: entry.message, signal: entry.signal, max_points: pointBudget() });
  if (s != null) params.set("start", s);
  if (e != null) params.set("end", e);
  const r = await api(`/api/series?${params}`);
  entry.t = r.t; entry.v = r.v; entry.unit = r.unit || entry.unit; entry.downsampled = r.downsampled;
}

async function fetchAllSeries() {
  const token = ++state.seriesToken;
  const results = await Promise.allSettled(state.selected.map((s) => fetchSeries(s)));
  results.forEach((result) => {
    if (result.status === "rejected") reportError(result.reason, "Series refresh failed");
  });
  if (token !== state.seriesToken) return false;   // a newer request superseded us
  return results.every((result) => result.status === "fulfilled");
}

/* ---- stacked plots (canvas) with zoom/pan (AC1) ------------------------ */
const canvas = $("plot");
const ctx = canvas.getContext("2d");
const PAD_L = 66, PAD_R = 12, PAD_T = 8, PAD_B = 22;

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = Math.max(1, Math.floor(w * dpr));
  canvas.height = Math.max(1, Math.floor(h * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function plotGeom() {
  const W = canvas.clientWidth, H = canvas.clientHeight;
  const plotW = W - PAD_L - PAD_R;
  const view = state.view || [0, 1];
  let [t0, t1] = view;
  if (t1 <= t0) t1 = t0 + 1;
  return { W, H, plotW, t0, t1, xOf: (t) => PAD_L + ((t - t0) / (t1 - t0)) * plotW,
           tOf: (x) => t0 + ((x - PAD_L) / plotW) * (t1 - t0) };
}

function renderPlot() {
  $("plotHint").style.display = state.selected.length ? "none" : "flex";
  resizeCanvas();
  const g = plotGeom();
  ctx.clearRect(0, 0, g.W, g.H);
  updateViewHint(g);
  if (!state.selected.length) return;
  const n = state.selected.length;
  const bandH = (g.H - PAD_T - PAD_B) / n;
  ctx.font = "11px " + css("--mono");
  if (state.grid) drawXGrid(g, PAD_T, PAD_T + n * bandH);
  state.selected.forEach((s, i) => {
    const top = PAD_T + i * bandH;
    drawBand(s, top, top + bandH - 6, g, i);
  });
  drawTimeAxis(g);
  drawCursors(g, bandH, n);
  updateMeasureBadges();
}

// Scope-style A/B/Δt readouts in the plotbar. Per-signal deltas live in the
// detailed #cursorReadout table below the plot.
function updateMeasureBadges() {
  const box = $("measure");
  const { a, b } = state.cursor;
  if (a == null && b == null) { box.classList.add("empty"); return; }
  box.classList.remove("empty");
  $("mA").textContent = a == null ? "—" : fmtTime(a);
  $("mB").textContent = b == null ? "—" : fmtTime(b);
  $("mD").textContent = (a == null || b == null) ? "—" : fmtDelta(b - a) + " s";
}

const X_TICKS = () => (state.grid ? 10 : 6);
const Y_SUBLINES = 4;

function drawXGrid(g, yTop, yBot) {
  const ticks = X_TICKS();
  ctx.save();
  ctx.strokeStyle = theme.grid;
  ctx.beginPath();
  for (let i = 0; i <= ticks; i++) {
    const x = PAD_L + (i / ticks) * g.plotW;
    ctx.moveTo(x, yTop); ctx.lineTo(x, yBot);
  }
  ctx.stroke();
  ctx.restore();
}

function drawBand(s, top, bot, g, idx) {
  let lo = Infinity, hi = -Infinity;
  for (const v of s.v) { if (v < lo) lo = v; if (v > hi) hi = v; }
  if (!isFinite(lo)) { lo = 0; hi = 1; }
  if (lo === hi) { lo -= 1; hi += 1; }
  const yOf = (v) => bot - ((v - lo) / (hi - lo)) * (bot - top);

  // Track separator (hairline) and phosphor value graduations.
  ctx.strokeStyle = theme.line;
  ctx.strokeRect(PAD_L, top, g.plotW, bot - top);
  ctx.fillStyle = theme.faint;
  ctx.textAlign = "right";
  ctx.fillText(fmtNum(hi), PAD_L - 5, top + 9);
  ctx.fillText(fmtNum(lo), PAD_L - 5, bot - 1);

  if (state.grid) {
    ctx.save();
    ctx.strokeStyle = theme.grid;
    ctx.beginPath();
    for (let j = 1; j < Y_SUBLINES; j++) {
      const y = bot - (bot - top) * (j / Y_SUBLINES);
      ctx.moveTo(PAD_L, y); ctx.lineTo(PAD_L + g.plotW, y);
    }
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = theme.faint;
    ctx.textAlign = "right";
    for (let j = 1; j < Y_SUBLINES; j++) {
      const y = bot - (bot - top) * (j / Y_SUBLINES);
      ctx.fillText(fmtNum(lo + (hi - lo) * (j / Y_SUBLINES)), PAD_L - 5, y + 3);
    }
  }

  // Channel label: "CHn message.signal [unit]" in the channel colour.
  ctx.textAlign = "left";
  ctx.fillStyle = s.color;
  const unit = s.unit ? ` [${s.unit}]` : "";
  const ch = `CH${(idx % SERIES_COLORS.length) + 1} `;
  ctx.fillText(`${ch}${s.message}.${s.signal}${unit}${s.downsampled ? " (downsampled)" : ""}`, PAD_L + 4, top + 11);

  // Sample-and-hold step line with a discreet phosphor glow; no interpolation.
  ctx.save();
  ctx.beginPath();
  ctx.rect(PAD_L, top, g.plotW, bot - top);
  ctx.clip();
  ctx.strokeStyle = s.color;
  ctx.shadowColor = s.color;
  ctx.shadowBlur = 4;
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  let started = false, prevY = 0;
  for (let k = 0; k < s.t.length; k++) {
    const x = g.xOf(s.t[k]), y = yOf(s.v[k]);
    if (!started) { ctx.moveTo(x, y); started = true; }
    else { ctx.lineTo(x, prevY); ctx.lineTo(x, y); }
    prevY = y;
  }
  ctx.stroke();
  ctx.restore();
  s._yOf = yOf; s._top = top; s._bot = bot;
}

function drawTimeAxis(g) {
  ctx.fillStyle = theme.faint;
  ctx.textAlign = "center";
  // Fewer text labels than grid lines so they never overlap on a dense grid.
  const ticks = 6;
  for (let i = 0; i <= ticks; i++) {
    const x = PAD_L + (i / ticks) * g.plotW;
    ctx.fillText(fmtTime(g.t0 + (i / ticks) * (g.t1 - g.t0)), x, g.H - 6);
  }
}

function drawCursors(g, bandH, n) {
  const yBot = PAD_T + n * bandH;
  for (const [which, color] of [["a", theme.curA], ["b", theme.curB]]) {
    const t = state.cursor[which];
    if (t == null) continue;
    const x = g.xOf(t);
    if (x < PAD_L || x > PAD_L + g.plotW) continue;
    ctx.strokeStyle = color;
    ctx.setLineDash(which === "b" ? [2, 3] : [4, 3]);
    ctx.beginPath(); ctx.moveTo(x, PAD_T); ctx.lineTo(x, yBot); ctx.stroke();
    ctx.setLineDash([]);
    // Lettered handle at the foot of the cursor, scope-style.
    const hw = 7, hy = yBot - 12;
    ctx.fillStyle = color;
    ctx.fillRect(x - hw, hy, hw * 2, 12);
    ctx.fillStyle = "#0a0e12";
    ctx.textAlign = "center";
    ctx.fillText(which.toUpperCase(), x, hy + 9);
  }
}

function updateViewHint(g) {
  if (!state.view) { $("viewHint").textContent = ""; return; }
  const full = state.bounds ? (state.bounds[1] - state.bounds[0]) : 0;
  const span = g.t1 - g.t0;
  const zoom = full > 0 ? full / span : 1;
  $("viewHint").textContent = `${fmtTime(g.t0)} – ${fmtTime(g.t1)}  (${zoom.toFixed(1)}×)`;
}

/* ---- plot view control -------------------------------------------------- */
let viewTimer = null;
function scheduleSeriesRefresh() {
  clearTimeout(viewTimer);
  viewTimer = setTimeout(async () => { if (await fetchAllSeries()) renderPlot(); }, 120);
}

function setView(t0, t1, opts) {
  if (!state.bounds) return;
  const preserveSpan = opts && opts.preserveSpan;
  const [lo, hi] = state.bounds;
  const fullSpan = hi - lo;
  const minSpan = Math.max(fullSpan / 1e6, 1e-6);
  let span = t1 - t0;
  if (span < minSpan) { const mid = (t0 + t1) / 2; t0 = mid - minSpan / 2; t1 = mid + minSpan / 2; span = minSpan; }

  if (span >= fullSpan) {
    // Fully zoomed out: snap to the whole extent.
    t0 = lo; t1 = hi;
  } else if (preserveSpan) {
    // Panning: hitting an edge must slide the window, never shrink it (no
    // edge "zoom"). Keep the span fixed and clamp the leading edge.
    if (t0 < lo) { t0 = lo; t1 = lo + span; }
    else if (t1 > hi) { t1 = hi; t0 = hi - span; }
  } else {
    // Zooming: clamping a single edge is fine (span changes intentionally).
    t0 = Math.max(lo, t0); t1 = Math.min(hi, t1);
  }
  if (t1 <= t0) { t0 = lo; t1 = hi; }
  state.view = [t0, t1];
  renderPlot();
  scheduleSeriesRefresh();
}

function zoomAt(centerT, factor) {
  const [t0, t1] = state.view;
  setView(centerT - (centerT - t0) * factor, centerT + (t1 - centerT) * factor);
}

function fitView() { if (state.bounds) setView(state.bounds[0], state.bounds[1]); }

canvas.addEventListener("wheel", (e) => {
  if (!state.view) return;
  e.preventDefault();
  const g = plotGeom();
  zoomAt(g.tOf(e.offsetX), e.deltaY < 0 ? 0.8 : 1.25);
}, { passive: false });

const CURSOR_HIT_PX = 6;      // pointer proximity to grab a cursor line

// Which placed cursor (if any) the pointer is within CURSOR_HIT_PX of.
function cursorNear(g, x) {
  let best = null, bestD = CURSOR_HIT_PX;
  for (const which of ["a", "b"]) {
    const t = state.cursor[which];
    if (t == null) continue;
    const d = Math.abs(g.xOf(t) - x);
    if (d <= bestD) { best = which; bestD = d; }
  }
  return best;
}

let pan = null;              // active pan gesture
let cursorDrag = null;       // "a" | "b" while dragging a cursor

canvas.addEventListener("mousedown", (e) => {
  if (!state.view) return;
  const g = plotGeom();
  const near = cursorNear(g, e.offsetX);
  if (near) {
    // Pressing on a placed cursor grabs it immediately: dragging the cursor
    // takes priority over panning the graph. Panning starts only when the
    // press begins away from any cursor line.
    cursorDrag = near;
    pan = null;
    canvas.style.cursor = "grabbing";
    return;
  }
  pan = { x: e.offsetX, t0: state.view[0], t1: state.view[1], moved: false };
});

window.addEventListener("mousemove", (e) => {
  const g = plotGeom();
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;

  if (cursorDrag) {
    const t = Math.max(g.t0, Math.min(g.t1, g.tOf(x)));
    state.cursor[cursorDrag] = t;
    renderPlot();
    refreshCursorReadoutDebounced();
    return;
  }
  if (pan) {
    const dx = x - pan.x;
    if (Math.abs(dx) > 3) pan.moved = true;   // moved: it's a pan, not a click
    const dt = (dx / g.plotW) * (pan.t1 - pan.t0);
    setView(pan.t0 - dt, pan.t1 - dt, { preserveSpan: true });
    return;
  }
  // Idle hover: hint that a cursor line is grabbable.
  if (state.view && x >= PAD_L && x <= PAD_L + g.plotW) {
    canvas.style.cursor = cursorNear(g, x) ? "grab" : "crosshair";
  }
});

window.addEventListener("mouseup", (e) => {
  if (cursorDrag) {
    const which = cursorDrag; cursorDrag = null;
    canvas.style.cursor = "crosshair";
    locateInTrace(state.cursor[which]);   // sync trace to the dropped cursor
    refreshCursorReadout();
    return;
  }
  if (!pan) return;
  const wasClick = !pan.moved;
  const startedInCanvas = e.target === canvas || canvas.contains(e.target);
  pan = null;
  if (wasClick && startedInCanvas) {
    const g = plotGeom();
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    if (x >= PAD_L && x <= PAD_L + g.plotW) placeCursor(g.tOf(x), e.shiftKey ? "b" : state.cursor.arm, true);
  }
});
canvas.addEventListener("dblclick", () => fitView());
canvas.addEventListener("keydown", (e) => {
  if (!state.view || !["ArrowLeft", "ArrowRight"].includes(e.key)) return;
  e.preventDefault();
  const which = state.cursor.arm || "a";
  const span = state.view[1] - state.view[0];
  const step = span / (e.shiftKey ? 10 : 100);
  const current = state.cursor[which] ?? ((state.view[0] + state.view[1]) / 2);
  const dir = e.key === "ArrowRight" ? 1 : -1;
  const next = Math.max(state.view[0], Math.min(state.view[1], current + dir * step));
  placeCursor(next, which, true);
});

/* ---- A/B cursors (AC2) + graph→trace sync (AC3) ------------------------ */
function placeCursor(t, which, locate) {
  state.cursor[which] = t;
  renderPlot();
  refreshCursorReadout();
  if (locate) locateInTrace(t);
}

// Cheap live update while dragging a cursor; the exact server read settles
// shortly after the pointer stops.
const refreshCursorReadoutDebounced = debounce(() => refreshCursorReadout(), 90);

async function refreshCursorReadout() {
  refreshStats();
  const box = $("cursorReadout");
  const { a, b } = state.cursor;
  if ((a == null && b == null) || !state.selected.length) { box.classList.add("empty"); return; }
  box.classList.remove("empty");

  // Nearest real samples for every selected signal at A and B in one bounded
  // call (AC8): no interpolation, exact, and no per-signal request fan-out.
  let va = {}, vb = {};
  try {
    const batch = await api("/api/cursors", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        signals: state.selected.map((s) => ({ message: s.message, signal: s.signal })),
        a, b,
      }),
    });
    va = batch.a || {}; vb = batch.b || {};
  } catch (err) {
    console.warn("Cursor batch lookup failed", err);
  }

  const head = `<tr><th>Signal</th><th>A</th><th>B</th><th>Δ (B−A)</th></tr>`;
  let rows = "";
  const tRow = (label, av, bv, dv) =>
    `<tr><td>${label}</td><td>${av}</td><td>${bv}</td><td>${dv}</td></tr>`;
  rows += tRow("<b>time</b>",
    a == null ? "—" : fmtTime(a), b == null ? "—" : fmtTime(b),
    (a == null || b == null) ? "—" : fmtDelta(b - a) + " s");
  for (const s of state.selected) {
    const key = favSig(s);
    const ra = va[key], rb = vb[key];
    const num = (r) => (r && typeof r.value === "number") ? r.value : null;
    const av = ra ? fmtVal(ra) : "—";
    const bv = rb ? fmtVal(rb) : "—";
    const na = num(ra), nb = num(rb);
    const dv = (na != null && nb != null) ? fmtDelta(nb - na) + (s.unit ? " " + s.unit : "") : "—";
    rows += tRow(`<span style="color:${s.color}">${esc(s.message)}.${esc(s.signal)}</span>`, av, bv, esc(dv));
  }
  box.querySelector("thead").innerHTML = head;
  box.querySelector("tbody").innerHTML = rows;
}

/* ---- range statistics between A and B (AC3) ---------------------------- */
async function refreshStats() {
  const box = $("statsReadout");
  const { a, b } = state.cursor;
  if (!state.selected.length || a == null || b == null) { box.classList.add("empty"); return; }
  box.classList.remove("empty");
  const start = Math.min(a, b), end = Math.max(a, b);
  $("statsMsg").textContent = `${fmtTime(start)} – ${fmtTime(end)}`;

  const results = await Promise.all(state.selected.map(async (s) => {
    try {
      const r = await api(
        `/api/signal-stats?message=${encodeURIComponent(s.message)}` +
        `&signal=${encodeURIComponent(s.signal)}&start=${start}&end=${end}`);
      return { s, r };
    } catch (err) {
      console.warn("Signal stats failed", err);
      return { s, r: null };
    }
  }));

  const head = `<tr><th>Signal</th><th>n</th><th>min</th><th>max</th><th>mean</th><th>std</th><th>rms</th></tr>`;
  let rows = "";
  for (const { s, r } of results) {
    const label = `<span style="color:${s.color}">${esc(s.message)}.${esc(s.signal)}</span>`;
    if (!r) { rows += `<tr><td>${label}</td><td colspan="6" class="none">stats unavailable</td></tr>`; continue; }
    const unit = r.unit ? ` ${r.unit}` : "";
    if (r.kind === "empty") {
      rows += `<tr><td>${label}</td><td>0</td><td colspan="5" class="none">no samples in range</td></tr>`;
    } else if (r.kind === "text") {
      const dist = (r.distribution || []).map((d) => `${esc(d.value)}×${d.count}`).join(", ");
      rows += `<tr><td>${label}</td><td>${r.count}</td><td colspan="5" class="dist">${dist || "—"}</td></tr>`;
    } else {
      const c = (v) => v == null ? "—" : esc(fmtNum(v) + unit);
      rows += `<tr><td>${label}</td><td>${r.count}</td><td>${c(r.min)}</td><td>${c(r.max)}</td>` +
        `<td>${c(r.mean)}</td><td>${c(r.std)}</td><td>${c(r.rms)}</td></tr>`;
    }
  }
  box.querySelector("thead").innerHTML = head;
  box.querySelector("tbody").innerHTML = rows;
}

/* ---- diagnostic report (AC1) ------------------------------------------- */
async function openReportDialog() {
  const body = $("reportBody");
  body.innerHTML = `<p class="summary" style="text-align:left; margin:0">Loading…</p>`;
  $("reportDialog").showModal();
  try {
    body.innerHTML = renderReport(await api("/api/report"));
  } catch (err) {
    body.innerHTML = `<p class="summary err" style="text-align:left; margin:0">${esc(err.message || "Load a trace first.")}</p>`;
  }
}

function renderReport(r) {
  const dur = r.duration_s == null ? "—" : fmtNum(r.duration_s) + " s";
  const dbUsed = (r.dbcs_used || []).map((u) => `${esc(u.source)} (${u.frames})`).join(", ") || "none";
  const dbLoaded = (r.dbc_paths || []).map((p) => esc(p)).join(", ") || "none";
  const a = r.anomalies || {};
  const asc = Object.entries(a.asc_events || {}).map(([k, v]) => `${esc(k)}×${v}`).join(", ") || "none";
  const chips = [];
  if (a.unknown_id) chips.push(`<span class="warn">${a.unknown_id} unknown id</span>`);
  if (a.ambiguous_id) chips.push(`<span class="warn">${a.ambiguous_id} ambiguous id</span>`);
  if (a.decode_error) chips.push(`<span class="err">${a.decode_error} decode error</span>`);
  const anomalies = chips.length ? chips.join(" · ") : `<span class="ok">none</span>`;
  return `<dl class="insp-grid">` +
    `<dt>File</dt><dd>${esc(r.trace_path || "—")}</dd>` +
    `<dt>Time range</dt><dd>${fmtTime(r.start_s)} – ${fmtTime(r.end_s)}</dd>` +
    `<dt>Duration</dt><dd>${dur}</dd>` +
    `<dt>Frames</dt><dd>${r.frames} (${r.decoded_frames} decoded)</dd>` +
    `<dt>Events</dt><dd>${r.events}</dd>` +
    `<dt>Unique ids</dt><dd>${r.unique_ids}</dd>` +
    `<dt>DBCs used</dt><dd>${dbUsed}</dd>` +
    `<dt>DBCs loaded</dt><dd>${dbLoaded}</dd>` +
    `<dt>Decode anomalies</dt><dd>${anomalies}</dd>` +
    `<dt>ASC events</dt><dd>${esc(asc)}</dd>` +
    `</dl>`;
}

/* ---- export dialog (AC2) ----------------------------------------------- */
function openExportDialog() {
  const err = $("exportError"); err.hidden = true; err.textContent = "";
  $("exportSignals").innerHTML = state.selected.length
    ? state.selected.map((s) => `<b>${esc(s.message)}.${esc(s.signal)}</b>`).join(", ")
    : `<span class="warn">No signals selected</span>`;
  const abReady = state.cursor.a != null && state.cursor.b != null;
  const scope = $("exportScope");
  scope.querySelector('option[value="between_ab"]').disabled = !abReady;
  if (!abReady && scope.value === "between_ab") scope.value = state.view ? "visible" : "full";
  $("exportDialog").showModal();
}

async function runExport() {
  const err = $("exportError"); err.hidden = true;
  const fail = (msg) => { err.textContent = msg; err.hidden = false; };
  if (!state.selected.length) return fail("Select at least one signal first.");
  const scope = $("exportScope").value;
  const format = $("exportFormat").value;
  const payload = {
    signals: state.selected.map((s) => ({ message: s.message, signal: s.signal })),
    scope, format,
  };
  if (scope === "between_ab") {
    const { a, b } = state.cursor;
    if (a == null || b == null) return fail("Place cursors A and B first.");
    payload.start = Math.min(a, b); payload.end = Math.max(a, b);
  } else if (scope === "visible") {
    if (!state.view) return fail("No visible window to export.");
    payload.start = state.view[0]; payload.end = state.view[1];
  }
  try {
    const resp = await fetch("/api/export", withToken({
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }));
    if (!resp.ok) {
      let detail = `Export failed (${resp.status})`;
      try { const j = await resp.json(); if (j.detail) detail = j.detail; } catch { /* keep default */ }
      throw new Error(detail);
    }
    downloadBlob(await resp.blob(), `cantracediag_export.${format === "parquet" ? "parquet" : "csv"}`);
    $("exportDialog").close();
  } catch (e) {
    fail(e.message || "Export failed.");
  }
}

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = name;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function favSig(s) { return `${s.message}.${s.signal}`; }
function fmtVal(r) {
  if (r.value == null) return "—";
  const v = typeof r.value === "number" ? fmtNum(r.value) : r.value;
  return esc(`${v}${r.unit ? " " + r.unit : ""}`);
}
function fmtDelta(d) {
  const sign = d >= 0 ? "+" : "";
  return sign + fmtNum(d);
}

async function locateInTrace(t) {
  const params = traceFilterParams();
  params.set("at", t);
  try {
    const loc = await api(`/api/trace-locate?${params}`);
    if (loc.cursor == null) return;
    // The opaque cursor opens the page that starts on the located row (AC9).
    await loadTrace(loc.cursor, loc.timestamp_s);
  } catch (err) {
    reportError(err, "Trace locate failed");
  }
}

/* ---- trace table (AC4, AC6) -------------------------------------------- */
function traceFilterParams() {
  const p = new URLSearchParams();
  p.set("frames", $("showFrames").checked);
  p.set("events", $("showEvents").checked);
  const id = $("fId").value.trim(); if (id) p.set("id", id);
  const msg = $("fMsg").value.trim(); if (msg) p.set("message", msg);
  const sig = $("fSignal").value.trim(); if (sig) p.set("signal", sig);
  const dir = $("fDir").value; if (dir) p.set("direction", dir);
  const stt = $("fStatus").value; if (stt) p.set("status", stt);
  const evt = $("fEvent").value; if (evt) p.set("event_type", evt);
  const s = $("fStart").value; if (s !== "") p.set("start", s);
  const e = $("fEnd").value; if (e !== "") p.set("end", e);
  return p;
}

function persistFilters() {
  store.set("filters", {
    id: $("fId").value, msg: $("fMsg").value, dir: $("fDir").value,
    status: $("fStatus").value, event: $("fEvent").value, signal: $("fSignal").value,
    frames: $("showFrames").checked, events: $("showEvents").checked,
  });
}

// Cursor-paginated trace load (AC9). `cursor` is an opaque keyset token from a
// previous page or a locate; null loads the first page.
async function loadTrace(cursor, highlightTs) {
  const params = traceFilterParams();
  if (cursor != null) params.set("cursor", cursor);
  params.set("limit", state.trace.limit);
  try {
    const r = await api(`/api/trace?${params}`);
    state.trace.total = r.total; state.trace.rows = r.rows;
    state.trace.startIndex = r.start_index;
    state.trace.nextCursor = r.next_cursor; state.trace.prevCursor = r.prev_cursor;
    if (highlightTs !== undefined) state.trace.selectedTs = highlightTs;
    renderTable(r.rows);
    const from = r.total ? r.start_index + 1 : 0;
    const to = r.start_index + r.rows.length;
    $("pageInfo").textContent = `${from}–${to} of ${r.total}`;
    $("prevBtn").disabled = r.prev_cursor == null;
    $("nextBtn").disabled = r.next_cursor == null;
    return true;
  } catch (err) {
    state.trace.rows = [];
    state.trace.nextCursor = state.trace.prevCursor = null;
    renderTable([]);
    $("pageInfo").textContent = "0-0 of 0";
    $("prevBtn").disabled = true;
    $("nextBtn").disabled = true;
    reportError(err, "Trace table failed to load");
    return false;
  }
}

function renderTable(rows) {
  const thead = $("traceTable").querySelector("thead");
  const tbody = $("traceTable").querySelector("tbody");
  const vis = columns.filter((c) => c.visible);
  thead.innerHTML = "<tr>" + vis.map((c) => `<th style="min-width:${Number(c.width) || 60}px">${esc(c.label)}</th>`).join("") + "</tr>";
  tbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const isFrame = row.kind === "frame";
    tr.className = isFrame ? "frame" : "event";
    if (isFrame && row.decode_status !== "ok") tr.classList.add("err");
    if (state.trace.selectedTs != null && row.timestamp_s === state.trace.selectedTs) tr.classList.add("selected");
    tr.innerHTML = vis.map((c) => `<td>${fmtCell(c, row[c.key])}</td>`).join("");
    tr.classList.add("expandable");
    tr.addEventListener("click", () => selectRow(row, tr));
    tbody.appendChild(tr);
  });
}

// Trace→graph sync (AC3): selecting a row moves cursor A and inspects it.
function selectRow(row, tr) {
  state.trace.selectedTs = row.timestamp_s;
  for (const el of $("traceTable").querySelectorAll("tr.selected")) el.classList.remove("selected");
  tr.classList.add("selected");
  state.cursor.a = row.timestamp_s;
  renderPlot();
  refreshCursorReadout();
  showInspector(row);
}

function fmtCell(col, value) {
  if (value === null || value === undefined) return "";
  if (col.format === "s") return `<span>${fmtTime(value)}</span>`;
  if (col.format === "status") return `<span class="st ${esc(value)}">${esc(value)}</span>`;
  if (col.format === "hex") return esc(String(value).toUpperCase());
  if (col.format === "dec") {
    const n = Number(value);
    return Number.isFinite(n) ? String(n) : esc(value);
  }
  if (col.format === "bin") {
    const n = typeof value === "number" ? value : parseInt(String(value).replaceAll(" ", ""), 16);
    return Number.isFinite(n) ? `0b${n.toString(2)}` : esc(value);
  }
  return esc(value);
}

/* ---- inspector (AC6) ---------------------------------------------------- */
function clearInspector() {
  $("inspBody").innerHTML = `<div class="insp-empty">Select a trace row to inspect it.</div>`;
}

async function showInspector(row) {
  let html = "";
  if (row.kind === "frame") {
    // Instrument header: arbitration id in large mono, message + DBC subtitle,
    // raw payload highlighted in an "instrument screen" block.
    const msgParts = [row.name ?? "(undecoded)"];
    if (row.dbc_source) msgParts.push(row.dbc_source);
    html += `<div class="insp-id">${esc(row.id_hex ?? "—")}</div>` +
      `<div class="insp-msg">${esc(msgParts.join(" · "))}</div>`;
    if (row.data_hex) html += `<div class="insp-raw">${esc(String(row.data_hex).toUpperCase())}</div>`;
    const rows = [
      ["Timestamp", fmtTime(row.timestamp_s)],
      ["Channel", row.channel ?? "—"],
      ["Direction", row.direction ?? "—"],
      ["DLC", row.dlc ?? "—"],
      ["Decode status", row.decode_status ?? "—"],
    ];
    html += `<dl class="insp-grid">` +
      rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("") + `</dl>`;
    if (row.id_hex) html += `<div class="insp-sec">Decoded signals</div><div id="inspSignals" class="insp-empty">loading…</div>`;
  } else {
    const rows = [
      ["Timestamp", fmtTime(row.timestamp_s)],
      ["Kind", row.kind],
      ["Channel", row.channel ?? "—"],
      ["Event", row.name ?? "—"],
      ["Detail", row.detail ?? "—"],
    ];
    html += `<dl class="insp-grid">` +
      rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("") + `</dl>`;
  }
  $("inspBody").innerHTML = html;

  if (row.kind === "frame" && row.id_hex) {
    try {
      const id = parseInt(row.id_hex, 16);
      const r = await api(`/api/frame-signals?at=${row.timestamp_s}&id=${id}`);
      const box = $("inspSignals");
      if (!r.signals.length) { box.textContent = "no decoded signals"; box.className = "insp-empty"; return; }
      box.className = "";
      box.innerHTML = r.signals.map((s) => {
        const v = s.value_num ?? s.value_text;
        return `<div class="insp-sig"><span>${esc(s.signal_name)}</span><span class="v">${esc(`${v}${s.unit ? " " + s.unit : ""}`)}</span></div>`;
      }).join("");
    } catch (err) {
      console.warn("Inspector signal lookup failed", err);
      const box = $("inspSignals");
      if (box) box.textContent = "decoded signals unavailable";
    }
  }
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
      `<span class="grab">≡</span>` +
      `<label style="flex:1"><input type="checkbox" ${col.visible ? "checked" : ""}/> ${esc(col.label)}</label>` +
      `<input type="number" value="${Number(col.width) || 60}" style="width:60px" title="width px"/>` +
      formatOptions(col);
    row.querySelector('input[type=checkbox]').addEventListener("change", (e) => {
      col.visible = e.target.checked; saveColumns(); renderTable(state.trace.rows);
    });
    row.querySelector('input[type=number]').addEventListener("change", (e) => {
      col.width = Math.max(20, parseInt(e.target.value) || col.width); saveColumns(); renderTable(state.trace.rows);
    });
    const sel = row.querySelector("select");
    if (sel) { sel.value = col.format; sel.addEventListener("change", (e) => { col.format = e.target.value; saveColumns(); renderTable(state.trace.rows); renderPlot(); }); }
    row.addEventListener("dragstart", (e) => e.dataTransfer.setData("i", i));
    row.addEventListener("dragover", (e) => e.preventDefault());
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      const from = +e.dataTransfer.getData("i");
      const [m] = columns.splice(from, 1); columns.splice(i, 0, m);
      saveColumns(); renderColDialog(); renderTable(state.trace.rows);
    });
    list.appendChild(row);
  });
}

function formatOptions(col) {
  const opts = col.key === "timestamp_s"
    ? [["s", "s"], ["ms", "ms"], ["hms", "h:m:s"]]
    : (["id_hex", "dlc", "data_hex"].includes(col.key)
      ? [["hex", "hex"], ["dec", "dec"], ["bin", "bin"], ["text", "text"]]
      : []);
  if (!opts.length) return "";
  return `<select>${opts.map(([v, label]) => `<option value="${v}">${label}</option>`).join("")}</select>`;
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

function populateEventFilter(types) {
  const sel = $("fEvent");
  const current = sel.value;
  sel.innerHTML = `<option value="">Event</option>` +
    (Array.isArray(types) ? types : Object.keys(types || {}))
      .map((t) => `<option>${esc(t)}</option>`)
      .join("");
  sel.value = current;
}

/* ---- panel collapse + resize persistence (AC7) ------------------------- */
function applyLayout() {
  const L = store.get("layout", {});
  if (L.explorerW) $("explorer").style.width = L.explorerW + "px";
  if (L.inspectorW) $("inspector").style.width = L.inspectorW + "px";
  if (L.traceH) $("traceWrap").style.height = L.traceH + "px";
  setCollapsed("explorer", "explorerToggle", !!L.explorerCollapsed, "‹", "›");
  setCollapsed("inspector", "inspectorToggle", !!L.inspectorCollapsed, "›", "‹");
}
function patchLayout(patch) { store.set("layout", { ...store.get("layout", {}), ...patch }); }

const COLLAPSED_W = 30;   // px, must match .panel.collapsed in the stylesheet

function setCollapsed(panelId, btnId, collapsed, openGlyph, closedGlyph) {
  const panel = $(panelId);
  panel.classList.toggle("collapsed", collapsed);
  $(btnId).textContent = collapsed ? closedGlyph : openGlyph;
  // Set the width inline explicitly: the `#explorer`/`#inspector` ID rules
  // (width 270/300px) out-specify the `.panel.collapsed` class rule, so merely
  // clearing the inline width would leave the panel full-size — the collapse
  // would be visually inert. An inline value always wins.
  if (collapsed) {
    panel.style.width = COLLAPSED_W + "px";
  } else {
    const L = store.get("layout", {});
    const w = panelId === "explorer" ? L.explorerW : L.inspectorW;
    panel.style.width = w ? w + "px" : "";   // "" -> fall back to the CSS default width
  }
}

function wireCollapse(panelId, btnId, key, openGlyph, closedGlyph) {
  $(btnId).addEventListener("click", () => {
    const collapsed = !$(panelId).classList.contains("collapsed");
    setCollapsed(panelId, btnId, collapsed, openGlyph, closedGlyph);
    patchLayout({ [key]: collapsed });
    renderPlot();
  });
}

const COLLAPSE_AT = 90;   // dragging a panel narrower than this collapses it

function wireSideResize(resizerId, panelId, btnId, side, key, collapsedKey, openGlyph, closedGlyph) {
  const resizer = $(resizerId), panel = $(panelId);
  let dragging = false;
  resizer.addEventListener("mousedown", (e) => { dragging = true; e.preventDefault(); document.body.style.userSelect = "none"; });
  window.addEventListener("mouseup", () => {
    if (!dragging) return;
    dragging = false; document.body.style.userSelect = "";
    const collapsed = panel.classList.contains("collapsed");
    patchLayout(collapsed ? { [collapsedKey]: true } : { [collapsedKey]: false, [key]: panel.getBoundingClientRect().width });
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const rect = panel.getBoundingClientRect();
    // Anchor point stays fixed; the resizer sits on the panel's inner edge.
    const raw = side === "left" ? e.clientX - rect.left : rect.right - e.clientX;
    if (raw < COLLAPSE_AT) {
      setCollapsed(panelId, btnId, true, openGlyph, closedGlyph);   // slide to ~zero width
    } else {
      setCollapsed(panelId, btnId, false, openGlyph, closedGlyph);
      panel.style.width = Math.min(Math.max(raw, 150), 620) + "px";
    }
    renderPlot();
  });
}

/* ---- events / bootstrap ------------------------------------------------- */
$("pickTraceBtn").addEventListener("click", () => $("traceFile").click());
$("pickDbcBtn").addEventListener("click", () => $("dbcFiles").click());
$("pickDbcDirBtn").addEventListener("click", () => $("dbcDir").click());
$("pickLibBtn").addEventListener("click", () => { renderLibrary(); $("libDialog").showModal(); });
$("libDone").addEventListener("click", () => { $("libDialog").close(); refreshPicked(); });
$("libPurge").addEventListener("click", async () => {
  await purgeWorkspace();
  $("libDialog").close();
});
$("traceFile").addEventListener("change", (e) => { picked.trace = e.target.files[0] || null; refreshPicked(); });
$("dbcFiles").addEventListener("change", (e) => {
  picked.dbcs = [...e.target.files].filter((f) => f.name.toLowerCase().endsWith(".dbc")); refreshPicked();
});
$("dbcDir").addEventListener("change", (e) => {
  picked.dbcs = [...e.target.files].filter((f) => f.name.toLowerCase().endsWith(".dbc")); refreshPicked();
});
$("loadBtn").addEventListener("click", doLoad);
$("cancelImportBtn").addEventListener("click", async () => {
  $("cancelImportBtn").disabled = true;
  try {
    await api("/api/import-cancel", { method: "POST" });
    startImportPolling();
  } catch (err) {
    reportError(err, "Import cancellation failed");
  }
});
$("conflictApply").addEventListener("click", applyConflictResolution);
$("conflictDialog").addEventListener("cancel", () => {
  if (state.pendingConflicts) $("resolveConflictsBtn").hidden = false;
});
$("resolveConflictsBtn").addEventListener("click", () => {
  if (state.pendingConflicts) openConflictDialog(state.pendingConflicts);
});

$("sigFilter").addEventListener("input", renderSignalList);
$("favOnly").addEventListener("change", () => { store.set("favOnly", $("favOnly").checked); renderSignalList(); });

$("fitBtn").addEventListener("click", fitView);
$("zoomInBtn").addEventListener("click", () => { const g = plotGeom(); zoomAt((g.t0 + g.t1) / 2, 0.7); });
$("zoomOutBtn").addEventListener("click", () => { const g = plotGeom(); zoomAt((g.t0 + g.t1) / 2, 1.4); });
$("gridBtn").addEventListener("click", () => {
  state.grid = !state.grid; store.set("grid", state.grid);
  $("gridBtn").classList.toggle("active", state.grid);
  renderPlot();
});
$("curABtn").addEventListener("click", () => { state.cursor.arm = "a"; armButtons(); });
$("curBBtn").addEventListener("click", () => { state.cursor.arm = "b"; armButtons(); });
$("curClearBtn").addEventListener("click", () => { state.cursor.a = state.cursor.b = null; renderPlot(); refreshCursorReadout(); });
function armButtons() {
  $("curABtn").classList.toggle("active", state.cursor.arm === "a");
  $("curBBtn").classList.toggle("active", state.cursor.arm === "b");
}

const reloadTrace = () => { persistFilters(); loadTrace(null); };
for (const id of ["fId", "fMsg", "fSignal", "fStart", "fEnd"]) $(id).addEventListener("input", debounce(reloadTrace, 250));
for (const id of ["fDir", "fStatus", "fEvent"]) $(id).addEventListener("change", reloadTrace);
$("showFrames").addEventListener("change", reloadTrace);
$("showEvents").addEventListener("change", reloadTrace);
$("clearFilters").addEventListener("click", () => {
  for (const id of ["fId", "fMsg", "fSignal", "fStart", "fEnd"]) $(id).value = "";
  for (const id of ["fDir", "fStatus", "fEvent"]) $(id).value = "";
  $("showFrames").checked = true; $("showEvents").checked = true;
  reloadTrace();
});
$("prevBtn").addEventListener("click", () => { if (state.trace.prevCursor != null) loadTrace(state.trace.prevCursor); });
$("nextBtn").addEventListener("click", () => { if (state.trace.nextCursor != null) loadTrace(state.trace.nextCursor); });
$("colBtn").addEventListener("click", () => { renderColDialog(); $("colDialog").showModal(); });
$("colClose").addEventListener("click", () => $("colDialog").close());
$("reportBtn").addEventListener("click", openReportDialog);
$("reportClose").addEventListener("click", () => $("reportDialog").close());
$("exportBtn").addEventListener("click", openExportDialog);
$("exportCancel").addEventListener("click", () => $("exportDialog").close());
$("exportRun").addEventListener("click", runExport);
window.addEventListener("resize", debounce(() => { refreshTheme(); renderPlot(); scheduleSeriesRefresh(); }, 150));

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

// vertical resize between plot and trace
(function () {
  const divider = $("divider"), traceWrap = $("traceWrap");
  let dragging = false;
  divider.addEventListener("mousedown", () => { dragging = true; document.body.style.userSelect = "none"; });
  window.addEventListener("mouseup", () => {
    if (!dragging) return;
    dragging = false; document.body.style.userSelect = "";
    patchLayout({ traceH: traceWrap.getBoundingClientRect().height });
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const center = $("center");
    const total = center.clientHeight;
    const fromTop = e.clientY - center.getBoundingClientRect().top;
    traceWrap.style.height = Math.min(Math.max(total - fromTop, 80), total - 120) + "px";
    renderPlot();
  });
})();

// restore persisted filters/prefs, then any active server-side trace
function restoreFilters() {
  const f = store.get("filters", null);
  if (!f) return;
  $("fId").value = f.id || ""; $("fMsg").value = f.msg || "";
  $("fSignal").value = f.signal || "";
  $("fDir").value = f.dir || ""; $("fStatus").value = f.status || ""; $("fEvent").value = f.event || "";
  if (typeof f.frames === "boolean") $("showFrames").checked = f.frames;
  if (typeof f.events === "boolean") $("showEvents").checked = f.events;
}

// Collapsible side panels (arrow buttons) and their edge resizers.
wireCollapse("explorer", "explorerToggle", "explorerCollapsed", "‹", "›");
wireCollapse("inspector", "inspectorToggle", "inspectorCollapsed", "›", "‹");
wireSideResize("explorerResizer", "explorer", "explorerToggle", "left", "explorerW", "explorerCollapsed", "‹", "›");
wireSideResize("inspectorResizer", "inspector", "inspectorToggle", "right", "inspectorW", "inspectorCollapsed", "›", "‹");

(async function init() {
  refreshTheme();
  refreshPicked();
  setLed("idle");
  $("favOnly").checked = store.get("favOnly", false);
  $("gridBtn").classList.toggle("active", state.grid);
  applyLayout();
  restoreFilters();
  armButtons();
  try {
    const st = await api("/api/status");
    if (st.loaded) await onLoaded(st);
  } catch (err) {
    console.debug("No active trace restored at startup", err);
  }
  loadLibrary();
})();
