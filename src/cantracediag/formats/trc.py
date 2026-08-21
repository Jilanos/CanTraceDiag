"""Reader for the verified PCAN-View text ``.trc`` v1.1 layout.

The reader accepts classic CAN data frames only.  Every record it recognizes
but cannot safely normalize is retained as a :class:`NonDataEvent`, so a bad
record never turns into a malformed frame.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from cantracediag.models import NonDataEvent, RawCanFrame

_RECORD = re.compile(r"^\s*(\d+)\)\s*([+-]?\d+(?:\.\d+)?)\s+(.*)$")
_HEX = re.compile(r"^[0-9a-fA-F]+$")
_CLASSIC_MAX_DLC = 8


@dataclass(slots=True)
class TrcParseResult:
    frames: list[RawCanFrame]
    events: list[NonDataEvent]
    line_count: int
    parsed_frames: int
    parsed_events: int


class _Scanner:
    def __init__(self) -> None:
        self.parsed_lines = 0

    def feed(self, raw_line: str) -> tuple[RawCanFrame | None, NonDataEvent | None]:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(";"):
            return None, None
        match = _RECORD.match(stripped)
        if not match:
            return None, None
        self.parsed_lines += 1
        timestamp_s = float(match.group(2)) / 1000
        return _parse_record(timestamp_s, match.group(3))


def parse_trc(path: str | Path) -> TrcParseResult:
    frames: list[RawCanFrame] = []
    events: list[NonDataEvent] = []
    scanner = _Scanner()
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            frame, event = scanner.feed(line)
            if frame is not None:
                frames.append(frame)
            if event is not None:
                events.append(event)
    return TrcParseResult(frames, events, scanner.parsed_lines, len(frames), len(events))


def stream_trc(
    path: str | Path,
    on_progress: Callable[[int], None] | None = None,
    progress_every: int = 5000,
) -> tuple[_Scanner, Iterator[RawCanFrame | NonDataEvent]]:
    """Stream normalized classic-CAN frames and diagnostic events."""
    scanner = _Scanner()

    def _gen() -> Iterator[RawCanFrame | NonDataEvent]:
        with open(path, encoding="utf-8", errors="replace") as handle:
            line_no = 0
            while line := handle.readline():
                line_no += 1
                frame, event = scanner.feed(line)
                if frame is not None:
                    yield frame
                if event is not None:
                    yield event
                if on_progress is not None and line_no % progress_every == 0:
                    on_progress(handle.tell())
            if on_progress is not None:
                on_progress(handle.tell())

    return scanner, _gen()


def _parse_record(timestamp_s: float, body: str) -> tuple[RawCanFrame | None, NonDataEvent | None]:
    tokens = body.split()
    if not tokens:
        return None, NonDataEvent(timestamp_s, None, "TrcAnomaly", "empty record")
    kind = tokens[0].lower()
    if kind in {"warning", "warn", "error"}:
        return None, NonDataEvent(timestamp_s, None, f"Trc{kind.title()}", body)
    if kind in {"canfd", "canxl", "lin", "flexray"}:
        return None, NonDataEvent(timestamp_s, None, "TrcUnsupported", body)
    if kind not in {"rx", "tx"}:
        return None, NonDataEvent(
            timestamp_s, None, "TrcAnomaly", f"unsupported record type {tokens[0]!r}"
        )
    if len(tokens) >= 2 and tokens[1].lower() in {"rtr", "remote"}:
        return None, NonDataEvent(timestamp_s, None, "TrcRemoteRequest", body)
    if len(tokens) < 3:
        return None, NonDataEvent(timestamp_s, None, "TrcAnomaly", "truncated classic CAN record")

    id_token, dlc_token = tokens[1:3]
    is_extended = id_token.endswith(("x", "X"))
    id_text = id_token[:-1] if is_extended else id_token
    if not _HEX.fullmatch(id_text):
        return None, NonDataEvent(
            timestamp_s, None, "TrcAnomaly", f"invalid arbitration id {id_token!r}"
        )
    arbitration_id = int(id_text, 16)
    if arbitration_id > (0x1FFFFFFF if is_extended else 0x7FF):
        return None, NonDataEvent(
            timestamp_s, None, "TrcAnomaly", f"arbitration id out of range {id_token!r}"
        )
    try:
        dlc = int(dlc_token, 10)
    except ValueError:
        return None, NonDataEvent(timestamp_s, None, "TrcAnomaly", f"invalid DLC {dlc_token!r}")
    if not 0 <= dlc <= _CLASSIC_MAX_DLC:
        return None, NonDataEvent(
            timestamp_s, None, "TrcAnomaly", f"classic CAN DLC {dlc} exceeds {_CLASSIC_MAX_DLC}"
        )
    payload = tokens[3:]
    if len(payload) != dlc:
        detail = f"payload length {len(payload)} does not match DLC {dlc}"
        return None, NonDataEvent(
            timestamp_s, None, "TrcAnomaly", detail
        )
    if any(not _HEX.fullmatch(byte) or len(byte) > 2 for byte in payload):
        return None, NonDataEvent(
            timestamp_s, None, "TrcAnomaly", "invalid hexadecimal payload byte"
        )
    return RawCanFrame(
        timestamp_s=timestamp_s,
        channel="1",
        arbitration_id=arbitration_id,
        is_extended_id=is_extended,
        dlc=dlc,
        data=bytes(int(byte, 16) for byte in payload),
        direction=tokens[0].title(),
        is_remote=False,
    ), None
