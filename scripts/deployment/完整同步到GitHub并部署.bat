@echo off
chcp 65001 >nul
title 完整同步到GitHub并部署到阿里云
color 0B

echo ========================================
echo    完整同步到GitHub并部署到阿里云
echo ========================================
echo.

REM 检查 Git 是否已初始化
if not exist ".git" (
    echo [错误] 当前目录不是 Git 仓库
    echo 请先运行: git init
    pause
    exit /b 1
)

echo [步骤1] 检查 Git 状态
echo.
git status
echo.

pause

echo.
echo [步骤2] 检查哪些文件被忽略了
echo.
echo 检查重要文件是否被忽略：
echo.

REM 检查重要文件
if exist "test_server.py" (
    git check-ignore -v test_server.py >nul 2>&1
    if %errorlevel% == 0 (
        echo [警告] test_server.py 被忽略了，但这是主应用文件
    ) else (
        echo [OK] test_server.py 未被忽略
    )
)

if exist "start_production.py" (
    git check-ignore -v start_production.py >nul 2>&1
    if %errorlevel% == 0 (
        echo [警告] start_production.py 被忽略了
    ) else (
        echo [OK] start_production.py 未被忽略
    )
)

if exist "gunicorn.conf.py" (
    git check-ignore -v gunicorn.conf.py >nul 2>&1
    if %errorlevel% == 0 (
        echo [警告] gunicorn.conf.py 被忽略了
    ) else (
        echo [OK] gunicorn.conf.py 未被忽略
    )
)

echo.
pause

echo.
echo [步骤3] 添加所有文件（.gitignore 会自动过滤）
echo.
git add .
echo.

echo [步骤4] 查看将要提交的文件
echo.
git status
echo.

pause

echo.
echo [步骤5] 提交更改
echo.
REM 确保使用UTF-8编码
chcp 65001 >nul
git config i18n.commitencoding utf-8
git config core.quotepath false

set /p commit_msg="请输入提交信息（直接回车使用默认）: "
if "%commit_msg%"=="" set commit_msg=更新代码：同步所有文件到GitHub

git commit -m "%commit_msg%"
echo.

if %errorlevel% neq 0 (
    echo [警告] 提交失败，可能没有更改需要提交
    echo 继续推送到远程仓库...
    echo.
)

echo.
echo [步骤6] 推送到 GitHub（私有仓库）
echo.
echo 提示：如果是私有仓库，可能需要输入 GitHub Token
echo.

REM 获取远程仓库地址
git remote -v
echo.

set /p push_confirm="确认推送到远程仓库？(Y/N): "
if /i not "%push_confirm%"=="Y" (
    echo 已取消推送
    pause
    exit /b 0
)

git push origin main
if %errorlevel% neq 0 (
    git push origin master
)

echo.
echo ========================================
echo    本地代码已推送到 GitHub
echo ========================================
echo.

REM 询问是否创建版本标签
set /p create_tag="是否创建版本标签？(Y/N，直接回车跳过): "
if /i "%create_tag%"=="Y" (
    echo.
    echo [创建版本标签]
    echo.
    
    REM 获取当前日期作为默认版本号（格式：v2026.01.27）
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set date_str=%datetime:~0,8%
    set default_version=v%date_str:~0,4%.%date_str:~4,2%.%date_str:~6,2%
    
    echo 建议版本号格式：
    echo   - 日期版本: %default_version% （如：v2026.01.27）
    echo   - 语义版本: v1.0.1 （主版本.次版本.修订版本）
    echo.
    
    set /p VERSION="请输入版本号（直接回车使用 %default_version%）: "
    if "%VERSION%"=="" set VERSION=%default_version%
    
    REM 确保版本号以 v 开头
    if not "%VERSION:~0,1%"=="v" set VERSION=v%VERSION%
    
    echo.
    set /p TAG_MESSAGE="请输入版本说明（直接回车使用默认）: "
    if "%TAG_MESSAGE%"=="" set TAG_MESSAGE=版本 %VERSION%：更新代码
    
    echo.
    echo 正在创建标签...
    echo   版本号: %VERSION%
    echo   说明: %TAG_MESSAGE%
    echo.
    
    git tag -a %VERSION% -m "%TAG_MESSAGE%"
    
    if %errorlevel% == 0 (
        echo ✅ 标签创建成功
        echo.
        echo 正在推送标签到GitHub...
        git push origin %VERSION%
        
        if %errorlevel% == 0 (
            echo.
            echo ✅ 版本标签已成功推送到GitHub
            echo.
            echo 📌 提示：可以在GitHub上创建Release：
            echo   https://github.com/chenxiaokaiAAAA/aistudio/releases/new
            echo   选择标签: %VERSION%
        ) else (
            echo [警告] 标签推送失败，但标签已创建
            echo 稍后可以运行: git push origin %VERSION%
        )
    ) else (
        echo [警告] 创建标签失败，继续部署流程...
    )
    echo.
)

set /p deploy_confirm="是否现在部署到阿里云服务器？(Y/N): "
if /i not "%deploy_confirm%"=="Y" (
    echo.
    echo 提示：可以稍后在服务器上运行以下命令同步代码：
    echo   cd /root/project_code
    echo   git pull origin main
    echo.
    pause
    exit /b 0
)

echo.
echo [步骤7] 部署到阿里云服务器
echo.
echo 请在服务器上执行以下命令：
echo.
echo   cd /root/project_code
echo   git pull origin main
echo   systemctl restart aistudio
echo.
echo 或者运行部署脚本：
echo   bash /root/project_code/scripts/deployment/sync_from_github.sh
echo.

pause
