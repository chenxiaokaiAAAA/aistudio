@echo off
chcp 65001 >nul
title 进一步整理根目录文件
color 0C

echo ========================================
echo    进一步整理根目录文件
echo ========================================
echo.
echo 将整理以下内容：
echo   1. 移动API文档到 docs/api/
echo   2. 移动打印服务文档到 打印-门店端-服务端/
echo   3. 移动配置文件到 config/
echo   4. 移动工具脚本到 scripts/tools/
echo   5. 清理临时和备份文件
echo.
pause

REM 创建目录
if not exist "docs\api" mkdir "docs\api"
if not exist "config\misc" mkdir "config\misc"

echo [1/5] 移动API文档...
if exist "API服务商集成说明.md" move "API服务商集成说明.md" "docs\api\"
if exist "API模板管理模块说明.md" move "API模板管理模块说明.md" "docs\api\"
echo ✅ API文档移动完成
echo.

echo [2/5] 移动打印服务相关文件...
if exist "README_打印代理服务.md" move "README_打印代理服务.md" "打印-门店端-服务端\"
if exist "start_print_proxy.bat" move "start_print_proxy.bat" "打印-门店端-服务端\"
if exist "print_proxy_server.py" move "print_proxy_server.py" "打印-门店端-服务端\"
echo ✅ 打印服务文件移动完成
echo.

echo [3/5] 移动配置文件...
if exist "clash_config_timeout_fix.yaml" move "clash_config_timeout_fix.yaml" "config\misc\"
echo ✅ 配置文件移动完成
echo.

echo [4/5] 移动工具脚本...
if exist "完整同步到GitHub并部署.bat" move "完整同步到GitHub并部署.bat" "scripts\deployment\"
if exist "整理根目录文件.bat" move "整理根目录文件.bat" "scripts\tools\"
if exist "photo_selection_detail.html" move "photo_selection_detail.html" "scripts\tools\"
echo ✅ 工具脚本移动完成
echo.

echo [5/5] 清理备份和临时文件...
if exist "franchisee_routes.bak" del "franchisee_routes.bak"
echo ✅ 清理完成
echo.

echo ========================================
echo    整理完成
echo ========================================
echo.
echo 根目录现在只保留：
echo   ✅ 核心代码文件（test_server.py等）
echo   ✅ 启动脚本（start.py, start_production.py）
echo   ✅ 配置文件（requirements.txt, gunicorn.conf.py）
echo   ✅ 重要文档（README.md, 根目录文件说明.md等）
echo.
echo 其他文件已分类整理到对应目录
echo.
pause
