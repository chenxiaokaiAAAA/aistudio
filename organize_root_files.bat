@echo off
chcp 65001 >nul
title Organize Root Directory Files
color 0B

echo ========================================
echo    Organize Root Directory Files
echo ========================================
echo.
echo [Info] This script will move files to appropriate directories
echo        Core files will remain in root directory
echo.

set /p confirm="Confirm to start? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled
    pause
    exit /b 0
)

echo.
echo [1/6] Organizing batch scripts...
if not exist "batch\deployment" mkdir "batch\deployment"
if not exist "scripts\deployment" mkdir "scripts\deployment"

if exist "快速同步到阿里云.bat" (
    move "快速同步到阿里云.bat" "scripts\deployment\" >nul 2>&1
    echo   [OK] 快速同步到阿里云.bat → scripts\deployment\
)
if exist "快速修复并同步.bat" (
    move "快速修复并同步.bat" "scripts\deployment\" >nul 2>&1
    echo   [OK] 快速修复并同步.bat → scripts\deployment\
)
if exist "完整同步到GitHub并部署.bat" (
    move "完整同步到GitHub并部署.bat" "scripts\deployment\" >nul 2>&1
    echo   [OK] 完整同步到GitHub并部署.bat → scripts\deployment\
)
if exist "配置并上传到GitHub.bat" (
    move "配置并上传到GitHub.bat" "scripts\deployment\" >nul 2>&1
    echo   [OK] 配置并上传到GitHub.bat → scripts\deployment\
)
if exist "创建版本标签.bat" (
    move "创建版本标签.bat" "scripts\deployment\" >nul 2>&1
    echo   [OK] 创建版本标签.bat → scripts\deployment\
)
if exist "上传到GitHub_生产环境优化版.bat" (
    move "上传到GitHub_生产环境优化版.bat" "scripts\deployment\" >nul 2>&1
    echo   [OK] 上传到GitHub_生产环境优化版.bat → scripts\deployment\
)

echo.
echo [2/6] Organizing shell scripts...
if exist "修复Nginx配置.sh" (
    move "修复Nginx配置.sh" "scripts\deployment\" >nul 2>&1
    echo   [OK] 修复Nginx配置.sh → scripts\deployment\
)
if exist "服务器端快速部署.sh" (
    move "服务器端快速部署.sh" "scripts\deployment\" >nul 2>&1
    echo   [OK] 服务器端快速部署.sh → scripts\deployment\
)
if exist "服务器部署下一步.sh" (
    move "服务器部署下一步.sh" "scripts\deployment\" >nul 2>&1
    echo   [OK] 服务器部署下一步.sh → scripts\deployment\
)
if exist "clone_repo.sh" (
    move "clone_repo.sh" "scripts\deployment\" >nul 2>&1
    echo   [OK] clone_repo.sh → scripts\deployment\
)

echo.
echo [3/6] Organizing PowerShell scripts...
if exist "打包并上传到服务器.ps1" (
    move "打包并上传到服务器.ps1" "scripts\deployment\" >nul 2>&1
    echo   [OK] 打包并上传到服务器.ps1 → scripts\deployment\
)

echo.
echo [4/6] Organizing documentation files...
if not exist "docs\deployment" mkdir "docs\deployment"
if not exist "docs\features" mkdir "docs\features"

if exist "快速同步指南.md" (
    move "快速同步指南.md" "docs\deployment\" >nul 2>&1
    echo   [OK] 快速同步指南.md → docs\deployment\
)
if exist "快速部署到阿里云.md" (
    move "快速部署到阿里云.md" "docs\deployment\" >nul 2>&1
    echo   [OK] 快速部署到阿里云.md → docs\deployment\
)
if exist "分类导航图标使用说明.md" (
    move "分类导航图标使用说明.md" "docs\features\" >nul 2>&1
    echo   [OK] 分类导航图标使用说明.md → docs\features\
)
if exist "GitHub仓库内容说明.md" (
    move "GitHub仓库内容说明.md" "docs\deployment\" >nul 2>&1
    echo   [OK] GitHub仓库内容说明.md → docs\deployment\
)
if exist "项目结构说明文档.md" (
    move "项目结构说明文档.md" "docs\" >nul 2>&1
    echo   [OK] 项目结构说明文档.md → docs\
)
if exist "服务器手动备份命令.txt" (
    move "服务器手动备份命令.txt" "docs\deployment\" >nul 2>&1
    echo   [OK] 服务器手动备份命令.txt → docs\deployment\
)

echo.
echo [5/6] Organizing test files...
if not exist "scripts\tests" mkdir "scripts\tests"

if exist "test_api_connection.py" (
    move "test_api_connection.py" "scripts\tests\" >nul 2>&1
    echo   [OK] test_api_connection.py → scripts\tests\
)
if exist "test_user_api_route.py" (
    move "test_user_api_route.py" "scripts\tests\" >nul 2>&1
    echo   [OK] test_user_api_route.py → scripts\tests\
)
if exist "extract_workflow_functions_final.py" (
    move "extract_workflow_functions_final.py" "scripts\tools\" >nul 2>&1
    echo   [OK] extract_workflow_functions_final.py → scripts\tools\
)

echo.
echo [6/6] Cleaning temporary files...
if exist ".winscp_temp_script.txt" (
    del ".winscp_temp_script.txt" >nul 2>&1
    echo   [OK] Deleted temporary script file
)
if exist ".winscp_temp_script.log" (
    del ".winscp_temp_script.log" >nul 2>&1
    echo   [OK] Deleted temporary log file
)

echo.
echo ========================================
echo    [OK] Organization Complete
echo ========================================
echo.
echo [Core files kept in root]
echo   - test_server.py (main service)
echo   - start.py (dev startup)
echo   - start_production.py (production startup)
echo   - requirements.txt (dependencies)
echo   - server_config.py (server config)
echo   - printer_config.py (printer config)
echo   - size_config.py (size config)
echo   - gunicorn.conf.py (Gunicorn config)
echo   - order_notification.py (order notification)
echo   - wechat_notification.py (wechat notification)
echo   - printer_client.py (printer client)
echo   - local_printer_client.py (local printer client)
echo   - local_printer.py (local printer)
echo   - print_proxy_server.py (print proxy)
echo   - README.md (project readme)
echo   - README_重要文档.md (doc index)
echo   - 根目录文件说明.md (file structure)
echo   - 根目录必需文件说明.md (required files)
echo   - Linux命令快速参考.md (command reference)
echo.
echo [Files moved]
echo   - Batch scripts → scripts\deployment\ or batch\
echo   - Shell scripts → scripts\deployment\
echo   - PowerShell scripts → scripts\deployment\
echo   - Documentation → docs\deployment\ or docs\features\
echo   - Test files → scripts\tests\
echo.
pause
