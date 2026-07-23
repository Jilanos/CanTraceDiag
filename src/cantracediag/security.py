"""Local-first API hardening (AC10, AC11).

CanTraceDiag follows a Jupyter-style local security model:

* it binds to loopback by default;
* it rejects requests whose ``Host`` is not on an allowlist (DNS-rebinding
  defence) or whose ``Origin`` is cross-site;
* it requires a per-process session token on mutating endpoints in local mode,
  and on *every* API endpoint in LAN mode;
* it caps upload size via documented configuration;
* it never echoes local filesystem paths in error messages; and
* it disables server-side path import outside loopback unless explicitly
  re-enabled.

Configuration is read from the environment so both ``create_app()`` and the
``uvicorn`` import-string entrypoint resolve the same settings.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlsplit

# Hostnames that always denote this machine's loopback interface, plus the
# Starlette in-process host used by TestClient.
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "[::1]", "testserver"})

_DEFAULT_MAX_UPLOAD_MB = 512.0


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def host_of(value: str | None) -> str | None:
    """Bare hostname of a ``Host`` header value (``host:port`` -> ``host``)."""
    if not value:
        return None
    value = value.strip()
    # IPv6 literal like ``[::1]:8000`` — keep the bracketed form used in the
    # allowlist, drop only a trailing ``:port`` outside the brackets.
    if value.startswith("["):
        end = value.find("]")
        if end != -1:
            return value[: end + 1]
        return value
    return value.rsplit(":", 1)[0] if ":" in value else value


def host_of_origin(origin: str | None) -> str | None:
    """Bare hostname of an ``Origin`` header (a full URL)."""
    if not origin:
        return None
    parsed = urlsplit(origin)
    if not parsed.hostname:
        return None
    # urlsplit strips the brackets of an IPv6 host; restore them to match the
    # allowlist form.
    host = parsed.hostname
    return f"[{host}]" if ":" in host else host


@dataclass(slots=True)
class SecurityConfig:
    """Resolved security posture for one server process."""

    lan: bool
    token: str
    allowed_hosts: frozenset[str]
    max_upload_bytes: int
    allow_server_import: bool

    @classmethod
    def from_env(cls) -> SecurityConfig:
        lan = _flag("CANTRACEDIAG_LAN")
        token = os.environ.get("CANTRACEDIAG_TOKEN") or secrets.token_urlsafe(24)

        allowed: set[str] = set(LOOPBACK_HOSTS)
        bind_host = os.environ.get("CANTRACEDIAG_HOST", "").strip()
        if bind_host and bind_host != "0.0.0.0":  # noqa: S104 - compared, not bound
            allowed.add(bind_host)
        for extra in os.environ.get("CANTRACEDIAG_ALLOWED_HOSTS", "").split(","):
            if extra.strip():
                allowed.add(extra.strip())

        try:
            mb = float(os.environ.get("CANTRACEDIAG_MAX_UPLOAD_MB", _DEFAULT_MAX_UPLOAD_MB))
        except ValueError:
            mb = _DEFAULT_MAX_UPLOAD_MB
        max_upload_bytes = max(1, int(mb * 1024 * 1024))

        # Server-side path import (arbitrary local file read) is allowed on
        # loopback by default and disabled in LAN unless explicitly re-enabled.
        if "CANTRACEDIAG_ALLOW_SERVER_IMPORT" in os.environ:
            allow_server_import = _flag("CANTRACEDIAG_ALLOW_SERVER_IMPORT")
        else:
            allow_server_import = not lan

        return cls(
            lan=lan,
            token=token,
            allowed_hosts=frozenset(allowed),
            max_upload_bytes=max_upload_bytes,
            allow_server_import=allow_server_import,
        )

    def host_allowed(self, host_header: str | None) -> bool:
        host = host_of(host_header)
        return host is not None and host in self.allowed_hosts

    def origin_allowed(self, origin_header: str | None) -> bool:
        if origin_header is None:
            return True
        return host_of_origin(origin_header) in self.allowed_hosts

    def token_ok(self, provided: str | None) -> bool:
        if not provided:
            return False
        return secrets.compare_digest(provided, self.token)

    def requires_token(self, path: str, method: str) -> bool:
        """Whether a request must carry a valid token.

        LAN mode protects the whole API and the app shell (so the token must be
        supplied to reach anything); local mode protects only mutating API
        endpoints.
        """
        if self.lan:
            return path.startswith("/api/") or path == "/"
        if path.startswith("/api/"):
            return method.upper() not in {"GET", "HEAD", "OPTIONS"}
        return False
