"""Persistent local workspace for CanTraceDiag (ADR 0006).

The workspace lets an operator relaunch the tool and immediately find the last
analysis and previously used DBC files, instead of re-uploading everything into
a throwaway ``tempfile`` directory each session.

Layout under the user data root (``$CANTRACEDIAG_DATA_DIR`` or
``$XDG_DATA_HOME/cantracediag`` or ``~/.local/share/cantracediag``)::

    dbc/
        index.json                 # {digest: {name, first_seen, last_used}}
        <digest>/<original_name>   # library DBC files, deduplicated by content
    analysis/
        <uuid>/analysis.duckdb     # indexed acquisitions (only the latest kept)
    last-analysis.json             # manifest describing the latest analysis

Everything stays outside the repository (ADR 0004). An *ephemeral* workspace
keeps the pre-workspace behaviour (throwaway temp dirs, nothing persisted); it
is what the test-suite uses so it never writes into the real user profile.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Bump when the persisted layout or DuckDB schema changes in a way that makes an
# older analysis unreadable; a manifest with a different version is ignored on
# restore rather than opened (AC7).
SCHEMA_VERSION = 1

DEFAULT_DBC_CAP = 20


def default_data_root() -> Path:
    """Resolve the user data root, honouring XDG conventions."""
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "cantracediag"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(slots=True)
class DbcEntry:
    digest: str
    name: str
    first_seen: str
    last_used: str
    path: Path


class Workspace:
    """A persistent (or ephemeral) local data directory for CanTraceDiag."""

    def __init__(
        self,
        root: Path,
        *,
        ephemeral: bool = False,
        dbc_cap: int = DEFAULT_DBC_CAP,
    ) -> None:
        self.root = Path(root)
        self.ephemeral = ephemeral
        self.dbc_cap = dbc_cap
        self.dbc_dir = self.root / "dbc"
        self.analysis_dir = self.root / "analysis"
        self.index_path = self.dbc_dir / "index.json"
        self.manifest_path = self.root / "last-analysis.json"
        if not ephemeral:
            self.dbc_dir.mkdir(parents=True, exist_ok=True)
            self.analysis_dir.mkdir(parents=True, exist_ok=True)

    # -- construction ------------------------------------------------------
    @classmethod
    def from_env(cls) -> Workspace:
        """Build the workspace from environment configuration.

        ``CANTRACEDIAG_EPHEMERAL=1`` forces an ephemeral workspace (used by the
        test-suite). Otherwise persistence is on, rooted at
        ``CANTRACEDIAG_DATA_DIR`` when set, else the XDG default.
        """
        if os.environ.get("CANTRACEDIAG_EPHEMERAL") == "1":
            return cls(Path(tempfile.mkdtemp(prefix="ctd_ws_")), ephemeral=True)
        root_env = os.environ.get("CANTRACEDIAG_DATA_DIR")
        root = Path(root_env) if root_env else default_data_root()
        cap_env = os.environ.get("CANTRACEDIAG_DBC_CAP")
        try:
            cap = int(cap_env) if cap_env else DEFAULT_DBC_CAP
        except ValueError:
            cap = DEFAULT_DBC_CAP
        return cls(root, ephemeral=False, dbc_cap=max(1, cap))

    # -- DBC library -------------------------------------------------------
    def _load_index(self) -> dict[str, dict]:
        if not self.index_path.is_file():
            return {}
        try:
            data = json.loads(self.index_path.read_text())
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write_index(self, index: dict[str, dict]) -> None:
        _atomic_write_text(self.index_path, json.dumps(index, indent=2))

    def store_dbc(self, src: Path, display_name: str) -> DbcEntry:
        """Copy a DBC into the library, deduplicated by content hash.

        Re-importing an identical file only refreshes its ``last_used`` stamp.
        No-op storage (returning a transient entry) in ephemeral mode.
        """
        src = Path(src)
        name = Path(display_name).name or src.name
        if self.ephemeral:
            return DbcEntry(
                digest="", name=name, first_seen=_now_iso(),
                last_used=_now_iso(), path=src,
            )
        digest = _sha256(src)
        index = self._load_index()
        dest_dir = self.dbc_dir / digest
        dest = dest_dir / name
        now = _now_iso()
        if digest in index and dest.is_file():
            index[digest]["last_used"] = now
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            first = index.get(digest, {}).get("first_seen", now)
            index[digest] = {"name": name, "first_seen": first, "last_used": now}
        self._write_index(index)
        self._enforce_lru(index)
        entry = index[digest]
        return DbcEntry(
            digest=digest, name=entry["name"],
            first_seen=entry["first_seen"], last_used=entry["last_used"], path=dest,
        )

    def library(self) -> list[DbcEntry]:
        """All library DBCs, most-recently-used first."""
        if self.ephemeral:
            return []
        index = self._load_index()
        entries: list[DbcEntry] = []
        for digest, meta in index.items():
            path = self.dbc_dir / digest / meta["name"]
            if path.is_file():
                entries.append(DbcEntry(
                    digest=digest, name=meta["name"],
                    first_seen=meta["first_seen"], last_used=meta["last_used"], path=path,
                ))
        entries.sort(key=lambda e: e.last_used, reverse=True)
        return entries

    def library_path(self, digest: str) -> Path | None:
        """Resolve a library digest to its on-disk DBC file, or None."""
        if self.ephemeral:
            return None
        meta = self._load_index().get(digest)
        if not meta:
            return None
        path = self.dbc_dir / digest / meta["name"]
        return path if path.is_file() else None

    def _enforce_lru(self, index: dict[str, dict]) -> None:
        """Evict least-recently-used library entries beyond the cap."""
        if len(index) <= self.dbc_cap:
            self._prune_orphans(index)
            return
        ordered = sorted(index.items(), key=lambda kv: kv[1]["last_used"])
        for digest, _ in ordered[: len(index) - self.dbc_cap]:
            shutil.rmtree(self.dbc_dir / digest, ignore_errors=True)
            index.pop(digest, None)
        self._write_index(index)
        self._prune_orphans(index)

    def _prune_orphans(self, index: dict[str, dict]) -> None:
        """Remove on-disk digest dirs referenced by no index entry."""
        if not self.dbc_dir.is_dir():
            return
        for child in self.dbc_dir.iterdir():
            if child.is_dir() and child.name not in index:
                shutil.rmtree(child, ignore_errors=True)

    # -- analysis persistence ---------------------------------------------
    def new_analysis_holder(self) -> tuple[str, Path]:
        """A fresh directory holding one analysis DuckDB.

        Ephemeral: a throwaway temp dir (pre-workspace behaviour). Persistent:
        a uuid-named dir under ``analysis/`` so the previous committed analysis
        stays intact until the new one succeeds (transactional swap).
        """
        if self.ephemeral:
            holder = Path(tempfile.mkdtemp(prefix="ctd_db_"))
        else:
            holder = self.analysis_dir / uuid.uuid4().hex
            holder.mkdir(parents=True, exist_ok=True)
        return str(holder / "analysis.duckdb"), holder

    def commit_analysis(
        self,
        holder: Path,
        *,
        trace_display: str,
        asc_base: str | None,
        dbcs: list[DbcEntry],
        resolution: dict[int, str],
    ) -> None:
        """Record ``holder`` as the latest analysis via an atomic manifest write."""
        if self.ephemeral:
            return
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "created": _now_iso(),
            "holder": Path(holder).name,
            "duckdb": "analysis.duckdb",
            "trace_display": trace_display,
            "asc_base": asc_base,
            "dbcs": [{"digest": e.digest, "name": e.name} for e in dbcs],
            "resolution": {_hex(k): v for k, v in resolution.items()},
        }
        _atomic_write_text(self.manifest_path, json.dumps(manifest, indent=2))
        self._prune_stale_analyses(keep=Path(holder).name)

    def _prune_stale_analyses(self, keep: str) -> None:
        if not self.analysis_dir.is_dir():
            return
        for child in self.analysis_dir.iterdir():
            if child.is_dir() and child.name != keep:
                shutil.rmtree(child, ignore_errors=True)

    def load_manifest(self) -> dict | None:
        """Return the last-analysis manifest if present and current, else None."""
        if self.ephemeral or not self.manifest_path.is_file():
            return None
        try:
            data = json.loads(self.manifest_path.read_text())
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            return None
        return data

    def analysis_db_path(self, manifest: dict) -> Path | None:
        holder = manifest.get("holder")
        db = manifest.get("duckdb", "analysis.duckdb")
        if not holder:
            return None
        path = self.analysis_dir / holder / db
        return path if path.is_file() else None

    # -- purge -------------------------------------------------------------
    def purge(self) -> None:
        """Delete the DBC library and the last analysis (keep the dirs)."""
        if self.ephemeral:
            return
        shutil.rmtree(self.dbc_dir, ignore_errors=True)
        shutil.rmtree(self.analysis_dir, ignore_errors=True)
        self.manifest_path.unlink(missing_ok=True)
        self.dbc_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _hex(frame_id: int) -> str:
    return hex(frame_id)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{uuid.uuid4().hex}")
    tmp.write_text(text)
    os.replace(tmp, path)
