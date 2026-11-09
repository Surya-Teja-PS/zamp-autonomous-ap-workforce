# ===================================================
#   ZAMP AGENT OS — Autonomous AP Workforce
#   "AI reads. Deterministic Rules decide. Humans handle exceptions."
# ===================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Locate the real Python executable
$PY = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $PY)) {
    $PY = "$env:LOCALAPPDATA\Python\bin\python.exe"
}
if (-not (Test-Path $PY)) {
    $PY = "python"
}

Write-Host "[1/2] Initializing database with Zamp Case Study records..." -ForegroundColor Cyan
& $PY db\seed_zamp.py

Write-Host ""
Write-Host "[2/2] Launching Zamp Agent OS Web Application..." -ForegroundColor Green
Write-Host "Point your browser to: http://localhost:5000" -ForegroundColor Yellow
& $PY server.py
