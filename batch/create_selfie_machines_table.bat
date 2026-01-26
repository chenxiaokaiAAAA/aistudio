@echo off
echo 正在创建自拍机设备表...
cd /d "%~dp0"
python create_selfie_machines_table.py
echo.
echo 脚本执行完成，按任意键退出...
pause >nul
