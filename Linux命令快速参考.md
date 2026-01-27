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

### 备份和恢复（重要！测试前必做）

```bash
# 快速备份（一键执行）
cd /root && BACKUP_DIR="project_code_backup_$(date +%Y%m%d_%H%M%S)" && \
mkdir -p "$BACKUP_DIR" && cp -r project_code/* "$BACKUP_DIR/" 2>/dev/null && \
[ -f project_code/instance/pet_painting.db ] && \
mkdir -p "$BACKUP_DIR/instance" && \
cp project_code/instance/pet_painting.db "$BACKUP_DIR/instance/pet_painting.db" && \
echo "✅ 备份完成: $BACKUP_DIR"

# 查看所有备份
ls -lah /root | grep project_code_backup

# 快速恢复备份（修改备份目录名）
BACKUP_DIR="project_code_backup_20260127_140000"  # 改为你的备份目录名
systemctl stop aistudio && \
rm -rf project_code/* && \
cp -r "$BACKUP_DIR"/* project_code/ && \
[ -f "$BACKUP_DIR/instance/pet_painting.db" ] && \
cp "$BACKUP_DIR/instance/pet_painting.db" project_code/instance/pet_painting.db && \
chmod 644 project_code/instance/pet_painting.db && \
systemctl start aistudio && \
echo "✅ 恢复完成"
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
| **快速备份** | 见下方"备份和恢复"部分 |
| **恢复备份** | 见下方"备份和恢复"部分 |
| **查看备份** | `ls -lah /root \| grep project_code_backup` |

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

### 使用备份脚本（推荐）
```bash
# 使用备份脚本（如果已上传到服务器）
bash /root/project_code/scripts/deployment/服务器备份脚本.sh

# 使用恢复脚本
bash /root/project_code/scripts/deployment/服务器恢复脚本.sh project_code_backup_20260127_140000
```

---

📖 **完整文档**：查看 [Linux服务器常用命令.md](./Linux服务器常用命令.md)
