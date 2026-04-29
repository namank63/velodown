@echo off
echo ========================================
echo   Video Downloader - Stopping Services
echo ========================================

echo Stopping Python Backend...
taskkill /F /IM python.exe /T 2>nul

echo Stopping Ngrok...
taskkill /F /IM ngrok.exe /T 2>nul

:: Note: This kills ALL python processes. If you have other python apps running, 
:: you might want to be more specific, but for a local setup this is the most effective.

echo.
echo All services stopped.
pause
