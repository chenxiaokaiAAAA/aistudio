# 深入排查 Nginx 404 问题

## 🔍 当前状态

- ⚠️ 警告：`conflicting server name "121.43.143.59"` - 可能有多个 server 块
- ❌ 本地访问：404
- ❌ 外网访问：404

---

## 🔧 深入排查

### 步骤1：检查 Nginx 配置内容

```bash
# 查看完整的 aistudio 配置
cat /etc/nginx/sites-available/aistudio

# 检查 location / 配置
cat /etc/nginx/sites-available/aistudio | grep -A 10 "location /"
```

### 步骤2：检查是否有多个 server 块

```bash
# 查找所有 server_name
grep -r "server_name" /etc/nginx/sites-enabled/

# 查看所有启用的配置
ls -la /etc/nginx/sites-enabled/
cat /etc/nginx/sites-enabled/*
```

### 步骤3：测试 Flask 应用是否正常

```bash
# 直接测试 Flask（绕过 Nginx）
curl -v http://localhost:8000/
curl -v http://localhost:8000/admin/
```

---

## 🚨 可能的问题

### 问题1：配置中没有 proxy_pass

如果 `location /` 没有 `proxy_pass`，需要添加。

### 问题2：有多个 server 块冲突

警告提示有冲突的 server_name，需要检查并删除重复的配置。

### 问题3：Flask 应用本身有问题

如果直接访问 `localhost:8000` 也返回 404，说明 Flask 应用有问题。

---

## 📋 完整排查命令

```bash
echo "=== 1. 查看完整配置 ==="
cat /etc/nginx/sites-available/aistudio

echo ""
echo "=== 2. 检查 location / 配置 ==="
cat /etc/nginx/sites-available/aistudio | grep -A 10 "location /"

echo ""
echo "=== 3. 检查所有启用的配置 ==="
ls -la /etc/nginx/sites-enabled/
echo ""
echo "所有启用的配置内容："
cat /etc/nginx/sites-enabled/*

echo ""
echo "=== 4. 测试 Flask 应用（绕过 Nginx）==="
curl -v http://localhost:8000/ 2>&1 | head -20
curl -v http://localhost:8000/admin/ 2>&1 | head -20

echo ""
echo "=== 5. 查看 Nginx 访问日志 ==="
tail -10 /var/log/nginx/access.log
```

---

## 🔧 如果配置缺少 proxy_pass

如果 `location /` 没有 `proxy_pass`，需要修复：

```bash
# 备份
cp /etc/nginx/sites-available/aistudio /etc/nginx/sites-available/aistudio.bak2

# 编辑配置
nano /etc/nginx/sites-available/aistudio
```

**确保包含**：
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## 🎯 立即执行

先执行上面的**完整排查命令**，把输出发给我，特别是：
1. `location /` 的配置内容
2. Flask 直接访问的结果
3. 所有启用的配置内容

这样我可以准确定位问题并提供修复方案。
