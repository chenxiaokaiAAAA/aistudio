@echo off
chcp 65001 >nul
echo ==========================================
echo AI拍照机系统 - 初始化Git仓库
echo ==========================================
echo.

REM 检查是否已经是Git仓库
if exist ".git" (
    echo [警告] 当前目录已经是Git仓库！
    echo.
    set /p continue="是否继续？(Y/N): "
    if /i not "%continue%"=="Y" (
        exit /b 0
    )
)

echo [1/3] 初始化Git仓库...
git init
if errorlevel 1 (
    echo [错误] Git初始化失败，请确保已安装Git
    pause
    exit /b 1
)
echo ✓ Git仓库初始化成功
echo.

echo [2/3] 配置远程仓库...
echo 请输入您的GitHub仓库地址：
echo   示例：https://github.com/username/repo-name.git
echo   或：git@github.com:username/repo-name.git
echo.
set /p repo_url="GitHub仓库地址: "
if "%repo_url%"=="" (
    echo [错误] 仓库地址不能为空
    pause
    exit /b 1
)

git remote add origin "%repo_url%"
if errorlevel 1 (
    echo [警告] 添加远程仓库失败，可能已存在
    echo 尝试更新远程仓库地址...
    git remote set-url origin "%repo_url%"
)
echo ✓ 远程仓库配置成功
echo.

echo [3/3] 验证配置...
echo 当前Git配置：
git remote -v
echo.
echo 当前分支：
git branch
echo.

echo ==========================================
echo 初始化完成！
echo ==========================================
echo.
echo 下一步操作：
echo   1. 检查.gitignore文件是否已正确配置
echo   2. 运行"上传到GitHub_生产环境优化版.bat"上传代码
echo   或手动执行：
echo     git add .
echo     git commit -m "初始提交"
echo     git push -u origin main
echo.
pause
