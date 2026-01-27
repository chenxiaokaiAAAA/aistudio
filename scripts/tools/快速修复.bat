@echo off
chcp 65001 >nul
echo ========================================
echo 快速修复嵌套仓库问题
echo ========================================
echo.

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

REM 移除所有嵌套的 Git 仓库
echo 正在移除嵌套的 Git 仓库...
if exist "AI-studio\.git" (
    echo 移除: AI-studio\.git
    rmdir /s /q "AI-studio\.git" 2>nul
)
if exist "AI-studio\AI-studio\.git" (
    echo 移除: AI-studio\AI-studio\.git
    rmdir /s /q "AI-studio\AI-studio\.git" 2>nul
)
if exist "AI-studio\AI-studio\AI-studio\.git" (
    echo 移除: AI-studio\AI-studio\AI-studio\.git
    rmdir /s /q "AI-studio\AI-studio\AI-studio\.git" 2>nul
)

echo.
echo ========================================
echo 完成！嵌套 Git 仓库已清理
echo ========================================
echo.
echo 现在可以运行"上传代码.bat"来上传代码
echo.
pause
