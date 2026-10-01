"""Raw CAN ASC export: serializer, store iterator, round trips and API.

The export reads stored raw frames, never decoded samples, so none of these
tests load a DBC or select a signal unless they check that doing so changes
nothing.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import can
import pytest
from blf_fixture import write_sample_blf
from conftest import make_client
from mf4_fixture import Group, Record, write_mf4
from starlette.testclient import TestClient

from cantracediag import export
from cantracediag.api import create_app
from cantracediag.models import RawCanFrame
from cantracediag.pipeline import import_trace
from cantracediag.store import TraceStore
from cantracediag.workspace import Workspace

FIX = Path(__file__).parent / "fixtures"
DBC = FIX / "sample.dbc"

GROUPS = [
    Group("CAN9_Rx", 32, constants={"BusChannel": 9, "IDE": 0, "Dir": 0}),
    Group("CAN1_Rx", 64, constants={"BusChannel": 1, "IDE": 0, "Dir": 0}),
    Group("CAN1_Tx_IDE", 67, constants={"BusChannel": 1, "IDE": 1, "Dir": 1}),
    Group("CAN1_Errors", 90, kind="error", constants={"BusChannel": 1}),
    Group("LIN1_Frame", 100, kind="lin", constants={"BusChannel": 1}),
]
RECORDS = [
    Record("CAN1_Rx", 0.5, 0x100, 8, bytes([0x40, 0x1F, 0x5A, 0, 0, 0, 0, 0])),
    Record("CAN9_Rx", 1.0, 0x7FF, 0, b""),
    Record("CAN1_Rx", 1.0, 0x123, 8, bytes(range(8))),
    Record("CAN1_Tx_IDE", 1.5, 0x18FF00AA, 2, b"\x01\x02"),
    Record("CAN1_Errors", 2.0),
    Record("LIN1_Frame", 2.5, 0x10, 2, b"zz"),
    Record("CAN1_Tx_IDE", 3.000001, 0x1FFFFFFF, 1, b"\xff"),
]

_COLUMNS = (
    "timestamp_s, channel, arbitration_id, is_extended_id, dlc, data_hex, "
    "direction, is_remote"
)


def _frames(store: TraceStore) -> list[tuple]:
    return store.con.execute(
        f"SELECT {_COLUMNS} FROM frames ORDER BY timestamp_s, seq"
    ).fetchall()


def _export(store: TraceStore, path: Path, start=None, end=None, policy="block") -> Path:
    summary = store.raw_export_summary(start, end)
    header = export.asc_header_lines(
        summary, source="t", scope="full" if start is None else "between_ab",
        start_s=start, end_s=end, policy=policy,
    )
    with open(path, "wb") as handle:
        for chunk in export.raw_asc(store.iter_raw_frames(start, end, batch_size=2),
                                    header, policy):
            handle.write(chunk)
    return path


def _assert_round_trip(original: list[tuple], reimported: list[tuple]) -> None:
    assert len(reimported) == len(original)
    for a, b in zip(original, reimported, strict=True):
        assert a[1:] == b[1:]
        assert abs(a[0] - b[0]) <= 1e-6


@pytest.fixture
def mf4(tmp_path: Path) -> Path:
    return write_mf4(tmp_path / "trace.MF4", GROUPS, RECORDS, unfinished=True)


# -- serializer -------------------------------------------------------------
def test_line_grammar() -> None:
    line = export.asc_frame_line
    assert line(1.5, "1", 0x123, False, 2, "01 AB", "Rx", False) == (
        "1.500000 1  123             Rx   d 2 01 AB"
    )
    assert line(0.0, "9", 0x18FF00AA, True, 0, None, "Tx", False) == (
        "0.000000 9  18FF00AAx       Tx   d 0"
    )
    assert line(2.0, "2", 0x55, False, 4, None, "Rx", True) == (
        "2.000000 2  55              Rx   r 4"
    )


def test_unknown_provenance_is_refused_unless_explicitly_assumed() -> None:
    with pytest.raises(export.ProvenanceError):
        export.asc_frame_line(1.0, None, 1, False, 0, None, "Rx", False)
    with pytest.raises(export.ProvenanceError):
        export.asc_frame_line(1.0, "1", 1, False, 0, None, None, False)
    assumed = export.asc_frame_line(1.0, None, 1, False, 0, None, None, False, "assume")
    assert assumed == "1.000000 1  1               Rx   d 0"


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_non_finite_timestamps_are_rejected(bad: float) -> None:
    with pytest.raises(ValueError):
        export.asc_frame_line(bad, "1", 1, False, 0, None, "Rx", False)


def test_header_discloses_scope_exclusions_assumptions_and_warnings() -> None:
    summary = {"frames": 3, "excluded_events": {"ErrorFrame": 2, "Mf4Skipped": 1},
               "nonfinite_frames": 1, "unknown_channel": 1, "unknown_direction": 2}
    lines = export.asc_header_lines(
        summary, source="00000002.MF4", scope="between_ab", start_s=1.0, end_s=2.0,
        policy="assume", warnings=["Recovered an unfinalized MDF 4.11 measurement"],
    )
    text = "\n".join(lines)
    assert lines[1] == "base hex  timestamps absolute"
    assert "between_ab 1.000000 .. 2.000000 s (inclusive)" in text
    assert "ErrorFrame=2" in text and "Mf4Skipped=1" in text
    assert "non-finite timestamp frames=1" in text
    assert "ASSUMED provenance" in text
    assert "warning: Recovered an unfinalized" in text
    assert lines[-1] == "Begin Triggerblock"


# -- store iterator ---------------------------------------------------------
def test_iterator_orders_by_time_then_seq_with_inclusive_bounds() -> None:
    store = TraceStore()
    frames = [RawCanFrame(t, "1", i, False, 0, b"", "Rx") for i, t in
              enumerate([3.0, 1.0, 2.0, 1.0, 2.0])]
    store.ingest_frames(frames, seqs=[0, 1, 2, 3, 4])

    def ids(start=None, end=None):
        return [i for batch in store.iter_raw_frames(start, end, batch_size=2)
                for i in batch["arbitration_id"]]

    assert ids() == [1, 3, 2, 4, 0]
    assert ids(1.0, 2.0) == [1, 3, 2, 4]  # both bounds inclusive
    assert ids(2.5, 2.9) == []
    store.close()


def test_iterator_yields_bounded_batches() -> None:
    store = TraceStore()
    store.ingest_frames([RawCanFrame(i * 0.001, "1", 1, False, 0, b"", "Rx")
                         for i in range(1000)])
    sizes = [len(b["timestamp_s"]) for b in store.iter_raw_frames(batch_size=128)]
    assert max(sizes) <= 128
    assert sum(sizes) == 1000
    store.close()


# -- round trips --------------------------------------------------------------
def test_mf4_round_trips_through_asc_without_a_dbc(mf4: Path, tmp_path: Path) -> None:
    store, _ = import_trace(mf4)
    asc = _export(store, tmp_path / "out.asc")
    again, result = import_trace(asc)

    _assert_round_trip(_frames(store), _frames(again))
    # Nothing in the ASC is anything but a frame: the excluded error frame and
    # skipped LIN group do not come back as events.
    assert result.summary["events"] == 0
    channels = {row[1] for row in _frames(again)}
    assert channels == {"1", "9"}  # sparse numbers kept, never renumbered
    store.close()
    again.close()


@pytest.mark.parametrize("source", ["sample.asc", "sample.trc", "sample_dec.asc", "blf"])
def test_existing_formats_round_trip_through_asc(source: str, tmp_path: Path) -> None:
    path = write_sample_blf(tmp_path / "s.blf") if source == "blf" else FIX / source
    store, _ = import_trace(path, [DBC])
    again, _ = import_trace(_export(store, tmp_path / "out.asc"))

    _assert_round_trip(_frames(store), _frames(again))
    store.close()
    again.close()


def test_timestamp_round_trip_error_stays_within_one_microsecond(tmp_path: Path) -> None:
    rng = random.Random(7)
    store = TraceStore()
    times = sorted(rng.uniform(0, 5000) for _ in range(2000)) + [0.0, 1e-7, 4999.9999995]
    store.ingest_frames([RawCanFrame(t, "1", 1, False, 0, b"", "Rx") for t in times])
    again, _ = import_trace(_export(store, tmp_path / "t.asc"))

    original = sorted(times)
    back = [row[0] for row in _frames(again)]
    assert max(abs(a - b) for a, b in zip(original, back, strict=True)) <= 0.5e-6 + 1e-12
    store.close()
    again.close()


def test_python_can_reads_the_export(mf4: Path, tmp_path: Path) -> None:
    store, _ = import_trace(mf4)
    asc = _export(store, tmp_path / "out.asc")
    messages = list(can.ASCReader(str(asc)))

    assert len(messages) == 5
    assert [m.arbitration_id for m in messages] == [0x100, 0x7FF, 0x123, 0x18FF00AA, 0x1FFFFFFF]
    assert [m.channel for m in messages] == [0, 8, 0, 0, 0]  # python-can is 0-based
    assert [m.is_rx for m in messages] == [True, True, True, False, False]
    assert messages[2].data == bytes(range(8))
    store.close()


# -- API --------------------------------------------------------------------
def _load(client: TestClient, path: Path, dbcs=()) -> None:
    r = client.post("/api/import", json={"trace_path": str(path),
                                         "dbc_paths": [str(d) for d in dbcs]})
    assert r.status_code == 200, r.text


def test_summary_discloses_exclusions_before_download(client: TestClient, mf4: Path) -> None:
    _load(client, mf4)
    body = client.get("/api/export-asc/summary").json()

    assert body["frames"] == 5
    assert body["excluded_events"] == {"ErrorFrame": 1, "Mf4Skipped": 1}
    assert body["blocked"] is None
    assert body["filename"] == "trace.asc"
    assert any("unfinalized" in w for w in body["warnings"])


def test_download_needs_no_dbc_and_no_signals(client: TestClient, mf4: Path,
                                              tmp_path: Path) -> None:
    _load(client, mf4)
    r = client.post("/api/export-asc", json={"scope": "full"})

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    assert 'filename="trace.asc"' in r.headers["content-disposition"]
    assert r.headers["x-ctd-export-frames"] == "5"
    assert r.headers["x-ctd-export-excluded"] == "2"
    assert "ErrorFrame=1, Mf4Skipped=1" in r.text
    out = tmp_path / "dl.asc"
    out.write_bytes(r.content)
    again, _ = import_trace(out)
    assert again.summary()["frames"] == 5
    again.close()


@pytest.mark.parametrize("scope", ["between_ab", "visible"])
def test_ranged_scopes_are_inclusive_and_ignore_signal_state(
    client: TestClient, mf4: Path, scope: str
) -> None:
    _load(client, mf4, [DBC])
    r = client.post("/api/export-asc", json={"scope": scope, "start": 1.5, "end": 1.0})

    assert r.status_code == 200
    lines = [ln for ln in r.text.splitlines() if ln[:1].isdigit()]
    assert [ln.split()[2] for ln in lines] == ["7FF", "123", "18FF00AAx"]
    assert f"// scope: {scope} 1.000000 .. 1.500000 s (inclusive)" in r.text


def test_empty_range_gives_a_valid_header_only_asc(client: TestClient, mf4: Path,
                                                   tmp_path: Path) -> None:
    _load(client, mf4)
    summary = client.get("/api/export-asc/summary",
                         params={"scope": "visible", "start": 10, "end": 20}).json()
    assert summary["frames"] == 0
    r = client.post("/api/export-asc", json={"scope": "visible", "start": 10, "end": 20})

    assert r.status_code == 200
    assert "// frames: 0" in r.text
    assert r.text.rstrip().endswith("End TriggerBlock")
    out = tmp_path / "empty.asc"
    out.write_bytes(r.content)
    again, result = import_trace(out)
    assert result.summary["frames"] == 0 and result.summary["events"] == 0
    again.close()


def test_unknown_provenance_blocks_until_explicitly_assumed(client: TestClient,
                                                            tmp_path: Path) -> None:
    anon = write_mf4(tmp_path / "anon.mf4", [Group("Anon", 1)],
                     [Record("Anon", 0.1, 0x10, 1, b"a")])
    _load(client, anon)

    summary = client.get("/api/export-asc/summary").json()
    assert summary["unknown_channel"] == 1 and summary["unknown_direction"] == 1
    assert "no numeric bus channel" in summary["blocked"]
    assert client.post("/api/export-asc", json={}).status_code == 409

    r = client.post("/api/export-asc", json={"provenance": "assume"})
    assert r.status_code == 200
    assert "ASSUMED provenance: 1 frame(s)" in r.text
    assert "0.100000 1  10              Rx   d 1 61" in r.text


@pytest.mark.parametrize(
    "payload",
    [{"scope": "nope"}, {"scope": "between_ab"}, {"provenance": "invent"}],
)
def test_bad_requests_are_rejected(client: TestClient, mf4: Path, payload: dict) -> None:
    _load(client, mf4)
    assert client.post("/api/export-asc", json=payload).status_code == 400


def test_export_without_a_trace_is_a_conflict(client: TestClient) -> None:
    assert client.post("/api/export-asc", json={}).status_code == 409


def test_signal_export_contract_is_unchanged(client: TestClient, mf4: Path) -> None:
    _load(client, mf4, [DBC])
    # CSV/Parquet still require a selected signal...
    assert client.post("/api/export", json={"signals": [], "scope": "full"}).status_code == 400
    # ...and still emit the long schema for MF4-sourced samples.
    r = client.post("/api/export", json={
        "signals": [{"message": "EngineData", "signal": "EngineSpeed"}],
        "scope": "full", "format": "csv",
    })
    assert r.status_code == 200
    assert r.text.splitlines()[0] == "timestamp_s,message,signal,value,unit"
    assert len(r.text.splitlines()) == 2


def test_export_works_on_a_restored_session(tmp_path: Path, mf4: Path) -> None:
    ws = Workspace(tmp_path / "ws", ephemeral=False)
    app1 = create_app(ws)
    _load(make_client(app1), mf4)
    app1.state.ctd_session.store.close()

    c2 = make_client(create_app(Workspace(ws.root, ephemeral=False)))
    summary = c2.get("/api/export-asc/summary").json()
    assert summary["frames"] == 5
    assert any("unfinalized" in w for w in summary["warnings"])
    r = c2.post("/api/export-asc", json={})
    assert r.status_code == 200
    assert r.headers["x-ctd-export-frames"] == "5"
