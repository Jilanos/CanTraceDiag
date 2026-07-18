"use strict";
/* CanTraceDiag UI — trace domain. Trace table, filters, pagination and column dialog. */

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
    // Keyboard-operable, named rows (AC13).
    tr.tabIndex = 0;
    tr.setAttribute("role", "button");
    tr.setAttribute("aria-label",
      `${row.kind} at ${fmtTime(row.timestamp_s)}${row.id_hex ? " id " + row.id_hex : ""}` +
      `${row.name ? " " + row.name : ""}`);
    tr.addEventListener("click", () => selectRow(row, tr));
    tr.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectRow(row, tr); }
    });
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

