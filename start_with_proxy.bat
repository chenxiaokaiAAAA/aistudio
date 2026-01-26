@echo off
REM Windows 批处理脚本：启动 Flask 服务器并配置代理

chcp 65001 >nul
echo ========================================
echo 启动 AI拍照机系统（已配置代理）
echo ========================================

REM 切换到项目目录
cd /d "%~dp0"
echo [INFO] 当前目录: %CD%
echo.

REM 设置端口（默认8000）
set PORT=8002

REM 设置代理（根据您的代理端口修改）
REM 常见代理端口：
REM - Clash: 7890 或 7897
REM - V2Ray: 10809
REM - Shadowsocks: 1080
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897

echo 端口设置：%PORT%
echo 代理设置：
echo   HTTP_PROXY=%HTTP_PROXY%
echo   HTTPS_PROXY=%HTTPS_PROXY%
echo ========================================
echo.

REM 检查代理端口是否可用（可选）
echo [INFO] 提示：如果代理端口不是 7890，请修改脚本中的 HTTP_PROXY 和 HTTPS_PROXY 设置
echo.

REM 启动 Flask 服务器
python start.py

pause
