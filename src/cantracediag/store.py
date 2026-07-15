"""Local DuckDB-backed index for a single acquisition.

The store keeps raw frames, non-data events, and decoded signal samples in
separate tables so the UI can query bounded time windows and paginated trace
rows without loading the whole acquisition (ADR: local cache/index layer).
The database file lives outside Git (see ``.gitignore``).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import duckdb
import pandas as pd

from cantracediag.models import DecodedSignalSample, NonDataEvent, RawCanFrame

_SCHEMA = """
CREATE TABLE IF NOT EXISTS frames (
    seq            BIGINT,
    timestamp_s    DOUBLE,
    channel        VARCHAR,
    arbitration_id BIGINT,
    id_hex         VARCHAR,
    is_extended_id BOOLEAN,
    dlc            INTEGER,
    data_hex       VARCHAR,
    direction      VARCHAR,
    is_remote      BOOLEAN,
    message_name   VARCHAR,
    decode_status  VARCHAR
);
CREATE TABLE IF NOT EXISTS events (
    seq         BIGINT,
    timestamp_s DOUBLE,
    channel     VARCHAR,
    event_type  VARCHAR,
    detail      VARCHAR
);
CREATE TABLE IF NOT EXISTS samples (
    timestamp_s    DOUBLE,
    channel        VARCHAR,
    arbitration_id BIGINT,
    message_name   VARCHAR,
    signal_name    VARCHAR,
    value_num      DOUBLE,
    value_text     VARCHAR,
    unit           VARCHAR
);
"""


@dataclass(slots=True)
class TimeBounds:
    start_s: float | None
    end_s: float | None


class TraceStore:
    def __init__(self, db_path: str = ":memory:"):
        self.con = duckdb.connect(db_path)
        self.con.execute(_SCHEMA)

    def close(self) -> None:
        self.con.close()

    # -- ingestion ---------------------------------------------------------

    def ingest_frames(self, frames: Iterable[RawCanFrame]) -> int:
        rows = [
            {
                "seq": i,
                "timestamp_s": f.timestamp_s,
                "channel": f.channel,
                "arbitration_id": f.arbitration_id,
                "id_hex": _id_hex(f.arbitration_id, f.is_extended_id),
                "is_extended_id": f.is_extended_id,
                "dlc": f.dlc,
                "data_hex": f.data.hex(" ").upper() or None,
                "direction": f.direction,
                "is_remote": f.is_remote,
                "message_name": f.message_name,
                "decode_status": f.decode_status,
            }
            for i, f in enumerate(frames)
        ]
        return self._append("frames", rows)

    def ingest_events(self, events: Iterable[NonDataEvent]) -> int:
        rows = [
            {
                "seq": i,
                "timestamp_s": e.timestamp_s,
                "channel": e.channel,
                "event_type": e.event_type,
                "detail": e.detail,
            }
            for i, e in enumerate(events)
        ]
        return self._append("events", rows)

    def ingest_samples(self, samples: Iterable[DecodedSignalSample]) -> int:
        rows = [
            {
                "timestamp_s": s.timestamp_s,
                "channel": s.channel,
                "arbitration_id": s.arbitration_id,
                "message_name": s.message_name,
                "signal_name": s.signal_name,
                "value_num": s.value if isinstance(s.value, (int, float)) else None,
                "value_text": s.value if isinstance(s.value, str) else None,
                "unit": s.unit,
            }
            for s in samples
        ]
        return self._append("samples", rows)

    def _append(self, table: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        frame = pd.DataFrame(rows)
        self.con.register("_incoming", frame)
        self.con.execute(f"INSERT INTO {table} SELECT * FROM _incoming")
        self.con.unregister("_incoming")
        return len(rows)

    # -- queries -----------------------------------------------------------

    def time_bounds(self) -> TimeBounds:
        row = self.con.execute(
            """
            SELECT min(t), max(t) FROM (
                SELECT timestamp_s AS t FROM frames
                UNION ALL SELECT timestamp_s FROM events
            )
            """
        ).fetchone()
        return TimeBounds(start_s=row[0], end_s=row[1])

    def summary(self) -> dict:
        frames = self.con.execute("SELECT count(*) FROM frames").fetchone()[0]
        events = self.con.execute("SELECT count(*) FROM events").fetchone()[0]
        decoded = self.con.execute(
            "SELECT count(*) FROM frames WHERE decode_status = 'ok'"
        ).fetchone()[0]
        ids = self.con.execute(
            "SELECT count(DISTINCT arbitration_id) FROM frames"
        ).fetchone()[0]
        bounds = self.time_bounds()
        return {
            "frames": frames,
            "events": events,
            "decoded_frames": decoded,
            "unique_ids": ids,
            "start_s": bounds.start_s,
            "end_s": bounds.end_s,
        }

    def signal_series(
        self,
        message_name: str,
        signal_name: str,
        start_s: float | None = None,
        end_s: float | None = None,
        max_points: int = 200_000,
    ) -> dict:
        """Ordered (t, value) pairs for a signal over an optional window."""
        clauses = ["message_name = ?", "signal_name = ?", "value_num IS NOT NULL"]
        params: list[object] = [message_name, signal_name]
        if start_s is not None:
            clauses.append("timestamp_s >= ?")
            params.append(start_s)
        if end_s is not None:
            clauses.append("timestamp_s <= ?")
            params.append(end_s)
        where = " AND ".join(clauses)
        df = self.con.execute(
            f"""
            SELECT timestamp_s, value_num
            FROM samples
            WHERE {where}
            ORDER BY timestamp_s
            LIMIT {int(max_points) + 1}
            """,
            params,
        ).df()
        truncated = len(df) > max_points
        if truncated:
            df = df.iloc[:max_points]
        unit = self.con.execute(
            "SELECT unit FROM samples WHERE message_name = ? AND signal_name = ? "
            "AND unit IS NOT NULL LIMIT 1",
            [message_name, signal_name],
        ).fetchone()
        return {
            "message_name": message_name,
            "signal_name": signal_name,
            "unit": unit[0] if unit else None,
            "t": df["timestamp_s"].tolist(),
            "v": df["value_num"].tolist(),
            "truncated": truncated,
        }

    def nearest_sample(
        self, message_name: str, signal_name: str, at_s: float
    ) -> dict | None:
        """Nearest sample by absolute time distance — no interpolation (AC5)."""
        row = self.con.execute(
            """
            SELECT timestamp_s, value_num, value_text, unit
            FROM samples
            WHERE message_name = ? AND signal_name = ?
            ORDER BY abs(timestamp_s - ?)
            LIMIT 1
            """,
            [message_name, signal_name, at_s],
        ).fetchone()
        if row is None:
            return None
        return {
            "timestamp_s": row[0],
            "value": row[1] if row[1] is not None else row[2],
            "unit": row[3],
        }

    def trace_rows(
        self,
        offset: int = 0,
        limit: int = 200,
        start_s: float | None = None,
        end_s: float | None = None,
        include_frames: bool = True,
        include_events: bool = True,
    ) -> dict:
        """Time-ordered, paginated view mixing frames and events (AC6)."""
        selects: list[str] = []
        window_params: list[object] = []
        window = self._window_clause(start_s, end_s, window_params)

        if include_frames:
            selects.append(
                f"""
                SELECT timestamp_s, channel, 'frame' AS kind, id_hex,
                       message_name AS name, direction, dlc, data_hex,
                       decode_status, NULL AS detail
                FROM frames {window}
                """
            )
        if include_events:
            selects.append(
                f"""
                SELECT timestamp_s, channel, 'event' AS kind, NULL AS id_hex,
                       event_type AS name, NULL AS direction, NULL AS dlc,
                       NULL AS data_hex, NULL AS decode_status, detail
                FROM events {window}
                """
            )
        if not selects:
            return {"total": 0, "offset": offset, "limit": limit, "rows": []}

        union = " UNION ALL ".join(selects)
        # The window clause (and its placeholders) is repeated once per select.
        params = window_params * len(selects)
        total = self.con.execute(
            f"SELECT count(*) FROM ({union})", list(params)
        ).fetchone()[0]
        rows = self.con.execute(
            f"""
            SELECT * FROM ({union})
            ORDER BY timestamp_s
            LIMIT {int(limit)} OFFSET {int(offset)}
            """,
            list(params),
        ).df()
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "rows": _records(rows),
        }

    def frame_signals(self, timestamp_s: float, arbitration_id: int) -> list[dict]:
        """Decoded signals for one frame, keyed by exact time and id."""
        df = self.con.execute(
            """
            SELECT signal_name, value_num, value_text, unit
            FROM samples
            WHERE timestamp_s = ? AND arbitration_id = ?
            ORDER BY signal_name
            """,
            [timestamp_s, arbitration_id],
        ).df()
        return _records(df)

    def _window_clause(
        self, start_s: float | None, end_s: float | None, params: list[object]
    ) -> str:
        clauses: list[str] = []
        if start_s is not None:
            clauses.append("timestamp_s >= ?")
            params.append(start_s)
        if end_s is not None:
            clauses.append("timestamp_s <= ?")
            params.append(end_s)
        return f"WHERE {' AND '.join(clauses)}" if clauses else ""


def _id_hex(arbitration_id: int, is_extended: bool) -> str:
    width = 8 if is_extended else 3
    return f"{arbitration_id:0{width}X}"


def _records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to JSON-safe dict rows (NaN/NaT -> None)."""
    clean = df.astype(object).where(pd.notnull(df), None)
    return clean.to_dict(orient="records")
