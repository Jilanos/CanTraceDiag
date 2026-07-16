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
