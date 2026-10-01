import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { DbcCatalog } from "../src/dbc.ts";
import { Decoder } from "../src/decode.ts";
import { LocalPwaBackend, LOCAL_TRACE_SUFFIXES, localTraceRejection } from "../src/local-backend.ts";
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
  it("keeps unique trace-filter event types while reporting exact anomaly counts", async () => {
    const backend = new LocalPwaBackend();
    await backend.importText([
      "base hex  timestamps absolute",
      "0.000000 1 ErrorFrame",
      "0.010000 1 ErrorFrame",
      "0.020000 CAN 1 Status:chip status error active",
    ].join("\n"), []);

    assert.deepEqual(backend.status().summary.event_types, ["ErrorFrame", "Status"]);
    const report = backend.report() as { events: number; anomalies: { asc_events: Record<string, number> } };
    assert.equal(report.events, 3);
    assert.deepEqual(report.anomalies.asc_events, { ErrorFrame: 2, Status: 1 });
  });

  it("dispatches a text TRC filename through the same normalized import path", async () => {
    const backend = new LocalPwaBackend();
    const result = await backend.importText(readFixture("sample.trc"), [], {}, "sample.trc");
    assert.equal(result.needs_resolution, false);
    assert.equal(backend.status().summary.frames, 4);
    assert.equal(backend.trace({ limit: 10 }).total, 4);
  });

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

  it("exposes imported DBC names in load order for collapsible explorer groups", async () => {
    const backend = new LocalPwaBackend();
    await backend.importText(readFixture("sample.asc"), [
      { name: "sample.dbc", text: readFixture("sample.dbc") },
      { name: "sample_body.dbc", text: readFixture("sample_body.dbc") },
    ]);

    const payload = backend.signals() as {
      databases: string[];
      active_database: string | null;
    };
    assert.deepEqual(payload.databases, ["sample.dbc", "sample_body.dbc"]);
    assert.equal(payload.active_database, "sample.dbc");
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

describe("Browser-local BLF capability boundary", () => {
  it("supports exactly the text trace formats the engine can parse", () => {
    assert.deepEqual([...LOCAL_TRACE_SUFFIXES], [".asc", ".trc"]);
    assert.equal(localTraceRejection("sample.asc"), null);
    assert.equal(localTraceRejection("sample.trc"), null);
    assert.equal(localTraceRejection("SAMPLE.TRC"), null);
  });

  it("names the server as the way to open a BLF recording", () => {
    const rejection = localTraceRejection("acquisition.blf") ?? "";
    assert.match(rejection, /BLF/);
    assert.match(rejection, /server/i);
  });

  it("names server mode as the way to open an MF4 recording", () => {
    for (const name of ["00000002.MF4", "trace.mf4"]) {
      const rejection = localTraceRejection(name) ?? "";
      assert.match(rejection, /MF4 recordings are not supported in the browser app/);
      assert.match(rejection, /server mode/i);
    }
  });

  it("rejects an MF4 selection before reading the file", async () => {
    const backend = createLocalProductBackend();
    const form = new FormData();
    form.append("trace", new File([new TextEncoder().encode("UnFinMF 4.11    ")], "00000002.MF4"));

    await assert.rejects(
      () => backend.uploadWithProgress(form, () => {}),
      /MF4 recordings are not supported in the browser app/,
    );
    assert.equal(Number((backend.__backend.status() as { summary: Record<string, unknown> }).summary.frames), 0);
  });

  it("advertises no server capability and refuses raw ASC export", async () => {
    const backend = createLocalProductBackend();
    // api() resolves paths against the page location, which node lacks.
    const hadWindow = "window" in globalThis;
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: { location: { href: "http://localhost/" } },
    });
    try {
      const status = (await backend.api("/api/status")) as Record<string, unknown>;
      assert.equal(status.capabilities, undefined);
      await assert.rejects(
        () => backend.api("/api/export-asc", { method: "POST", body: "{}" }),
        /Raw ASC trace export needs the CanTraceDiag server app/,
      );
    } finally {
      if (!hadWindow) delete (globalThis as { window?: unknown }).window;
    }
  });

  it("rejects a BLF selection before reading the file", async () => {
    const backend = createLocalProductBackend();
    const form = new FormData();
    // A file the engine must never try to parse as text, chosen past the
    // picker's advisory accept filter.
    form.append("trace", new File([new Uint8Array([0x4c, 0x4f, 0x47, 0x47])], "acquisition.blf"));
    form.append("dbcs", new File([readFixture("sample.dbc")], "sample.dbc"));

    await assert.rejects(
      () => backend.uploadWithProgress(form, () => {}),
      /Binary BLF traces are not supported in the browser app/,
    );
    // Nothing was imported, so the previous (empty) session is untouched.
    assert.equal(Number((backend.__backend.status() as { summary: Record<string, unknown> }).summary.frames), 0);
  });

  it("still imports ASC and TRC traces locally", async () => {
    // The import path persists DBCs to the library, which node has no
    // localStorage for; the stub keeps the assertion about the trace formats.
    const originalStorage = globalThis.localStorage;
    let stored = "[]";
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: keyedStorage(() => stored, (value) => { stored = value; }),
    });
    try {
      for (const name of ["sample.asc", "sample.trc"]) {
        const backend = createLocalProductBackend();
        const form = new FormData();
        form.append("trace", new File([readFixture(name)], name));
        form.append("dbcs", new File([readFixture("sample.dbc")], "sample.dbc"));
        await backend.uploadWithProgress(form, () => {});
        const status = backend.__backend.status() as { summary: Record<string, unknown> };
        assert.ok(Number(status.summary.frames) > 0, `${name} imported no frames`);
      }
    } finally {
      Object.defineProperty(globalThis, "localStorage", {
        configurable: true,
        value: originalStorage,
      });
    }
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

  it("keeps a deterministic legacy hash collision as distinct DBC library entries", async () => {
    const originalStorage = globalThis.localStorage;
    let stored = "[]";
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: keyedStorage(() => stored, (value) => { stored = value; }),
    });
    try {
      const suffix = '\nBO_ 256 Msg: 1 Vector__XXX\n SG_ Value : 0|8@1+ (1,0) [0|255] "" Vector__XXX\n';
      const first = `costarring${suffix}`;
      const second = `liquid${suffix}`;
      const backend = createLocalProductBackend();
      const form = new FormData();
      form.append("trace", new File([readFixture("sample.asc")], "sample.asc"));
      form.append("dbcs", new File([first], "first.dbc"));
      form.append("dbcs", new File([second], "second.dbc"));
      await backend.uploadWithProgress(form, () => {});

      const entries = JSON.parse(stored) as Array<{ digest: string; name: string }>;
      assert.deepEqual(entries.map((entry) => entry.name), ["first.dbc", "second.dbc"]);
      assert.equal(new Set(entries.map((entry) => entry.digest)).size, 2);
      assert.ok(entries.every((entry) => /^[a-f0-9]{64}$/.test(entry.digest)));

      const duplicate = new FormData();
      duplicate.append("trace", new File([readFixture("sample.asc")], "sample.asc"));
      duplicate.append("dbcs", new File([first], "renamed-copy.dbc"));
      await backend.uploadWithProgress(duplicate, () => {});
      assert.equal((JSON.parse(stored) as unknown[]).length, 2);
    } finally {
      Object.defineProperty(globalThis, "localStorage", {
        configurable: true,
        value: originalStorage,
      });
    }
  });

  it("migrates a usable legacy DBC library entry before reusing it", async () => {
    const originalStorage = globalThis.localStorage;
    let stored = JSON.stringify([{
      digest: "5e4daa9d",
      name: "legacy.dbc",
      text: readFixture("sample.dbc"),
      last_used: "2026-01-01T00:00:00.000Z",
    }]);
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: keyedStorage(() => stored, (value) => { stored = value; }),
    });
    try {
      const backend = createLocalProductBackend();
      const migrate = new FormData();
      migrate.append("trace", new File([readFixture("sample.asc")], "sample.asc"));
      migrate.append("dbcs", new File([readFixture("sample_body.dbc")], "body.dbc"));
      await backend.uploadWithProgress(migrate, () => {});

      const entries = JSON.parse(stored) as Array<{ digest: string; name: string }>;
      const legacy = entries.find((entry) => entry.name === "legacy.dbc");
      assert.ok(legacy);
      assert.match(legacy.digest, /^[a-f0-9]{64}$/);

      const reuse = new FormData();
      reuse.append("trace", new File([readFixture("sample.asc")], "sample.asc"));
      reuse.append("library", legacy.digest);
      const result = await backend.uploadWithProgress(reuse, () => {}) as { needs_resolution: boolean };
      assert.equal(result.needs_resolution, false);
      assert.equal(backend.__backend.status().summary.decoded_frames, 5);
    } finally {
      Object.defineProperty(globalThis, "localStorage", {
        configurable: true,
        value: originalStorage,
      });
    }
  });
});

/* localStorage stub: the DBC library slot is exposed through `get`/`set` so a
 * test can inspect it, every other key (e.g. the remembered selection) lives
 * in its own map. */
function keyedStorage(get: () => string, set: (value: string) => void) {
  const other = new Map<string, string>();
  return {
    getItem(key: string) { return key === LIBRARY_KEY ? get() : other.get(key) ?? null; },
    removeItem(key: string) { if (key === LIBRARY_KEY) set("[]"); else other.delete(key); },
    setItem(key: string, value: string) { if (key === LIBRARY_KEY) set(value); else other.set(key, value); },
    other,
  };
}

const LIBRARY_KEY = "ctd.pwa.dbc-library.v1";
const HISTORY_KEY = "ctd.pwa.last-dbc-selection.v1";

describe("Remembered DBC selection in the local adapter", () => {
  async function withStorage(run: (storage: ReturnType<typeof keyedStorage>, library: () => Array<{ digest: string; name: string }>) => Promise<void>) {
    const originalStorage = globalThis.localStorage;
    let stored = "[]";
    const storage = keyedStorage(() => stored, (value) => { stored = value; });
    const originalWindow = (globalThis as { window?: unknown }).window;
    Object.defineProperty(globalThis, "localStorage", { configurable: true, value: storage });
    // The adapter resolves endpoint paths against the page URL.
    Object.defineProperty(globalThis, "window", { configurable: true, value: { location: { href: "http://127.0.0.1/" } } });
    try {
      await run(storage, () => JSON.parse(stored));
    } finally {
      Object.defineProperty(globalThis, "localStorage", { configurable: true, value: originalStorage });
      Object.defineProperty(globalThis, "window", { configurable: true, value: originalWindow });
    }
  }

  function form(dbcs: Array<[string, string]>, library: string[] = [], trace = "sample.asc"): FormData {
    const data = new FormData();
    data.append("trace", new File([readFixture(trace)], trace));
    for (const [name, text] of dbcs) data.append("dbcs", new File([text], name));
    for (const digest of library) data.append("library", digest);
    return data;
  }

  it("persists the ordered mixed uploaded/reused set and survives a new adapter (reload)", async () => {
    await withStorage(async (_storage, library) => {
      let backend = createLocalProductBackend();
      assert.deepEqual((await backend.api("/api/dbc-library") as { last_session_digests: string[] }).last_session_digests, []);
      await backend.uploadWithProgress(form([["sample.dbc", readFixture("sample.dbc")]]), () => {});
      const reused = library()[0].digest;
      await backend.uploadWithProgress(form([["sample_body.dbc", readFixture("sample_body.dbc")]], [reused]), () => {});
      const uploaded = library().find((entry) => entry.name === "sample_body.dbc")!.digest;

      backend = createLocalProductBackend();   // a browser reload builds a fresh adapter
      const payload = await backend.api("/api/dbc-library") as { last_session_digests: string[]; last_session: string[] };
      assert.deepEqual(payload.last_session_digests, [uploaded, reused]);
      assert.deepEqual(payload.last_session, ["sample_body.dbc", "sample.dbc"]);
      // Trace-only load with the remembered set.
      await backend.uploadWithProgress(form([], payload.last_session_digests), () => {});
      assert.ok(Number(backend.__backend.status().summary.decoded_frames) > 0);
    });
  });

  it("selects identical content once and keeps same-name different content distinct", async () => {
    await withStorage(async (storage, library) => {
      const backend = createLocalProductBackend();
      await backend.uploadWithProgress(form([["common.dbc", readFixture("sample.dbc")]]), () => {});
      const first = library()[0].digest;
      // Re-upload of identical content while also checking its library entry.
      await backend.uploadWithProgress(form([["copy.dbc", readFixture("sample.dbc")]], [first]), () => {});
      assert.deepEqual(JSON.parse(storage.other.get(HISTORY_KEY)!).digests, [first]);
      await backend.uploadWithProgress(form([["common.dbc", readFixture("sample_body.dbc")]]), () => {});
      const history = JSON.parse(storage.other.get(HISTORY_KEY)!).digests;
      assert.equal(history.length, 1);
      assert.notEqual(history[0], first);
      assert.equal(library().filter((entry) => entry.name === "common.dbc").length, 1);
    });
  });

  it("keeps the previous set on failed or unresolved imports and commits after resolution", async () => {
    await withStorage(async (storage, library) => {
      const backend = createLocalProductBackend();
      await backend.uploadWithProgress(form([["sample.dbc", readFixture("sample.dbc")]]), () => {});
      const before = storage.other.get(HISTORY_KEY);
      await assert.rejects(() => backend.uploadWithProgress(form([], []), () => {}));
      assert.equal(storage.other.get(HISTORY_KEY), before);

      const digest = library()[0].digest;
      const conflict = await backend.uploadWithProgress(
        form([["sample_conflict.dbc", readFixture("sample_conflict.dbc")]], [digest]), () => {},
      ) as { needs_resolution: boolean };
      assert.equal(conflict.needs_resolution, true);
      assert.equal(storage.other.get(HISTORY_KEY), before);

      await backend.api("/api/resolve", { method: "POST", body: JSON.stringify({ resolution: { "0x100": "sample.dbc" } }) });
      const after = JSON.parse(storage.other.get(HISTORY_KEY)!).digests;
      assert.equal(after.length, 2);
      assert.ok(after.includes(digest));
    });
  });

  it("skips deleted entries, migrates only unique legacy names, and clears on purge", async () => {
    await withStorage(async (storage, library) => {
      const backend = createLocalProductBackend();
      await backend.uploadWithProgress(form([["a.dbc", readFixture("sample.dbc")]]), () => {});
      await backend.uploadWithProgress(form([["body.dbc", readFixture("sample_body.dbc")]]), () => {});
      storage.other.set(HISTORY_KEY, JSON.stringify({ version: 1, digests: ["gone", library()[0].digest] }));
      let payload = await backend.api("/api/dbc-library") as { last_session_digests: string[] };
      assert.deepEqual(payload.last_session_digests, [library()[0].digest]);

      storage.other.set(HISTORY_KEY, JSON.stringify(["a.dbc", "missing.dbc"]));
      payload = await backend.api("/api/dbc-library") as { last_session_digests: string[] };
      assert.deepEqual(payload.last_session_digests, [library()[0].digest]);
      assert.deepEqual(JSON.parse(storage.other.get(HISTORY_KEY)!), { version: 1, digests: [library()[0].digest] });

      // Two entries named alike: an ambiguous legacy name stays unchecked.
      const entries = library();
      entries[1].name = "a.dbc";
      storage.setItem(LIBRARY_KEY, JSON.stringify(entries));
      storage.other.set(HISTORY_KEY, JSON.stringify(["a.dbc"]));
      payload = await backend.api("/api/dbc-library") as { last_session_digests: string[] };
      assert.deepEqual(payload.last_session_digests, []);

      storage.other.set(HISTORY_KEY, "{not json");
      payload = await backend.api("/api/dbc-library") as { last_session_digests: string[] };
      assert.deepEqual(payload.last_session_digests, []);

      await backend.api("/api/workspace-purge", { method: "POST" });
      assert.equal(storage.other.has(HISTORY_KEY), false);
      assert.deepEqual(library(), []);
    });
  });

  it("never blocks a completed import when the history cannot be written", async () => {
    await withStorage(async (storage) => {
      const original = storage.setItem;
      storage.setItem = (key: string, value: string) => {
        if (key === HISTORY_KEY) throw new DOMException("quota", "QuotaExceededError");
        original(key, value);
      };
      const warn = console.warn;
      console.warn = () => {};
      try {
        const backend = createLocalProductBackend();
        const result = await backend.uploadWithProgress(form([["sample.dbc", readFixture("sample.dbc")]]), () => {}) as { needs_resolution: boolean };
        assert.equal(result.needs_resolution, false);
        const payload = await backend.api("/api/dbc-library") as { last_session_digests: string[] };
        assert.deepEqual(payload.last_session_digests, []);
      } finally {
        console.warn = warn;
      }
    });
  });
});
