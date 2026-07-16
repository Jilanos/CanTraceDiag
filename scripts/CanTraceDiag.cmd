@echo off
REM ===================================================================
REM CanTraceDiag launcher for Windows + WSL.
REM
REM Double-click this file (or a shortcut to it) to start CanTraceDiag:
REM it launches the server inside your default WSL distro and opens the
REM UI in your Windows browser. No terminal, no typed commands.
REM
REM The repository path inside WSL is configured below. Adjust CTD_DIR
REM if your clone lives elsewhere, or use scripts\install-shortcut.ps1
REM which fills it in automatically.
REM ===================================================================

set "CTD_DIR=%~1"
if "%CTD_DIR%"=="" set "CTD_DIR=__CTD_DIR__"

wsl.exe -e bash -lc "cd '%CTD_DIR%' && (.venv/bin/cantracediag serve --open || PYTHONPATH=src python3 -m cantracediag.cli serve --open)"
