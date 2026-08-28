"""BLF imports through the shared pipeline, API, and export contracts.

The point of these tests is that there is nothing BLF-specific downstream: once
the adapter has normalized a container, every consumer is the one ASC and TRC
already use. They assert the shared behaviour, not a parallel BLF path.
"""

from __future__ import annotations

import io
import threading
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from blf_fixture import (
    ENGINE_DATA_ID,
    VEHICLE_STATE_ID,
    write_bulk_blf,
    write_corrupt_blf,
    write_sample_blf,
)
from starlette.testclient import TestClient

from cantracediag.pipeline import ImportCancelled, import_trace

FIX = Path(__file__).parent / "fixtures"
DBC = FIX / "sample.dbc"


@pytest.fixture
def blf(tmp_path: Path) -> Path:
    return write_sample_blf(tmp_path / "sample.blf")


def _import_blf(client: TestClient, blf: Path):
    return client.post(
        "/api/import",
        json={"trace_path": str(blf), "dbc_paths": [str(DBC)]},
    )


# -- pipeline ---------------------------------------------------------------
def test_blf_imports_through_the_normalized_pipeline(blf: Path) -> None:
    store, result = import_trace(blf, [DBC], decode_samples=True)

    summary = result.summary
    assert summary["frames"] == 4
    assert summary["events"] == 3
    # Two decode: the 8-byte EngineData frame and the 2-byte VehicleState one.
    # The extended id is unknown to sample.dbc, and the zero-DLC VehicleState
    # frame is too short for its message definition.
    assert summary["decoded_frames"] == 2
    assert summary["unique_ids"] == 3
    assert summary["start_s"] == 0.0
    assert summary["end_s"] == 0.005
    store.close()


def test_blf_frames_decode_against_the_shared_dbc_decoder(blf: Path) -> None:
    store, _ = import_trace(blf, [DBC], decode_samples=True)

    series = store.signal_series("EngineData", "EngineSpeed")
    assert series["unit"] == "rpm"
    assert series["t"] == sorted(series["t"])
    assert len(series["v"]) == 1
    store.close()


def test_blf_trace_rows_merge_frames_and_events_in_file_order(blf: Path) -> None:
    store, _ = import_trace(blf, [DBC], decode_samples=True)

    page = store.trace_rows(limit=100)
    assert page["total"] == 7
    # The two frames sharing timestamp 0.0 keep their file order, and the
    # diagnostics follow the frames, because seq is assigned as objects arrive.
    assert [row["kind"] for row in page["rows"]] == ["frame"] * 4 + ["event"] * 3
    assert [row["timestamp_s"] for row in page["rows"]] == sorted(
        row["timestamp_s"] for row in page["rows"]
    )
    assert page["rows"][0]["id_hex"] == f"{ENGINE_DATA_ID:03X}"
    assert page["rows"][1]["id_hex"] == f"{VEHICLE_STATE_ID:03X}"
    store.close()


def test_blf_diagnostics_appear_in_the_shared_event_summary(blf: Path) -> None:
    store, result = import_trace(blf, [DBC])

    assert result.summary["event_types"] == {
        "BlfRemoteRequest": 1,
        "ErrorFrame": 1,
        "BlfUnsupported": 1,
    }
    store.close()


def test_blf_import_reports_monotonic_progress(tmp_path: Path) -> None:
    fractions: list[float] = []
    store, _ = import_trace(
        write_bulk_blf(tmp_path / "bulk.blf", 20_000), on_progress=fractions.append
    )

    assert fractions == sorted(fractions)
    assert 0.0 <= fractions[0] <= fractions[-1] <= 1.0
    assert fractions[-1] == 1.0
    store.close()


def test_blf_import_honours_cancellation(tmp_path: Path) -> None:
    cancel = threading.Event()
    cancel.set()

    with pytest.raises(ImportCancelled):
        import_trace(write_bulk_blf(tmp_path / "bulk.blf", 5_000), cancel_check=cancel.is_set)


def test_a_corrupt_blf_publishes_no_trace(tmp_path: Path) -> None:
    with pytest.raises(Exception) as excinfo:
        import_trace(write_corrupt_blf(tmp_path / "corrupt.blf"), [DBC])

    assert "BLF" in str(excinfo.value)


# -- API --------------------------------------------------------------------
def test_path_import_accepts_a_blf_trace(client: TestClient, blf: Path) -> None:
    r = _import_blf(client, blf)

    assert r.status_code == 200
    assert r.json()["summary"]["frames"] == 4
    assert client.get("/api/status").json()["loaded"] is True


def test_upload_import_accepts_a_blf_trace(client: TestClient, blf: Path) -> None:
    r = client.post(
        "/api/import-files",
        files=[
            ("trace", ("sample.blf", blf.read_bytes(), "application/octet-stream")),
            ("dbcs", ("sample.dbc", DBC.read_bytes(), "application/octet-stream")),
        ],
    )

    assert r.status_code == 200
    assert r.json()["summary"]["frames"] == 4
    assert client.get("/api/trace", params={"limit": 100}).json()["total"] == 7


def test_upload_import_still_rejects_an_unsupported_suffix(client: TestClient) -> None:
    r = client.post(
        "/api/import-files",
        files=[("trace", ("trace.mf4", b"\x00", "application/octet-stream"))],
    )

    assert r.status_code == 400


def test_a_corrupt_blf_upload_fails_without_replacing_the_loaded_trace(
    client: TestClient, tmp_path: Path
) -> None:
    ok = client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"), "dbc_paths": [str(DBC)]},
    )
    assert ok.status_code == 200

    corrupt = write_corrupt_blf(tmp_path / "corrupt.blf")
    r = client.post(
        "/api/import-files",
        files=[("trace", ("corrupt.blf", corrupt.read_bytes(), "application/octet-stream"))],
    )

    assert r.status_code == 500
    # The failure never echoes a local path, and the previous acquisition is
    # still the one being served.
    assert str(tmp_path) not in r.text
    assert client.get("/api/status").json()["summary"]["frames"] == 6
    assert client.get("/api/import-job").json()["phase"] == "failed"


# -- downstream contracts ---------------------------------------------------
def test_blf_frames_reach_the_report(client: TestClient, blf: Path) -> None:
    _import_blf(client, blf)

    report = client.get("/api/report").json()
    assert report["frames"] == 4
    assert report["events"] == 3
    # BLF diagnostics land in the same trace-level anomaly bucket as ASC events.
    assert report["anomalies"]["asc_events"] == {
        "BlfRemoteRequest": 1,
        "ErrorFrame": 1,
        "BlfUnsupported": 1,
    }


def test_blf_frames_reach_the_csv_export(client: TestClient, blf: Path) -> None:
    _import_blf(client, blf)

    r = client.post(
        "/api/export",
        json={
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
            "scope": "full",
            "format": "csv",
        },
    )

    assert r.status_code == 200
    lines = r.text.strip().splitlines()
    assert lines[0] == "timestamp_s,message,signal,value,unit"
    assert len(lines) > 1


def test_blf_frames_reach_the_parquet_export(client: TestClient, blf: Path) -> None:
    _import_blf(client, blf)

    r = client.post(
        "/api/export",
        json={
            "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
            "scope": "full",
            "format": "parquet",
        },
    )

    assert r.status_code == 200
    assert pq.read_table(io.BytesIO(r.content)).num_rows > 0


def test_blf_frames_reach_trace_navigation(client: TestClient, blf: Path) -> None:
    _import_blf(client, blf)

    located = client.get("/api/trace-locate", params={"at": 0.002}).json()
    assert located["total"] == 7
