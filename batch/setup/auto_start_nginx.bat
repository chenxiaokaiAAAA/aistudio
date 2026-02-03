@echo off
echo 正在启动HTTPS服务...
echo.

REM 停止IIS相关服务
echo 停止IIS服务...
net stop W3SVC /y
net stop HTTP /y

REM 等待服务完全停止
timeout /t 3 /nobreak >nul

REM 检查并终止占用80端口的进程
echo 检查端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":80" ^| findstr "LISTENING"') do (
    echo 发现进程 %%a 占用80端口，正在终止...
    taskkill /PID %%a /F >nul 2>&1
)

REM 等待端口释放
timeout /t 2 /nobreak >nul

REM 启动Nginx
echo 启动Nginx服务...
cd /d "C:\new\pet-painting-system"
C:\nginx\nginx.exe -c "C:\new\pet-painting-system\nginx.conf"

REM 检查Nginx是否启动成功
timeout /t 3 /nobreak >nul
netstat -ano | findstr ":80" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo ✅ HTTPS服务启动成功！
    echo 可以通过 https://photogooo 访问您的网站
) else (
    echo ❌ HTTPS服务启动失败，请检查日志
)

echo.
echo 按任意键退出...
pause >nul
