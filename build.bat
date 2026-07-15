@echo off
title Build SMTCPlayer EXE

echo ============================================================
echo   SMTC Player - Build Tool
echo ============================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found.
    pause
    exit /b 1
)
echo [OK] Python ready
echo.

echo [2/4] Installing PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing PyInstaller...
    pip install pyinstaller
)
echo [OK] PyInstaller ready
echo.

echo [3/4] Installing project dependencies...
pip install -r server\requirements.txt
echo [OK] Dependencies ready
echo.

echo [4/4] Building SMTCPlayer.exe ...
echo.

pyinstaller --clean --noconfirm SMTCPlayer.spec

if errorlevel 1 (
    echo.
    echo [Error] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build complete!
echo   Output: dist\SMTCPlayer.exe
echo ============================================================
echo.
echo   Usage:
echo     dist\SMTCPlayer.exe                 (default port 8888, GUI)
echo     dist\SMTCPlayer.exe --port 9999     (custom port, GUI)
echo     dist\SMTCPlayer.exe --port 9999 --save-port   (save port)
echo     dist\SMTCPlayer.exe --no-gui        (Flask only, no GUI)
echo.
echo   Config: create config.json alongside the exe
echo     { "port": 9999 }
echo.
pause
