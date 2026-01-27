# Linux 服务器常用命令参考

## 📋 服务管理（Systemd）

### 启动服务

```bash
# 启动 aistudio 服务
systemctl start aistudio

# 启动 Nginx
systemctl start nginx

# 启动 FRP 服务端
systemctl start frps
```

### 停止服务

```bash
# 停止 aistudio 服务
systemctl stop aistudio

# 停止 Nginx
systemctl stop nginx

# 停止 FRP 服务端
systemctl stop frps
```

### 重启服务

```bash
# 重启 aistudio 服务
systemctl restart aistudio

# 重启 Nginx
systemctl restart nginx

# 重启 FRP 服务端
systemctl restart frps
```

### 查看服务状态

```bash
# 查看 aistudio 服务状态
systemctl status aistudio

# 查看 Nginx 状态
systemctl status nginx

# 查看 FRP 服务端状态
systemctl status frps

# 查看所有服务状态（简短）
systemctl list-units --type=service --state=running
```

### 启用/禁用开机自启

```bash
# 启用 aistudio 开机自启
systemctl enable aistudio

# 禁用 aistudio 开机自启
systemctl disable aistudio

# 查看是否已启用开机自启
systemctl is-enabled aistudio
```

## 📊 日志查看

### 实时查看日志（推荐）

```bash
# 实时查看 aistudio 服务日志（最常用）
journalctl -u aistudio -f

# 实时查看 Nginx 错误日志
tail -f /var/log/nginx/error.log

# 实时查看 Nginx 访问日志
tail -f /var/log/nginx/access.log

# 实时查看应用日志文件
tail -f /root/project_code/app.log

# 实时查看 Gunicorn 错误日志
tail -f /root/project_code/logs/error.log

# 实时查看 Gunicorn 访问日志
tail -f /root/project_code/logs/access.log
```

### 查看最近日志

```bash
# 查看 aistudio 最近 100 行日志
journalctl -u aistudio -n 100

# 查看最近 50 行日志（带时间戳）
journalctl -u aistudio -n 50 --no-pager

# 查看今天的日志
journalctl -u aistudio --since today

# 查看最近 1 小时的日志
journalctl -u aistudio --since "1 hour ago"

# 查看指定时间段的日志
journalctl -u aistudio --since "2026-01-27 10:00:00" --until "2026-01-27 12:00:00"
```

### 搜索日志

```bash
# 搜索包含 "error" 的日志
journalctl -u aistudio | grep -i error

# 搜索包含 "401" 的日志
journalctl -u aistudio | grep 401

# 搜索最近的错误日志
journalctl -u aistudio -p err -n 50
```

### 查看日志文件

```bash
# 查看应用日志（最后 100 行）
tail -n 100 /root/project_code/app.log

# 查看应用日志（最后 50 行，实时更新）
tail -n 50 -f /root/project_code/app.log

# 查看 Gunicorn 错误日志
cat /root/project_code/logs/error.log

# 查看 Gunicorn 访问日志（最后 100 行）
tail -n 100 /root/project_code/logs/access.log
```

## 🔍 进程管理

### 查看进程

```bash
# 查看所有 Python 进程
ps aux | grep python

# 查看 Gunicorn 进程
ps aux | grep gunicorn

# 查看进程树
pstree -p | grep python

# 查看进程详细信息
ps -ef | grep gunicorn
```

### 杀死进程

```bash
# 根据进程名杀死（谨慎使用）
pkill -f gunicorn

# 根据 PID 杀死进程
kill 12345

# 强制杀死进程
kill -9 12345

# 杀死所有 Python 进程（谨慎使用）
killall python
```

### 查看端口占用

```bash
# 查看端口 8000 是否被占用
netstat -tuln | grep 8000

# 或者使用 ss 命令（更现代）
ss -tuln | grep 8000

# 查看所有监听端口
netstat -tuln

# 查看端口占用及进程
lsof -i :8000

# 或者
netstat -tulnp | grep 8000
```

## 📁 文件操作

### 查看文件

```bash
# 查看文件内容
cat /root/project_code/test_server.py

# 分页查看文件
less /root/project_code/test_server.py

# 查看文件前 20 行
head -n 20 /root/project_code/test_server.py

# 查看文件后 20 行
tail -n 20 /root/project_code/test_server.py

# 查看文件大小
ls -lh /root/project_code/test_server.py

# 查看目录大小
du -sh /root/project_code/
```

### 编辑文件

```bash
# 使用 nano 编辑（推荐新手）
nano /root/project_code/test_server.py

# 使用 vim 编辑
vim /root/project_code/test_server.py

# 使用 vi 编辑
vi /root/project_code/test_server.py
```

### 文件权限

```bash
# 修改文件权限
chmod 644 /root/project_code/test_server.py

# 修改目录权限（递归）
chmod -R 755 /root/project_code/static

# 修改文件所有者
chown root:root /root/project_code/test_server.py

# 修改目录所有者（递归）
chown -R root:root /root/project_code/
```

### 查找文件

```bash
# 查找文件
find /root/project_code -name "*.py"

# 查找文件（忽略大小写）
find /root/project_code -iname "*.log"

# 查找最近修改的文件
find /root/project_code -type f -mtime -1
```

## 🌐 网络检查

### 测试连接

```bash
# 测试本地端口
curl http://localhost:8000/health

# 测试公网访问
curl http://121.43.143.59/health

# 测试端口是否开放
telnet localhost 8000

# 或者使用 nc
nc -zv localhost 8000
```

### 查看网络连接

```bash
# 查看所有网络连接
netstat -an

# 查看 TCP 连接
netstat -ant

# 查看监听端口
netstat -tuln

# 查看网络统计
netstat -s
```

### 防火墙

```bash
# 查看防火墙状态（Ubuntu/Debian）
ufw status

# 查看防火墙状态（CentOS/RHEL）
firewall-cmd --state

# 开放端口（Ubuntu/Debian）
ufw allow 8000/tcp

# 开放端口（CentOS/RHEL）
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

## 💾 数据库操作

### SQLite 数据库

```bash
# 进入 SQLite 命令行
sqlite3 /root/project_code/instance/pet_painting.db

# 在 SQLite 中执行命令
sqlite3 /root/project_code/instance/pet_painting.db "SELECT * FROM users LIMIT 5;"

# 备份数据库
cp /root/project_code/instance/pet_painting.db /root/project_code/instance/pet_painting.db.backup

# 查看数据库文件大小
ls -lh /root/project_code/instance/pet_painting.db
```

### 数据库常用 SQL 命令

```sql
-- 查看所有表
.tables

-- 查看表结构
.schema users

-- 查看表数据
SELECT * FROM users LIMIT 10;

-- 退出
.quit
```

## 🔧 系统信息

### 系统资源

```bash
# 查看 CPU 使用率
top

# 或者使用 htop（如果已安装）
htop

# 查看内存使用
free -h

# 查看磁盘使用
df -h

# 查看磁盘使用详情
du -sh /root/project_code/*

# 查看系统负载
uptime
```

### 系统信息

```bash
# 查看系统版本
cat /etc/os-release

# 查看内核版本
uname -r

# 查看系统运行时间
uptime

# 查看当前用户
whoami

# 查看当前目录
pwd
```

## 🐍 Python 环境

### 虚拟环境

```bash
# 激活虚拟环境
source /root/project_code/venv/bin/activate

# 退出虚拟环境
deactivate

# 查看已安装的包
pip list

# 安装依赖
pip install -r /root/project_code/requirements.txt
```

### Python 脚本

```bash
# 运行 Python 脚本
python3 /root/project_code/test_server.py

# 使用虚拟环境的 Python
/root/project_code/venv/bin/python test_server.py
```

## 🔄 常用组合命令

### 一键重启服务

```bash
# 停止服务 → 等待 → 启动服务
systemctl stop aistudio && sleep 2 && systemctl start aistudio

# 重启服务并查看状态
systemctl restart aistudio && systemctl status aistudio
```

### 查看服务并查看日志

```bash
# 查看服务状态，然后查看日志
systemctl status aistudio && journalctl -u aistudio -n 50
```

### 清理日志

```bash
# 清理旧的 systemd 日志（保留最近 7 天）
journalctl --vacuum-time=7d

# 清理日志文件（保留最近 100MB）
journalctl --vacuum-size=100M
```

### 快速检查服务健康

```bash
# 检查服务状态、端口、日志
echo "=== 服务状态 ===" && \
systemctl status aistudio --no-pager -l && \
echo -e "\n=== 端口监听 ===" && \
netstat -tuln | grep 8000 && \
echo -e "\n=== 最近日志 ===" && \
journalctl -u aistudio -n 20 --no-pager
```

## 📝 常用快捷命令（别名）

可以将以下内容添加到 `~/.bashrc` 或 `~/.bash_aliases`：

```bash
# 编辑配置文件
nano ~/.bashrc

# 添加以下别名
alias aistudio-start='systemctl start aistudio'
alias aistudio-stop='systemctl stop aistudio'
alias aistudio-restart='systemctl restart aistudio'
alias aistudio-status='systemctl status aistudio'
alias aistudio-logs='journalctl -u aistudio -f'
alias aistudio-logs-tail='journalctl -u aistudio -n 100'
alias nginx-restart='systemctl restart nginx'
alias nginx-logs='tail -f /var/log/nginx/error.log'
alias app-logs='tail -f /root/project_code/app.log'
alias cd-project='cd /root/project_code'
```

然后执行：
```bash
source ~/.bashrc
```

之后就可以使用：
```bash
aistudio-start    # 启动服务
aistudio-stop     # 停止服务
aistudio-restart  # 重启服务
aistudio-logs     # 实时查看日志
```

## 🚨 紧急情况处理

### 服务无法启动

```bash
# 1. 查看详细错误
systemctl status aistudio -l

# 2. 查看完整日志
journalctl -u aistudio -n 100 --no-pager

# 3. 检查配置文件
cat /etc/systemd/system/aistudio.service

# 4. 检查 Python 环境
/root/project_code/venv/bin/python --version

# 5. 手动测试启动
cd /root/project_code && /root/project_code/venv/bin/python start_production.py
```

### 端口被占用

```bash
# 1. 查找占用端口的进程
lsof -i :8000

# 2. 杀死占用进程
kill -9 <PID>

# 3. 或者使用
fuser -k 8000/tcp
```

### 磁盘空间不足

```bash
# 1. 查看磁盘使用
df -h

# 2. 查找大文件
find /root/project_code -type f -size +100M

# 3. 清理日志
journalctl --vacuum-time=3d

# 4. 清理临时文件
rm -rf /tmp/*
```

## 📚 其他有用命令

### 压缩/解压

```bash
# 压缩目录
tar -czf backup.tar.gz /root/project_code

# 解压文件
tar -xzf backup.tar.gz

# 解压 zip 文件
unzip file.zip
```

### 文件传输

```bash
# 从本地上传到服务器（在本地执行）
scp file.txt root@121.43.143.59:/root/project_code/

# 从服务器下载到本地（在本地执行）
scp root@121.43.143.59:/root/project_code/file.txt ./
```

### 定时任务

```bash
# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e

# 查看 cron 日志
grep CRON /var/log/syslog
```

## 💡 提示

1. **使用 Tab 键自动补全**：输入命令时按 Tab 键可以自动补全
2. **使用上下箭头**：可以快速访问历史命令
3. **使用 Ctrl+C**：可以中断正在运行的命令
4. **使用 Ctrl+D**：可以退出当前会话
5. **使用 `man` 命令**：查看命令帮助，如 `man systemctl`
6. **使用 `--help`**：查看命令选项，如 `systemctl --help`

## 🔗 相关文档

- [服务启动说明](./服务启动说明.md)
- [查看详细错误日志](./查看详细错误日志.md)
- [实时查看应用日志](./实时查看应用日志.md)
- [验证服务是否正常运行](./验证服务是否正常运行.md)
