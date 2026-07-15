from pathlib import Path

from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.models import (
    DECODE_ERROR,
    DECODE_NO_DB,
    DECODE_OK,
    DECODE_UNKNOWN_ID,
    RawCanFrame,
)

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


def test_truncated_payload_is_visible_decode_error() -> None:
    decoder = Decoder(_catalog().message_index())
    frame = RawCanFrame(0.0, "1", 0x100, False, 8, b"\x00", direction="Rx")
    updated, samples = decoder.decode_frame(frame)
    assert updated.decode_status == DECODE_ERROR
    assert updated.message_name == "EngineData"
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


def test_same_message_name_with_different_definition_is_ambiguous(tmp_path: Path) -> None:
    other = tmp_path / "v2.dbc"
    other.write_text(
        'VERSION ""\nNS_ :\nBS_:\nBU_: ECU\n'
        "BO_ 256 EngineData: 8 ECU\n"
        ' SG_ EngineSpeed : 0|16@1+ (0.5,0) [0|32767.5] "rpm" Vector__XXX\n'
        ' SG_ EngineTorque : 16|16@1+ (1,0) [0|65535] "Nm" Vector__XXX\n'
    )
    catalog = DbcCatalog()
    catalog.load(DBC)
    catalog.load(other)
    ambiguous = catalog.find_ambiguous_ids()
    assert 0x100 in ambiguous
    assert any("v2.dbc:EngineData" == choice for choice in ambiguous[0x100])


def test_equivalent_duplicate_definition_is_not_ambiguous(tmp_path: Path) -> None:
    clone = tmp_path / "clone.dbc"
    clone.write_text(DBC.read_text())
    catalog = DbcCatalog()
    catalog.load(DBC)
    catalog.load(clone)
    assert 0x100 not in catalog.find_ambiguous_ids()


def test_multiplexed_duplicate_definition_is_hashable(tmp_path: Path) -> None:
    multiplexed = tmp_path / "multiplexed.dbc"
    multiplexed.write_text(
        'VERSION ""\nNS_ :\nBS_:\nBU_: ECU\n'
        "BO_ 1024 MultiplexedData: 8 ECU\n"
        ' SG_ Mode M : 0|8@1+ (1,0) [0|255] "" Vector__XXX\n'
        ' SG_ ValueA m1 : 8|8@1+ (1,0) [0|255] "" Vector__XXX\n'
        ' SG_ ValueB m2 : 8|8@1+ (1,0) [0|255] "" Vector__XXX\n'
    )
    clone = tmp_path / "multiplexed_clone.dbc"
    clone.write_text(multiplexed.read_text())

    catalog = DbcCatalog()
    catalog.load(multiplexed)
    catalog.load(clone)

    assert 0x400 not in catalog.find_ambiguous_ids()
