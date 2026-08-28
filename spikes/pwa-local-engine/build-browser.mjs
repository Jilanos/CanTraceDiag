import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { stripTypeScriptTypes } from "node:module";
import { moduleManifestComment, resolveProductModules, WEB_JS_DIR } from "./product-modules.mjs";

const srcDir = path.resolve("spikes/pwa-local-engine/src");
const distDir = path.resolve("spikes/pwa-local-engine/browser");
const siteDir = path.resolve("spikes/pwa-local-engine/site");
fs.mkdirSync(distDir, { recursive: true });

/* The shell is shared with the server-backed app, which imports BLF; the static
 * bundle cannot (see src/local-backend.ts). These rewrites take BLF back out of
 * the generated picker, and `replaceOnce` fails the build if the source shell
 * stops matching -- a silent no-op would ship a picker offering a format the
 * bundle has no reader for. */
const STATIC_SHELL_REWRITES = [
  [
    '<input id="traceFile" type="file" accept=".asc,.trc,.blf" hidden />',
    '<input id="traceFile" type="file" accept=".asc,.trc" hidden />',
  ],
  [
    'title="Choose an ASC, text TRC, or binary BLF CAN trace"',
    'title="Choose an ASC or text TRC CAN trace"',
  ],
];

for (const entry of fs.readdirSync(srcDir)) {
  if (!entry.endsWith(".ts")) continue;
  const inputPath = path.join(srcDir, entry);
  const outputName = entry.replace(/\.ts$/, ".mjs");
  const outputPath = path.join(distDir, outputName);
  let source = fs.readFileSync(inputPath, "utf8");
  source = source
    .replaceAll(/from "\.\/([^"]+)\.ts"/g, 'from "./$1.mjs"')
    .replaceAll(/from "\.\.\/src\/([^"]+)\.ts"/g, 'from "../dist/$1.mjs"');
  const stripped = stripTypeScriptTypes(source, { mode: "strip" });
  fs.writeFileSync(outputPath, stripped);
}

const version = buildVersion();
const productAppSource = buildProductAppSource();
fs.writeFileSync(path.join(distDir, "product-app.mjs"), productAppSource);

fs.rmSync(siteDir, { recursive: true, force: true });
fs.mkdirSync(path.join(siteDir, "browser"), { recursive: true });
fs.mkdirSync(path.join(siteDir, "assets"), { recursive: true });
fs.writeFileSync(path.join(siteDir, "index.html"), buildProductIndex(version));
fs.copyFileSync(path.resolve("src/cantracediag/web/styles.css"), path.join(siteDir, "styles.css"));
fs.copyFileSync(path.resolve("spikes/pwa-local-engine/manifest.webmanifest"), path.join(siteDir, "manifest.webmanifest"));
fs.writeFileSync(path.join(siteDir, "sw.js"), buildServiceWorker(version));
for (const entry of fs.readdirSync(distDir)) {
  if (entry === "app.mjs") continue;
  fs.copyFileSync(path.join(distDir, entry), path.join(siteDir, "browser", entry));
}
for (const entry of fs.readdirSync(path.resolve("spikes/pwa-local-engine/assets"))) {
  fs.copyFileSync(
    path.resolve("spikes/pwa-local-engine/assets", entry),
    path.join(siteDir, "assets", entry),
  );
}
fs.copyFileSync(path.resolve("src/cantracediag/web/app-icon.svg"), path.join(siteDir, "assets", "app-icon.svg"));
fs.copyFileSync(path.resolve("src/cantracediag/web/app-emblem.svg"), path.join(siteDir, "assets", "app-emblem.svg"));
fs.copyFileSync(path.resolve("src/cantracediag/web/paulmondou-emblem.svg"), path.join(siteDir, "assets", "paulmondou-emblem.svg"));

console.log(`Built browser modules in ${path.relative(process.cwd(), distDir)}`);
console.log(`Built static site in ${path.relative(process.cwd(), siteDir)}`);

function replaceOnce(html, from, to) {
  const parts = html.split(from);
  if (parts.length !== 2) {
    throw new Error(`Static shell rewrite matched ${parts.length - 1} times, expected 1: ${from}`);
  }
  return parts.join(to);
}

function buildProductIndex(version) {
  let html = fs.readFileSync(path.resolve("src/cantracediag/web/index.html"), "utf8")
    .replace('<link rel="icon" href="/static/app-icon.svg" type="image/svg+xml" />', '<link rel="icon" href="./assets/app-icon.svg" type="image/svg+xml" />')
    .replace('<link rel="alternate icon" href="/favicon.ico" />', '<link rel="manifest" href="./manifest.webmanifest" />')
    .replace('<link rel="stylesheet" href="/static/styles.css" />', `<link rel="stylesheet" href="./styles.css?v=${version}" />`)
    .replace('src="/static/app-emblem.svg"', 'src="./assets/app-emblem.svg"')
    .replace('src="/static/paulmondou-emblem.svg"', 'src="./assets/paulmondou-emblem.svg"')
    .replaceAll("__CTD_APP_VERSION__", appVersion());
  for (const [from, to] of STATIC_SHELL_REWRITES) html = replaceOnce(html, from, to);
  html = html.replace(
    /<script src="\/static\/js\/[^"]+"><\/script>\n?/g,
    "",
  );
  return html.replace("</body>", `<script type="module" src="./browser/product-app.mjs?v=${version}"></script>\n</body>`);
}

function buildServiceWorker(version) {
  return fs.readFileSync(path.resolve("spikes/pwa-local-engine/sw.js"), "utf8")
    .replaceAll("__CTD_BUILD_VERSION__", version);
}

function buildVersion() {
  const hash = crypto.createHash("sha256");
  for (const file of buildVersionInputs()) {
    hash.update(path.relative(process.cwd(), file));
    hash.update("\0");
    hash.update(fs.readFileSync(file));
    hash.update("\0");
  }
  return hash.digest("hex").slice(0, 16);
}

function buildVersionInputs() {
  const files = [
    path.resolve("spikes/pwa-local-engine/manifest.webmanifest"),
    path.resolve("spikes/pwa-local-engine/sw.js"),
    path.resolve("src/cantracediag/web/index.html"),
    path.resolve("src/cantracediag/web/styles.css"),
    path.resolve("src/cantracediag/web/app-icon.svg"),
    path.resolve("src/cantracediag/web/app-emblem.svg"),
    path.resolve("src/cantracediag/web/paulmondou-emblem.svg"),
    path.resolve("pyproject.toml"),
  ];
  for (const entry of fs.readdirSync(srcDir).filter((entry) => entry.endsWith(".ts")).sort()) {
    files.push(path.join(srcDir, entry));
  }
  for (const entry of fs.readdirSync(path.resolve("src/cantracediag/web/js")).filter((entry) => entry.endsWith(".js")).sort()) {
    files.push(path.resolve("src/cantracediag/web/js", entry));
  }
  for (const entry of fs.readdirSync(path.resolve("spikes/pwa-local-engine/assets")).sort()) {
    files.push(path.resolve("spikes/pwa-local-engine/assets", entry));
  }
  return files;
}

function appVersion() {
  const pyproject = fs.readFileSync(path.resolve("pyproject.toml"), "utf8");
  const match = pyproject.match(/^version = "([^"]+)"$/m);
  if (!match) throw new Error("Unable to read project version from pyproject.toml");
  return match[1];
}

function buildProductAppSource() {
  // The module set and its execution order come from the source HTML shell.
  // A second hard-coded list here is what let `fullscreen.js` be delivered as
  // an inert control; `resolveProductModules` fails the build on divergence.
  const modules = resolveProductModules();
  let source = modules
    .map((entry) => fs.readFileSync(path.join(WEB_JS_DIR, entry), "utf8"))
    .join("\n\n");
  source = replaceBlock(
    source,
    "async function api(path, opts) {",
    "\n\nfunction reportError",
    `async function api(path, opts) {
  return localProductBackend.api(path, opts);
}

function reportError`,
  );
  source = replaceBlock(
    source,
    "// Upload with progress (AC8): XHR exposes upload.onprogress; fetch does not.",
    "\n\n/* ---- formatting",
    `// Local PWA import keeps the existing UI progress contract without XHR.
function uploadWithProgress(url, formData, onProgress, onUploadComplete) {
  return localProductBackend.uploadWithProgress(formData, onProgress, onUploadComplete);
}

/* ---- formatting`,
  );
  source = replaceBlock(
    source,
    '    const resp = await fetch("/api/export", withToken({',
    '    $("exportDialog").close();',
    `    const blob = exportLocalProductBlob(payload, localProductBackend);
    downloadBlob(blob, \`cantracediag_export.\${format === "parquet" ? "parquet" : "csv"}\`);
    $("exportDialog").close();`,
  );
  return `${moduleManifestComment(modules)}
import { createLocalProductBackend } from "./product-backend.mjs";
import { exportLocalProductBlob } from "./product-backend.mjs";

const localProductBackend = createLocalProductBackend();

${source}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch((error) => {
    console.warn("Service worker registration failed", error);
  });
}`;
}

function replaceBlock(source, start, end, replacement) {
  const startIndex = source.indexOf(start);
  if (startIndex < 0) throw new Error(`Unable to find start marker: ${start}`);
  const endIndex = source.indexOf(end, startIndex);
  if (endIndex < 0) throw new Error(`Unable to find end marker: ${end}`);
  return source.slice(0, startIndex) + replacement + source.slice(endIndex + end.length);
}
