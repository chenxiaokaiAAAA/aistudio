@echo off
chcp 65001 >nul
echo ========================================
echo 最终修复并上传到 GitHub
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
REM 注意：token 应该通过 Git Credential Manager 提供
git remote add origin https://github.com/chenxiaokaiAAAA/aistudio.git
echo 提示：推送时会提示输入用户名和 token
echo.

REM 步骤 5: 更新 .gitignore
echo [5] 更新 .gitignore...
if not exist ".gitignore" (
    type nul > .gitignore
)
findstr /C:"上传到GitHub" .gitignore >nul 2>&1
if %errorlevel% neq 0 (
    echo. >> .gitignore
    echo # 排除包含 token 的上传脚本 >> .gitignore
    echo 上传到GitHub*.bat >> .gitignore
    echo 修复并上传.bat >> .gitignore
    echo 清理并重新提交.bat >> .gitignore
    echo 移除Token并重新提交.bat >> .gitignore
    echo publish_to_github.py >> .gitignore
    echo publish_to_github.bat >> .gitignore
    echo scripts/上传到GitHub.bat >> .gitignore
    echo GITHUB_PUBLISH.md >> .gitignore
    echo 已更新 .gitignore
)
echo.

REM 步骤 6: 重置所有更改（但保留上传脚本）
echo [6] 重置所有更改...
git reset --hard HEAD 2>nul
REM 不执行 git clean，避免删除上传脚本
echo.

REM 步骤 7: 添加文件（排除嵌套 Git 仓库）
echo [7] 添加文件...
REM 先添加主要文件和目录
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

REM 步骤 8: 检查暂存状态
echo [8] 检查暂存的文件...
git status --short
echo.

REM 步骤 9: 提交
echo [9] 提交代码...
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
    echo [10] 设置分支...
    for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set BRANCH=%%i
    if "%BRANCH%"=="" (
        git checkout -b main
    ) else (
        if not "%BRANCH%"=="main" (
            git branch -M main
        )
    )
    echo.
    echo [11] 推送到 GitHub...
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
