#!/bin/bash
# 从 GitHub 同步代码到服务器

set -e  # 遇到错误立即退出

echo "========================================"
echo "    从 GitHub 同步代码到服务器"
echo "========================================"
echo

# 配置
PROJECT_DIR="/root/project_code"
GIT_BRANCH="main"
SERVICE_NAME="aistudio"

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "[错误] 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 进入项目目录
cd "$PROJECT_DIR"

# 检查是否是 Git 仓库
if [ ! -d ".git" ]; then
    echo "[错误] 当前目录不是 Git 仓库"
    echo "请先运行: git clone <repository-url> $PROJECT_DIR"
    exit 1
fi

echo "[步骤1] 检查当前状态"
echo
git status
echo

echo "[步骤2] 获取最新代码"
echo
# 先获取远程更新（不合并）
git fetch origin

# 检查是否有更新
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$GIT_BRANCH)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ 代码已是最新版本，无需更新"
else
    echo "发现新版本，开始更新..."
    echo
    
    # 备份当前代码（可选）
    echo "[步骤3] 备份当前代码"
    BACKUP_DIR="/root/project_code_backup_$(date +%Y%m%d_%H%M%S)"
    echo "备份到: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r "$PROJECT_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
    echo "✅ 备份完成"
    echo
    
    # 拉取最新代码
    echo "[步骤4] 拉取最新代码"
    git pull origin $GIT_BRANCH
    
    if [ $? -ne 0 ]; then
        echo "[错误] 拉取代码失败"
        echo "尝试使用 master 分支..."
        git pull origin master
    fi
    
    echo "✅ 代码更新完成"
    echo
fi

echo "[步骤5] 检查重要文件是否存在"
echo

# 检查重要文件
MISSING_FILES=()

if [ ! -f "test_server.py" ]; then
    MISSING_FILES+=("test_server.py")
fi

if [ ! -f "start_production.py" ]; then
    MISSING_FILES+=("start_production.py")
fi

if [ ! -f "gunicorn.conf.py" ]; then
    MISSING_FILES+=("gunicorn.conf.py")
fi

if [ ! -f "requirements.txt" ]; then
    MISSING_FILES+=("requirements.txt")
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "[警告] 以下重要文件缺失："
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo
else
    echo "✅ 所有重要文件都存在"
    echo
fi

echo "[步骤6] 检查虚拟环境"
echo
if [ ! -d "venv" ]; then
    echo "[警告] 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
    echo
fi

echo "[步骤7] 更新依赖（如果需要）"
echo
source venv/bin/activate
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo "✅ 依赖已更新"
else
    echo "[警告] requirements.txt 不存在，跳过依赖更新"
fi
deactivate
echo

echo "[步骤8] 检查数据库文件"
echo
if [ ! -f "instance/pet_painting.db" ]; then
    echo "[警告] 数据库文件不存在: instance/pet_painting.db"
    echo "提示：数据库文件不会被 Git 同步，需要单独备份和恢复"
    echo
else
    echo "✅ 数据库文件存在"
    echo
fi

echo "[步骤9] 重启服务"
echo
read -p "是否重启 aistudio 服务？(Y/n): " restart_service

if [[ "$restart_service" =~ ^[Yy]$ ]] || [ -z "$restart_service" ]; then
    echo "正在重启服务..."
    systemctl restart $SERVICE_NAME
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ 服务已重启并运行正常"
    else
        echo "[错误] 服务启动失败，请检查日志："
        echo "  journalctl -u $SERVICE_NAME -n 50"
    fi
else
    echo "跳过服务重启"
fi

echo
echo "========================================"
echo "    同步完成"
echo "========================================"
echo
echo "提示："
echo "  - 查看服务状态: systemctl status $SERVICE_NAME"
echo "  - 查看服务日志: journalctl -u $SERVICE_NAME -f"
echo "  - 查看应用日志: tail -f $PROJECT_DIR/app.log"
echo
