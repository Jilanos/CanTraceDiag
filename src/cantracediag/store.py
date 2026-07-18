"""Local DuckDB-backed index for a single acquisition.

The store keeps raw frames, non-data events, and decoded signal samples in
separate tables so the UI can query bounded time windows and paginated trace
rows without loading the whole acquisition (ADR: local cache/index layer).
The database file lives outside Git (see ``.gitignore``).
"""

from __future__ import annotations

import base64
import binascii
import json
import threading
from collections.abc import Callable, Iterable
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
CREATE TABLE IF NOT EXISTS series_cache (
    message_name VARCHAR,
    signal_name  VARCHAR,
    start_s      DOUBLE,
    end_s        DOUBLE,
    frame_count  BIGINT,
    sample_count BIGINT
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
        # Reference-counted lifecycle: a store swapped out by a new import
        # must not be closed under an in-flight request (AC3), so close()
        # only takes effect once every acquire() has a matching release().
        self._active_lock = threading.Lock()
        self._active = 0
        self._closing = False
        self._closed = False
        self._on_closed: Callable[[], None] | None = None
        self.con.execute(_SCHEMA)

    def acquire(self) -> bool:
        """Mark the store as in use by one more concurrent request.

        Returns ``False`` if the store is already closing/closed, in which
        case the caller must treat it as unavailable rather than use it.
        """
        with self._active_lock:
            if self._closing or self._closed:
                return False
            self._active += 1
            return True

    def release(self) -> None:
        """Release a hold taken by :meth:`acquire`."""
        with self._active_lock:
            self._active = max(0, self._active - 1)
            should_close = self._closing and self._active == 0 and not self._closed
        if should_close:
            self._finish_close()

    def close(self, on_closed: Callable[[], None] | None = None) -> None:
        """Close the store once no request is using it (AC3).

        Marks the store as closing immediately so no *new* request can
        acquire it, but defers the actual DuckDB close (and ``on_closed``)
        until every in-flight request has released it.
        """
        with self._active_lock:
            if self._closed:
                already_closed = True
                close_now = False
            else:
                already_closed = False
                self._closing = True
                self._on_closed = on_closed
                close_now = self._active == 0
        if already_closed and on_closed is not None:
            on_closed()
        elif close_now:
            self._finish_close()

    def _finish_close(self) -> None:
        with self._active_lock:
            if self._closed:
                return
            self._closed = True
            callback = self._on_closed
            self._on_closed = None
        with self._lock:
            self.con.close()
        if callback is not None:
            callback()

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

    def ingest_frames(
        self,
        frames: Iterable[RawCanFrame],
        seq_start: int = 0,
        seqs: list[int] | None = None,
    ) -> int:
        frames = list(frames)
        if seqs is None:
            seqs = [seq_start + i for i in range(len(frames))]
        rows = [
            {
                "seq": seqs[i],
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

    def ingest_events(
        self,
        events: Iterable[NonDataEvent],
        seq_start: int = 0,
        seqs: list[int] | None = None,
    ) -> int:
        events = list(events)
        if seqs is None:
            seqs = [seq_start + i for i in range(len(events))]
        rows = [
            {
                "seq": seqs[i],
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

    def replace_signal_samples(
        self,
        message_name: str,
        signal_name: str,
        samples: Iterable[DecodedSignalSample],
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> int:
        clauses = ["message_name = ?", "signal_name = ?"]
        params: list[object] = [message_name, signal_name]
        if start_s is not None:
            clauses.append("timestamp_s >= ?")
            params.append(start_s)
        if end_s is not None:
            clauses.append("timestamp_s <= ?")
            params.append(end_s)
        with self._lock:
            self.con.execute(f"DELETE FROM samples WHERE {' AND '.join(clauses)}", params)
        return self.ingest_samples(samples)

    def mark_series_cached(
        self,
        message_name: str,
        signal_name: str,
        start_s: float | None,
        end_s: float | None,
        frame_count: int,
        sample_count: int,
    ) -> None:
        rows = [{
            "message_name": message_name,
            "signal_name": signal_name,
            "start_s": start_s,
            "end_s": end_s,
            "frame_count": frame_count,
            "sample_count": sample_count,
        }]
        self._append("series_cache", rows)

    def has_series_cache(
        self,
        message_name: str,
        signal_name: str,
        start_s: float | None,
        end_s: float | None,
    ) -> bool:
        row = self._one(
            """
            SELECT 1
            FROM series_cache
            WHERE message_name = ? AND signal_name = ?
              AND (start_s IS NULL OR start_s <= ?)
              AND (end_s IS NULL OR end_s >= ?)
            LIMIT 1
            """,
            [
                message_name,
                signal_name,
                start_s if start_s is not None else -float("inf"),
                end_s if end_s is not None else float("inf"),
            ],
        )
        return row is not None

    def cache_stats(self) -> dict:
        row = self._one(
            """
            SELECT count(*), coalesce(sum(frame_count), 0), coalesce(sum(sample_count), 0)
            FROM series_cache
            """
        )
        samples = self._one("SELECT count(*) FROM samples")[0]
        return {
            "series": int(row[0] or 0),
            "decoded_frames": int(row[1] or 0),
            "samples": int(samples or 0),
        }

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

    def sample_count(self) -> int:
        return int(self._one("SELECT count(*) FROM samples")[0] or 0)

    def dbc_usage(self) -> list[dict]:
        """DBCs that actually decoded at least one frame (AC1).

        Reports only databases credited with a successful decode, so the report
        distinguishes DBCs that were loaded from DBCs that were effectively used.
        """
        rows = self._all(
            """
            SELECT dbc_source, count(*)
            FROM frames
            WHERE decode_status = 'ok' AND dbc_source IS NOT NULL
            GROUP BY dbc_source
            ORDER BY dbc_source
            """
        )
        return [{"source": r[0], "frames": int(r[1])} for r in rows]

    def signal_stats(
        self,
        message_name: str,
        signal_name: str,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> dict:
        """Range statistics for one signal between two bounds (AC3).

        Numeric signals report count, min, max, mean, standard deviation and
        RMS. Text/enum signals report the sample count and the distribution of
        observed values instead of synthetic numeric statistics. An empty
        window is reported explicitly (``kind = "empty"``) rather than as zeros.
        """
        clauses = ["message_name = ?", "signal_name = ?"]
        params: list[object] = [message_name, signal_name]
        self._time_clauses(start_s, end_s, clauses, params)
        where = " AND ".join(clauses)

        unit_row = self._one(
            "SELECT unit FROM samples WHERE message_name = ? AND signal_name = ? "
            "AND unit IS NOT NULL LIMIT 1",
            [message_name, signal_name],
        )
        unit = unit_row[0] if unit_row else None

        agg = self._one(
            f"""
            SELECT count(*), count(value_num),
                   min(value_num), max(value_num), avg(value_num),
                   stddev_samp(value_num), sqrt(avg(value_num * value_num))
            FROM samples WHERE {where}
            """,
            params,
        )
        total = int(agg[0] or 0)
        numeric = int(agg[1] or 0)
        base = {
            "message_name": message_name,
            "signal_name": signal_name,
            "unit": unit,
            "count": total,
        }
        if total == 0:
            return {**base, "kind": "empty"}
        if numeric > 0:
            return {
                **base,
                "kind": "numeric",
                "count": numeric,
                "min": _f(agg[2]),
                "max": _f(agg[3]),
                "mean": _f(agg[4]),
                "std": _f(agg[5]),
                "rms": _f(agg[6]),
            }
        dist = self._all(
            f"""
            SELECT value_text, count(*)
            FROM samples WHERE {where} AND value_text IS NOT NULL
            GROUP BY value_text
            ORDER BY count(*) DESC, value_text
            """,
            params,
        )
        return {
            **base,
            "kind": "text",
            "distribution": [{"value": r[0], "count": int(r[1])} for r in dist],
        }

    def iter_export_batches(
        self,
        pairs: list[tuple[str, str]],
        start_s: float | None = None,
        end_s: float | None = None,
        batch_size: int = 8192,
    ):
        """Yield decoded samples as bounded Arrow record batches (AC2).

        Streams the selected ``(message, signal)`` pairs over an optional window,
        ordered by ``(timestamp_s, message, signal)`` so a wide export can align
        by timestamp. DuckDB's record-batch cursor caps the resident rows at
        ``batch_size`` regardless of the total exported, so peak memory does not
        grow with the number of rows. The connection lock is held for the whole
        stream because the cursor lives on the shared connection.
        """
        if not pairs:
            return
        pair_clause = " OR ".join(
            "(message_name = ? AND signal_name = ?)" for _ in pairs
        )
        params: list[object] = []
        for message_name, signal_name in pairs:
            params.extend((message_name, signal_name))
        clauses = [f"({pair_clause})"]
        self._time_clauses(start_s, end_s, clauses, params)
        where = " AND ".join(clauses)
        sql = f"""
            SELECT timestamp_s,
                   message_name AS message,
                   signal_name AS signal,
                   coalesce(CAST(value_num AS VARCHAR), value_text) AS value,
                   unit
            FROM samples WHERE {where}
            ORDER BY timestamp_s, message_name, signal_name
        """
        with self._lock:
            reader = self.con.execute(sql, params).to_arrow_reader(max(1, batch_size))
            yield from reader

    def present_arbitration_ids(self) -> set[int]:
        rows = self._all("SELECT DISTINCT arbitration_id FROM frames")
        return {int(r[0]) for r in rows}

    def frames_for_signal(
        self,
        arbitration_id: int,
        start_s: float | None = None,
        end_s: float | None = None,
    ) -> list[RawCanFrame]:
        clauses = ["arbitration_id = ?"]
        params: list[object] = [arbitration_id]
        if start_s is not None:
            clauses.append("timestamp_s >= ?")
            params.append(start_s)
        if end_s is not None:
            clauses.append("timestamp_s <= ?")
            params.append(end_s)
        df = self._df(
            f"""
            SELECT timestamp_s, channel, arbitration_id, is_extended_id, dlc,
                   data_hex, direction, is_remote, message_name, decode_status, dbc_source
            FROM frames
            WHERE {' AND '.join(clauses)}
            ORDER BY timestamp_s
            """,
            params,
        )
        return [_frame_from_record(row) for row in _records(df)]

    def frame_at(self, timestamp_s: float, arbitration_id: int) -> RawCanFrame | None:
        row = self._one(
            """
            SELECT timestamp_s, channel, arbitration_id, is_extended_id, dlc,
                   data_hex, direction, is_remote, message_name, decode_status, dbc_source
            FROM frames
            WHERE timestamp_s = ? AND arbitration_id = ?
            LIMIT 1
            """,
            [timestamp_s, arbitration_id],
        )
        if row is None:
            return None
        return _frame_from_record({
            "timestamp_s": row[0],
            "channel": row[1],
            "arbitration_id": row[2],
            "is_extended_id": row[3],
            "dlc": row[4],
            "data_hex": row[5],
            "direction": row[6],
            "is_remote": row[7],
            "message_name": row[8],
            "decode_status": row[9],
            "dbc_source": row[10],
        })

    def nearest_frame_for_signal(
        self, arbitration_id: int, at_s: float
    ) -> RawCanFrame | None:
        """Frame of ``arbitration_id`` nearest to ``at_s`` (AC8).

        Bounded like :meth:`nearest_sample`: one lookup before and one after,
        never a distance sort over every frame of the id.
        """
        candidates = self._nearest_rows(
            "frames",
            "timestamp_s, channel, arbitration_id, is_extended_id, dlc, "
            "data_hex, direction, is_remote, message_name, decode_status, dbc_source",
            ["arbitration_id = ?"],
            [arbitration_id],
            at_s,
        )
        if not candidates:
            return None
        row = min(candidates, key=lambda r: abs(r[0] - at_s))
        return _frame_from_record({
            "timestamp_s": row[0],
            "channel": row[1],
            "arbitration_id": row[2],
            "is_extended_id": row[3],
            "dlc": row[4],
            "data_hex": row[5],
            "direction": row[6],
            "is_remote": row[7],
            "message_name": row[8],
            "decode_status": row[9],
            "dbc_source": row[10],
        })

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
        """Nearest sample to ``at_s`` — no interpolation (AC8).

        Uses at most one bounded lookup before ``at_s`` and one after, each
        ordered on the raw timestamp with ``LIMIT 1`` (never a sort by absolute
        distance over every sample), then keeps the closer of the two. A
        synthetic benchmark asserts this stays two bounded queries so the hot
        cursor path never regresses to a full scan.
        """
        candidates = self._nearest_rows(
            "samples",
            "timestamp_s, value_num, value_text, unit",
            ["message_name = ?", "signal_name = ?"],
            [message_name, signal_name],
            at_s,
        )
        if not candidates:
            return None
        row = min(candidates, key=lambda r: abs(r[0] - at_s))
        return {
            "timestamp_s": row[0],
            "value": row[1] if row[1] is not None else row[2],
            "unit": row[3],
        }

    def _nearest_rows(
        self,
        table: str,
        columns: str,
        clauses: list[str],
        params: list[object],
        at_s: float,
    ) -> list[tuple]:
        """Return the row just at/before ``at_s`` and the one just at/after it.

        Two bounded ``LIMIT 1`` queries (one ``<=`` descending, one ``>=``
        ascending), so the number of queries is constant regardless of how many
        rows the table holds (AC8).
        """
        prefix = " AND ".join([*clauses, ""]) if clauses else ""
        before = self._one(
            f"SELECT {columns} FROM {table} WHERE {prefix}timestamp_s <= ? "
            f"ORDER BY timestamp_s DESC LIMIT 1",
            [*params, at_s],
        )
        after = self._one(
            f"SELECT {columns} FROM {table} WHERE {prefix}timestamp_s >= ? "
            f"ORDER BY timestamp_s ASC LIMIT 1",
            [*params, at_s],
        )
        return [row for row in (before, after) if row is not None]

    def trace_rows(
        self,
        cursor: str | None = None,
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
        signal: str | None = None,
        signal_ids: list[int] | None = None,
    ) -> dict:
        """Deterministically ordered, cursor-paginated frames+events (AC9).

        Rows are totally ordered by the canonical ``(timestamp_s, seq)`` key and
        paginated with an opaque keyset ``cursor`` instead of ``OFFSET`` so the
        same row is never duplicated or skipped across pages, even when several
        rows share a timestamp. Every filter is combinable and applied
        server-side. ``id_hex``/``message`` match case-insensitive substrings;
        the rest match exactly.
        """
        limit = max(1, int(limit))
        union, params = self._trace_union(
            start_s, end_s, include_frames, include_events,
            id_hex, message, direction, decode_status, event_type, signal, signal_ids,
        )
        if union is None:
            return {
                "total": 0, "limit": limit, "start_index": 0,
                "rows": [], "next_cursor": None, "prev_cursor": None,
            }

        total = int(self._one(f"SELECT count(*) FROM ({union})", list(params))[0])
        mode, key = _decode_cursor(cursor)

        key_sql, key_params, descending = _keyset_predicate(mode, key)
        order = "DESC" if descending else "ASC"
        where = f"WHERE {key_sql}" if key_sql else ""
        rows_df = self._df(
            f"SELECT * FROM ({union}) {where} "
            f"ORDER BY timestamp_s {order}, seq {order} LIMIT {limit}",
            [*params, *key_params],
        )
        rows = _records(rows_df)
        if descending:
            rows.reverse()

        if not rows:
            return {
                "total": total, "limit": limit, "start_index": total,
                "rows": [], "next_cursor": None, "prev_cursor": None,
            }

        first_key = (float(rows[0]["timestamp_s"]), int(rows[0]["seq"]))
        last_key = (float(rows[-1]["timestamp_s"]), int(rows[-1]["seq"]))
        # Ordinal of the first row = rows strictly before it in canonical order.
        start_index = int(self._one(
            f"SELECT count(*) FROM ({union}) "
            f"WHERE (timestamp_s < ? OR (timestamp_s = ? AND seq < ?))",
            [*params, first_key[0], first_key[0], first_key[1]],
        )[0])
        prev_cursor = (
            None if start_index == 0
            else _encode_cursor("before", *first_key)
        )
        next_cursor = (
            None if start_index + len(rows) >= total
            else _encode_cursor("after", *last_key)
        )
        return {
            "total": total,
            "limit": limit,
            "start_index": start_index,
            "rows": rows,
            "next_cursor": next_cursor,
            "prev_cursor": prev_cursor,
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
        signal: str | None = None,
        signal_ids: list[int] | None = None,
    ) -> dict:
        """Locate the trace row nearest to ``at_s`` under active filters (AC9).

        Powers graph-to-trace synchronization: returns the row's canonical
        ordinal and an opaque ``cursor`` that opens the page starting exactly on
        that row, so the located frame is always visible and highlightable. The
        nearest row is found with two bounded lookups (one before, one after),
        never a distance sort over the whole trace.
        """
        union, params = self._trace_union(
            start_s, end_s, include_frames, include_events,
            id_hex, message, direction, decode_status, event_type, signal, signal_ids,
        )
        empty = {"total": 0, "index": None, "timestamp_s": None, "seq": None, "cursor": None}
        if union is None:
            return empty
        total = int(self._one(f"SELECT count(*) FROM ({union})", list(params))[0])
        candidates = self._nearest_rows(
            f"({union})", "timestamp_s, seq", [], list(params), at_s
        )
        if not candidates:
            return {**empty, "total": total}
        ts, seq = min(candidates, key=lambda r: abs(r[0] - at_s))
        ts, seq = float(ts), int(seq)
        index = int(self._one(
            f"SELECT count(*) FROM ({union}) "
            f"WHERE (timestamp_s < ? OR (timestamp_s = ? AND seq < ?))",
            [*params, ts, ts, seq],
        )[0])
        return {
            "total": total,
            "index": index,
            "timestamp_s": ts,
            "seq": seq,
            "cursor": _encode_cursor("at", ts, seq),
        }

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
        signal: str | None,
        signal_ids: list[int] | None,
    ) -> tuple[str | None, list[object]]:
        selects: list[str] = []
        params: list[object] = []

        # A frame-only attribute filter excludes events (they carry no id /
        # direction / decode status); an event-type filter excludes frames.
        # ``message`` matches decoded message names and event types, so it is
        # kept on both sides.
        if id_hex or direction or decode_status or signal or signal_ids:
            include_events = False
        if event_type:
            include_frames = False

        if include_frames:
            clauses, fparams = self._frame_filters(
                start_s, end_s, id_hex, message, direction, decode_status, signal,
                signal_ids,
            )
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            selects.append(
                f"""
                SELECT timestamp_s, seq, channel, 'frame' AS kind, id_hex,
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
                SELECT timestamp_s, seq, channel, 'event' AS kind, NULL AS id_hex,
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
        signal: str | None,
        signal_ids: list[int] | None,
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
        if signal and not signal_ids:
            clauses.append(
                """
                EXISTS (
                    SELECT 1 FROM samples s
                    WHERE s.timestamp_s = frames.timestamp_s
                      AND s.arbitration_id = frames.arbitration_id
                      AND lower(s.signal_name) LIKE ?
                )
                """
            )
            params.append(f"%{signal.lower()}%")
        if signal_ids:
            placeholders = ", ".join("?" for _ in signal_ids)
            clauses.append(f"arbitration_id IN ({placeholders})")
            params.extend(signal_ids)
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

    def present_signal_keys(self) -> set[tuple[str, str, int]]:
        rows = self._all(
            """
            SELECT DISTINCT message_name, signal_name, arbitration_id
            FROM samples
            ORDER BY message_name, signal_name, arbitration_id
            """
        )
        return {(r[0], r[1], int(r[2])) for r in rows}

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


def _f(value: object) -> float | None:
    """Coerce a DuckDB aggregate result to a plain float (NULL -> None)."""
    return None if value is None else float(value)


# -- opaque keyset cursors (AC9) ------------------------------------------
# A cursor is an opaque base64 token wrapping the canonical key of a boundary
# row and the direction to read from it: ``after``/``at`` page forward (``at``
# includes the boundary row, so a located row lands first on its page),
# ``before`` pages backward.
_CURSOR_MODES = {"after", "at", "before"}


def _encode_cursor(mode: str, timestamp_s: float, seq: int) -> str:
    payload = json.dumps({"m": mode, "t": float(timestamp_s), "s": int(seq)})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _decode_cursor(cursor: str | None) -> tuple[str | None, tuple[float, int] | None]:
    """Return ``(mode, (timestamp_s, seq))`` for a token, ``(None, None)`` for
    the first page. Raises ``ValueError`` on a malformed token."""
    if not cursor:
        return None, None
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        mode = payload["m"]
        key = (float(payload["t"]), int(payload["s"]))
    except (ValueError, KeyError, TypeError, binascii.Error) as exc:
        raise ValueError(f"Invalid trace cursor: {cursor!r}") from exc
    if mode not in _CURSOR_MODES:
        raise ValueError(f"Invalid trace cursor mode: {mode!r}")
    return mode, key


def _keyset_predicate(
    mode: str | None, key: tuple[float, int] | None
) -> tuple[str, list[object], bool]:
    """SQL keyset predicate, its params, and whether the page reads descending."""
    if mode is None or key is None:
        return "", [], False
    ts, seq = key
    if mode == "before":
        return "(timestamp_s < ? OR (timestamp_s = ? AND seq < ?))", [ts, ts, seq], True
    op = ">=" if mode == "at" else ">"
    return (
        f"(timestamp_s > ? OR (timestamp_s = ? AND seq {op} ?))",
        [ts, ts, seq],
        False,
    )


def _id_hex(arbitration_id: int, is_extended: bool) -> str:
    width = 8 if is_extended else 3
    return f"{arbitration_id:0{width}X}"


def _records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to JSON-safe dict rows (NaN/NaT -> None)."""
    clean = df.astype(object).where(pd.notnull(df), None)
    return clean.to_dict(orient="records")


def _frame_from_record(row: dict) -> RawCanFrame:
    data_hex = row.get("data_hex") or ""
    return RawCanFrame(
        timestamp_s=float(row["timestamp_s"]),
        channel=row.get("channel"),
        arbitration_id=int(row["arbitration_id"]),
        is_extended_id=bool(row["is_extended_id"]),
        dlc=int(row["dlc"]),
        data=bytes.fromhex(data_hex),
        direction=row.get("direction"),
        is_remote=bool(row["is_remote"]),
        message_name=row.get("message_name"),
        decode_status=row.get("decode_status"),
        dbc_source=row.get("dbc_source"),
    )
