@echo off
SETLOCAL EnableDelayedExpansion

echo ========================================
echo   Video Downloader - Starting Services
echo ========================================

:: 1. Navigate to the project root
cd /d "%~dp0"

:: 2. Ensure logs directory exists
if not exist "backend\logs" mkdir "backend\logs"

:: 3. Build the frontend (Production mode)
echo [1/3] Building frontend...
cd frontend
call npm.cmd run build
if %ERRORLEVEL% NEQ 0 (
    echo Error: Frontend build failed.
    pause
    exit /b %ERRORLEVEL%
)
cd ..

:: 4. Start the Backend in a separate window
echo [2/3] Starting Backend (Port 8000)...
start "VideoDown-Backend" cmd /c "python backend\main.py"

:: 5. Wait a few seconds for backend to initialize
timeout /t 3 /nobreak >nul

:: 6. Start Ngrok in a separate window
echo [3/3] Starting Ngrok Tunnel...
echo Make sure ngrok is installed and authenticated!
start "VideoDown-Ngrok" cmd /c "ngrok http 8000"

echo.
echo ========================================
echo   SERVICES ARE RUNNING
echo   Local: http://localhost:8000
echo   Remote: Check the Ngrok window for URL
echo ========================================
echo Press any key to see the stop instructions...
pause
