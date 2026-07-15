"""Reader for CANalyzer ASCII (``.asc``) trace files.

The parser normalizes an acquisition into :class:`RawCanFrame` objects and
:class:`NonDataEvent` objects. It is intentionally permissive: lines it does
not understand are preserved as ``Other`` events instead of being dropped, so
the trace view can still surface them (AC6).
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from cantracediag.models import NonDataEvent, RawCanFrame

# A leading float timestamp is the reliable marker of a trace line.
_TIMESTAMP = re.compile(r"^\s*(\d+(?:\.\d+)?)\s+(.*)$")


@dataclass(slots=True)
class AscParseResult:
    frames: list[RawCanFrame]
    events: list[NonDataEvent]
    base: str
    line_count: int
    parsed_frames: int
    parsed_events: int


def _parse_int(token: str, base: int) -> int | None:
    try:
        return int(token, base)
    except ValueError:
        return None


class _Scanner:
    """Line-oriented ASC scanner that tracks the current numeric base."""

    def __init__(self) -> None:
        self.base = "hex"
        self.parsed_lines = 0

    def feed(self, raw_line: str) -> tuple[RawCanFrame | None, NonDataEvent | None]:
        stripped = raw_line.strip()
        if not stripped:
            return None, None

        lowered = stripped.lower()
        if lowered.startswith("base"):
            self.base = "dec" if "dec" in lowered else "hex"
            return None, None
        if _is_header(stripped):
            return None, None

        match = _TIMESTAMP.match(raw_line.rstrip("\n"))
        if not match:
            return None, None

        self.parsed_lines += 1
        timestamp = float(match.group(1))
        rest = match.group(2).strip()
        return _parse_body(timestamp, rest, self.base)


def parse_asc(path: str | Path) -> AscParseResult:
    """Parse an ASC file eagerly into frames and events."""

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

    return AscParseResult(
        frames=frames,
        events=events,
        base=scanner.base,
        line_count=scanner.parsed_lines,
        parsed_frames=len(frames),
        parsed_events=len(events),
    )


def iter_asc(path: str | Path) -> Iterator[RawCanFrame | NonDataEvent]:
    """Stream frames and events without holding the whole file in memory."""

    scanner = _Scanner()
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            frame, event = scanner.feed(line)
            if frame is not None:
                yield frame
            if event is not None:
                yield event


def stream_asc(path: str | Path) -> tuple[_Scanner, Iterator[RawCanFrame | NonDataEvent]]:
    """Stream frames/events and expose the scanner so the caller can read the
    detected numeric ``base`` after iteration completes."""

    scanner = _Scanner()

    def _gen() -> Iterator[RawCanFrame | NonDataEvent]:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                frame, event = scanner.feed(line)
                if frame is not None:
                    yield frame
                if event is not None:
                    yield event

    return scanner, _gen()


def _is_header(stripped: str) -> bool:
    lowered = stripped.lower()
    if lowered.startswith("//"):
        return True
    if lowered.startswith(("begin triggerblock", "end triggerblock")):
        return True
    # Header lines start with a keyword rather than a numeric timestamp.
    first = stripped.split(maxsplit=1)[0].lower()
    return first in {"date", "base", "no", "measurement", "internal", "version"}


def _parse_body(
    timestamp: float, rest: str, base_name: str
) -> tuple[RawCanFrame | None, NonDataEvent | None]:
    tokens = rest.split()
    if not tokens:
        return None, None

    base = 16 if base_name == "hex" else 10

    # Non-data events. Channel may or may not be present before the keyword.
    if tokens[0].lower().startswith("errorframe"):
        return None, NonDataEvent(timestamp, None, "ErrorFrame", rest or None)
    if len(tokens) >= 2 and tokens[1].lower().startswith("errorframe"):
        return None, NonDataEvent(timestamp, tokens[0], "ErrorFrame",
                                  " ".join(tokens[2:]) or None)
    if _looks_like_status(tokens):
        channel, detail = _status_fields(tokens)
        return None, NonDataEvent(timestamp, channel, "Status", detail)
    if tokens[0].upper() == "CANFD" or (len(tokens) > 1 and tokens[1].upper() == "CANFD"):
        # CAN FD is out of MVP scope; preserve the raw line so nothing is lost.
        return None, NonDataEvent(timestamp, None, "CANFD", rest)

    frame = _parse_data_frame(timestamp, tokens, base)
    if frame is not None:
        return frame, None

    return None, NonDataEvent(timestamp, None, "Other", rest)


def _looks_like_status(tokens: list[str]) -> bool:
    return any(tok.lower().startswith("status") for tok in tokens[:4])


def _status_fields(tokens: list[str]) -> tuple[str | None, str | None]:
    channel = None
    if tokens and tokens[0].upper() == "CAN" and len(tokens) > 1:
        channel = tokens[1]
    elif tokens and tokens[0].isdigit():
        channel = tokens[0]
    return channel, " ".join(tokens)


def _parse_data_frame(
    timestamp: float, tokens: list[str], base: int
) -> RawCanFrame | None:
    # Expected shape: <channel> <id>[x] <dir> <d|r> <dlc> [data...]
    if len(tokens) < 5:
        return None

    channel = tokens[0]
    id_token = tokens[1]
    is_extended = id_token.endswith(("x", "X"))
    id_clean = id_token[:-1] if is_extended else id_token
    arbitration_id = _parse_int(id_clean, base)
    if arbitration_id is None:
        return None

    direction = tokens[2]
    if direction not in {"Rx", "Tx"}:
        return None

    kind = tokens[3].lower()
    if kind not in {"d", "r"}:
        return None
    is_remote = kind == "r"

    dlc = _parse_int(tokens[4], 10)
    if dlc is None or dlc < 0 or dlc > 64:
        return None

    data = b""
    if not is_remote:
        data_tokens = tokens[5:5 + dlc]
        try:
            # Data bytes use the same numeric base as the file header
            # (CANalyzer "base dec" emits decimal byte values).
            data = bytes(int(byte, base) for byte in data_tokens)
        except ValueError:
            return None

    return RawCanFrame(
        timestamp_s=timestamp,
        channel=channel,
        arbitration_id=arbitration_id,
        is_extended_id=is_extended,
        dlc=dlc,
        data=data,
        direction=direction,
        is_remote=is_remote,
    )
