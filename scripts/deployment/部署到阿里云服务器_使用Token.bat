@echo off
chcp 65001 >nul
echo ==========================================
echo AI拍照机系统 - 部署到阿里云服务器（使用GitHub Token）
echo 服务器IP: 121.43.143.59
echo ==========================================
echo.

echo [说明]
echo 此脚本使用GitHub Token克隆代码，不需要SSH密钥
echo 但连接服务器仍需要密码或SSH密钥
echo.

echo [1/3] 准备部署脚本...
echo 正在创建服务器端脚本...
(
echo #!/bin/bash
echo # 使用GitHub Token克隆仓库
echo GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
echo GITHUB_REPO="chenxiaokaiAAAA/aistudio"
echo PROJECT_DIR="/root/project_code"
echo.
echo mkdir -p $PROJECT_DIR
echo cd $PROJECT_DIR
echo.
echo if [ -d ".git" ]; then
echo     echo "更新代码..."
echo     git pull origin master
echo else
echo     echo "克隆仓库..."
echo     git clone https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git .
echo fi
echo.
echo git config --global credential.helper store
echo echo "https://${GITHUB_TOKEN}@github.com" ^> ~/.git-credentials
echo chmod 600 ~/.git-credentials
) > clone_repo.sh

echo ✓ 脚本已创建: clone_repo.sh
echo.

echo [2/3] 连接服务器...
echo.
echo 请选择连接方式:
echo 1. 使用密码连接（推荐，如果忘记了SSH密钥）
echo 2. 使用SSH密钥连接
echo 3. 手动连接
echo.
set /p connect_choice="请选择 (1-3): "

if "%connect_choice%"=="1" (
    echo.
    echo 正在连接服务器（使用密码）...
    echo 请输入服务器密码
    ssh root@121.43.143.59 "bash -s" < clone_repo.sh
) else if "%connect_choice%"=="2" (
    echo.
    echo 请输入SSH密钥文件路径（.pem或.key文件）:
    set /p key_file="密钥文件路径: "
    if exist "!key_file!" (
        ssh -i "!key_file!" root@121.43.143.59 "bash -s" < clone_repo.sh
    ) else (
        echo [错误] 找不到密钥文件
        pause
        exit /b 1
    )
) else (
    echo.
    echo 请手动执行以下步骤:
    echo.
    echo 1. 连接到服务器:
    echo    ssh root@121.43.143.59
    echo.
    echo 2. 在服务器上执行:
    echo    cd /root/project_code
    echo    git clone https://YOUR_GITHUB_TOKEN@github.com/chenxiaokaiAAAA/aistudio.git .
    echo.
    echo 3. 执行部署脚本:
    echo    chmod +x /root/deploy_aliyun.sh
    echo    /root/deploy_aliyun.sh
    pause
    exit /b 0
)

echo.
echo [3/3] 上传数据库和图片文件...
echo.
echo 请使用以下方式上传文件:
echo.
echo 方式1: 使用PowerShell脚本（推荐）
echo   powershell -ExecutionPolicy Bypass -File scripts\deployment\upload_to_aliyun.ps1
echo.
echo 方式2: 使用WinSCP（图形界面）
echo   1. 下载WinSCP
echo   2. 连接: root@121.43.143.59
echo   3. 拖拽上传文件
echo.
echo 方式3: 使用SCP命令（需要密码或密钥）
echo   scp instance/pet_painting.db root@121.43.143.59:/root/project_code/instance/
echo.

echo ==========================================
echo 操作完成！
echo ==========================================
echo.
echo 下一步:
echo   1. 上传数据库和图片文件
echo   2. 在服务器上执行部署脚本
echo   3. 启动服务
echo.
pause
