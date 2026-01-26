@echo off
chcp 65001 >nul
echo ========================================
echo 检查 API 服务商配置数据
echo ========================================
echo.

cd /d "%~dp0.."

python scripts\database\check_imported_data.py

echo.
pause
