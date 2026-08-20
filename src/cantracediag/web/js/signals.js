"use strict";
/* CanTraceDiag UI — signals domain. Signal explorer, selection and series fetch. */

/* ---- signal explorer (AC5) --------------------------------------------- */
async function loadSignals() {
  try {
    const r = await api("/api/signals");
    state.signals = r.signals;
    setDatabases(r.databases || [], r.active_database || null);
    renderSignalList();
  } catch (err) {
    state.signals = [];
    setDatabases([], null);
    renderSignalList();
    reportError(err, "Signal list failed to load");
  }
}

function favKey(sig) { return `${sig.message_name}.${sig.signal_name}`; }

/* ---- DBC groups -------------------------------------------------------- */
const NO_DBC = "(no DBC)";

/* Adopt the ordered DBC metadata of a freshly loaded or restored analysis: the
 * active DBC comes first and starts expanded, every other loaded DBC is listed
 * but collapsed, so a large multi-DBC catalog stays scannable (AC2). */
function setDatabases(names, active) {
  state.databases = [...names];
  state.activeDatabase = active || names[0] || null;
  state.groupsOpen = new Map(state.databases.map((n) => [n, n === state.activeDatabase]));
}

function groupOpen(db) {
  if (state.groupsOpen.has(db)) return state.groupsOpen.get(db);
  // A group the API did not list (the "no DBC" bucket, or a catalog name absent
  // from the session) has no recency to defer to, so it opens by default.
  const open = !state.databases.includes(db) || db === state.activeDatabase;
  state.groupsOpen.set(db, open);
  return open;
}

/* DBC names come from imported files and may contain anything, so element ids
 * are sequence numbers rather than the name itself. */
const groupIds = new Map();
function groupSlug(db) {
  if (!groupIds.has(db)) groupIds.set(db, `g${groupIds.size}`);
  return groupIds.get(db);
}
const groupHeadId = (db) => `grpHead-${groupSlug(db)}`;
const groupBodyId = (db) => `grpBody-${groupSlug(db)}`;

/* Toggle one group in place: re-rendering the whole list would move focus off
 * the header the operator just activated, and only this group's rows change
 * (selection, favorites, search text and other groups stay as they are, AC3). */
function setGroupOpen(db, open) {
  state.groupsOpen.set(db, open);
  const head = $(groupHeadId(db));
  const body = $(groupBodyId(db));
  if (!head || !body) { renderSignalList(); return; }
  head.setAttribute("aria-expanded", open ? "true" : "false");
  head.querySelector(".caret").textContent = open ? "\u25be" : "\u25b8";
  body.hidden = !open;
}

function groupHeader(db, count) {
  const open = groupOpen(db);
  const head = document.createElement("button");
  head.type = "button";
  head.className = "grp" + (db === state.activeDatabase ? " active" : "");
  head.id = groupHeadId(db);
  head.setAttribute("aria-expanded", open ? "true" : "false");
  head.setAttribute("aria-controls", groupBodyId(db));
  head.innerHTML =
    `<span class="caret" aria-hidden="true">${open ? "\u25be" : "\u25b8"}</span>` +
    `<span class="grp-name">${esc(db)}</span>` +
    (db === state.activeDatabase ? `<span class="grp-tag">active</span>` : "") +
    `<span class="grp-count">${count}</span>`;
  head.addEventListener("click", () => setGroupOpen(db, !groupOpen(db)));
  return head;
}

function renderSignalList() {
  const filter = $("sigFilter").value.toLowerCase();
  const favOnly = $("favOnly").checked;
  const dispOnly = $("dispOnly").checked;
  const list = $("signalList");
  list.innerHTML = "";

  // Group by DBC database, then by message. Every loaded DBC gets a bucket up
  // front so it still has a header when no signal of its own matches (AC2).
  const groups = new Map(state.databases.map((db) => [db, []]));
  for (const sig of state.signals) {
    const key = favKey(sig);
    const haystack = [
      sig.message_name, sig.signal_name, sig.id_hex, sig.unit,
      ...(sig.databases || []),
    ].join(" ").toLowerCase();
    // The three predicates intersect: text AND favorites AND displayed (AC1).
    if (filter && !haystack.includes(filter)) continue;
    if (favOnly && !state.favorites.has(key)) continue;
    if (dispOnly && !isDisplayed(sig)) continue;
    const db = (sig.databases && sig.databases[0]) || NO_DBC;
    if (!groups.has(db)) groups.set(db, []);
    groups.get(db).push(sig);
  }

  // Session order first (active DBC leading), then anything the session did not
  // name — a stale catalog entry or the "no DBC" bucket — alphabetically.
  const extra = [...groups.keys()].filter((db) => !state.databases.includes(db)).sort();
  let matched = 0;
  for (const db of [...state.databases, ...extra]) {
    const sigs = groups.get(db) || [];
    matched += sigs.length;
    list.appendChild(groupHeader(db, sigs.length));
    const body = document.createElement("div");
    body.className = "grp-body";
    body.id = groupBodyId(db);
    body.hidden = !groupOpen(db);
    sigs.sort((a, b) => favKey(a).localeCompare(favKey(b)));
    for (const sig of sigs) body.appendChild(signalRow(sig));
    list.appendChild(body);
  }
  if (!matched) {
    const empty = document.createElement("div");
    empty.className = "grp-empty";
    empty.id = "signalEmpty";
    empty.textContent = state.signals.length ? "No matching signals." : "No signals (load a DBC).";
    list.appendChild(empty);
  }
}

/* "Displayed" means currently selected for plotting — a selected signal counts
 * even while its DBC group is collapsed (AC1). */
function isDisplayed(sig) {
  return state.selected.some((s) => s.message === sig.message_name && s.signal === sig.signal_name);
}

function signalRow(sig) {
  const key = favKey(sig);
  const sel = state.selected.find((s) => s.message === sig.message_name && s.signal === sig.signal_name);
  const row = document.createElement("label");
  row.className = "sig";
  if (sig.present === false) row.classList.add("absent");
  if (sel) { row.classList.add("on"); row.style.setProperty("--sw", sel.color); }
  const swatch = sel ? `<span class="swatch" style="background:${sel.color}"></span>` : `<span class="swatch"></span>`;
  const fav = state.favorites.has(key);
  const label = `${sig.message_name}.${sig.signal_name}`;
  row.innerHTML =
    `<span class="star ${fav ? "on" : ""}" role="button" tabindex="0" ` +
      `aria-pressed="${fav}" aria-label="Toggle favorite for ${esc(label)}">★</span>` +
    `<input type="checkbox" ${sel ? "checked" : ""} aria-label="Plot ${esc(label)}"/>` +
    swatch +
    `<span class="name">${esc(sig.message_name)}.<b>${esc(sig.signal_name)}</b></span>` +
    `<span class="unit">${esc(sig.unit || "")}${sig.present === false ? " · DBC" : ""}</span>`;
  const toggleFav = (e) => {
    e.preventDefault(); e.stopPropagation();
    if (state.favorites.has(key)) state.favorites.delete(key); else state.favorites.add(key);
    store.set("favorites", [...state.favorites]);
    renderSignalList();
  };
  const star = row.querySelector(".star");
  star.addEventListener("click", toggleFav);
  star.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") toggleFav(e); });
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
      clearComponentError("plotError");
    } catch (err) {
      state.selected = state.selected.filter((s) => s !== entry);
      // Series errors surface on the plot with a retry, not on the global summary (AC6).
      showComponentError("plotError",
        `Series failed to load: ${entry.message}.${entry.signal} — ${err.message || err}`,
        () => toggleSignal(sig, true));
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
  const failed = results.find((result) => result.status === "rejected");
  if (failed) {
    showComponentError("plotError",
      `Series refresh failed — ${failed.reason?.message || failed.reason}`,
      () => { scheduleSeriesRefresh(); });
  } else {
    clearComponentError("plotError");
  }
  if (token !== state.seriesToken) return false;   // a newer request superseded us
  return results.every((result) => result.status === "fulfilled");
}

