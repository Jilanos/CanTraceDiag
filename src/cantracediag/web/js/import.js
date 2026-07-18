"use strict";
/* CanTraceDiag UI — import domain. Trace/DBC import, library and conflict resolution. */

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

