"""Full-size qualification of the frozen Windows executable on a large ASC (req_034 AC1-AC4, AC10).

Drives the real ``CanTraceDiag.exe`` over loopback HTTP (and optionally through
the browser UI with Playwright) against a generated fixture from
``scripts/generate_large_asc.py``, and writes a JSON report containing only
anonymized facts: counts, hashes, timings, memory and hardware description.

Phases (all against the same running service, fresh per-user home):

1. boundary: a trace part of cap + 1 bytes is rejected while streaming, leaves no
   staging data and no analysis;
2. cap - 1 bytes import is accepted (``--skip-cap-minus-one`` to save time);
3. the exact-size import is timed (upload, indexing, ready) while the service
   process tree's working set is sampled;
4. counts are checked against the fixture manifest (no silent frame loss);
5. warm latency: >= N iterations each of a filtered 200-row trace page, two
   signals at <= 4000 points, and a two-signal A/B cursor lookup (p50/p95/max);
6. cancellation: during transfer and during indexing (acknowledgement time), the
   previous analysis stays published and staging is removed;
7. fidelity: the raw ASC export is compared frame by frame with the source
   (timestamp to 1 us, channel, id, extended flag, direction, DLC, payload) and
   the source SHA-256 is unchanged;
8. optional browser phase (``--browser msedge``): import through the real file
   picker and UI interactions while the browser process tree is sampled.

Requires ``psutil`` (and ``playwright`` for the browser phase) in the harness
environment; the executable itself needs neither.

    python scripts/qualify_windows_large_asc.py --exe dist/windows/CanTraceDiag-....exe \\
        --asc D:/qual/g1g.asc --report qual.json --browser msedge
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import uuid
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

GIB = 1024**3


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8 << 20):
            h.update(chunk)
    return h.hexdigest()


def pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(q / 100 * (len(ordered) - 1))))
    return ordered[k]


def summarize(values: list[float]) -> dict:
    return {"n": len(values), "p50_s": round(statistics.median(values), 4),
            "p95_s": round(pct(values, 95), 4), "max_s": round(max(values), 4)}


class TreeSampler:
    """Samples the combined working set of a process tree every ``period`` s.

    Reports the sampled combined peak and a conservative upper bound: the sum of
    every process's own peak working set (``peak_wset``), which can only exceed
    the true simultaneous peak.
    """

    def __init__(self, roots, period: float = 0.25) -> None:
        self._roots = roots  # callable returning root psutil.Process objects
        self.period = period
        self.peak_combined = 0
        self.peak_wset: dict[int, int] = {}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _procs(self) -> list[psutil.Process]:
        procs: dict[int, psutil.Process] = {}
        for root in self._roots():
            try:
                procs[root.pid] = root
                for child in root.children(recursive=True):
                    procs[child.pid] = child
            except psutil.Error:
                continue
        return list(procs.values())

    def _run(self) -> None:
        while not self._stop.is_set():
            total = 0
            for proc in self._procs():
                try:
                    info = proc.memory_info()
                except psutil.Error:
                    continue
                total += info.rss  # WorkingSetSize on Windows
                peak = getattr(info, "peak_wset", info.rss)
                self.peak_wset[proc.pid] = max(self.peak_wset.get(proc.pid, 0), peak)
            self.peak_combined = max(self.peak_combined, total)
            self._stop.wait(self.period)

    def start(self) -> TreeSampler:
        self._thread.start()
        return self

    def stop(self) -> dict:
        self._stop.set()
        self._thread.join()
        return {
            "sampled_combined_peak_bytes": self.peak_combined,
            "sum_of_process_peaks_bytes": sum(self.peak_wset.values()),
            "processes": len(self.peak_wset),
        }


class Service:
    def __init__(self, exe: Path, home: Path) -> None:
        self.exe, self.home = exe, home
        self.proc: subprocess.Popen | None = None
        self.port = 0
        self.token = ""

    def start(self) -> float:
        t0 = time.monotonic()
        log = open(self.home.parent / "service-console.log", "a", encoding="utf-8")  # noqa: SIM115
        self.proc = subprocess.Popen(
            [str(self.exe), "--home", str(self.home), "--no-browser"],
            stdout=log, stderr=subprocess.STDOUT,
        )
        instance = self.home / "instance.json"
        while time.monotonic() - t0 < 180:
            if instance.is_file():
                try:
                    data = json.loads(instance.read_text(encoding="utf-8"))
                    self.port, self.token = data["port"], data["token"]
                    return time.monotonic() - t0
                except (ValueError, KeyError):
                    pass
            if self.proc.poll() is not None:
                raise RuntimeError("service exited during startup")
            time.sleep(0.2)
        raise RuntimeError("service did not become ready")

    def root(self) -> list[psutil.Process]:
        return [psutil.Process(self.proc.pid)] if self.proc and self.proc.poll() is None else []

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            subprocess.run([str(self.exe), "--home", str(self.home), "--stop"],
                           capture_output=True, timeout=60)
            try:
                self.proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                               capture_output=True)

    # -- HTTP --------------------------------------------------------------
    def conn(self, timeout: float = 3600) -> http.client.HTTPConnection:
        return http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)

    def get(self, path: str) -> dict:
        c = self.conn()
        c.request("GET", path, headers={"X-CTD-Token": self.token})
        r = c.getresponse()
        body = r.read()
        c.close()
        if r.status != 200:
            raise RuntimeError(f"GET {path} -> {r.status}: {body[:200]!r}")
        return json.loads(body)

    def post(self, path: str, payload: dict | None = None) -> tuple[int, bytes]:
        c = self.conn()
        data = json.dumps(payload or {}).encode()
        c.request("POST", path, body=data, headers={
            "X-CTD-Token": self.token, "Content-Type": "application/json"})
        r = c.getresponse()
        body = r.read()
        c.close()
        return r.status, body

    def upload(self, trace: Path, dbc: Path | None, *, trace_bytes: int | None = None,
               extra: bytes = b"", chunked: bool = False, on_sent=None) -> tuple[int, dict]:
        """Stream a multipart upload of ``trace`` (first ``trace_bytes`` + ``extra``)."""
        size = trace.stat().st_size if trace_bytes is None else trace_bytes
        boundary = uuid.uuid4().hex
        head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"trace\"; "
                f"filename=\"{trace.name}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
                ).encode()
        tail = b"\r\n"
        if dbc is not None:
            tail += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"dbcs\"; "
                     f"filename=\"{dbc.name}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
                     ).encode() + dbc.read_bytes() + b"\r\n"
        tail += f"--{boundary}--\r\n".encode()
        total = len(head) + size + len(extra) + len(tail)
        c = self.conn()
        c.putrequest("POST", "/api/import-files")
        c.putheader("X-CTD-Token", self.token)
        c.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
        if chunked:
            c.putheader("Transfer-Encoding", "chunked")
        else:
            c.putheader("Content-Length", str(total))
        c.endheaders()

        def send(data: bytes) -> None:
            if chunked:
                c.send(f"{len(data):X}\r\n".encode() + data + b"\r\n")
            else:
                c.send(data)

        sent = 0
        try:
            send(head)
            with open(trace, "rb") as handle:
                remaining = size
                while remaining:
                    block = handle.read(min(4 << 20, remaining))
                    if not block:
                        break
                    send(block)
                    remaining -= len(block)
                    sent += len(block)
                    if on_sent is not None:
                        on_sent(sent)
            if extra:
                send(extra)
            send(tail)
            if chunked:
                c.send(b"0\r\n\r\n")
        except (ConnectionError, OSError):
            pass  # the server may reject and close early; read its response
        try:
            r = c.getresponse()
            body = r.read()
            status = r.status
        except (ConnectionError, OSError, http.client.HTTPException) as exc:
            c.close()
            return 0, {"detail": f"connection closed: {exc!r}"}
        c.close()
        try:
            return status, json.loads(body)
        except ValueError:
            return status, {"raw": body[:200].decode("latin-1")}


def staging_entries(home: Path) -> list[str]:
    staging = home / "data" / "staging"
    return [p.name for p in staging.iterdir()] if staging.is_dir() else []


def hardware() -> dict:
    def ps(cmd: str) -> str:
        out = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd],
                             capture_output=True, text=True, timeout=60)
        return out.stdout.strip()

    return {
        "os": ps("(Get-CimInstance Win32_OperatingSystem | "
                 "ForEach-Object { $_.Caption + ' ' + $_.Version + ' ' + $_.OSArchitecture })"),
        "cpu": ps("(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cpus": psutil.cpu_count(logical=True),
        "ram_bytes": psutil.virtual_memory().total,
        "disk": ps("Get-PhysicalDisk | ForEach-Object { $_.FriendlyName + ' ' + $_.MediaType + "
                   "' ' + $_.BusType } | Select-Object -First 3 | Out-String").splitlines(),
        "python_harness": platform.python_version(),
    }


def compare_fidelity(source: Path, exported: Path) -> dict:
    """Stream both ASC files and compare every frame; returns counts and mismatches."""
    from cantracediag.formats.asc import iter_asc
    from cantracediag.models import RawCanFrame

    def frames(path: Path):
        for item in iter_asc(path):
            if isinstance(item, RawCanFrame):
                yield (round(item.timestamp_s * 1e6), item.channel, item.arbitration_id,
                       item.is_extended_id, item.direction, item.dlc, bytes(item.data))

    count = mismatches = 0
    first_mismatch = None
    a_iter, b_iter = frames(source), frames(exported)
    sentinel = object()
    while True:
        a = next(a_iter, sentinel)
        b = next(b_iter, sentinel)
        if a is sentinel and b is sentinel:
            break
        count += 1
        if a != b:
            mismatches += 1
            if first_mismatch is None:
                first_mismatch = count  # index only: never publish payloads
    return {"frames_compared": count, "mismatches": mismatches,
            "first_mismatch_index": first_mismatch}


def wait_job(svc: Service, until: set[str], timeout: float) -> dict:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        job = svc.get("/api/import-job")
        if job.get("phase") in until:
            return job
        time.sleep(0.05)
    raise RuntimeError(f"job did not reach {until}")


def latency_phase(svc: Service, n: int, rng: random.Random) -> dict:
    status = svc.get("/api/status")
    lo, hi = status["summary"]["start_s"], status["summary"]["end_s"]
    signals = [s for s in svc.get("/api/signals")["signals"] if s.get("present")]
    numeric = [s for s in signals if s.get("unit")] or signals
    pair = numeric[:2]

    def series(s, start, end) -> None:
        q = urllib.parse.urlencode({"message": s["message_name"], "signal": s["signal_name"],
                                    "start": start, "end": end, "max_points": 4000})
        r = svc.get(f"/api/series?{q}")
        assert len(r["t"]) <= 4000

    def plot_two(start, end) -> float:
        t0 = time.perf_counter()
        threads = [threading.Thread(target=series, args=(s, start, end)) for s in pair]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return time.perf_counter() - t0

    # Cold: first full-range plot decodes the signals' frames on demand.
    cold_plot = plot_two(lo, hi)

    def window() -> tuple[float, float]:
        span = (hi - lo) * rng.choice([1.0, 0.25, 0.05, 0.01])
        start = rng.uniform(lo, hi - span)
        return start, start + span

    for _ in range(3):  # warm-up
        plot_two(*window())
    plots = [plot_two(*window()) for _ in range(n)]

    ids = [s["id_hex"] for s in pair]
    pages = []
    for i in range(n):
        start = rng.uniform(lo, hi)
        q = urllib.parse.urlencode({"limit": 200, "start": start, "id": ids[i % len(ids)]})
        t0 = time.perf_counter()
        r = svc.get(f"/api/trace?{q}")
        pages.append(time.perf_counter() - t0)
        assert len(r["rows"]) <= 200

    cursors = []
    body = {"signals": [{"message": s["message_name"], "signal": s["signal_name"]} for s in pair]}
    for _ in range(n):
        a = rng.uniform(lo, hi)
        b = rng.uniform(lo, hi)
        t0 = time.perf_counter()
        status_code, _ = svc.post("/api/cursors", {**body, "a": a, "b": b})
        cursors.append(time.perf_counter() - t0)
        assert status_code == 200

    return {
        "signals": "two DBC signals of the fixture (names withheld)",
        "cold_first_full_range_plot_s": round(cold_plot, 3),
        "trace_page_200_filtered": summarize(pages),
        "plot_two_signals_4000_points": summarize(plots),
        "cursor_ab_two_signals": summarize(cursors),
    }


def browser_phase(url: str, asc: Path, dbc: Path, channel: str, n: int,
                  out: dict | None = None, ui_import: bool = True) -> dict:
    from playwright.sync_api import sync_playwright

    before = {p.pid for p in psutil.process_iter()}

    def browser_roots() -> list[psutil.Process]:
        roots = []
        for p in psutil.process_iter(["pid", "cmdline"]):
            if p.pid in before:
                continue
            try:
                if "--remote-debugging-pipe" in " ".join(p.info["cmdline"] or []):
                    roots.append(p)
            except psutil.Error:
                continue
        return roots

    out = {} if out is None else out
    out["channel"] = channel
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel=channel, headless=False)
        out["browser_version"] = browser.version
        sampler = TreeSampler(browser_roots).start()
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        console: list[str] = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text[:200]}")
                if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: console.append(f"pageerror: {str(e)[:200]}"))
        requests: dict[str, float] = {}
        finished: list[tuple[str, float]] = []

        def _short(u: str) -> str:
            return u.split("/api/", 1)[-1][:80]

        page.on("request", lambda r: requests.__setitem__(r.url, time.monotonic())
                if "/api/" in r.url else None)
        def _done(r) -> None:
            if "/api/" not in r.url:
                return
            resp = r.response()
            finished.append((_short(r.url), resp.status if resp else None,
                             round(time.monotonic() - requests.pop(r.url, time.monotonic()), 2)))

        page.on("requestfinished", _done)
        out["_requests"] = (requests, finished, _short)
        page.goto(url)
        page.wait_for_function("() => typeof state !== 'undefined'")
        if not ui_import:
            page.wait_for_function("() => state.loaded && state.signals.length > 0",
                                   timeout=120_000)
        else:
            _ui_import(page, asc, dbc, out, console)
        _ui_interactions(page, n, out)
        out["memory"] = sampler.stop()
        browser.close()
    out.pop("_requests", None)
    return out


def _ui_import(page, asc: Path, dbc: Path, out: dict, console: list[str]) -> None:
    page.set_input_files("#traceFile", str(asc))
    page.set_input_files("#dbcFiles", str(dbc))
    t0 = time.monotonic()
    # A restored analysis already looks "indexed": wait for this import's
    # own response, then for the UI to finish rendering it.
    with page.expect_response(lambda r: "/api/import-files" in r.url,
                              timeout=30 * 60 * 1000) as resp:
        page.click("#loadBtn")
    out["ui_import_status"] = resp.value.status
    try:
        page.wait_for_function(
            # onLoaded() ends with the first trace page: only then has it also
            # restored the persisted signal selection (which resets it).
            "() => state.loaded && state.signals.length > 0 &&"
            " document.getElementById('statusLed').classList.contains('indexed') &&"
            " state.trace.rows.length > 0",
            timeout=10 * 60 * 1000, polling=500)
    except Exception:
        out["ui_state_on_timeout"] = page.evaluate(
            "() => ({loaded: state.loaded, signals: state.signals.length,"
            " led: document.getElementById('statusLed').className,"
            " summary: document.getElementById('summary').textContent.slice(0, 200)})")
        out["console_errors"] = console[-10:]
        raise
    out["ui_import_to_ready_s"] = round(time.monotonic() - t0, 1)


def _ui_interactions(page, n: int, out: dict) -> None:
    t0 = time.monotonic()
    page.evaluate("""async () => {
        const sigs = state.signals.filter((s) => s.present && s.unit);
        await toggleSignal(sigs[0], true);
        await toggleSignal(sigs[1], true);
    }""")
    try:
        page.wait_for_function("() => state.selected.length === 2 && "
                               "state.selected.every((s) => s.t.length > 0)", timeout=600_000)
    except Exception:
        requests, finished, short = out["_requests"]
        now = time.monotonic()
        out["pending_requests"] = [(short(u), round(now - t, 1)) for u, t in requests.items()]
        out["finished_requests"] = finished[-15:]
        out["ui_state_on_timeout"] = page.evaluate(
            "() => ({selected: state.selected.map((s) => s.t.length),"
            " plotError: document.getElementById('plotError').textContent.slice(0, 300)})")
        raise
    out["ui_plot_two_signals_first_s"] = round(time.monotonic() - t0, 2)

    # Timed inside the page (fetch + render), so Playwright's own
    # instrumentation overhead does not count as application latency.
    cursor_ms = page.evaluate("""async (n) => {
        const out = [];
        const [lo, hi] = state.bounds;
        for (let i = 0; i < n; i++) {
            const f = (i + 0.5) / n;
            const t = performance.now();
            state.cursor.a = lo + (hi - lo) * f;
            state.cursor.b = lo + (hi - lo) * f * 0.9;
            renderPlot();
            await refreshCursorReadout();
            out.push(performance.now() - t);
        }
        return out;
    }""", n)
    out["ui_cursor_update"] = summarize([v / 1000 for v in cursor_ms])

    page.click("#viewTrace")
    page.wait_for_selector("#traceTable tbody tr")
    # Filtered pages, as the 200-row criterion states: filter by one id.
    page_ms = page.evaluate("""async (n) => {
        const ids = [...new Set(state.signals.filter((s) => s.present).map((s) => s.id_hex))];
        const [lo, hi] = state.bounds;
        const out = [];
        for (let i = 0; i < n; i++) {
            $("fId").value = ids[i % ids.length];
            $("fStart").value = String(lo + (hi - lo) * ((i * 37) % n) / n);
            const t = performance.now();
            const ok = await loadTrace(null);
            if (!ok || !state.trace.rows.length) throw new Error("trace page failed");
            out.push(performance.now() - t);
        }
        return out;
    }""", n)
    out["ui_trace_page_200_filtered"] = summarize([v / 1000 for v in page_ms])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--asc", type=Path, required=True)
    parser.add_argument("--dbc", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=None,
                        help="scratch folder on the drive under test (default: temp)")
    parser.add_argument("--interactions", type=int, default=20)
    parser.add_argument("--browser", default=None, help="Playwright channel, e.g. msedge")
    parser.add_argument("--skip-cap-minus-one", action="store_true")
    parser.add_argument("--skip-boundary", action="store_true")
    parser.add_argument("--skip-latency", action="store_true")
    parser.add_argument("--browser-reuse-import", action="store_true",
                        help="open the browser on the API-imported analysis (no UI upload)")
    parser.add_argument("--skip-fidelity", action="store_true")
    parser.add_argument("--external", action="store_true",
                        help="the ASC is an external acquisition: no manifest, no boundary")
    args = parser.parse_args()

    asc, exe = args.asc.resolve(), args.exe.resolve()
    dbc = (args.dbc or asc.with_suffix(".dbc")).resolve()
    manifest = None if args.external else json.loads(
        (args.manifest or asc.with_suffix(".json")).read_text())
    work = Path(tempfile.mkdtemp(prefix="ctd-qual-", dir=args.work))
    home = work / "home"
    rng = random.Random(20261019)
    report: dict = {
        "exe": {"name": exe.name, "sha256": sha256(exe), "size": exe.stat().st_size},
        "hardware": hardware(),
        "fixture": {"bytes": asc.stat().st_size, "sha256_before": sha256(asc),
                    "dbc_present": dbc.is_file()},
    }
    if manifest:
        report["fixture"]["manifest"] = manifest
    print(json.dumps(report["hardware"], indent=1), flush=True)

    svc = Service(exe, home)
    report["startup_s"] = round(svc.start(), 2)
    sampler = TreeSampler(svc.root).start()
    dbc_arg = dbc if dbc.is_file() else None
    size = asc.stat().st_size
    try:
        if not args.external and not args.skip_boundary:
            cap = 1_073_741_824
            assert size == cap, f"boundary phases expect an exact 1 GiB fixture, got {size}"
            t0 = time.monotonic()
            status, body = svc.upload(asc, dbc_arg, extra=b"\n")
            report["boundary_cap_plus_one"] = {
                "status": status, "detail": body.get("detail"),
                "seconds": round(time.monotonic() - t0, 1),
                "staging_left": len(staging_entries(home)),
                "analysis_loaded": svc.get("/api/status").get("loaded"),
            }
            print("cap+1:", report["boundary_cap_plus_one"], flush=True)
            status, body = svc.upload(asc, dbc_arg, extra=b"\n", chunked=True)
            report["boundary_cap_plus_one_chunked"] = {"status": status,
                                                       "detail": body.get("detail")}
            print("cap+1 chunked:", report["boundary_cap_plus_one_chunked"], flush=True)
            if not args.skip_cap_minus_one:
                t0 = time.monotonic()
                status, body = svc.upload(asc, dbc_arg, trace_bytes=size - 1)
                report["boundary_cap_minus_one"] = {
                    "status": status, "seconds": round(time.monotonic() - t0, 1),
                    "frames": (body.get("summary") or {}).get("frames"),
                }
                print("cap-1:", report["boundary_cap_minus_one"], flush=True)

        # Main measured import.
        t0 = time.monotonic()
        upload_done: dict = {}

        def on_sent(n: int) -> None:
            if n >= size and "t" not in upload_done:
                upload_done["t"] = time.monotonic() - t0

        status, body = svc.upload(asc, dbc_arg, on_sent=on_sent)
        total = time.monotonic() - t0
        assert status == 200, (status, body)
        summary = body["summary"]
        report["import"] = {
            "status": status,
            "transfer_s": round(upload_done.get("t", 0.0), 1),
            "upload_to_ready_s": round(total, 1),
            "frames": summary["frames"], "events": summary["events"],
            "decoded_frames": summary["decoded_frames"],
            "unique_ids": summary["unique_ids"], "event_types": summary["event_types"],
            "start_s": summary["start_s"], "end_s": summary["end_s"],
            "staging_left": len(staging_entries(home)),
        }
        if manifest:
            expected_events = manifest["error_frames"] + manifest["status"] + manifest["malformed"]
            report["import"]["frames_match_manifest"] = summary["frames"] == manifest["frames"]
            report["import"]["events_match_manifest"] = summary["events"] == expected_events
        analysis = home / "data" / "analysis"
        report["import"]["analysis_bytes_on_disk"] = sum(
            p.stat().st_size for p in analysis.rglob("*") if p.is_file())
        print("import:", report["import"], flush=True)

        if not args.skip_latency:
            report["latency"] = latency_phase(svc, args.interactions, rng)
            print("latency:", json.dumps(report["latency"]), flush=True)

        if not args.external:
            # Cancel during transfer.
            cancelled: dict = {}

            def cancel_mid_transfer(n: int) -> None:
                if n >= size // 4 and "t" not in cancelled:
                    cancelled["t"] = time.monotonic()
                    svc.post("/api/import-cancel")

            status, body = svc.upload(asc, dbc_arg, on_sent=cancel_mid_transfer)
            st = svc.get("/api/status")
            report["cancel_during_transfer"] = {
                "status": status, "detail": body.get("detail"),
                "previous_analysis_kept": st["summary"]["frames"] == summary["frames"],
                "staging_left": len(staging_entries(home)),
            }
            print("cancel transfer:", report["cancel_during_transfer"], flush=True)

            # Cancel during indexing.
            result: dict = {}
            th = threading.Thread(target=lambda: result.update(
                zip(("status", "body"), svc.upload(asc, dbc_arg), strict=True)))
            th.start()
            wait_job(svc, {"indexing"}, 600)
            time.sleep(5)
            t0 = time.monotonic()
            svc.post("/api/import-cancel")
            wait_job(svc, {"cancelled", "failed", "complete"}, 600)
            ack = time.monotonic() - t0
            th.join()
            st = svc.get("/api/status")
            report["cancel_during_indexing"] = {
                "ack_s": round(ack, 2), "status": result.get("status"),
                "previous_analysis_kept": st["summary"]["frames"] == summary["frames"],
                "staging_left": len(staging_entries(home)),
                "analysis_dirs": len([p for p in analysis.iterdir() if p.is_dir()]),
            }
            print("cancel indexing:", report["cancel_during_indexing"], flush=True)

        if not args.skip_fidelity:
            exported = work / "export.asc"
            c = svc.conn()
            c.request("POST", "/api/export-asc", body=json.dumps({"scope": "full"}).encode(),
                      headers={"X-CTD-Token": svc.token, "Content-Type": "application/json"})
            r = c.getresponse()
            t0 = time.monotonic()
            with open(exported, "wb") as handle:
                while chunk := r.read(8 << 20):
                    handle.write(chunk)
            c.close()
            report["fidelity"] = {"export_status": r.status,
                                  "export_s": round(time.monotonic() - t0, 1),
                                  **compare_fidelity(asc, exported)}
            exported.unlink()
            print("fidelity:", report["fidelity"], flush=True)

        report["service_memory"] = sampler.stop()
        sampler = None
        if args.browser:
            url = f"http://127.0.0.1:{svc.port}/"
            service_sampler = TreeSampler(svc.root).start()
            browser_out: dict = {}
            try:
                report["browser"] = browser_phase(url, asc, dbc, args.browser, args.interactions,
                                                  browser_out, not args.browser_reuse_import)
            except Exception as exc:
                browser_out.pop("_requests", None)
                report["browser"] = {**browser_out, "error": repr(exc)[:300]}
            report["service_memory_during_browser"] = service_sampler.stop()
            print("browser:", json.dumps(report["browser"]), flush=True)
    finally:
        if sampler is not None:
            report["service_memory"] = sampler.stop()
        svc.stop()
        log = home / "logs" / "cantracediag.log"
        if log.is_file():
            lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
            report["service_log_errors"] = [
                ln[:300] for ln in lines if "ERROR" in ln or "Traceback" in ln or "Error" in ln
            ][-30:]
        report["fixture"]["sha256_after"] = sha256(asc)
        report["fixture"]["source_unchanged"] = (
            report["fixture"]["sha256_after"] == report["fixture"]["sha256_before"])
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        shutil.rmtree(work, ignore_errors=True)
    print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
