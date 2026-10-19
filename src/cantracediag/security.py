"""Local-first API hardening (AC10, AC11).

CanTraceDiag follows a Jupyter-style local security model:

* it binds to loopback by default;
* it rejects requests whose ``Host`` is not on an allowlist (DNS-rebinding
  defence) or whose ``Origin`` is cross-site;
* it requires a per-process session token on mutating endpoints in local mode,
  and on *every* API endpoint in LAN mode;
* it caps upload size via documented configuration: an inclusive per-trace
  cap, an independent aggregate DBC cap and a multipart-envelope allowance,
  whose sum bounds the whole request (see :class:`UploadLimits`);
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

MIB = 1024 * 1024

# Local (loopback) defaults: a full 1 GiB trace is accepted *inclusively*, and
# uploaded DBCs and the multipart envelope get their own budgets on top of it so
# neither eats into the trace allowance (req_034 AC1).
DEFAULT_MAX_TRACE_BYTES = 1024 * MIB
DEFAULT_MAX_DBC_BYTES = 64 * MIB
DEFAULT_ENVELOPE_BYTES = 8 * MIB
# Historical aggregate cap. LAN deployments keep it unless an administrator
# explicitly raises a limit, so the new local default never silently widens what
# a network-exposed server accepts.
LEGACY_MAX_UPLOAD_BYTES = 512 * MIB


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


def _bytes_env(name_mb: str) -> int | None:
    """Positive byte count from a ``*_MB`` variable (fractions allowed), or None."""
    raw = os.environ.get(name_mb)
    if raw is None or not raw.strip():
        return None
    try:
        mb = float(raw)
    except ValueError:
        return None
    return max(1, int(mb * MIB)) if mb > 0 else None


@dataclass(frozen=True, slots=True)
class UploadLimits:
    """Byte budgets enforced while a browser upload streams in.

    ``trace`` is inclusive (a trace of exactly ``trace`` bytes is accepted),
    ``dbc`` bounds the *sum* of uploaded DBC files, and ``envelope`` bounds the
    multipart framing plus non-file form fields. ``request`` bounds the whole
    body and defaults to the sum of the three.
    """

    trace: int = DEFAULT_MAX_TRACE_BYTES
    dbc: int = DEFAULT_MAX_DBC_BYTES
    envelope: int = DEFAULT_ENVELOPE_BYTES
    request: int | None = None

    @property
    def max_request(self) -> int:
        if self.request is not None:
            return self.request
        return self.trace + self.dbc + self.envelope

    @classmethod
    def uniform(cls, max_bytes: int) -> UploadLimits:
        """Every budget (and the whole request) capped at ``max_bytes``."""
        return cls(trace=max_bytes, dbc=max_bytes, envelope=max_bytes, request=max_bytes)

    @classmethod
    def from_env(cls, lan: bool) -> UploadLimits:
        """Resolve the limits from the environment.

        ``CANTRACEDIAG_MAX_TRACE_MB``, ``CANTRACEDIAG_MAX_DBC_MB`` and
        ``CANTRACEDIAG_MAX_ENVELOPE_MB`` set each budget. The historical
        ``CANTRACEDIAG_MAX_UPLOAD_MB``, when set, stays an administrator cap on
        the whole request (and therefore on the trace). Without any explicit
        setting, LAN mode keeps the historical 512 MiB aggregate cap.
        """
        trace = _bytes_env("CANTRACEDIAG_MAX_TRACE_MB")
        dbc = _bytes_env("CANTRACEDIAG_MAX_DBC_MB")
        envelope = _bytes_env("CANTRACEDIAG_MAX_ENVELOPE_MB")
        aggregate = _bytes_env("CANTRACEDIAG_MAX_UPLOAD_MB")
        explicit = any(v is not None for v in (trace, dbc, envelope, aggregate))
        if lan and not explicit:
            aggregate = LEGACY_MAX_UPLOAD_BYTES
        limits = cls(
            trace=trace or DEFAULT_MAX_TRACE_BYTES,
            dbc=dbc or DEFAULT_MAX_DBC_BYTES,
            envelope=envelope or DEFAULT_ENVELOPE_BYTES,
        )
        if aggregate is not None:
            limits = cls(
                trace=min(limits.trace, aggregate),
                dbc=min(limits.dbc, aggregate),
                envelope=limits.envelope,
                request=aggregate,
            )
        return limits


@dataclass(slots=True)
class SecurityConfig:
    """Resolved security posture for one server process."""

    lan: bool
    token: str
    allowed_hosts: frozenset[str]
    upload_limits: UploadLimits
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
            upload_limits=UploadLimits.from_env(lan),
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
