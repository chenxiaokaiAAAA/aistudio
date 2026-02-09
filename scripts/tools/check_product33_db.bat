@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
echo ============================================================
echo 检查产品33的数据库记录
echo ============================================================
python scripts/tools/check_product33_db.py
echo.
echo 按任意键关闭...
pause >nul
