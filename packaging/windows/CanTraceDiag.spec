# PyInstaller spec for the standalone Windows executable (req_034 AC5).
# Built by packaging/windows/build.ps1; run from the repository root.
# ruff: noqa
import os
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

ROOT = Path(SPECPATH).parents[1]
NAME = os.environ.get("CTD_EXE_NAME", "CanTraceDiag")

datas = collect_data_files("cantracediag")  # static UI: cantracediag/web/**
datas += collect_data_files("cantools")
datas += collect_data_files("asammdf")
datas += collect_data_files("canmatrix")
# Packages that read their own version through importlib.metadata at runtime.
for dist in ("cantracediag", "asammdf", "python-can", "cantools", "fastapi", "uvicorn",
             "starlette", "pydantic", "duckdb", "pyarrow", "pandas", "numpy"):
    datas += copy_metadata(dist)
notices = ROOT / "build" / "THIRD_PARTY_NOTICES.txt"
if notices.is_file():
    datas.append((str(notices), "."))

hiddenimports = []
binaries = []
# chardet (an asammdf dependency) ships mypyc-compiled ``*__mypyc`` extension
# modules and model .bin files that static analysis does not find; without them
# ``import asammdf`` fails in the frozen app and MF4 import is lost.
for pkg in ("chardet",):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden
for pkg in ("cantracediag", "uvicorn", "cantools", "can.io", "asammdf.blocks", "canmatrix",
            "python_multipart"):
    hiddenimports += collect_submodules(pkg)

a = Analysis(
    [str(ROOT / "packaging" / "windows" / "entry.py")],
    pathex=[str(ROOT / "src")],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=[
        # GUI/plotting stacks pulled in optionally by asammdf/canmatrix; the
        # executable serves a browser UI and never imports them.
        "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "pyqtgraph", "matplotlib",
        "IPython", "jupyter", "notebook", "pytest", "playwright",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=NAME,
    icon=str(ROOT / "src" / "cantracediag" / "web" / "app-icon.ico"),
    version=str(ROOT / "build" / "version_info.txt"),
    console=True,  # the console window is the visible stop action
    upx=False,
    disable_windowed_traceback=False,
    target_arch="x86_64",
)
