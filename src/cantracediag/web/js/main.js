"use strict";
/* CanTraceDiag UI — main domain. Event wiring, layout wiring, bootstrap and the window.__ctd test surface. */

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
$("exportBtn").addEventListener("click", openExportDialog);
$("reportExportBtn").addEventListener("click", openExportDialog);
$("reportRefresh").addEventListener("click", loadReport);
$("exportCancel").addEventListener("click", () => $("exportDialog").close());
$("exportRun").addEventListener("click", runExport);
window.addEventListener("resize", debounce(() => { refreshTheme(); renderPlot(); scheduleSeriesRefresh(); }, 150));

/* ---- workspace tabs: Analysis / Trace / Report (AC4) ------------------- */
// Panels keep their DOM (and state) when hidden, so switching tabs never loses
// the current selection, cursors, filters or report. The signal explorer,
// inspector and session status live outside the tabs and persist across them.
const TABS = ["analysis", "trace", "report"];
function showTab(name) {
  if (!TABS.includes(name)) name = "analysis";
  for (const btn of document.querySelectorAll(".tab")) {
    const on = btn.dataset.tab === name;
    btn.classList.toggle("active", on);
    btn.setAttribute("aria-selected", on ? "true" : "false");
    btn.tabIndex = on ? 0 : -1;
  }
  for (const panel of document.querySelectorAll(".tabpanel")) {
    panel.hidden = panel.dataset.panel !== name;
  }
  store.set("tab", name);
  if (name === "analysis") { renderPlot(); scheduleSeriesRefresh(); }
  if (name === "report") loadReport();
}
for (const btn of document.querySelectorAll(".tab")) {
  btn.addEventListener("click", () => showTab(btn.dataset.tab));
  btn.addEventListener("keydown", (e) => {
    const i = TABS.indexOf(btn.dataset.tab);
    let next = null;
    if (e.key === "ArrowRight") next = TABS[(i + 1) % TABS.length];
    else if (e.key === "ArrowLeft") next = TABS[(i - 1 + TABS.length) % TABS.length];
    else return;
    e.preventDefault();
    showTab(next);
    $("tab" + next[0].toUpperCase() + next.slice(1)).focus();
  });
}
// Layout presets restore a persisted view (AC4).
$("presetPlots").addEventListener("click", () => showTab("analysis"));
$("presetTrace").addEventListener("click", () => showTab("trace"));
$("presetFull").addEventListener("click", () => showTab("report"));

// Collapsible secondary filters (AC7): value is kept even while collapsed.
$("moreFilters").addEventListener("click", () => {
  const sec = $("secondaryFilters");
  const open = sec.hidden;
  sec.hidden = !open;
  $("moreFilters").setAttribute("aria-expanded", open ? "true" : "false");
  $("moreFilters").textContent = open ? "More filters ▴" : "More filters ▾";
  store.set("moreFilters", open);
});

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
  if (store.get("moreFilters", false)) $("moreFilters").click();
  showTab(store.get("tab", "analysis"));
  updateTraceEmpty(0, false);   // "No trace loaded" until an import lands
  try {
    const st = await api("/api/status");
    if (st.loaded) await onLoaded(st);
  } catch (err) {
    console.debug("No active trace restored at startup", err);
  }
  loadLibrary();
})();

/* Explicit surface for browser tests (AC15): the only app internals the E2E
 * suite is allowed to touch. Everything else is reached through the rendered
 * DOM, keeping tests decoupled from implementation details. */
window.__ctd = {
  state,
  loadTrace,
  placeCursor,
  setView,
  plotGeom,
  zoomAt,
  renderPlot,
  refreshCursorReadout,
  refreshStats,
  fitView,
  selectRow,
  get selected() { return state.selected; },
  get cursor() { return { a: state.cursor.a, b: state.cursor.b, arm: state.cursor.arm }; },
  get trace() { return state.trace; },
};
