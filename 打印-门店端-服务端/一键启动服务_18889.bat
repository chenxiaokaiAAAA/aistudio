@echo off
chcp 65001 >nul
title 打印服务一键启动（打印代理 + FRP客户端）- 端口18889
color 0B

echo ========================================
echo    打印服务一键启动（端口 18889）
echo ========================================
echo.
echo 将同时启动以下服务：
echo   1. 打印代理服务（本地端口 8888）
echo   2. FRP 客户端（连接到服务器，映射端口 18889）
echo.
echo ========================================
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set FRP_DIR=%SCRIPT_DIR%frp_0.66.0_windows_amd64

REM 检查必要文件是否存在
if not exist "%SCRIPT_DIR%print_proxy_server.py" (
    echo [错误] 找不到 print_proxy_server.py
    pause
    exit /b 1
)

if not exist "%FRP_DIR%\frpc.exe" (
    echo [错误] 找不到 frpc.exe
    pause
    exit /b 1
)

if not exist "%FRP_DIR%\frpc_18889.toml" (
    echo [错误] 找不到 frpc_18889.toml
    pause
    exit /b 1
)

echo [1/2] 正在启动打印代理服务...
echo.

REM 设置打印代理服务环境变量
set LOCAL_PRINTER_PATH=\\sm003\HP OfficeJet Pro 7730 series
set PRINT_PROXY_PORT=8888
set PRINT_PROXY_API_KEY=your-secret-token-123456

REM 在新窗口中启动打印代理服务
start "打印代理服务（18889）" /D "%SCRIPT_DIR%" python print_proxy_server.py

REM 等待打印代理服务启动（给几秒时间）
timeout /t 3 /nobreak >nul

echo [2/2] 正在启动 FRP 客户端（端口 18889）...
echo.
echo ========================================
echo  FRP 客户端连接信息
echo ========================================
echo  服务端地址: 121.43.143.59:7000
echo  本地服务: 127.0.0.1:8888
echo  公网端口: 18889
echo ========================================
echo.
echo 提示：
echo  - 打印代理服务已在独立窗口运行
echo  - 当前窗口显示 FRP 客户端连接状态
echo  - 按 Ctrl+C 可停止 FRP 客户端
echo  - 关闭打印代理服务窗口可停止打印服务
echo.
echo ========================================
echo.

REM 切换到 FRP 目录并启动客户端（使用 18889 配置）
cd /d "%FRP_DIR%"
frpc.exe -c frpc_18889.toml

REM 如果 FRP 客户端退出，提示用户
echo.
echo ========================================
echo  FRP 客户端已停止
echo ========================================
echo.
echo 提示：打印代理服务仍在运行，如需停止请关闭其窗口
echo.
pause
