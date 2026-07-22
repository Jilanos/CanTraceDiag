import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { DbcCatalog } from "../src/dbc.ts";
import { Decoder } from "../src/decode.ts";
import { LocalPwaBackend } from "../src/local-backend.ts";
import { createLocalProductBackend } from "../src/product-backend.ts";
import type { RawCanFrame } from "../src/types.ts";

const FIX = path.resolve("tests/fixtures");

function readFixture(name: string): string {
  return fs.readFileSync(path.join(FIX, name), "utf8");
}

describe("local DBC and decode", () => {
  it("lists fixture signals and decodes physical values", () => {
    const catalog = new DbcCatalog();
    catalog.loadText(readFixture("sample.dbc"), "sample.dbc");
    const names = new Set(catalog.signals().map((s) => `${s.message_name}.${s.signal_name}`));
    assert.ok(names.has("EngineData.EngineSpeed"));
    assert.ok(names.has("VehicleState.VehicleSpeed"));

    const decoder = new Decoder(catalog.messageIndex());
    const frame: RawCanFrame = {
      seq: 0,
      timestamp_s: 0,
      channel: "1",
      arbitration_id: 0x100,
      id_hex: "100",
      is_extended_id: false,
      dlc: 8,
      data: Uint8Array.from([0x00, 0x10, 0x64, 0, 0, 0, 0, 0]),
      data_hex: "00 10 64 00 00 00 00 00",
      direction: "Rx",
      is_remote: false,
      message_name: null,
      decode_status: "no_database",
      dbc_source: null,
    };
    const decoded = decoder.decodeFrame(frame);
    assert.equal(decoded.frame.decode_status, "ok");
    assert.equal(decoded.frame.message_name, "EngineData");
    const speed = decoded.samples.find((sample) => sample.signal_name === "EngineSpeed");
    assert.equal(speed?.value, 1024);
    assert.equal(speed?.unit, "rpm");
  });

  it("detects conflicting arbitration ids", () => {
    const catalog = new DbcCatalog();
    catalog.loadText(readFixture("sample.dbc"), "sample.dbc");
    catalog.loadText(readFixture("sample_conflict.dbc"), "sample_conflict.dbc");
    const ambiguous = catalog.findAmbiguousIds();
    assert.deepEqual(ambiguous[0x100], ["sample.dbc:EngineData", "sample_conflict.dbc:BrakeData"]);
  });

  it("uses duplicated identical DBC definitions instead of marking unknown", () => {
    const catalog = new DbcCatalog();
    const text = readFixture("sample.dbc");
    catalog.loadText(text, "a.dbc");
    catalog.loadText(text, "b.dbc");
    assert.equal(catalog.findAmbiguousIds()[0x100], undefined);
    assert.ok(catalog.messageIndex().has(0x100));
  });

  it("normalizes DBC extended ids and decodes extended ASC frames", () => {
    const catalog = new DbcCatalog();
    catalog.loadText(`
BO_ 2364539904 EEC1: 8 Vector__XXX
 SG_ EngineSpeed : 24|16@1+ (0.125,0) [0|8031.875] "rpm" Vector__XXX
`, "j1939.dbc");
    const message = catalog.messageIndex().get(0x0cf00400);
    assert.ok(message);
    assert.equal(message.is_extended_id, true);

    const decoder = new Decoder(catalog.messageIndex());
    const decoded = decoder.decodeFrame({
      seq: 0,
      timestamp_s: 0,
      channel: "1",
      arbitration_id: 0x0cf00400,
      id_hex: "CF00400",
      is_extended_id: true,
      dlc: 8,
      data: Uint8Array.from([0, 0, 0, 0x20, 0x4e, 0, 0, 0]),
      data_hex: "00 00 00 20 4E 00 00 00",
      direction: "Rx",
      is_remote: false,
      message_name: null,
      decode_status: "no_database",
      dbc_source: null,
    });
    assert.equal(decoded.frame.decode_status, "ok");
    assert.equal(decoded.samples.find((sample) => sample.signal_name === "EngineSpeed")?.value, 2500);
  });

  it("decodes Motorola big-endian signals", () => {
    const catalog = new DbcCatalog();
    catalog.loadText(`
BO_ 256 BigMsg: 8 Vector__XXX
 SG_ BigSignal : 7|16@0+ (1,0) [0|65535] "" Vector__XXX
`, "big.dbc");
    const decoder = new Decoder(catalog.messageIndex());
    const frame: RawCanFrame = {
      seq: 0,
      timestamp_s: 0,
      channel: "1",
      arbitration_id: 0x100,
      id_hex: "100",
      is_extended_id: false,
      dlc: 8,
      data: Uint8Array.from([0x12, 0x34, 0, 0, 0, 0, 0, 0]),
      data_hex: "12 34 00 00 00 00 00 00",
      direction: "Rx",
      is_remote: false,
      message_name: null,
      decode_status: "no_database",
      dbc_source: null,
    };
    const decoded = decoder.decodeFrame(frame);
    assert.equal(decoded.frame.decode_status, "ok");
    assert.equal(decoded.samples.find((sample) => sample.signal_name === "BigSignal")?.value, 0x1234);
  });

  it("filters multiplexed signals by active mux value", () => {
    const catalog = new DbcCatalog();
    catalog.loadText(`
BO_ 512 MuxMsg: 8 Vector__XXX
 SG_ Mode M : 0|4@1+ (1,0) [0|15] "" Vector__XXX
 SG_ A m1 : 8|8@1+ (1,0) [0|255] "" Vector__XXX
 SG_ B m2 : 16|8@1+ (1,0) [0|255] "" Vector__XXX
`, "mux.dbc");
    const decoder = new Decoder(catalog.messageIndex());
    const frame: RawCanFrame = {
      seq: 0,
      timestamp_s: 0,
      channel: "1",
      arbitration_id: 0x200,
      id_hex: "200",
      is_extended_id: false,
      dlc: 8,
      data: Uint8Array.from([0x02, 0xaa, 0xbb, 0, 0, 0, 0, 0]),
      data_hex: "02 AA BB 00 00 00 00 00",
      direction: "Rx",
      is_remote: false,
      message_name: null,
      decode_status: "no_database",
      dbc_source: null,
    };
    const decoded = decoder.decodeFrame(frame);
    assert.equal(decoded.frame.decode_status, "ok");
    assert.deepEqual(decoded.samples.map((sample) => sample.signal_name), ["Mode", "B"]);
    assert.equal(decoded.samples.find((sample) => sample.signal_name === "B")?.value, 0xbb);
  });
});

describe("LocalPwaBackend", () => {
  it("imports fixture trace and exposes API-equivalent queries without FastAPI", async () => {
    const backend = new LocalPwaBackend();
    const result = await backend.importText(readFixture("sample.asc"), [
      { name: "sample.dbc", text: readFixture("sample.dbc") },
    ]);
    assert.equal(result.needs_resolution, false);
    assert.deepEqual(backend.status().summary, {
      frames: 6,
      events: 2,
      decoded_frames: 5,
      unique_ids: 3,
      start_s: 0,
      end_s: 0.05,
      decode_status: { ok: 5, unknown_id: 1 },
      event_types: ["ErrorFrame", "Status"],
    });

    const signals = backend.signals().signals as Array<{ signal_name: string }>;
    assert.ok(signals.some((signal) => signal.signal_name === "EngineSpeed"));
    const trace = backend.trace({ limit: 100 });
    assert.equal(trace.total, 8);
    assert.equal((trace.rows as Array<unknown>).length, 8);
    assert.equal(backend.trace({ limit: 100, signal: "EngineSpeed" }).total, 4);

    const series = backend.series("EngineData", "EngineSpeed");
    assert.deepEqual(series.t, [0, 0.01, 0.02, 0.05]);
    assert.deepEqual(series.v, [1024, 2048, 3072, 4096]);
    assert.equal(series.unit, "rpm");
    assert.deepEqual(backend.cursor("EngineData", "EngineSpeed", 0.012), {
      timestamp_s: 0.01,
      value: 2048,
      unit: "rpm",
    });
    const frameSignals = backend.frameSignals(0, 0x100).signals as Array<{ signal_name: string }>;
    assert.ok(frameSignals.some((sample) => sample.signal_name === "EngineTemp"));
    assert.deepEqual(backend.traceLocate(0.019), { index: 3, offset: 3, timestamp_s: 0.02, cursor: "3" });
    assert.deepEqual(backend.cursors([{ message: "EngineData", signal: "EngineSpeed" }], 0, 0.012), {
      a: { "EngineData.EngineSpeed": { timestamp_s: 0, value: 1024, unit: "rpm" } },
      b: { "EngineData.EngineSpeed": { timestamp_s: 0.01, value: 2048, unit: "rpm" } },
    });
    assert.deepEqual(backend.signalStats("EngineData", "EngineSpeed", 0, 0.02), {
      message: "EngineData",
      signal: "EngineSpeed",
      message_name: "EngineData",
      signal_name: "EngineSpeed",
      unit: "rpm",
      total: 3,
      kind: "numeric",
      count: 3,
      min: 1024,
      max: 3072,
      mean: 2048,
      std: 1024,
      rms: Math.sqrt((1024 ** 2 + 2048 ** 2 + 3072 ** 2) / 3),
    });
    assert.deepEqual(backend.signalStats("EngineData", "EngineSpeed", 10, 11), {
      message: "EngineData",
      signal: "EngineSpeed",
      message_name: "EngineData",
      signal_name: "EngineSpeed",
      unit: null,
      total: 0,
      kind: "empty",
      count: 0,
    });
    const report = backend.report();
    assert.equal(report.frames, 6);
    assert.equal(report.trace_path, "browser-local trace");
    assert.deepEqual(report.dbc_paths, ["sample.dbc"]);
    assert.match(backend.exportCsv([{ message: "EngineData", signal: "EngineSpeed" }], { start: 0, end: 0.01 }), /timestamp_s,message,signal,value,unit\n0,EngineData,EngineSpeed,1024,rpm\n0.01,EngineData,EngineSpeed,2048,rpm\n/);
    assert.match(backend.exportCsv([{ message: "EngineData", signal: "EngineSpeed" }], { format: "csv_wide" }), /timestamp_s,EngineData.EngineSpeed\n0,1024\n0.01,2048\n/);
    assert.throws(
      () => backend.exportCsv([{ message: "EngineData", signal: "EngineSpeed" }], { format: "parquet" }),
      /Parquet export is deferred/,
    );
    assert.equal(backend.importJob().phase, "complete");
    backend.purge();
    assert.equal(backend.status().loaded, false);
  });

  it("returns conflicts before importing when DBC definitions disagree", async () => {
    const backend = new LocalPwaBackend();
    const result = await backend.importText(readFixture("sample.asc"), [
      { name: "sample.dbc", text: readFixture("sample.dbc") },
      { name: "sample_conflict.dbc", text: readFixture("sample_conflict.dbc") },
    ]);
    assert.equal(result.needs_resolution, true);
    const conflicts = result.conflicts as Array<{ id_hex: string }>;
    assert.ok(conflicts.some((conflict) => conflict.id_hex === "100"));
  });
});

describe("Local product backend adapter", () => {
  it("turns DBC library quota failures into recoverable import errors", async () => {
    const originalStorage = globalThis.localStorage;
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: {
        getItem() { return "[]"; },
        removeItem() {},
        setItem() { throw new DOMException("quota", "QuotaExceededError"); },
      },
    });
    try {
      const backend = createLocalProductBackend();
      const form = new FormData();
      form.append("trace", new File([readFixture("sample.asc")], "sample.asc"));
      form.append("dbcs", new File([readFixture("sample.dbc")], "sample.dbc"));
      await assert.rejects(
        () => backend.uploadWithProgress(form, () => {}),
        /Local DBC library quota exceeded/,
      );
    } finally {
      Object.defineProperty(globalThis, "localStorage", {
        configurable: true,
        value: originalStorage,
      });
    }
  });
});
