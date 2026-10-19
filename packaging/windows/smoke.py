"""Smoke-test the frozen CanTraceDiag.exe exactly as distributed (req_034 AC5, AC7-AC9).

Runs the executable with a scrubbed environment (no Python on PATH, no
``PYTHON*`` variables), from and with per-user paths containing spaces and
non-ASCII characters, and checks over loopback HTTP:

* start on an *occupied* preferred port -> next free port, ``instance.json``;
* ASC (+DBC), TRC, BLF and raw-CAN MF4 uploads through ``/api/import-files``;
* signals, plotted series, 200-row trace page, A/B cursors, report, CSV export
  and raw ASC export on the decoded ASC;
* server-side path import of a non-ASCII Windows path, kept native;
* a second launch attaches to the running instance instead of starting again;
* ``--stop`` stops it; a restart restores the last analysis and DBC library.

The harness itself uses Python (it generates the BLF/MF4 fixtures with the test
helpers); the executable under test never sees it. Writes a JSON report.

    python packaging/windows/smoke.py dist/windows/CanTraceDiag-1.3.0-windows-x64.exe
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "tests"))


class Smoke:
    def __init__(self, exe: Path, work: Path) -> None:
        self.exe = exe
        self.work = work
        self.home = work / "Profil utilisateur é ü" / "CanTraceDiag home"
        self.data = work / "Acquisitions d'essai ñ"
        self.data.mkdir(parents=True)
        self.proc: subprocess.Popen | None = None
        self.port = 0
        self.token = ""
        self.checks: list[dict] = []

    # -- process control -----------------------------------------------------
    def env(self) -> dict[str, str]:
        keep = ("SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "TEMP", "TMP", "USERPROFILE",
                "LOCALAPPDATA", "APPDATA", "USERNAME", "COMPUTERNAME", "PROCESSOR_ARCHITECTURE",
                "NUMBER_OF_PROCESSORS", "COMSPEC", "PATHEXT")
        env = {k: v for k, v in os.environ.items() if k.upper() in keep}
        system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
        env["PATH"] = os.pathsep.join([system_root + r"\System32", system_root])
        return env

    def run_exe(self, *args: str, wait: bool) -> subprocess.CompletedProcess | subprocess.Popen:
        cmd = [str(self.exe), "--home", str(self.home), "--no-browser", *args]
        if wait:
            return subprocess.run(cmd, env=self.env(), capture_output=True, text=True,
                                  timeout=180, encoding="utf-8", errors="replace")
        log = open(self.work / f"exe-{uuid.uuid4().hex[:6]}.log", "w", encoding="utf-8")  # noqa: SIM115
        return subprocess.Popen(cmd, env=self.env(), stdout=log, stderr=subprocess.STDOUT)

    def start(self, preferred: int) -> float:
        instance = self.home / "instance.json"
        instance.unlink(missing_ok=True)
        t0 = time.monotonic()
        self.proc = self.run_exe("--port", str(preferred), wait=False)
        deadline = t0 + 180
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise AssertionError(f"executable exited early with {self.proc.returncode}")
            if instance.is_file():
                try:
                    data = json.loads(instance.read_text(encoding="utf-8"))
                except ValueError:
                    data = None
                if data:
                    self.port, self.token = data["port"], data["token"]
                    return time.monotonic() - t0
            time.sleep(0.25)
        raise AssertionError("executable did not become ready")

    def stop(self) -> None:
        result = self.run_exe("--stop", wait=True)
        assert result.returncode == 0, result.stdout
        assert self.proc is not None
        self.proc.wait(timeout=60)

    # -- HTTP --------------------------------------------------------------
    def http(self, method: str, path: str, body: bytes | None = None,
             headers: dict | None = None, timeout: float = 300) -> tuple[int, bytes]:
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", data=body, method=method,
            headers={"X-CTD-Token": self.token, **(headers or {})},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def json(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        status, raw = self.http(method, path, body, headers)
        assert status == 200, f"{method} {path} -> {status}: {raw[:300]!r}"
        return json.loads(raw)

    def upload(self, trace: Path, dbcs: list[Path] = ()) -> dict:
        boundary = uuid.uuid4().hex
        out = bytearray()
        for field, path in [("trace", trace), *[("dbcs", d) for d in dbcs]]:
            out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
                    f"filename=\"{path.name}\"\r\nContent-Type: application/octet-stream"
                    "\r\n\r\n").encode()
            out += path.read_bytes() + b"\r\n"
        out += f"--{boundary}--\r\n".encode()
        status, raw = self.http("POST", "/api/import-files", bytes(out),
                                {"Content-Type": f"multipart/form-data; boundary={boundary}"})
        assert status == 200, f"upload {trace.name} -> {status}: {raw[:300]!r}"
        return json.loads(raw)

    def check(self, name: str, ok: bool, detail: object = None) -> None:
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + (f" -- {detail}" if detail else ""),
              flush=True)

    # -- scenario ----------------------------------------------------------
    def fixtures(self) -> dict[str, Path]:
        from blf_fixture import write_sample_blf
        from mf4_fixture import Group, Record, write_mf4

        asc = shutil.copy(FIX / "sample.asc", self.data / "essai é.asc")
        dbc = shutil.copy(FIX / "sample.dbc", self.data / "réseau.dbc")
        trc = shutil.copy(FIX / "sample.trc", self.data / "essai é.trc")
        blf = write_sample_blf(self.data / "essai é.blf")
        mf4 = write_mf4(
            self.data / "essai é.mf4",
            [Group("CAN1_Rx", 64, constants={"BusChannel": 1, "IDE": 0, "Dir": 0}),
             Group("CAN9_Rx", 32, constants={"BusChannel": 9, "IDE": 0, "Dir": 0})],
            [Record("CAN1_Rx", 0.5, 0x100, 8, bytes([0x40, 0x1F, 0x5A, 0, 0, 0, 0, 0])),
             Record("CAN9_Rx", 1.0, 0x7FF, 0, b""),
             Record("CAN1_Rx", 1.5, 0x200, 2, b"\x10\x27")],
            unfinished=True,
        )
        return {"asc": Path(asc), "dbc": Path(dbc), "trc": Path(trc),
                "blf": Path(blf), "mf4": Path(mf4)}

    def run(self) -> None:
        fx = self.fixtures()
        with socket.socket() as blocker:
            blocker.bind(("127.0.0.1", 0))
            blocker.listen()
            taken = blocker.getsockname()[1]
            ready_s = self.start(taken)
            self.check("starts on loopback, skips an occupied port",
                       self.port != taken, {"ready_s": round(ready_s, 1), "port": self.port})

        status = self.json("GET", "/api/status")
        self.check("reports its version", bool(status.get("version")), status.get("version"))

        for kind in ("trc", "blf", "mf4"):
            r = self.upload(fx[kind])
            frames = r["summary"]["frames"]
            self.check(f"imports {kind.upper()}", frames > 0, {"frames": frames})

        r = self.upload(fx["asc"], [fx["dbc"]])
        self.check("imports ASC with DBC", r["summary"]["decoded_frames"] > 0,
                   {"frames": r["summary"]["frames"], "decoded": r["summary"]["decoded_frames"]})
        signals = self.json("GET", "/api/signals")
        sig = next(s for s in signals["signals"] if s.get("present"))
        msg, name = sig["message_name"], sig["signal_name"]
        q = urllib.parse.urlencode({"message": msg, "signal": name, "max_points": 4000})
        series = self.json("GET", f"/api/series?{q}")
        self.check("plots a signal", len(series["t"]) > 0, {"points": len(series["t"])})
        page = self.json("GET", "/api/trace?limit=200")
        self.check("pages the trace", len(page["rows"]) > 0, {"rows": len(page["rows"])})
        cursors = self.json("POST", "/api/cursors",
                            {"signals": [{"message": msg, "signal": name}], "a": 0.0, "b": 0.05})
        self.check("resolves A/B cursors", bool(cursors["a"]) and bool(cursors["b"]))
        report = self.json("GET", "/api/report")
        self.check("builds the report", bool(report))
        status, csv = self.http("POST", "/api/export", json.dumps({
            "signals": [{"message": msg, "signal": name}], "scope": "full", "format": "csv",
        }).encode(), {"Content-Type": "application/json"})
        self.check("exports CSV", status == 200 and len(csv.splitlines()) > 1)
        status, asc = self.http("POST", "/api/export-asc", json.dumps({"scope": "full"}).encode(),
                                {"Content-Type": "application/json"})
        self.check("exports raw ASC", status == 200 and b"End TriggerBlock" in asc)

        native = str(fx["asc"])
        r = self.json("POST", "/api/import", {"trace_path": native, "dbc_paths": [str(fx["dbc"])]})
        self.check("imports a non-ASCII native path", r["summary"]["frames"] > 0,
                   {"trace_path_kept_native": r["trace_path"] == native})

        second = self.run_exe(wait=True)
        self.check("second launch attaches to the running instance",
                   second.returncode == 0 and "already running" in second.stdout,
                   second.stdout.strip().splitlines()[-1:] or None)

        self.stop()
        self.check("--stop stops the service", self.proc.returncode is not None)

        self.start(self.port)
        status = self.json("GET", "/api/status")
        library = self.json("GET", "/api/dbc-library")
        self.check("restart restores analysis and DBC library",
                   status.get("loaded") and len(library.get("dbcs", [])) >= 1,
                   {"trace": status.get("trace_path")})
        self.stop()


def kill_tree(pid: int) -> None:
    """Kill the onefile bootloader *and* its child (``kill()`` would orphan it)."""
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exe", type=Path)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix="ctd smoke é "))
    smoke = Smoke(args.exe.resolve(), work)
    failed = False
    try:
        smoke.run()
    except Exception as exc:  # noqa: BLE001 - reported as a failed check
        smoke.check("scenario completed", False, repr(exc))
        failed = True
    finally:
        if smoke.proc is not None and smoke.proc.poll() is None:
            kill_tree(smoke.proc.pid)
    failed = failed or not all(c["ok"] for c in smoke.checks)
    report = {"exe": args.exe.name, "ok": not failed, "checks": smoke.checks}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not failed:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"Work directory kept for inspection: {work}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
