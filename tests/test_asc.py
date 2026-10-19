from pathlib import Path

from cantracediag.formats.asc import parse_asc
from cantracediag.formats.trc import parse_trc

FIXTURE = Path(__file__).parent / "fixtures" / "sample.asc"
FIXTURE_DEC = Path(__file__).parent / "fixtures" / "sample_dec.asc"
FIXTURE_MALFORMED = Path(__file__).parent / "fixtures" / "malformed.asc"
TRC_FIXTURE = Path(__file__).parent / "fixtures" / "sample.trc"
TRC_MALFORMED = Path(__file__).parent / "fixtures" / "malformed.trc"


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


def test_dlc_zero_ignores_trailing_numeric_metadata(tmp_path: Path) -> None:
    asc = tmp_path / "dlc_zero.asc"
    asc.write_text(
        "date Thu Jul 23 00:00:00.000 2026\n"
        "base hex timestamps absolute\n"
        "   0.000000 1 100 Rx d 0 8 64 Length = 0 BitCount = 42\n"
    )
    result = parse_asc(asc)
    assert result.parsed_frames == 1
    assert result.parsed_events == 0
    frame = result.frames[0]
    assert frame.dlc == 0
    assert frame.data == b""


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


def test_trc_v11_normalizes_representative_records() -> None:
    result = parse_trc(TRC_FIXTURE)
    assert result.parsed_frames == 4
    assert result.parsed_events == 0
    assert [(f.timestamp_s, f.direction, f.arbitration_id, f.data) for f in result.frames] == [
        (0.0, "Rx", 0x414, bytes.fromhex("F0069C")),
        (0.0009, "Rx", 0x1A1, bytes.fromhex("7E7F8EAFF04E0124")),
        (0.02, "Rx", 0x414, bytes.fromhex("F0069C")),
        (0.0399, "Tx", 0x600, bytes.fromhex("0000")),
    ]


def test_trc_invalid_records_become_inspectable_events() -> None:
    result = parse_trc(TRC_MALFORMED)
    assert result.parsed_frames == 2
    assert {event.event_type for event in result.events} == {
        "TrcAnomaly", "TrcRemoteRequest", "TrcUnsupported", "TrcWarning"
    }
    assert all(len(frame.data) == frame.dlc for frame in result.frames)


def _scan_all(lines: list[str], fast: bool) -> list:
    from cantracediag.formats.asc import _Scanner

    scanner = _Scanner(fast=fast)
    out = [scanner.feed(line) for line in lines]
    return [out, scanner.base, scanner.parsed_lines]


def test_fast_path_matches_general_parser_exactly(tmp_path: Path) -> None:
    """The data-frame fast path must build exactly what the general path builds."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen", Path(__file__).parents[1] / "scripts" / "generate_large_asc.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    generated = tmp_path / "g.asc"
    gen.generate(generated, 400_000)
    lines = generated.read_text().splitlines(keepends=True)
    for name in ("sample.asc", "sample_dec.asc", "malformed.asc", "same_timestamp.asc",
                 "repeated_events.asc"):
        lines += (FIXTURE.parent / name).read_text().splitlines(keepends=True)
    lines += [
        "base hex  timestamps absolute\n",
        "   1.000000 1  100             Rx   d 8 00 10 64 00 00 00 00 00\n",
        "1.0 1 100 Rx d 8 00 10 64 00 00 00 00\n",           # payload shorter than DLC
        "1.0 1 100 Rx d 2 00 10 64\n",                       # payload longer than DLC
        "1.0 1 100 Rx d 0 00\n",                             # DLC 0 ignores trailing tokens
        "1.0 1 100 Rx d 0\n",
        "1.0 1 1FFFFFFFx Tx d 1 FF\r\n",
        "1.0 1 1fffffffX Tx d 1 ff\n",                       # upper-case X: general path
        "1.0 1 100 Rx d 8 0 1 2 3 4 5 6 7\n",               # single-digit bytes
        "1.0 1 100 Rx d 2 00 10  Length = 1 BitCount = 2\n",
        "1.0 1 100 Rx r 2\n",
        "1.0 1 100 Rx d 9 00 00 00 00 00 00 00 00 00\n",
        "1.0\t2\t7FF\tRx\td\t1\t0A\n",
        "1.0 1 100 Rx d 1 0A \n",
        "-1.5 1 100 Rx d 1 0A\n",
        "1e-3 1 100 Rx d 1 0A\n",
        "1.0 CANFD 1 Rx 100 d 1 0A\n",
        "1.0 1 Status:chip status error active\n",
        "1.0 1 ErrorFrame\n",
        "1.0 1 123456789 Rx d 1 0A\n",                      # 9 hex digits
        "1.0 1 100 Rx d 1 ٠١\n",                              # non-ASCII digits
        "base dec\n",
        "1.0 1 256 Rx d 2 16 39\n",
        "1.0 1 100 Rx d 1 10\n",
        "base hex\n",
        "1.0 1 100 Rx d 1 10\n",
    ]
    fast, general = _scan_all(lines, True), _scan_all(lines, False)
    assert fast == general
