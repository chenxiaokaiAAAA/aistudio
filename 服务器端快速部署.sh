#!/bin/bash
# 服务器端快速部署脚本（如果GitHub克隆失败，使用本地上传的代码）
# 在服务器上执行此脚本

set -e

echo "=========================================="
echo "AI拍照机系统 - 服务器端快速部署"
echo "=========================================="
echo ""

PROJECT_DIR="/root/project_code"
DATA_DIR="/root/project_data"

# 检查项目目录是否存在代码
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "错误: 项目代码未找到！"
    echo "请先："
    echo "  1. 从GitHub克隆代码，或"
    echo "  2. 上传代码压缩包并解压"
    exit 1
fi

echo "[1/8] 更新系统..."
apt update && apt upgrade -y
echo "✓ 完成"
echo ""

echo "[2/8] 安装必要软件..."
apt install -y python3 python3-pip python3-venv nginx git unzip
echo "✓ 完成"
echo ""

echo "[3/8] 创建数据目录..."
mkdir -p $DATA_DIR/user_images/{uploads,final_works,hd_images}
mkdir -p $DATA_DIR/logs
mkdir -p $DATA_DIR/backups
echo "✓ 完成"
echo ""

echo "[4/8] 创建Python虚拟环境..."
cd $PROJECT_DIR
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

echo "[5/8] 创建必要目录..."
mkdir -p logs uploads final_works hd_images static instance backups
echo "✓ 完成"
echo ""

echo "[6/8] 创建符号链接..."
ln -sf $DATA_DIR/user_images/uploads uploads
ln -sf $DATA_DIR/user_images/final_works final_works
ln -sf $DATA_DIR/user_images/hd_images hd_images
echo "✓ 完成"
echo ""

echo "[7/8] 配置环境变量..."
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

echo "[8/8] 配置Nginx和Systemd服务..."
if [ -f "config/nginx_linux.conf" ]; then
    cp config/nginx_linux.conf /etc/nginx/sites-available/aistudio
    sed -i "s|/opt/aistudio|$PROJECT_DIR|g" /etc/nginx/sites-available/aistudio
    sed -i "s|alias /opt/aistudio/uploads/|alias $DATA_DIR/user_images/uploads/|g" /etc/nginx/sites-available/aistudio
    sed -i "s|alias /opt/aistudio/final_works/|alias $DATA_DIR/user_images/final_works/|g" /etc/nginx/sites-available/aistudio
    sed -i "s|alias /opt/aistudio/hd_images/|alias $DATA_DIR/user_images/hd_images/|g" /etc/nginx/sites-available/aistudio
    ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    echo "✓ Nginx配置完成"
fi

# 创建Systemd服务
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

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 上传数据库文件到: $PROJECT_DIR/instance/"
echo "  2. 上传图片文件到: $DATA_DIR/user_images/"
echo "  3. 启动服务: systemctl start aistudio"
echo "  4. 查看状态: systemctl status aistudio"
echo ""
