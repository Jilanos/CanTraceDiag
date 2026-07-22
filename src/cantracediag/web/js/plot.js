"use strict";
/* CanTraceDiag UI — plot domain. Stacked canvas plots, view control and A/B cursors. */

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

// Graph interactions use Pointer Events (AC13): one code path covers mouse, pen
// and touch, with no mouse regression. `touch-action: none` on the canvas (CSS)
// stops the browser from hijacking the gesture for scrolling.
canvas.addEventListener("pointerdown", (e) => {
  if (!state.view) return;
  const g = plotGeom();
  const near = cursorNear(g, e.offsetX);
  if (e.pointerId != null && canvas.setPointerCapture) {
    try { canvas.setPointerCapture(e.pointerId); } catch { /* capture is best-effort */ }
  }
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

window.addEventListener("pointermove", (e) => {
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

window.addEventListener("pointerup", (e) => {
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

let cursorReadoutRequest = 0;
async function refreshCursorReadout() {
  const request = ++cursorReadoutRequest;
  const box = $("cursorReadout");
  const { a, b } = state.cursor;
  if ((a == null && b == null) || !state.selected.length) {
    box.classList.add("empty");
    $("statsMsg").textContent = "";
    return;
  }
  box.classList.remove("empty");

  // Nearest real samples for every selected signal at A and B in one bounded
  // call (AC8): no interpolation, exact, and no per-signal request fan-out.
  const start = a == null || b == null ? null : Math.min(a, b);
  const end = a == null || b == null ? null : Math.max(a, b);
  const cursorPromise = api("/api/cursors", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      signals: state.selected.map((s) => ({ message: s.message, signal: s.signal })),
      a, b,
    }),
  }).catch((err) => { console.warn("Cursor batch lookup failed", err); return {}; });
  const statsPromise = start == null ? Promise.resolve([]) : loadRangeStats(start, end);
  const [batch, stats] = await Promise.all([cursorPromise, statsPromise]);
  if (request !== cursorReadoutRequest) return;
  const va = batch.a || {}, vb = batch.b || {};
  const statsBySignal = new Map(stats.map(({ s, r }) => [favSig(s), r]));
  $("statsMsg").textContent = start == null ? "Place both cursors for range analysis" : `${fmtTime(start)} – ${fmtTime(end)}`;

  const head = `<tr><th rowspan="2">Signal</th><th colspan="3" class="group">Cursor values</th>` +
    `<th colspan="6" class="group">Range analysis A–B</th></tr>` +
    `<tr><th class="range-start">A</th><th>B</th><th>Δ (B−A)</th>` +
    `<th class="range-start">n</th><th>min</th><th>max</th><th>mean</th><th>std</th><th>rms</th></tr>`;
  const statsCells = (r) => {
    if (!r) return `<td colspan="6" class="range-start none">—</td>`;
    const unit = r.unit ? ` ${r.unit}` : "";
    if (r.kind === "empty") {
      return `<td class="range-start">0</td><td colspan="5" class="none">no samples in range</td>`;
    }
    if (r.kind === "text") {
      const dist = (r.distribution || []).map((d) => `${esc(d.value)}×${d.count}`).join(", ");
      return `<td class="range-start">${r.count}</td><td colspan="5" class="dist">${dist || "—"}</td>`;
    }
    const c = (v) => v == null ? "—" : esc(fmtNum(v) + unit);
    return `<td class="range-start">${r.count}</td><td>${c(r.min)}</td><td>${c(r.max)}</td>` +
      `<td>${c(r.mean)}</td><td>${c(r.std)}</td><td>${c(r.rms)}</td>`;
  };
  let rows = `<tr><td><b>time</b></td><td class="range-start">${a == null ? "—" : fmtTime(a)}</td>` +
    `<td>${b == null ? "—" : fmtTime(b)}</td>` +
    `<td>${a == null || b == null ? "—" : fmtDelta(b - a) + " s"}</td>` +
    `<td colspan="6" class="range-start none">—</td></tr>`;
  for (const s of state.selected) {
    const key = favSig(s);
    const ra = va[key], rb = vb[key];
    const num = (r) => (r && typeof r.value === "number") ? r.value : null;
    const av = ra ? fmtVal(ra) : "—";
    const bv = rb ? fmtVal(rb) : "—";
    const na = num(ra), nb = num(rb);
    const dv = (na != null && nb != null) ? fmtDelta(nb - na) + (s.unit ? " " + s.unit : "") : "—";
    rows += `<tr><td><span style="color:${s.color}">${esc(s.message)}.${esc(s.signal)}</span></td>` +
      `<td class="range-start">${av}</td><td>${bv}</td><td>${esc(dv)}</td>` +
      `${statsCells(statsBySignal.get(key))}</tr>`;
  }
  box.querySelector("thead").innerHTML = head;
  box.querySelector("tbody").innerHTML = rows;
}
