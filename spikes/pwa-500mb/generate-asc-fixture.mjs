import fs from "node:fs";
import path from "node:path";

const targetMiB = Number(process.argv[2] || 50);
const outPath = process.argv[3] || path.join("tmp", `ctd-${targetMiB}mib.asc`);
const targetBytes = targetMiB * 1024 * 1024;

fs.mkdirSync(path.dirname(outPath), { recursive: true });
const handle = fs.openSync(outPath, "w");
let written = 0;

function write(text) {
  const bytes = Buffer.byteLength(text);
  fs.writeSync(handle, text);
  written += bytes;
}

write("date Mon Jan 01 00:00:00.000 2024\n");
write("base hex timestamps absolute\n");
write("internal events logged\n");

let i = 0;
while (written < targetBytes) {
  const timestamp = (i / 1000).toFixed(6).padStart(12, " ");
  const id = (0x100 + (i % 512)).toString(16).toUpperCase();
  const direction = i % 2 === 0 ? "Rx" : "Tx";
  const data = [
    i & 0xff,
    (i >> 8) & 0xff,
    (i >> 16) & 0xff,
    (i >> 24) & 0xff,
    0x11,
    0x22,
    0x33,
    0x44,
  ].map((v) => v.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  write(`${timestamp} 1 ${id} ${direction} d 8 ${data}\n`);
  i += 1;
}

fs.closeSync(handle);
console.log(JSON.stringify({ outPath, targetMiB, bytes: written, lines: i + 3 }, null, 2));
