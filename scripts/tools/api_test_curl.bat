@echo off
chcp 65001 >nul
REM API 接口 curl 自动化测试脚本 (Windows)
REM 使用前请确保服务已启动: python test_server.py
REM 用法: api_test_curl.bat [BASE_URL]
REM 默认: http://localhost:8000

set BASE_URL=%1
if "%BASE_URL%"=="" set BASE_URL=http://localhost:8000

echo ==========================================
echo API 接口 curl 测试
echo    基础URL: %BASE_URL%
echo ==========================================
echo.

echo [1] 小程序接口
echo   产品分类...
curl -s -o nul -w "%%{http_code}" "%BASE_URL%/api/miniprogram/product-categories"
echo.
echo   产品列表...
curl -s -o nul -w "%%{http_code}" "%BASE_URL%/api/miniprogram/products"
echo.
echo   风格列表...
curl -s -o nul -w "%%{http_code}" "%BASE_URL%/api/miniprogram/styles"
echo.
echo   轮播图...
curl -s -o nul -w "%%{http_code}" "%BASE_URL%/api/miniprogram/banners"
echo.
echo   订单列表...
curl -s -o nul -w "%%{http_code}" "%BASE_URL%/api/miniprogram/orders?openid=test"
echo.

echo.
echo ==========================================
echo 测试完成。若状态码为 200 表示接口可用。
echo ==========================================
pause
