@echo off
echo Starting Arrears Manager API Server...
cd /d "c:\ARREARS MANAGER"

:: Activate virtual environment if it exists, otherwise assume global python
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Set environment variables for production-like local run
set FLASK_APP=app.py
set FLASK_ENV=production
set FLASK_DEBUG=0

:: Run the server on 0.0.0.0 to be finding on local network
:: Using python directly for simplicity, but gunicorn/waitress is better for "real" prod
:: For Windows, 'waitress' is recommended over gunicorn. Let's try direct flask first.
echo Server running on http://0.0.0.0:5000
python -m flask run --host=0.0.0.0 --port=5000

pause
