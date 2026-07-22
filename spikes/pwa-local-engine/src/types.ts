export type DecodeStatus = "ok" | "unknown_id" | "decode_error" | "no_database" | "ambiguous_id";

export type RawCanFrame = {
  seq: number;
  timestamp_s: number;
  channel: string;
  arbitration_id: number;
  id_hex: string;
  is_extended_id: boolean;
  dlc: number;
  data: Uint8Array;
  data_hex: string | null;
  direction: string;
  is_remote: boolean;
  message_name: string | null;
  decode_status: DecodeStatus;
  dbc_source: string | null;
};

export type NonDataEvent = {
  seq: number;
  timestamp_s: number;
  channel: string | null;
  event_type: string;
  detail: string | null;
};

export type SignalDefinition = {
  message_name: string;
  signal_name: string;
  arbitration_id: number;
  is_extended_id: boolean;
  start_bit: number;
  bit_length: number;
  byte_order: "little" | "big";
  signed: boolean;
  factor: number;
  offset: number;
  minimum: number | null;
  maximum: number | null;
  unit: string | null;
  databases: string[];
  is_multiplexer: boolean;
  multiplex_value: number | null;
};

export type MessageDefinition = {
  database: string;
  name: string;
  arbitration_id: number;
  is_extended_id: boolean;
  dlc: number;
  signals: SignalDefinition[];
};

export type DecodedSignalSample = {
  timestamp_s: number;
  channel: string;
  arbitration_id: number;
  message_name: string;
  signal_name: string;
  value: number | string;
  unit: string | null;
};

export type ImportProgress = {
  phase: string;
  progress: number;
  detail?: string;
  cancellable: boolean;
};

export type TraceRow = {
  timestamp_s: number;
  kind: "frame" | "event";
  channel: string | null;
  id_hex: string | null;
  name: string | null;
  direction: string | null;
  dlc: number | null;
  data_hex: string | null;
  decode_status: DecodeStatus | null;
  dbc_source: string | null;
  event_type: string | null;
  detail: string | null;
};
