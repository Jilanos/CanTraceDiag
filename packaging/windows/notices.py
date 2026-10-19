"""Write THIRD_PARTY_NOTICES.txt for the bundled runtime (req_034 AC9).

Lists every distribution installed in the build environment (the frozen
executable bundles a subset of them) with its version, declared license and
home page, followed by the LGPL relinking note for asammdf and python-can.
"""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

BUILD_ONLY = {"pyinstaller", "pyinstaller-hooks-contrib", "pip", "setuptools", "wheel",
              "altgraph", "pefile", "pywin32-ctypes", "packaging"}

LGPL_NOTE = """
LGPL components
---------------
asammdf (LGPL-3.0-or-later) and python-can (LGPL-3.0-only) are used unmodified
as libraries. Their complete corresponding source is available from PyPI at the
versions listed above. The executable is built by PyInstaller from the public
CanTraceDiag source (packaging/windows/build.ps1): you can rebuild it with a
modified version of either library by installing it into the build environment
and re-running that script.
"""


def license_of(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    expr = meta.get("License-Expression")
    if expr:
        return expr
    classifiers = [c.split("::")[-1].strip() for c in meta.get_all("Classifier") or []
                   if c.startswith("License ::")]
    if classifiers:
        return "; ".join(classifiers)
    raw = (meta.get("License") or "").strip().splitlines()
    return raw[0][:80] if raw else "see project"


def main(out: Path) -> None:
    rows = []
    for dist in metadata.distributions():
        name = dist.metadata["Name"]
        if not name or name.lower() in BUILD_ONLY:
            continue
        home = dist.metadata.get("Home-page") or ""
        if not home:
            for url in dist.metadata.get_all("Project-URL") or []:
                home = url.split(",", 1)[-1].strip()
                break
        rows.append((name.lower(), name, dist.version, license_of(dist), home))
    rows.sort()
    lines = [
        "CanTraceDiag for Windows -- third-party runtime notices",
        "=======================================================",
        "",
        f"Python {sys.version.split()[0]} (PSF-2.0) is embedded by PyInstaller.",
        "",
    ]
    for _, name, version, lic, home in rows:
        lines.append(f"{name} {version} -- {lic}" + (f" -- {home}" if home else ""))
    lines.append(LGPL_NOTE)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
