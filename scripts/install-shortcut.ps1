# ===================================================================
# Install a Desktop shortcut that launches CanTraceDiag in one click.
#
# Run once per Windows machine (PowerShell, from the repo's scripts dir):
#
#   powershell -ExecutionPolicy Bypass -File .\install-shortcut.ps1
#
# It detects the WSL path of this repository, writes it into a private
# copy of the launcher, and drops a "CanTraceDiag" shortcut on your
# Desktop. Re-run it after moving the clone.
# ===================================================================

$ErrorActionPreference = "Stop"

# Repo root = parent of this scripts directory.
$ScriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptsDir

# Windows path -> WSL path (C:\Users\me\CanTraceDiag -> /mnt/c/Users/me/CanTraceDiag).
function Convert-ToWslPath([string]$WinPath) {
    $resolved = Resolve-Path $WinPath
    $full = $resolved.ProviderPath
    if (-not $full) {
        $full = $resolved.Path -replace '^Microsoft\.PowerShell\.Core\\FileSystem::', ''
    }
    if ($full -match '^([A-Za-z]):\\(.*)$') {
        $drive = $matches[1].ToLower()
        $rest = $matches[2] -replace '\\', '/'
        return "/mnt/$drive/$rest"
    }
    # Already a UNC \\wsl.localhost\... path: strip host + distro.
    if ($full -match '^\\\\wsl(?:\.localhost|\$)\\[^\\]+\\(.*)$') {
        return "/" + ($matches[1] -replace '\\', '/')
    }
    throw "Could not map '$full' to a WSL path. Run this from inside the repo."
}

$WslDir = Convert-ToWslPath $RepoRoot
Write-Host "Repository (WSL path): $WslDir"

# Materialize a launcher with the real repo path baked in.
$TemplatePath = Join-Path $ScriptsDir "CanTraceDiag.cmd"
$LauncherPath = Join-Path $RepoRoot "CanTraceDiag.local.cmd"
(Get-Content $TemplatePath -Raw).Replace("__CTD_DIR__", $WslDir) | Set-Content -Path $LauncherPath -Encoding ASCII
Write-Host "Launcher written: $LauncherPath"

# Explorer is unreliable at loading shortcut icons from \\wsl.localhost paths.
# Keep a Windows-local copy of the icon and point the shortcut to that file.
$LocalAppDir = Join-Path $env:LOCALAPPDATA "CanTraceDiag"
New-Item -ItemType Directory -Force -Path $LocalAppDir | Out-Null
$RepoIconPath = Join-Path $RepoRoot "src\cantracediag\web\app-icon.ico"
$LocalIconPath = Join-Path $LocalAppDir "app-icon.ico"
if (Test-Path $RepoIconPath) {
    Copy-Item -Force $RepoIconPath $LocalIconPath
    Write-Host "Icon copied: $LocalIconPath"
}

# Create the Desktop shortcut.
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "CanTraceDiag.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $LauncherPath
$Shortcut.WorkingDirectory = $RepoRoot
if (Test-Path $LocalIconPath) {
    $Shortcut.IconLocation = "$LocalIconPath,0"
}
$Shortcut.WindowStyle = 7          # minimized
$Shortcut.Description = "Launch CanTraceDiag (WSL server + Windows browser)"
$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath"
Write-Host "Done. Double-click 'CanTraceDiag' on your Desktop to start."
