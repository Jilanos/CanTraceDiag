import type { MessageDefinition, SignalDefinition } from "./types.ts";

const BO = /^BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+(\w+)/;
const SG = /^\s*SG_\s+(\w+)(?:\s+(M|m\d+))?\s*:\s*(\d+)\|(\d+)@([01])([+-])\s+\(([-\d.eE]+),([-\d.eE]+)\)\s+\[([-\d.eE]+)\|([-\d.eE]+)\]\s+"([^"]*)"/;
const EXTENDED_ID_FLAG = 0x80000000;
const EXTENDED_ID_MASK = 0x7fffffff;

export class DbcCatalog {
  messages: MessageDefinition[] = [];

  loadText(text: string, name = "uploaded.dbc"): void {
    let current: MessageDefinition | null = null;
    for (const line of text.split(/\r?\n/)) {
      const bo = BO.exec(line);
      if (bo) {
        const rawId = Number(bo[1]);
        const isExtended = (rawId & EXTENDED_ID_FLAG) !== 0;
        current = {
          database: name,
          arbitration_id: isExtended ? rawId & EXTENDED_ID_MASK : rawId,
          is_extended_id: isExtended,
          name: bo[2],
          dlc: Number(bo[3]),
          signals: [],
        };
        this.messages.push(current);
        continue;
      }
      const sg = SG.exec(line);
      if (sg && current) {
        const muxToken = sg[2] ?? "";
        const signal: SignalDefinition = {
          message_name: current.name,
          signal_name: sg[1],
          arbitration_id: current.arbitration_id,
          is_extended_id: current.is_extended_id,
          start_bit: Number(sg[3]),
          bit_length: Number(sg[4]),
          byte_order: sg[5] === "1" ? "little" : "big",
          signed: sg[6] === "-",
          factor: Number(sg[7]),
          offset: Number(sg[8]),
          minimum: Number(sg[9]),
          maximum: Number(sg[10]),
          unit: sg[11] || null,
          databases: [name],
          is_multiplexer: muxToken === "M",
          multiplex_value: muxToken.startsWith("m") ? Number(muxToken.slice(1)) : null,
        };
        current.signals.push(signal);
      }
    }
  }

  signals(): SignalDefinition[] {
    return this.messages.flatMap((message) => message.signals);
  }

  messageIndex(resolution: Record<number, string> = {}): Map<number, MessageDefinition> {
    const index = new Map<number, MessageDefinition>();
    const byId = groupById(this.messages);
    for (const [id, messages] of byId) {
      if (messages.length === 1) {
        index.set(id, messages[0]);
        continue;
      }
      const chosen = resolution[id];
      if (chosen) {
        const match = messages.find((message) => choiceName(message) === chosen || message.database === chosen);
        if (match) index.set(id, match);
        continue;
      }
      if (new Set(messages.map(messageSignature)).size === 1) {
        index.set(id, messages[0]);
      }
    }
    return index;
  }

  findAmbiguousIds(): Record<number, string[]> {
    const ambiguous: Record<number, string[]> = {};
    for (const [id, messages] of groupById(this.messages)) {
      const signatures = new Set(messages.map(messageSignature));
      if (signatures.size > 1) ambiguous[id] = messages.map(choiceName);
    }
    return ambiguous;
  }
}

function groupById(messages: MessageDefinition[]): Map<number, MessageDefinition[]> {
  const out = new Map<number, MessageDefinition[]>();
  for (const message of messages) {
    const group = out.get(message.arbitration_id) ?? [];
    group.push(message);
    out.set(message.arbitration_id, group);
  }
  return out;
}

function choiceName(message: MessageDefinition): string {
  return `${message.database}:${message.name}`;
}

function messageSignature(message: MessageDefinition): string {
  return JSON.stringify({
    name: message.name,
    dlc: message.dlc,
    signals: message.signals.map((signal) => ({
      name: signal.signal_name,
      start: signal.start_bit,
      bits: signal.bit_length,
      order: signal.byte_order,
      signed: signal.signed,
      factor: signal.factor,
      offset: signal.offset,
      unit: signal.unit,
      mux: signal.is_multiplexer ? "M" : signal.multiplex_value,
    })),
  });
}
