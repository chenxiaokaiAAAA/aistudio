@echo off
chcp 65001 >nul
title 最终整理根目录
color 0B

echo ========================================
echo    最终整理根目录
echo ========================================
echo.
echo 将执行以下操作：
echo   1. 删除历史遗留的二维码图片
echo   2. 删除备份文件
echo   3. 移动API文档到 docs/api/
echo   4. 移动打印服务文件到 打印-门店端-服务端/
echo   5. 移动工具脚本到 scripts/tools/
echo.
pause

REM 删除二维码图片
echo [1/5] 删除历史遗留的二维码图片...
if exist "merchant_6_qrcode.png" del /f /q "merchant_6_qrcode.png" && echo   已删除: merchant_6_qrcode.png
if exist "merchant_7_qrcode.png" del /f /q "merchant_7_qrcode.png" && echo   已删除: merchant_7_qrcode.png
if exist "website_qrcode.png" del /f /q "website_qrcode.png" && echo   已删除: website_qrcode.png
if exist "test_qrcode.jpg" del /f /q "test_qrcode.jpg" && echo   已删除: test_qrcode.jpg
if exist "qrcode_page_.jpg" del /f /q "qrcode_page_.jpg" && echo   已删除: qrcode_page_.jpg
echo ✅ 二维码图片清理完成
echo.

REM 删除备份文件
echo [2/5] 删除备份文件...
if exist "franchisee_routes.bak" del /f /q "franchisee_routes.bak" && echo   已删除: franchisee_routes.bak
echo ✅ 备份文件清理完成
echo.

REM 创建目录
if not exist "docs\api" mkdir "docs\api"

REM 移动API文档
echo [3/5] 移动API文档到 docs/api/...
if exist "API服务商集成说明.md" move "API服务商集成说明.md" "docs\api\" && echo   已移动: API服务商集成说明.md
if exist "API模板管理模块说明.md" move "API模板管理模块说明.md" "docs\api\" && echo   已移动: API模板管理模块说明.md
echo ✅ API文档移动完成
echo.

REM 移动打印服务文件
echo [4/5] 移动打印服务文件到 打印-门店端-服务端/...
if exist "README_打印代理服务.md" move "README_打印代理服务.md" "打印-门店端-服务端\" && echo   已移动: README_打印代理服务.md
if exist "print_proxy_server.py" move "print_proxy_server.py" "打印-门店端-服务端\" && echo   已移动: print_proxy_server.py
if exist "start_print_proxy.bat" move "start_print_proxy.bat" "打印-门店端-服务端\" && echo   已移动: start_print_proxy.bat
echo ✅ 打印服务文件移动完成
echo.

REM 移动工具脚本
echo [5/5] 移动工具脚本到 scripts/tools/...
if exist "完整同步到GitHub并部署.bat" move "完整同步到GitHub并部署.bat" "scripts\tools\" && echo   已移动: 完整同步到GitHub并部署.bat
if exist "整理根目录文件.bat" move "整理根目录文件.bat" "scripts\tools\" && echo   已移动: 整理根目录文件.bat
if exist "photo_selection_detail.html" move "photo_selection_detail.html" "scripts\tools\" && echo   已移动: photo_selection_detail.html
echo ✅ 工具脚本移动完成
echo.

echo ========================================
echo    整理完成
echo ========================================
echo.
echo 已完成的操作：
echo   ✅ 删除了历史遗留的二维码图片
echo   ✅ 删除了备份文件
echo   ✅ 移动了API文档到 docs/api/
echo   ✅ 移动了打印服务文件到 打印-门店端-服务端/
echo   ✅ 移动了工具脚本到 scripts/tools/
echo.
echo 根目录现在更整洁了！
echo.
pause
