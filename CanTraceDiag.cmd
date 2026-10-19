@echo off
setlocal
REM CanTraceDiag for Windows: double-click to start.
REM Downloads the executable published for this checkout (once), verifies it
REM and runs it. See README "Windows standalone". Arguments are passed through,
REM e.g. "CanTraceDiag.cmd --stop" or "CanTraceDiag.cmd -Release v1.4.0".
REM PowerShell 7 exports a PSModulePath that breaks Windows PowerShell modules.
set "PSModulePath="
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0packaging\windows\launcher.ps1" %*
set "CTD_EXIT=%ERRORLEVEL%"
if "%CTD_EXIT%"=="2" pause
exit /b %CTD_EXIT%
