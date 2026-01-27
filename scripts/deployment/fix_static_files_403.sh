#!/bin/bash
# 修复静态文件 403 错误
# 问题：Nginx 无法访问 static 目录，返回 403 Forbidden

echo "=========================================="
echo "修复静态文件 403 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/root/project_code"
STATIC_DIR="$PROJECT_DIR/static"

# 1. 检查目录是否存在
echo "[1/5] 检查 static 目录..."
if [ ! -d "$STATIC_DIR" ]; then
    echo "❌ static 目录不存在: $STATIC_DIR"
    exit 1
fi
echo "✅ static 目录存在: $STATIC_DIR"

# 2. 检查文件是否存在
echo ""
echo "[2/5] 检查关键文件..."
if [ ! -f "$STATIC_DIR/css/bootstrap.min.css" ]; then
    echo "⚠️  bootstrap.min.css 不存在"
else
    echo "✅ bootstrap.min.css 存在"
fi

if [ ! -f "$STATIC_DIR/js/bootstrap.bundle.min.js" ]; then
    echo "⚠️  bootstrap.bundle.min.js 不存在"
else
    echo "✅ bootstrap.bundle.min.js 存在"
fi

# 3. 检查当前权限
echo ""
echo "[3/5] 检查当前权限..."
ls -la "$STATIC_DIR" | head -5
echo ""

# 4. 修复权限
echo "[4/5] 修复权限..."
# 确保目录可读可执行
chmod -R 755 "$STATIC_DIR"
# 确保文件可读
find "$STATIC_DIR" -type f -exec chmod 644 {} \;
# 确保目录可执行（用于遍历）
find "$STATIC_DIR" -type d -exec chmod 755 {} \;

# 检查 Nginx 用户（通常是 www-data 或 nginx）
NGINX_USER=$(ps aux | grep '[n]ginx' | head -1 | awk '{print $1}')
if [ -z "$NGINX_USER" ]; then
    # 尝试常见用户名
    if id "www-data" &>/dev/null; then
        NGINX_USER="www-data"
    elif id "nginx" &>/dev/null; then
        NGINX_USER="nginx"
    else
        NGINX_USER="root"
    fi
fi

echo "Nginx 运行用户: $NGINX_USER"

# 如果 Nginx 不是以 root 运行，需要确保它能访问文件
if [ "$NGINX_USER" != "root" ]; then
    # 确保项目目录对 Nginx 用户可读
    chmod 755 "$PROJECT_DIR"
    # 如果可能，设置组权限
    if getent group "$NGINX_USER" > /dev/null 2>&1; then
        chgrp -R "$NGINX_USER" "$STATIC_DIR" 2>/dev/null || echo "⚠️  无法更改组，但权限已设置"
    fi
fi

echo "✅ 权限已修复"

# 5. 检查 Nginx 配置
echo ""
echo "[5/5] 检查 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/aistudio"
if [ -f "$NGINX_CONFIG" ]; then
    echo "检查 static 配置..."
    if grep -q "location /static/" "$NGINX_CONFIG"; then
        echo "✅ Nginx 配置中包含 /static/ location"
        grep "location /static/" -A 5 "$NGINX_CONFIG" | head -6
    else
        echo "⚠️  Nginx 配置中缺少 /static/ location"
    fi
else
    echo "⚠️  Nginx 配置文件不存在: $NGINX_CONFIG"
fi

# 6. 测试 Nginx 配置并重启
echo ""
echo "测试 Nginx 配置..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx 配置测试通过"
    echo "重启 Nginx..."
    systemctl restart nginx
    sleep 2
    systemctl status nginx --no-pager -l | head -10
else
    echo "❌ Nginx 配置测试失败，请检查配置"
    exit 1
fi

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "现在请："
echo "  1. 清除浏览器缓存（Ctrl + Shift + Delete）"
echo "  2. 刷新页面（Ctrl + F5）"
echo "  3. 检查浏览器控制台是否还有 403 错误"
echo ""
echo "如果仍然有问题，检查："
echo "  - 文件是否存在: ls -la $STATIC_DIR/css/"
echo "  - Nginx 错误日志: tail -f /var/log/nginx/error.log"
echo "  - Nginx 访问日志: tail -f /var/log/nginx/access.log"
