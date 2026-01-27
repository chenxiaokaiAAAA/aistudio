#!/bin/bash
# 修复静态文件权限问题 - 完整方案

echo "=========================================="
echo "修复静态文件权限问题（完整方案）"
echo "=========================================="
echo ""

# 1. 检查符号链接
echo "[1/6] 检查符号链接..."
ls -la /var/www/static
if [ ! -L /var/www/static ]; then
    echo "创建符号链接..."
    mkdir -p /var/www
    ln -sf /root/project_code/static /var/www/static
    echo "✅ 符号链接已创建"
else
    echo "✅ 符号链接已存在"
fi

# 2. 检查并修复 /var/www 权限
echo ""
echo "[2/6] 检查 /var/www 权限..."
ls -ld /var/www
chmod 755 /var/www
chown root:root /var/www
echo "✅ /var/www 权限已设置"

# 3. 检查符号链接指向的目录权限
echo ""
echo "[3/6] 检查实际目录权限..."
ls -ld /root/project_code/static
ls -ld /root/project_code/static/css
ls -ld /root/project_code/static/js

# 4. 确保所有目录有执行权限
echo ""
echo "[4/6] 修复目录权限..."
chmod 755 /root/project_code/static
find /root/project_code/static -type d -exec chmod 755 {} \;
find /root/project_code/static -type f -exec chmod 644 {} \;
echo "✅ 目录权限已修复"

# 5. 检查 Nginx 配置
echo ""
echo "[5/6] 检查 Nginx 配置..."
grep -A 3 "location /static/" /etc/nginx/sites-available/aistudio

# 6. 检查 Nginx 用户
echo ""
echo "[6/6] 检查 Nginx 用户..."
NGINX_USER=$(ps aux | grep '[n]ginx: master' | awk '{print $1}')
echo "Nginx 运行用户: $NGINX_USER"

# 如果 Nginx 不是 root，需要确保它能访问
if [ "$NGINX_USER" != "root" ]; then
    echo "Nginx 以 $NGINX_USER 用户运行"
    echo "检查 /root 目录权限..."
    ls -ld /root
    
    # 给 /root 添加执行权限（让其他用户可以进入）
    echo "给 /root 添加执行权限..."
    chmod 755 /root
    echo "✅ /root 权限已更新"
fi

# 7. 测试并重启
echo ""
echo "测试 Nginx 配置..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx 配置测试通过"
    echo "重启 Nginx..."
    systemctl restart nginx
    sleep 2
    
    echo ""
    echo "测试静态文件访问..."
    curl -I http://localhost/static/css/bootstrap.min.css 2>&1 | head -5
    
    echo ""
    echo "检查 Nginx 错误日志（如果有）..."
    tail -5 /var/log/nginx/error.log | grep -i "static\|permission" || echo "无相关错误"
else
    echo "❌ Nginx 配置测试失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
