@echo off
echo 重启nginx和Flask服务...

echo 停止nginx...
taskkill /f /im nginx.exe 2>nul

echo 启动nginx...
start nginx.exe -c nginx.conf

echo 等待nginx启动...
timeout /t 2 /nobreak >nul

echo 重启完成！
echo 请测试下载功能是否正常
pause
