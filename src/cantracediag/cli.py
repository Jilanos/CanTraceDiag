"""Command-line entry point for CanTraceDiag."""

from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import typer

from cantracediag.dbc import DbcCatalog
from cantracediag.pipeline import import_trace

app = typer.Typer(help="Local analysis of CANalyzer ASC traces with DBC decoding.")


@app.command()
def info(
    trace: Path = typer.Argument(..., help="Path to a local .asc trace"),
    dbc: list[Path] = typer.Option([], "--dbc", "-d", help="Local DBC file(s)"),
) -> None:
    """Import a trace and print a summary without launching the UI."""
    store, result = import_trace(trace, list(dbc))
    s = result.summary
    typer.echo(f"Trace: {result.trace_path}  (base {result.asc_base})")
    typer.echo(f"DBC:   {', '.join(result.dbc_paths) or '(none)'}")
    typer.echo(
        f"Frames: {s['frames']}  decoded: {s['decoded_frames']}  "
        f"events: {s['events']}  unique ids: {s['unique_ids']}"
    )
    typer.echo(f"Time:   {s['start_s']}s .. {s['end_s']}s")
    if result.ambiguous_ids:
        typer.echo("Ambiguous ids across DBCs:")
        for frame_id, names in result.ambiguous_ids.items():
            typer.echo(f"  {hex(frame_id)}: {', '.join(names)}")
    store.close()


@app.command()
def signals(
    dbc: list[Path] = typer.Argument(..., help="Local DBC file(s) to inspect"),
) -> None:
    """List messages and signals available in the given DBC files."""
    catalog = DbcCatalog()
    for path in dbc:
        catalog.load(path)
    for sig in catalog.signals():
        unit = f" [{sig.unit}]" if sig.unit else ""
        typer.echo(f"{sig.message_name}.{sig.signal_name}{unit}  ({hex(sig.arbitration_id)})")


# -- serve helpers (unit-testable) -------------------------------------------
def is_wsl() -> bool:
    """True when running inside WSL (so we should open the Windows browser)."""
    if "microsoft" in os.environ.get("WSL_DISTRO_NAME", "").lower():
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def find_free_port(host: str, start: int, attempts: int = 50) -> int:
    """First free port at or after ``start`` (falls back to an ephemeral one)."""
    for candidate in range(start, start + attempts):
        if not port_in_use(host, candidate):
            return candidate
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def is_ctd_instance(host: str, port: int) -> bool:
    """True if a CanTraceDiag server already answers on host:port."""
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/status", timeout=1) as resp:
            import json

            return "loaded" in json.load(resp)
    except (urllib.error.URLError, OSError, ValueError):
        return False


def resolve_serve_target(host: str, port: int) -> tuple[str, int]:
    """Decide whether to start a new server or attach to a running one (AC3).

    Returns ``("attach", port)`` if a CanTraceDiag instance already answers on
    the requested port, ``("start", free_port)`` otherwise — picking another
    free port when the requested one is taken by something else.
    """
    if port_in_use(host, port):
        if is_ctd_instance(host, port):
            return "attach", port
        return "start", find_free_port(host, port + 1)
    return "start", port


def open_browser(url: str) -> None:
    """Open ``url`` in the user's browser, best-effort and never raising.

    Under WSL the Windows browser is launched via ``explorer.exe`` (falling back
    to ``wslview``); elsewhere the platform default is used. A failure here must
    never prevent the server from running (req_006 risk).
    """
    try:
        if is_wsl():
            for cmd in (["explorer.exe", url], ["wslview", url]):
                try:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except FileNotFoundError:
                    continue
        import webbrowser

        webbrowser.open(url)
    except Exception as exc:  # noqa: BLE001 - opening a browser is best-effort
        typer.echo(f"(could not open browser automatically: {exc})")


def _open_when_ready(host: str, port: int, url: str) -> None:
    for _ in range(100):
        if port_in_use(host, port):
            open_browser(url)
            return
        time.sleep(0.1)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host (localhost by default)"),
    port: int = typer.Option(8000, help="Preferred port (auto-selects if taken)"),
    open_ui: bool = typer.Option(
        False, "--open/--no-open", help="Open the UI in the browser once ready"
    ),
) -> None:
    """Launch the local web UI and query API."""
    import uvicorn

    action, port = resolve_serve_target(host, port)
    url = f"http://{host}:{port}"
    if action == "attach":
        typer.echo(f"CanTraceDiag is already running at {url}")
        if open_ui:
            open_browser(url)
        return

    typer.echo(f"CanTraceDiag UI on {url}")
    if open_ui:
        threading.Thread(target=_open_when_ready, args=(host, port, url), daemon=True).start()
    uvicorn.run("cantracediag.api:app", host=host, port=port, log_level="info")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
