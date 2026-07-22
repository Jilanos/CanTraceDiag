import fs from "node:fs";
import { performance } from "node:perf_hooks";

import { createLineSplitter, createScanStats, scanLines } from "./scanner-core.mjs";

globalThis.performance ??= performance;

const filePath = process.argv[2];
const chunkMiB = Number(process.argv[3] || 8);

if (!filePath) {
  console.error("Usage: node spikes/pwa-500mb/benchmark-node.mjs <trace.asc> [chunkMiB]");
  process.exit(2);
}

const fileSize = fs.statSync(filePath).size;
const decoder = new TextDecoder("utf-8", { fatal: false });
const stats = createScanStats();
const splitter = createLineSplitter((lines) => scanLines(lines, stats));
const started = performance.now();
let offset = 0;
let chunks = 0;
for await (const chunk of fs.createReadStream(filePath, { highWaterMark: chunkMiB * 1024 * 1024 })) {
  offset += chunk.byteLength;
  chunks += 1;
  stats.bytesDecoded += chunk.byteLength;
  splitter.push(decoder.decode(chunk, { stream: offset < fileSize }));
  if (chunks % 8 === 0) {
    const elapsed = Math.max(1, performance.now() - started);
    const throughput = (offset / 1024 / 1024) / (elapsed / 1000);
    process.stderr.write(
      `progress=${((offset / fileSize) * 100).toFixed(1)}% `
      + `throughput=${throughput.toFixed(1)}MiB/s\r`,
    );
  }
}
const tail = decoder.decode();
if (tail) splitter.push(tail);
splitter.finish();
const elapsedMs = performance.now() - started;
process.stderr.write("\n");
console.log(JSON.stringify({
  filePath,
  fileMiB: fileSize / 1024 / 1024,
  chunkMiB,
  elapsedMs,
  throughputMiBps: (fileSize / 1024 / 1024) / (elapsedMs / 1000),
  frames: stats.frames,
  events: stats.events,
  lines: stats.lines,
  chunks,
  firstTimestamp: stats.firstTimestamp,
  lastTimestamp: stats.lastTimestamp,
  memory: process.memoryUsage(),
}, null, 2));
