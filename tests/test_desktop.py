"""Standalone launcher lifecycle (req_034 AC7): start, reopen, version clash, stop."""

from __future__ import annotations

import json
import logging
import logging.handlers
import socket
import threading
import time
from pathlib import Path

import pytest

from cantracediag import __version__, desktop


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch):
    for name in ("CANTRACEDIAG_DATA_DIR", "CANTRACEDIAG_TOKEN", "CANTRACEDIAG_LAN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(desktop, "_open_browser", lambda url: None)
    yield
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            root.removeHandler(handler)
            handler.close()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(predicate, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise AssertionError("condition not met in time")


def test_start_reopen_and_stop(tmp_path: Path, capsys) -> None:
    home = tmp_path / "Per user é dir"
    port = _free_port()
    result: list[int] = []
    worker = threading.Thread(
        target=lambda: result.append(desktop.main(["--home", str(home), "--port", str(port),
                                                   "--no-browser"])),
        daemon=True,
    )
    worker.start()
    paths = desktop.Paths.resolve(home)
    _wait_for(lambda: desktop.read_instance(paths) is not None)
    instance = desktop.read_instance(paths)
    assert instance["port"] == port and instance["version"] == __version__
    assert (paths.logs / "cantracediag.log").is_file()

    # A second launch of the same version attaches instead of starting again.
    assert desktop.main(["--home", str(home), "--no-browser"]) == 0
    assert "already running" in capsys.readouterr().out

    assert desktop.main(["--home", str(home), "--stop"]) == 0
    worker.join(timeout=30)
    assert not worker.is_alive()
    assert result == [0]
    assert desktop.read_instance(paths) is None


def test_occupied_port_falls_back_to_next_free(tmp_path: Path) -> None:
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        taken = blocker.getsockname()[1]
        worker = threading.Thread(
            target=desktop.main,
            args=(["--home", str(tmp_path), "--port", str(taken), "--no-browser"],),
            daemon=True,
        )
        worker.start()
        paths = desktop.Paths.resolve(tmp_path)
        _wait_for(lambda: desktop.read_instance(paths) is not None)
        assert desktop.read_instance(paths)["port"] != taken
        assert desktop.main(["--home", str(tmp_path), "--stop"]) == 0
        worker.join(timeout=30)


def test_incompatible_running_version_is_refused(tmp_path: Path, monkeypatch, capsys) -> None:
    paths = desktop.Paths.resolve(tmp_path)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.instance.write_text(json.dumps({"pid": 1, "port": 1, "version": "0.0.1", "token": "t"}))
    monkeypatch.setattr(desktop, "probe_version", lambda port, timeout=1.5: "0.0.1")
    assert desktop.main(["--home", str(tmp_path), "--no-browser"]) == 3
    out = capsys.readouterr().out
    assert "0.0.1 is already running" in out and "--stop" in out


def test_stale_instance_file_is_discarded(tmp_path: Path, monkeypatch) -> None:
    paths = desktop.Paths.resolve(tmp_path)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.instance.write_text(json.dumps({"pid": 1, "port": 1, "version": "x", "token": "t"}))
    monkeypatch.setattr(desktop, "probe_version", lambda port, timeout=1.5: None)
    assert desktop.main(["--home", str(tmp_path), "--stop"]) == 0
    called: list[int] = []
    monkeypatch.setattr(desktop, "serve", lambda *a, **k: called.append(1) or 0)
    assert desktop.main(["--home", str(tmp_path), "--no-browser"]) == 0
    assert called == [1]
    assert not paths.instance.exists()


def test_shutdown_endpoint_absent_without_hook(client) -> None:
    assert client.post("/api/shutdown").status_code == 404
