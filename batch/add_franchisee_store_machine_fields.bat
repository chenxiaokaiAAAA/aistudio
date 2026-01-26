@echo off
chcp 65001 >nul
echo ========================================
echo 添加加盟商门店和自拍机字段
echo ========================================
echo.

cd /d "%~dp0"
python add_franchisee_store_machine_fields.py

echo.
echo 按任意键退出...
pause >nul
