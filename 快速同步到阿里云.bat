@echo off
chcp 65001 >nul
title 快速同步到阿里云服务器
cd /d "%~dp0"

echo ========================================
echo    快速同步到阿里云服务器
echo ========================================
echo.

REM 优先使用 Python 脚本（使用 %~dp0 避免路径含空格出错）
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [信息] 使用 Python 脚本同步
    python "%~dp0scripts\deployment\sync_to_aliyun.py"
    goto :end
)

REM 否则使用 PowerShell
echo [信息] 使用 PowerShell 脚本同步
set /p choice="请选择: 1=代码 2=数据库 3=图片 4=全部 (直接回车=4): "
if "%choice%"=="" set choice=4
if "%choice%"=="1" powershell -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync_to_aliyun.ps1" -CodeOnly
if "%choice%"=="2" powershell -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync_to_aliyun.ps1" -DatabaseOnly
if "%choice%"=="3" powershell -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync_to_aliyun.ps1" -ImagesOnly
if "%choice%"=="4" powershell -ExecutionPolicy Bypass -File "%~dp0scripts\deployment\sync_to_aliyun.ps1" -All

:end
pause
