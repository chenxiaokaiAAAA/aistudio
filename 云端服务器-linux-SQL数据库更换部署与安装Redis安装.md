# Redis安装和配置指南

**更新日期**: 2026-02-04  
**状态**: 📋 Windows安装指南

---

## 🔍 检查Redis是否已安装

### 方法1: 检查命令
```bash
redis-server --version
redis-cli --version
```

如果提示"不是内部或外部命令"，说明Redis未安装或未添加到PATH。

### 方法2: 检查服务
```bash
services.msc
```
在服务列表中查找 "Redis" 服务。

---

## 📥 Windows安装Redis

### 方法1: 使用预编译版本（推荐）

1. **下载Redis for Windows**:
   - 访问: https://github.com/microsoftarchive/redis/releases
   - 或: https://github.com/tporadowski/redis/releases
   - 下载最新版本的 `Redis-x64-*.zip`

2. **解压文件**:
   - 解压到 `C:\Redis` 或任意目录（例如: `E:\Redis`）

3. **添加到PATH（可选）**:
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑"
   - 添加Redis目录路径（例如: `C:\Redis`）

4. **测试安装**:
   ```bash
   cd C:\Redis
   redis-server.exe
   ```

### 方法2: 使用WSL（Windows Subsystem for Linux）

如果已安装WSL，可以在WSL中安装Redis：

```bash
# 在WSL中执行
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

### 方法3: 使用Docker（如果已安装Docker）

```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

---

## 🚀 启动Redis服务

### 方式1: 命令行启动（临时）

```bash
# 切换到Redis目录
cd C:\Redis

# 启动Redis服务器
redis-server.exe

# 或指定配置文件
redis-server.exe redis.windows.conf
```

**注意**: 这种方式启动的Redis会在关闭命令行窗口时停止。

### 方式2: 注册为Windows服务（推荐）

#### 步骤1: 安装Redis服务

```bash
# 以管理员身份运行命令提示符
cd C:\Redis

# 安装Redis服务
redis-server.exe --service-install redis.windows.conf

# 启动Redis服务
redis-server.exe --service-start

# 查看服务状态
redis-server.exe --service-status
```

#### 步骤2: 验证服务

```bash
# 方法1: 服务管理器
services.msc
# 查找 "Redis" 服务，状态应为"正在运行"

# 方法2: 命令行
sc query Redis
```

#### 步骤3: 服务管理命令

```bash
# 启动服务
redis-server.exe --service-start

# 停止服务
redis-server.exe --service-stop

# 卸载服务
redis-server.exe --service-uninstall
```

---

## ✅ 验证Redis是否正常工作

### 方法1: 使用redis-cli

```bash
# 连接到Redis
redis-cli.exe

# 测试命令
ping
# 应该返回: PONG

# 设置一个测试值
set test "hello"

# 获取测试值
get test
# 应该返回: "hello"

# 退出
exit
```

### 方法2: 使用Python脚本

```bash
python scripts/test_cache.py
```

如果Redis正常运行，应该显示：
```
缓存可用: 是
```

---

## ⚙️ 配置Redis

### 配置文件位置

Redis配置文件通常位于Redis安装目录：
- `redis.windows.conf` (Windows)
- `redis.conf` (Linux)

### 常用配置项

```conf
# 绑定地址（0.0.0.0表示监听所有网络接口）
bind 0.0.0.0

# 端口（默认6379）
port 6379

# 密码（可选，建议设置）
# requirepass your_password_here

# 持久化（RDB）
save 900 1
save 300 10
save 60 10000

# 日志级别
loglevel notice

# 日志文件
logfile ""

# 数据库数量
databases 16
```

### 修改配置后重启服务

```bash
# 停止服务
redis-server.exe --service-stop

# 启动服务（使用新配置）
redis-server.exe --service-start
```

---

## 🔧 故障排除

### 问题1: 端口6379被占用

**错误信息**: `[ERR] Address already in use`

**解决方法**:
```bash
# 检查端口占用
netstat -ano | findstr :6379

# 如果被占用，可以：
# 1. 停止占用端口的程序
# 2. 或修改Redis配置文件中的端口
```

### 问题2: 服务无法启动

**可能原因**:
- 配置文件有错误
- 权限不足
- 端口被占用

**解决方法**:
```bash
# 检查Redis日志
# 日志通常在Redis安装目录或系统日志中

# 以管理员身份运行
# 检查配置文件语法
redis-server.exe --test-memory 1
```

### 问题3: 连接被拒绝

**错误信息**: `Error 10061 connecting to localhost:6379`

**解决方法**:
1. 确认Redis服务正在运行
2. 检查防火墙设置
3. 检查Redis配置中的 `bind` 设置

---

## 📝 项目配置

### .env文件配置

在项目根目录的 `.env` 文件中添加：

```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 测试连接

```bash
python scripts/test_cache.py
```

---

## 🎯 快速安装脚本（Windows）

创建 `scripts/setup/install_redis.bat`:

```batch
@echo off
echo ========================================
echo Redis安装脚本
echo ========================================
echo.

REM 检查是否已安装
where redis-server >nul 2>&1
if %errorlevel% == 0 (
    echo Redis已安装
    redis-server --version
    goto :check_service
)

echo Redis未安装，请先下载并安装Redis
echo 下载地址: https://github.com/tporadowski/redis/releases
echo.
echo 安装步骤:
echo 1. 下载 Redis-x64-*.zip
echo 2. 解压到 C:\Redis
echo 3. 运行此脚本注册服务
pause
exit /b 1

:check_service
echo.
echo 检查Redis服务状态...
sc query Redis >nul 2>&1
if %errorlevel% == 0 (
    echo Redis服务已注册
    sc query Redis
) else (
    echo Redis服务未注册
    echo.
    echo 是否注册为Windows服务? (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        cd C:\Redis
        redis-server.exe --service-install redis.windows.conf
        redis-server.exe --service-start
        echo Redis服务已启动
    )
)

echo.
echo ========================================
echo 安装完成
echo ========================================
pause
```

---

## 📚 相关文档

- [缓存系统使用指南](../features/缓存系统使用指南.md)
- [性能问题修复方案](../refactoring/性能问题修复方案.md)

---

**最后更新**: 2026-02-04  
**状态**: 📋 Windows安装指南
