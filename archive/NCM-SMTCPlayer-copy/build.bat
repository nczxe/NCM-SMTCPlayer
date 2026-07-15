@echo off
chcp 65001 >nul 2>&1
title Build SMTCPlayer EXE

echo ============================================================
echo   SMTC Player - PyInstaller 打包工具
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
echo   使用方式:
echo     dist\SMTCPlayer.exe                 (默认端口 8888, 启动 GUI)
echo     dist\SMTCPlayer.exe --port 9999     (指定端口, 启动 GUI)
echo     dist\SMTCPlayer.exe --port 9999 --save-port   (保存端口)
echo     dist\SMTCPlayer.exe --no-gui        (仅 Flask 服务, 无 GUI)
echo.
echo   配置: 在 exe 同目录创建 config.json
echo     { "port": 9999 }
echo.
pause
