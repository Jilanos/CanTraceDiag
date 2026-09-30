"use strict";
/* CanTraceDiag UI — integral domain. Opt-in signed trapezoidal integral of one plotted signal between cursors A and B. */

/* ---- cursor integral (req_032) ----------------------------------------- */
// Off by default and on every new trace: nothing is rendered or requested
// until the operator explicitly enables it for one plotted signal. The state
// lives only in the current analysis (never persisted). `token` rejects any
// response that a newer request, a disable or a trace change superseded.
const integral = { enabled: false, target: null, token: 0, requests: 0 };

const INTEGRAL_REASONS = {
  no_samples: "No samples for this signal.",
  text_signal: "Text signal — no numeric integral.",
  no_coverage: "Signal data does not cover both cursors (no extrapolation).",
  invalid_samples: "Invalid or non-finite samples in the range are not bridged.",
};

function setIntegralButton() {
  const btn = $("integralBtn");
  btn.classList.toggle("active", integral.enabled);
  btn.setAttribute("aria-pressed", integral.enabled ? "true" : "false");
}

function setIntegralEnabled(on) {
  integral.enabled = on;
  integral.token += 1;
  setIntegralButton();
  if (!on) {
    integral.target = null;
    const panel = $("integralPanel");
    if (panel) panel.remove();
    return;
  }
  if (!state.selected.some((s) => favSig(s) === integral.target)) {
    integral.target = state.selected.length ? favSig(state.selected[0]) : null;
  }
  renderIntegralPanel();
  refreshIntegral();
}

// New trace, purge or reload: integral mode always starts disabled.
function resetIntegral() {
  if (integral.enabled) setIntegralEnabled(false);
  else integral.token += 1;
}

// Removing the target signal disables integral mode until the next explicit
// activation; otherwise only the target choices follow the plotted set.
function syncIntegralTarget() {
  if (!integral.enabled) return;
  if (integral.target && !state.selected.some((s) => favSig(s) === integral.target)) {
    setIntegralEnabled(false);
    return;
  }
  renderIntegralPanel();
}

function renderIntegralPanel() {
  let panel = $("integralPanel");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "integralPanel";
    panel.setAttribute("role", "region");
    panel.setAttribute("aria-label", "Signal integral between cursors");
    panel.innerHTML =
      `<span class="lbl">∫ Integral A–B</span>` +
      `<label>Signal <select id="integralTarget"></select></label>` +
      `<output id="integralValue" aria-live="polite"></output>` +
      `<span class="integral-method" id="integralMethod">trapezoidal · linear interpolation between samples (the plot draws steps)</span>`;
    $("cursorReadout").after(panel);
    panel.querySelector("#integralTarget").addEventListener("change", (e) => {
      integral.target = e.target.value || null;
      refreshIntegral();
    });
  }
  const select = panel.querySelector("#integralTarget");
  select.innerHTML = state.selected.length
    ? state.selected.map((s) => {
      const key = favSig(s);
      return `<option value="${esc(key)}" ${key === integral.target ? "selected" : ""}>${esc(key)}</option>`;
    }).join("")
    : `<option value="">— plot a signal —</option>`;
  select.disabled = !state.selected.length;
}

function showIntegral(text, kind) {
  const out = $("integralValue");
  if (!out) return;
  out.textContent = text;
  out.dataset.state = kind;
}

async function refreshIntegral() {
  if (!integral.enabled) return;   // zero integral work while disabled
  const token = ++integral.token;
  const s = state.selected.find((x) => favSig(x) === integral.target);
  if (!s) { showIntegral("Plot a signal to integrate.", "unavailable"); return; }
  const { a, b } = state.cursor;
  if (a == null || b == null) { showIntegral("Place cursors A and B to integrate.", "unavailable"); return; }
  showIntegral("Computing…", "pending");
  integral.requests += 1;
  let r;
  try {
    const params = new URLSearchParams({ message: s.message, signal: s.signal, a, b });
    r = await api(`/api/signal-integral?${params}`);
  } catch (err) {
    if (token !== integral.token || !integral.enabled) return;
    showIntegral(`Integral failed — ${err.message || err}`, "error");
    return;
  }
  if (token !== integral.token || !integral.enabled) return;   // stale response
  if (r.available) showIntegral(`${fmtNum(r.integral)} ${r.unit}`, "ok");
  else showIntegral(INTEGRAL_REASONS[r.reason] || "Integral unavailable.", "unavailable");
}
