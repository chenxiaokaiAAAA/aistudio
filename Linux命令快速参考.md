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
| **数据库导入** | `sudo -u postgres psql -d pet_painting -f /root/pet_painting.sql` |
| **Redis 检查** | `redis-cli ping` 或 `python scripts/test_cache.py` |
| **Nginx 重启** | `sudo systemctl restart nginx` |
| **开机自启检查** | `systemctl is-enabled postgresql@14-main redis-server nginx aistudio` |

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

## 📦 数据库导出与导入（PostgreSQL）

### 本地 Windows 导出

```cmd
# 进入 PostgreSQL bin 目录（按实际版本修改 15/16/18）
cd "C:\Program Files\PostgreSQL\18\bin"

# 方式1：Custom 格式（需云端 PostgreSQL 版本与本地一致）
pg_dump -U postgres -d pet_painting -F c -f C:\Users\Administrator\pet_painting.dump

# 方式2：纯 SQL 格式（推荐，版本兼容性好）
pg_dump -U postgres -d pet_painting -F p -f C:\Users\Administrator\pet_painting.sql
```

### 上传到云端

```cmd
# 在本地 CMD 执行
scp C:\Users\Administrator\pet_painting.sql root@你的服务器IP:/root/
```

### 云端 Linux 导入

```bash
# 若为 .dump 格式（需 pg_restore 版本与导出时一致）
sudo -u postgres pg_restore -U postgres -d pet_painting -c /root/pet_painting.dump

# 若为 .sql 格式（推荐，兼容所有版本）
sudo -u postgres psql -d pet_painting -f /root/pet_painting.sql
```

### 导入前清空数据库（可选）

```bash
# 清空所有表后重新导入
sudo -u postgres psql -d pet_painting -c "
DO \$\$ DECLARE r RECORD;
BEGIN
  FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
    EXECUTE 'TRUNCATE TABLE \"' || r.tablename || '\" CASCADE';
  END LOOP;
END \$\$;
"
```

## 🔐 域名证书部署（HTTPS）

### 1. 上传证书到服务器

```bash
# 创建 SSL 目录
sudo mkdir -p /etc/nginx/ssl

# 上传后执行（将证书文件复制到正确位置）
sudo cp 你的证书.pem /etc/nginx/ssl/photogooo.pem
sudo cp 你的私钥.key /etc/nginx/ssl/photogooo.key
sudo chmod 644 /etc/nginx/ssl/photogooo.pem
sudo chmod 600 /etc/nginx/ssl/photogooo.key
```

### 2. 配置 Nginx

```bash
# 复制站点配置
sudo cp /root/project_code/config/nginx_linux_site.conf /etc/nginx/sites-available/aistudio

# 创建软链接
sudo ln -sf /etc/nginx/sites-available/aistudio /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 3. 验证 HTTPS

```bash
curl -I https://photogooo.com/
```

## 📦 Redis 缓存检查

### 查看 Redis 是否运行

```bash
# 检查 Redis 服务状态
sudo systemctl status redis-server

# 或
redis-cli ping
# 返回 PONG 表示正常运行
```

### 测试应用缓存

```bash
cd /root/project_code
source venv/bin/activate
python scripts/test_cache.py
# 输出 "缓存可用: 是" 表示 Redis 已正确接入应用
```

### Redis 常用命令

```bash
# 启动 Redis
sudo systemctl start redis-server

# 停止 Redis
sudo systemctl stop redis-server

# 设置开机自启
sudo systemctl enable redis-server
```

## 🔄 开机自启检查（服务器重启后自动启动）

### 一键检查所有服务是否开机自启

```bash
# 检查 PostgreSQL、Redis、Nginx、应用服务 是否已设置开机自启
systemctl is-enabled postgresql@14-main 2>/dev/null || systemctl is-enabled postgresql 2>/dev/null
systemctl is-enabled redis-server
systemctl is-enabled nginx
systemctl is-enabled aistudio

# 输出 "enabled" 表示开机自启，输出 "disabled" 表示未设置
```

### 逐个检查并设置开机自启

```bash
# PostgreSQL（Ubuntu 22.04 服务名可能为 postgresql@14-main）
systemctl is-enabled postgresql@14-main
sudo systemctl enable postgresql@14-main   # 若为 disabled 则执行此命令

# Redis
systemctl is-enabled redis-server
sudo systemctl enable redis-server

# Nginx
systemctl is-enabled nginx
sudo systemctl enable nginx

# 应用服务
systemctl is-enabled aistudio
sudo systemctl enable aistudio
```

### 一键设置全部开机自启

```bash
sudo systemctl enable postgresql@14-main redis-server nginx aistudio
```

### 查看当前运行状态

```bash
# 查看所有相关服务状态
systemctl status postgresql@14-main redis-server nginx aistudio
```

---

📖 **完整文档**：查看 [Linux服务器常用命令.md](./Linux服务器常用命令.md)
