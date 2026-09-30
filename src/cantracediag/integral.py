"""Signed trapezoidal time integral of one decoded signal between two cursors.

The plot draws sample-and-hold steps, but this analysis deliberately reports
piecewise *linear* (trapezoidal) interpolation between full-resolution stored
samples, never the decimated plot arrays. The contract is mirrored by the PWA
engine (``spikes/pwa-local-engine/src/integral.ts``) and both are held to the
same fixtures:

* the interval is ``[min(a, b), max(a, b)]`` so swapping cursor labels keeps
  the result; values below zero subtract area;
* the caller supplies the samples inside the interval plus at most the one
  bracketing sample on each side, used only to interpolate the exact boundary
  value -- the result is never extrapolated beyond available data;
* duplicate timestamps collapse to the last sample in stable ingestion order;
* a positive-width interval needs finite numeric coverage at both boundaries;
  a zero-width interval with a defined finite value integrates to 0;
* text-only signals, missing coverage and non-finite or non-numeric samples in
  the used set are reported as an explicit unavailable reason, never bridged.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

METHOD = "trapezoidal"
INTERPOLATION = "linear"

# Stable unavailable reason codes (shared with the PWA engine and the UI).
REASON_NO_SAMPLES = "no_samples"
REASON_TEXT_SIGNAL = "text_signal"
REASON_NO_COVERAGE = "no_coverage"
REASON_INVALID_SAMPLES = "invalid_samples"


def integral_unit(unit: str | None) -> str:
    """DBC unit multiplied by seconds (``A`` -> ``A·s``), or ``s`` if unitless."""
    unit = (unit or "").strip()
    return f"{unit}·s" if unit else "s"


def collapse_duplicates(
    rows: Iterable[tuple[float, object]],
) -> list[tuple[float, object]]:
    """Keep the last sample per timestamp; ``rows`` is in (time, ingestion) order."""
    out: list[tuple[float, object]] = []
    for ts, value in rows:
        if out and out[-1][0] == ts:
            out[-1] = (ts, value)
        else:
            out.append((ts, value))
    return out


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def integrate(
    rows: Sequence[tuple[float, object]],
    a: float,
    b: float,
    unit: str | None = None,
) -> dict:
    """Integrate ``rows`` (time-ordered, ingestion-stable) over ``[a, b]``.

    ``rows`` holds the samples inside the interval plus the bracketing
    neighbours; any other sample is ignored. Returns a JSON-ready result with
    the bounds, method, integral, units and, when unavailable, the reason.
    """
    lo, hi = (a, b) if a <= b else (b, a)
    base = {
        "start_s": lo,
        "end_s": hi,
        "method": METHOD,
        "interpolation": INTERPOLATION,
        "unit": integral_unit(unit),
        "signal_unit": unit,
    }

    def unavailable(reason: str, used: int = 0) -> dict:
        return {**base, "available": False, "integral": None, "reason": reason,
                "sample_count": used}

    points = collapse_duplicates(
        (float(ts), value) for ts, value in rows if math.isfinite(float(ts))
    )
    if not points:
        return unavailable(REASON_NO_SAMPLES)
    if all(isinstance(value, str) for _, value in points):
        return unavailable(REASON_TEXT_SIGNAL)

    inside = [i for i, (ts, _) in enumerate(points) if lo <= ts <= hi]
    first = inside[0] if inside else None
    last = inside[-1] if inside else None
    # Bracketing neighbours: the latest point before lo and earliest after hi.
    before = max((i for i, (ts, _) in enumerate(points) if ts < lo), default=None)
    after = min((i for i, (ts, _) in enumerate(points) if ts > hi), default=None)

    start = first if first is not None and points[first][0] == lo else before
    end = last if last is not None and points[last][0] == hi else after
    if start is None or end is None:
        return unavailable(REASON_NO_COVERAGE, len(inside))
    used = points[start:end + 1]
    if not all(_finite_number(value) for _, value in used):
        return unavailable(REASON_INVALID_SAMPLES, len(inside))
    if hi == lo:
        return {**base, "available": True, "integral": 0.0, "reason": None,
                "sample_count": len(inside)}

    total = 0.0
    for (t0, v0), (t1, v1) in zip(used, used[1:], strict=False):
        s, e = max(t0, lo), min(t1, hi)
        if e <= s:
            continue
        slope = (v1 - v0) / (t1 - t0)
        vs = v0 + slope * (s - t0)
        ve = v0 + slope * (e - t0)
        total += (e - s) * (vs + ve) / 2.0
    return {**base, "available": True, "integral": total, "reason": None,
            "sample_count": len(inside)}
