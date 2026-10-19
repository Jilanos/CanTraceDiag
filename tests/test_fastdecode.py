"""The vectorized decoder must equal the exact per-frame path (req_034 AC2, AC4)."""

from __future__ import annotations

import random
from pathlib import Path

import cantools
import pytest

from cantracediag import fastdecode
from cantracediag.decode import Decoder
from cantracediag.models import DECODE_NOT_DECODED, RawCanFrame

FIX = Path(__file__).parent / "fixtures"

DBC = """VERSION ""
BS_:
BU_: ECU
BO_ 256 Intel8: 8 ECU
 SG_ U16 : 0|16@1+ (0.25,0) [0|0] "rpm" Vector__XXX
 SG_ S12 : 16|12@1- (1,-40) [0|0] "degC" Vector__XXX
 SG_ U3 : 29|3@1+ (1,0) [0|0] "" Vector__XXX
 SG_ S32 : 32|32@1- (0.001,12.5) [0|0] "A" Vector__XXX
BO_ 512 Moto6: 6 ECU
 SG_ M16 : 7|16@0+ (0.01,0) [0|0] "km/h" Vector__XXX
 SG_ MS13 : 21|13@0- (2,1) [0|0] "" Vector__XXX
 SG_ M1 : 41|1@0+ (1,0) [0|0] "" Vector__XXX
 SG_ M12 : 39|12@0+ (0.1,-100) [0|0] "" Vector__XXX
BO_ 768 Short2: 2 ECU
 SG_ B : 0|16@1- (3,7) [0|0] "" Vector__XXX
BO_ 1024 Wide: 8 ECU
 SG_ W52 : 0|52@1+ (1,0) [0|0] "" Vector__XXX
 
BO_ 1025 Wider: 8 ECU
 SG_ W53 : 0|53@1+ (1,0) [0|0] "" Vector__XXX
"""


@pytest.fixture(scope="module")
def db():
    return cantools.database.load_string(DBC, "dbc")


def _frames(arb_id: int, n: int, rng: random.Random) -> list[RawCanFrame]:
    out = []
    for i in range(n):
        dlc = rng.choice([0, 1, 2, 5, 6, 7, 8, 8, 8, 8])
        out.append(RawCanFrame(
            i * 0.001, "1", arb_id, False, dlc,
            bytes(rng.randrange(256) for _ in range(dlc)), "Rx", rng.random() < 0.05,
            None, DECODE_NOT_DECODED, None,
        ))
    return out


@pytest.mark.parametrize(("message", "signal"), [
    ("Intel8", "U16"), ("Intel8", "S12"), ("Intel8", "U3"), ("Intel8", "S32"),
    ("Moto6", "M16"), ("Moto6", "MS13"), ("Moto6", "M1"), ("Moto6", "M12"),
    ("Short2", "B"), ("Wide", "W52"),
])
def test_vectorized_decode_equals_cantools(db, message: str, signal: str) -> None:
    msg = db.get_message_by_name(message)
    plan = fastdecode.plan(msg, signal)
    assert plan is not None
    decoder = Decoder({msg.frame_id: [("t.dbc", msg)]})
    frames = _frames(msg.frame_id, 4000, random.Random(hash((message, signal)) & 0xFFFF))
    keep, values = fastdecode.decode(
        plan, [f.data.hex(" ").upper() or None for f in frames], [f.is_remote for f in frames]
    )
    for i, frame in enumerate(frames):
        expected = decoder.decode_signal(frame, message, signal)
        assert bool(keep[i]) == (expected is not None), (i, frame)
        if expected is not None:
            assert float(values[i]) == float(expected.value), (i, frame.data.hex())


def test_ineligible_signals_keep_the_exact_path(db) -> None:
    assert fastdecode.plan(db.get_message_by_name("Wider"), "W53") is None
    assert fastdecode.plan(db.get_message_by_name("Wide"), "missing") is None
    mux = cantools.database.load_file(FIX / "sample.dbc")
    for message in mux.messages:
        if message.is_multiplexed():
            assert fastdecode.plan(message, message.signals[0].name) is None


def test_api_series_identical_on_both_paths(tmp_path: Path, monkeypatch) -> None:
    import importlib.util

    from conftest import make_client

    spec = importlib.util.spec_from_file_location(
        "gen", Path(__file__).parents[1] / "scripts" / "generate_large_asc.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    asc, dbc = tmp_path / "g.asc", tmp_path / "g.dbc"
    gen.write_dbc(dbc)
    gen.generate(asc, 600_000)

    def series(client, message, signal):
        r = client.get("/api/series", params={"message": message, "signal": signal,
                                               "max_points": 50_000})
        assert r.status_code == 200
        return r.json()

    pairs = [("Msg_100", "Torque"), ("Msg_18FEF100", "BrakeSwitch"), ("Msg_310", "PackCurrent"),
             ("Msg_1CFF0009", "AuxTemp")]
    fast_client = make_client()
    assert fast_client.post("/api/import", json={"trace_path": str(asc),
                                                 "dbc_paths": [str(dbc)]}).status_code == 200
    fast = [series(fast_client, m, s) for m, s in pairs]
    monkeypatch.setattr(fastdecode, "plan", lambda message, signal: None)
    slow_client = make_client()
    assert slow_client.post("/api/import", json={"trace_path": str(asc),
                                                 "dbc_paths": [str(dbc)]}).status_code == 200
    slow = [series(slow_client, m, s) for m, s in pairs]
    for f, s in zip(fast, slow, strict=True):
        assert len(f["t"]) > 0
        assert f == s
