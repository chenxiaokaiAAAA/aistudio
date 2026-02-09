@echo off
chcp 65001 >nul
echo ========================================
echo 设置 PostgreSQL 数据库环境变量
echo ========================================
echo.

REM 设置环境变量（当前会话有效）
set DATABASE_URL=postgresql://aistudio_user:a3183683@localhost:5432/pet_painting

echo ✅ 环境变量已设置（当前CMD窗口有效）
echo.
echo DATABASE_URL=%DATABASE_URL%
echo.
echo 注意: 这个设置只在当前CMD窗口中有效
echo 如果关闭窗口，需要重新运行此脚本
echo.
echo 或者创建 .env 文件（推荐，永久有效）
echo.

REM 检查.env文件是否存在
if exist .env (
    echo ⚠️  .env 文件已存在
    set /p overwrite="是否覆盖? (y/N): "
    if /i not "%overwrite%"=="y" (
        echo 跳过创建 .env 文件
        goto :end
    )
)

REM 创建.env文件
echo 正在创建 .env 文件...
(
    echo # PostgreSQL数据库配置
    echo DATABASE_URL=postgresql://aistudio_user:a3183683@localhost:5432/pet_painting
) > .env

echo ✅ .env 文件已创建
echo.
echo 现在可以运行测试脚本:
echo   python test_postgresql_connection.py
echo.

:end
pause
