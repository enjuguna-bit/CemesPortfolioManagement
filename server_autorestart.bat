@echo off
REM Flask Server Auto-restart Script
REM This script ensures the server restarts cleanly

cd /d "c:\ARREARS MANAGER"

:RESTART_LOOP
echo ========================================
echo Starting Arrears Manager Flask Server
echo Time: %date% %time%
echo ========================================

REM Kill any existing Python processes running the server
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Flask*" >nul 2>&1

REM Start the server
python app.py

REM If server crashes, wait 5 seconds before restart
timeout /t 5 /nobreak >nul

REM Loop back to restart
goto RESTART_LOOP
