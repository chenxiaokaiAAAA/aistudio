@echo off
chcp 65001 >nul
echo 正在添加退款申请字段和创建团购套餐表...
echo.

cd /d "%~dp0"

python scripts/database/add_refund_request_fields.py
echo.
python scripts/database/create_groupon_packages_table.py
echo.

echo 完成！
pause
