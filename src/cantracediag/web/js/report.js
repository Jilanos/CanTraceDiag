"use strict";
/* CanTraceDiag UI — report domain. Range statistics, diagnostic report and export. */

/* ---- range statistics between A and B (AC3) ---------------------------- */
async function loadRangeStats(start, end) {
  return Promise.all(state.selected.map(async (s) => {
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
}

function refreshStats() { return refreshCursorReadout(); }

/* ---- diagnostic report tab (AC1, AC4) ---------------------------------- */
async function loadReport() {
  const body = $("reportBody");
  body.innerHTML = `<p class="empty-state">Loading…</p>`;
  try {
    body.innerHTML = renderReport(await api("/api/report"));
  } catch (err) {
    // A 409 means no trace is loaded — a distinct empty state, not an error (AC6).
    if (/No trace loaded/i.test(err.message || "")) {
      body.innerHTML = `<p class="empty-state"><b>No trace loaded</b>Import a trace to see its diagnostic report.</p>`;
    } else {
      body.innerHTML =
        `<div class="comp-error"><span class="msg">${esc(err.message || "Report failed to load.")}</span>` +
        `<button id="reportRetry">Retry</button></div>`;
      $("reportRetry").addEventListener("click", loadReport);
    }
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
  const warnings = (r.warnings || []).map((w) => `<span class="warn">${esc(w)}</span>`).join("<br>") ||
    `<span class="ok">none</span>`;
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
    `<dt>Trace events</dt><dd>${esc(asc)}</dd>` +
    `<dt>Import warnings</dt><dd>${warnings}</dd>` +
    `</dl>`;
}

/* ---- export dialog (AC2) ----------------------------------------------- */
/* Raw ASC export is a server capability: the static PWA reports none, so the
 * option is withdrawn there rather than offered and failing on use. */
function rawAscAvailable() { return !!(state.capabilities && state.capabilities.raw_asc_export); }

function syncExportCapabilities() {
  const option = $("exportRawOption");
  if (!option) return;
  option.disabled = !rawAscAvailable();
  option.hidden = !rawAscAvailable();
  if (!rawAscAvailable() && $("exportFormat").value === "asc_raw") $("exportFormat").value = "csv";
}

/* Start/end of the chosen scope, or an error message. Shared by both exports. */
function exportRange(scope) {
  if (scope === "between_ab") {
    const { a, b } = state.cursor;
    if (a == null || b == null) return { error: "Place cursors A and B first." };
    return { start: Math.min(a, b), end: Math.max(a, b) };
  }
  if (scope === "visible") {
    if (!state.view) return { error: "No visible window to export." };
    return { start: state.view[0], end: state.view[1] };
  }
  return {};
}

let exportSummaryToken = 0;
async function refreshExportMode() {
  const raw = $("exportFormat").value === "asc_raw";
  $("exportIntro").hidden = raw;
  $("exportRawIntro").hidden = !raw;
  $("exportSignalsRow").hidden = raw;
  const info = $("exportRawInfo");
  info.hidden = !raw;
  if (!raw) { $("exportAssumeRow").hidden = true; return; }
  const scope = $("exportScope").value;
  const range = exportRange(scope);
  if (range.error) { info.innerHTML = `<span class="warn">${esc(range.error)}</span>`; return; }
  const params = new URLSearchParams({ scope, provenance: $("exportAssume").checked ? "assume" : "block" });
  if (range.start != null) { params.set("start", range.start); params.set("end", range.end); }
  const token = ++exportSummaryToken;
  info.textContent = "Checking the range…";
  try {
    const s = await api(`/api/export-asc/summary?${params}`);
    if (token !== exportSummaryToken) return;
    state.rawExport = s;
    info.innerHTML = renderRawExportSummary(s);
    $("exportAssumeRow").hidden = !(s.unknown_channel || s.unknown_direction);
  } catch (err) {
    if (token !== exportSummaryToken) return;
    state.rawExport = null;
    info.innerHTML = `<span class="err">${esc(err.message || "Could not check the export range.")}</span>`;
  }
}

function renderRawExportSummary(s) {
  const parts = [`<b>${s.frames}</b> frame${s.frames === 1 ? "" : "s"} → <b>${esc(s.filename)}</b>`];
  if (!s.frames) parts.push(`<span class="warn">The range holds no frames: the file will contain only the ASC header.</span>`);
  const excluded = Object.entries(s.excluded_events || {});
  if (s.nonfinite_frames) excluded.push(["non-finite timestamp frames", s.nonfinite_frames]);
  parts.push(excluded.length
    ? `<span class="warn">Not written as frames: ${excluded.map(([k, v]) => `${esc(k)}×${v}`).join(", ")}</span>`
    : `<span class="ok">Nothing excluded.</span>`);
  if (s.unknown_channel || s.unknown_direction) {
    parts.push(s.blocked
      ? `<span class="err">${esc(s.blocked)}</span>`
      : `<span class="warn">${s.unknown_channel} frame(s) will be written on channel 1 and ${s.unknown_direction} as Rx; the file says so.</span>`);
  }
  for (const w of s.warnings || []) parts.push(`<span class="warn">${esc(w)}</span>`);
  return parts.join("<br>");
}

function openExportDialog() {
  const err = $("exportError"); err.hidden = true; err.textContent = "";
  syncExportCapabilities();
  $("exportSignals").innerHTML = state.selected.length
    ? state.selected.map((s) => `<b>${esc(s.message)}.${esc(s.signal)}</b>`).join(", ")
    : `<span class="warn">No signals selected</span>`;
  const abReady = state.cursor.a != null && state.cursor.b != null;
  const scope = $("exportScope");
  scope.querySelector('option[value="between_ab"]').disabled = !abReady;
  if (!abReady && scope.value === "between_ab") scope.value = state.view ? "visible" : "full";
  refreshExportMode();
  $("exportDialog").showModal();
}

async function runRawAscExport(fail) {
  const scope = $("exportScope").value;
  const range = exportRange(scope);
  if (range.error) return fail(range.error);
  const payload = { scope, provenance: $("exportAssume").checked ? "assume" : "block", ...range };
  try {
    const resp = await fetch("/api/export-asc", withToken({
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }));
    if (!resp.ok) {
      let detail = `Export failed (${resp.status})`;
      try { const j = await resp.json(); if (j.detail) detail = j.detail; } catch { /* keep default */ }
      throw new Error(detail);
    }
    const match = /filename="([^"]+)"/.exec(resp.headers.get("Content-Disposition") || "");
    downloadBlob(await resp.blob(), match ? match[1] : "cantracediag_trace.asc");
    $("exportDialog").close();
  } catch (e) {
    fail(e.message || "Export failed.");
  }
}

async function runExport() {
  const err = $("exportError"); err.hidden = true;
  const fail = (msg) => { err.textContent = msg; err.hidden = false; };
  const format = $("exportFormat").value;
  if (format === "asc_raw") {
    if (!rawAscAvailable()) return fail("Raw ASC export needs the CanTraceDiag server app.");
    return runRawAscExport(fail);
  }
  if (!state.selected.length) return fail("Select at least one signal first.");
  const scope = $("exportScope").value;
  const payload = {
    signals: state.selected.map((s) => ({ message: s.message, signal: s.signal })),
    scope, format,
  };
  const range = exportRange(scope);
  if (range.error) return fail(range.error);
  Object.assign(payload, range);
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
