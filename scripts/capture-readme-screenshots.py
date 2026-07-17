"""Generate README screenshots from the real local UI.

The script starts the FastAPI app on a free localhost port, imports the
synthetic test fixture, drives Chromium through Playwright, and writes stable
PNG captures under docs/assets.
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "assets"

_LOCAL_LIBS = REPO / ".pw-libs" / "extracted" / "usr" / "lib" / "x86_64-linux-gnu"
if _LOCAL_LIBS.is_dir():
    os.environ["LD_LIBRARY_PATH"] = (
        str(_LOCAL_LIBS) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
    )


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(base_url: str) -> None:
    for _ in range(100):
        try:
            urllib.request.urlopen(f"{base_url}/api/status", timeout=1)
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("uvicorn did not start")


def _import_fixture(base_url: str) -> None:
    trace = OUT / "readme-sample.asc"
    _write_synth_asc(trace)
    req = urllib.request.Request(
        f"{base_url}/api/import",
        data=json.dumps(
            {
                "trace_path": str(trace),
                "dbc_paths": [str(REPO / "tests" / "fixtures" / "sample.dbc")],
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10).read()


def _write_synth_asc(path: Path) -> None:
    """A compact, decodable trace for documentation screenshots."""
    lines = [
        "date Tue Jul 15 10:00:00 2026",
        "base hex  timestamps absolute",
        "internal events logged",
        "// version 8.5.0",
        "Begin Triggerblock Tue Jul 15 10:00:00 2026",
    ]
    t, i = 0.0, 0
    while t <= 8.0:
        speed = int((2200 + 1400 * (i % 160) / 160) / 0.25) & 0xFFFF
        temp = (70 + (i % 45)) & 0xFF
        data = [speed & 0xFF, (speed >> 8) & 0xFF, temp, 0, 0, 0, 0, 0]
        lines.append(
            f"   {t:.6f} 1  100             Rx   d 8 "
            + " ".join(f"{value:02X}" for value in data)
        )
        vehicle_speed = int((35 + 22 * (i % 80) / 80) / 0.01) & 0xFFFF
        data2 = [vehicle_speed & 0xFF, (vehicle_speed >> 8) & 0xFF]
        lines.append(
            f"   {t + 0.002:.6f} 1  200             Rx   d 2 "
            + " ".join(f"{value:02X}" for value in data2)
        )
        if i in {200, 900, 1300}:
            lines.append(f"   {t + 0.003:.6f} 1  ErrorFrame")
        t += 0.006
        i += 1
    lines.append("End Triggerblock")
    path.write_text("\n".join(lines) + "\n")


def _start_server() -> tuple[str, object]:
    import uvicorn

    os.environ["CANTRACEDIAG_EPHEMERAL"] = "1"
    from cantracediag.api import create_app
    from cantracediag.workspace import Workspace

    port = _free_port()
    app = create_app(Workspace(Path(tempfile.mkdtemp(prefix="ctd_readme_")), ephemeral=True))
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    _wait_for_server(base_url)
    _import_fixture(base_url)
    return base_url, server


def _prepare_loaded_page(page, base_url: str) -> None:
    page.goto(base_url)
    page.evaluate("() => localStorage.clear()")
    page.reload()
    page.wait_for_function("() => typeof state !== 'undefined' && state.signals.length >= 2")
    page.evaluate(
        """async () => {
            await toggleSignal(state.signals[0], true);
            await toggleSignal(state.signals[1], true);
            setView(0, 0.35);
            placeCursor(0.1, "a", false);
            placeCursor(0.25, "b", false);
            const row = document.querySelector("#traceTable tbody tr.expandable");
            if (row) row.click();
        }"""
    )
    page.wait_for_timeout(500)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base_url, server = _start_server()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=1, viewport={"width": 1600, "height": 940})
            _prepare_loaded_page(page, base_url)

            page.screenshot(path=OUT / "cantracediag-workspace.png", full_page=True)
            page.locator("#plotArea").screenshot(path=OUT / "cantracediag-cursors.png")

            page.locator("#colBtn").click()
            page.locator("#colDialog").screenshot(path=OUT / "cantracediag-columns.png")
            page.locator("#colDialog").evaluate("(dialog) => dialog.close()")

            page.locator("#pickLibBtn").click()
            page.locator("#libDialog").screenshot(path=OUT / "cantracediag-library.png")
            browser.close()
    finally:
        server.should_exit = True


if __name__ == "__main__":
    main()
