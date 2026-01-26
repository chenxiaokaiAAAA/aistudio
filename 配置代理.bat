@echo off
chcp 65001 >nul
echo ========================================
echo 配置 Git 代理
echo ========================================
echo.

REM 设置代理地址（根据你的代理端口修改）
set PROXY_HOST=127.0.0.1
set PROXY_PORT=7897

echo 正在配置 Git 使用代理: http://%PROXY_HOST%:%PROXY_PORT%
echo.

git config --global http.proxy http://%PROXY_HOST%:%PROXY_PORT%
git config --global https.proxy http://%PROXY_HOST%:%PROXY_PORT%

echo Git 代理配置完成！
echo.
echo 如需取消代理，请运行: git config --global --unset http.proxy
echo.

pause
