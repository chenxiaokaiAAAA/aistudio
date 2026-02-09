@echo off
chcp 65001 >nul
echo ==========================================
echo AI拍照机系统 - 配置并上传到GitHub
echo 仓库地址: https://github.com/chenxiaokaiAAAA/aistudio
echo ==========================================
echo.

REM 检查是否是Git仓库
if not exist ".git" (
    echo [1/7] 初始化Git仓库...
    git init
    if errorlevel 1 (
        echo [错误] Git初始化失败，请确保已安装Git
        pause
        exit /b 1
    )
    echo ✓ Git仓库初始化成功
    echo.
) else (
    echo [1/7] Git仓库已存在，跳过初始化
    echo.
)

echo [2/7] 配置远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/chenxiaokaiAAAA/aistudio.git
if errorlevel 1 (
    echo [警告] 添加远程仓库失败，尝试更新...
    git remote set-url origin https://github.com/chenxiaokaiAAAA/aistudio.git
)
echo ✓ 远程仓库配置成功
echo.

echo [3/7] 验证远程仓库配置...
git remote -v
echo.

echo [4/7] 检查忽略规则（验证数据库和图片是否被忽略）...
echo 检查数据库文件...
git check-ignore -v *.db instance/*.db 2>nul | findstr /C:"*.db" >nul
if errorlevel 1 (
    echo   ⚠ 警告：某些数据库文件可能未被忽略
) else (
    echo   ✓ 数据库文件已被忽略
)
echo 检查图片目录...
git check-ignore -v uploads/ final_works/ hd_images/ 2>nul | findstr /C:"uploads" >nul
if errorlevel 1 (
    echo   ⚠ 警告：图片目录可能未被忽略
) else (
    echo   ✓ 图片目录已被忽略
)
echo.

echo [5/7] 添加所有更改的文件...
git add .
echo ✓ 文件已添加到暂存区
echo.

echo [6/7] 检查将要提交的文件...
echo 以下文件将被提交（核心代码）：
git status --short
echo.
echo ⚠ 注意：数据库文件（*.db）和图片文件（uploads/, final_works/, hd_images/）已被忽略，不会上传
echo.

set /p confirm="确认继续提交？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消提交
    pause
    exit /b 0
)

echo [7/7] 提交并推送...

REM 检查Git用户配置
git config user.name >nul 2>&1
if errorlevel 1 (
    echo [配置] 检测到Git用户信息未配置，正在配置...
    git config --global user.name "chenxiaokaiAAAA"
    git config --global user.email "chenxiaokaiAAAA@users.noreply.github.com"
    echo ✓ Git用户信息已配置
    echo.
)

set /p commit_msg="请输入提交信息（直接回车使用默认信息）: "
if "%commit_msg%"=="" (
    set commit_msg=生产环境优化：添加图片路径配置、Gunicorn配置、Nginx配置和部署文档
)

git commit -m "%commit_msg%"
if errorlevel 1 (
    echo [错误] 提交失败，可能没有需要提交的更改
    echo 尝试查看状态...
    git status
    pause
    exit /b 1
)
echo ✓ 提交成功
echo.

echo 推送到GitHub...
set /p branch="分支名称（直接回车使用main）: "
if "%branch%"=="" set branch=main

git push -u origin %branch%
if errorlevel 1 (
    echo.
    echo [错误] 推送失败，可能的原因：
    echo   1. 需要先拉取远程代码：git pull origin %branch% --allow-unrelated-histories
    echo   2. 需要设置上游分支：git branch --set-upstream-to=origin/%branch% %branch%
    echo   3. 网络连接问题
    echo   4. 权限问题
    echo.
    set /p retry="是否尝试拉取并合并后再推送？(Y/N): "
    if /i "%retry%"=="Y" (
        echo 拉取远程代码...
        git pull origin %branch% --allow-unrelated-histories --no-edit
        echo 再次推送...
        git push -u origin %branch%
    )
)
echo.

echo ==========================================
echo 操作完成！
echo ==========================================
echo.
echo 仓库地址: https://github.com/chenxiaokaiAAAA/aistudio
echo.
echo 已忽略的文件（未上传）：
echo   ✓ 数据库文件（*.db, *.sqlite）
echo   ✓ 图片文件（uploads/, final_works/, hd_images/）
echo   ✓ 静态图片资源（static/images/中的图片）
echo   ✓ 日志文件（*.log）
echo   ✓ 环境变量文件（.env）
echo   ✓ 敏感配置文件
echo.
echo 请访问 https://github.com/chenxiaokaiAAAA/aistudio 确认上传结果
echo.
pause
