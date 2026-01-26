#!/bin/bash
# -*- coding: utf-8 -*-
#
# Linux生产环境快速部署脚本
# 使用方法: bash scripts/deployment/deploy_linux.sh
#

set -e  # 遇到错误立即退出

echo "=========================================="
echo "AI拍照机系统 - Linux生产环境部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}请不要使用root用户运行此脚本${NC}"
    exit 1
fi

# 项目路径（根据实际情况修改）
PROJECT_DIR="/opt/aistudio"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${GREEN}步骤1: 检查系统环境...${NC}"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3未安装，请先安装Python3${NC}"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3未安装，请先安装pip3${NC}"
    exit 1
fi
echo "✅ pip3已安装"

# 检查Nginx
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}⚠️  Nginx未安装，请先安装Nginx${NC}"
    echo "Ubuntu/Debian: sudo apt install nginx -y"
    echo "CentOS/RHEL: sudo yum install nginx -y"
    exit 1
fi
echo "✅ Nginx已安装"

echo -e "${GREEN}步骤2: 创建项目目录...${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo -e "${GREEN}步骤3: 创建Python虚拟环境...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

echo -e "${GREEN}步骤4: 激活虚拟环境并安装依赖...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依赖安装完成"

echo -e "${GREEN}步骤5: 创建必要目录...${NC}"
mkdir -p logs uploads final_works hd_images static instance backups
echo "✅ 目录创建完成"

echo -e "${GREEN}步骤6: 配置Gunicorn...${NC}"
if [ ! -f "gunicorn.conf.py" ]; then
    echo -e "${YELLOW}⚠️  未找到gunicorn.conf.py，请确保文件存在${NC}"
else
    echo "✅ Gunicorn配置文件已就绪"
fi

echo -e "${GREEN}步骤7: 配置Nginx...${NC}"
if [ -f "config/nginx_linux.conf" ]; then
    echo "请手动执行以下命令配置Nginx:"
    echo "  sudo cp config/nginx_linux.conf /etc/nginx/sites-available/aistudio"
    echo "  sudo nano /etc/nginx/sites-available/aistudio  # 修改域名和路径"
    echo "  sudo ln -s /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/"
    echo "  sudo nginx -t"
    echo "  sudo systemctl restart nginx"
else
    echo -e "${YELLOW}⚠️  未找到config/nginx_linux.conf${NC}"
fi

echo -e "${GREEN}步骤8: 创建Systemd服务...${NC}"
echo "请手动创建 /etc/systemd/system/aistudio.service 文件"
echo "参考文档: docs/deployment/生产环境部署指南.md"

echo ""
echo -e "${GREEN}=========================================="
echo "部署准备完成！"
echo "==========================================${NC}"
echo ""
echo "接下来的步骤:"
echo "1. 配置环境变量: nano $PROJECT_DIR/.env"
echo "2. 配置Nginx: 参考步骤7"
echo "3. 配置SSL证书"
echo "4. 创建Systemd服务"
echo "5. 启动服务: sudo systemctl start aistudio"
echo ""
echo "详细说明请查看: docs/deployment/生产环境部署指南.md"
