"""Shared data models for raw CAN frames and decoded signals."""

from dataclasses import dataclass


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
    message_name: str | None = None
    decode_status: str = "not_decoded"


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
