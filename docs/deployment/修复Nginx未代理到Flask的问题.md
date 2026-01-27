# 修复 Nginx 未代理到 Flask 的问题

## 🔍 问题分析

从错误日志看：
- ❌ 所有请求都在 `/usr/share/nginx/html/` 中查找文件
- ❌ 说明 Nginx 没有代理到 Flask，而是使用默认的静态文件目录
- ⚠️ 有警告：`conflicting server name "121.43.143.59"` - 可能有多个 server 块

---

## 🔧 立即修复

### 步骤1：检查当前 Nginx 配置

```bash
# 查看站点配置
cat /etc/nginx/sites-available/aistudio

# 查看启用的配置
ls -la /etc/nginx/sites-enabled/

# 检查是否有默认配置在干扰
cat /etc/nginx/sites-enabled/default 2>/dev/null || echo "默认配置不存在"
```

### 步骤2：检查是否有多个 server 块

```bash
# 查找所有包含 server_name 的配置
grep -r "server_name" /etc/nginx/sites-enabled/
```

### 步骤3：修复配置

```bash
# 1. 禁用默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 2. 确保我们的配置已启用
ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/

# 3. 检查配置
nginx -t

# 4. 重启 Nginx
systemctl restart nginx
```

---

## 📋 完整修复脚本

```bash
#!/bin/bash
echo "=========================================="
echo "修复 Nginx 配置"
echo "=========================================="
echo ""

# 1. 备份当前配置
echo "[1/5] 备份配置..."
cp /etc/nginx/sites-available/aistudio /etc/nginx/sites-available/aistudio.bak
echo "✅ 已备份"
echo ""

# 2. 禁用默认配置
echo "[2/5] 禁用默认配置..."
rm -f /etc/nginx/sites-enabled/default
echo "✅ 默认配置已禁用"
echo ""

# 3. 确保我们的配置已启用
echo "[3/5] 启用 aistudio 配置..."
ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/
echo "✅ 配置已启用"
echo ""

# 4. 检查配置
echo "[4/5] 检查配置..."
nginx -t
echo ""

# 5. 重启 Nginx
echo "[5/5] 重启 Nginx..."
systemctl restart nginx
echo "✅ Nginx 已重启"
echo ""

echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo ""
echo "测试访问："
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost/admin/
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://121.43.143.59/admin/
```

---

## 🔍 检查配置内容

如果配置有问题，需要确保包含正确的 `proxy_pass`：

```bash
# 查看 location / 配置
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

---

## 🚨 如果配置不正确

如果 `location /` 没有 `proxy_pass`，需要修复：

```bash
# 编辑配置
nano /etc/nginx/sites-available/aistudio
```

**确保包含**：
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

    # 所有其他请求代理到 Flask
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

然后：
```bash
nginx -t
systemctl restart nginx
```

---

## 🎯 立即执行

执行上面的**完整修复脚本**，应该能解决问题。

执行后告诉我结果！
