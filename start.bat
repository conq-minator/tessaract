@echo off
title Tesseract System Launcher
cd /d "%~dp0"

echo ================================================================
echo                     STARTING TESSERACT SYSTEM
echo ================================================================

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.11+ or add it to your environment PATH.
    pause
    exit /b 1
)

python -u scripts\run_tesseract.py %*

rem Double-check cleanup in case CMD window was interrupted
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 9700,9701,9702 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul

echo.
echo Tesseract session ended.
exit /b 0
