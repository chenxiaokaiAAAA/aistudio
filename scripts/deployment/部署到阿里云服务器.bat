@echo off
chcp 65001 >nul
echo ==========================================
echo AI拍照机系统 - 部署到阿里云服务器
echo 服务器IP: 121.43.143.59
echo ==========================================
echo.

REM 检查密钥文件
set KEY_PATH=aliyun-key
if not exist "%KEY_PATH%" (
    echo [错误] 找不到 aliyun-key 目录
    echo 请将SSH密钥文件放在 aliyun-key 目录下
    pause
    exit /b 1
)

echo [1/4] 检查SSH密钥文件...
dir /b "%KEY_PATH%\*.pem" >nul 2>&1
if errorlevel 1 (
    dir /b "%KEY_PATH%\*.key" >nul 2>&1
    if errorlevel 1 (
        echo [警告] 未找到 .pem 或 .key 文件
        echo 请将SSH密钥文件放在 aliyun-key 目录下
        echo.
        set /p continue="是否继续？(Y/N): "
        if /i not "!continue!"=="Y" exit /b 0
    )
)

echo.
echo [2/4] 选择操作...
echo 1. 上传部署脚本到服务器
echo 2. 上传数据库和图片文件
echo 3. 连接到服务器执行部署
echo 4. 全部执行
echo 5. 取消
echo.
set /p choice="请选择 (1-5): "

if "%choice%"=="5" exit /b 0

REM 查找密钥文件
for %%f in ("%KEY_PATH%\*.pem" "%KEY_PATH%\*.key") do (
    set KEY_FILE=%%f
    goto :found_key
)
:found_key

if not defined KEY_FILE (
    echo [错误] 未找到密钥文件
    pause
    exit /b 1
)

set SERVER=root@121.43.143.59

if "%choice%"=="1" goto :upload_script
if "%choice%"=="2" goto :upload_files
if "%choice%"=="3" goto :connect_server
if "%choice%"=="4" goto :all_steps

:upload_script
echo.
echo [上传部署脚本...]
scp -i "%KEY_FILE%" scripts\deployment\deploy_aliyun.sh %SERVER%:/root/
if errorlevel 1 (
    echo [错误] 上传失败
    pause
    exit /b 1
)
echo ✓ 部署脚本已上传
echo.
echo 请在服务器上执行:
echo   ssh -i "%KEY_FILE%" %SERVER%
echo   chmod +x /root/deploy_aliyun.sh
echo   /root/deploy_aliyun.sh
goto :end

:upload_files
echo.
echo [上传数据库和图片文件...]
echo 请使用 PowerShell 脚本上传文件:
echo   powershell -ExecutionPolicy Bypass -File scripts\deployment\upload_to_aliyun.ps1
goto :end

:connect_server
echo.
echo [连接到服务器...]
echo 执行以下命令连接到服务器:
echo   ssh -i "%KEY_FILE%" %SERVER%
echo.
echo 连接后执行:
echo   chmod +x /root/deploy_aliyun.sh
echo   /root/deploy_aliyun.sh
pause
ssh -i "%KEY_FILE%" %SERVER%
goto :end

:all_steps
echo.
echo [执行全部步骤...]
echo [步骤1] 上传部署脚本...
scp -i "%KEY_FILE%" scripts\deployment\deploy_aliyun.sh %SERVER%:/root/
if errorlevel 1 (
    echo [错误] 上传脚本失败
    pause
    exit /b 1
)
echo ✓ 部署脚本已上传
echo.
echo [步骤2] 请在服务器上执行部署...
echo   1. 连接到服务器: ssh -i "%KEY_FILE%" %SERVER%
echo   2. 执行: chmod +x /root/deploy_aliyun.sh
echo   3. 执行: /root/deploy_aliyun.sh
echo.
echo [步骤3] 上传数据库和图片文件...
echo   执行: powershell -ExecutionPolicy Bypass -File scripts\deployment\upload_to_aliyun.ps1
goto :end

:end
echo.
echo ==========================================
echo 操作完成！
echo ==========================================
echo.
echo 详细说明请查看: docs/deployment/阿里云服务器部署完整指南.md
echo.
pause
