@echo off
chcp 65001 >nul
echo ========================================
echo 清空订单数据
echo ========================================
echo.

cd /d "%~dp0"
python clear_orders.py

pause
