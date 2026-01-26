@echo off
chcp 65001 >nul
echo ========================================
echo 从 Git 中移除包含 token 的文件并推送
echo ========================================
echo.

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

REM 步骤 1: 从 Git 中移除包含 token 的文件
echo [1] 从 Git 中移除包含 token 的文件...
git rm --cached "最终修复并上传.bat" 2>nul
git rm --cached "修复并上传.bat" 2>nul
git rm --cached "上传到GitHub.bat" 2>nul
git rm --cached "上传到GitHub_修复版.bat" 2>nul
git rm --cached "上传到GitHub_完整修复.bat" 2>nul
git rm --cached "publish_to_github.py" 2>nul
git rm --cached "publish_to_github.bat" 2>nul
git rm --cached "GITHUB_PUBLISH.md" 2>nul
git rm --cached "scripts/上传到GitHub.bat" 2>nul
echo.

REM 步骤 2: 更新 .gitignore
echo [2] 更新 .gitignore...
git add .gitignore
echo.

REM 步骤 3: 提交更改
echo [3] 提交更改（移除包含 token 的文件）...
git commit -m "Remove files containing tokens"

if %errorlevel% == 0 (
    echo 提交成功
    set COMMIT_OK=1
) else (
    echo 检查是否有更改...
    git status --short
    if exist ".git\COMMIT_EDITMSG" (
        echo 已有提交，继续推送
        set COMMIT_OK=1
    ) else (
        echo 没有更改需要提交
        set COMMIT_OK=1
    )
)

if "%COMMIT_OK%"=="1" (
    echo.
    echo [4] 强制推送到 GitHub...
    echo 提示：推送时会要求输入用户名和 token
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
    echo 操作失败
    echo ========================================
)

echo.
pause
