"""Exercise CanTraceDiag.cmd + launcher.ps1 against a local fake release (req_034 AC6).

Builds throwaway checkouts (paths with spaces and non-ASCII characters) holding
only what the launcher reads -- CanTraceDiag.cmd, packaging/windows/launcher.ps1,
src/cantracediag/__init__.py and .git metadata -- and serves release assets for
the real executable from a loopback HTTP server via ``CTD_RELEASE_BASE``. Each
scenario runs ``CanTraceDiag.cmd --version`` through cmd.exe, so a successful
launch is the executable printing its own version.

    python packaging/windows/test_launcher.py dist/windows/CanTraceDiag-<version>-windows-x64.exe

Optional ``--unc-root \\\\wsl.localhost\\Ubuntu\\...`` also runs the matching
scenario from a checkout on that UNC share.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "0123456789abcdef0123456789abcdef01234567"
OTHER = "fedcba9876543210fedcba9876543210fedcba98"


class Release:
    """A served release directory: <root>/<tag>/<assets>."""

    def __init__(self, root: Path, exe: Path, version: str) -> None:
        self.root = root
        self.exe = exe
        self.version = version
        self.tag = f"v{version}"
        self.base = f"CanTraceDiag-{version}-windows-x64"

    def publish(self, *, commit: str = COMMIT, arch: str = "x64", payload: bytes | None = None,
                published_sha: str | None = None, omit: tuple[str, ...] = ()) -> None:
        folder = self.root / self.tag
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        data = self.exe.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        served = data if payload is None else payload
        prov = {"schema": 1, "name": "CanTraceDiag", "version": self.version, "tag": self.tag,
                "commit": commit, "platform": "windows", "architecture": arch,
                "asset": f"{self.base}.exe", "sha256": sha, "size": len(data),
                "signed": False}
        files = {
            f"{self.base}.exe": served,
            f"{self.base}.exe.sha256": f"{published_sha or sha} *{self.base}.exe\n".encode(),
            f"{self.base}.provenance.json": json.dumps(prov).encode(),
        }
        for name, content in files.items():
            if name not in omit:
                (folder / name).write_bytes(content)


class Server:
    def __init__(self, root: Path) -> None:
        handler = functools.partial(_QuietHandler, directory=str(root))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.hits: list[str] = []
        _QuietHandler.hits = self.hits

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    hits: list[str] = []

    def log_message(self, *args) -> None:
        pass

    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        _QuietHandler.hits.append(self.path)
        super().do_GET()


def make_checkout(where: Path, version: str, head: str | None, packed: bool = False) -> Path:
    (where / "packaging" / "windows").mkdir(parents=True)
    (where / "src" / "cantracediag").mkdir(parents=True)
    shutil.copy(ROOT / "CanTraceDiag.cmd", where / "CanTraceDiag.cmd")
    shutil.copy(ROOT / "packaging" / "windows" / "launcher.ps1",
                where / "packaging" / "windows" / "launcher.ps1")
    (where / "src" / "cantracediag" / "__init__.py").write_text(f'__version__ = "{version}"\n')
    if head is not None:
        git = where / ".git"
        (git / "refs" / "heads").mkdir(parents=True)
        (git / "HEAD").write_text("ref: refs/heads/main\n")
        if packed:
            (git / "packed-refs").write_text(f"# pack-refs\n{head} refs/heads/main\n")
        else:
            (git / "refs" / "heads" / "main").write_text(head + "\n")
    return where


def run(checkout: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    cmd = ["cmd.exe", "/d", "/c", str(checkout / "CanTraceDiag.cmd"), *args]
    return subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600,
                          input="\n", encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exe", type=Path)
    parser.add_argument("--unc-root", default=None)
    args = parser.parse_args()
    exe = args.exe.resolve()
    version = exe.name.split("-")[1]

    work = Path(tempfile.mkdtemp(prefix="ctd launcher é "))
    release = Release(work / "release", exe, version)
    server = Server(work / "release")
    cache = work / "cache ü"
    env = {**os.environ, "CTD_RELEASE_BASE": server.url, "CTD_LAUNCHER_CACHE": str(cache)}
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, out: str = "") -> None:
        results.append((name, ok, out))
        print(("PASS " if ok else "FAIL ") + name, flush=True)
        if not ok:
            print(out[-1500:])

    def cached_exe() -> Path:
        return cache / release.tag / f"{release.base}.exe"

    expected = f"CanTraceDiag {version}"
    co = make_checkout(work / "clone with spaces ñ", version, COMMIT)

    # Missing release -> actionable failure, nothing executed.
    r = run(co, env, "--version")
    check("missing release fails clearly",
          r.returncode == 2 and "No published Windows executable" in r.stdout
          and expected not in r.stdout, r.stdout)

    # Development commit -> refuses, never falls back to another binary.
    release.publish(commit=OTHER)
    server.hits.clear()
    r = run(co, env, "--version")
    check("development commit refused with checkout instructions",
          r.returncode == 2 and f"git checkout {release.tag}" in r.stdout
          and not any(h.endswith(".exe") for h in server.hits), r.stdout)

    # Wrong architecture in provenance.
    release.publish(arch="arm64")
    r = run(co, env, "--version")
    check("wrong architecture refused", r.returncode == 2 and "windows/x64" in r.stdout, r.stdout)

    # Checksum file disagrees with provenance.
    release.publish(published_sha="0" * 64)
    r = run(co, env, "--version")
    check("checksum/provenance mismatch refused",
          r.returncode == 2 and "disagree" in r.stdout, r.stdout)

    # Incomplete download (truncated executable) -> hash mismatch, not run, not cached.
    release.publish(payload=exe.read_bytes()[: 1024 * 1024])
    r = run(co, env, "--version")
    check("incomplete download refused and not cached",
          r.returncode == 2 and "incomplete or altered" in r.stdout and not cached_exe().exists(),
          r.stdout)

    # Altered executable with valid metadata.
    tampered = bytearray(exe.read_bytes())
    tampered[-1] ^= 0xFF
    release.publish(payload=bytes(tampered))
    r = run(co, env, "--version")
    check("altered executable refused", r.returncode == 2 and not cached_exe().exists(), r.stdout)

    # Matching release -> download, verify, run.
    release.publish()
    r = run(co, env, "--version")
    check("matching release downloads, verifies and runs",
          r.returncode == 0 and expected in r.stdout and cached_exe().is_file(), r.stdout)

    # Offline: server gone, verified cache reused.
    server.stop()
    r = run(co, env, "--version")
    check("offline launch reuses verified cache",
          r.returncode == 0 and "Using verified cached" in r.stdout and expected in r.stdout,
          r.stdout)

    # Corrupted cache while offline -> discarded, fails without running it.
    data = bytearray(cached_exe().read_bytes())
    data[100] ^= 0xFF
    cached_exe().write_bytes(bytes(data))
    r = run(co, env, "--version")
    check("corrupted cache is discarded, never executed",
          r.returncode == 2 and "Discarding cached" in r.stdout and expected not in r.stdout,
          r.stdout)

    # Network failure (nothing listening) is reported, not hidden.
    check("network failure is actionable", "Download failed" in r.stdout, r.stdout)

    server = Server(work / "release")
    env["CTD_RELEASE_BASE"] = server.url

    # packed-refs checkout and explicit -Release on a dev checkout.
    co2 = make_checkout(work / "packed clone", version, COMMIT, packed=True)
    r = run(co2, env, "--version")
    check("packed-refs checkout resolves its commit", r.returncode == 0 and expected in r.stdout,
          r.stdout)
    co3 = make_checkout(work / "dev clone", "9.9.9", OTHER)
    r = run(co3, env, "-Release", release.tag, "--version")
    check("explicit -Release runs the chosen published tag",
          r.returncode == 0 and expected in r.stdout, r.stdout)

    if args.unc_root:
        unc = Path(args.unc_root) / f"ctd-launcher-{os.getpid()}"
        try:
            co4 = make_checkout(unc, version, COMMIT)
            shutil.rmtree(cache, ignore_errors=True)
            r = run(co4, env, "--version")
            check("checkout on a UNC share (WSL) works without WSL",
                  r.returncode == 0 and expected in r.stdout, r.stdout)
        finally:
            shutil.rmtree(unc, ignore_errors=True)

    server.stop()
    failed = [n for n, ok, _ in results if not ok]
    if not failed:
        shutil.rmtree(work, ignore_errors=True)
    print(f"{len(results) - len(failed)}/{len(results)} launcher checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
