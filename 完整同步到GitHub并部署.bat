@echo off
chcp 65001 >nul
title 完整同步到GitHub并部署到阿里云
cd /d "%~dp0"

echo ========================================
echo    完整同步到GitHub并部署到阿里云
echo ========================================
echo.

REM 使用完整路径调用，避免路径含空格或中文出错
call "%~dp0scripts\deployment\完整同步到GitHub并部署.bat"
pause
