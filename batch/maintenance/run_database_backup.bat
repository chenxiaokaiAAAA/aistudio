@echo off
REM 数据库备份脚本 - 带详细日志
echo ========================================
echo 数据库备份任务开始
echo 时间: %date% %time%
echo ========================================

REM 切换到项目目录
cd /d C:\new\pet-painting-system
if errorlevel 1 (
    echo 错误: 无法切换到目录 C:\new\pet-painting-system
    pause
    exit /b 1
)

echo 当前目录: %CD%

REM 检查Python是否可用
python --version
if errorlevel 1 (
    echo 错误: 无法找到Python，请检查Python是否已安装并添加到PATH
    pause
    exit /b 1
)

REM 检查数据库文件是否存在
echo.
echo 检查数据库文件...
if exist "instance\pet_painting.db" (
    echo  找到: instance\pet_painting.db
) else (
    echo  警告: instance\pet_painting.db 不存在
)

if exist "pet_painting.db" (
    echo  找到: pet_painting.db
) else (
    echo  警告: pet_painting.db 不存在
)

REM 创建备份目录
if not exist "instance\backups" (
    echo.
    echo 创建备份目录...
    mkdir "instance\backups"
    if errorlevel 1 (
        echo 错误: 无法创建备份目录
        pause
        exit /b 1
    )
    echo  备份目录已创建
) else (
    echo.
    echo 备份目录已存在: instance\backups
)

REM 执行备份脚本
echo.
echo ========================================
echo 开始执行备份...
echo ========================================
python database_backup_scheduler.py --run

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
    echo 备份脚本执行完成
    echo ========================================
)

REM 检查备份文件
echo.
echo 检查备份文件...
if exist "instance\backups\*.bak" (
    echo  找到备份文件:
    dir /b instance\backups\*.bak
) else (
    echo  警告: 没有找到备份文件！
    echo  请检查上面的错误信息
)

echo.
echo ========================================
echo 备份任务结束
echo 时间: %date% %time%
echo ========================================
pause
