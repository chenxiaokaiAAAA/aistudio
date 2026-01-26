@echo off
chcp 65001 >nul
echo ========================================
echo 切换到生产环境
echo ========================================
echo.

cd /d "%~dp0"

echo 正在更新后端配置...
python -c "import re; content = open('server_config.py', 'r', encoding='utf-8').read(); content = re.sub(r\"ENV = os\.environ\.get\('SERVER_ENV', '.*?'\)\", \"ENV = os.environ.get('SERVER_ENV', 'production')\", content); open('server_config.py', 'w', encoding='utf-8').write(content); print('✅ 后端已切换到生产环境')"

echo.
echo ✅ 完成！
echo.
echo 注意：前端小程序需要单独切换，运行：
echo   cd ..\AI-小程序
echo   switch_to_production.bat
echo.
pause
