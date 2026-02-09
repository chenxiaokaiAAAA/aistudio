@echo off
chcp 65001 >nul
echo ========================================
echo PostgreSQL 快速设置脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查psycopg2
python -c "import psycopg2" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 psycopg2-binary...
    pip install psycopg2-binary
    if errorlevel 1 (
        echo ❌ 安装失败，请手动执行: pip install psycopg2-binary
        pause
        exit /b 1
    )
    echo ✅ psycopg2-binary 安装成功
) else (
    echo ✅ psycopg2-binary 已安装
)

echo.
echo 正在运行数据库初始化脚本...
echo.
python scripts\database\setup_postgresql.py

pause
