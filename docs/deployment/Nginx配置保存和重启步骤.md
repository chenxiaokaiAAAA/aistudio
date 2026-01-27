# Nginx配置保存和重启步骤

## 当前操作：编辑Nginx配置文件

您正在编辑：`/etc/nginx/sites-available/aistudio`

## 操作步骤

### 步骤1：保存文件（在nano编辑器中）

1. 按 `Ctrl + O`（Write Out - 保存文件）
2. 按 `Enter` 确认文件名
3. 看到 "Wrote X lines" 表示保存成功

### 步骤2：退出编辑器

按 `Ctrl + X` 退出nano

### 步骤3：测试Nginx配置

```bash
nginx -t
```

**如果看到**：
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
说明配置正确！

**如果看到错误**：
- 根据错误信息修改配置
- 重新执行 `nginx -t` 直到通过

### 步骤4：重启Nginx

```bash
systemctl restart nginx
```

### 步骤5：检查状态

```bash
systemctl status nginx
```

应该看到 `active (running)` 状态。

---

## 完整命令序列（复制粘贴执行）

```bash
# 1. 测试配置
nginx -t

# 2. 如果测试通过，重启Nginx
systemctl restart nginx

# 3. 检查状态
systemctl status nginx

# 4. 测试访问
curl http://localhost:8000/admin/
```

---

## 如果配置有错误

如果 `nginx -t` 显示错误：

1. **查看错误信息**：找到错误行号
2. **重新编辑**：`nano /etc/nginx/sites-available/aistudio`
3. **修复错误**：根据错误提示修改
4. **保存并测试**：重复步骤1-3

---

## 常见错误

### 错误1：语法错误
```
nginx: [emerg] unexpected "}" in /etc/nginx/sites-available/aistudio:XX
```
**解决**：检查括号是否匹配

### 错误2：指令位置错误
```
nginx: [emerg] "worker_processes" directive is not allowed here
```
**解决**：确保 `worker_processes` 不在站点配置文件中（应该在主配置文件）

### 错误3：路径不存在
```
nginx: [emerg] open() "/path/to/file" failed (2: No such file or directory)
```
**解决**：检查路径是否正确，目录是否存在

---

## 快速参考

| 操作 | 快捷键/命令 |
|------|------------|
| 保存文件 | `Ctrl + O`，然后 `Enter` |
| 退出编辑器 | `Ctrl + X` |
| 测试配置 | `nginx -t` |
| 重启Nginx | `systemctl restart nginx` |
| 查看状态 | `systemctl status nginx` |
| 查看日志 | `tail -f /var/log/nginx/error.log` |
