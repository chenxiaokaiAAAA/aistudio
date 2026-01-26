@echo off
REM 添加到开机启动项
echo 正在添加HTTPS服务到开机启动项...

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

REM 复制启动脚本到启动文件夹
copy "startup_https.bat" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\" >nul 2>&1

if %errorLevel% equ 0 (
    echo ✅ 已添加到开机启动项！
    echo HTTPS服务将在下次重启后自动启动
) else (
    echo ❌ 添加到启动项失败
    echo 请手动将 startup_https.bat 复制到启动文件夹
    echo 启动文件夹路径: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
)

echo.
echo 要立即测试启动脚本，请运行: startup_https.bat
echo.
pause
