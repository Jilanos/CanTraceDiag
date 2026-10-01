"""End-to-end UI tests driving the real web app in Chromium via Playwright.

These exercise the browser-side interactions that unit tests cannot reach:

* cursor A/B dragging takes priority over graph panning (regression: the old
  long-press scheme let panning always win);
* collapsing a side panel actually shrinks it (regression: an ID-selector CSS
  width out-specified the ``.collapsed`` rule, so collapse was visually inert);
* rapid parallel /api/series + /api/cursor traffic never 500s (regression: a
  shared DuckDB connection corrupted result sets under threadpool concurrency).

The suite boots the real FastAPI app in a background thread, seeds it with a
synthetic multi-signal trace, and drives Chromium headless. It self-skips when
a browser cannot be launched so it never breaks environments without one.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.request
from pathlib import Path

import pytest

# CI must run the E2E suite, so a missing Playwright is a hard failure there
# rather than a silent skip (AC14); locally it self-skips.
try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depends on the environment
    if os.environ.get("CI"):
        raise
    pytest.skip("playwright not installed", allow_module_level=True)

REPO = Path(__file__).resolve().parents[1]

# On hosts where Chromium's system libs (libnss3/libnspr4/libasound2) are not
# installed globally, a repo-local copy under .pw-libs makes the browser launch
# without root. Harmless when the dir is absent.
_LOCAL_LIBS = REPO / ".pw-libs" / "extracted" / "usr" / "lib" / "x86_64-linux-gnu"
if _LOCAL_LIBS.is_dir():
    os.environ["LD_LIBRARY_PATH"] = (
        str(_LOCAL_LIBS) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
    )


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _write_synth_asc(path: Path) -> None:
    """A trace decodable by tests/fixtures/sample.dbc (ids 100 and 200)."""
    lines = [
        "date Tue Jul 15 10:00:00 2026",
        "base hex  timestamps absolute",
        "internal events logged",
        "// version 8.5.0",
        "Begin Triggerblock Tue Jul 15 10:00:00 2026",
    ]
    t, i = 0.0, 0
    while t <= 20.0:
        spd = int((3000 + 2000 * (i % 100) / 100) / 0.25) & 0xFFFF
        temp = (40 + (i % 80)) & 0xFF
        b = [spd & 0xFF, (spd >> 8) & 0xFF, temp, 0, 0, 0, 0, 0]
        lines.append(f"   {t:.6f} 1  100             Rx   d 8 " + " ".join(f"{x:02X}" for x in b))
        vs = int((50 + 40 * (i % 50) / 50) / 0.01) & 0xFFFF
        b2 = [vs & 0xFF, (vs >> 8) & 0xFF]
        lines.append(f"   {t:.6f} 1  200             Rx   d 2 " + " ".join(f"{x:02X}" for x in b2))
        t += 0.005
        i += 1
    lines.append("End Triggerblock")
    path.write_text("\n".join(lines) + "\n")


_SEED: dict = {}


def _seed_synth_trace() -> dict:
    """(Re)import the synthetic trace into the shared live session."""
    req = urllib.request.Request(
        f"{_SEED['base']}/api/import",
        data=json.dumps(
            {
                "trace_path": str(_SEED["trace"]),
                "dbc_paths": [str(REPO / "tests" / "fixtures" / "sample.dbc")],
            }
        ).encode(),
        # Mutating endpoints require the session token (AC10); read it from the
        # live app the server was built from.
        headers={"Content-Type": "application/json", "X-CTD-Token": _SEED["token"]},
    )
    return json.load(urllib.request.urlopen(req))["summary"]


@pytest.fixture(scope="session")
def live_url(tmp_path_factory):
    import uvicorn

    from cantracediag.api import app

    trace = tmp_path_factory.mktemp("e2e") / "synth.asc"
    _write_synth_asc(trace)

    port = _free_port()
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(cfg)
    th = threading.Thread(target=server.run, daemon=True)
    th.start()

    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(f"{base}/api/status", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        server.should_exit = True
        pytest.fail("uvicorn did not start")

    _SEED.update(base=base, trace=trace, token=app.state.ctd_security.token)
    assert _seed_synth_trace()["frames"] == 8000

    yield base
    server.should_exit = True


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # pragma: no cover - env without a usable browser
            # In CI a browser that will not launch is a failure, not a silent
            # skip, so viewport/accessibility coverage cannot quietly vanish (AC14).
            if os.environ.get("CI"):
                pytest.fail(f"Chromium must launch in CI (AC14): {e}")
            pytest.skip(f"Chromium unavailable: {e}")
        yield b
        b.close()


@pytest.fixture
def page(browser, live_url):
    """A fresh page with two signals plotted and a clean localStorage."""
    # Import tests replace the shared session; restore the synthetic trace.
    status = json.load(urllib.request.urlopen(f"{live_url}/api/status"))
    if (status.get("summary") or {}).get("frames") != 8000:
        _seed_synth_trace()
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    pg = ctx.new_page()

    # Capture any server error so backend regressions surface as test failures.
    pg._ctd_http_errors = []
    pg.on(
        "response",
        lambda r: pg._ctd_http_errors.append((r.status, r.url))
        if r.status >= 500 and "/api/" in r.url
        else None,
    )

    pg.goto(live_url)
    pg.evaluate("() => localStorage.clear()")
    pg.reload()
    pg.wait_for_function("() => typeof state !== 'undefined' && state.signals.length >= 2")

    # Plot the first two signals and wait until their samples arrive.
    pg.evaluate(
        """async () => {
            await toggleSignal(state.signals[0], true);
            await toggleSignal(state.signals[1], true);
        }"""
    )
    pg.wait_for_function("() => state.selected.length === 2 && state.selected[0].t.length > 0")
    yield pg
    ctx.close()


# --- geometry helpers -------------------------------------------------------
def _canvas_pt(pg, t, frac_y=0.5):
    """Viewport (x, y) for data time ``t`` at vertical fraction of the plot."""
    return pg.evaluate(
        """({t, fy}) => {
            const r = document.getElementById('plot').getBoundingClientRect();
            const g = window.__ctd.plotGeom();
            return { x: r.left + g.xOf(t), y: r.top + r.height * fy };
        }""",
        {"t": t, "fy": frac_y},
    )


def _setup_view_cursor(pg, t0, t1, cursor_t=None, clear=False):
    """Drive the plot into a known state through the __ctd surface (AC15)."""
    pg.evaluate(
        "({t0, t1, ct, clear}) => {"
        " window.__ctd.setView(t0, t1);"
        " if (ct !== null) window.__ctd.placeCursor(ct, 'a', false);"
        " if (clear) { window.__ctd.state.cursor.a = null; window.__ctd.state.cursor.arm = 'a'; }"
        " }",
        {"t0": t0, "t1": t1, "ct": cursor_t, "clear": clear},
    )


def _view_and_a(pg):
    return pg.evaluate(
        "() => ({ view: [...window.__ctd.state.view],"
        " a: window.__ctd.state.cursor.a })"
    )


def _cursor_a(pg):
    return pg.evaluate("() => window.__ctd.state.cursor.a")


def _drag(pg, x0, y0, x1, y1, steps=10):
    pg.mouse.move(x0, y0)
    pg.mouse.down()
    pg.mouse.move(x1, y1, steps=steps)
    pg.mouse.up()


# --- tests ------------------------------------------------------------------
def test_cursor_drag_moves_cursor_not_graph(page):
    """Pressing on cursor A and dragging must move A, not pan the view."""
    _setup_view_cursor(page, 5, 15, cursor_t=10)
    before = _view_and_a(page)

    p_from = _canvas_pt(page, 10.0)
    p_to = _canvas_pt(page, 12.0)
    _drag(page, p_from["x"], p_from["y"], p_to["x"], p_from["y"])

    after = _view_and_a(page)
    # Cursor A moved toward t=12...
    assert after["a"] == pytest.approx(12.0, abs=0.3), after
    assert after["a"] != before["a"]
    # ...and the view did NOT pan.
    assert after["view"] == pytest.approx(before["view"], abs=1e-6), after
    assert not page._ctd_http_errors


def test_drag_off_cursor_pans_and_leaves_cursor(page):
    """Dragging on empty plot area pans the view but leaves cursor A put."""
    _setup_view_cursor(page, 5, 15, cursor_t=10)
    before = _view_and_a(page)

    p_from = _canvas_pt(page, 7.0)   # >6px away from the cursor at t=10
    _drag(page, p_from["x"], p_from["y"], p_from["x"] - 120, p_from["y"])

    after = _view_and_a(page)
    assert after["a"] == pytest.approx(before["a"], abs=1e-6), after   # cursor unmoved
    assert after["view"] != before["view"]                            # view panned
    assert not page._ctd_http_errors


def test_click_places_cursor(page):
    """A click (no drag) on the plot places the armed cursor."""
    _setup_view_cursor(page, 0, 20, clear=True)
    pt = _canvas_pt(page, 8.0)
    page.mouse.click(pt["x"], pt["y"])
    a = _cursor_a(page)
    assert a == pytest.approx(8.0, abs=0.4), a


def test_keyboard_moves_armed_cursor(page):
    _setup_view_cursor(page, 0, 20, clear=True)
    page.focus("#plot")
    page.keyboard.press("ArrowRight")
    a = _cursor_a(page)
    assert a is not None
    page.keyboard.press("ArrowRight")
    b = _cursor_a(page)
    assert b > a


def test_cursor_values_and_range_analysis_share_one_panel(page):
    """A/B values and interval statistics render in one measurement table."""
    page.evaluate(
        "() => { window.__ctd.placeCursor(6, 'a', false);"
        " window.__ctd.placeCursor(14, 'b', false); }"
    )
    panel = page.locator("#cursorReadout")
    panel.locator("th", has_text="Range analysis A–B").wait_for()
    assert panel.is_visible()
    assert page.locator("#statsReadout").count() == 0
    headings = panel.locator("thead").inner_text().lower()
    assert "cursor values" in headings
    assert "range analysis a–b" in headings
    assert "mean" in headings
    assert panel.locator("tbody tr").count() == 3  # time + two selected signals
    assert not page._ctd_http_errors


@pytest.mark.parametrize(
    "panel,toggle",
    [("explorer", "explorerToggle"), ("inspector", "inspectorToggle")],
)
def test_panel_collapse_shrinks_width(page, panel, toggle):
    """Collapsing a side panel actually reduces its width to ~30px.

    The pre-fix bug left the panel at its full width (collapse was inert), so
    the assertion that matters is collapsed << open and collapsed ~= 30px.
    """
    w_open = page.evaluate(f"() => document.getElementById('{panel}').offsetWidth")
    assert w_open > 60, f"{panel} unexpectedly narrow when open: {w_open}"

    page.click(f"#{toggle}")
    w_collapsed = page.evaluate(f"() => document.getElementById('{panel}').offsetWidth")
    assert w_collapsed <= 32, f"{panel} stayed {w_collapsed}px after collapse"
    assert w_collapsed < w_open

    page.click(f"#{toggle}")
    w_reopened = page.evaluate(f"() => document.getElementById('{panel}').offsetWidth")
    assert w_reopened == pytest.approx(w_open, abs=2), w_reopened


def test_collapse_state_persists_across_reload(page):
    """Collapsed state is stored and re-applied on reload (AC7)."""
    page.click("#explorerToggle")
    assert page.evaluate("() => document.getElementById('explorer').offsetWidth") <= 32
    page.reload()
    page.wait_for_function("() => typeof state !== 'undefined'")
    assert page.evaluate("() => document.getElementById('explorer').offsetWidth") <= 32


def test_rapid_zoom_pan_no_server_errors(page):
    """Hammer the parallel series/cursor endpoints; none may 500.

    This is the browser-side guard for the DuckDB concurrency fix: many
    overlapping /api/series (and /api/cursor) requests fired back-to-back.
    """
    page.evaluate(
        "() => { window.__ctd.placeCursor(6, 'a', false);"
        " window.__ctd.placeCursor(14, 'b', false); }"
    )
    for _ in range(12):
        page.evaluate("() => window.__ctd.zoomAt(10, 0.7)")
        page.evaluate("() => window.__ctd.zoomAt(10, 1.4)")
        page.evaluate("() => refreshCursorReadout()")
    page.wait_for_timeout(600)   # let debounced series refreshes settle
    assert not page._ctd_http_errors, page._ctd_http_errors


def _visible_rows(pg) -> int:
    """Signal rows the operator can actually see (collapsed groups excluded)."""
    return pg.locator("#signalList .grp-body:not([hidden]) .sig").count()


def test_signal_filters_intersect_and_show_an_empty_state(page):
    """Displayed-only, favorites-only and text search intersect (AC1, AC3)."""
    pg = page
    total = pg.evaluate("() => state.signals.length")
    assert _visible_rows(pg) == total

    # Displayed-only keeps exactly the plotted signals.
    pg.locator("#dispOnly").check()
    assert _visible_rows(pg) == 2
    first = pg.evaluate("() => state.selected[0].signal")

    # ... and intersects with the text search instead of replacing it.
    pg.locator("#sigFilter").fill(first)
    assert _visible_rows(pg) == 1

    # ... and with favorites-only, which no signal satisfies yet.
    pg.locator("#favOnly").check()
    assert _visible_rows(pg) == 0
    empty = pg.locator("#signalEmpty")
    assert empty.is_visible()
    assert "no matching signals" in empty.inner_text().lower()

    # Filtering never touched the plotted selection or the query (AC3).
    assert pg.evaluate("() => state.selected.length") == 2
    assert pg.locator("#sigFilter").input_value() == first

    pg.locator("#favOnly").uncheck()
    pg.locator("#dispOnly").uncheck()
    pg.locator("#sigFilter").fill("")
    assert _visible_rows(pg) == total
    assert pg.locator("#signalEmpty").count() == 0


def test_dbc_groups_are_ordered_and_independently_collapsible(browser, live_url):
    """Relevant DBCs are compact by default; unused ones remain on demand."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate("() => localStorage.clear()")
    pg.set_input_files("#traceFile", str(REPO / "tests" / "fixtures" / "sample.asc"))
    pg.set_input_files(
        "#dbcFiles",
        [
            str(REPO / "tests" / "fixtures" / "sample.dbc"),
            str(REPO / "tests" / "fixtures" / "sample_body.dbc"),
        ],
    )
    pg.click("#loadBtn")
    pg.wait_for_function("() => window.__ctd && window.__ctd.state.databases.length === 2")

    heads = pg.locator("#signalList .grp")
    # The trace uses sample.dbc, so the unused catalog entry is compacted until
    # the operator explicitly asks to inspect it.
    assert heads.count() == 1
    assert pg.locator("#showUnusedDbcs").inner_text().lower() == "+ 1 unused dbc"
    pg.locator("#showUnusedDbcs").click()
    assert heads.count() == 2
    assert "sample.dbc" in heads.nth(0).inner_text().lower()
    assert "sample_body.dbc" in heads.nth(1).inner_text().lower()
    assert heads.nth(0).get_attribute("aria-expanded") == "true"
    assert heads.nth(1).get_attribute("aria-expanded") == "false"
    assert heads.nth(0).locator(".grp-tag").inner_text().lower() == "active"
    # Regression: a class named `active` inherited the global accent-filled
    # button style, painting the header the same color as its own badge.
    assert pg.evaluate(
        """() => {
            const head = document.querySelector('#signalList .grp');
            const tag = head.querySelector('.grp-tag');
            return getComputedStyle(head).backgroundColor !== getComputedStyle(tag).color;
        }"""
    )
    bodies = pg.locator("#signalList .grp-body")
    assert bodies.nth(0).is_visible()
    assert not bodies.nth(1).is_visible()

    # Plot a signal from the active group, then drive the second header from the
    # keyboard: only that group changes, and the selection survives (AC3).
    # The first message of the active DBC is reachable immediately; its header
    # is only toggled when the operator explicitly collapses it.
    assert bodies.nth(0).locator(".msg-grp").first.get_attribute("aria-expanded") == "true"
    bodies.nth(0).locator("input[type=checkbox]").first.check()
    pg.wait_for_function("() => window.__ctd.selected.length === 1")
    heads.nth(1).focus()
    pg.keyboard.press("Enter")
    pg.wait_for_function(
        "() => document.querySelectorAll('#signalList .grp')[1]"
        ".getAttribute('aria-expanded') === 'true'"
    )
    assert bodies.nth(1).is_visible()
    assert heads.nth(0).get_attribute("aria-expanded") == "true"
    assert pg.evaluate("() => window.__ctd.selected.length") == 1

    # Collapsing the active group hides only its rows, never the selection.
    heads.nth(0).click()
    assert heads.nth(0).get_attribute("aria-expanded") == "false"
    assert not bodies.nth(0).is_visible()
    assert bodies.nth(1).is_visible()
    assert pg.evaluate("() => window.__ctd.selected.length") == 1

    # Search removes groups with no matching signal, rather than leaving an
    # operator to scan empty DBC headers.
    heads.nth(0).click()
    pg.locator("#sigFilter").fill("EngineSpeed")
    assert heads.count() == 1
    assert heads.nth(0).locator(".grp-count").inner_text() == "1"
    assert _visible_rows(pg) == 1
    ctx.close()


# --- fullscreen -------------------------------------------------------------
# The native API is stubbed rather than driven for real: headless Chromium
# cannot be trusted to grant document fullscreen, and what these tests must pin
# down is that the control follows the *native* state rather than the click.
_FS_STUB = """
    (mode) => {
      window.__fsEl = null;
      window.__fsCalls = 0;
      Object.defineProperty(document, "fullscreenElement", {
        configurable: true, get: () => window.__fsEl,
      });
      Object.defineProperty(document, "fullscreenEnabled", {
        configurable: true, get: () => mode !== "unsupported",
      });
      if (mode === "unsupported") {
        document.documentElement.requestFullscreen = undefined;
        return;
      }
      document.documentElement.requestFullscreen = () => {
        window.__fsCalls++;
        if (mode === "reject") return Promise.reject(new Error("denied"));
        window.__fsEl = document.documentElement;
        return Promise.resolve();
      };
      document.exitFullscreen = () => {
        window.__fsEl = null;
        return Promise.resolve();
      };
    }
"""


def test_fullscreen_control_follows_native_state(browser, live_url):
    """Enter, then an external exit: the pressed state mirrors the browser (AC1, AC2)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate(_FS_STUB, "grant")
    btn = pg.locator("#fullscreenBtn")
    assert btn.get_attribute("aria-pressed") == "false"
    assert btn.get_attribute("aria-label") == "Enter fullscreen"

    btn.click()  # a real user gesture, as the API requires
    pg.wait_for_function("() => window.__fsCalls === 1")
    # The state only moves once the browser confirms it.
    pg.evaluate("() => document.dispatchEvent(new Event('fullscreenchange'))")
    pg.wait_for_function(
        "() => document.getElementById('fullscreenBtn').getAttribute('aria-pressed') === 'true'"
    )
    assert btn.get_attribute("aria-label") == "Exit fullscreen"

    # An exit we did not initiate (Escape, F11, the browser UI) restores the
    # enter affordance.
    pg.evaluate(
        "() => { window.__fsEl = null; document.dispatchEvent(new Event('fullscreenchange')); }"
    )
    pg.wait_for_function(
        "() => document.getElementById('fullscreenBtn').getAttribute('aria-pressed') === 'false'"
    )
    assert btn.get_attribute("aria-label") == "Enter fullscreen"
    assert pg.locator("#fullscreenNote").is_hidden()
    ctx.close()


@pytest.mark.parametrize(
    ("mode", "message"),
    [("reject", "refused"), ("unsupported", "not available")],
)
def test_fullscreen_failure_is_announced_without_blocking(browser, live_url, mode, message):
    """A refused or unsupported request leaves the page usable (AC3)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate(_FS_STUB, mode)
    btn = pg.locator("#fullscreenBtn")
    btn.click()
    note = pg.locator("#fullscreenNote")
    note.wait_for(state="visible")
    assert message in note.inner_text()
    # Not a dialog, and the control still advertises entering fullscreen.
    assert pg.locator("dialog[open]").count() == 0
    assert btn.get_attribute("aria-pressed") == "false"
    assert btn.get_attribute("aria-label") == "Enter fullscreen"
    # The workspace is untouched and still responds.
    pg.locator("#viewTrace").click()
    assert pg.locator("#traceWrap").is_visible()
    ctx.close()


def test_imported_text_does_not_execute_html(browser, live_url, tmp_path):
    """Hostile ASC/DBC text must render as text, not executable markup."""
    trace = tmp_path / "hostile.asc"
    trace.write_text(
        "\n".join(
            [
                "date Tue Jul 15 10:00:00 2026",
                "base hex  timestamps absolute",
                "Begin Triggerblock Tue Jul 15 10:00:00 2026",
                "   0.000000 1  100             Rx   d 8 00 10 64 00 00 00 00 00",
                "   0.001000 <img src=x onerror=window.__ctdXss=1>",
                "End Triggerblock",
            ]
        )
        + "\n"
    )
    dbc = tmp_path / "hostile.dbc"
    dbc.write_text(
        'VERSION ""\nNS_ :\nBS_:\nBU_: ECU\n'
        "BO_ 256 EngineData: 8 ECU\n"
        ' SG_ EngineSpeed : 0|16@1+ (0.25,0) [0|16383.75] '
        '"<svg/onload=window.__ctdXss=2>" Vector__XXX\n'
    )

    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate("() => { localStorage.clear(); window.__ctdXss = 0; }")
    pg.set_input_files("#traceFile", str(trace))
    pg.set_input_files("#dbcFiles", str(dbc))
    pg.click("#loadBtn")
    pg.wait_for_function("() => window.__ctd && window.__ctd.state.signals.length === 1")
    pg.locator("#viewTrace").click()  # the trace table lives in the Trace view
    pg.wait_for_selector("#traceTable tbody tr")
    pg.wait_for_timeout(200)
    assert pg.evaluate("() => window.__ctdXss") == 0
    assert "<img src=x onerror=window.__ctdXss=1>" in pg.locator("#traceTable").inner_text()
    assert "<svg/onload=window.__ctdXss=2>" in pg.locator("#signalList").inner_text()
    ctx.close()


def test_blf_trace_imports_through_the_real_picker(browser, live_url, tmp_path):
    """A BLF recording reaches the loaded UI through the shipped file picker.

    The unit tests cover the adapter and the API; this is the one that proves
    the picker actually accepts the extension and the trace view renders the
    normalized frames.
    """
    from blf_fixture import write_sample_blf

    trace = write_sample_blf(tmp_path / "acquisition.blf")

    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate("() => localStorage.clear()")
    assert pg.get_attribute("#traceFile", "accept") == ".asc,.trc,.blf,.mf4"

    pg.set_input_files("#traceFile", str(trace))
    pg.set_input_files("#dbcFiles", str(REPO / "tests" / "fixtures" / "sample.dbc"))
    pg.click("#loadBtn")
    pg.locator("#viewTrace").click()
    # Wait on this fixture's own row count (4 frames + 3 diagnostics), not merely
    # on "something is loaded": the server session outlives a page, so a fresh
    # page can render a trace a previous test imported while this one is still
    # importing.
    pg.wait_for_function("() => window.__ctd && window.__ctd.state.trace.total === 7")
    pg.wait_for_selector("#traceTable tbody tr")

    table = pg.locator("#traceTable").inner_text()
    assert "EngineData" in table
    # The diagnostics the adapter emits are visible in the same trace view.
    assert "BlfUnsupported" in table
    ctx.close()


def test_mf4_imports_and_downloads_as_raw_asc_without_signals(browser, live_url, tmp_path):
    """An unfinalized MF4 goes in through the picker and out as raw ASC.

    No DBC and no selected signal: the export dialog must offer the raw trace,
    disclose exclusions and the recovery warning before download, and name the
    file ``.asc``. Selected-signal formats keep their own validation.
    """
    from mf4_fixture import Group, Record, write_mf4

    groups = [
        Group("CAN9_Rx", 32, constants={"BusChannel": 9, "IDE": 0, "Dir": 0}),
        Group("CAN1_Rx", 64, constants={"BusChannel": 1, "IDE": 0, "Dir": 0}),
        Group("CAN1_Errors", 90, kind="error", constants={"BusChannel": 1}),
    ]
    records = [
        Record("CAN1_Rx", 0.25, 0x100, 8, bytes(8)),
        Record("CAN9_Rx", 0.5, 0x7FF, 1, b"\x01"),
        Record("CAN1_Errors", 0.75),
        Record("CAN1_Rx", 1.0, 0x101, 0, b""),
    ]
    trace = write_mf4(tmp_path / "00000002.MF4", groups, records, unfinished=True)

    ctx = browser.new_context(viewport={"width": 1280, "height": 720}, accept_downloads=True)
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate("() => localStorage.clear()")
    pg.set_input_files("#traceFile", str(trace))
    pg.click("#loadBtn")
    pg.locator("#viewTrace").click()
    pg.wait_for_function("() => window.__ctd && window.__ctd.state.trace.total === 4")
    assert "1 import warning" in pg.locator("#summary").inner_text()

    pg.locator("#viewPlots").click()
    pg.click("#exportBtn")
    pg.select_option("#exportFormat", "asc_raw")
    pg.select_option("#exportScope", "full")
    info = pg.locator("#exportRawInfo")
    info.locator("text=00000002.asc").wait_for()
    text = info.inner_text()
    assert "3 frames" in text
    assert "ErrorFrame×1" in text
    assert "unfinalized" in text
    assert pg.locator("#exportSignalsRow").is_hidden()

    with pg.expect_download() as dl:
        pg.click("#exportRun")
    download = dl.value
    assert download.suggested_filename == "00000002.asc"
    body = Path(download.path()).read_text()
    assert "// excluded (not written as frames): ErrorFrame=1" in body
    assert "0.500000 9  7FF             Rx   d 1 01" in body

    # Back on a signal format, the "select a signal" rule still applies.
    pg.click("#exportBtn")
    pg.select_option("#exportFormat", "csv")
    pg.click("#exportRun")
    assert "Select at least one signal" in pg.locator("#exportError").inner_text()
    ctx.close()


def test_dbc_conflict_dialog_can_be_reopened_after_escape(browser, live_url):
    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.evaluate("() => localStorage.clear()")
    pg.set_input_files("#traceFile", str(REPO / "tests" / "fixtures" / "sample.asc"))
    pg.set_input_files(
        "#dbcFiles",
        [
            str(REPO / "tests" / "fixtures" / "sample.dbc"),
            str(REPO / "tests" / "fixtures" / "sample_conflict.dbc"),
        ],
    )
    pg.click("#loadBtn")
    pg.wait_for_selector("#conflictDialog[open]")

    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.getElementById('conflictDialog').open")
    assert pg.locator("#resolveConflictsBtn").is_visible()

    pg.click("#resolveConflictsBtn")
    pg.wait_for_selector("#conflictDialog[open]")
    ctx.close()


def test_narrow_viewport_keeps_critical_actions_reachable(browser, live_url):
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    pg.goto(live_url)
    # Minimal 390x844 support: import, load, main filters, views and export
    # stay reachable within the viewport (AC14).
    # Plots is active by default; import/load/views/export stay reachable.
    for selector in [
        "#pickTraceBtn", "#loadBtn", "#viewSplit", "#viewReport", "#exportBtn",
        # The compact-screen additions must stay reachable too (AC5).
        "#dispOnly", "#favOnly", "#fullscreenBtn",
    ]:
        box = pg.locator(selector).bounding_box()
        assert box is not None, selector
        assert box["x"] >= 0, selector
        assert box["x"] + box["width"] <= 390 + 1, selector
    ctx.close()


# The four viewports AC14 mandates; CI runs every one of them.
_VIEWPORTS = [
    (1024, 768),
    (1280, 720),
    (1600, 900),
    (390, 844),
]


@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_no_horizontal_overflow_at_supported_viewports(browser, live_url, width, height):
    ctx = browser.new_context(viewport={"width": width, "height": height})
    pg = ctx.new_page()
    pg.goto(live_url)
    # No main control overflows horizontally: the document is not wider than the
    # viewport (AC14).
    overflow = pg.evaluate(
        "() => document.documentElement.scrollWidth - window.innerWidth"
    )
    assert overflow <= 1, f"horizontal overflow of {overflow}px at {width}x{height}"
    # Key controls sit within the viewport width at every desktop size.
    if width >= 1024:
        controls = [
            "#loadBtn", "#exportBtn", "#viewPlots", "#viewSplit",
            "#viewTrace", "#viewReport",
        ]
        for selector in controls:
            box = pg.locator(selector).bounding_box()
            assert box is not None, selector
            assert box["x"] + box["width"] <= width + 1, f"{selector} overflows at {width}"
    ctx.close()


def test_main_controls_have_accessible_names(browser, live_url):
    """Automated accessibility check over the main paths (AC13)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    pg = ctx.new_page()
    pg.goto(live_url)
    unnamed = pg.evaluate(
        """
        () => {
          const sel = 'button, input, select, [role=button], [role=separator]';
          return [...document.querySelectorAll(sel)]
            .filter(el => el.offsetParent !== null || el.tagName === 'CANVAS')
            .filter(el => {
              const name = (el.getAttribute('aria-label') || el.textContent
                || el.getAttribute('title') || el.getAttribute('placeholder') || '').trim();
              return !name;
            })
            .map(el => el.id || el.className || el.tagName);
        }
        """
    )
    assert unnamed == [], f"controls without an accessible name: {unnamed}"


def test_favorite_toggles_via_keyboard(browser, live_url):
    """A favorite star is operable from the keyboard (AC13)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    pg = ctx.new_page()
    pg.goto(live_url)
    star = pg.locator(".sig .star").first
    star.wait_for()
    before = star.get_attribute("aria-pressed")
    star.focus()
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(50)
    after = pg.locator(".sig .star").first.get_attribute("aria-pressed")
    assert before != after
    ctx.close()


def test_trace_dialogs_close_with_escape(browser, live_url):
    """Dialogs are keyboard-dismissable (AC13)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.locator("#viewTrace").click()  # column dialog lives in the Trace view
    pg.locator("#colBtn").click()
    assert pg.locator("#colDialog").evaluate("d => d.open") is True
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(50)
    assert pg.locator("#colDialog").evaluate("d => d.open") is False
    ctx.close()


def test_workspace_views_include_split_and_preserve_state(browser, live_url):
    """One view control restores plots, split, trace and report layouts (AC4)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    pg = ctx.new_page()
    pg.goto(live_url)
    # Plot a signal in the Plots view.
    pg.locator(".sig input[type=checkbox]").first.check()
    pg.wait_for_timeout(200)
    selected_before = pg.evaluate("() => window.__ctd.selected.length")
    assert selected_before > 0
    # The combined view restores the plot and trace at the same time.
    pg.locator("#viewSplit").click()
    assert pg.locator("#plotArea").is_visible()
    assert pg.locator("#traceWrap").is_visible()
    assert pg.locator("#splitDivider").is_visible()
    # Trace alone hides the plot.
    pg.locator("#viewTrace").click()
    assert pg.locator("#traceWrap").is_visible()
    assert not pg.locator("#plotArea").is_visible()
    assert pg.locator("#traceTable").is_visible()
    # Switch to Report: it renders the synthesis.
    pg.locator("#viewReport").click()
    pg.wait_for_timeout(100)
    assert pg.locator("#reportPanel").is_visible()
    assert "frames" in pg.locator("#reportBody").inner_text().lower()
    # Back to Plots: the plotted selection is intact (state preserved).
    pg.locator("#viewPlots").click()
    assert pg.locator("#plotArea").is_visible()
    assert pg.evaluate("() => window.__ctd.selected.length") == selected_before
    ctx.close()


def test_trace_empty_state_for_no_matching_filter(browser, live_url):
    """A filter with no matches shows a distinct empty state (AC7)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    pg = ctx.new_page()
    pg.goto(live_url)
    pg.locator("#viewTrace").click()
    pg.locator("#fId").fill("ZZZZ")  # no id matches
    pg.wait_for_timeout(400)
    empty = pg.locator("#traceEmpty")
    assert empty.is_visible()
    assert "No matching rows" in empty.inner_text()
    # The active filter is shown as a removable chip that restores results.
    chip = pg.locator("#filterChips .chip")
    assert chip.count() >= 1
    chip.first.locator("button").click()
    pg.wait_for_timeout(400)
    assert not pg.locator("#traceEmpty").is_visible()
    ctx.close()


# --- opt-in cursor integral (req_032 AC1/AC2/AC6) ---------------------------
def _integral_requests(pg):
    return pg.evaluate("() => window.__ctd.integral.requests")


def _integral_value(pg):
    pg.wait_for_function(
        "() => { const o = document.getElementById('integralValue');"
        " return o && o.dataset.state && o.dataset.state !== 'pending'; }"
    )
    return pg.evaluate(
        "() => ({ text: document.getElementById('integralValue').textContent,"
        " state: document.getElementById('integralValue').dataset.state })"
    )


def _direct_integral(pg, sig_index, a, b):
    return pg.evaluate(
        """async ({i, a, b}) => {
            const s = state.selected[i];
            const q = new URLSearchParams({ message: s.message, signal: s.signal, a, b });
            const r = await api(`/api/signal-integral?${q}`);
            return `${fmtNum(r.integral)} ${r.unit}`;
        }""",
        {"i": sig_index, "a": a, "b": b},
    )


def test_integral_is_absent_and_request_free_until_enabled(page):
    network = []
    page.on("request", lambda r: network.append(r.url) if "signal-integral" in r.url else None)
    page.evaluate("() => { window.__ctd.placeCursor(6, 'a', false);"
                  " window.__ctd.placeCursor(14, 'b', false); }")
    page.locator("#cursorReadout th", has_text="Range analysis A–B").wait_for()
    page.wait_for_timeout(200)
    assert page.locator("#integralPanel").count() == 0
    assert "integral" not in page.locator("#cursorReadout").inner_text().lower()
    assert _integral_requests(page) == 0 and network == []
    btn = page.locator("#integralBtn")
    assert btn.is_visible() and btn.get_attribute("aria-pressed") == "false"


def test_integral_enable_follow_target_and_cursors_then_disable(page):
    page.evaluate("() => { window.__ctd.placeCursor(6, 'a', false);"
                  " window.__ctd.placeCursor(14, 'b', false); }")
    page.click("#integralBtn")
    assert page.get_attribute("#integralBtn", "aria-pressed") == "true"
    first = _integral_value(page)
    assert first["state"] == "ok"
    assert first["text"] == _direct_integral(page, 0, 6, 14)
    assert "trapezoidal" in page.locator("#integralMethod").inner_text()
    # Ordinary statistics keep rendering beside the integral.
    assert "mean" in page.locator("#cursorReadout thead").inner_text().lower()

    # Target switch.
    second_key = page.evaluate("() => favSig(state.selected[1])")
    page.select_option("#integralTarget", second_key)
    page.wait_for_function(
        "(t) => document.getElementById('integralValue').textContent === t",
        arg=_direct_integral(page, 1, 6, 14),
    )
    # Cursor movement (drag cursor B) follows the new bounds.
    page.evaluate("() => window.__ctd.setView(0, 20)")
    p_from = _canvas_pt(page, 14.0)
    p_to = _canvas_pt(page, 16.0)
    _drag(page, p_from["x"], p_from["y"], p_to["x"], p_from["y"])
    b = page.evaluate("() => window.__ctd.state.cursor.b")
    assert b == pytest.approx(16.0, abs=0.3)
    page.wait_for_function(
        "(t) => document.getElementById('integralValue').textContent === t",
        arg=_direct_integral(page, 1, 6, b),
    )
    # Missing cursor: a reason, not a stale value.
    page.click("#curClearBtn")
    assert "Place cursors" in _integral_value(page)["text"]

    page.click("#integralBtn")
    assert page.locator("#integralPanel").count() == 0
    before = _integral_requests(page)
    page.evaluate("() => { window.__ctd.placeCursor(5, 'a', false);"
                  " window.__ctd.placeCursor(9, 'b', false); }")
    page.wait_for_timeout(200)
    assert _integral_requests(page) == before
    assert not page._ctd_http_errors


def test_integral_is_keyboard_operable(page):
    page.evaluate("() => { window.__ctd.placeCursor(6, 'a', false);"
                  " window.__ctd.placeCursor(14, 'b', false); }")
    page.focus("#integralBtn")
    page.keyboard.press("Enter")
    assert _integral_value(page)["state"] == "ok"
    page.focus("#integralTarget")
    page.keyboard.press("ArrowDown")
    page.wait_for_function(
        "() => window.__ctd.integral.target === favSig(state.selected[1])"
    )
    page.focus("#integralBtn")
    page.keyboard.press("Space")
    assert page.locator("#integralPanel").count() == 0


def test_integral_rejects_stale_responses(page):
    page.evaluate("() => { window.__ctd.placeCursor(6, 'a', false);"
                  " window.__ctd.placeCursor(14, 'b', false); }")
    page.click("#integralBtn")
    _integral_value(page)
    # Delay the next integral response so a newer request overtakes it.
    page.evaluate(
        """() => {
            const original = window.fetch;
            window.__ctdDelayNext = true;
            window.fetch = function(input, init) {
                const url = String(input);
                if (url.includes('signal-integral') && window.__ctdDelayNext) {
                    window.__ctdDelayNext = false;
                    return new Promise((r) => setTimeout(r, 700)).then(() => original(input, init));
                }
                return original(input, init);
            };
        }"""
    )
    page.evaluate("() => window.__ctd.placeCursor(10, 'b', false)")   # delayed
    page.evaluate("() => window.__ctd.placeCursor(12, 'b', false)")   # fast, newer
    expected = _direct_integral(page, 0, 6, 12)
    page.wait_for_timeout(1000)
    assert page.locator("#integralValue").inner_text() == expected

    # A response arriving after disable never resurrects the result.
    page.evaluate(
        "() => { window.__ctdDelayNext = true; window.__ctd.placeCursor(11, 'b', false); }"
    )
    page.click("#integralBtn")
    page.wait_for_timeout(1000)
    assert page.locator("#integralPanel").count() == 0


def test_removing_the_target_or_reloading_disables_integral(page):
    page.evaluate("() => { window.__ctd.placeCursor(6, 'a', false);"
                  " window.__ctd.placeCursor(14, 'b', false); }")
    page.click("#integralBtn")
    _integral_value(page)
    page.evaluate("async () => { await toggleSignal(state.signals.find((s) =>"
                  " favSig({message: s.message_name, signal: s.signal_name})"
                  " === window.__ctd.integral.target), false); }")
    assert page.locator("#integralPanel").count() == 0
    assert page.get_attribute("#integralBtn", "aria-pressed") == "false"

    page.click("#integralBtn")
    _integral_value(page)
    page.reload()
    page.wait_for_function("() => typeof state !== 'undefined' && state.loaded")
    assert page.locator("#integralPanel").count() == 0
    assert page.evaluate("() => window.__ctd.integral.enabled") is False


# --- remembered DBC selection (req_032 AC4/AC5/AC6) --------------------------
def _serve(app):
    import uvicorn

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(f"{base}/api/status", timeout=1)
            return server, base
        except Exception:
            time.sleep(0.1)
    server.should_exit = True
    pytest.fail("uvicorn did not start")


def _load_via_picker(pg, trace, dbcs=()):
    pg.set_input_files("#traceFile", str(trace))
    if dbcs:
        pg.set_input_files("#dbcFiles", [str(p) for p in dbcs])
    with pg.expect_response(lambda r: "/api/import-files" in r.url) as resp:
        pg.click("#loadBtn")
    assert resp.value.status == 200, resp.value.text()
    pg.wait_for_function("() => window.__ctd.state.loaded && state.signals.length > 0")


def test_last_dbc_set_is_prechecked_after_reload_and_server_restart(browser, tmp_path):
    from cantracediag.api import create_app
    from cantracediag.workspace import Workspace

    fix = REPO / "tests" / "fixtures"
    root = tmp_path / "ws"
    server, base = _serve(create_app(Workspace(root, ephemeral=False)))
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    pg = ctx.new_page()
    try:
        pg.goto(base)
        pg.evaluate("() => localStorage.clear()")
        pg.reload()
        assert pg.evaluate("() => window.__ctd.pickedLibrary") == []   # first use
        _load_via_picker(pg, fix / "sample.asc", [fix / "sample.dbc", fix / "sample_body.dbc"])

        pg.reload()
        pg.wait_for_function("() => window.__ctd.pickedLibrary.length === 2")
        assert "2 DBC (2 from library)" in pg.locator("#picked").inner_text()

        # A new trace needs no DBC selection; the integral stays off for it.
        _load_via_picker(pg, fix / "sample_dec.asc")
        status = pg.evaluate("() => api('/api/status')")
        assert sorted(status["dbc_paths"]) == ["sample.dbc", "sample_body.dbc"]
        assert pg.locator("#integralPanel").count() == 0

        # Manual uncheck-all survives reopening and a background refresh.
        pg.click("#pickLibBtn")
        for box in pg.locator("#libList input[type=checkbox]").all():
            if box.is_checked():
                box.uncheck()
        pg.click("#libDone")
        pg.click("#pickLibBtn")
        assert not any(b.is_checked() for b in pg.locator("#libList input[type=checkbox]").all())
        pg.evaluate("() => window.__ctd.loadLibrary()")
        assert not any(b.is_checked() for b in pg.locator("#libList input[type=checkbox]").all())
        pg.click("#libDone")
        assert pg.evaluate("() => window.__ctd.pickedLibrary") == []

        # Server restart on the same workspace keeps the remembered set.
        server.should_exit = True
        time.sleep(0.5)
        server, base = _serve(create_app(Workspace(root, ephemeral=False)))
        pg.goto(base)
        pg.wait_for_function("() => window.__ctd.pickedLibrary.length === 2")

        # Purge clears library and remembered selection.
        pg.click("#pickLibBtn")
        pg.click("#libPurge")
        pg.reload()
        pg.wait_for_timeout(300)
        assert pg.evaluate("() => window.__ctd.pickedLibrary") == []
    finally:
        ctx.close()
        server.should_exit = True
