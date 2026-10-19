<#
.SYNOPSIS
  Download (once), verify and start the CanTraceDiag executable matching this checkout.

.DESCRIPTION
  Invoked by CanTraceDiag.cmd at the repository root. Resolution is deterministic
  (req_034 AC6):

  1. The checkout version is read from src\cantracediag\__init__.py and its
     commit from the .git metadata (no git installation needed).
  2. The release is v<version> on the canonical origin. Its provenance must name
     that version and tag, the x64 architecture and -- when the checkout commit
     is known -- exactly that commit. A development commit without a published
     binary fails with instructions; the latest release is never substituted.
  3. The executable is downloaded to a temporary file and its SHA-256 must equal
     both the published .sha256 file and the provenance before it is moved into
     the per-user cache (%LOCALAPPDATA%\CanTraceDiag\releases\v<version>).
  4. Later launches re-hash the cached executable against the cached provenance
     and run offline. Nothing unverified is ever executed.

  Arguments after the script name are passed to the executable (e.g. --stop).

.PARAMETER Release
  Explicitly run a published release tag (e.g. v1.4.0) instead of the one that
  matches this checkout.
#>
[CmdletBinding()]
param(
  [string]$Release = "",
  [Parameter(ValueFromRemainingArguments = $true)][string[]]$AppArgs = @()
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"  # Windows PowerShell's progress bar slows downloads

$Repository = "Jilanos/CanTraceDiag"
$ReleaseBase = if ($env:CTD_RELEASE_BASE) { $env:CTD_RELEASE_BASE.TrimEnd("/") } `
               else { "https://github.com/$Repository/releases/download" }
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).ProviderPath
$CacheRoot = if ($env:CTD_LAUNCHER_CACHE) { $env:CTD_LAUNCHER_CACHE } `
             else { Join-Path $env:LOCALAPPDATA "CanTraceDiag\releases" }

function Fail([string]$Message) { throw $Message }

function Get-CheckoutVersion {
  $init = Join-Path $Root "src\cantracediag\__init__.py"
  if (-not (Test-Path -LiteralPath $init)) { Fail "This folder is not a CanTraceDiag checkout ($init is missing)." }
  $m = Select-String -LiteralPath $init -Pattern '__version__ = "([^"]+)"'
  if (-not $m) { Fail "Could not read the CanTraceDiag version from $init." }
  return $m.Matches[0].Groups[1].Value
}

function Get-CheckoutCommit {
  # Returns the 40-hex HEAD commit, or $null when there is no git metadata
  # (e.g. a source archive). Reads .git directly so git.exe is not required.
  $git = Join-Path $Root ".git"
  if (Test-Path -LiteralPath $git -PathType Leaf) {
    $pointer = (Get-Content -LiteralPath $git -Raw).Trim()
    if ($pointer -notmatch '^gitdir:\s*(.+)$') { return $null }
    $git = $Matches[1]
    if (-not [System.IO.Path]::IsPathRooted($git)) { $git = Join-Path $Root $git }
  }
  $headFile = Join-Path $git "HEAD"
  if (-not (Test-Path -LiteralPath $headFile)) { return $null }
  $head = (Get-Content -LiteralPath $headFile -Raw).Trim()
  if ($head -match '^[0-9a-f]{40}$') { return $head }
  if ($head -notmatch '^ref:\s*(.+)$') { return $null }
  $ref = $Matches[1].Trim()
  $common = $git
  $commonFile = Join-Path $git "commondir"
  if (Test-Path -LiteralPath $commonFile) {
    $common = Join-Path $git ((Get-Content -LiteralPath $commonFile -Raw).Trim())
  }
  foreach ($dir in @($git, $common)) {
    $loose = Join-Path $dir ($ref -replace "/", "\")
    if (Test-Path -LiteralPath $loose) { return (Get-Content -LiteralPath $loose -Raw).Trim() }
  }
  $packed = Join-Path $common "packed-refs"
  if (Test-Path -LiteralPath $packed) {
    foreach ($line in Get-Content -LiteralPath $packed) {
      if ($line -match "^([0-9a-f]{40}) $([regex]::Escape($ref))$") { return $Matches[1] }
    }
  }
  return $null
}

function Assert-X64 {
  $arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
  if ($arch -ne "AMD64") {
    Fail "CanTraceDiag for Windows is published for x64 only; this machine reports '$arch'."
  }
}

function Get-Sha256([string]$Path) {
  # .NET directly rather than Get-FileHash: started from PowerShell 7, Windows
  # PowerShell can inherit a PSModulePath where that command does not load.
  $stream = [System.IO.File]::OpenRead($Path)
  try {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $bytes = $sha.ComputeHash($stream) } finally { $sha.Dispose() }
  } finally { $stream.Dispose() }
  return (-join ($bytes | ForEach-Object { $_.ToString("x2") }))
}

function Read-Json([string]$Path) {
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8) | ConvertFrom-Json
}

function Test-Provenance($Prov, [string]$Version, [string]$Tag, [string]$Commit, [string]$Asset) {
  # Returns $null when acceptable, else the reason.
  if ($Prov.name -ne "CanTraceDiag") { return "it is not a CanTraceDiag build" }
  if ($Prov.version -ne $Version) { return "it is version $($Prov.version), not $Version" }
  if ($Prov.tag -ne $Tag) { return "it was built for tag '$($Prov.tag)', not $Tag" }
  if ($Prov.platform -ne "windows" -or $Prov.architecture -ne "x64") {
    return "it targets $($Prov.platform)/$($Prov.architecture), not windows/x64"
  }
  if ($Prov.asset -ne $Asset) { return "it describes '$($Prov.asset)', not $Asset" }
  if ($Prov.sha256 -notmatch '^[0-9a-f]{64}$') { return "its SHA-256 is malformed" }
  if ($Commit -and $Prov.commit -ne $Commit) {
    return "it was built from commit $($Prov.commit), not this checkout's $Commit"
  }
  return $null
}

function Invoke-Download([string]$Url, [string]$Destination) {
  try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination -TimeoutSec 600
  } catch {
    $status = $null
    if ($_.Exception.PSObject.Properties["Response"] -and $_.Exception.Response) {
      $status = [int]$_.Exception.Response.StatusCode
    }
    if ($status -eq 404) { return 404 }
    Fail "Download failed for $Url ($($_.Exception.Message)). Check the network connection and retry."
  }
  return 200
}

function Resolve-Executable([string]$Version, [string]$Tag, [string]$Commit) {
  $base = "CanTraceDiag-$Version-windows-x64"
  $asset = "$base.exe"
  $cacheDir = Join-Path $CacheRoot $Tag
  $cachedExe = Join-Path $cacheDir $asset
  $cachedProv = Join-Path $cacheDir "$base.provenance.json"

  # 1. Verified cache: works offline.
  if ((Test-Path -LiteralPath $cachedExe) -and (Test-Path -LiteralPath $cachedProv)) {
    $prov = Read-Json $cachedProv
    $reason = Test-Provenance $prov $Version $Tag $Commit $asset
    if (-not $reason -and (Get-Sha256 $cachedExe) -eq $prov.sha256) {
      Write-Host "Using verified cached $asset"
      return $cachedExe
    }
    Write-Host "Discarding cached $asset (it no longer verifies)."
    Remove-Item -LiteralPath $cacheDir -Recurse -Force
  }

  # 2. Download into a staging folder; only verified files reach the cache.
  New-Item -ItemType Directory -Force -Path $CacheRoot | Out-Null
  $staging = Join-Path $CacheRoot (".download-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $staging | Out-Null
  try {
    $url = "$ReleaseBase/$Tag"
    Write-Host "Resolving release $Tag from $url"
    $provPath = Join-Path $staging "$base.provenance.json"
    if ((Invoke-Download "$url/$base.provenance.json" $provPath) -eq 404) {
      Fail ("No published Windows executable for $Tag. Use a checkout of a published release " +
            "tag (git checkout vX.Y.Z, see https://github.com/$Repository/releases) or run " +
            "CanTraceDiag.cmd -Release vX.Y.Z.")
    }
    $prov = Read-Json $provPath
    $reason = Test-Provenance $prov $Version $Tag $Commit $asset
    if ($reason) {
      Fail ("The published $Tag executable does not match this checkout: $reason. This is a " +
            "development checkout without a published binary. Run 'git checkout $Tag' (or " +
            "another published release tag) and start CanTraceDiag.cmd again, or run " +
            "CanTraceDiag.cmd -Release $Tag.")
    }
    $shaPath = Join-Path $staging "$asset.sha256"
    if ((Invoke-Download "$url/$asset.sha256" $shaPath) -eq 404) { Fail "Release $Tag has no $asset.sha256." }
    $published = ((Get-Content -LiteralPath $shaPath -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
    if ($published -ne $prov.sha256) { Fail "Release $Tag checksum file and provenance disagree; refusing to run it." }

    $exePath = Join-Path $staging "$asset.partial"
    Write-Host "Downloading $asset ($([math]::Round($prov.size / 1MB)) MiB)..."
    if ((Invoke-Download "$url/$asset" $exePath) -eq 404) { Fail "Release $Tag has no $asset." }
    $actual = Get-Sha256 $exePath
    if ($actual -ne $prov.sha256) {
      Fail "Downloaded $asset is incomplete or altered (SHA-256 $actual, expected $($prov.sha256)); it was not run. Retry the download."
    }

    if (Test-Path -LiteralPath $cacheDir) { Remove-Item -LiteralPath $cacheDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
    Move-Item -LiteralPath $provPath -Destination $cachedProv
    Move-Item -LiteralPath $exePath -Destination $cachedExe
    Write-Host "Verified $asset (SHA-256 $actual)."
    return $cachedExe
  } finally {
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
  }
}

try {
  Assert-X64
  $version = Get-CheckoutVersion
  $commit = Get-CheckoutCommit
  if ($Release) {
    if ($Release -notmatch '^v(\d+\.\d+\.\d+.*)$') { Fail "-Release expects a tag like v1.4.0, got '$Release'." }
    $tag = $Release
    $version = $Matches[1]
    $commit = $null  # explicit choice: the release no longer has to match this checkout
  } else {
    $tag = "v$version"
    if (-not $commit) { Write-Host "No git metadata found: matching the release by version ($tag) only." }
  }
  $exe = Resolve-Executable $version $tag $commit
  & $exe @AppArgs
  exit $LASTEXITCODE
} catch {
  Write-Host ""
  Write-Host "CanTraceDiag could not start: $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
