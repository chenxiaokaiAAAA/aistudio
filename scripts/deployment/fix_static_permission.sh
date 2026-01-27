#!/bin/bash
# 修复静态文件权限问题 - 使用符号链接方案

echo "=========================================="
echo "修复静态文件权限问题（符号链接方案）"
echo "=========================================="
echo ""

# 1. 创建 /var/www 目录（如果不存在）
echo "[1/4] 创建 /var/www 目录..."
mkdir -p /var/www
chown root:root /var/www
chmod 755 /var/www
echo "✅ 完成"

# 2. 创建符号链接
echo ""
echo "[2/4] 创建符号链接..."
if [ -L /var/www/static ]; then
    echo "⚠️  符号链接已存在，删除旧链接..."
    rm -f /var/www/static
fi

ln -sf /root/project_code/static /var/www/static
ls -la /var/www/static
echo "✅ 符号链接已创建"

# 3. 修改 Nginx 配置
echo ""
echo "[3/4] 修改 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/aistudio"
if [ -f "$NGINX_CONFIG" ]; then
    # 备份原配置
    cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
    
    # 替换 static 路径
    sed -i 's|alias /root/project_code/static/;|alias /var/www/static/;|' "$NGINX_CONFIG"
    
    echo "✅ Nginx 配置已更新"
    echo "新的配置："
    grep -A 3 "location /static/" "$NGINX_CONFIG"
else
    echo "❌ Nginx 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi

# 4. 测试并重启 Nginx
echo ""
echo "[4/4] 测试并重启 Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx 配置测试通过"
    systemctl restart nginx
    sleep 2
    systemctl status nginx --no-pager -l | head -10
else
    echo "❌ Nginx 配置测试失败"
    exit 1
fi

# 5. 测试访问
echo ""
echo "测试静态文件访问..."
curl -I http://localhost/static/css/bootstrap.min.css 2>&1 | head -5

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "现在请："
echo "  1. 清除浏览器缓存（Ctrl + Shift + Delete）"
echo "  2. 硬刷新页面（Ctrl + F5）"
echo "  3. 检查浏览器控制台是否还有 403 错误"
