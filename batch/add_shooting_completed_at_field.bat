@echo off
echo 正在为订单表添加拍摄完成时间字段...
cd /d "%~dp0"
python add_shooting_completed_at_field.py
echo.
echo 脚本执行完成，按任意键退出...
pause >nul
