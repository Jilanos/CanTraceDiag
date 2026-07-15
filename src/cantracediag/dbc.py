"""Loading and inspection of one or more local DBC databases.

Multiple DBC files may be loaded for a single acquisition. IDs are expected to
be unique *within* one acquisition, but overlaps *across* DBC files are
possible; :func:`find_ambiguous_ids` exposes them so the operator can resolve
which database owns a frame (AC2, product decision on ambiguity).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cantools
from cantools.database import Database
from cantools.database.can import Message

from cantracediag.models import SignalInfo


@dataclass(slots=True)
class LoadedDatabase:
    name: str
    path: str
    database: Database


@dataclass(slots=True)
class DbcCatalog:
    """A collection of loaded DBC files plus a merged message index."""

    databases: list[LoadedDatabase] = field(default_factory=list)

    def load(self, path: str | Path) -> LoadedDatabase:
        path = Path(path)
        database = cantools.database.load_file(str(path))
        loaded = LoadedDatabase(name=path.name, path=str(path), database=database)
        self.databases.append(loaded)
        return loaded

    def messages(self) -> list[tuple[str, Message]]:
        """All (database_name, message) pairs across every loaded DBC."""
        pairs: list[tuple[str, Message]] = []
        for loaded in self.databases:
            for message in loaded.database.messages:
                pairs.append((loaded.name, message))
        return pairs

    def signals(self) -> list[SignalInfo]:
        """Flat catalog of every signal available for plotting."""
        # Merge databases owning the same (id, signal) so the catalog is deduped
        # but still records which DBCs contribute each signal.
        index: dict[tuple[int, str, str], SignalInfo] = {}
        for db_name, message in self.messages():
            for signal in message.signals:
                key = (message.frame_id, message.name, signal.name)
                existing = index.get(key)
                dbs = (db_name,) if existing is None else (*existing.databases, db_name)
                index[key] = SignalInfo(
                    message_name=message.name,
                    signal_name=signal.name,
                    arbitration_id=message.frame_id,
                    is_extended_id=bool(message.is_extended_frame),
                    unit=signal.unit,
                    minimum=_as_float(signal.minimum),
                    maximum=_as_float(signal.maximum),
                    databases=dbs,
                )
        return sorted(
            index.values(),
            key=lambda s: (s.message_name, s.signal_name),
        )

    def message_index(self) -> dict[int, list[tuple[str, Message]]]:
        """Map arbitration id -> [(database_name, message)] for decoding."""
        index: dict[int, list[tuple[str, Message]]] = {}
        for db_name, message in self.messages():
            index.setdefault(message.frame_id, []).append((db_name, message))
        return index

    def find_ambiguous_ids(self) -> dict[int, list[str]]:
        """Arbitration ids defined by more than one DBC, with differing names."""
        ambiguous: dict[int, list[str]] = {}
        for frame_id, entries in self.message_index().items():
            names = {message.name for _, message in entries}
            if len(entries) > 1 and len(names) > 1:
                ambiguous[frame_id] = sorted(
                    f"{db_name}:{message.name}" for db_name, message in entries
                )
        return ambiguous


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
