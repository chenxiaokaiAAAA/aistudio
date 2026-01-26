@echo off
REM Nginx服务包装器 - 作为Windows服务运行
echo Nginx HTTPS Service Starting...

REM 停止IIS相关服务
net stop W3SVC /y >nul 2>&1
net stop HTTP /y >nul 2>&1

REM 等待服务停止
timeout /t 3 /nobreak >nul

REM 检查并终止占用80端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":80" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM 等待端口释放
timeout /t 2 /nobreak >nul

REM 启动Nginx
cd /d "C:\new\pet-painting-system"
C:\nginx\nginx.exe -c "C:\new\pet-painting-system\nginx.conf"

REM 保持服务运行
:loop
timeout /t 30 /nobreak >nul
tasklist | findstr "nginx.exe" >nul
if %errorlevel% neq 0 (
    echo Nginx进程已停止，重新启动...
    C:\nginx\nginx.exe -c "C:\new\pet-painting-system\nginx.conf"
)
goto loop
