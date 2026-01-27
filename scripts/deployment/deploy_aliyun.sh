#!/bin/bash
# 阿里云服务器部署脚本
# 在服务器上执行此脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "AI拍照机系统 - 阿里云服务器部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_DIR="/root/project_code"
DATA_DIR="/root/project_data"
GITHUB_REPO="https://github.com/chenxiaokaiAAAA/aistudio.git"

echo -e "${GREEN}步骤1: 更新系统...${NC}"
apt update && apt upgrade -y
echo "✓ 系统更新完成"
echo ""

echo -e "${GREEN}步骤2: 安装必要软件...${NC}"
apt install -y python3 python3-pip python3-venv nginx git unzip
echo "✓ 软件安装完成"
echo ""

echo -e "${GREEN}步骤3: 创建目录结构...${NC}"
mkdir -p $PROJECT_DIR
mkdir -p $DATA_DIR/user_images/uploads
mkdir -p $DATA_DIR/user_images/final_works
mkdir -p $DATA_DIR/user_images/hd_images
mkdir -p $DATA_DIR/logs
mkdir -p $DATA_DIR/backups
echo "✓ 目录创建完成"
echo ""

echo -e "${GREEN}步骤4: 克隆GitHub仓库...${NC}"
cd $PROJECT_DIR

# 检查是否提供了GitHub Token
if [ -n "$GITHUB_TOKEN" ]; then
    echo "  使用GitHub Token克隆..."
    if [ -d ".git" ]; then
        echo "  仓库已存在，更新代码..."
        git pull origin master
    else
        git clone https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git .
    fi
    # 配置Git凭据
    git config --global credential.helper store
    echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
    chmod 600 ~/.git-credentials
else
    echo "  使用公开仓库克隆..."
    if [ -d ".git" ]; then
        echo "  仓库已存在，更新代码..."
        git pull origin master
    else
        git clone $GITHUB_REPO .
    fi
fi
echo "✓ 代码同步完成"
echo ""

echo -e "${GREEN}步骤5: 创建Python虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
else
    echo "✓ 虚拟环境已存在"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 依赖安装完成"
echo ""

echo -e "${GREEN}步骤6: 创建必要目录...${NC}"
mkdir -p logs uploads final_works hd_images static instance backups
echo "✓ 目录创建完成"
echo ""

echo -e "${GREEN}步骤7: 配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << EOF
FLASK_ENV=production
SERVER_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///instance/pet_painting.db
UPLOAD_FOLDER=$DATA_DIR/user_images/uploads
FINAL_FOLDER=$DATA_DIR/user_images/final_works
HD_FOLDER=$DATA_DIR/user_images/hd_images
EOF
    echo "✓ 环境变量文件已创建"
else
    echo "✓ 环境变量文件已存在"
fi
echo ""

echo -e "${GREEN}步骤8: 创建符号链接（如果使用数据目录）...${NC}"
cd $PROJECT_DIR
ln -sf $DATA_DIR/user_images/uploads uploads
ln -sf $DATA_DIR/user_images/final_works final_works
ln -sf $DATA_DIR/user_images/hd_images hd_images
echo "✓ 符号链接创建完成"
echo ""

echo -e "${GREEN}步骤9: 配置Nginx...${NC}"
if [ -f "config/nginx_linux.conf" ]; then
    cp config/nginx_linux.conf /etc/nginx/sites-available/aistudio
    
    # 替换路径
    sed -i "s|/opt/aistudio|$PROJECT_DIR|g" /etc/nginx/sites-available/aistudio
    sed -i "s|alias /opt/aistudio/uploads/|alias $DATA_DIR/user_images/uploads/|g" /etc/nginx/sites-available/aistudio
    sed -i "s|alias /opt/aistudio/final_works/|alias $DATA_DIR/user_images/final_works/|g" /etc/nginx/sites-available/aistudio
    sed -i "s|alias /opt/aistudio/hd_images/|alias $DATA_DIR/user_images/hd_images/|g" /etc/nginx/sites-available/aistudio
    
    ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    echo "✓ Nginx配置完成"
else
    echo "⚠ Nginx配置文件未找到，请手动配置"
fi
echo ""

echo -e "${GREEN}步骤10: 创建Systemd服务...${NC}"
cat > /etc/systemd/system/aistudio.service << EOF
[Unit]
Description=AI Studio Gunicorn Application Server
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/start_production.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aistudio
echo "✓ Systemd服务配置完成"
echo ""

echo -e "${GREEN}步骤11: 配置防火墙...${NC}"
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw --force enable
echo "✓ 防火墙配置完成"
echo ""

echo -e "${GREEN}=========================================="
echo "部署完成！"
echo "==========================================${NC}"
echo ""
echo "下一步操作:"
echo "  1. 上传数据库文件（如果还没有）"
echo "  2. 上传图片文件（如果还没有）"
echo "  3. 启动服务: systemctl start aistudio"
echo "  4. 查看状态: systemctl status aistudio"
echo "  5. 查看日志: journalctl -u aistudio -f"
echo ""
echo "服务管理命令:"
echo "  启动: systemctl start aistudio"
echo "  停止: systemctl stop aistudio"
echo "  重启: systemctl restart aistudio"
echo "  状态: systemctl status aistudio"
echo ""
