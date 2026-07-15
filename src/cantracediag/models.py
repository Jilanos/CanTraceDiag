"""Shared data models for raw CAN frames, decoded signals, and events."""

from __future__ import annotations

from dataclasses import dataclass, field

# Decode status values kept as plain strings so they survive Parquet/DuckDB
# round-trips without custom converters.
DECODE_OK = "ok"
DECODE_NO_DB = "no_database"
DECODE_UNKNOWN_ID = "unknown_id"
DECODE_ERROR = "decode_error"
DECODE_NOT_DECODED = "not_decoded"


@dataclass(frozen=True, slots=True)
class RawCanFrame:
    """Normalized representation of one CAN frame from an acquisition trace."""

    timestamp_s: float
    channel: str | None
    arbitration_id: int
    is_extended_id: bool
    dlc: int
    data: bytes
    direction: str | None = None
    is_remote: bool = False
    message_name: str | None = None
    decode_status: str = DECODE_NOT_DECODED


@dataclass(frozen=True, slots=True)
class NonDataEvent:
    """A non-data trace event such as ErrorFrame or a CAN status change."""

    timestamp_s: float
    channel: str | None
    event_type: str
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class DecodedSignalSample:
    """One decoded physical signal sample."""

    timestamp_s: float
    channel: str | None
    arbitration_id: int
    message_name: str
    signal_name: str
    value: float | int | str | None
    unit: str | None = None
    raw_value: int | None = None
    quality: str = "ok"


@dataclass(frozen=True, slots=True)
class SignalInfo:
    """Catalog entry describing a signal available for plotting."""

    message_name: str
    signal_name: str
    arbitration_id: int
    is_extended_id: bool
    unit: str | None
    minimum: float | None
    maximum: float | None
    databases: tuple[str, ...] = field(default_factory=tuple)
