@echo off
chcp 65001 >nul 2>&1
title SMTC Player Beta

echo ============================================================
echo   SMTC Player (Beta)
echo   New: Song Search / Playlist
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%server"

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python ready
echo.

echo [2/4] Checking dependencies...
python -c "import flask, requests" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing dependencies...
    pip install -r requirements.txt
)
echo [OK] Dependencies ready
echo.

echo [3/4] Checking netease-watcher...
if exist "..\netease-watcher\netease-watcher.exe" (
    echo [OK] netease-watcher found
) else (
    echo [Info] netease-watcher.exe not found
    echo        SMTC raw data will be used
)
echo.

echo [4/4] Starting server...
echo.
python app.py

pause
