@echo off
title Homesteader Asset Kit // Server (Port 8088)
echo ========================================================
echo       Homesteader Master Asset Kit Server
echo       (Features 1-Click Delete & Rename Asset)
echo ========================================================
echo.

netstat -ano | findstr :8088 | findstr LISTENING >nul
if %ERRORLEVEL% equ 0 (
    echo Asset Kit server is already active on port 8088.
    echo Opening browser to http://localhost:8088/index.html...
    start http://localhost:8088/index.html
    exit /b 0
)

echo Starting local Asset Kit server on port 8088...
echo Opening browser to http://localhost:8088/index.html...
echo.
start http://localhost:8088/index.html

:loop
python ..\tools\server.py 8088
echo.
echo Server stopped. Restarting in 1 second... (Press Ctrl+C to exit)
timeout /t 1 /nobreak >nul
goto loop
