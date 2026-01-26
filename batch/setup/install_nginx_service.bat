@echo off
REM Windows服务安装脚本 - 将Nginx设置为Windows服务
echo 正在安装Nginx为Windows服务...

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

REM 创建服务
sc create "NginxHTTPS" binPath= "C:\new\pet-painting-system\nginx_service.bat" start= auto DisplayName= "Nginx HTTPS Service"

if %errorLevel% equ 0 (
    echo ✅ Nginx服务安装成功！
    echo 服务将在下次重启后自动启动
    echo.
    echo 要立即启动服务，请运行: sc start NginxHTTPS
    echo 要停止服务，请运行: sc stop NginxHTTPS
    echo 要删除服务，请运行: sc delete NginxHTTPS
) else (
    echo ❌ 服务安装失败
)

echo.
pause
