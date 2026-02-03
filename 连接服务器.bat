@echo off
chcp 65001 >nul
title 连接到阿里云服务器
color 0B

echo ========================================
echo    连接到阿里云服务器
echo ========================================
echo.

REM 检查密钥文件
set KEY_FILE=aliyun-key\aistudio.pem
if not exist "%KEY_FILE%" (
    echo [错误] 找不到密钥文件: %KEY_FILE%
    echo.
    echo 请先修复SSH密钥权限:
    echo   修复SSH密钥权限.bat
    pause
    exit /b 1
)

echo [信息] 服务器信息:
echo   服务器: root@121.43.143.59
echo   密钥文件: %KEY_FILE%
echo.

echo [提示] 如果连接失败，请先运行: 修复SSH密钥权限.bat
echo.

pause

echo.
echo [连接中...]
ssh -i "%KEY_FILE%" root@121.43.143.59
