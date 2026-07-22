import { LocalPwaBackend } from "./local-backend.ts";
import { WorkspaceManager, type WorkspaceDbc, type WorkspaceSnapshot } from "./workspace.ts";

const backend = new LocalPwaBackend();
const workspaces = new WorkspaceManager();

const traceInput = document.querySelector<HTMLInputElement>("#trace")!;
const dbcInput = document.querySelector<HTMLInputElement>("#dbc")!;
const workspaceImport = document.querySelector<HTMLInputElement>("#workspaceImport")!;
const workspaceName = document.querySelector<HTMLInputElement>("#workspaceName")!;
const loadBtn = document.querySelector<HTMLButtonElement>("#load")!;
const purgeBtn = document.querySelector<HTMLButtonElement>("#purge")!;
const saveBtn = document.querySelector<HTMLButtonElement>("#saveWorkspace")!;
const exportBtn = document.querySelector<HTMLButtonElement>("#exportWorkspace")!;
const importBtn = document.querySelector<HTMLButtonElement>("#importWorkspace")!;
const workspaceList = document.querySelector<HTMLElement>("#workspaceList")!;
const quota = document.querySelector<HTMLElement>("#quota")!;
const summary = document.querySelector<HTMLElement>("#summary")!;
const signals = document.querySelector<HTMLElement>("#signals")!;
const trace = document.querySelector<HTMLElement>("#traceRows")!;
const series = document.querySelector<HTMLElement>("#series")!;
const appStatus = document.querySelector<HTMLElement>("#appStatus")!;

let currentWorkspace: WorkspaceSnapshot | null = null;
let currentTraceName = "";
let currentTraceText = "";
let currentDbcs: WorkspaceDbc[] = [];

loadBtn.addEventListener("click", async () => {
  const traceFile = traceInput.files?.[0];
  const dbcFiles = Array.from(dbcInput.files ?? []);
  if (!traceFile || !dbcFiles.length) {
    appStatus.textContent = "Choose one ASC trace and at least one DBC.";
    return;
  }
  const traceText = await traceFile.text();
  const dbcs = await Promise.all(dbcFiles.map(async (file) => ({ name: file.name, text: await file.text() })));
  currentWorkspace = null;
  currentTraceName = traceFile.name;
  currentTraceText = traceText;
  currentDbcs = dbcs;
  const result = await backend.importText(traceText, dbcs);
  if (result.needs_resolution) {
    appStatus.textContent = `DBC conflict needs resolution: ${JSON.stringify(result.conflicts)}`;
    render();
    return;
  }
  appStatus.textContent = "Imported locally. Save a workspace to keep it in this browser.";
  render();
});

purgeBtn.addEventListener("click", () => {
  backend.purge();
  workspaces.purge();
  currentWorkspace = null;
  currentTraceName = "";
  currentTraceText = "";
  currentDbcs = [];
  appStatus.textContent = "Local workspaces purged.";
  render();
});

saveBtn.addEventListener("click", () => {
  if (!currentTraceText || !currentDbcs.length) {
    appStatus.textContent = "Import a trace and DBC before saving a workspace.";
    return;
  }
  try {
    currentWorkspace = workspaces.save({
      id: currentWorkspace?.id,
      name: workspaceName.value || currentTraceName || "Workspace",
      traceName: currentTraceName,
      traceText: currentTraceText,
      dbcs: currentDbcs,
    });
    appStatus.textContent = `Workspace saved: ${currentWorkspace.name}`;
  } catch (error) {
    appStatus.textContent = error instanceof Error ? error.message : String(error);
  }
  render();
});

exportBtn.addEventListener("click", () => {
  if (!currentWorkspace) {
    appStatus.textContent = "Save or open a workspace before exporting.";
    return;
  }
  const blob = new Blob([workspaces.export(currentWorkspace.id)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${currentWorkspace.name.replace(/[^a-z0-9_.-]+/gi, "_")}.ctd-workspace.json`;
  link.click();
  URL.revokeObjectURL(url);
});

importBtn.addEventListener("click", async () => {
  const file = workspaceImport.files?.[0];
  if (!file) {
    appStatus.textContent = "Choose a workspace export first.";
    return;
  }
  try {
    const imported = workspaces.import(await file.text());
    await openWorkspace(imported.id);
    appStatus.textContent = `Workspace imported: ${imported.name}`;
  } catch (error) {
    appStatus.textContent = error instanceof Error ? error.message : String(error);
  }
});

workspaceList.addEventListener("click", async (event) => {
  const target = event.target as HTMLElement;
  const id = target.dataset.id;
  if (!id) return;
  if (target.dataset.action === "open") await openWorkspace(id);
  if (target.dataset.action === "delete") {
    workspaces.delete(id);
    if (currentWorkspace?.id === id) currentWorkspace = null;
    appStatus.textContent = "Workspace deleted.";
    render();
  }
});

async function openWorkspace(id: string): Promise<void> {
  const snapshot = workspaces.read(id);
  if (!snapshot) {
    appStatus.textContent = "Workspace not found.";
    return;
  }
  const result = await backend.importText(snapshot.traceText, snapshot.dbcs);
  if (result.needs_resolution) {
    appStatus.textContent = `Workspace needs DBC resolution: ${JSON.stringify(result.conflicts)}`;
    render();
    return;
  }
  currentWorkspace = snapshot;
  currentTraceName = snapshot.traceName;
  currentTraceText = snapshot.traceText;
  currentDbcs = snapshot.dbcs;
  workspaceName.value = snapshot.name;
  appStatus.textContent = `Workspace opened: ${snapshot.name}`;
  render();
}

function render() {
  summary.textContent = JSON.stringify(backend.status(), null, 2);
  const signalRows = (backend.signals().signals as Array<{ message_name: string; signal_name: string; unit: string | null }>).slice(0, 20);
  signals.innerHTML = signalRows.map((s) => `<li>${esc(s.message_name)}.${esc(s.signal_name)} ${esc(s.unit ?? "")}</li>`).join("");
  const rows = backend.trace({ limit: 20 }).rows as Array<Record<string, unknown>>;
  trace.textContent = rows.map((row) => `${row.timestamp_s} ${row.kind} ${row.id_hex ?? ""} ${row.name ?? row.event_type ?? ""}`).join("\n");
  if (signalRows.length) {
    const first = signalRows[0];
    series.textContent = JSON.stringify(backend.series(first.message_name, first.signal_name), null, 2);
  } else {
    series.textContent = "";
  }
  workspaceList.innerHTML = workspaces.list().map((ws) => `
    <li>
      <span>${esc(ws.name)} <small>${esc(ws.traceName)}</small></span>
      <button type="button" data-action="open" data-id="${esc(ws.id)}">Open</button>
      <button type="button" data-action="delete" data-id="${esc(ws.id)}">Delete</button>
    </li>
  `).join("");
  workspaces.estimateQuota().then((estimate) => {
    if (!estimate) {
      quota.textContent = "Storage estimate unavailable.";
      return;
    }
    const used = estimate.usage ?? 0;
    const total = estimate.quota ?? 0;
    quota.textContent = total
      ? `Storage: ${formatBytes(used)} used of ${formatBytes(total)} available to this origin.`
      : `Storage: ${formatBytes(used)} used.`;
  });
}

function esc(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function formatBytes(bytes: number): string {
  const units = ["B", "KiB", "MiB", "GiB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").then(
    () => { appStatus.textContent = appStatus.textContent || "PWA shell ready."; },
    () => { appStatus.textContent = "Service worker registration failed."; },
  );
}

render();
