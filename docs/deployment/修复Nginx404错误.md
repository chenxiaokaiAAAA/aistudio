# 修复 Nginx 404 错误

## 🔍 问题

- ✅ 服务运行正常：`active (running)`
- ✅ 端口监听正常：`8000` 端口正在监听
- ❌ 访问返回 404：`http://121.43.143.59/admin/` 返回 404

**原因**：Nginx 配置可能不正确，没有正确代理到 Flask 应用。

---

## 🔧 立即排查

### 步骤1：检查 Nginx 配置

```bash
# 查看 Nginx 站点配置
cat /etc/nginx/sites-available/aistudio

# 检查配置语法
nginx -t
```

### 步骤2：测试本地访问

```bash
# 测试 Flask 应用是否正常响应
curl http://localhost:8000/admin/

# 如果返回 HTML，说明 Flask 正常
# 如果返回错误，说明 Flask 有问题
```

### 步骤3：检查 Nginx 错误日志

```bash
# 查看 Nginx 错误日志
tail -50 /var/log/nginx/error.log

# 查看 Nginx 访问日志
tail -50 /var/log/nginx/access.log
```

---

## 🚨 常见问题及解决方案

### 问题1：Nginx 配置中路径不正确

**检查**：
```bash
cat /etc/nginx/sites-available/aistudio | grep -A 10 "location /"
```

**应该看到**：
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    ...
}
```

### 问题2：Nginx 配置未启用

**检查**：
```bash
# 检查是否创建了符号链接
ls -la /etc/nginx/sites-enabled/ | grep aistudio

# 如果没有，创建它
ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 问题3：Flask 路由问题

**检查**：
```bash
# 测试 Flask 应用路由
curl http://localhost:8000/
curl http://localhost:8000/admin/
```

---

## 🔧 修复 Nginx 配置

### 检查当前配置

```bash
# 查看完整配置
cat /etc/nginx/sites-available/aistudio
```

### 标准配置应该是

```nginx
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

    # API 和主应用
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 所有其他请求
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📋 完整排查命令

```bash
echo "=== 1. 检查 Nginx 配置 ==="
cat /etc/nginx/sites-available/aistudio

echo ""
echo "=== 2. 检查配置是否启用 ==="
ls -la /etc/nginx/sites-enabled/ | grep aistudio

echo ""
echo "=== 3. 测试 Nginx 配置 ==="
nginx -t

echo ""
echo "=== 4. 测试本地 Flask 访问 ==="
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/admin/

echo ""
echo "=== 5. 查看 Nginx 错误日志 ==="
tail -20 /var/log/nginx/error.log

echo ""
echo "=== 6. 查看 Nginx 访问日志 ==="
tail -10 /var/log/nginx/access.log
```

---

## 🔧 快速修复

如果配置有问题，执行：

```bash
# 1. 备份原配置
cp /etc/nginx/sites-available/aistudio /etc/nginx/sites-available/aistudio.bak

# 2. 检查并修复配置（根据上面的标准配置）

# 3. 确保配置已启用
ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/

# 4. 测试配置
nginx -t

# 5. 重启 Nginx
systemctl restart nginx

# 6. 测试访问
curl http://121.43.143.59/admin/
```

---

## 🎯 请先执行排查命令

执行上面的**完整排查命令**，把输出发给我，我会根据具体情况提供修复方案。
