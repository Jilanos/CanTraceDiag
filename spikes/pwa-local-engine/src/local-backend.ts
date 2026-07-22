import { parseAscText, type AscItem } from "./asc.ts";
import { DbcCatalog } from "./dbc.ts";
import { Decoder } from "./decode.ts";
import { LocalTraceStore } from "./store.ts";
import type { ImportProgress, NonDataEvent, RawCanFrame } from "./types.ts";

export class LocalPwaBackend {
  store = new LocalTraceStore();
  catalog = new DbcCatalog();
  lastJob: ImportProgress = { phase: "idle", progress: 0, cancellable: false };
  ambiguousIds: Record<number, string[]> = {};
  resolution: Record<number, string> = {};
  traceName: string | null = null;
  dbcNames: string[] = [];

  async importText(traceText: string, dbcs: { name: string; text: string }[], resolution: Record<number, string> = {}): Promise<Record<string, unknown>> {
    this.purge();
    this.lastJob = { phase: "loading_dbc", progress: 0.05, cancellable: true };
    this.dbcNames = dbcs.map((dbc) => dbc.name);
    for (const dbc of dbcs) this.catalog.loadText(dbc.text, dbc.name);
    this.ambiguousIds = this.catalog.findAmbiguousIds();
    this.resolution = resolution;
    const unresolved = Object.keys(this.ambiguousIds)
      .map(Number)
      .filter((id) => resolution[id] === undefined);
    if (unresolved.length) {
      this.lastJob = { phase: "awaiting_resolution", progress: 0.95, cancellable: false };
      return { needs_resolution: true, conflicts: this.conflictPayload() };
    }

    this.lastJob = { phase: "indexing", progress: 0.2, cancellable: true };
    const parsed = parseAscText(traceText);
    const messageIndex = this.catalog.messageIndex(resolution);
    const decoder = new Decoder(messageIndex, new Set(Object.keys(this.ambiguousIds).map(Number)));
    const items: AscItem[] = [];
    for (const frame of parsed.frames) items.push({ kind: "frame", frame });
    for (const event of parsed.events) items.push({ kind: "event", event });
    this.ingestItems(items, decoder);
    this.lastJob = { phase: "complete", progress: 1, cancellable: false };
    return {
      needs_resolution: false,
      summary: this.store.summary(),
      ambiguous_ids: this.hexKeyedAmbiguousIds(),
      resolution: this.hexKeyedResolution(),
    };
  }

  status(): Record<string, unknown> {
    const summary = this.store.summary();
    return {
      loaded: Number(summary.frames) > 0,
      summary,
      ambiguous_ids: this.hexKeyedAmbiguousIds(),
      resolution: this.hexKeyedResolution(),
      event_types: summary.event_types,
    };
  }

  signals(): Record<string, unknown> {
    const present = this.store.presentSignalKeys();
    const presentIds = this.store.presentArbitrationIds();
    return {
      signals: this.catalog.signals().map((signal) => ({
        ...signal,
        id_hex: idHex(signal.arbitration_id, signal.is_extended_id),
        present: present.has(`${signal.message_name}\u0000${signal.signal_name}\u0000${signal.arbitration_id}`)
          || presentIds.has(signal.arbitration_id),
      })),
    };
  }

  trace(params: {
    offset?: number;
    cursor?: string;
    limit?: number;
    start?: number;
    end?: number;
    includeFrames?: boolean;
    includeEvents?: boolean;
    idHex?: string;
    message?: string;
    direction?: string;
    decodeStatus?: string;
    eventType?: string;
    signal?: string;
  } = {}): Record<string, unknown> {
    const limit = params.limit ?? 200;
    const offset = cursorToOffset(params.cursor) ?? params.offset ?? 0;
    const result = this.store.traceRows({ ...params, offset, limit });
    const prevOffset = Math.max(0, offset - limit);
    const nextOffset = offset + result.rows.length;
    return {
      ...result,
      start_index: offset,
      next_cursor: nextOffset < result.total ? String(nextOffset) : null,
      prev_cursor: offset > 0 ? String(prevOffset) : null,
    };
  }

  traceLocate(at: number, params: Parameters<LocalPwaBackend["trace"]>[0] = {}): Record<string, unknown> {
    const loc = this.store.locateRow(at, params);
    return { ...loc, cursor: loc.index === null ? null : String(loc.index) };
  }

  series(message: string, signal: string, params: { start?: number; end?: number; maxPoints?: number } = {}): Record<string, unknown> {
    return this.store.signalSeries(message, signal, params);
  }

  cursor(message: string, signal: string, at: number): Record<string, unknown> | null {
    return this.store.nearestSample(message, signal, at);
  }

  cursors(signals: Array<{ message: string; signal: string }>, a?: number | null, b?: number | null): Record<string, unknown> {
    const values = (at: number | null | undefined) => {
      if (at === null || at === undefined) return {};
      return Object.fromEntries(signals.map(({ message, signal }) => [
        `${message}.${signal}`,
        this.cursor(message, signal, at),
      ]));
    };
    return { a: values(a), b: values(b) };
  }

  frameSignals(at: number, id: number): Record<string, unknown> {
    return { signals: this.store.frameSignals(at, id) };
  }

  signalStats(message: string, signal: string, start?: number, end?: number): Record<string, unknown> {
    return this.store.signalStats(message, signal, start, end);
  }

  report(): Record<string, unknown> {
    const summary = this.store.summary();
    if (Number(summary.frames) === 0 && Number(summary.events) === 0) {
      throw new Error("No trace loaded.");
    }
    const start = summary.start_s as number | null;
    const end = summary.end_s as number | null;
    const status = summary.decode_status as Record<string, number>;
    const eventCounts: Record<string, number> = {};
    for (const eventType of summary.event_types as string[]) eventCounts[eventType] = (eventCounts[eventType] ?? 0) + 1;
    return {
      trace_path: this.traceName ?? "browser-local trace",
      dbc_paths: this.dbcNames,
      dbcs_used: this.store.dbcsUsed(),
      start_s: start,
      end_s: end,
      duration_s: start === null || end === null ? null : end - start,
      frames: summary.frames,
      events: summary.events,
      decoded_frames: summary.decoded_frames,
      unique_ids: summary.unique_ids,
      decode_status: status,
      anomalies: {
        unknown_id: status.unknown_id ?? 0,
        ambiguous_id: status.ambiguous_id ?? 0,
        decode_error: status.decode_error ?? 0,
        asc_events: eventCounts,
      },
    };
  }

  exportCsv(
    signals: Array<{ message: string; signal: string }>,
    options: { start?: number; end?: number; format?: string } = {},
  ): string {
    if (!signals.length) throw new Error("Select at least one signal to export.");
    if (options.format === "parquet") {
      throw new Error("Parquet export is deferred in the static browser PWA because it needs a browser-side Parquet/WASM writer.");
    }
    const rows = this.store.exportRows(signals, options.start, options.end);
    if (options.format === "csv_wide") return wideCsv(rows, signals);
    return longCsv(rows);
  }

  importJob(): ImportProgress {
    return this.lastJob;
  }

  purge(): void {
    this.store.clear();
    this.catalog = new DbcCatalog();
    this.ambiguousIds = {};
    this.resolution = {};
    this.traceName = null;
    this.dbcNames = [];
    this.lastJob = { phase: "idle", progress: 0, cancellable: false };
  }

  private ingestItems(items: AscItem[], decoder: Decoder): void {
    let frameSeq = 0;
    let eventSeq = 0;
    const frames: RawCanFrame[] = [];
    const events: NonDataEvent[] = [];
    for (const item of items.sort((a, b) => timestamp(a) - timestamp(b))) {
      if (item.kind === "frame") {
        const decoded = decoder.decodeFrame({ ...item.frame, seq: frameSeq });
        frames.push(decoded.frame);
        this.store.ingestSamples(decoded.samples);
        frameSeq += 1;
      } else {
        events.push({ ...item.event, seq: eventSeq });
        eventSeq += 1;
      }
    }
    this.store.ingestFrames(frames);
    this.store.ingestEvents(events);
  }

  private conflictPayload(): Array<{ id_hex: string; options: Array<{ database: string; message: string }> }> {
    return Object.entries(this.ambiguousIds).map(([id, choices]) => ({
      id_hex: idHex(Number(id), false),
      options: choices.map((choice) => {
        const [database, message] = choice.split(":");
        return { database: choice, message: message || database };
      }),
    }));
  }

  private hexKeyedAmbiguousIds(): Record<string, string[]> {
    return Object.fromEntries(Object.entries(this.ambiguousIds).map(([id, choices]) => [idHex(Number(id), false), choices]));
  }

  private hexKeyedResolution(): Record<string, string> {
    return Object.fromEntries(Object.entries(this.resolution).map(([id, choice]) => [idHex(Number(id), false), choice]));
  }
}

function timestamp(item: AscItem): number {
  return item.kind === "frame" ? item.frame.timestamp_s : item.event.timestamp_s;
}

function idHex(id: number, extended: boolean): string {
  return extended ? id.toString(16).toUpperCase().padStart(8, "0") : id.toString(16).toUpperCase().padStart(3, "0");
}

function cursorToOffset(cursor: string | undefined): number | undefined {
  if (!cursor) return undefined;
  const parsed = Number(cursor);
  return Number.isFinite(parsed) && parsed >= 0 ? Math.floor(parsed) : undefined;
}

function csvCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function longCsv(rows: Array<{ timestamp_s: number; message: string; signal: string; value: number | string; unit: string | null }>): string {
  const lines = [["timestamp_s", "message", "signal", "value", "unit"].join(",")];
  for (const row of rows) {
    lines.push([row.timestamp_s, row.message, row.signal, row.value, row.unit ?? ""].map(csvCell).join(","));
  }
  return `${lines.join("\n")}\n`;
}

function wideCsv(
  rows: Array<{ timestamp_s: number; message: string; signal: string; value: number | string }>,
  signals: Array<{ message: string; signal: string }>,
): string {
  const labels = signals.map((signal) => `${signal.message}.${signal.signal}`);
  const lines = [["timestamp_s", ...labels].map(csvCell).join(",")];
  let currentTs: number | null = null;
  let current = new Map<string, number | string>();
  const flush = () => {
    if (currentTs === null) return;
    lines.push([currentTs, ...labels.map((label) => current.get(label) ?? "")].map(csvCell).join(","));
  };
  for (const row of rows) {
    if (currentTs !== null && row.timestamp_s !== currentTs) {
      flush();
      current = new Map();
    }
    currentTs = row.timestamp_s;
    current.set(`${row.message}.${row.signal}`, row.value);
  }
  flush();
  return `${lines.join("\n")}\n`;
}
