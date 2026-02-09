@echo off
chcp 65001 >nul
REM PostgreSQL数据库备份脚本
REM 使用方法: 直接运行此脚本

echo ========================================
echo PostgreSQL数据库备份工具
echo ========================================
echo.

REM 切换到项目根目录
cd /d "%~dp0\..\.."
if errorlevel 1 (
    echo 错误: 无法切换到项目根目录
    pause
    exit /b 1
)

echo 当前目录: %CD%
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 无法找到Python，请检查Python是否已安装并添加到PATH
    pause
    exit /b 1
)

REM 检查PostgreSQL工具是否可用
where pg_dump >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到 pg_dump 命令
    echo 请确保PostgreSQL已安装并添加到PATH环境变量
    echo 通常位于: C:\Program Files\PostgreSQL\XX\bin\
    echo.
    set /p continue="是否继续? (y/N): "
    if /i not "%continue%"=="y" (
        exit /b 1
    )
)

REM 创建备份目录
if not exist "data\backups\postgresql" (
    echo 创建备份目录...
    mkdir "data\backups\postgresql"
)

echo ========================================
echo 开始执行备份...
echo ========================================
echo.

REM 执行备份脚本
python scripts\database\backup_postgresql.py --backup --cleanup --stats

REM 检查执行结果
if errorlevel 1 (
    echo.
    echo ========================================
    echo 备份执行失败！
    echo ========================================
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo 备份任务完成
    echo ========================================
)

echo.
pause
