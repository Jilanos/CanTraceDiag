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

    req = urllib.request.Request(
        f"{base}/api/import",
        data=json.dumps(
            {
                "trace_path": str(trace),
                "dbc_paths": [str(REPO / "tests" / "fixtures" / "sample.dbc")],
            }
        ).encode(),
        # Mutating endpoints require the session token (AC10); read it from the
        # live app the server was built from.
        headers={"Content-Type": "application/json",
                 "X-CTD-Token": app.state.ctd_security.token},
    )
    summary = json.load(urllib.request.urlopen(req))["summary"]
    assert summary["frames"] == 8000

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
    pg.wait_for_function("() => typeof state !== 'undefined' && state.signals.length === 1")
    pg.wait_for_selector("#traceTable tbody tr")
    pg.wait_for_timeout(200)
    assert pg.evaluate("() => window.__ctdXss") == 0
    assert "<img src=x onerror=window.__ctdXss=1>" in pg.locator("#traceTable").inner_text()
    assert "<svg/onload=window.__ctdXss=2>" in pg.locator("#signalList").inner_text()
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
    # Minimal 390x844 support: import, load, main filters, tab/section and export
    # stay reachable within the viewport (AC14).
    for selector in ["#pickTraceBtn", "#loadBtn", "#fId", "#exportBtn", "#reportBtn"]:
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
        for selector in ["#loadBtn", "#exportBtn", "#reportBtn", "#fId", "#colBtn"]:
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
    pg.locator("#colBtn").click()
    assert pg.locator("#colDialog").evaluate("d => d.open") is True
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(50)
    assert pg.locator("#colDialog").evaluate("d => d.open") is False
    ctx.close()
