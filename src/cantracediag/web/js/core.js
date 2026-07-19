"use strict";
/* CanTraceDiag UI — core domain. Shared foundation: theme, DOM/util helpers, persistence, state, API, formatting, layout. */
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
  loaded: false,                    // whether an acquisition is currently loaded
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

/* Per-component error banner with an optional Retry action (AC6). Errors surface
 * in the affected component and never overwrite the global session summary or
 * block the other components. `slotId` is a dedicated empty `.comp-error` div. */
function showComponentError(slotId, message, onRetry) {
  const slot = $(slotId);
  if (!slot) return;
  slot.hidden = false;
  slot.innerHTML = `<span class="msg">${esc(message)}</span>`;
  if (onRetry) {
    const btn = document.createElement("button");
    btn.textContent = "Retry";
    btn.addEventListener("click", () => { clearComponentError(slotId); onRetry(); });
    slot.appendChild(btn);
  }
}

function clearComponentError(slotId) {
  const slot = $(slotId);
  if (!slot) return;
  slot.hidden = true;
  slot.innerHTML = "";
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
  // Named, keyboard-operable separator (AC13).
  resizer.setAttribute("role", "separator");
  resizer.setAttribute("aria-orientation", "vertical");
  resizer.setAttribute("tabindex", "0");
  resizer.setAttribute("aria-label", `Resize ${panelId} panel (arrow keys)`);
  let dragging = false;

  const persist = () => {
    const collapsed = panel.classList.contains("collapsed");
    patchLayout(collapsed ? { [collapsedKey]: true } : { [collapsedKey]: false, [key]: panel.getBoundingClientRect().width });
  };
  const applyWidth = (raw) => {
    if (raw < COLLAPSE_AT) {
      setCollapsed(panelId, btnId, true, openGlyph, closedGlyph);   // slide to ~zero width
    } else {
      setCollapsed(panelId, btnId, false, openGlyph, closedGlyph);
      panel.style.width = Math.min(Math.max(raw, 150), 620) + "px";
    }
    renderPlot();
  };

  resizer.addEventListener("pointerdown", (e) => {
    dragging = true; e.preventDefault(); document.body.style.userSelect = "none";
    if (e.pointerId != null && resizer.setPointerCapture) {
      try { resizer.setPointerCapture(e.pointerId); } catch { /* best-effort */ }
    }
  });
  window.addEventListener("pointerup", () => {
    if (!dragging) return;
    dragging = false; document.body.style.userSelect = "";
    persist();
  });
  window.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const rect = panel.getBoundingClientRect();
    // Anchor point stays fixed; the resizer sits on the panel's inner edge.
    const raw = side === "left" ? e.clientX - rect.left : rect.right - e.clientX;
    applyWidth(raw);
  });
  // Keyboard resize: arrows nudge, Enter/Space toggles collapse.
  resizer.addEventListener("keydown", (e) => {
    const width = panel.getBoundingClientRect().width;
    const grow = side === "left" ? "ArrowRight" : "ArrowLeft";
    const shrink = side === "left" ? "ArrowLeft" : "ArrowRight";
    if (e.key === grow) { applyWidth(width + 24); persist(); }
    else if (e.key === shrink) { applyWidth(width - 24); persist(); }
    else if (e.key === "Enter" || e.key === " ") { $(btnId).click(); }
    else return;
    e.preventDefault();
  });
}

function armButtons() {
  $("curABtn").classList.toggle("active", state.cursor.arm === "a");
  $("curBBtn").classList.toggle("active", state.cursor.arm === "b");
}
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
