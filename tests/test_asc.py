from pathlib import Path

from cantracediag.formats.asc import parse_asc

FIXTURE = Path(__file__).parent / "fixtures" / "sample.asc"
FIXTURE_DEC = Path(__file__).parent / "fixtures" / "sample_dec.asc"
FIXTURE_MALFORMED = Path(__file__).parent / "fixtures" / "malformed.asc"


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


def test_decimal_base_parses_ids_and_data() -> None:
    # CANalyzer "base dec": arbitration ids and data bytes are decimal, and
    # data frames carry trailing "Length =/BitCount =" tokens to be ignored.
    result = parse_asc(FIXTURE_DEC)
    assert result.base == "dec"
    assert result.parsed_frames == 2
    frame = result.frames[0]
    assert frame.arbitration_id == 1552  # 0x610
    assert frame.dlc == 7
    # decimal tokens "9 19 0 0 0 0 43" -> bytes 09 13 00 00 00 00 2b
    assert frame.data == bytes([9, 19, 0, 0, 0, 0, 43])
    # A byte value > 0xFF (231) must not be misread as hex and dropped.
    assert result.frames[1].data[0] == 231


# -- parsing integrity (AC12) ---------------------------------------------


def test_negative_and_scientific_timestamps_are_accepted() -> None:
    result = parse_asc(FIXTURE_MALFORMED)
    times = {f.timestamp_s for f in result.frames}
    assert -0.001 in times          # negative timestamp
    assert 0.0015 in times          # scientific notation 1.5e-3


def test_malformed_lines_become_explicit_anomalies_not_corrupt_frames() -> None:
    result = parse_asc(FIXTURE_MALFORMED)
    # Only the three well-formed lines yield frames; every byte matches its DLC.
    assert result.parsed_frames == 3
    for frame in result.frames:
        assert len(frame.data) == (0 if frame.is_remote else frame.dlc)
        assert all(0 <= b <= 0xFF for b in frame.data)

    anomalies = [e for e in result.events if e.event_type == "AscAnomaly"]
    reasons = " | ".join(e.detail or "" for e in anomalies)
    # One explicit anomaly per defective line, none silently dropped.
    assert len(anomalies) == 5
    assert "payload shorter than DLC" in reasons
    assert "payload longer than DLC" in reasons
    assert "out of range" in reasons
    assert "exceeds 8" in reasons
    assert "truncated data frame line" in reasons


def test_valid_frames_survive_alongside_anomalies() -> None:
    result = parse_asc(FIXTURE_MALFORMED)
    last = max(result.frames, key=lambda f: f.timestamp_s)
    assert last.data == bytes([0xAA, 0xBB])  # the trailing well-formed frame
