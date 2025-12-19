@echo off
echo Starting Arrears Manager + Zrok...
cd /d "c:\ARREARS MANAGER"

:: 1. Start Flask Server in a new window
echo Starting Flask Server on port 5000...
start "Arrears Manager API" cmd /k "venv\Scripts\activate.bat && python -m flask run --host=0.0.0.0 --port=5000"

:: 2. Start Zrok Share in a new window
echo Starting Zrok Tunnel (Reserved Share)...
echo URL: https://exv6k8sx0vdk.share.zrok.io
start "Zrok Tunnel" cmd /k "c:\Users\DELL\Downloads\zrok_1.1.10_windows_amd64\zrok.exe share reserved exv6k8sx0vdk --headless"

echo.
echo System is ON.
pause
