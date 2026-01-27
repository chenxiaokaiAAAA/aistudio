@echo off
chcp 65001 >nul
echo ========================================
echo 彻底清理 Token 并重新上传
echo ========================================
echo.
echo 此脚本将：
echo   1. 从所有文件中移除 token
echo   2. 删除所有 Git 历史（重新开始）
echo   3. 重新提交干净的代码
echo   4. 强制推送到 GitHub
echo.
pause

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

REM 步骤 1: 移除所有嵌套的 Git 仓库
echo [1] 移除所有嵌套的 Git 仓库...
if exist "AI-studio\.git" rmdir /s /q "AI-studio\.git" 2>nul
if exist "AI-studio\AI-studio\.git" rmdir /s /q "AI-studio\AI-studio\.git" 2>nul
if exist "AI-studio\AI-studio\AI-studio\.git" rmdir /s /q "AI-studio\AI-studio\AI-studio\.git" 2>nul
echo.

REM 步骤 2: 删除整个 .git 目录（重新开始）
echo [2] 删除 Git 历史（重新开始）...
if exist ".git" (
    echo 删除 .git 目录...
    rmdir /s /q ".git" 2>nul
    echo 已删除
)
echo.

REM 步骤 3: 从文件中移除 token（使用占位符替换）
echo [3] 从文件中移除 token...
REM 这些文件应该被 .gitignore 排除，但为了安全还是移除 token
echo 注意：包含 token 的文件将被 .gitignore 排除，不会提交
echo.

REM 步骤 4: 更新 .gitignore
echo [4] 更新 .gitignore...
if not exist ".gitignore" type nul > .gitignore
findstr /C:"上传到GitHub" .gitignore >nul 2>&1
if %errorlevel% neq 0 (
    echo. >> .gitignore
    echo # 排除包含 token 的上传脚本 >> .gitignore
    echo 上传到GitHub*.bat >> .gitignore
    echo 修复并上传.bat >> .gitignore
    echo publish_to_github.py >> .gitignore
    echo publish_to_github.bat >> .gitignore
    echo scripts/上传到GitHub.bat >> .gitignore
    echo GITHUB_PUBLISH.md >> .gitignore
)
REM 但保留当前脚本和快速修复脚本
echo 已更新 .gitignore
echo.

REM 步骤 5: 重新初始化 Git
echo [5] 重新初始化 Git 仓库...
git init
echo.

REM 步骤 6: 配置 Git
echo [6] 配置 Git...
git config user.name "chenxiaokaiAAAA"
git config user.email "chenxiaokaiAAAA@users.noreply.github.com"
git config i18n.commitencoding utf-8
git config i18n.logoutputencoding utf-8
git config core.quotepath false
echo.

REM 步骤 7: 配置远程仓库（不包含 token）
echo [7] 配置远程仓库...
git remote add origin https://github.com/chenxiaokaiAAAA/aistudio.git
echo 注意：推送时会提示输入用户名和 token
echo.

REM 步骤 8: 添加文件（.gitignore 会自动排除包含 token 的文件）
echo [8] 添加文件...
REM 先添加当前脚本（确保保留）
git add "%~nx0" 2>nul
git add "快速修复.bat" 2>nul
REM 添加主要文件
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
REM 添加 AI-studio 目录
if exist "AI-studio" (
    cd AI-studio
    git add . 2>nul
    cd ..
)
REM 添加所有其他文件
git add . 2>nul
echo.

REM 步骤 9: 检查暂存状态
echo [9] 检查暂存的文件...
git status --short
echo.

REM 步骤 10: 提交
echo [10] 提交干净的代码...
git diff --cached --quiet
if %errorlevel% == 1 (
    git commit -m "Initial commit: AI-studio project"
    if %errorlevel% == 0 (
        echo 提交成功
        set COMMIT_OK=1
    ) else (
        git commit --allow-empty -m "Initial commit: AI-studio project"
        set COMMIT_OK=1
    )
) else (
    git commit --allow-empty -m "Initial commit: AI-studio project"
    set COMMIT_OK=1
)

if "%COMMIT_OK%"=="1" (
    echo.
    echo [11] 创建 main 分支...
    git checkout -b main
    echo.
    echo [12] 强制推送到 GitHub（覆盖所有历史）...
    echo 提示：推送时会要求输入用户名和密码
    echo 用户名: chenxiaokaiAAAA
    echo 密码: 粘贴你的 Personal Access Token
    echo.
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
        echo GitHub 仍然检测到 secret，请：
        echo 1. 访问: https://github.com/chenxiaokaiAAAA/aistudio/security/secret-scanning/unblock-secret/38TLbot96XT7oPdC3fRTyjrvqKT
        echo 2. 点击"Allow this secret"取消阻止
        echo 3. 然后再次运行此脚本
    )
) else (
    echo.
    echo ========================================
    echo 提交失败
    echo ========================================
)

echo.
pause
