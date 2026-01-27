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
