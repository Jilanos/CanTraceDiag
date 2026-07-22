export type WorkspaceDbc = {
  name: string;
  text: string;
};

export type WorkspaceSnapshot = {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  traceName: string;
  traceText: string;
  dbcs: WorkspaceDbc[];
};

const INDEX_KEY = "ctd.pwa.workspaces";
const PREFIX = "ctd.pwa.workspace.";

export class WorkspaceManager {
  private storage: Storage;

  constructor(storage: Storage = localStorage) {
    this.storage = storage;
  }

  list(): Array<Pick<WorkspaceSnapshot, "id" | "name" | "traceName" | "createdAt" | "updatedAt">> {
    return this.readIndex()
      .map((id) => this.read(id))
      .filter((entry): entry is WorkspaceSnapshot => entry !== null)
      .map(({ id, name, traceName, createdAt, updatedAt }) => ({ id, name, traceName, createdAt, updatedAt }))
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  }

  save(input: {
    id?: string;
    name: string;
    traceName: string;
    traceText: string;
    dbcs: WorkspaceDbc[];
  }): WorkspaceSnapshot {
    const now = new Date().toISOString();
    const previous = input.id ? this.read(input.id) : null;
    const snapshot: WorkspaceSnapshot = {
      id: input.id || createId(),
      name: input.name,
      createdAt: previous?.createdAt || now,
      updatedAt: now,
      traceName: input.traceName,
      traceText: input.traceText,
      dbcs: input.dbcs,
    };
    try {
      this.storage.setItem(PREFIX + snapshot.id, JSON.stringify(snapshot));
      this.writeIndex([...new Set([snapshot.id, ...this.readIndex()])]);
    } catch (error) {
      this.storage.removeItem(PREFIX + snapshot.id);
      throw new Error(storageErrorMessage(error));
    }
    return snapshot;
  }

  read(id: string): WorkspaceSnapshot | null {
    const raw = this.storage.getItem(PREFIX + id);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as WorkspaceSnapshot;
    } catch {
      return null;
    }
  }

  delete(id: string): void {
    this.storage.removeItem(PREFIX + id);
    this.writeIndex(this.readIndex().filter((entry) => entry !== id));
  }

  purge(): void {
    for (const id of this.readIndex()) this.storage.removeItem(PREFIX + id);
    this.storage.removeItem(INDEX_KEY);
  }

  export(id: string): string {
    const snapshot = this.read(id);
    if (!snapshot) throw new Error("Workspace not found.");
    return JSON.stringify({ schema: "cantracediag-pwa-workspace-v1", workspace: snapshot }, null, 2);
  }

  import(text: string): WorkspaceSnapshot {
    const parsed = JSON.parse(text);
    const source = parsed.workspace ?? parsed;
    if (!source.traceText || !Array.isArray(source.dbcs)) {
      throw new Error("Invalid workspace export.");
    }
    return this.save({
      name: source.name || "Imported workspace",
      traceName: source.traceName || "imported.asc",
      traceText: source.traceText,
      dbcs: source.dbcs,
    });
  }

  estimateQuota(): Promise<StorageEstimate | null> {
    return navigator.storage?.estimate ? navigator.storage.estimate() : Promise.resolve(null);
  }

  private readIndex(): string[] {
    try {
      const parsed = JSON.parse(this.storage.getItem(INDEX_KEY) || "[]");
      return Array.isArray(parsed) ? parsed.filter((id) => typeof id === "string") : [];
    } catch {
      return [];
    }
  }

  private writeIndex(ids: string[]): void {
    this.storage.setItem(INDEX_KEY, JSON.stringify(ids));
  }
}

function createId(): string {
  return `ws_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function storageErrorMessage(error: unknown): string {
  if (error instanceof DOMException && error.name === "QuotaExceededError") {
    return "Local storage quota exceeded. Delete old workspaces or export them before retrying.";
  }
  if (error instanceof Error) return error.message;
  return String(error);
}
