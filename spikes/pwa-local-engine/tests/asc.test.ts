import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { parseAscText } from "../src/asc.ts";

const FIX = path.resolve("tests/fixtures");

describe("local ASC parser", () => {
  it("matches Python fixture counts and event types", () => {
    const parsed = parseAscText(fs.readFileSync(path.join(FIX, "sample.asc"), "utf8"));
    assert.equal(parsed.base, "hex");
    assert.equal(parsed.frames.length, 6);
    assert.equal(parsed.events.length, 2);
    assert.deepEqual(new Set(parsed.events.map((e) => e.event_type)), new Set(["ErrorFrame", "Status"]));
  });

  it("parses standard, extended, dlc, direction and data bytes", () => {
    const parsed = parseAscText(fs.readFileSync(path.join(FIX, "sample.asc"), "utf8"));
    const first = parsed.frames.find((frame) => frame.arbitration_id === 0x100);
    assert.ok(first);
    assert.equal(first.dlc, 8);
    assert.equal(first.direction, "Rx");
    assert.equal(first.data_hex, "00 10 64 00 00 00 00 00");
    assert.ok(parsed.frames.some((frame) => frame.arbitration_id === 0x7ff && frame.is_extended_id));
  });

  it("handles decimal-base CANalyzer data", () => {
    const parsed = parseAscText(fs.readFileSync(path.join(FIX, "sample_dec.asc"), "utf8"));
    assert.equal(parsed.base, "dec");
    assert.equal(parsed.frames.length, 2);
    assert.equal(parsed.frames[0].arbitration_id, 1552);
    assert.equal(parsed.frames[0].dlc, 7);
    assert.deepEqual(Array.from(parsed.frames[0].data), [9, 19, 0, 0, 0, 0, 43]);
    assert.equal(parsed.frames[1].data[0], 231);
  });

  it("rejects malformed ids and bytes instead of parsing prefixes", () => {
    const parsed = parseAscText(`
base hex
0.000000 1 100zzz Rx d 1 01
0.010000 1 100 Rx d 1 0G
0.020000 1 100 Rx d 1 0A
`);
    assert.equal(parsed.frames.length, 1);
    assert.equal(parsed.frames[0].timestamp_s, 0.02);
    assert.equal(parsed.events.length, 2);
  });
});
