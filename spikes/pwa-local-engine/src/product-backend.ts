import { LocalPwaBackend } from "./local-backend.ts";

type LocalDbc = {
  digest: string;
  name: string;
  text: string;
  last_used: string;
};

type PendingImport = {
  traceText: string;
  traceName: string;
  dbcs: Array<{ name: string; text: string }>;
};

const LIBRARY_KEY = "ctd.pwa.dbc-library.v1";

export function createLocalProductBackend(): {
  api: (path: string, opts?: RequestInit) => Promise<unknown>;
  uploadWithProgress: (
    formData: FormData,
    onProgress: (fraction: number) => void,
    onUploadComplete?: () => void,
  ) => Promise<unknown>;
  __backend: LocalPwaBackend;
} {
  const backend = new LocalPwaBackend();
  let pending: PendingImport | null = null;
  let lastSessionDbcs: string[] = [];

  async function api(path: string, opts: RequestInit = {}): Promise<unknown> {
    const url = new URL(path, window.location.href);
    if (url.pathname === "/api/status") return backend.status();
    if (url.pathname === "/api/signals") return backend.signals();
    if (url.pathname === "/api/import-job") return backend.importJob();
    if (url.pathname === "/api/import-cancel") return { cancelled: false, reason: "Local imports finish synchronously in this MVP adapter." };
    if (url.pathname === "/api/dbc-library") return { dbcs: readLibrary().map(({ text, ...entry }) => entry), last_session: lastSessionDbcs };
    if (url.pathname === "/api/report") return backend.report();
    if (url.pathname === "/api/workspace-purge") {
      backend.purge();
      pending = null;
      lastSessionDbcs = [];
      localStorage.removeItem(LIBRARY_KEY);
      return { purged: true };
    }
    if (url.pathname === "/api/resolve") {
      if (!pending) throw new Error("No load is awaiting DBC conflict resolution.");
      const body = JSON.parse(String(opts.body || "{}"));
      const resolution = parseResolution(body.resolution || {});
      const result = await backend.importText(pending.traceText, pending.dbcs, resolution);
      backend.traceName = pending.traceName;
      if (!result.needs_resolution) pending = null;
      return result;
    }
    if (url.pathname === "/api/series") {
      return backend.series(required(url, "message"), required(url, "signal"), {
        start: numberParam(url, "start"),
        end: numberParam(url, "end"),
        maxPoints: numberParam(url, "max_points"),
      });
    }
    if (url.pathname === "/api/cursor") {
      const result = backend.cursor(required(url, "message"), required(url, "signal"), Number(required(url, "at")));
      if (!result) throw new Error("No sample for that signal.");
      return result;
    }
    if (url.pathname === "/api/cursors") {
      const body = JSON.parse(String(opts.body || "{}"));
      return backend.cursors(body.signals || [], body.a, body.b);
    }
    if (url.pathname === "/api/signal-stats") {
      return backend.signalStats(
        required(url, "message"),
        required(url, "signal"),
        numberParam(url, "start"),
        numberParam(url, "end"),
      );
    }
    if (url.pathname === "/api/trace") return backend.trace(traceParams(url));
    if (url.pathname === "/api/trace-locate") return backend.traceLocate(Number(required(url, "at")), traceParams(url));
    if (url.pathname === "/api/frame-signals") return backend.frameSignals(Number(required(url, "at")), Number(required(url, "id")));
    throw new Error(`Unsupported local PWA endpoint: ${url.pathname}`);
  }

  async function uploadWithProgress(
    formData: FormData,
    onProgress: (fraction: number) => void,
    onUploadComplete?: () => void,
  ): Promise<unknown> {
    onProgress(0.05);
    const trace = formData.get("trace");
    if (!(trace instanceof File)) throw new Error("Trace file must be selected.");
    const freshDbcs = formData.getAll("dbcs").filter((entry): entry is File => entry instanceof File);
    const libraryDigests = formData.getAll("library").map(String);
    const library = readLibrary();
    const libraryDbcs = library
      .filter((entry) => libraryDigests.includes(entry.digest))
      .map((entry) => ({ name: entry.name, text: entry.text }));
    const uploadedDbcs = await Promise.all(freshDbcs.map(async (file) => ({ name: file.name, text: await file.text() })));
    const dbcs = [...uploadedDbcs, ...libraryDbcs];
    if (!dbcs.length) throw new Error("Choose at least one DBC file or local library entry.");
    onProgress(0.35);
    const traceText = await trace.text();
    onProgress(0.75);
    const result = await backend.importText(traceText, dbcs);
    backend.traceName = trace.name;
    lastSessionDbcs = dbcs.map((dbc) => dbc.name);
    try {
      saveDbcs(uploadedDbcs);
    } catch (error) {
      throw new Error(storageErrorMessage(error));
    }
    if (result && typeof result === "object" && "needs_resolution" in result && result.needs_resolution) {
      pending = { traceText, traceName: trace.name, dbcs };
    } else {
      pending = null;
    }
    onProgress(0.99);
    return result;
  }

  return { api, uploadWithProgress, __backend: backend };
}

export function exportLocalProductBlob(payload: {
  signals: Array<{ message: string; signal: string }>;
  scope: string;
  format: string;
  start?: number;
  end?: number;
}, backendApi: ReturnType<typeof createLocalProductBackend>): Blob {
  const backend = backendApi.__backend;
  if (!backend) throw new Error("Local export backend unavailable.");
  const csv = backend.exportCsv(payload.signals, {
    start: payload.scope === "full" ? undefined : payload.start,
    end: payload.scope === "full" ? undefined : payload.end,
    format: payload.format,
  });
  return new Blob([csv], { type: "text/csv;charset=utf-8" });
}

function traceParams(url: URL): Parameters<LocalPwaBackend["trace"]>[0] {
  return {
    offset: numberParam(url, "offset"),
    cursor: textParam(url, "cursor"),
    limit: numberParam(url, "limit"),
    start: numberParam(url, "start"),
    end: numberParam(url, "end"),
    includeFrames: boolParam(url, "frames", true),
    includeEvents: boolParam(url, "events", true),
    idHex: textParam(url, "id"),
    message: textParam(url, "message"),
    direction: textParam(url, "direction"),
    decodeStatus: textParam(url, "status"),
    eventType: textParam(url, "event_type"),
    signal: textParam(url, "signal"),
  };
}

function required(url: URL, key: string): string {
  const value = url.searchParams.get(key);
  if (value === null || value === "") throw new Error(`Missing parameter: ${key}`);
  return value;
}

function textParam(url: URL, key: string): string | undefined {
  return url.searchParams.get(key) || undefined;
}

function numberParam(url: URL, key: string): number | undefined {
  const value = url.searchParams.get(key);
  if (value === null || value === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function boolParam(url: URL, key: string, fallback: boolean): boolean {
  const value = url.searchParams.get(key);
  if (value === null || value === "") return fallback;
  return value === "true" || value === "1";
}

function parseResolution(input: Record<string, string>): Record<number, string> {
  return Object.fromEntries(Object.entries(input).map(([id, choice]) => [Number.parseInt(id, 16), choice]));
}

function readLibrary(): LocalDbc[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(LIBRARY_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.filter(isLocalDbc) : [];
  } catch {
    return [];
  }
}

function saveDbcs(dbcs: Array<{ name: string; text: string }>): void {
  const now = new Date().toISOString();
  const current = readLibrary();
  const byDigest = new Map(current.map((entry) => [entry.digest, entry]));
  for (const dbc of dbcs) {
    const digest = digestText(dbc.text);
    byDigest.set(digest, { digest, name: dbc.name, text: dbc.text, last_used: now });
  }
  localStorage.setItem(LIBRARY_KEY, JSON.stringify([...byDigest.values()].slice(-20)));
}

function storageErrorMessage(error: unknown): string {
  if (error instanceof DOMException && error.name === "QuotaExceededError") {
    return "Local DBC library quota exceeded. Purge saved DBCs or use fewer/lighter DBC files, then retry.";
  }
  if (error instanceof Error) return error.message;
  return "Local DBC library storage failed.";
}

function digestText(text: string): string {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function isLocalDbc(value: unknown): value is LocalDbc {
  if (!value || typeof value !== "object") return false;
  const entry = value as Record<string, unknown>;
  return typeof entry.digest === "string"
    && typeof entry.name === "string"
    && typeof entry.text === "string"
    && typeof entry.last_used === "string";
}
