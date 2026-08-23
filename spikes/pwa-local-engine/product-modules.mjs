import fs from "node:fs";
import path from "node:path";

/* Single source of truth for the product web modules that make up the PWA
 * bundle. The source HTML shell (`src/cantracediag/web/index.html`) declares
 * both the module set and its execution order; duplicating that list in the
 * build is what let `fullscreen.js` ship as a dead control. */

export const SHELL_HTML = path.resolve("src/cantracediag/web/index.html");
export const WEB_JS_DIR = path.resolve("src/cantracediag/web/js");

const SHELL_SCRIPT_PATTERN = /<script\s+src="\/static\/js\/([^"]+)"><\/script>/g;

/** Ordered product module filenames declared by the source HTML shell. */
export function shellModules(htmlPath = SHELL_HTML) {
  const html = fs.readFileSync(htmlPath, "utf8");
  return [...html.matchAll(SHELL_SCRIPT_PATTERN)].map((match) => match[1]);
}

/** Product module filenames present on disk. */
export function availableModules(jsDir = WEB_JS_DIR) {
  return fs.readdirSync(jsDir).filter((entry) => entry.endsWith(".js")).sort();
}

/**
 * Ordered module list for the generated bundle, or a thrown error describing
 * the divergence. The build must not be able to silently drop a module the
 * delivered HTML shell relies on, nor bundle one the shell never declares.
 */
export function resolveProductModules({ htmlPath = SHELL_HTML, jsDir = WEB_JS_DIR } = {}) {
  const declared = shellModules(htmlPath);
  if (!declared.length) {
    throw new Error(`No product script tags found in ${path.relative(process.cwd(), htmlPath)}`);
  }
  const available = availableModules(jsDir);
  const missingOnDisk = declared.filter((entry) => !available.includes(entry));
  if (missingOnDisk.length) {
    throw new Error(`Shell declares modules that do not exist in ${path.relative(process.cwd(), jsDir)}: ${missingOnDisk.join(", ")}`);
  }
  const undeclared = available.filter((entry) => !declared.includes(entry));
  if (undeclared.length) {
    throw new Error(`Product modules exist but are not declared by the HTML shell: ${undeclared.join(", ")}`);
  }
  return declared;
}

/** Marker line embedded in the generated bundle so the artifact is auditable. */
export function moduleManifestComment(modules) {
  return `// ctd:modules ${modules.join(",")}`;
}

/** Module list recorded in a generated bundle, or null when absent. */
export function bundledModules(bundleSource) {
  const match = bundleSource.match(/^\/\/ ctd:modules (.+)$/m);
  return match ? match[1].split(",") : null;
}
