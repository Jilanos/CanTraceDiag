import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { integralUnit, integrate, type IntegralPoint } from "../src/integral.ts";
import { LocalTraceStore } from "../src/store.ts";
import type { DecodedSignalSample } from "../src/types.ts";

/* Same fixture file as tests/test_integral.py: Python/TypeScript parity. */
type RawValue = number | string | { nonfinite: string };
type Case = {
  name: string;
  samples: Array<[number, RawValue]>;
  a: number;
  b: number;
  unit: string | null;
  expect: { available: boolean; integral?: number; reason?: string; unit?: string };
};
const fixturePath = path.resolve("tests/fixtures/integral_cases.json");
const CASES: Case[] = JSON.parse(fs.readFileSync(fixturePath, "utf8")).cases;

function value(raw: RawValue): number | string {
  if (typeof raw === "object") return raw.nonfinite === "nan" ? NaN : raw.nonfinite === "-inf" ? -Infinity : Infinity;
  return raw;
}

function sample(timestamp_s: number, v: number | string, unit: string | null): DecodedSignalSample {
  return {
    timestamp_s,
    channel: "1",
    arbitration_id: 0x100,
    message_name: "M",
    signal_name: "Sig",
    value: v,
    unit,
  } as DecodedSignalSample;
}

function check(result: ReturnType<typeof integrate>, c: Case): void {
  assert.equal(result.available, c.expect.available, c.name);
  assert.equal(result.method, "trapezoidal");
  assert.equal(result.start_s, Math.min(c.a, c.b));
  assert.equal(result.end_s, Math.max(c.a, c.b));
  if (c.expect.available) {
    assert.ok(Math.abs((result.integral as number) - (c.expect.integral as number)) <= 1e-12, `${c.name}: ${result.integral}`);
    assert.equal(result.reason, null);
  } else {
    assert.equal(result.integral, null);
    assert.equal(result.reason, c.expect.reason, c.name);
  }
  if (c.expect.unit) assert.equal(result.unit, c.expect.unit);
}

describe("signal integral parity fixtures", () => {
  for (const c of CASES) {
    it(`pure engine: ${c.name}`, () => {
      const rows: IntegralPoint[] = c.samples.map(([t, v]) => [t, value(v)]);
      check(integrate(rows, c.a, c.b, c.unit), c);
    });
    it(`store: ${c.name}`, () => {
      const store = new LocalTraceStore();
      store.ingestSamples(c.samples.map(([t, v]) => sample(t, value(v), c.unit || null)));
      check(store.signalIntegral("M", "Sig", c.a, c.b), c);
    });
  }
});

describe("signal integral contract", () => {
  it("formats units as the DBC unit times seconds without derived conversions", () => {
    assert.equal(integralUnit("A"), "A·s");
    assert.equal(integralUnit(""), "s");
    assert.equal(integralUnit(null), "s");
    assert.equal(integralUnit("Ah"), "Ah·s");
  });

  it("integrates full resolution regardless of plot decimation and cursor order", () => {
    const store = new LocalTraceStore();
    const samples: DecodedSignalSample[] = [];
    for (let i = 0; i <= 20_000; i += 1) samples.push(sample(i / 1000, i / 1000, "A"));
    store.ingestSamples(samples);
    assert.equal(store.signalSeries("M", "Sig", { maxPoints: 100 }).downsampled, true);
    const forward = store.signalIntegral("M", "Sig", 2.0005, 12.0005);
    const backward = store.signalIntegral("M", "Sig", 12.0005, 2.0005);
    const expected = (12.0005 ** 2 - 2.0005 ** 2) / 2;
    assert.ok(Math.abs((forward.integral as number) - expected) / expected < 1e-12);
    assert.equal(backward.integral, forward.integral);
  });
});
