import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { Blob } from "node:buffer";

import {
  createLineSplitter,
  scanBlob,
  scanLines,
} from "./scanner-core.mjs";

describe("createLineSplitter", () => {
  it("reconstructs lines split across arbitrary chunks", () => {
    const seen = [];
    const splitter = createLineSplitter((lines) => seen.push(...lines));

    splitter.push("date Mon\nbase h");
    splitter.push("ex timestamps absolute\n   0.000");
    splitter.push("001 1 100 Rx d 2 01 02\n   0.000002 1 101 Tx d 1 FF");
    assert.equal(splitter.getCarry(), "   0.000002 1 101 Tx d 1 FF");
    splitter.finish();

    assert.deepEqual(seen, [
      "date Mon",
      "base hex timestamps absolute",
      "   0.000001 1 100 Rx d 2 01 02",
      "   0.000002 1 101 Tx d 1 FF",
    ]);
  });
});

describe("scanLines", () => {
  it("counts classic CAN frames and events without retaining frame objects", () => {
    const stats = scanLines([
      "date Mon",
      "base hex timestamps absolute",
      "   0.000001 1 100 Rx d 2 01 02",
      "   0.000002 1 101 Tx d 1 FF",
      "   0.000003 CAN 1 Status foo",
      "not parseable",
    ]);

    assert.equal(stats.lines, 4);
    assert.equal(stats.frames, 2);
    assert.equal(stats.events, 2);
    assert.equal(stats.rxFrames, 1);
    assert.equal(stats.txFrames, 1);
    assert.equal(stats.firstTimestamp, 0.000001);
    assert.equal(stats.lastTimestamp, 0.000003);
  });
});

describe("scanBlob", () => {
  it("scans a blob using small chunks and preserves split line boundaries", async () => {
    const blob = new Blob([
      "date Mon\nbase hex timestamps absolute\n",
      "   0.000001 1 100 Rx d 2 01 02\n",
      "   0.000002 1 101 Tx d 1 FF\n",
      "   0.000003 CAN 1 Status foo\n",
    ]);
    const progress = [];
    const stats = await scanBlob(blob, {
      chunkSize: 9,
      onProgress: (payload) => progress.push(payload),
    });

    assert.equal(stats.cancelled, false);
    assert.equal(stats.frames, 2);
    assert.equal(stats.events, 1);
    assert.equal(stats.chunks > 1, true);
    assert.equal(progress.length > 1, true);
  });
});
