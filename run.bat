@echo off
setlocal
echo ===================================================
echo   ZAMP AGENT OS — Autonomous AP Workforce
echo   "AI reads. Deterministic Rules decide. Humans handle exceptions."
echo ===================================================
echo.

cd /d "%~dp0"

REM Prioritize the real Python installation to bypass WindowsApps store stub
set "PY="
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
) else if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY=%LOCALAPPDATA%\Python\bin\python.exe"
) else (
    set "PY=python"
)

echo [1/2] Initializing database with Zamp Case Study records...
"%PY%" db\seed_zamp.py
if %errorlevel% neq 0 (
    echo [ERROR] Database initialization failed.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] Launching Zamp Agent OS Web Application...
echo Point your browser to: http://localhost:5000
"%PY%" server.py
