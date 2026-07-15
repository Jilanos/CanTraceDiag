from pathlib import Path

from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.models import DECODE_NO_DB, DECODE_OK, DECODE_UNKNOWN_ID, RawCanFrame

DBC = Path(__file__).parent / "fixtures" / "sample.dbc"


def _catalog() -> DbcCatalog:
    catalog = DbcCatalog()
    catalog.load(DBC)
    return catalog


def test_signal_catalog_lists_all_signals() -> None:
    signals = _catalog().signals()
    names = {(s.message_name, s.signal_name) for s in signals}
    assert ("EngineData", "EngineSpeed") in names
    assert ("VehicleState", "VehicleSpeed") in names


def test_decode_produces_physical_values() -> None:
    decoder = Decoder(_catalog().message_index())
    frame = RawCanFrame(0.0, "1", 0x100, False, 8, bytes.fromhex("0010640000000000"),
                        direction="Rx")
    updated, samples = decoder.decode_frame(frame)
    assert updated.decode_status == DECODE_OK
    assert updated.message_name == "EngineData"
    speed = next(s for s in samples if s.signal_name == "EngineSpeed")
    assert speed.value == 1024.0  # 0x1000 little-endian * 0.25
    assert speed.unit == "rpm"


def test_unknown_id_is_preserved() -> None:
    decoder = Decoder(_catalog().message_index())
    frame = RawCanFrame(0.0, "1", 0x999, False, 1, b"\x00", direction="Rx")
    updated, samples = decoder.decode_frame(frame)
    assert updated.decode_status == DECODE_UNKNOWN_ID
    assert samples == []


def test_no_database_marks_status() -> None:
    decoder = Decoder(None)
    frame = RawCanFrame(0.0, "1", 0x100, False, 8, b"\x00" * 8, direction="Rx")
    updated, samples = decoder.decode_frame(frame)
    assert updated.decode_status == DECODE_NO_DB
    assert samples == []


def test_ambiguous_ids_detected(tmp_path: Path) -> None:
    # A second DBC that reuses id 0x100 with a different message name.
    other = tmp_path / "other.dbc"
    other.write_text(
        'VERSION ""\nNS_ :\nBS_:\nBU_: ECU\n'
        "BO_ 256 BrakeData: 1 ECU\n"
        ' SG_ BrakePressure : 0|8@1+ (1,0) [0|255] "bar" Vector__XXX\n'
    )
    catalog = DbcCatalog()
    catalog.load(DBC)
    catalog.load(other)
    ambiguous = catalog.find_ambiguous_ids()
    assert 0x100 in ambiguous
