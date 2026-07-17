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
from argparse import ArgumentParser, Namespace
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


def _start_server() -> tuple[str, object | None]:
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


def _prepare_loaded_page(page, base_url: str, *, live_poc3: bool) -> None:
    page.goto(base_url)
    page.evaluate("() => localStorage.clear()")
    page.reload()
    page.wait_for_function("() => typeof state !== 'undefined' && state.signals.length >= 2")
    if live_poc3:
        page.evaluate(
            """async () => {
                const picks = [
                    { message: "Edrv_Act_1", signal: "Edrv_tqAct" },
                    { message: "Ecran1", signal: "Vitesse" },
                ];
                state.selected = [];
                store.set("selected", []);
                for (const id of ["fId", "fSignal", "fStart", "fEnd"]) {
                    document.getElementById(id).value = "";
                }
                document.getElementById("fMsg").value = "Edrv_Act_1";
                document.getElementById("fDir").value = "";
                document.getElementById("fStatus").value = "";
                document.getElementById("fEvent").value = "";
                document.getElementById("showFrames").checked = true;
                document.getElementById("showEvents").checked = false;
                setView(1200, 1230);
                await new Promise((resolve) => setTimeout(resolve, 150));
                for (const pick of picks) {
                    const sig = state.signals.find(
                        (s) => s.message_name === pick.message && s.signal_name === pick.signal
                    );
                    if (!sig) throw new Error(`Missing signal ${pick.message}.${pick.signal}`);
                    await toggleSignal(sig, true);
                }
                setView(1200, 1230);
                await fetchAllSeries();
                await locateInTrace(1204);
                const row = document.querySelector("#traceTable tbody tr.selected")
                    || document.querySelector("#traceTable tbody tr.expandable");
                if (row) row.click();
                await new Promise((resolve) => setTimeout(resolve, 400));
                state.cursor.a = 1204;
                state.cursor.b = 1222;
                await refreshCursorReadout();
                const aliases = [
                    ["Edrv_Act_1", "Powertrain"],
                    ["Edrv_tqAct", "MotorTorque"],
                    ["Edrv_nAct", "MotorSpeed"],
                    ["Edrv_iAct", "MotorCurrent"],
                    ["Edrv_uAct", "MotorVoltage"],
                    ["Edrv_stOperModAct", "OperatingMode"],
                    ["Edrv_stRunAct", "RunState"],
                    ["Edrv_nrAlvCntrAct", "Counter"],
                    ["Edrv_nrChksAct", "Checksum"],
                    ["Ecran1", "Vehicle"],
                    ["Vitesse", "VehicleSpeed"],
                    ["SEG_v3.dbc", "powertrain.dbc"],
                    ["IHM_TopCon_Circle_v4.dbc", "vehicle.dbc"],
                    ["2026-06-11_13-24-28_T085_Poc3_SBS_SEG.asc", "road-test-segment.asc"],
                ];
                state.selected[0].message = "Powertrain";
                state.selected[0].signal = "MotorTorque";
                state.selected[0].unit = "Nm";
                state.selected[1].message = "Vehicle";
                state.selected[1].signal = "VehicleSpeed";
                state.selected[1].unit = "km/h";
                renderPlot();
                document.getElementById("fMsg").value = "Powertrain";
                document.getElementById("signalList").innerHTML = `
                    <div class="grp">ANONYMIZED DATA</div>
                    <label class="sig on" style="--sw:${state.selected[0].color}">
                        <span class="star">★</span><input type="checkbox" checked/>
                        <span class="swatch" style="background:${state.selected[0].color}"></span>
                        <span class="name">Powertrain.<b>MotorTorque</b></span>
                        <span class="unit">Nm</span>
                    </label>
                    <label class="sig on" style="--sw:${state.selected[1].color}">
                        <span class="star">★</span><input type="checkbox" checked/>
                        <span class="swatch" style="background:${state.selected[1].color}"></span>
                        <span class="name">Vehicle.<b>VehicleSpeed</b></span>
                        <span class="unit">km/h</span>
                    </label>`;
                document.getElementById("inspBody").innerHTML = `
                    <div class="insp-id">0A3</div>
                    <div class="insp-msg">Powertrain · powertrain.dbc</div>
                    <div class="insp-raw">D9 4E 17 D4 F7 DD 59 F4</div>
                    <dl class="insp-grid">
                        <dt>Timestamp</dt><dd>1204.000000 s</dd>
                        <dt>Channel</dt><dd>1</dd>
                        <dt>Direction</dt><dd>Rx</dd>
                        <dt>DLC</dt><dd>8</dd>
                        <dt>Decode status</dt><dd>ok</dd>
                    </dl>
                    <div class="insp-sec">Decoded signals</div>
                    <div class="insp-sig">
                        <span>MotorTorque</span><span class="v">14.1 Nm</span>
                    </div>
                    <div class="insp-sig">
                        <span>MotorSpeed</span><span class="v">2580 rpm</span>
                    </div>`;
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                const nodes = [];
                while (walker.nextNode()) nodes.push(walker.currentNode);
                for (const node of nodes) {
                    let text = node.nodeValue;
                    for (const [from, to] of aliases) text = text.replaceAll(from, to);
                    node.nodeValue = text;
                }
            }"""
        )
        page.wait_for_timeout(500)
        return

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


def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--url",
        help="Reuse an already running CanTraceDiag server instead of starting a fixture server.",
    )
    parser.add_argument(
        "--live-poc3",
        action="store_true",
        help="Capture the loaded POC3 trace with anonymized signal names.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.url:
        base_url, server = args.url.rstrip("/"), None
    else:
        base_url, server = _start_server()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=1, viewport={"width": 1600, "height": 940})
            _prepare_loaded_page(page, base_url, live_poc3=args.live_poc3)

            page.screenshot(path=OUT / "cantracediag-workspace.png", full_page=True)
            page.locator("#plotArea").screenshot(path=OUT / "cantracediag-cursors.png")

            page.locator("#colBtn").click()
            page.locator("#colDialog").screenshot(path=OUT / "cantracediag-columns.png")
            page.locator("#colDialog").evaluate("(dialog) => dialog.close()")

            page.locator("#pickLibBtn").click()
            if args.live_poc3:
                page.evaluate(
                    """() => {
                        const list = document.querySelector("#libList");
                        if (!list) return;
                        list.innerHTML = "";
                        for (const name of [
                            "powertrain.dbc",
                            "vehicle.dbc",
                            "body-control.dbc",
                            "energy-system.dbc",
                        ]) {
                            const row = document.createElement("label");
                            row.className = "lib-row";
                            row.innerHTML =
                                `<input type="checkbox" checked/>` +
                                `<span class="lname">${name}</span>` +
                                `<span class="lmeta">cached</span>`;
                            list.appendChild(row);
                        }
                    }"""
                )
            page.locator("#libDialog").screenshot(path=OUT / "cantracediag-library.png")
            browser.close()
    finally:
        if server is not None:
            server.should_exit = True


if __name__ == "__main__":
    main()
