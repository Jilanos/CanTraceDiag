"""CLI serve helpers: auto-port and instance detection (req_006, AC3)."""

from __future__ import annotations

import socket

from cantracediag.cli import find_free_port, port_in_use, resolve_serve_target


def test_free_port_when_requested_is_taken() -> None:
    host = "127.0.0.1"
    # Occupy a port with a non-CanTraceDiag listener.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind((host, 0))
        busy.listen()
        taken = busy.getsockname()[1]
        assert port_in_use(host, taken)

        action, chosen = resolve_serve_target(host, taken)
        # A stranger holds the port -> start on a different, free port.
        assert action == "start"
        assert chosen != taken
        assert not port_in_use(host, chosen)


def test_free_port_returns_requested_when_available() -> None:
    host = "127.0.0.1"
    free = find_free_port(host, 8137)
    action, chosen = resolve_serve_target(host, free)
    assert action == "start"
    assert chosen == free
