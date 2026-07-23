"""Reader for CANalyzer ASCII (``.asc``) trace files.

The parser normalizes an acquisition into :class:`RawCanFrame` objects and
:class:`NonDataEvent` objects. It is intentionally permissive: lines it does
not understand are preserved as ``Other`` events instead of being dropped, so
the trace view can still surface them (AC6).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from cantracediag.models import NonDataEvent, RawCanFrame

# A leading float timestamp is the reliable marker of a trace line. Negative and
# scientific-notation timestamps are accepted (AC12).
_TIMESTAMP = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+(.*)$")

# Classic CAN tops out at 8 data bytes; a larger DLC on a non-FD line is invalid.
_CLASSIC_MAX_DLC = 8


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


def stream_asc(
    path: str | Path,
    on_progress: Callable[[int], None] | None = None,
    progress_every: int = 5000,
) -> tuple[_Scanner, Iterator[RawCanFrame | NonDataEvent]]:
    """Stream frames/events and expose the scanner so the caller can read the
    detected numeric ``base`` after iteration completes.

    ``on_progress``, when given, is called with the current byte offset in
    the file every ``progress_every`` lines (and once more at end of file) so
    a caller can report import progress without pre-scanning the file.
    """

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

    frame, anomaly = _parse_data_frame(timestamp, tokens, base)
    if frame is not None:
        return frame, None
    if anomaly is not None:
        # A data-frame line that failed integrity checks becomes an explicit
        # import anomaly rather than a silently corrupted frame (AC12).
        channel = tokens[0] if tokens else None
        return None, NonDataEvent(timestamp, channel, "AscAnomaly", anomaly)

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
) -> tuple[RawCanFrame | None, str | None]:
    """Parse one data-frame line.

    Returns ``(frame, None)`` on success, ``(None, reason)`` when the line is a
    data-frame *attempt* that fails an integrity check (the caller records an
    explicit anomaly, AC12), or ``(None, None)`` when the line is not a data
    frame at all (the caller records a generic ``Other`` event).

    Expected shape: ``<channel> <id>[x] <dir> <d|r> <dlc> [data...] [meta...]``.
    """
    # A data frame is recognised by an Rx/Tx direction in the third column; any
    # other short line (e.g. "Start of measurement") is not a frame attempt.
    if len(tokens) < 3 or tokens[2] not in {"Rx", "Tx"}:
        return None, None
    if len(tokens) < 5:
        return None, "truncated data frame line"

    channel = tokens[0]
    id_token = tokens[1]
    is_extended = id_token.endswith(("x", "X"))
    id_clean = id_token[:-1] if is_extended else id_token
    arbitration_id = _parse_int(id_clean, base)
    if arbitration_id is None:
        return None, f"invalid arbitration id {id_token!r}"

    kind = tokens[3].lower()
    if kind not in {"d", "r"}:
        return None, f"invalid frame kind {tokens[3]!r} (expected 'd' or 'r')"
    is_remote = kind == "r"

    dlc = _parse_int(tokens[4], 10)
    if dlc is None or dlc < 0:
        return None, f"invalid DLC {tokens[4]!r}"
    if dlc > _CLASSIC_MAX_DLC:
        return None, f"classic CAN DLC {dlc} exceeds {_CLASSIC_MAX_DLC}"

    data = b""
    if not is_remote:
        if dlc == 0:
            return (
                RawCanFrame(
                    timestamp_s=timestamp,
                    channel=channel,
                    arbitration_id=arbitration_id,
                    is_extended_id=is_extended,
                    dlc=dlc,
                    data=data,
                    direction=tokens[2],
                    is_remote=is_remote,
                ),
                None,
            )
        # Leading numeric tokens are data bytes; the first non-numeric token
        # begins trailing metadata ("Length =/BitCount =") which is ignored.
        values: list[int] = []
        for tok in tokens[5:]:
            value = _parse_int(tok, base)
            if value is None:
                break
            values.append(value)
        if len(values) < dlc:
            return None, f"payload shorter than DLC ({len(values)} < {dlc})"
        if len(values) > dlc:
            return None, f"payload longer than DLC ({len(values)} > {dlc})"
        if any(v < 0 or v > 0xFF for v in values):
            return None, "data byte out of range 0..255"
        data = bytes(values)

    return (
        RawCanFrame(
            timestamp_s=timestamp,
            channel=channel,
            arbitration_id=arbitration_id,
            is_extended_id=is_extended,
            dlc=dlc,
            data=data,
            direction=tokens[2],
            is_remote=is_remote,
        ),
        None,
    )
