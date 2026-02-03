@echo off
chcp 65001 >nul
title 修复SSH密钥文件权限
color 0B

echo ========================================
echo    修复SSH密钥文件权限
echo ========================================
echo.

set KEY_FILE=aliyun-key\aistudio.pem

if not exist "%KEY_FILE%" (
    echo [错误] 找不到密钥文件: %KEY_FILE%
    pause
    exit /b 1
)

echo [步骤1] 检查当前权限...
icacls "%KEY_FILE%"
echo.

echo [步骤2] 设置正确的权限（仅当前用户可访问）...
echo.

REM 移除所有用户的访问权限
icacls "%KEY_FILE%" /inheritance:r >nul 2>&1

REM 只给当前用户完全控制权限
icacls "%KEY_FILE%" /grant "%USERNAME%:(F)" >nul 2>&1
if errorlevel 1 (
    echo [警告] 无法自动设置权限，请手动运行：
    echo   icacls "%KEY_FILE%" /grant "%USERNAME%:(F)"
)

REM 移除其他所有权限
icacls "%KEY_FILE%" /remove "Users" >nul 2>&1
icacls "%KEY_FILE%" /remove "Everyone" >nul 2>&1
icacls "%KEY_FILE%" /remove "Authenticated Users" >nul 2>&1

echo [步骤3] 验证权限设置...
icacls "%KEY_FILE%"
echo.

echo ========================================
echo    权限修复完成
echo ========================================
echo.
echo 现在可以重新运行同步脚本了。
echo.

pause
