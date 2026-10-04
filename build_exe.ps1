[CmdletBinding()]
param(
    [string]$AppName = "PulseMusic"
)

$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $AppDir

$Python = Join-Path $AppDir ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    py -m venv .venv
}

$VlcCandidates = @(
    "$env:ProgramFiles\VideoLAN\VLC",
    "${env:ProgramFiles(x86)}\VideoLAN\VLC"
)
$VlcDir = $VlcCandidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ "libvlc.dll") } | Select-Object -First 1
if (-not $VlcDir) {
    throw "VLC runtime was not found. Install VLC desktop on the build machine, then run this script again."
}

& $Python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "Could not install PyInstaller (exit code $LASTEXITCODE)."
}
$OriginalPath = $env:PATH
$env:PATH = ($OriginalPath -split [IO.Path]::PathSeparator | Where-Object { $_ -notmatch "\\poppler\\Library\\bin$" }) -join [IO.Path]::PathSeparator
try {
    & $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name $AppName `
    --distpath "$AppDir\dist" `
    --workpath "$AppDir\build" `
    --specpath "$AppDir\build" `
    --add-data "$VlcDir;vlc" `
    --collect-data yt_dlp `
    --runtime-hook "$AppDir\rthook_qt_runtime.py" `
    music_chat.py
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed (exit code $LASTEXITCODE)."
    }
}
finally {
    $env:PATH = $OriginalPath
}

$Executable = Join-Path $AppDir "dist\$AppName.exe"
if (-not (Test-Path -LiteralPath $Executable)) {
    throw "Build finished without creating $Executable."
}

if ($AppName -eq "PulseMusic") {
    $PackageDir = Join-Path $AppDir "npm-package"
    $PackageAppDir = Join-Path $PackageDir "app"
    New-Item -ItemType Directory -Force -Path $PackageAppDir | Out-Null
    Copy-Item -LiteralPath $Executable -Destination (Join-Path $PackageAppDir "PulseMusic.exe") -Force
    Push-Location $PackageDir
    try {
        & npm pack --pack-destination (Join-Path $AppDir "dist")
        if ($LASTEXITCODE -ne 0) {
            throw "npm pack failed (exit code $LASTEXITCODE)."
        }
    }
    finally {
        Pop-Location
    }
    Write-Host "Created npm installer: $AppDir\dist\spotifynano-1.0.0.tgz"
}
Write-Host "Created: $Executable"
