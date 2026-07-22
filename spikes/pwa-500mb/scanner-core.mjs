const TIMESTAMP_RE = /^\s*(\d+(?:\.\d+)?)\s+(.*)$/;

export function createScanStats() {
  return {
    lines: 0,
    frames: 0,
    events: 0,
    parseableTimestampLines: 0,
    rxFrames: 0,
    txFrames: 0,
    firstTimestamp: null,
    lastTimestamp: null,
    minLineLength: null,
    maxLineLength: 0,
    bytesDecoded: 0,
  };
}

export function mergeStats(target, source) {
  target.lines += source.lines;
  target.frames += source.frames;
  target.events += source.events;
  target.parseableTimestampLines += source.parseableTimestampLines;
  target.rxFrames += source.rxFrames;
  target.txFrames += source.txFrames;
  target.bytesDecoded += source.bytesDecoded;
  if (source.firstTimestamp !== null) {
    target.firstTimestamp = target.firstTimestamp === null
      ? source.firstTimestamp
      : Math.min(target.firstTimestamp, source.firstTimestamp);
  }
  if (source.lastTimestamp !== null) {
    target.lastTimestamp = target.lastTimestamp === null
      ? source.lastTimestamp
      : Math.max(target.lastTimestamp, source.lastTimestamp);
  }
  if (source.minLineLength !== null) {
    target.minLineLength = target.minLineLength === null
      ? source.minLineLength
      : Math.min(target.minLineLength, source.minLineLength);
  }
  target.maxLineLength = Math.max(target.maxLineLength, source.maxLineLength);
  return target;
}

export function scanLine(line, stats = createScanStats()) {
  const trimmed = line.trim();
  if (!trimmed) return stats;
  const lowered = trimmed.toLowerCase();
  if (
    lowered.startsWith("//")
    || lowered.startsWith("date")
    || lowered.startsWith("base")
    || lowered.startsWith("begin triggerblock")
    || lowered.startsWith("end triggerblock")
  ) {
    return stats;
  }

  stats.lines += 1;
  stats.minLineLength = stats.minLineLength === null
    ? line.length
    : Math.min(stats.minLineLength, line.length);
  stats.maxLineLength = Math.max(stats.maxLineLength, line.length);

  const match = TIMESTAMP_RE.exec(line);
  if (!match) {
    stats.events += 1;
    return stats;
  }

  stats.parseableTimestampLines += 1;
  const timestamp = Number(match[1]);
  if (Number.isFinite(timestamp)) {
    stats.firstTimestamp = stats.firstTimestamp === null
      ? timestamp
      : Math.min(stats.firstTimestamp, timestamp);
    stats.lastTimestamp = stats.lastTimestamp === null
      ? timestamp
      : Math.max(stats.lastTimestamp, timestamp);
  }

  const tokens = match[2].trim().split(/\s+/);
  if (looksLikeClassicCanFrame(tokens)) {
    stats.frames += 1;
    if (tokens[2] === "Rx") stats.rxFrames += 1;
    if (tokens[2] === "Tx") stats.txFrames += 1;
  } else {
    stats.events += 1;
  }
  return stats;
}

export function scanLines(lines, stats = createScanStats()) {
  for (const line of lines) scanLine(line, stats);
  return stats;
}

export function createLineSplitter(onLines) {
  let carry = "";
  return {
    push(text) {
      const joined = carry + text;
      const lines = joined.split(/\r?\n/);
      carry = lines.pop() ?? "";
      if (lines.length) onLines(lines);
      return lines.length;
    },
    finish() {
      if (carry) {
        onLines([carry]);
        carry = "";
        return 1;
      }
      return 0;
    },
    getCarry() {
      return carry;
    },
  };
}

export async function scanBlob(blob, options = {}) {
  const {
    chunkSize = 8 * 1024 * 1024,
    onProgress,
    shouldCancel,
  } = options;
  const decoder = new TextDecoder("utf-8", { fatal: false });
  const stats = createScanStats();
  const splitter = createLineSplitter((lines) => scanLines(lines, stats));
  const startedAt = performance.now();
  let offset = 0;
  let chunks = 0;

  while (offset < blob.size) {
    if (shouldCancel?.()) {
      return finishResult({ stats, startedAt, offset, chunks, chunkSize, cancelled: true });
    }
    const next = Math.min(offset + chunkSize, blob.size);
    const buffer = await blob.slice(offset, next).arrayBuffer();
    offset = next;
    chunks += 1;
    const text = decoder.decode(buffer, { stream: offset < blob.size });
    stats.bytesDecoded += buffer.byteLength;
    splitter.push(text);
    onProgress?.(progressPayload({ stats, offset, size: blob.size, chunks, chunkSize, startedAt }));
  }

  const tail = decoder.decode();
  if (tail) splitter.push(tail);
  splitter.finish();
  return finishResult({ stats, startedAt, offset, chunks, chunkSize, cancelled: false });
}

function looksLikeClassicCanFrame(tokens) {
  if (tokens.length < 5) return false;
  if (!/^\d+$/.test(tokens[0])) return false;
  if (!/^[0-9A-Fa-f]+x?$/.test(tokens[1])) return false;
  if (tokens[2] !== "Rx" && tokens[2] !== "Tx") return false;
  if (tokens[3] !== "d" && tokens[3] !== "r") return false;
  const dlc = Number(tokens[4]);
  return Number.isInteger(dlc) && dlc >= 0 && dlc <= 64;
}

function progressPayload({ stats, offset, size, chunks, chunkSize, startedAt }) {
  const elapsedMs = Math.max(1, performance.now() - startedAt);
  return {
    ...stats,
    offset,
    size,
    chunks,
    chunkSize,
    elapsedMs,
    percent: size ? offset / size : 1,
    throughputMBps: (offset / 1024 / 1024) / (elapsedMs / 1000),
  };
}

function finishResult({ stats, startedAt, offset, chunks, chunkSize, cancelled }) {
  const elapsedMs = Math.max(1, performance.now() - startedAt);
  return {
    ...stats,
    offset,
    chunks,
    chunkSize,
    elapsedMs,
    cancelled,
    throughputMBps: (offset / 1024 / 1024) / (elapsedMs / 1000),
  };
}
