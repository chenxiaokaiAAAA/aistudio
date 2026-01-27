@echo off
chcp 65001 >nul
title 快速排查打印问题
color 0E

echo ========================================
echo    快速排查打印问题
echo ========================================
echo.

echo [步骤1] 检查打印机连接状态
echo.
echo 正在检查打印机 "HP OfficeJet Pro 7730 series"...
echo.

REM 检查打印机是否在线
powershell -Command "Get-Printer -Name '*HP OfficeJet*' | Format-Table Name, PrinterStatus, DriverName -AutoSize"

echo.
echo [步骤2] 检查打印队列
echo.
echo 正在打开打印队列...
echo 请查看是否有打印任务，以及任务状态
echo.

REM 打开打印队列
start "" "control printers"

echo.
echo [步骤3] 检查网络连接
echo.
echo 正在检查网络打印机连接...
echo.

ping -n 2 sm003 >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ 网络打印机连接正常
) else (
    echo ❌ 无法连接到网络打印机 sm003
    echo    请检查网络连接和打印机是否在线
)

echo.
echo [步骤4] 测试手动打印
echo.
echo 正在创建测试文件...
echo.

REM 创建测试文件
echo 这是测试打印内容 > test_print.txt
echo 如果能看到这行文字，说明打印功能正常 >> test_print.txt
echo 测试时间: %date% %time% >> test_print.txt

echo 测试文件已创建: test_print.txt
echo.
echo 请手动测试打印：
echo   1. 右键点击 test_print.txt
echo   2. 选择"打印"
echo   3. 选择打印机: HP OfficeJet Pro 7730 series
echo   4. 查看是否能正常打印
echo.

pause

echo.
echo [步骤5] 检查打印服务日志
echo.
echo 请查看打印代理服务窗口的日志，确认：
echo   - 是否显示"打印机连接正常"
echo   - 是否有任何错误信息
echo   - ShellExecute 返回码是多少
echo.

pause

echo.
echo ========================================
echo    排查完成
echo ========================================
echo.
echo 如果以上步骤都正常，但打印仍然失败：
echo   1. 检查打印机驱动是否正确安装
echo   2. 尝试重启打印机
echo   3. 检查打印机是否有纸张和墨水
echo   4. 查看打印代理服务的详细日志
echo.

pause
