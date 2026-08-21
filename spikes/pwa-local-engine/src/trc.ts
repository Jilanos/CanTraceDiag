import type { NonDataEvent, RawCanFrame } from "./types.ts";

export type TrcItem = { kind: "frame"; frame: Omit<RawCanFrame, "seq"> }
  | { kind: "event"; event: Omit<NonDataEvent, "seq"> };

const RECORD = /^\s*\d+\)\s*([+-]?\d+(?:\.\d+)?)\s+(.*)$/;
const HEX = /^[0-9a-f]+$/i;

/** Parse the verified PCAN-View text TRC v1.1 grammar. */
export function parseTrcText(text: string): { frames: RawCanFrame[]; events: NonDataEvent[] } {
  const frames: RawCanFrame[] = [];
  const events: NonDataEvent[] = [];
  let frameSeq = 0;
  let eventSeq = 0;
  for (const line of text.split(/\r?\n/)) {
    const item = parseTrcLine(line);
    if (!item) continue;
    if (item.kind === "frame") frames.push({ ...item.frame, seq: frameSeq++ });
    else events.push({ ...item.event, seq: eventSeq++ });
  }
  return { frames, events };
}

function parseTrcLine(line: string): TrcItem | null {
  const stripped = line.trim();
  if (!stripped || stripped.startsWith(";")) return null;
  const match = RECORD.exec(stripped);
  if (!match) return null;
  const timestamp_s = Number(match[1]) / 1000;
  const body = match[2];
  const tokens = body.split(/\s+/).filter(Boolean);
  if (!tokens.length) return event(timestamp_s, "TrcAnomaly", "empty record");
  const kind = tokens[0].toLowerCase();
  if (["warning", "warn", "error"].includes(kind)) return event(timestamp_s, `Trc${kind[0].toUpperCase()}${kind.slice(1)}`, body);
  if (["canfd", "canxl", "lin", "flexray"].includes(kind)) return event(timestamp_s, "TrcUnsupported", body);
  if (kind !== "rx" && kind !== "tx") return event(timestamp_s, "TrcAnomaly", `unsupported record type '${tokens[0]}'`);
  if (["rtr", "remote"].includes(tokens[1]?.toLowerCase())) return event(timestamp_s, "TrcRemoteRequest", body);
  if (tokens.length < 3) return event(timestamp_s, "TrcAnomaly", "truncated classic CAN record");
  const idToken = tokens[1];
  const is_extended_id = /x$/i.test(idToken);
  const idText = is_extended_id ? idToken.slice(0, -1) : idToken;
  if (!HEX.test(idText)) return event(timestamp_s, "TrcAnomaly", `invalid arbitration id '${idToken}'`);
  const arbitration_id = Number.parseInt(idText, 16);
  if (arbitration_id > (is_extended_id ? 0x1fffffff : 0x7ff)) return event(timestamp_s, "TrcAnomaly", `arbitration id out of range '${idToken}'`);
  if (!/^\d+$/.test(tokens[2])) return event(timestamp_s, "TrcAnomaly", `invalid DLC '${tokens[2]}'`);
  const dlc = Number(tokens[2]);
  if (dlc > 8) return event(timestamp_s, "TrcAnomaly", `classic CAN DLC ${dlc} exceeds 8`);
  const payload = tokens.slice(3);
  if (payload.length !== dlc) return event(timestamp_s, "TrcAnomaly", `payload length ${payload.length} does not match DLC ${dlc}`);
  if (payload.some((byte) => !HEX.test(byte) || byte.length > 2)) return event(timestamp_s, "TrcAnomaly", "invalid hexadecimal payload byte");
  const data = Uint8Array.from(payload.map((byte) => Number.parseInt(byte, 16)));
  return { kind: "frame", frame: {
    timestamp_s, channel: "1", arbitration_id, id_hex: idHex(arbitration_id, is_extended_id),
    is_extended_id, dlc, data,
    data_hex: data.length ? Array.from(data, (byte) => byte.toString(16).toUpperCase().padStart(2, "0")).join(" ") : null,
    direction: tokens[0][0].toUpperCase() + tokens[0].slice(1).toLowerCase(), is_remote: false,
    message_name: null, decode_status: "no_database", dbc_source: null,
  } };
}

function event(timestamp_s: number, event_type: string, detail: string): TrcItem {
  return { kind: "event", event: { timestamp_s, channel: null, event_type, detail } };
}

function idHex(id: number, extended: boolean): string {
  return id.toString(16).toUpperCase().padStart(extended ? 8 : 3, "0");
}
