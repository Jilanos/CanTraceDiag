"""Tests for the diagnostic-improvement wave: server-side downsampling,
combinable trace filters, graph/trace locate, and DBC conflict resolution."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from cantracediag.api import create_app
from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.models import DECODE_OK, DecodedSignalSample, NonDataEvent, RawCanFrame
from cantracediag.store import TraceStore

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# -- server-side downsampling (AC9) ---------------------------------------


def _dense_store(n: int = 10_000, spike_at: int | None = None) -> TraceStore:
    store = TraceStore()
    samples = []
    for i in range(n):
        value = float(i)
        if spike_at is not None and i == spike_at:
            value = 1e9
        samples.append(
            DecodedSignalSample(i / 1000.0, "1", 0x100, "M", "Sig", value, "u")
        )
    store.ingest_samples(samples)
    return store


def test_series_downsamples_above_budget() -> None:
    store = _dense_store()
    series = store.signal_series("M", "Sig", max_points=500)
    assert series["downsampled"] is True
    assert series["raw_count"] == 10_000
    assert len(series["t"]) <= 500
    # Points stay time-ordered and real (present in original data).
    assert series["t"] == sorted(series["t"])
    store.close()


def test_series_preserves_extrema() -> None:
    store = _dense_store(spike_at=5000)
    series = store.signal_series("M", "Sig", max_points=400)
    # Min/max decimation must keep the spike so anomalies survive on screen.
    assert 1e9 in series["v"]
    store.close()


def test_series_not_downsampled_when_small() -> None:
    store = _dense_store(n=100)
    series = store.signal_series("M", "Sig", max_points=4000)
    assert series["downsampled"] is False
    assert len(series["t"]) == 100
    store.close()


# -- combinable trace filters (AC4) ---------------------------------------


def _filter_store() -> TraceStore:
    store = TraceStore()
    store.ingest_frames(
        [
            RawCanFrame(0.0, "1", 0x100, False, 1, b"\x01", direction="Rx",
                        message_name="EngineData", decode_status=DECODE_OK),
            RawCanFrame(0.1, "1", 0x200, False, 1, b"\x02", direction="Tx",
                        message_name="VehicleState", decode_status="unknown_id"),
        ]
    )
    store.ingest_events([NonDataEvent(0.05, "1", "ErrorFrame", "bus error")])
    return store


def test_filter_by_id_excludes_events() -> None:
    store = _filter_store()
    page = store.trace_rows(limit=100, id_hex="100")
    assert page["total"] == 1
    assert {r["kind"] for r in page["rows"]} == {"frame"}
    store.close()


def test_filter_by_event_type_excludes_frames() -> None:
    store = _filter_store()
    page = store.trace_rows(limit=100, event_type="ErrorFrame")
    assert page["total"] == 1
    assert {r["kind"] for r in page["rows"]} == {"event"}
    store.close()


def test_filter_by_direction_and_status_combine() -> None:
    store = _filter_store()
    page = store.trace_rows(limit=100, direction="Rx", decode_status=DECODE_OK)
    assert page["total"] == 1
    assert page["rows"][0]["id_hex"] == "100"
    store.close()


def test_filter_by_time_window() -> None:
    store = _filter_store()
    page = store.trace_rows(limit=100, start_s=0.04, end_s=0.06)
    assert page["total"] == 1
    assert page["rows"][0]["kind"] == "event"
    store.close()


# -- graph/trace locate (AC3) ---------------------------------------------


def test_locate_row_returns_nearest_index() -> None:
    store = TraceStore()
    store.ingest_frames(
        [RawCanFrame(i / 10.0, "1", 0x100, False, 1, b"\x01", direction="Rx")
         for i in range(10)]
    )
    loc = store.locate_row(0.52, include_events=False)
    assert loc["index"] == 5  # nearest to 0.52 is 0.5 at index 5
    assert loc["timestamp_s"] == 0.5
    assert loc["total"] == 10
    store.close()


def test_locate_row_honours_filters() -> None:
    store = _filter_store()
    loc = store.locate_row(0.09, include_events=False, id_hex="200")
    assert loc["total"] == 1
    assert loc["index"] == 0
    store.close()


# -- DBC conflict resolution (AC10) ---------------------------------------


def test_decoder_honours_resolution() -> None:
    catalog = DbcCatalog()
    catalog.load(FIX / "sample.dbc")
    catalog.load(FIX / "sample_conflict.dbc")
    # Force id 0x100 to decode as BrakeData from the conflicting DBC.
    decoder = Decoder(catalog.message_index(), resolution={0x100: "sample_conflict.dbc"})
    frame = RawCanFrame(0.0, "1", 0x100, False, 8, bytes(8), direction="Rx")
    updated, samples = decoder.decode_frame(frame)
    assert updated.message_name == "BrakeData"
    assert updated.dbc_source == "sample_conflict.dbc"
    assert any(s.signal_name == "BrakePressure" for s in samples)


def test_import_flow_requires_then_resolves_conflict(client: TestClient) -> None:
    asc = (FIX / "sample.asc").read_bytes()
    dbc_a = (FIX / "sample.dbc").read_bytes()
    dbc_b = (FIX / "sample_conflict.dbc").read_bytes()
    first = client.post(
        "/api/import-files",
        files=[
            ("trace", ("sample.asc", asc, "application/octet-stream")),
            ("dbcs", ("sample.dbc", dbc_a, "application/octet-stream")),
            ("dbcs", ("sample_conflict.dbc", dbc_b, "application/octet-stream")),
        ],
    )
    assert first.status_code == 200
    body = first.json()
    assert body["needs_resolution"] is True
    ids = {c["id_hex"] for c in body["conflicts"]}
    assert "0x100" in ids
    # The load is not finalized until resolution is posted.
    assert client.get("/api/status").json()["loaded"] is False

    resolved = client.post(
        "/api/resolve", json={"resolution": {"0x100": "sample_conflict.dbc"}}
    )
    assert resolved.status_code == 200
    rbody = resolved.json()
    assert rbody["needs_resolution"] is False
    assert rbody["resolution"] == {"0x100": "sample_conflict.dbc"}
    # Frame 0x100 now decodes with the chosen DBC.
    trace = client.get("/api/trace", params={"limit": 100, "id": "100"}).json()
    assert any(r["dbc_source"] == "sample_conflict.dbc" for r in trace["rows"])


def test_resolve_without_pending_returns_409(client: TestClient) -> None:
    assert client.post("/api/resolve", json={"resolution": {}}).status_code == 409


def test_import_without_conflict_finalizes_directly(client: TestClient) -> None:
    r = client.post(
        "/api/import",
        json={"trace_path": str(FIX / "sample.asc"),
              "dbc_paths": [str(FIX / "sample.dbc")]},
    )
    assert r.status_code == 200
    assert r.json()["needs_resolution"] is False
    assert client.get("/api/status").json()["loaded"] is True
