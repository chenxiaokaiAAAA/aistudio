# Linux 命令快速参考卡片

## 🚀 最常用命令（收藏这个）

### 服务管理

```bash
# 启动服务
systemctl start aistudio

# 停止服务
systemctl stop aistudio

# 重启服务
systemctl restart aistudio

# 查看服务状态
systemctl status aistudio
```

### 查看日志（最常用）

```bash
# 实时查看日志（推荐，按 Ctrl+C 退出）
journalctl -u aistudio -f

# 查看最近 100 行日志
journalctl -u aistudio -n 100

# 查看应用日志文件
tail -f /root/project_code/app.log
```

### 快速检查

```bash
# 一键检查：状态 + 端口 + 日志
systemctl status aistudio && netstat -tuln | grep 8000 && journalctl -u aistudio -n 20
```

## 📋 完整命令列表

| 操作 | 命令 |
|------|------|
| **启动服务** | `systemctl start aistudio` |
| **停止服务** | `systemctl stop aistudio` |
| **重启服务** | `systemctl restart aistudio` |
| **查看状态** | `systemctl status aistudio` |
| **实时日志** | `journalctl -u aistudio -f` |
| **最近日志** | `journalctl -u aistudio -n 100` |
| **应用日志** | `tail -f /root/project_code/app.log` |
| **查看端口** | `netstat -tuln \| grep 8000` |
| **查看进程** | `ps aux \| grep python` |
| **进入项目** | `cd /root/project_code` |
| **编辑文件** | `nano 文件名` |
| **查看文件** | `cat 文件名` 或 `less 文件名` |

## 🔥 紧急情况

### 服务无法启动
```bash
journalctl -u aistudio -n 100 --no-pager
```

### 端口被占用
```bash
lsof -i :8000
kill -9 <PID>
```

### 查看错误
```bash
journalctl -u aistudio -p err -n 50
```

---

📖 **完整文档**：查看 [Linux服务器常用命令.md](./Linux服务器常用命令.md)
