import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { LocalTraceStore } from "../src/store.ts";
import type { DecodedSignalSample, RawCanFrame } from "../src/types.ts";

function frame(timestamp_s: number, id = 0x100): RawCanFrame {
  return {
    seq: 0,
    timestamp_s,
    channel: "1",
    arbitration_id: id,
    id_hex: id.toString(16).toUpperCase().padStart(3, "0"),
    is_extended_id: false,
    dlc: 1,
    data: Uint8Array.from([0]),
    data_hex: "00",
    direction: "Rx",
    is_remote: false,
    message_name: "M",
    decode_status: "ok",
    dbc_source: "fixture.dbc",
  };
}

function sample(timestamp_s: number, value: number | string): DecodedSignalSample {
  return {
    timestamp_s,
    channel: "1",
    arbitration_id: 0x100,
    message_name: "M",
    signal_name: "Sig",
    value,
    unit: "u",
  };
}

describe("LocalTraceStore parity behavior", () => {
  it("locateRow chooses the nearest row and clamps beyond the last row", () => {
    const store = new LocalTraceStore();
    store.ingestFrames([frame(0), frame(0.5), frame(1)]);
    assert.deepEqual(store.locateRow(0.74), { index: 1, offset: 1, timestamp_s: 0.5 });
    assert.deepEqual(store.locateRow(9), { index: 2, offset: 2, timestamp_s: 1 });
  });

  it("frame filters exclude events and id filters are substring/case-insensitive", () => {
    const store = new LocalTraceStore();
    store.ingestFrames([frame(0, 0x100), frame(0.2, 0x210)]);
    store.ingestEvents([{ seq: 0, timestamp_s: 0.1, channel: "1", event_type: "ErrorFrame", detail: "bus" }]);
    const byId = store.traceRows({ idHex: "10", limit: 100 });
    assert.equal(byId.total, 2);
    assert.deepEqual(new Set(byId.rows.map((row) => row.kind)), new Set(["frame"]));
    const byEvent = store.traceRows({ eventType: "ErrorFrame", limit: 100 });
    assert.equal(byEvent.total, 1);
    assert.equal(byEvent.rows[0].kind, "event");
  });

  it("signalSeries drops non-numeric values and keeps extrema while downsampling", () => {
    const store = new LocalTraceStore();
    store.ingestSamples([
      sample(0, 1),
      sample(0.01, "bad"),
      sample(0.02, 1000),
      sample(0.03, 2),
      sample(0.04, 3),
    ]);
    const series = store.signalSeries("M", "Sig", { maxPoints: 3 });
    assert.equal(series.downsampled, true);
    assert.ok(!series.v.includes("bad"));
    assert.ok(series.v.includes(1000));
  });

  it("signalStats exposes Python-compatible names while preserving legacy aliases", () => {
    const store = new LocalTraceStore();
    store.ingestSamples([sample(0, 1), sample(0.01, 2)]);
    const stats = store.signalStats("M", "Sig");
    assert.equal(stats.message_name, "M");
    assert.equal(stats.signal_name, "Sig");
    assert.equal(stats.message, "M");
    assert.equal(stats.signal, "Sig");
    assert.equal(stats.count, 2);
  });

  it("summarizes and computes stats without spreading large arrays into Math", () => {
    const store = new LocalTraceStore();
    const count = 140_000;
    const frames: RawCanFrame[] = [];
    const samples: DecodedSignalSample[] = [];
    for (let i = 0; i < count; i += 1) {
      frames.push(frame(i / 1000));
      samples.push(sample(i / 1000, i));
    }
    store.ingestFrames(frames);
    store.ingestSamples(samples);

    const summary = store.summary();
    assert.equal(summary.frames, count);
    assert.equal(summary.start_s, 0);
    assert.equal(summary.end_s, (count - 1) / 1000);

    const stats = store.signalStats("M", "Sig");
    assert.equal(stats.count, count);
    assert.equal(stats.min, 0);
    assert.equal(stats.max, count - 1);
  });
});
