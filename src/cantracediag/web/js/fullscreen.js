"use strict";
/* CanTraceDiag UI — fullscreen domain. Document fullscreen driven by a user
 * gesture and mirrored from the browser's native state. */

/* The Fullscreen API cannot hide the browser chrome the way F11 does, and it
 * only accepts a request that comes from a user gesture. The control therefore
 * requests *document* fullscreen, treats `fullscreenchange` as the single
 * source of truth for its own state, and stays usable when the request is
 * unsupported or refused. */
function fullscreenSupported() {
  if (document.fullscreenEnabled === false) return false;
  return typeof document.documentElement.requestFullscreen === "function"
    && typeof document.exitFullscreen === "function";
}

function inFullscreen() { return !!document.fullscreenElement; }

/* Inline, non-blocking status line: a refusal must never interrupt the session
 * with a dialog. `role="status"` announces it to assistive technology. */
function setFullscreenNote(message) {
  const note = $("fullscreenNote");
  if (!note) return;
  note.textContent = message || "";
  note.hidden = !message;
}

function syncFullscreenButton() {
  const btn = $("fullscreenBtn");
  if (!btn) return;
  const on = inFullscreen();
  const label = on ? "Exit fullscreen" : "Enter fullscreen";
  btn.setAttribute("aria-pressed", on ? "true" : "false");
  btn.setAttribute("aria-label", label);
  btn.title = label;
  btn.classList.toggle("active", on);
}

async function toggleFullscreen() {
  if (!fullscreenSupported()) {
    setFullscreenNote("Fullscreen is not available in this browser.");
    return;
  }
  const wasFullscreen = inFullscreen();
  try {
    if (wasFullscreen) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
    setFullscreenNote("");
  } catch (err) {
    // Refused by a permissions policy, an embedding frame, or the user: the
    // layout is untouched and only the note changes.
    console.debug("Fullscreen request refused", err);
    setFullscreenNote(wasFullscreen
      ? "Could not leave fullscreen."
      : "The browser refused fullscreen.");
  }
  // Re-sync even after a rejection: the pressed state must follow the native
  // state, never the intent of the click.
  syncFullscreenButton();
}

$("fullscreenBtn").addEventListener("click", toggleFullscreen);

/* Escape, F11 and the browser's own UI all land here rather than in the click
 * handler, so the control follows an exit it did not initiate. */
document.addEventListener("fullscreenchange", () => {
  setFullscreenNote("");
  syncFullscreenButton();
  renderPlot();
});
document.addEventListener("fullscreenerror", () => {
  setFullscreenNote("The browser refused fullscreen.");
  syncFullscreenButton();
});

syncFullscreenButton();
