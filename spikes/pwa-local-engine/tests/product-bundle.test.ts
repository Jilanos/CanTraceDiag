import { describe, it, before } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

import {
  availableModules,
  bundledModules,
  resolveProductModules,
  shellModules,
} from "../product-modules.mjs";

const siteDir = path.resolve("spikes/pwa-local-engine/site");
const bundlePath = path.join(siteDir, "browser", "product-app.mjs");
const indexPath = path.join(siteDir, "index.html");

describe("Static PWA bundle parity", () => {
  before(() => {
    // The delivered artifact is what the audit found broken, so assert against
    // a freshly generated site rather than whatever is left in the worktree.
    execFileSync(process.execPath, ["spikes/pwa-local-engine/build-browser.mjs"], { stdio: "pipe" });
  });

  it("declares every product module that exists on disk", () => {
    assert.deepEqual(resolveProductModules().slice().sort(), availableModules());
  });

  it("bundles the shell modules in the shell's execution order", () => {
    const bundle = fs.readFileSync(bundlePath, "utf8");
    assert.deepEqual(bundledModules(bundle), shellModules());
  });

  it("keeps the fullscreen controller in the delivered bundle", () => {
    const bundle = fs.readFileSync(bundlePath, "utf8");
    assert.ok(shellModules().includes("fullscreen.js"), "shell must declare fullscreen.js");
    // Assert with `ok` rather than `match`: a failed `match` prints the whole
    // generated bundle, which drowns the actual signal.
    assert.ok(bundle.includes("function toggleFullscreen("), "bundle is missing toggleFullscreen()");
    assert.ok(bundle.includes('$("fullscreenBtn")'), "bundle never wires #fullscreenBtn");
  });

  it("does not leave any shell module out of the generated bundle", () => {
    const bundle = fs.readFileSync(bundlePath, "utf8");
    for (const entry of shellModules()) {
      const source = fs.readFileSync(path.resolve("src/cantracediag/web/js", entry), "utf8");
      const marker = source.split("\n").find((line) => /^(function|async function|const|class) /.test(line));
      assert.ok(marker, `no stable marker found in ${entry}`);
      assert.ok(bundle.includes(marker), `generated bundle is missing ${entry} (marker: ${marker})`);
    }
  });

  it("serves the generated site without stale FastAPI script tags", () => {
    const html = fs.readFileSync(indexPath, "utf8");
    assert.ok(!html.includes("/static/js/"), "generated shell still loads FastAPI script tags");
    assert.ok(html.includes("browser/product-app.mjs"), "generated shell does not load the bundle");
  });
});
