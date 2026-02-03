@echo off
chcp 65001 >nul
title 备份并同步到阿里云服务器
color 0B

echo ========================================
echo    备份并同步到阿里云服务器
echo ========================================
echo.
echo [功能说明]
echo   1. 先在服务器上备份当前版本（自动创建带时间戳的备份）
echo   2. 然后同步本地最新代码和数据到服务器
echo   3. 同步内容包括: 代码、数据库、图片
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [信息] 使用Python脚本执行备份+同步
    echo.
    python "scripts\deployment\backup_and_sync_to_aliyun.py"
    goto :end
)

echo [错误] 未找到Python，请先安装Python
echo.
echo 或者使用以下脚本:
echo   - 快速同步到阿里云.bat (不包含备份功能)
pause
exit /b 1

:end
pause
