import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { stripTypeScriptTypes } from "node:module";

const srcDir = path.resolve("spikes/pwa-local-engine/src");
const distDir = path.resolve("spikes/pwa-local-engine/browser");
const siteDir = path.resolve("spikes/pwa-local-engine/site");
fs.mkdirSync(distDir, { recursive: true });

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

const productAppSource = buildProductAppSource();
fs.writeFileSync(path.join(distDir, "product-app.mjs"), productAppSource);

fs.rmSync(siteDir, { recursive: true, force: true });
fs.mkdirSync(path.join(siteDir, "browser"), { recursive: true });
fs.mkdirSync(path.join(siteDir, "assets"), { recursive: true });
fs.writeFileSync(path.join(siteDir, "index.html"), buildProductIndex());
fs.copyFileSync(path.resolve("src/cantracediag/web/styles.css"), path.join(siteDir, "styles.css"));
fs.copyFileSync(path.resolve("spikes/pwa-local-engine/manifest.webmanifest"), path.join(siteDir, "manifest.webmanifest"));
fs.writeFileSync(path.join(siteDir, "sw.js"), buildServiceWorker());
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

console.log(`Built browser modules in ${path.relative(process.cwd(), distDir)}`);
console.log(`Built static site in ${path.relative(process.cwd(), siteDir)}`);

function buildProductIndex() {
  let html = fs.readFileSync(path.resolve("src/cantracediag/web/index.html"), "utf8")
    .replace('<link rel="icon" href="/static/app-icon.svg" type="image/svg+xml" />', '<link rel="icon" href="./assets/app-icon.svg" type="image/svg+xml" />')
    .replace('<link rel="alternate icon" href="/favicon.ico" />', '<link rel="manifest" href="./manifest.webmanifest" />')
    .replace('<link rel="stylesheet" href="/static/styles.css" />', '<link rel="stylesheet" href="./styles.css" />');
  html = html.replace(
    /<script src="\/static\/js\/[^"]+"><\/script>\n?/g,
    "",
  );
  return html.replace("</body>", '<script type="module" src="./browser/product-app.mjs"></script>\n</body>');
}

function buildServiceWorker() {
  const version = buildVersion();
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

function buildProductAppSource() {
  const webJsDir = path.resolve("src/cantracediag/web/js");
  const modules = ["core.js", "import.js", "signals.js", "plot.js", "report.js", "trace.js", "inspector.js", "main.js"];
  let source = modules
    .map((entry) => fs.readFileSync(path.join(webJsDir, entry), "utf8"))
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
  return `import { createLocalProductBackend } from "./product-backend.mjs";
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
