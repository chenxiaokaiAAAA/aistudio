# 修复 Nginx 配置和 Flask 路由问题

## 🔍 问题分析

1. **Nginx 配置问题**：有两个 server 块冲突
2. **Flask 路由问题**：`/admin/` 返回 404，可能需要访问 `/admin/dashboard` 或其他路径

---

## 🔧 修复步骤

### 步骤1：修复 Nginx 配置（删除重复的 server 块）

```bash
# 备份
cp /etc/nginx/sites-available/aistudio /etc/nginx/sites-available/aistudio.bak3

# 编辑配置，删除第一个空的 server 块
nano /etc/nginx/sites-available/aistudio
```

**删除第一个 server 块**（只有注释的那个），保留完整的配置。

**或者直接修复**：
```bash
# 创建正确的配置
cat > /etc/nginx/sites-available/aistudio << 'EOF'
server {
    listen 80;
    server_name 121.43.143.59;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /root/project_code/static/;
        expires 30d;
    }
    
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
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

### 步骤2：检查 Flask 路由

```bash
# 测试不同的路径
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/login
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/admin/dashboard
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/admin/styles
```

---

## 📋 完整修复脚本

```bash
#!/bin/bash
echo "=========================================="
echo "修复 Nginx 配置和测试路由"
echo "=========================================="
echo ""

# 1. 修复 Nginx 配置
echo "[1/3] 修复 Nginx 配置..."
cat > /etc/nginx/sites-available/aistudio << 'EOF'
server {
    listen 80;
    server_name 121.43.143.59;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /root/project_code/static/;
        expires 30d;
    }
    
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
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "✅ 配置已修复"
echo ""

# 2. 测试并重启 Nginx
echo "[2/3] 测试并重启 Nginx..."
nginx -t
systemctl restart nginx
echo "✅ Nginx 已重启"
echo ""

# 3. 测试路由
echo "[3/3] 测试路由..."
echo "测试 / :"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/
echo "测试 /login :"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/login
echo "测试 /admin/dashboard :"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/admin/dashboard
echo "测试 /admin/styles :"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/admin/styles

echo ""
echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "现在测试外网访问："
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://121.43.143.59/
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://121.43.143.59/login
```

---

## 🎯 可能的路由路径

如果 `/admin/` 不存在，可能需要访问：
- `/admin/dashboard` - 仪表盘
- `/admin/styles` - 风格管理
- `/login` - 登录页面（登录后可能重定向到管理后台）

---

## ✅ 执行修复

执行上面的**完整修复脚本**，它会：
1. 修复 Nginx 配置（删除重复的 server 块）
2. 重启 Nginx
3. 测试不同的路由路径

执行后告诉我结果！
