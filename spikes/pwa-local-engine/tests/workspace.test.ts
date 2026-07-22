import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { WorkspaceManager } from "../src/workspace.ts";

class MemoryStorage implements Storage {
  private data = new Map<string, string>();

  get length(): number {
    return this.data.size;
  }

  clear(): void {
    this.data.clear();
  }

  getItem(key: string): string | null {
    return this.data.get(key) ?? null;
  }

  key(index: number): string | null {
    return Array.from(this.data.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.data.delete(key);
  }

  setItem(key: string, value: string): void {
    this.data.set(key, value);
  }
}

class QuotaStorage extends MemoryStorage {
  setItem(): void {
    throw new DOMException("quota", "QuotaExceededError");
  }
}

describe("WorkspaceManager", () => {
  it("saves, lists, exports, imports and deletes workspaces", () => {
    const manager = new WorkspaceManager(new MemoryStorage());
    const saved = manager.save({
      name: "Fixture workspace",
      traceName: "sample.asc",
      traceText: "trace",
      dbcs: [{ name: "sample.dbc", text: "dbc" }],
    });
    assert.equal(manager.list().length, 1);
    assert.equal(manager.read(saved.id)?.traceText, "trace");

    const exported = manager.export(saved.id);
    manager.delete(saved.id);
    assert.equal(manager.list().length, 0);
    const imported = manager.import(exported);
    assert.equal(imported.name, "Fixture workspace");
    assert.equal(manager.list()[0].traceName, "sample.asc");

    manager.purge();
    assert.equal(manager.list().length, 0);
  });

  it("converts quota errors into recoverable messages", () => {
    const manager = new WorkspaceManager(new QuotaStorage());
    assert.throws(
      () => manager.save({
        name: "Large",
        traceName: "large.asc",
        traceText: "x",
        dbcs: [],
      }),
      /quota exceeded/i,
    );
  });
});
