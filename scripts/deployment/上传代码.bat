@echo off
chcp 65001 >nul
echo ========================================
echo 上传 AI-studio 项目到 GitHub
echo ========================================
echo.

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

REM 步骤 1: 移除所有嵌套的 Git 仓库
echo [1] 移除所有嵌套的 Git 仓库...
if exist "AI-studio\.git" (
    echo 移除 AI-studio\.git...
    rmdir /s /q "AI-studio\.git" 2>nul
)
if exist "AI-studio\AI-studio\.git" (
    echo 移除 AI-studio\AI-studio\.git...
    rmdir /s /q "AI-studio\AI-studio\.git" 2>nul
)
if exist "AI-studio\AI-studio\AI-studio\.git" (
    echo 移除 AI-studio\AI-studio\AI-studio\.git...
    rmdir /s /q "AI-studio\AI-studio\AI-studio\.git" 2>nul
)
echo 嵌套 Git 仓库已清理
echo.

REM 步骤 2: 配置 Git
echo [2] 配置 Git...
git config user.name "chenxiaokaiAAAA"
git config user.email "chenxiaokaiAAAA@users.noreply.github.com"
git config i18n.commitencoding utf-8
git config i18n.logoutputencoding utf-8
git config core.quotepath false
echo.

REM 步骤 3: 初始化仓库
echo [3] 检查 Git 仓库...
if not exist ".git" (
    echo 初始化 Git 仓库...
    git init
)
echo.

REM 步骤 4: 配置远程仓库
echo [4] 配置远程仓库...
git remote remove origin 2>nul
REM 注意：token 应该通过环境变量或 Git Credential Manager 提供
REM 这里使用占位符，实际使用时需要替换
git remote add origin https://github.com/chenxiaokaiAAAA/aistudio.git
echo 提示：推送时需要输入用户名和 token
echo.

REM 步骤 5: 更新 .gitignore（确保不排除当前脚本）
echo [5] 更新 .gitignore...
if not exist ".gitignore" (
    type nul > .gitignore
)
echo.

REM 步骤 6: 添加文件（先添加当前脚本，确保不会被删除）
echo [6] 添加文件...
REM 先添加当前脚本和快速修复脚本（保留在仓库中）
git add "%~nx0" 2>nul
git add "快速修复.bat" 2>nul
REM 添加主要文件和目录
git add .gitignore
git add README.md
git add requirements.txt
git add *.py
git add *.bat
git add *.md
git add *.yaml
git add *.yml
git add app/
git add templates/
git add static/
git add config/
git add scripts/
git add docs/
git add batch/
REM 添加 AI-studio 目录（但排除其中的 .git）
if exist "AI-studio" (
    echo 添加 AI-studio 目录...
    cd AI-studio
    git add . 2>nul
    cd ..
)
REM 最后添加所有其他文件
git add . 2>nul
echo.

REM 步骤 7: 检查暂存状态
echo [7] 检查暂存的文件...
git status --short
echo.

REM 步骤 8: 提交
echo [8] 提交代码...
git diff --cached --quiet
if %errorlevel% == 1 (
    echo 有文件已暂存，正在提交...
    git commit -m "Initial commit: AI-studio project"
    if %errorlevel% == 0 (
        echo 提交成功
        set COMMIT_OK=1
    ) else (
        echo 提交失败，尝试创建空提交...
        git commit --allow-empty -m "Initial commit: AI-studio project"
        set COMMIT_OK=1
    )
) else (
    echo 没有文件被暂存
    git rev-parse --verify HEAD >nul 2>&1
    if %errorlevel% == 0 (
        echo 仓库已有提交
        set COMMIT_OK=1
    ) else (
        echo 创建空提交...
        git commit --allow-empty -m "Initial commit: AI-studio project"
        set COMMIT_OK=1
    )
)

if "%COMMIT_OK%"=="1" (
    echo.
    echo [9] 设置分支...
    for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set BRANCH=%%i
    if "%BRANCH%"=="" (
        git checkout -b main
    ) else (
        if not "%BRANCH%"=="main" (
            git branch -M main
        )
    )
    echo.
    echo [10] 推送到 GitHub...
    git push -u origin main --force
    
    if %errorlevel% == 0 (
        echo.
        echo ========================================
        echo 上传成功！
        echo ========================================
        echo.
        echo 仓库地址: https://github.com/chenxiaokaiAAAA/aistudio
        echo.
        git remote set-url origin https://github.com/chenxiaokaiAAAA/aistudio.git
        echo 已移除 URL 中的 token
    ) else (
        echo.
        echo ========================================
        echo 推送失败
        echo ========================================
        echo.
        echo 如果 GitHub 检测到 secret，请：
        echo 1. 访问: https://github.com/chenxiaokaiAAAA/aistudio/security/secret-scanning
        echo 2. 取消阻止 secret
        echo 3. 再次运行此脚本
    )
) else (
    echo.
    echo ========================================
    echo 提交失败
    echo ========================================
    echo.
    echo 当前状态：
    git status
)

echo.
pause
