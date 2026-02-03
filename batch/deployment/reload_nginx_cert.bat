@echo off
echo ========================================
echo Nginx证书更新 - 重新加载配置
echo ========================================
echo.

REM 检查证书文件是否存在
echo 检查证书文件...
if exist "C:\nginx\ssl\photogooo.pem" (
    echo ✅ 找到证书文件: C:\nginx\ssl\photogooo.pem
) else (
    echo ❌ 未找到证书文件: C:\nginx\ssl\photogooo.pem
    echo 请确认证书文件位置是否正确
)

if exist "C:\nginx\ssl\photogooo.key" (
    echo ✅ 找到私钥文件: C:\nginx\ssl\photogooo.key
) else (
    echo ❌ 未找到私钥文件: C:\nginx\ssl\photogooo.key
    echo 请确认私钥文件位置是否正确
)

echo.
echo 检查Nginx进程...
tasklist | findstr "nginx.exe" >nul
if %errorlevel% neq 0 (
    echo ⚠️  Nginx未运行，将启动Nginx...
    call auto_start_nginx.bat
    goto :end
)

echo ✅ Nginx正在运行
echo.
echo 正在重新加载Nginx配置（不会中断服务）...
C:\nginx\nginx.exe -s reload

if %errorlevel% equ 0 (
    echo.
    echo ✅ Nginx配置重新加载成功！
    echo 新证书已生效，无需重启服务
    echo.
    echo 请访问 https://photogooo 测试证书是否正常
) else (
    echo.
    echo ❌ 重新加载失败，尝试重启Nginx...
    echo 停止Nginx...
    taskkill /f /im nginx.exe 2>nul
    timeout /t 2 /nobreak >nul
    echo 启动Nginx...
    cd /d "C:\new\pet-painting-system"
    C:\nginx\nginx.exe -c "C:\new\pet-painting-system\nginx.conf"
    if %errorlevel% equ 0 (
        echo ✅ Nginx重启成功！
    ) else (
        echo ❌ Nginx启动失败，请检查配置文件
        echo 查看错误日志: C:\new\pet-painting-system\logs\error.log
    )
)

:end
echo.
echo 按任意键退出...
pause >nul



