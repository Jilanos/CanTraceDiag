import type { DecodedSignalSample, MessageDefinition, RawCanFrame } from "./types.ts";

export class Decoder {
  private messages: Map<number, MessageDefinition> | null;
  private ambiguousIds: Set<number>;

  constructor(messages: Map<number, MessageDefinition> | null, ambiguousIds = new Set<number>()) {
    this.messages = messages;
    this.ambiguousIds = ambiguousIds;
  }

  describeFrame(frame: RawCanFrame): RawCanFrame {
    if (!this.messages) return { ...frame, decode_status: "no_database", message_name: null, dbc_source: null };
    if (this.ambiguousIds.has(frame.arbitration_id) && !this.messages.has(frame.arbitration_id)) {
      return { ...frame, decode_status: "ambiguous_id", message_name: null, dbc_source: null };
    }
    const message = this.messages.get(frame.arbitration_id);
    if (!message) return { ...frame, decode_status: "unknown_id", message_name: null, dbc_source: null };
    if (frame.data.length < message.dlc && !frame.is_remote) {
      return { ...frame, decode_status: "decode_error", message_name: message.name, dbc_source: message.database };
    }
    return { ...frame, decode_status: "ok", message_name: message.name, dbc_source: message.database };
  }

  decodeFrame(frame: RawCanFrame): { frame: RawCanFrame; samples: DecodedSignalSample[] } {
    const updated = this.describeFrame(frame);
    if (updated.decode_status !== "ok" || !this.messages) return { frame: updated, samples: [] };
    const message = this.messages.get(frame.arbitration_id);
    if (!message) return { frame: updated, samples: [] };
    const samples: DecodedSignalSample[] = [];
    try {
      const muxSignal = message.signals.find((signal) => signal.is_multiplexer);
      const muxValue = muxSignal
        ? extractSignal(frame.data, muxSignal.start_bit, muxSignal.bit_length, muxSignal.byte_order)
        : null;
      for (const signal of message.signals) {
        if (signal.multiplex_value !== null && signal.multiplex_value !== muxValue) continue;
        const raw = extractSignal(frame.data, signal.start_bit, signal.bit_length, signal.byte_order);
        const signed = signal.signed ? signExtend(raw, signal.bit_length) : raw;
        samples.push({
          timestamp_s: frame.timestamp_s,
          channel: frame.channel,
          arbitration_id: frame.arbitration_id,
          message_name: message.name,
          signal_name: signal.signal_name,
          value: signed * signal.factor + signal.offset,
          unit: signal.unit,
        });
      }
      return { frame: updated, samples };
    } catch {
      return {
        frame: { ...updated, decode_status: "decode_error" },
        samples: [],
      };
    }
  }

  decodeSignal(frame: RawCanFrame, messageName: string, signalName: string): DecodedSignalSample | null {
    const decoded = this.decodeFrame(frame);
    return decoded.samples.find((sample) => (
      sample.message_name === messageName && sample.signal_name === signalName
    )) ?? null;
  }
}

export function extractSignal(
  data: Uint8Array,
  startBit: number,
  bitLength: number,
  byteOrder: "little" | "big",
): number {
  if (bitLength <= 0 || bitLength > 52) throw new Error("Unsupported signal length");
  if (byteOrder === "big") return extractBigEndianSignal(data, startBit, bitLength);
  let raw = 0;
  for (let i = 0; i < bitLength; i += 1) {
    const bitIndex = startBit + i;
    const byteIndex = Math.floor(bitIndex / 8);
    if (byteIndex >= data.length) throw new Error("Signal exceeds payload");
    const bitInByte = bitIndex % 8;
    const bit = (data[byteIndex] >> bitInByte) & 1;
    raw += bit * 2 ** i;
  }
  return raw;
}

function extractBigEndianSignal(data: Uint8Array, startBit: number, bitLength: number): number {
  let raw = 0;
  let bitIndex = startBit;
  for (let i = 0; i < bitLength; i += 1) {
    const byteIndex = Math.floor(bitIndex / 8);
    if (byteIndex < 0 || byteIndex >= data.length) throw new Error("Signal exceeds payload");
    const bitInByte = bitIndex % 8;
    const bit = (data[byteIndex] >> bitInByte) & 1;
    raw = raw * 2 + bit;
    bitIndex = bitInByte === 0 ? bitIndex + 15 : bitIndex - 1;
  }
  return raw;
}

function signExtend(value: number, bits: number): number {
  const sign = 2 ** (bits - 1);
  return value & sign ? value - 2 ** bits : value;
}
