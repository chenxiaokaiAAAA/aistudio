#!/bin/bash
# 快速切换域名脚本
# 使用方法: bash switch_domain.sh your-domain.com

set -e

if [ -z "$1" ]; then
    echo "使用方法: bash switch_domain.sh <域名>"
    echo "示例: bash switch_domain.sh example.com"
    exit 1
fi

DOMAIN=$1
NGINX_CONFIG="/etc/nginx/sites-available/aistudio"
PROJECT_DIR="/root/project_code"

echo "=========================================="
echo "切换域名: $DOMAIN"
echo "=========================================="
echo ""

# 1. 修改Nginx配置
echo "[1/3] 修改Nginx配置..."
if [ -f "$NGINX_CONFIG" ]; then
    # 备份原配置
    cp $NGINX_CONFIG ${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)
    
    # 替换域名
    sed -i "s/server_name .*/server_name $DOMAIN www.$DOMAIN;/g" $NGINX_CONFIG
    
    echo "✓ Nginx配置已更新"
else
    echo "⚠ Nginx配置文件不存在: $NGINX_CONFIG"
fi
echo ""

# 2. 测试Nginx配置
echo "[2/3] 测试Nginx配置..."
nginx -t
if [ $? -eq 0 ]; then
    systemctl restart nginx
    echo "✓ Nginx已重启"
else
    echo "✗ Nginx配置测试失败"
    exit 1
fi
echo ""

# 3. 提示修改系统配置
echo "[3/3] 系统URL配置..."
echo ""
echo "请在管理后台修改系统URL配置："
echo "  1. 访问: http://121.43.143.59:8000/admin/system-config"
echo "  2. 进入'服务器URL配置'"
echo "  3. 修改以下URL："
echo "     - 服务器基础URL: https://$DOMAIN"
echo "     - API基础URL: https://$DOMAIN/api"
echo "     - 媒体文件URL: https://$DOMAIN/media"
echo "     - 静态文件URL: https://$DOMAIN/static"
echo "  4. 点击'保存服务器URL配置'"
echo ""

echo "=========================================="
echo "域名切换完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 配置DNS解析: $DOMAIN → 121.43.143.59"
echo "  2. 申请SSL证书（如果使用HTTPS）"
echo "  3. 在管理后台更新系统URL配置"
echo "  4. 测试访问: https://$DOMAIN/admin/"
echo ""
