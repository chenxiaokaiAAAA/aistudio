@echo off
echo ===== AI自拍机-系统连接调试 =====

echo.
echo 1. 检查8000端口是否被监听：
netstat -an | findstr :8000

echo.
echo 2. 检查Python进程：
tasklist | findstr python

echo.
echo 3. 检查防火墙规则：
netsh advfirewall firewall show rule name="PetPainting-8000"

echo.
echo 4. 测试本地连接：
curl -I http://localhost:8000 2>nul || echo "curl命令不可用，请手动测试浏览器访问"

echo.
echo 5. 获取服务器IP：
ipconfig | findstr "IPv4"

echo.
echo ===== 调试完成 =====
pause

