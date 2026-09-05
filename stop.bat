@echo off
title Stop Tesseract
cd /d "%~dp0"

echo ================================================================
echo               STOPPING ALL TESSERACT SERVICES
echo ================================================================
echo Releasing ports 9700, 9701, 9702...

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 9700,9701,9702 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { $id = $_; Write-Host \"  [-] Terminating process $id...\"; Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }"

echo.
echo [OK] All Tesseract services and ports have been cleanly stopped.
echo ================================================================
ping 127.0.0.1 -n 2 >nul
exit /b 0
