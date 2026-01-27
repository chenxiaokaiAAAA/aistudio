# 上传 test_server.py 后重启服务

## ✅ 文件已上传

现在需要验证文件并重启服务。

---

## 🔍 验证文件上传

在服务器终端执行：

```bash
# 1. 检查文件是否存在
ls -la /root/project_code/test_server.py

# 2. 检查文件权限
chmod 644 /root/project_code/test_server.py

# 3. 检查文件内容（前几行）
head -20 /root/project_code/test_server.py
```

---

## 🔄 重启服务

```bash
# 1. 停止服务
systemctl stop aistudio

# 2. 等待几秒
sleep 2

# 3. 启动服务
systemctl start aistudio

# 4. 查看状态
systemctl status aistudio
```

---

## ✅ 验证服务是否正常

```bash
# 1. 检查服务状态
systemctl status aistudio

# 2. 检查端口监听
netstat -tlnp | grep 8000

# 3. 检查进程
ps aux | grep gunicorn | grep -v grep

# 4. 测试访问
curl http://localhost:8000/admin/
```

---

## 📋 完整验证命令（一键执行）

```bash
echo "=== 1. 检查文件 ==="
ls -lh /root/project_code/test_server.py

echo ""
echo "=== 2. 重启服务 ==="
systemctl stop aistudio
sleep 2
systemctl start aistudio

echo ""
echo "=== 3. 查看状态 ==="
systemctl status aistudio --no-pager -l | head -20

echo ""
echo "=== 4. 检查端口 ==="
netstat -tlnp | grep 8000 || echo "⚠️ 8000端口未监听"

echo ""
echo "=== 5. 检查进程 ==="
ps aux | grep gunicorn | grep -v grep || echo "⚠️ Gunicorn进程未运行"

echo ""
echo "=== 6. 测试访问 ==="
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/admin/
```

---

## 🚨 如果仍然失败

### 查看详细日志

```bash
# 查看服务日志
journalctl -u aistudio -n 50 --no-pager

# 查看应用日志
tail -50 /root/project_code/logs/error.log 2>/dev/null || echo "日志文件不存在"
tail -50 /root/project_code/logs/startup.log 2>/dev/null || echo "日志文件不存在"
```

### 手动测试启动

```bash
# 停止服务
systemctl stop aistudio

# 手动启动（查看详细错误）
cd /root/project_code
source venv/bin/activate
python start_production.py
```

---

## ✅ 如果服务正常启动

应该看到：
- ✅ `systemctl status aistudio` 显示 `active (running)`
- ✅ `netstat` 显示 `8000` 端口正在监听
- ✅ `curl` 返回 HTML 内容（不是错误）

然后可以：
1. **浏览器访问**：`http://121.43.143.59/admin/`
2. **默认账号**：`admin` / `admin123`

---

## 📝 下一步

服务正常后，可以：
1. ✅ 上传数据库文件
2. ✅ 上传图片文件
