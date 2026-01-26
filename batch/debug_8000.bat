@echo off
echo ===== AI自拍机-系统8000端口调试 =====

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
echo 4. 检查端口占用详情：
netstat -ano | findstr :8000

echo.
echo 5. 获取服务器IP：
ipconfig | findstr "IPv4"

echo.
echo 6. 测试本地连接：
echo 请在浏览器中访问: http://localhost:8000

echo.
echo ===== 调试完成 =====
echo 如果本地能访问，外网不能访问，请检查：
echo 1. 阿里云安全组是否已开放8000端口
echo 2. 应用是否绑定到0.0.0.0而不是127.0.0.1
echo 3. 防火墙是否允许8000端口
pause

