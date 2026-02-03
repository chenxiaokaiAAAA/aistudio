@echo off
chcp 65001 >nul
title 创建GitHub版本标签
color 0B

echo ========================================
echo    创建GitHub版本标签
echo ========================================
echo.

REM 获取当前版本号
set /p VERSION="请输入版本号（如：v1.0.1）: "
if "%VERSION%"=="" (
    echo [错误] 版本号不能为空
    pause
    exit /b 1
)

echo.
set /p MESSAGE="请输入版本说明（直接回车使用默认）: "
if "%MESSAGE%"=="" set MESSAGE=版本 %VERSION%：更新代码

echo.
echo 正在创建标签...
echo 版本号: %VERSION%
echo 说明: %MESSAGE%
echo.

REM 创建标签
git tag -a %VERSION% -m "%MESSAGE%"

if %errorlevel% neq 0 (
    echo [错误] 创建标签失败
    pause
    exit /b 1
)

echo ✅ 标签创建成功
echo.

REM 推送到远程
set /p PUSH_CONFIRM="是否推送到GitHub？(Y/N): "
if /i not "%PUSH_CONFIRM%"=="Y" (
    echo 标签已创建但未推送，稍后可以运行：
    echo   git push origin %VERSION%
    pause
    exit /b 0
)

echo.
echo 正在推送到GitHub...
git push origin %VERSION%

if %errorlevel% == 0 (
    echo.
    echo ✅ 版本标签已成功推送到GitHub
    echo.
    echo 提示：可以在GitHub上创建Release：
    echo   https://github.com/chenxiaokaiAAAA/aistudio/releases/new
    echo   选择标签: %VERSION%
) else (
    echo.
    echo [错误] 推送失败
)

echo.
pause
