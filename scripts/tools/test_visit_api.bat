@echo off
chcp 65001 >nul
REM 测试 /api/user/visit 接口是否可访问
REM 用法: test_visit_api.bat [BASE_URL]
REM 默认: https://photogooo.com

set BASE_URL=%1
if "%BASE_URL%"=="" set BASE_URL=https://photogooo.com

echo ==========================================
echo 测试 visit 接口: %BASE_URL%/api/user/visit
echo ==========================================
echo.

curl -X POST "%BASE_URL%/api/user/visit" -H "Content-Type: application/json" -d "{\"sessionId\":\"test123\",\"type\":\"launch\"}"

echo.
echo.
echo 若返回 {"success":true,...} 表示接口正常
pause
