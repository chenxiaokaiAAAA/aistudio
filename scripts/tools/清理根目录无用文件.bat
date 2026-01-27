@echo off
chcp 65001 >nul
title 清理根目录无用文件
color 0C

echo ========================================
echo    清理根目录无用文件
echo ========================================
echo.
echo 将清理以下文件：
echo   1. 历史遗留的二维码图片（系统已改为动态生成）
echo   2. 备份文件
echo   3. 临时文件
echo.
echo 注意：这些文件已被.gitignore忽略，不影响Git仓库
echo.
pause

echo [1/3] 清理历史遗留的二维码图片...
if exist "merchant_6_qrcode.png" (
    echo 删除: merchant_6_qrcode.png
    del "merchant_6_qrcode.png"
)
if exist "merchant_7_qrcode.png" (
    echo 删除: merchant_7_qrcode.png
    del "merchant_7_qrcode.png"
)
if exist "website_qrcode.png" (
    echo 删除: website_qrcode.png
    del "website_qrcode.png"
)
if exist "test_qrcode.jpg" (
    echo 删除: test_qrcode.jpg
    del "test_qrcode.jpg"
)
if exist "qrcode_page_.jpg" (
    echo 删除: qrcode_page_.jpg
    del "qrcode_page_.jpg"
)
echo ✅ 二维码图片清理完成
echo.

echo [2/3] 清理备份文件...
if exist "franchisee_routes.bak" (
    echo 删除: franchisee_routes.bak
    del "franchisee_routes.bak"
)
echo ✅ 备份文件清理完成
echo.

echo [3/3] 检查其他临时文件...
if exist "photo_selection_detail.html" (
    echo [提示] photo_selection_detail.html 可以移动到 scripts/tools/
)
echo.

echo ========================================
echo    清理完成
echo ========================================
echo.
echo 已清理的文件：
echo   - 历史遗留的二维码图片（系统已改为动态生成）
echo   - 备份文件
echo.
echo 说明：
echo   - 这些文件已被.gitignore忽略，不影响Git仓库
echo   - 系统现在使用动态生成二维码，不需要这些静态文件
echo.
pause
