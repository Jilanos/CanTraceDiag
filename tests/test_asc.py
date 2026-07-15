from pathlib import Path

from cantracediag.formats.asc import parse_asc

FIXTURE = Path(__file__).parent / "fixtures" / "sample.asc"


def test_parses_frames_and_events() -> None:
    result = parse_asc(FIXTURE)
    assert result.base == "hex"
    # 6 data frames, 2 non-data events (ErrorFrame + Status).
    assert result.parsed_frames == 6
    assert result.parsed_events == 2
    event_types = {e.event_type for e in result.events}
    assert "ErrorFrame" in event_types
    assert "Status" in event_types


def test_standard_and_extended_ids() -> None:
    result = parse_asc(FIXTURE)
    ids = {(f.arbitration_id, f.is_extended_id) for f in result.frames}
    assert (0x100, False) in ids
    assert (0x7FF, True) in ids


def test_data_bytes_and_dlc() -> None:
    result = parse_asc(FIXTURE)
    first = next(f for f in result.frames if f.arbitration_id == 0x100)
    assert first.dlc == 8
    assert first.data == bytes.fromhex("0010640000000000")
    assert first.direction == "Rx"
