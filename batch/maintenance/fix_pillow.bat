@echo off
chcp 65001 >nul
echo ========================================
echo 修复 Pillow 安装问题
echo ========================================
echo.

cd /d "%~dp0"
python fix_pillow_install.py

echo.
pause
