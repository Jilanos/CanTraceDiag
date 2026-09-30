/* Signed trapezoidal time integral of one decoded signal between two cursors.
 *
 * Mirrors src/cantracediag/integral.py; both engines are held to the shared
 * fixtures in tests/fixtures/integral_cases.json. The plot draws
 * sample-and-hold steps, but this analysis deliberately uses piecewise linear
 * (trapezoidal) interpolation over full-resolution stored samples:
 * - the interval is [min(a, b), max(a, b)], so swapped cursors keep the result;
 * - callers pass the samples inside the interval plus at most the bracketing
 *   sample timestamp on each side; the result is never extrapolated;
 * - duplicate timestamps collapse to the last sample in stable ingestion order;
 * - text-only signals, missing coverage and non-finite or non-numeric samples
 *   in the used set yield an explicit unavailable reason, never a bridged value.
 */

export const INTEGRAL_METHOD = "trapezoidal";
export const INTEGRAL_INTERPOLATION = "linear";

export type IntegralReason = "no_samples" | "text_signal" | "no_coverage" | "invalid_samples";

export type IntegralResult = {
  start_s: number;
  end_s: number;
  method: typeof INTEGRAL_METHOD;
  interpolation: typeof INTEGRAL_INTERPOLATION;
  unit: string;
  signal_unit: string | null;
  available: boolean;
  integral: number | null;
  reason: IntegralReason | null;
  sample_count: number;
};

export type IntegralPoint = [timestamp_s: number, value: number | string | null];

export function integralUnit(unit: string | null | undefined): string {
  const trimmed = (unit ?? "").trim();
  return trimmed ? `${trimmed}·s` : "s";
}

export function collapseDuplicates(rows: IntegralPoint[]): IntegralPoint[] {
  const out: IntegralPoint[] = [];
  for (const [ts, value] of rows) {
    if (out.length && out[out.length - 1][0] === ts) out[out.length - 1] = [ts, value];
    else out.push([ts, value]);
  }
  return out;
}

function finiteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** Integrate time-ordered, ingestion-stable `rows` over [a, b]. */
export function integrate(rows: IntegralPoint[], a: number, b: number, unit: string | null = null): IntegralResult {
  const lo = Math.min(a, b);
  const hi = Math.max(a, b);
  const base = {
    start_s: lo,
    end_s: hi,
    method: INTEGRAL_METHOD,
    interpolation: INTEGRAL_INTERPOLATION,
    unit: integralUnit(unit),
    signal_unit: unit,
  } as const;
  const unavailable = (reason: IntegralReason, used = 0): IntegralResult => ({
    ...base, available: false, integral: null, reason, sample_count: used,
  });

  const points = collapseDuplicates(rows.filter(([ts]) => Number.isFinite(ts)));
  if (!points.length) return unavailable("no_samples");
  if (points.every(([, value]) => typeof value === "string")) return unavailable("text_signal");

  let first: number | null = null;
  let last: number | null = null;
  let before: number | null = null;
  let after: number | null = null;
  for (let i = 0; i < points.length; i += 1) {
    const ts = points[i][0];
    if (ts >= lo && ts <= hi) {
      if (first === null) first = i;
      last = i;
    } else if (ts < lo) {
      before = i;
    } else if (after === null) {
      after = i;
    }
  }
  const inside = first === null || last === null ? 0 : last - first + 1;
  const start = first !== null && points[first][0] === lo ? first : before;
  const end = last !== null && points[last][0] === hi ? last : after;
  if (start === null || end === null) return unavailable("no_coverage", inside);
  const used = points.slice(start, end + 1);
  if (!used.every(([, value]) => finiteNumber(value))) return unavailable("invalid_samples", inside);
  if (hi === lo) return { ...base, available: true, integral: 0, reason: null, sample_count: inside };

  let total = 0;
  for (let i = 0; i + 1 < used.length; i += 1) {
    const [t0, v0] = used[i] as [number, number];
    const [t1, v1] = used[i + 1] as [number, number];
    const s = Math.max(t0, lo);
    const e = Math.min(t1, hi);
    if (e <= s) continue;
    const slope = (v1 - v0) / (t1 - t0);
    const vs = v0 + slope * (s - t0);
    const ve = v0 + slope * (e - t0);
    total += (e - s) * (vs + ve) / 2;
  }
  return { ...base, available: true, integral: total, reason: null, sample_count: inside };
}
