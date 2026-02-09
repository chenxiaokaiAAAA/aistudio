@echo off
chcp 65001 >nul
title 部署到阿里云服务器
cd /d "%~dp0"

echo ========================================
echo    部署到阿里云服务器
echo ========================================
echo.

REM 使用完整路径调用，避免路径含空格或中文出错
call "%~dp0scripts\deployment\部署到阿里云服务器.bat"
pause
