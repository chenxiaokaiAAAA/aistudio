@echo off
chcp 65001 >nul
title 快速同步到阿里云服务器
color 0B

echo ========================================
echo    快速同步到阿里云服务器
echo ========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [信息] 使用Python脚本同步
    echo.
    python "scripts\deployment\sync_to_aliyun.py"
    goto :end
)

REM 如果Python不可用，使用PowerShell脚本
echo [信息] 使用PowerShell脚本同步
echo.
echo 选择同步内容：
echo   1. 只同步代码（通过Git）
echo   2. 只同步数据库
echo   3. 只同步图片
echo   4. 同步所有（代码+数据库+图片）
echo   0. 取消
echo.

set /p choice="请选择 (0-4): "

if "%choice%"=="0" exit /b 0
if "%choice%"=="1" (
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\sync_to_aliyun.ps1" -CodeOnly
    goto :end
)
if "%choice%"=="2" (
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\sync_to_aliyun.ps1" -DatabaseOnly
    goto :end
)
if "%choice%"=="3" (
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\sync_to_aliyun.ps1" -ImagesOnly
    goto :end
)
if "%choice%"=="4" (
    powershell -ExecutionPolicy Bypass -File "scripts\deployment\sync_to_aliyun.ps1" -All
    goto :end
)

echo [错误] 无效的选择
pause
exit /b 1

:end
pause
