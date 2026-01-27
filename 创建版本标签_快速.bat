@echo off
chcp 65001 >nul
title 快速创建版本标签
color 0B

echo ========================================
echo    快速创建版本标签
echo ========================================
echo.

REM 获取当前日期作为默认版本号
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set date_str=%datetime:~0,8%
set default_version=v%date_str:~0,4%.%date_str:~4,2%.%date_str:~6,2%

echo 建议版本号：
echo   - 日期版本: %default_version% （如：v2026.01.27）
echo   - 语义版本: v1.1.0 （主版本.次版本.修订版本）
echo.

set /p VERSION="请输入版本号（直接回车使用 %default_version%）: "
if "%VERSION%"=="" set VERSION=%default_version%

REM 确保版本号以 v 开头
if not "%VERSION:~0,1%"=="v" set VERSION=v%VERSION%

echo.
set /p TAG_MESSAGE="请输入版本说明（直接回车使用默认）: "
if "%TAG_MESSAGE%"=="" set TAG_MESSAGE=版本 %VERSION%：整理项目结构并添加版本管理功能

echo.
echo 正在创建标签...
echo   版本号: %VERSION%
echo   说明: %TAG_MESSAGE%
echo   提交: ac9cdce (整理项目结构：移动文件到对应目录并添加版本管理功能)
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
        echo [错误] 标签推送失败
    )
) else (
    echo [错误] 创建标签失败
)

echo.
pause
