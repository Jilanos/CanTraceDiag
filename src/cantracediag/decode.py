"""Decoding of raw CAN frames into physical signal samples.

Decoding never discards data: every frame is returned with an updated
``decode_status`` and ``message_name`` (AC3), and decode failures are recorded
rather than dropped so they remain visible in the trace view (AC6).
"""

from __future__ import annotations

from dataclasses import replace

from cantools.database.can import Message

from cantracediag.models import (
    DECODE_AMBIGUOUS_ID,
    DECODE_ERROR,
    DECODE_NO_DB,
    DECODE_OK,
    DECODE_UNKNOWN_ID,
    DecodedSignalSample,
    RawCanFrame,
)


class Decoder:
    """Decodes frames against a merged DBC message index."""

    def __init__(
        self,
        message_index: dict[int, list[tuple[str, Message]]] | None,
        resolution: dict[int, str] | None = None,
        ambiguous_ids: set[int] | None = None,
    ):
        self._index = message_index or {}
        self._has_db = bool(message_index)
        # Per-arbitration-id operator choice of which DBC owns a conflicting id
        # (AC10). Maps arbitration_id -> database name.
        self._resolution = resolution or {}
        self._ambiguous_ids = ambiguous_ids or set()
        self._described: dict[int, tuple[str, Message | None, str | None]] = {}
        self._units: dict[str, dict[str, str | None]] = {}

    def decode_frame(
        self, frame: RawCanFrame
    ) -> tuple[RawCanFrame, list[DecodedSignalSample]]:
        updated, message = self.describe_frame(frame)
        if message is None or updated.is_remote or updated.decode_status != DECODE_OK:
            return updated, []

        try:
            decoded = message.decode(
                frame.data, decode_choices=False, allow_truncated=False
            )
        except Exception:
            return replace(updated, decode_status=DECODE_ERROR), []

        return updated, self._to_samples(updated, message, decoded)

    def describe_frame(self, frame: RawCanFrame) -> tuple[RawCanFrame, Message | None]:
        """Resolve message metadata without materializing every signal sample.

        The outcome depends only on the arbitration id (the index and the
        operator resolution are fixed for this decoder), so it is memoized per
        id; this runs once per frame of a full import.
        """
        resolved = self._described.get(frame.arbitration_id)
        if resolved is None:
            resolved = self._describe_id(frame.arbitration_id)
            self._described[frame.arbitration_id] = resolved
        status, message, db_name = resolved
        updated = RawCanFrame(
            frame.timestamp_s, frame.channel, frame.arbitration_id, frame.is_extended_id,
            frame.dlc, frame.data, frame.direction, frame.is_remote,
            message.name if message is not None else frame.message_name,
            status,
            db_name if message is not None else frame.dbc_source,
        )
        return updated, message

    def _describe_id(self, arbitration_id: int) -> tuple[str, Message | None, str | None]:
        if not self._has_db:
            return DECODE_NO_DB, None, None
        entries = self._index.get(arbitration_id)
        if not entries:
            return DECODE_UNKNOWN_ID, None, None
        # When several DBCs claim the same id, honour the operator's resolution
        # if one was made; otherwise take the first. Remaining ambiguity is
        # surfaced separately via DbcCatalog.find_ambiguous_ids.
        picked = self._pick(arbitration_id, entries)
        if picked is None:
            return DECODE_AMBIGUOUS_ID, None, None
        db_name, message = picked
        return DECODE_OK, message, db_name

    def decode_signal(
        self, frame: RawCanFrame, message_name: str, signal_name: str
    ) -> DecodedSignalSample | None:
        """Decode one signal from one frame, preserving no-interpolation semantics."""
        updated, message = self.describe_frame(frame)
        if (
            message is None
            or updated.is_remote
            or updated.decode_status != DECODE_OK
            or message.name != message_name
        ):
            return None
        try:
            decoded = message.decode(
                updated.data, decode_choices=False, allow_truncated=False
            )
        except Exception:
            return None
        if signal_name not in decoded:
            return None
        units = self._units.get(message.name)
        if units is None:
            units = self._units[message.name] = {sig.name: sig.unit for sig in message.signals}
        value = decoded[signal_name]
        numeric = _numeric(value)
        return DecodedSignalSample(
            timestamp_s=updated.timestamp_s,
            channel=updated.channel,
            arbitration_id=updated.arbitration_id,
            message_name=message.name,
            signal_name=signal_name,
            value=numeric if numeric is not None else _as_text(value),
            unit=units.get(signal_name),
        )

    def _pick(
        self, arbitration_id: int, entries: list[tuple[str, Message]]
    ) -> tuple[str, Message] | None:
        chosen = self._resolution.get(arbitration_id)
        if chosen is not None:
            for db_name, message in entries:
                if db_name == chosen:
                    return db_name, message
        if arbitration_id in self._ambiguous_ids and len(entries) > 1:
            return None
        return entries[0]

    def _to_samples(
        self, frame: RawCanFrame, message: Message, decoded: dict
    ) -> list[DecodedSignalSample]:
        units = {sig.name: sig.unit for sig in message.signals}
        samples: list[DecodedSignalSample] = []
        for signal_name, value in decoded.items():
            numeric = _numeric(value)
            samples.append(
                DecodedSignalSample(
                    timestamp_s=frame.timestamp_s,
                    channel=frame.channel,
                    arbitration_id=frame.arbitration_id,
                    message_name=message.name,
                    signal_name=signal_name,
                    value=numeric if numeric is not None else _as_text(value),
                    unit=units.get(signal_name),
                )
            )
        return samples


def _numeric(value: object) -> float | int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    # cantools NamedSignalValue carries an integer .value for enum choices.
    inner = getattr(value, "value", None)
    if isinstance(inner, (int, float)):
        return inner
    return None


def _as_text(value: object) -> str | None:
    return None if value is None else str(value)
