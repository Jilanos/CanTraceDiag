"""Vector BLF adapter: supported subset, diagnostics, and safety boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from blf_fixture import (
    ENGINE_DATA_ID,
    EXTENDED_ID,
    VEHICLE_STATE_ID,
    write_anomaly_blf,
    write_bulk_blf,
    write_corrupt_blf,
    write_non_blf_bytes,
    write_sample_blf,
)

from cantracediag.formats.blf import BlfImportError, parse_blf, stream_blf
from cantracediag.models import NonDataEvent, RawCanFrame


@pytest.fixture
def sample(tmp_path: Path) -> Path:
    return write_sample_blf(tmp_path / "sample.blf")


def test_supported_subset_normalizes_representative_frames(sample: Path) -> None:
    result = parse_blf(sample)

    assert [
        (f.timestamp_s, f.channel, hex(f.arbitration_id), f.is_extended_id, f.dlc,
         f.data.hex(), f.direction)
        for f in result.frames
    ] == [
        (0.0, "1", hex(ENGINE_DATA_ID), False, 8, "0010640000000000", "Rx"),
        (0.0, "1", hex(VEHICLE_STATE_ID), False, 2, "1027", "Rx"),
        (0.001, "2", hex(EXTENDED_ID), True, 3, "010203", "Tx"),
        (0.002, "1", hex(VEHICLE_STATE_ID), False, 0, "", "Rx"),
    ]
    assert all(f.is_remote is False for f in result.frames)
    assert result.object_count == 7
    assert result.parsed_frames == 4
    assert result.parsed_events == 3


def test_unsupported_objects_become_inspectable_events(sample: Path) -> None:
    result = parse_blf(sample)

    assert [(e.timestamp_s, e.channel, e.event_type) for e in result.events] == [
        (0.003, "1", "BlfRemoteRequest"),
        (0.004, "1", "ErrorFrame"),
        (0.005, "1", "BlfUnsupported"),
    ]
    # The CAN FD diagnostic names the object kind so an operator can tell why
    # the frame is missing from the trace rather than guessing.
    assert "CAN FD/XL" in (result.events[2].detail or "")


def test_stream_preserves_file_order(sample: Path) -> None:
    _, items = stream_blf(sample)
    kinds = ["frame" if isinstance(i, RawCanFrame) else "event" for i in items]
    assert kinds == ["frame"] * 4 + ["event"] * 3


def test_stream_reports_progress_up_to_the_file_size(sample: Path) -> None:
    offsets: list[int] = []
    _, items = stream_blf(sample, on_progress=offsets.append, progress_every=2)
    list(items)

    assert offsets, "streaming must report progress at least once"
    assert offsets == sorted(offsets)
    assert offsets[-1] == sample.stat().st_size


def test_an_invalid_object_does_not_contaminate_valid_frames(tmp_path: Path) -> None:
    result = parse_blf(write_anomaly_blf(tmp_path / "anomaly.blf"))

    assert [f.dlc for f in result.frames] == [8]
    assert [(e.event_type, e.detail) for e in result.events] == [
        ("BlfAnomaly", "classic CAN DLC 9 exceeds 8"),
    ]


def test_a_desynchronized_object_stream_fails_the_whole_import(tmp_path: Path) -> None:
    # A partial trace would look complete to the operator, so corruption stops
    # the import instead of publishing the frames read so far.
    with pytest.raises(BlfImportError):
        parse_blf(write_corrupt_blf(tmp_path / "corrupt.blf"))


def test_a_non_blf_file_is_rejected_at_open(tmp_path: Path) -> None:
    with pytest.raises(BlfImportError):
        parse_blf(write_non_blf_bytes(tmp_path / "not.blf"))


def test_streaming_never_materializes_the_whole_trace(tmp_path: Path) -> None:
    # Pulling one item must not require reading every object, which is what
    # keeps peak memory flat on a large acquisition.
    _, items = stream_blf(write_bulk_blf(tmp_path / "bulk.blf", 20_000))
    first = next(iter(items))

    assert isinstance(first, RawCanFrame)
    assert first.arbitration_id == ENGINE_DATA_ID


def test_bulk_input_normalizes_every_frame_in_order(tmp_path: Path) -> None:
    result = parse_blf(write_bulk_blf(tmp_path / "bulk.blf", 20_000))

    assert result.parsed_frames == 20_000
    assert result.parsed_events == 0
    assert [f.timestamp_s for f in result.frames[:3]] == [0.0, 0.001, 0.002]
    assert result.frames[-1].timestamp_s == pytest.approx(19.999)


def test_events_and_frames_share_the_normalized_models(sample: Path) -> None:
    result = parse_blf(sample)

    assert all(isinstance(f, RawCanFrame) for f in result.frames)
    assert all(isinstance(e, NonDataEvent) for e in result.events)
