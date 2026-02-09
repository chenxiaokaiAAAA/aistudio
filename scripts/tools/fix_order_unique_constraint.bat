@echo off
chcp 65001 >nul
echo ============================================================
echo 移除 orders 表 order_number 唯一约束（修复创建订单失败）
echo ============================================================
echo.
REM 若未设置 DATABASE_URL，可在此临时设置
if "%DATABASE_URL%"=="" (
    echo 提示: 未检测到 DATABASE_URL，将使用默认 PostgreSQL 连接
    set DATABASE_URL=postgresql://aistudio_user:a3183683@localhost:5432/pet_painting
)
python scripts\database\remove_order_number_unique_postgresql.py
echo.
pause
