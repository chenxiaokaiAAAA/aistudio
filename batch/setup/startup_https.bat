@echo off
REM 开机自动启动HTTPS服务
echo 开机自动启动HTTPS服务...

REM 等待系统完全启动
timeout /t 10 /nobreak >nul

REM 停止IIS服务
net stop W3SVC /y >nul 2>&1
net stop HTTP /y >nul 2>&1

REM 等待服务停止
timeout /t 5 /nobreak >nul

REM 终止占用80端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":80" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM 等待端口释放
timeout /t 3 /nobreak >nul

REM 启动Nginx
cd /d "C:\new\pet-painting-system"
start /min C:\nginx\nginx.exe -c "C:\new\pet-painting-system\nginx.conf"

REM 记录启动日志
echo %date% %time% - HTTPS服务已启动 >> "C:\new\pet-painting-system\logs\startup.log"
