@echo off
echo 正在使用 SQLAlchemy 为订单表添加门店和自拍机字段...
cd /d "%~dp0"
python add_order_store_machine_fields_sqlalchemy.py
echo.
echo 脚本执行完成，按任意键退出...
pause >nul
