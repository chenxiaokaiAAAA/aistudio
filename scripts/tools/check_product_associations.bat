@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
echo 正在诊断产品/风格关联...
python scripts/database/check_product_style_associations.py
pause
