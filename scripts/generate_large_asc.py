"""Generate a representative classic-CAN ASC of an exact byte size plus its DBC.

Used for the req_034 1 GiB qualification (and its scaled-down CI runs). The
fixture is synthetic and deterministic (seeded), so its counts and SHA-256 can be
published without exposing any operational acquisition. It covers:

* channels 1 and a sparse channel 9;
* standard and extended (``x``-suffixed) identifiers, Rx and Tx;
* DLC 0..8 and equal timestamps (bursts that share one timestamp);
* periodic malformed records, error frames and status events;
* a DBC whose messages decode most frames into several physical signals.

The file is padded with a trailing ``//`` comment so its size is exactly
``--size`` bytes. A JSON manifest with the expected counts is written next to it
(or to ``--manifest``) so an import can be checked for silent frame loss.

    python scripts/generate_large_asc.py out.asc --size 1073741824
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

HEADER = (
    "date Mon Oct 19 10:00:00 2026\n"
    "base hex  timestamps absolute\n"
    "internal events logged\n"
    "// version 8.5.0\n"
    "Begin Triggerblock Mon Oct 19 10:00:00 2026\n"
)
FOOTER = "End Triggerblock\n"

# (id, extended, dlc, channel, period weight, signals as (name, start, length, scale, offset, unit))
MESSAGES = [
    (0x100, False, 8, "1", 8, [("EngineSpeed", 0, 16, 0.25, 0, "rpm"),
                               ("EngineTemp", 16, 8, 1, -40, "degC"),
                               ("ThrottlePos", 24, 8, 0.4, 0, "%"),
                               ("Torque", 32, 16, 0.5, -1000, "Nm")]),
    (0x200, False, 2, "1", 6, [("VehicleSpeed", 0, 16, 0.01, 0, "km/h")]),
    (0x18FEF100, True, 8, "1", 5, [("WheelSpeed", 0, 16, 0.00390625, 0, "km/h"),
                                   ("BrakeSwitch", 16, 2, 1, 0, ""),
                                   ("CruiseState", 18, 3, 1, 0, "")]),
    (0x310, False, 6, "1", 4, [("PackVoltage", 0, 16, 0.1, 0, "V"),
                               ("PackCurrent", 16, 16, 0.1, -3200, "A"),
                               ("PackSoC", 32, 8, 0.5, 0, "%")]),
    (0x7E8, False, 8, "9", 1, [("DiagByte0", 0, 8, 1, 0, ""),
                               ("DiagWord", 8, 16, 1, 0, "")]),
    (0x1CFF0009, True, 5, "9", 1, [("AuxTemp", 0, 8, 1, -40, "degC"),
                                   ("AuxPressure", 8, 16, 0.1, 0, "kPa")]),
    (0x5A0, False, 0, "1", 1, []),
    (0x3FF, False, 3, "1", 1, []),  # no DBC entry: stays an unknown id
]


def write_dbc(path: Path) -> None:
    lines = ['VERSION ""', "", "NS_ :", "", "BS_:", "", "BU_: ECU", ""]
    for ident, ext, dlc, _ch, _w, signals in MESSAGES:
        if not signals:
            continue
        raw_id = ident | 0x80000000 if ext else ident
        lines.append(f"BO_ {raw_id} Msg_{ident:X}: {dlc} ECU")
        for name, start, length, scale, offset, unit in signals:
            hi = (2**length - 1) * scale + offset
            lines.append(
                f' SG_ {name} : {start}|{length}@1+ ({scale},{offset}) '
                f'[{offset}|{hi}] "{unit}" Vector__XXX'
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def generate(path: Path, size: int, seed: int = 20261019) -> dict:
    rng = random.Random(seed)
    weights = [m[4] for m in MESSAGES]
    counts = {"frames": 0, "error_frames": 0, "status": 0, "malformed": 0,
              "extended_frames": 0, "channel_9_frames": 0, "equal_timestamp_lines": 0}
    ids: set[str] = set()
    footer_len = len(FOOTER)
    budget = size - footer_len
    t = 0.0
    line_no = 0
    digest = hashlib.sha256()
    with open(path, "wb") as out:
        written = 0

        def emit(text: str) -> None:
            nonlocal written
            data = text.encode("ascii")
            out.write(data)
            digest.update(data)
            written += len(data)

        emit(HEADER)
        # Leave room for at least the 4-byte padding comment "//\n".
        while True:
            line_no += 1
            burst = line_no % 97 == 0
            if not burst:
                t += rng.uniform(0.00005, 0.0006)
            else:
                counts["equal_timestamp_lines"] += 1
            ts = f"{t:11.6f}"
            if line_no % 250_007 == 0:
                line = f"{ts} 1  ErrorFrame\n"
                kind = "error_frames"
            elif line_no % 500_009 == 0:
                line = f"{ts} CAN 1 Status:chip status error active\n"
                kind = "status"
            elif line_no % 300_007 == 0:
                # DLC says 8, only 3 bytes present: an AscAnomaly, never a frame.
                line = f"{ts} 1  100             Rx   d 8 01 02 03\n"
                kind = "malformed"
            else:
                ident, ext, dlc, ch, _w, _s = rng.choices(MESSAGES, weights)[0]
                ident_s = f"{ident:X}x" if ext else f"{ident:X}"
                direction = "Tx" if line_no % 11 == 0 else "Rx"
                payload = " ".join(f"{rng.randrange(256):02X}" for _ in range(dlc))
                line = f"{ts} {ch}  {ident_s:<15} {direction}   d {dlc} {payload}".rstrip() + "\n"
                kind = "frames"
            if written + len(line) + 3 > budget:
                break
            emit(line)
            counts[kind] += 1
            if kind == "frames":
                ids.add(ident_s)
                counts["extended_frames"] += ext
                counts["channel_9_frames"] += ch == "9"
        pad = budget - written - 3
        emit("//" + " " * pad + "\n")
        emit(FOOTER)
    assert written == size, (written, size)
    counts["unique_ids"] = len(ids)
    return {
        "bytes": size,
        "sha256": digest.hexdigest(),
        "seed": seed,
        "end_s": round(t, 6),
        **counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=1_073_741_824)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--dbc", type=Path, help="DBC path (default: <output>.dbc)")
    parser.add_argument("--manifest", type=Path, help="manifest path (default: <output>.json)")
    args = parser.parse_args()
    if args.size < len(HEADER) + len(FOOTER) + 3:
        parser.error("--size too small for a valid ASC")
    dbc = args.dbc or args.output.with_suffix(".dbc")
    write_dbc(dbc)
    manifest = generate(args.output, args.size, args.seed)
    manifest["dbc_sha256"] = hashlib.sha256(dbc.read_bytes()).hexdigest()
    target = args.manifest or args.output.with_suffix(".json")
    target.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
