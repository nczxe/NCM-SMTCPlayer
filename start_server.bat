@echo off
chcp 65001 >nul
echo ============================================================
echo   SMTC Player - 媒体控制器服务端启动脚本
echo ============================================================
echo.

cd /d "%~dp0server"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python环境正常
echo.

echo [2/3] 检查依赖...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    pip install -r requirements.txt
)
echo [OK] 依赖已就绪
echo.

echo [3/3] 启动服务端...
echo.
python app.py

pause
