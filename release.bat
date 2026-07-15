@echo off
title Release SMTCPlayer

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo ============================================================
echo   SMTC Player - Release
echo ============================================================

echo [1/4] Syntax check...
python -m compileall server tests
if errorlevel 1 exit /b 1

echo [2/4] Running tests...
python -m pytest tests
if errorlevel 1 (
    echo [Info] pytest unavailable or tests failed, trying unittest...
    python -m unittest discover -s tests
    if errorlevel 1 exit /b 1
)

echo [3/4] Building executable...
call build.bat
if errorlevel 1 exit /b 1

echo [4/4] Release artifact ready:
echo   dist\SMTCPlayer.exe
