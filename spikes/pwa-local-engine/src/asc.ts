import type { NonDataEvent, RawCanFrame } from "./types.ts";

const TIMESTAMP = /^\s*(\d+(?:\.\d+)?)\s+(.*)$/;

export type AscItem = { kind: "frame"; frame: Omit<RawCanFrame, "seq"> }
  | { kind: "event"; event: Omit<NonDataEvent, "seq"> };

export type AscParseResult = {
  base: "hex" | "dec";
  frames: RawCanFrame[];
  events: NonDataEvent[];
};

export class AscScanner {
  base: "hex" | "dec" = "hex";
  parsedLines = 0;

  feed(rawLine: string): AscItem | null {
    const stripped = rawLine.trim();
    if (!stripped) return null;

    const lowered = stripped.toLowerCase();
    if (lowered.startsWith("base")) {
      this.base = lowered.includes("dec") ? "dec" : "hex";
      return null;
    }
    if (isHeader(stripped)) return null;

    const match = TIMESTAMP.exec(rawLine.replace(/\n$/, ""));
    if (!match) return null;
    this.parsedLines += 1;

    const timestamp = Number(match[1]);
    const rest = match[2].trim();
    return parseBody(timestamp, rest, this.base);
  }
}

export function parseAscText(text: string): AscParseResult {
  const scanner = new AscScanner();
  const frames: RawCanFrame[] = [];
  const events: NonDataEvent[] = [];
  let frameSeq = 0;
  let eventSeq = 0;

  for (const line of text.split(/\r?\n/)) {
    const item = scanner.feed(line);
    if (!item) continue;
    if (item.kind === "frame") {
      frames.push({ ...item.frame, seq: frameSeq });
      frameSeq += 1;
    } else {
      events.push({ ...item.event, seq: eventSeq });
      eventSeq += 1;
    }
  }
  return { base: scanner.base, frames, events };
}

export async function importAscFile(
  file: Blob,
  onBatch: (batch: AscItem[]) => void,
  options: { chunkSize?: number; batchSize?: number; onProgress?: (progress: number) => void } = {},
): Promise<{ base: "hex" | "dec"; frames: number; events: number }> {
  const chunkSize = options.chunkSize ?? 8 * 1024 * 1024;
  const batchSize = options.batchSize ?? 25_000;
  const scanner = new AscScanner();
  const decoder = new TextDecoder("utf-8", { fatal: false });
  let carry = "";
  let offset = 0;
  let frames = 0;
  let events = 0;
  let batch: AscItem[] = [];

  const flush = () => {
    if (!batch.length) return;
    onBatch(batch);
    batch = [];
  };
  const handleLine = (line: string) => {
    const item = scanner.feed(line);
    if (!item) return;
    if (item.kind === "frame") frames += 1;
    else events += 1;
    batch.push(item);
    if (batch.length >= batchSize) flush();
  };

  while (offset < file.size) {
    const next = Math.min(offset + chunkSize, file.size);
    const buffer = await file.slice(offset, next).arrayBuffer();
    offset = next;
    const text = decoder.decode(buffer, { stream: offset < file.size });
    const joined = carry + text;
    const lines = joined.split(/\r?\n/);
    carry = lines.pop() ?? "";
    for (const line of lines) handleLine(line);
    options.onProgress?.(file.size ? offset / file.size : 1);
  }
  const tail = decoder.decode();
  if (tail) carry += tail;
  if (carry) handleLine(carry);
  flush();
  return { base: scanner.base, frames, events };
}

function parseBody(timestamp_s: number, rest: string, baseName: "hex" | "dec"): AscItem | null {
  const tokens = rest.split(/\s+/).filter(Boolean);
  if (!tokens.length) return null;

  if (tokens[0].toLowerCase().startsWith("errorframe")) {
    return { kind: "event", event: { timestamp_s, channel: null, event_type: "ErrorFrame", detail: rest || null } };
  }
  if (tokens.length >= 2 && tokens[1].toLowerCase().startsWith("errorframe")) {
    return { kind: "event", event: { timestamp_s, channel: tokens[0], event_type: "ErrorFrame", detail: tokens.slice(2).join(" ") || null } };
  }
  if (looksLikeStatus(tokens)) {
    return { kind: "event", event: { timestamp_s, channel: statusChannel(tokens), event_type: "Status", detail: tokens.join(" ") } };
  }
  if (tokens[0]?.toUpperCase() === "CANFD" || tokens[1]?.toUpperCase() === "CANFD") {
    return { kind: "event", event: { timestamp_s, channel: null, event_type: "CANFD", detail: rest } };
  }

  const frame = parseDataFrame(timestamp_s, tokens, baseName);
  if (frame) return { kind: "frame", frame };
  return { kind: "event", event: { timestamp_s, channel: null, event_type: "Other", detail: rest } };
}

function parseDataFrame(
  timestamp_s: number,
  tokens: string[],
  baseName: "hex" | "dec",
): Omit<RawCanFrame, "seq"> | null {
  if (tokens.length < 5) return null;
  const numericBase = baseName === "hex" ? 16 : 10;
  const channel = tokens[0];
  const idToken = tokens[1];
  const is_extended_id = /x$/i.test(idToken);
  const arbitration_id = parseIntSafe(is_extended_id ? idToken.slice(0, -1) : idToken, numericBase);
  if (arbitration_id === null) return null;
  const direction = tokens[2];
  if (direction !== "Rx" && direction !== "Tx") return null;
  const kind = tokens[3].toLowerCase();
  if (kind !== "d" && kind !== "r") return null;
  const dlc = parseIntSafe(tokens[4], 10);
  if (dlc === null || dlc < 0 || dlc > 64) return null;

  const values = tokens.slice(5, 5 + dlc).map((token) => parseIntSafe(token, numericBase));
  if (values.some((v) => v === null || v < 0 || v > 255)) return null;
  const data = kind === "r" ? new Uint8Array() : Uint8Array.from(values as number[]);

  return {
    timestamp_s,
    channel,
    arbitration_id,
    id_hex: idHex(arbitration_id, is_extended_id),
    is_extended_id,
    dlc,
    data,
    data_hex: data.length ? Array.from(data, (byte) => byte.toString(16).toUpperCase().padStart(2, "0")).join(" ") : null,
    direction,
    is_remote: kind === "r",
    message_name: null,
    decode_status: "no_database",
    dbc_source: null,
  };
}

export function idHex(arbitration_id: number, is_extended_id: boolean): string {
  return arbitration_id.toString(16).toUpperCase().padStart(is_extended_id ? 8 : 3, "0");
}

function parseIntSafe(token: string, base: number): number | null {
  const pattern = base === 16 ? /^[0-9a-fA-F]+$/ : /^\d+$/;
  if (!pattern.test(token)) return null;
  const value = Number.parseInt(token, base);
  return Number.isFinite(value) ? value : null;
}

function isHeader(stripped: string): boolean {
  const lowered = stripped.toLowerCase();
  if (lowered.startsWith("//")) return true;
  if (lowered.startsWith("begin triggerblock") || lowered.startsWith("end triggerblock")) return true;
  const first = stripped.split(/\s+/, 1)[0]?.toLowerCase();
  return ["date", "base", "no", "measurement", "internal", "version"].includes(first);
}

function looksLikeStatus(tokens: string[]): boolean {
  return tokens.slice(0, 4).some((token) => token.toLowerCase().startsWith("status"));
}

function statusChannel(tokens: string[]): string | null {
  if (tokens[0] === "CAN" && tokens[1]) return tokens[1];
  if (/^\d+$/.test(tokens[0])) return tokens[0];
  return null;
}
