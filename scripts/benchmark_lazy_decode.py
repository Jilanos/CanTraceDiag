"""Synthetic benchmark for lazy CAN signal decoding.

Run with:
    python scripts/benchmark_lazy_decode.py --frames 50000 --signals 8

The script generates a temporary ASC/DBC pair, compares lazy import with the
legacy exhaustive import mode, then decodes the first 1..N signals on demand.
It prints JSON so runs can be archived or compared in CI logs.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from cantracediag.dbc import DbcCatalog
from cantracediag.decode import Decoder
from cantracediag.pipeline import import_trace


def main() -> None:
    args = _args()
    with tempfile.TemporaryDirectory(prefix="ctd_bench_") as tmp:
        root = Path(tmp)
        asc = root / "synthetic.asc"
        dbc = root / "synthetic.dbc"
        _write_dbc(dbc, args.messages, args.signals)
        _write_asc(asc, args.frames, args.messages, args.signals)

        lazy_start = time.perf_counter()
        lazy_store, _ = import_trace(asc, [dbc])
        lazy_import_s = time.perf_counter() - lazy_start

        eager_start = time.perf_counter()
        eager_store, _ = import_trace(asc, [dbc], decode_samples=True)
        eager_import_s = time.perf_counter() - eager_start
        eager_samples = eager_store.sample_count()
        eager_store.close()

        catalog = DbcCatalog()
        catalog.load(dbc)
        decoder = Decoder(catalog.message_index())
        selected = catalog.signals()[: args.signals]
        on_demand = []
        for count in range(1, min(8, len(selected)) + 1):
            start = time.perf_counter()
            frames_scanned = 0
            samples_created = 0
            for info in selected[:count]:
                if lazy_store.has_series_cache(info.message_name, info.signal_name, None, None):
                    continue
                frames = lazy_store.frames_for_signal(info.arbitration_id)
                samples = [
                    sample
                    for frame in frames
                    if (sample := decoder.decode_signal(
                        frame, info.message_name, info.signal_name
                    )) is not None
                ]
                lazy_store.replace_signal_samples(info.message_name, info.signal_name, samples)
                lazy_store.mark_series_cached(
                    info.message_name,
                    info.signal_name,
                    None,
                    None,
                    len(frames),
                    len(samples),
                )
                frames_scanned += len(frames)
                samples_created += len(samples)
            on_demand.append({
                "signals": count,
                "decode_s": time.perf_counter() - start,
                "frames_scanned": frames_scanned,
                "samples_created": samples_created,
                "cache": lazy_store.cache_stats(),
            })

        result = {
            "frames": args.frames,
            "messages": args.messages,
            "signals_per_message": args.signals,
            "lazy_import_s": lazy_import_s,
            "eager_import_s": eager_import_s,
            "import_speedup": eager_import_s / lazy_import_s if lazy_import_s else None,
            "lazy_import_samples": 0,
            "eager_import_samples": eager_samples,
            "on_demand": on_demand,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        lazy_store.close()


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=50_000)
    parser.add_argument("--messages", type=int, default=8)
    parser.add_argument("--signals", type=int, default=8)
    return parser.parse_args()


def _write_dbc(path: Path, messages: int, signals: int) -> None:
    lines = ['VERSION ""', "", "NS_ :", "", "BS_:", "", "BU_: ECU", ""]
    for msg in range(messages):
        frame_id = 0x100 + msg
        lines.append(f"BO_ {frame_id} Msg{msg}: 8 ECU")
        for sig in range(signals):
            start = sig * 8
            lines.append(
                f' SG_ Sig{sig} : {start}|8@1+ (1,0) [0|255] "u" Vector__XXX'
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_asc(path: Path, frames: int, messages: int, signals: int) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("date Tue Jul 15 10:00:00 2026\n")
        handle.write("base hex  timestamps absolute\n")
        handle.write("Begin Triggerblock Tue Jul 15 10:00:00 2026\n")
        for i in range(frames):
            frame_id = 0x100 + (i % messages)
            payload = " ".join(f"{(i + j) % 256:02X}" for j in range(8))
            handle.write(f"{i / 1000:.6f} 1 {frame_id:X} Rx d 8 {payload}\n")
        handle.write("End Triggerblock\n")


if __name__ == "__main__":
    main()
