#!/bin/bash
# 修复Nginx配置错误
# 在服务器上执行此脚本

echo "=========================================="
echo "修复Nginx配置错误"
echo "=========================================="
echo ""

# 删除错误的配置文件
echo "[1/4] 删除错误的配置文件..."
rm -f /etc/nginx/sites-available/aistudio
rm -f /etc/nginx/sites-enabled/aistudio
echo "✓ 完成"
echo ""

# 创建正确的站点配置文件（只包含server块）
echo "[2/4] 创建正确的Nginx站点配置..."
cat > /etc/nginx/sites-available/aistudio << 'EOF'
server {
    listen 80;
    server_name 121.43.143.59;  # 使用IP地址，后续可以配置域名
    
    client_max_body_size 100M;
    
    # 静态文件处理
    location /static/ {
        alias /root/project_code/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # 媒体文件处理（原图）
    location /media/original/ {
        alias /root/project_data/user_images/uploads/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # 媒体文件处理（效果图）
    location /media/final/ {
        alias /root/project_data/user_images/final_works/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # 高清图片处理
    location /media/hd/ {
        alias /root/project_data/user_images/hd_images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # API接口
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 120s;
    }
    
    # 代理到Flask应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 120s;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

echo "✓ 配置文件已创建"
echo ""

# 创建符号链接
echo "[3/4] 创建符号链接..."
ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/
echo "✓ 完成"
echo ""

# 测试并重启Nginx
echo "[4/4] 测试并重启Nginx..."
nginx -t
if [ $? -eq 0 ]; then
    systemctl restart nginx
    echo "✓ Nginx配置修复成功并已重启"
else
    echo "✗ Nginx配置测试失败，请检查错误信息"
    exit 1
fi

echo ""
echo "=========================================="
echo "Nginx配置修复完成！"
echo "=========================================="
echo ""
echo "验证："
echo "  systemctl status nginx"
echo "  curl http://localhost:8000/admin/"
echo ""
