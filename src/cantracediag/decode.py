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

    def decode_frame(
        self, frame: RawCanFrame
    ) -> tuple[RawCanFrame, list[DecodedSignalSample]]:
        if not self._has_db:
            return replace(frame, decode_status=DECODE_NO_DB), []

        entries = self._index.get(frame.arbitration_id)
        if not entries:
            return replace(frame, decode_status=DECODE_UNKNOWN_ID), []

        # When several DBCs claim the same id, honour the operator's resolution
        # if one was made; otherwise take the first. Remaining ambiguity is
        # surfaced separately via DbcCatalog.find_ambiguous_ids.
        picked = self._pick(frame.arbitration_id, entries)
        if picked is None:
            return replace(frame, decode_status=DECODE_AMBIGUOUS_ID), []
        db_name, message = picked
        if frame.is_remote:
            return replace(
                frame, message_name=message.name, decode_status=DECODE_OK,
                dbc_source=db_name,
            ), []

        try:
            decoded = message.decode(
                frame.data, decode_choices=False, allow_truncated=False
            )
        except Exception:
            return replace(
                frame, message_name=message.name, decode_status=DECODE_ERROR,
                dbc_source=db_name,
            ), []

        samples = self._to_samples(frame, message, decoded)
        updated = replace(
            frame, message_name=message.name, decode_status=DECODE_OK,
            dbc_source=db_name,
        )
        return updated, samples

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
