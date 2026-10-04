$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $AppDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

if (-not (Test-Path "$env:ProgramFiles\VideoLAN\VLC\vlc.exe") -and -not (Test-Path "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe")) {
    Write-Error "VLC Media Player was not found. Install the desktop VLC app, then run this script again."
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe music_chat.py
