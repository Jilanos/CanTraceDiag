"""Shared test configuration.

Force an *ephemeral* workspace for the whole suite so tests never write into the
real user profile (`~/.local/share/cantracediag/`) and keep the pre-workspace
behaviour by default (AC9, AC10). This is set at import time — before any test
module imports ``cantracediag.api`` and builds its module-level app — so the
default app also resolves to an ephemeral workspace. Tests that exercise
persistence construct their own ``Workspace`` with a tmp path explicitly.
"""

from __future__ import annotations

import os

os.environ.setdefault("CANTRACEDIAG_EPHEMERAL", "1")

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402 - after the env default is set
from starlette.testclient import TestClient  # noqa: E402

from cantracediag.api import create_app  # noqa: E402


def make_client(app: FastAPI | None = None) -> TestClient:
    """Client that talks to a loopback Host and carries the session token (AC10).

    Tests exercise the app the way the shipped UI does: from an allowed Host,
    same-origin, and authenticated. Hostile tests build their own bare client to
    assert the rejections.
    """
    app = app or create_app()
    token = app.state.ctd_security.token
    return TestClient(app, base_url="http://localhost", headers={"X-CTD-Token": token})


@pytest.fixture
def client() -> TestClient:
    return make_client()
