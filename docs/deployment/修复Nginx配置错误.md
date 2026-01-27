# 修复Nginx配置错误

## 问题

从部署日志看到错误：
```
nginx: [emerg] "worker_processes" directive is not allowed here in /etc/nginx/sites-enabled/aistudio:5
```

**原因**：`worker_processes` 指令只能放在主配置文件 `/etc/nginx/nginx.conf` 中，不能放在站点配置文件 `/etc/nginx/sites-available/` 中。

## 解决方案

### 在服务器上执行以下命令修复：

```bash
# 1. 删除错误的配置文件
rm /etc/nginx/sites-available/aistudio
rm /etc/nginx/sites-enabled/aistudio

# 2. 使用正确的站点配置文件（只包含server块）
cat > /etc/nginx/sites-available/aistudio << 'EOF'
# HTTP服务器 - 重定向到HTTPS
server {
    listen 80;
    server_name 121.43.143.59;  # 暂时使用IP，后续可以配置域名
    
    # 暂时不重定向，直接代理（如果没有SSL证书）
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态文件处理
    location /static/ {
        alias /root/project_code/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 媒体文件处理
    location /media/original/ {
        alias /root/project_data/user_images/uploads/;
        expires 7d;
    }
    
    location /media/final/ {
        alias /root/project_data/user_images/final_works/;
        expires 30d;
    }
    
    location /media/hd/ {
        alias /root/project_data/user_images/hd_images/;
        expires 30d;
    }
    
    # API接口
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 文件上传大小限制
    client_max_body_size 100M;
}
EOF

# 3. 创建符号链接
ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/

# 4. 测试配置
nginx -t

# 5. 重启Nginx
systemctl restart nginx

# 6. 检查状态
systemctl status nginx
```

---

## 简化版Nginx配置（如果不需要HTTPS）

如果暂时不需要HTTPS，可以使用这个简化配置：

```bash
cat > /etc/nginx/sites-available/aistudio << 'EOF'
server {
    listen 80;
    server_name 121.43.143.59;
    
    client_max_body_size 100M;
    
    # 静态文件
    location /static/ {
        alias /root/project_code/static/;
        expires 30d;
    }
    
    # 媒体文件
    location /media/ {
        alias /root/project_data/user_images/;
        expires 7d;
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
    }
}
EOF

ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## 验证部署

修复Nginx后，验证部署：

```bash
# 1. 检查Nginx状态
systemctl status nginx

# 2. 检查应用服务状态
systemctl status aistudio

# 3. 检查端口监听
netstat -tlnp | grep 8000

# 4. 测试访问
curl http://localhost:8000/admin/
```

---

## 如果还有问题

```bash
# 查看Nginx错误日志
tail -f /var/log/nginx/error.log

# 查看应用日志
tail -f /root/project_code/logs/error.log
journalctl -u aistudio -f
```
