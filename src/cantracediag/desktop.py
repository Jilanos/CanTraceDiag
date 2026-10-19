"""Entry point of the standalone Windows executable (req_034 AC5, AC7).

``CanTraceDiag.exe`` bundles the local Python/FastAPI service and the static UI.
Double-clicking it:

1. resolves per-user directories outside any clone (``%LOCALAPPDATA%\\CanTraceDiag``:
   ``data`` for the DBC library, analyses and upload staging, ``logs`` for the
   service log, ``instance.json`` for the running instance);
2. reopens the browser on an already running instance of the *same* version,
   or refuses explicitly when another version is running;
3. otherwise binds a loopback-only port (the preferred one, or the next free one
   when it is occupied), starts the service and opens the default browser once
   ``/api/status`` answers.

The console window is the stop action: closing it, or pressing Ctrl+C, stops the
service. ``CanTraceDiag.exe --stop`` stops a running instance from elsewhere.
Nothing here depends on WSL, a Python installation or administrator rights.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from cantracediag import __version__

APP_NAME = "CanTraceDiag"
LOOPBACK = "127.0.0.1"
DEFAULT_PORT = 8000
READY_TIMEOUT_S = 120.0

log = logging.getLogger("cantracediag.desktop")


@dataclass(slots=True)
class Paths:
    root: Path
    data: Path
    logs: Path
    instance: Path

    @classmethod
    def resolve(cls, override: Path | None = None) -> Paths:
        if override is not None:
            root = override
        elif os.name == "nt" and os.environ.get("LOCALAPPDATA"):
            root = Path(os.environ["LOCALAPPDATA"]) / APP_NAME
        else:
            xdg = os.environ.get("XDG_STATE_HOME")
            root = (Path(xdg) if xdg else Path.home() / ".local" / "state") / "cantracediag"
        return cls(root, root / "data", root / "logs", root / "instance.json")


# -- running instance discovery ---------------------------------------------


def read_instance(paths: Paths) -> dict | None:
    try:
        data = json.loads(paths.instance.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("port"), int) else None


def write_instance(paths: Paths, port: int, token: str) -> None:
    payload = {"pid": os.getpid(), "port": port, "version": __version__, "token": token}
    tmp = paths.instance.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, paths.instance)


def clear_instance(paths: Paths, port: int) -> None:
    current = read_instance(paths)
    if current is not None and current.get("port") == port and current.get("pid") == os.getpid():
        paths.instance.unlink(missing_ok=True)


def probe_version(port: int, timeout: float = 1.5) -> str | None:
    """Version reported by a CanTraceDiag service on ``port``, or None."""
    try:
        with urllib.request.urlopen(
            f"http://{LOOPBACK}:{port}/api/status", timeout=timeout
        ) as resp:
            body = json.load(resp)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    if not isinstance(body, dict) or "loaded" not in body:
        return None
    return str(body.get("version") or "unknown")


def request_stop(port: int, token: str) -> bool:
    req = urllib.request.Request(
        f"http://{LOOPBACK}:{port}/api/shutdown",
        method="POST",
        headers={"X-CTD-Token": token},
        data=b"",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            return True
    except (urllib.error.URLError, OSError):
        return False


# -- logging -----------------------------------------------------------------


def configure_logging(paths: Paths) -> Path:
    paths.logs.mkdir(parents=True, exist_ok=True)
    log_file = paths.logs / "cantracediag.log"
    handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3,
                                  encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)  # uvicorn's loggers propagate here (log_config=None)
    return log_file


def say(message: str) -> None:
    print(message, flush=True)
    log.info(message)


# -- main --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Standalone local CanTraceDiag service with the browser UI.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="preferred loopback port (the next free one is used if taken)")
    parser.add_argument("--no-browser", action="store_true",
                        help="do not open the browser once the service is ready")
    parser.add_argument("--home", type=Path, default=None,
                        help="per-user directory for data, logs and instance file")
    parser.add_argument("--stop", action="store_true", help="stop the running instance")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = Paths.resolve(args.home)
    paths.root.mkdir(parents=True, exist_ok=True)
    log_file = configure_logging(paths)

    instance = read_instance(paths)
    running = probe_version(instance["port"]) if instance else None

    if args.stop:
        if instance is None or running is None:
            say("No running CanTraceDiag instance.")
            return 0
        ok = request_stop(instance["port"], str(instance.get("token", "")))
        say("CanTraceDiag stopped." if ok else "Could not stop the running instance.")
        return 0 if ok else 1

    if instance is not None and running is not None:
        url = f"http://{LOOPBACK}:{instance['port']}/"
        if running == __version__:
            say(f"CanTraceDiag {running} is already running at {url}")
            if not args.no_browser:
                _open_browser(url)
            return 0
        say(
            f"CanTraceDiag {running} is already running at {url}, but this is "
            f"version {__version__}. Close the other CanTraceDiag window (or run "
            f"'{APP_NAME}.exe --stop'), then start this version again."
        )
        _pause_if_double_clicked()
        return 3
    if instance is not None:
        paths.instance.unlink(missing_ok=True)  # stale: its process is gone

    return serve(paths, args.port, open_browser=not args.no_browser, log_file=log_file)


def serve(paths: Paths, preferred_port: int, *, open_browser: bool, log_file: Path) -> int:
    import secrets

    paths.data.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CANTRACEDIAG_DATA_DIR", str(paths.data))
    os.environ["CANTRACEDIAG_LAN"] = "0"
    os.environ.setdefault("CANTRACEDIAG_TOKEN", secrets.token_urlsafe(24))
    token = os.environ["CANTRACEDIAG_TOKEN"]

    sock = bind_loopback(preferred_port)
    port = sock.getsockname()[1]
    if port != preferred_port:
        say(f"Port {preferred_port} is unavailable; using {port} instead.")

    say(f"CanTraceDiag {__version__} starting (loopback only)...")
    say(f"Data: {paths.data}")
    say(f"Log:  {log_file}")

    import uvicorn

    from cantracediag.api import create_app

    app = create_app()
    config = uvicorn.Config(app, host=LOOPBACK, port=port, log_level="info",
                            log_config=None, access_log=False)
    server = uvicorn.Server(config)
    app.state.ctd_shutdown = lambda: setattr(server, "should_exit", True)

    url = f"http://{LOOPBACK}:{port}/"

    def _when_ready() -> None:
        deadline = time.monotonic() + READY_TIMEOUT_S
        while time.monotonic() < deadline and not server.should_exit:
            if probe_version(port, timeout=1.0) == __version__:
                write_instance(paths, port, token)
                say(f"Ready: {url}")
                say("Keep this window open while you work. Close it (or press "
                    "Ctrl+C) to stop CanTraceDiag.")
                if open_browser:
                    _open_browser(url)
                return
            time.sleep(0.2)

    threading.Thread(target=_when_ready, daemon=True).start()
    try:
        server.run(sockets=[sock])
    finally:
        clear_instance(paths, port)
        say("CanTraceDiag stopped.")
    return 0


def bind_loopback(preferred: int, attempts: int = 50) -> socket.socket:
    """A listening-ready loopback socket on ``preferred`` or the next usable port.

    The port is reserved by actually binding it rather than by probing with a
    connect: on Windows a port can look free yet sit in a range reserved by
    Hyper-V/WSL (bind fails with WinError 10013), and probing first would also
    race with other processes. The bound socket is handed to uvicorn as is.
    """
    for candidate in range(preferred, preferred + attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if os.name == "nt":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind((LOOPBACK, candidate))
        except OSError:
            sock.close()
            continue
        return sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((LOOPBACK, 0))
    return sock


def _open_browser(url: str) -> None:
    import webbrowser

    try:
        webbrowser.open(url)
    except Exception as exc:  # noqa: BLE001 - opening a browser is best-effort
        say(f"Open {url} in your browser (automatic opening failed: {exc}).")


def _pause_if_double_clicked() -> None:
    """Keep a double-clicked console open long enough to read the message."""
    if os.name == "nt" and getattr(sys, "frozen", False):
        try:
            input("Press Enter to close this window.")
        except EOFError:
            pass


if __name__ == "__main__":
    sys.exit(main())
