import type { DecodedSignalSample, NonDataEvent, RawCanFrame, TraceRow } from "./types.ts";

export class LocalTraceStore {
  private frameSeq: number[] = [];
  private frameTs: number[] = [];
  private frameChannel: string[] = [];
  private frameId: number[] = [];
  private frameIdHex: string[] = [];
  private frameExt: boolean[] = [];
  private frameDlc: number[] = [];
  private frameData: Uint8Array[] = [];
  private frameDataHex: (string | null)[] = [];
  private frameDirection: string[] = [];
  private frameRemote: boolean[] = [];
  private frameMessage: (string | null)[] = [];
  private frameStatus: RawCanFrame["decode_status"][] = [];
  private frameDbc: (string | null)[] = [];
  private events: NonDataEvent[] = [];
  private samples: DecodedSignalSample[] = [];

  clear(): void {
    this.frameSeq = [];
    this.frameTs = [];
    this.frameChannel = [];
    this.frameId = [];
    this.frameIdHex = [];
    this.frameExt = [];
    this.frameDlc = [];
    this.frameData = [];
    this.frameDataHex = [];
    this.frameDirection = [];
    this.frameRemote = [];
    this.frameMessage = [];
    this.frameStatus = [];
    this.frameDbc = [];
    this.events = [];
    this.samples = [];
  }

  ingestFrames(frames: RawCanFrame[]): void {
    for (const frame of frames) {
      this.frameSeq.push(frame.seq);
      this.frameTs.push(frame.timestamp_s);
      this.frameChannel.push(frame.channel);
      this.frameId.push(frame.arbitration_id);
      this.frameIdHex.push(frame.id_hex);
      this.frameExt.push(frame.is_extended_id);
      this.frameDlc.push(frame.dlc);
      this.frameData.push(frame.data);
      this.frameDataHex.push(frame.data_hex);
      this.frameDirection.push(frame.direction);
      this.frameRemote.push(frame.is_remote);
      this.frameMessage.push(frame.message_name);
      this.frameStatus.push(frame.decode_status);
      this.frameDbc.push(frame.dbc_source);
    }
  }

  ingestEvents(events: NonDataEvent[]): void {
    this.events.push(...events);
  }

  ingestSamples(samples: DecodedSignalSample[]): void {
    this.samples.push(...samples);
  }

  summary(): Record<string, number | null | Record<string, number> | string[]> {
    const bounds = this.timeBounds();
    return {
      frames: this.frameTs.length,
      events: this.events.length,
      decoded_frames: this.frameStatus.filter((status) => status === "ok").length,
      unique_ids: new Set(this.frameId).size,
      start_s: bounds.start_s,
      end_s: bounds.end_s,
      decode_status: this.decodeStatusCounts(),
      event_types: this.eventTypes(),
    };
  }

  eventTypes(): string[] {
    return [...new Set(this.events.map((event) => event.event_type))].sort();
  }

  timeBounds(): { start_s: number | null; end_s: number | null } {
    const all = [...this.frameTs, ...this.events.map((event) => event.timestamp_s)];
    if (!all.length) return { start_s: null, end_s: null };
    return { start_s: Math.min(...all), end_s: Math.max(...all) };
  }

  frameAt(timestamp_s: number, arbitration_id: number): RawCanFrame | null {
    const idx = this.frameTs.findIndex((ts, i) => ts === timestamp_s && this.frameId[i] === arbitration_id);
    return idx >= 0 ? this.frame(idx) : null;
  }

  nearestFrameForSignal(arbitration_id: number, at: number): RawCanFrame | null {
    let best: { idx: number; dist: number } | null = null;
    for (let i = 0; i < this.frameTs.length; i += 1) {
      if (this.frameId[i] !== arbitration_id) continue;
      const dist = Math.abs(this.frameTs[i] - at);
      if (!best || dist < best.dist) best = { idx: i, dist };
    }
    return best ? this.frame(best.idx) : null;
  }

  framesForSignal(arbitration_id: number, start?: number, end?: number): RawCanFrame[] {
    const out: RawCanFrame[] = [];
    for (let i = 0; i < this.frameTs.length; i += 1) {
      if (this.frameId[i] !== arbitration_id) continue;
      if (start !== undefined && this.frameTs[i] < start) continue;
      if (end !== undefined && this.frameTs[i] > end) continue;
      out.push(this.frame(i));
    }
    return out;
  }

  presentSignalKeys(): Set<string> {
    return new Set(this.samples.map((sample) => `${sample.message_name}\u0000${sample.signal_name}\u0000${sample.arbitration_id}`));
  }

  presentArbitrationIds(): Set<number> {
    return new Set(this.samples.map((sample) => sample.arbitration_id));
  }

  signalSeries(
    message: string,
    signal: string,
    options: { start?: number; end?: number; maxPoints?: number } = {},
  ): { t: number[]; v: (number | string)[]; unit: string | null; downsampled: boolean } {
    let rows = this.samples
      .filter((sample) => sample.message_name === message && sample.signal_name === signal)
      .sort((a, b) => a.timestamp_s - b.timestamp_s);
    if (options.start !== undefined) rows = rows.filter((sample) => sample.timestamp_s >= options.start!);
    if (options.end !== undefined) rows = rows.filter((sample) => sample.timestamp_s <= options.end!);
    const numericRows = rows.filter((sample) => typeof sample.value === "number" && Number.isFinite(sample.value));
    if (numericRows.length) rows = numericRows;
    const maxPoints = Math.max(2, options.maxPoints ?? 4_000);
    const downsampled = rows.length > maxPoints;
    if (downsampled) {
      rows = minMaxDownsample(rows, maxPoints);
    }
    return {
      t: rows.map((sample) => sample.timestamp_s),
      v: rows.map((sample) => sample.value),
      unit: rows[0]?.unit ?? null,
      downsampled,
    };
  }

  nearestSample(message: string, signal: string, at: number): { timestamp_s: number; value: number | string; unit: string | null } | null {
    const rows = this.samples.filter((sample) => sample.message_name === message && sample.signal_name === signal);
    let best: DecodedSignalSample | null = null;
    for (const sample of rows) {
      if (!best || Math.abs(sample.timestamp_s - at) < Math.abs(best.timestamp_s - at)) best = sample;
    }
    return best ? { timestamp_s: best.timestamp_s, value: best.value, unit: best.unit } : null;
  }

  frameSignals(timestamp_s: number, arbitration_id: number): DecodedSignalSample[] {
    return this.samples.filter((sample) => sample.timestamp_s === timestamp_s && sample.arbitration_id === arbitration_id);
  }

  signalStats(message: string, signal: string, start?: number, end?: number): Record<string, unknown> {
    const rows = this.signalSamples(message, signal, start, end);
    const unit = rows.find((sample) => sample.unit)?.unit ?? null;
    const base = {
      message,
      signal,
      message_name: message,
      signal_name: signal,
      unit,
      total: rows.length,
      count: rows.length,
    };
    if (!rows.length) return { ...base, kind: "empty", count: 0 };
    const numeric = rows
      .map((sample) => sample.value)
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
    if (numeric.length) {
      const sum = numeric.reduce((acc, value) => acc + value, 0);
      const mean = sum / numeric.length;
      const variance = numeric.length > 1
        ? numeric.reduce((acc, value) => acc + (value - mean) ** 2, 0) / (numeric.length - 1)
        : null;
      const squareMean = numeric.reduce((acc, value) => acc + value * value, 0) / numeric.length;
      return {
        ...base,
        kind: "numeric",
        count: numeric.length,
        min: Math.min(...numeric),
        max: Math.max(...numeric),
        mean,
        std: variance === null ? null : Math.sqrt(variance),
        rms: Math.sqrt(squareMean),
      };
    }
    const counts: Record<string, number> = {};
    for (const sample of rows) {
      const key = String(sample.value);
      counts[key] = (counts[key] ?? 0) + 1;
    }
    const distribution = Object.entries(counts)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([value, count]) => ({ value, count }));
    return { ...base, kind: "text", count: rows.length, distribution };
  }

  exportRows(
    pairs: Array<{ message: string; signal: string }>,
    start?: number,
    end?: number,
  ): Array<{ timestamp_s: number; message: string; signal: string; value: number | string; unit: string | null }> {
    const wanted = new Set(pairs.map((pair) => `${pair.message}\u0000${pair.signal}`));
    return this.samples
      .filter((sample) => wanted.has(`${sample.message_name}\u0000${sample.signal_name}`))
      .filter((sample) => start === undefined || sample.timestamp_s >= start)
      .filter((sample) => end === undefined || sample.timestamp_s <= end)
      .sort((a, b) => a.timestamp_s - b.timestamp_s || a.message_name.localeCompare(b.message_name) || a.signal_name.localeCompare(b.signal_name))
      .map((sample) => ({
        timestamp_s: sample.timestamp_s,
        message: sample.message_name,
        signal: sample.signal_name,
        value: sample.value,
        unit: sample.unit,
      }));
  }

  dbcsUsed(): Array<{ source: string; frames: number }> {
    const counts = new Map<string, number>();
    for (const source of this.frameDbc) {
      if (!source) continue;
      counts.set(source, (counts.get(source) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([source, frames]) => ({ source, frames }));
  }

  traceRows(options: {
    offset?: number;
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
  } = {}): { offset: number; limit: number; total: number; rows: TraceRow[] } {
    const includeFrames = options.includeFrames ?? true;
    const includeEvents = options.includeEvents ?? true;
    const rows: TraceRow[] = [];
    const signalIds = options.signal
      ? new Set(this.samples.filter((s) => s.signal_name.toLowerCase().includes(options.signal!.toLowerCase())).map((s) => s.arbitration_id))
      : null;
    const wantedId = options.idHex ? normalizeHex(options.idHex) : null;
    const wantedMessage = options.message?.toLowerCase();
    const wantedDirection = options.direction?.toLowerCase();
    const wantedStatus = options.decodeStatus?.toLowerCase();
    const wantedEvent = options.eventType?.toLowerCase();
    const hasFrameOnlyFilter = Boolean(wantedId || wantedMessage || wantedDirection || wantedStatus);
    if (includeFrames && !wantedEvent) {
      for (let i = 0; i < this.frameTs.length; i += 1) {
        if (options.start !== undefined && this.frameTs[i] < options.start) continue;
        if (options.end !== undefined && this.frameTs[i] > options.end) continue;
        if (signalIds && !signalIds.has(this.frameId[i])) continue;
        if (wantedId && !normalizeHex(this.frameIdHex[i]).includes(wantedId)) continue;
        if (wantedMessage && !(this.frameMessage[i] ?? "").toLowerCase().includes(wantedMessage)) continue;
        if (wantedDirection && this.frameDirection[i].toLowerCase() !== wantedDirection) continue;
        if (wantedStatus && this.frameStatus[i].toLowerCase() !== wantedStatus) continue;
        rows.push({
          timestamp_s: this.frameTs[i],
          kind: "frame",
          channel: this.frameChannel[i],
          id_hex: this.frameIdHex[i],
          name: this.frameMessage[i],
          direction: this.frameDirection[i],
          dlc: this.frameDlc[i],
          data_hex: this.frameDataHex[i],
          decode_status: this.frameStatus[i],
          dbc_source: this.frameDbc[i],
          event_type: null,
          detail: null,
        });
      }
    }
    if (includeEvents && !signalIds && !hasFrameOnlyFilter) {
      for (const event of this.events) {
        if (options.start !== undefined && event.timestamp_s < options.start) continue;
        if (options.end !== undefined && event.timestamp_s > options.end) continue;
        if (wantedEvent && event.event_type.toLowerCase() !== wantedEvent) continue;
        rows.push({
          timestamp_s: event.timestamp_s,
          kind: "event",
          channel: event.channel,
          id_hex: null,
          name: null,
          direction: null,
          dlc: null,
          data_hex: null,
          decode_status: null,
          dbc_source: null,
          event_type: event.event_type,
          detail: event.detail,
        });
      }
    }
    rows.sort((a, b) => a.timestamp_s - b.timestamp_s);
    const offset = options.offset ?? 0;
    const limit = options.limit ?? 200;
    return { offset, limit, total: rows.length, rows: rows.slice(offset, offset + limit) };
  }

  private signalSamples(message: string, signal: string, start?: number, end?: number): DecodedSignalSample[] {
    return this.samples
      .filter((sample) => sample.message_name === message && sample.signal_name === signal)
      .filter((sample) => start === undefined || sample.timestamp_s >= start)
      .filter((sample) => end === undefined || sample.timestamp_s <= end)
      .sort((a, b) => a.timestamp_s - b.timestamp_s);
  }

  locateRow(at: number, options: Parameters<LocalTraceStore["traceRows"]>[0] = {}): { index: number | null; offset: number; timestamp_s: number | null } {
    const rows = this.traceRows({ ...options, offset: 0, limit: Number.MAX_SAFE_INTEGER }).rows;
    if (!rows.length) return { index: null, offset: 0, timestamp_s: null };
    let index = 0;
    for (let i = 1; i < rows.length; i += 1) {
      const current = Math.abs(rows[i].timestamp_s - at);
      const best = Math.abs(rows[index].timestamp_s - at);
      if (current < best) index = i;
    }
    return { index, offset: index, timestamp_s: rows[index].timestamp_s };
  }

  private frame(i: number): RawCanFrame {
    return {
      seq: this.frameSeq[i],
      timestamp_s: this.frameTs[i],
      channel: this.frameChannel[i],
      arbitration_id: this.frameId[i],
      id_hex: this.frameIdHex[i],
      is_extended_id: this.frameExt[i],
      dlc: this.frameDlc[i],
      data: this.frameData[i],
      data_hex: this.frameDataHex[i],
      direction: this.frameDirection[i],
      is_remote: this.frameRemote[i],
      message_name: this.frameMessage[i],
      decode_status: this.frameStatus[i],
      dbc_source: this.frameDbc[i],
    };
  }

  private decodeStatusCounts(): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const status of this.frameStatus) counts[status] = (counts[status] ?? 0) + 1;
    return counts;
  }
}

function normalizeHex(value: string): string {
  return value.trim().replace(/^0x/i, "").replace(/^0+([0-9a-f])/i, "$1").toUpperCase();
}

function minMaxDownsample(rows: DecodedSignalSample[], maxPoints: number): DecodedSignalSample[] {
  const bucketCount = Math.max(1, Math.floor(maxPoints / 2));
  const bucketSize = Math.ceil(rows.length / bucketCount);
  const out: DecodedSignalSample[] = [];
  for (let start = 0; start < rows.length; start += bucketSize) {
    const bucket = rows.slice(start, start + bucketSize);
    let min = bucket[0];
    let max = bucket[0];
    for (const sample of bucket) {
      if ((sample.value as number) < (min.value as number)) min = sample;
      if ((sample.value as number) > (max.value as number)) max = sample;
    }
    const pair = min.timestamp_s <= max.timestamp_s ? [min, max] : [max, min];
    for (const sample of pair) {
      if (!out.length || out[out.length - 1] !== sample) out.push(sample);
    }
  }
  return out.slice(0, maxPoints).sort((a, b) => a.timestamp_s - b.timestamp_s);
}
