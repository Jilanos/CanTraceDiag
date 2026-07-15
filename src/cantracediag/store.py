"""Local DuckDB-backed index for a single acquisition.

The store keeps raw frames, non-data events, and decoded signal samples in
separate tables so the UI can query bounded time windows and paginated trace
rows without loading the whole acquisition (ADR: local cache/index layer).
The database file lives outside Git (see ``.gitignore``).
"""

from __future__ import annotations

import threading
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
    decode_status  VARCHAR,
    dbc_source     VARCHAR
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
        # A single DuckDB connection is not safe for concurrent use: FastAPI
        # runs these sync endpoints in a threadpool and the UI fires several
        # /api/series and /api/cursor calls in parallel, so without this lock
        # their result sets interleave and corrupt each other (observed as
        # KeyError/NoneType/tuple-index/int('Nm') crashes in signal_series).
        # RLock because some query methods call others (e.g. summary→time_bounds).
        self._lock = threading.RLock()
        self.con.execute(_SCHEMA)

    def close(self) -> None:
        with self._lock:
            self.con.close()

    # -- thread-safe query helpers ----------------------------------------
    # The lazy window between execute() and fetch is where concurrent threads
    # corrupt one another, so each helper holds the lock across both.
    def _one(self, sql: str, params: Iterable[object] = ()):
        with self._lock:
            return self.con.execute(sql, list(params)).fetchone()

    def _all(self, sql: str, params: Iterable[object] = ()):
        with self._lock:
            return self.con.execute(sql, list(params)).fetchall()

    def _df(self, sql: str, params: Iterable[object] = ()) -> pd.DataFrame:
        with self._lock:
            return self.con.execute(sql, list(params)).df()

    # -- ingestion ---------------------------------------------------------

    def ingest_frames(self, frames: Iterable[RawCanFrame], seq_start: int = 0) -> int:
        rows = [
            {
                "seq": seq_start + i,
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
                "dbc_source": f.dbc_source,
            }
            for i, f in enumerate(frames)
        ]
        return self._append("frames", rows)

    def ingest_events(self, events: Iterable[NonDataEvent], seq_start: int = 0) -> int:
        rows = [
            {
                "seq": seq_start + i,
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
        with self._lock:
            self.con.register("_incoming", frame)
            self.con.execute(f"INSERT INTO {table} SELECT * FROM _incoming")
            self.con.unregister("_incoming")
        return len(rows)

    # -- queries -----------------------------------------------------------

    def time_bounds(self) -> TimeBounds:
        row = self._one(
            """
            SELECT min(t), max(t) FROM (
                SELECT timestamp_s AS t FROM frames
                UNION ALL SELECT timestamp_s FROM events
            )
            """
        )
        return TimeBounds(start_s=row[0], end_s=row[1])

    def summary(self) -> dict:
        frames = self._one("SELECT count(*) FROM frames")[0]
        events = self._one("SELECT count(*) FROM events")[0]
        decoded = self._one(
            "SELECT count(*) FROM frames WHERE decode_status = 'ok'"
        )[0]
        ids = self._one("SELECT count(DISTINCT arbitration_id) FROM frames")[0]
        status_rows = self._all(
            "SELECT decode_status, count(*) FROM frames GROUP BY decode_status"
        )
        event_rows = self._all(
            "SELECT event_type, count(*) FROM events GROUP BY event_type"
        )
        bounds = self.time_bounds()
        return {
            "frames": frames,
            "events": events,
            "decoded_frames": decoded,
            "unique_ids": ids,
            "start_s": bounds.start_s,
            "end_s": bounds.end_s,
            "decode_status": {r[0]: r[1] for r in status_rows},
            "event_types": {r[0]: r[1] for r in event_rows},
        }

    def signal_series(
        self,
        message_name: str,
        signal_name: str,
        start_s: float | None = None,
        end_s: float | None = None,
        max_points: int = 4000,
    ) -> dict:
        """Ordered (t, value) pairs for a signal over an optional window.

        When the window holds more samples than ``max_points``, the series is
        decimated server-side (AC9): the window is split into time buckets and
        each bucket contributes its min-value and max-value samples. Every point
        returned is a real stored sample (no interpolation, AC2), and spikes are
        preserved because per-bucket extrema are kept.
        """
        clauses = ["message_name = ?", "signal_name = ?", "value_num IS NOT NULL"]
        params: list[object] = [message_name, signal_name]
        if start_s is not None:
            clauses.append("timestamp_s >= ?")
            params.append(start_s)
        if end_s is not None:
            clauses.append("timestamp_s <= ?")
            params.append(end_s)
        where = " AND ".join(clauses)

        stats = self._one(
            f"SELECT count(*), min(timestamp_s), max(timestamp_s) "
            f"FROM samples WHERE {where}",
            params,
        )
        raw_count = int(stats[0] or 0)
        t_lo, t_hi = stats[1], stats[2]

        max_points = max(2, int(max_points))
        downsampled = raw_count > max_points and t_hi is not None and t_hi > t_lo
        if downsampled:
            df = self._decimate(where, params, max_points, t_lo, t_hi)
        else:
            df = self._df(
                f"SELECT timestamp_s, value_num FROM samples WHERE {where} "
                f"ORDER BY timestamp_s",
                params,
            )

        unit = self._one(
            "SELECT unit FROM samples WHERE message_name = ? AND signal_name = ? "
            "AND unit IS NOT NULL LIMIT 1",
            [message_name, signal_name],
        )
        return {
            "message_name": message_name,
            "signal_name": signal_name,
            "unit": unit[0] if unit else None,
            "t": df["timestamp_s"].tolist(),
            "v": df["value_num"].tolist(),
            "raw_count": raw_count,
            "downsampled": downsampled,
        }

    def _decimate(
        self,
        where: str,
        params: list[object],
        max_points: int,
        t_lo: float,
        t_hi: float,
    ) -> pd.DataFrame:
        """Min/max time-bucket decimation returning real samples in time order."""
        # Two points per bucket (min + max), so half as many buckets as points.
        nbuckets = max(1, max_points // 2)
        span = t_hi - t_lo
        # arg_min/arg_max pick the actual timestamp at which each extreme occurs.
        df = self._df(
            f"""
            WITH win AS (
                SELECT timestamp_s, value_num,
                       least({nbuckets - 1},
                             CAST((timestamp_s - {t_lo!r}) / {span!r}
                                  * {nbuckets} AS BIGINT)) AS bucket
                FROM samples WHERE {where}
            ),
            agg AS (
                SELECT bucket,
                       arg_min(timestamp_s, value_num) AS t_min, min(value_num) AS v_min,
                       arg_max(timestamp_s, value_num) AS t_max, max(value_num) AS v_max
                FROM win GROUP BY bucket
            ),
            pts AS (
                SELECT t_min AS timestamp_s, v_min AS value_num FROM agg
                UNION ALL
                SELECT t_max AS timestamp_s, v_max AS value_num FROM agg
            )
            SELECT DISTINCT timestamp_s, value_num FROM pts ORDER BY timestamp_s
            """,
            params,
        )
        return df

    def nearest_sample(
        self, message_name: str, signal_name: str, at_s: float
    ) -> dict | None:
        """Nearest sample by absolute time distance — no interpolation (AC5)."""
        row = self._one(
            """
            SELECT timestamp_s, value_num, value_text, unit
            FROM samples
            WHERE message_name = ? AND signal_name = ?
            ORDER BY abs(timestamp_s - ?)
            LIMIT 1
            """,
            [message_name, signal_name, at_s],
        )
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
        id_hex: str | None = None,
        message: str | None = None,
        direction: str | None = None,
        decode_status: str | None = None,
        event_type: str | None = None,
    ) -> dict:
        """Time-ordered, paginated view mixing frames and events (AC4, AC6).

        Every filter is combinable and applied server-side so the browser never
        loads the whole trace. ``id_hex``/``message`` match case-insensitive
        substrings; the rest match exactly.
        """
        union, params = self._trace_union(
            start_s, end_s, include_frames, include_events,
            id_hex, message, direction, decode_status, event_type,
        )
        if union is None:
            return {"total": 0, "offset": offset, "limit": limit, "rows": []}

        total = self._one(
            f"SELECT count(*) FROM ({union})", list(params)
        )[0]
        rows = self._df(
            f"""
            SELECT * FROM ({union})
            ORDER BY timestamp_s
            LIMIT {int(limit)} OFFSET {int(offset)}
            """,
            list(params),
        )
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "rows": _records(rows),
        }

    def locate_row(
        self,
        at_s: float,
        include_frames: bool = True,
        include_events: bool = True,
        start_s: float | None = None,
        end_s: float | None = None,
        id_hex: str | None = None,
        message: str | None = None,
        direction: str | None = None,
        decode_status: str | None = None,
        event_type: str | None = None,
    ) -> dict:
        """Row index of the trace row nearest to ``at_s`` under active filters.

        Powers graph-to-trace synchronization (AC3): the UI pages to the index
        so the nearest frames become visible and can be highlighted.
        """
        union, params = self._trace_union(
            start_s, end_s, include_frames, include_events,
            id_hex, message, direction, decode_status, event_type,
        )
        if union is None:
            return {"total": 0, "index": None, "timestamp_s": None}
        total = self._one(
            f"SELECT count(*) FROM ({union})", list(params)
        )[0]
        # Rows strictly before the nearest sit ahead of it in time order.
        row = self._one(
            f"""
            WITH ordered AS (
                SELECT timestamp_s,
                       row_number() OVER (ORDER BY timestamp_s) - 1 AS idx
                FROM ({union})
            )
            SELECT idx, timestamp_s FROM ordered
            ORDER BY abs(timestamp_s - ?) , idx LIMIT 1
            """,
            [*params, at_s],
        )
        if row is None:
            return {"total": total, "index": None, "timestamp_s": None}
        return {"total": total, "index": int(row[0]), "timestamp_s": row[1]}

    def _trace_union(
        self,
        start_s: float | None,
        end_s: float | None,
        include_frames: bool,
        include_events: bool,
        id_hex: str | None,
        message: str | None,
        direction: str | None,
        decode_status: str | None,
        event_type: str | None,
    ) -> tuple[str | None, list[object]]:
        selects: list[str] = []
        params: list[object] = []

        # A frame-only attribute filter excludes events (they carry no id /
        # direction / decode status); an event-type filter excludes frames.
        # ``message`` matches decoded message names and event types, so it is
        # kept on both sides.
        if id_hex or direction or decode_status:
            include_events = False
        if event_type:
            include_frames = False

        if include_frames:
            clauses, fparams = self._frame_filters(
                start_s, end_s, id_hex, message, direction, decode_status
            )
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            selects.append(
                f"""
                SELECT timestamp_s, channel, 'frame' AS kind, id_hex,
                       message_name AS name, direction, dlc, data_hex,
                       decode_status, dbc_source, NULL AS detail
                FROM frames {where}
                """
            )
            params.extend(fparams)
        if include_events:
            clauses, eparams = self._event_filters(
                start_s, end_s, message, event_type
            )
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            selects.append(
                f"""
                SELECT timestamp_s, channel, 'event' AS kind, NULL AS id_hex,
                       event_type AS name, NULL AS direction, NULL AS dlc,
                       NULL AS data_hex, NULL AS decode_status,
                       NULL AS dbc_source, detail
                FROM events {where}
                """
            )
            params.extend(eparams)

        if not selects:
            return None, []
        return " UNION ALL ".join(selects), params

    def _frame_filters(
        self,
        start_s: float | None,
        end_s: float | None,
        id_hex: str | None,
        message: str | None,
        direction: str | None,
        decode_status: str | None,
    ) -> tuple[list[str], list[object]]:
        clauses: list[str] = []
        params: list[object] = []
        self._time_clauses(start_s, end_s, clauses, params)
        if id_hex:
            clauses.append("lower(id_hex) LIKE ?")
            params.append(f"%{id_hex.lower().removeprefix('0x')}%")
        if message:
            clauses.append("lower(coalesce(message_name, '')) LIKE ?")
            params.append(f"%{message.lower()}%")
        if direction:
            clauses.append("direction = ?")
            params.append(direction)
        if decode_status:
            clauses.append("decode_status = ?")
            params.append(decode_status)
        return clauses, params

    def _event_filters(
        self,
        start_s: float | None,
        end_s: float | None,
        message: str | None,
        event_type: str | None,
    ) -> tuple[list[str], list[object]]:
        clauses: list[str] = []
        params: list[object] = []
        self._time_clauses(start_s, end_s, clauses, params)
        # A frame-oriented id/direction/status filter must exclude every event.
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if message:
            clauses.append("lower(event_type) LIKE ?")
            params.append(f"%{message.lower()}%")
        return clauses, params

    def _time_clauses(
        self,
        start_s: float | None,
        end_s: float | None,
        clauses: list[str],
        params: list[object],
    ) -> None:
        if start_s is not None:
            clauses.append("timestamp_s >= ?")
            params.append(start_s)
        if end_s is not None:
            clauses.append("timestamp_s <= ?")
            params.append(end_s)

    def event_types(self) -> list[str]:
        rows = self._all(
            "SELECT DISTINCT event_type FROM events ORDER BY event_type"
        )
        return [r[0] for r in rows]

    def frame_signals(self, timestamp_s: float, arbitration_id: int) -> list[dict]:
        """Decoded signals for one frame, keyed by exact time and id."""
        df = self._df(
            """
            SELECT signal_name, value_num, value_text, unit
            FROM samples
            WHERE timestamp_s = ? AND arbitration_id = ?
            ORDER BY signal_name
            """,
            [timestamp_s, arbitration_id],
        )
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
