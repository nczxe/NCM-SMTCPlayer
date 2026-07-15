@echo off
echo ============================================================
echo   SMTC Player - Server Startup
echo ============================================================
echo.

cd /d "%~dp0server"

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python ready
echo.

echo [2/3] Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing dependencies...
    pip install -r requirements.txt
)
echo [OK] Dependencies ready
echo.

echo [3/3] Starting SMTC Player...
echo.
python main.py

pause
