"use strict";
/* CanTraceDiag UI — signals domain. Signal explorer, selection and series fetch. */

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

