<#
.SYNOPSIS
  Build the standalone CanTraceDiag Windows x64 executable and its release metadata.

.DESCRIPTION
  Creates an isolated build virtual environment, installs the package with its
  API runtime and a pinned PyInstaller, freezes packaging/windows/CanTraceDiag.spec
  into a single portable .exe and writes, next to it in dist/windows:

    CanTraceDiag-<version>-windows-x64.exe
    CanTraceDiag-<version>-windows-x64.exe.sha256      ("<sha256> *<file name>")
    CanTraceDiag-<version>-windows-x64.provenance.json (version, commit, tag, sha256...)
    THIRD_PARTY_NOTICES.txt

  Used identically by CI (.github/workflows/windows.yml) and by hand. Run it from
  the repository root on Windows x64. It needs Python only on the build machine;
  the resulting executable needs none.

.PARAMETER Python
  Interpreter used to create the build environment (default: "py -3.13").

.PARAMETER Commit
  Source commit recorded in the provenance (default: GITHUB_SHA or git HEAD).

.PARAMETER ReuseEnv
  Keep an existing build environment instead of recreating it (local iteration).

.PARAMETER Tag
  Release tag recorded in the provenance (default: GITHUB_REF_NAME when it is a
  v* tag, else empty).
#>
[CmdletBinding()]
param(
  [string]$Python = "py -3.13",
  [string]$Commit = "",
  [string]$Tag = "",
  [switch]$ReuseEnv
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PyInstallerVersion = "6.16.0"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

function Write-Utf8NoBom([string]$Path, [string]$Text) {
  [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
  & $Exe @Arguments
  if ($LASTEXITCODE -ne 0) { throw "$Exe $($Arguments -join ' ') failed with exit code $LASTEXITCODE" }
}

$version = (Select-String -Path "src\cantracediag\__init__.py" -Pattern '__version__ = "([^"]+)"').Matches[0].Groups[1].Value
if (-not $Commit) {
  if ($env:GITHUB_SHA) { $Commit = $env:GITHUB_SHA }
  else { $Commit = (git -C $Root rev-parse HEAD).Trim() }
}
if (-not $Tag -and $env:GITHUB_REF_NAME -and $env:GITHUB_REF_NAME -like "v*") { $Tag = $env:GITHUB_REF_NAME }
if ($Tag -and $Tag -ne "v$version") { throw "Tag $Tag does not match package version $version" }

$buildDir = Join-Path $Root "build"
$distDir = Join-Path $Root "dist\windows"
$venv = Join-Path $buildDir "venv-windows"
New-Item -ItemType Directory -Force -Path $buildDir, $distDir | Out-Null
Get-ChildItem $distDir -File | Remove-Item -Force

Write-Host "==> Build environment ($Python)"
$pyParts = $Python -split " "
$py = Join-Path $venv "Scripts\python.exe"
if (-not ($ReuseEnv -and (Test-Path $py))) {
  if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }
  $pyArgs = @()
  if ($pyParts.Length -gt 1) { $pyArgs = @($pyParts[1..($pyParts.Length - 1)]) }
  Invoke-Checked $pyParts[0] ($pyArgs + @("-m", "venv", $venv))
  Invoke-Checked $py @("-m", "pip", "install", "--disable-pip-version-check", "-q", "--upgrade", "pip")
}
# Constrained to the pinned set so a rebuild of the same commit bundles the
# same runtime; the package itself is always reinstalled from this checkout.
Invoke-Checked $py @("-m", "pip", "install", "--disable-pip-version-check", "-q",
  "-c", "packaging\windows\constraints.txt", "--force-reinstall", "--no-deps", ".")
Invoke-Checked $py @("-m", "pip", "install", "--disable-pip-version-check", "-q",
  "-c", "packaging\windows\constraints.txt", ".[api]", "pyinstaller==$PyInstallerVersion")

Write-Host "==> Notices and version resource"
Invoke-Checked $py @("packaging\windows\notices.py", (Join-Path $buildDir "THIRD_PARTY_NOTICES.txt"))
$nums = ($version -split "[.-]")[0..2] + @("0")
$tuple = ($nums | ForEach-Object { [int]$_ }) -join ", "
@"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=($tuple), prodvers=($tuple), mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'CanTraceDiag'),
      StringStruct('FileDescription', 'CanTraceDiag local CAN trace diagnostics'),
      StringStruct('FileVersion', '$version'),
      StringStruct('InternalName', 'CanTraceDiag'),
      StringStruct('OriginalFilename', 'CanTraceDiag.exe'),
      StringStruct('ProductName', 'CanTraceDiag'),
      StringStruct('ProductVersion', '$version'),
      StringStruct('Comments', 'source $Commit')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@ | ForEach-Object { Write-Utf8NoBom (Join-Path $buildDir "version_info.txt") $_ }

Write-Host "==> PyInstaller $PyInstallerVersion"
$exeBase = "CanTraceDiag-$version-windows-x64"
$env:CTD_EXE_NAME = $exeBase
Invoke-Checked $py @("-m", "PyInstaller", "--noconfirm", "--clean",
  "--distpath", $distDir, "--workpath", (Join-Path $buildDir "pyinstaller"),
  "packaging\windows\CanTraceDiag.spec")

$exe = Join-Path $distDir "$exeBase.exe"
if (-not (Test-Path $exe)) { throw "Expected $exe was not produced" }
Copy-Item (Join-Path $buildDir "THIRD_PARTY_NOTICES.txt") $distDir

Write-Host "==> Checksum and provenance"
$sha = (Get-FileHash -Algorithm SHA256 $exe).Hash.ToLowerInvariant()
Write-Utf8NoBom (Join-Path $distDir "$exeBase.exe.sha256") "$sha *$exeBase.exe`n"
$pyVersion = (& $py -c "import sys; print(sys.version.split()[0])").Trim()
$provenance = [ordered]@{
  schema       = 1
  name         = "CanTraceDiag"
  version      = $version
  tag          = $Tag
  commit       = $Commit
  platform     = "windows"
  architecture = "x64"
  asset        = "$exeBase.exe"
  sha256       = $sha
  size         = (Get-Item $exe).Length
  python       = $pyVersion
  pyinstaller  = $PyInstallerVersion
  signed       = $false
  built_at     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  builder      = $(if ($env:GITHUB_ACTIONS) { "github-actions" } else { "local" })
}
Write-Utf8NoBom (Join-Path $distDir "$exeBase.provenance.json") ($provenance | ConvertTo-Json)

Get-ChildItem $distDir | Format-Table Name, Length
Write-Host "Built $exe ($sha)"
