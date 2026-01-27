# FRP Token 配置说明

## 📋 Token 配置格式

在 `frps.toml` 文件中，添加以下配置：

```toml
bindPort = 7000
auth.token = "your-secret-token-123456"
```

**重要提示：**
- Token 必须用**双引号**括起来
- Token 可以是任意字符串（建议使用随机字符串，增强安全性）

---

## 🔧 配置步骤

### 步骤1：编辑 frps.toml

在服务器上编辑配置文件：

```bash
nano /etc/frp/frps.toml
```

或使用你当前打开的文件编辑器。

### 步骤2：添加完整配置

文件内容应该是：

```toml
bindPort = 7000
auth.token = "your-secret-token-123456"
```

**示例（使用随机 token）：**

```toml
bindPort = 7000
auth.token = "aistudio-frp-token-2026-123456"
```

### 步骤3：生成安全的 Token（可选）

如果想生成一个随机 token：

```bash
# 生成随机 token
openssl rand -hex 16

# 或使用 Python
python3 -c "import secrets; print(secrets.token_hex(16))"
```

---

## 🔄 确保客户端和服务端 Token 一致

### 服务器端（frps.toml）

```toml
bindPort = 7000
auth.token = "your-secret-token-123456"  # 服务器端 token
```

### 客户端（本地 Windows 的 frpc.toml）

```toml
serverAddr = "121.43.143.59"
serverPort = 7000
auth.token = "your-secret-token-123456"  # 必须与服务器端相同

[[proxies]]
name = "print_proxy"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888
```

**⚠️ 重要：两个 token 必须完全相同！**

---

## 📝 完整配置示例

### 服务器端（/etc/frp/frps.toml）

```toml
bindPort = 7000
auth.token = "aistudio-frp-2026-secret-token"

# 可选：日志配置
log.to = "/var/log/frps.log"
log.level = "info"
log.maxDays = 7
```

### 客户端（本地 Windows 的 frpc.toml）

```toml
serverAddr = "121.43.143.59"
serverPort = 7000
auth.token = "aistudio-frp-2026-secret-token"

[[proxies]]
name = "print_proxy"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888
```

---

## 🎯 快速配置命令

在服务器上执行（替换 `your-secret-token-123456` 为你想要的 token）：

```bash
# 创建完整配置
cat > /etc/frp/frps.toml << 'EOF'
bindPort = 7000
auth.token = "your-secret-token-123456"
EOF

# 验证配置
cat /etc/frp/frps.toml

# 重启服务
systemctl restart frps

# 检查状态
systemctl status frps
```

---

## ⚠️ 常见错误

### 错误1：Token 格式错误

**错误：**
```toml
auth.token = your-secret-token-123456  # 缺少引号
```

**正确：**
```toml
auth.token = "your-secret-token-123456"  # 有引号
```

### 错误2：Token 不匹配

如果服务端和客户端 token 不一致，会看到：
```
token mismatch
```

**解决：** 确保两边的 token 完全相同（包括引号内的内容）

### 错误3：配置文件路径错误

**检查配置文件路径：**
```bash
# 服务端配置
ls -la /etc/frp/frps.toml

# 客户端配置（本地 Windows）
# 应该在 frp 目录下的 frpc.toml
```

---

## ✅ 验证配置

### 在服务器上验证

```bash
# 检查配置文件
cat /etc/frp/frps.toml

# 检查服务状态
systemctl status frps

# 检查日志
journalctl -u frps -n 20
```

### 在本地 Windows 验证

1. 检查 `frpc.toml` 中的 token 是否与服务器一致
2. 启动 FRP 客户端
3. 应该看到 "login to server success"

---

## 🔐 安全建议

1. **使用强密码作为 token**：
   - 至少 16 个字符
   - 包含字母、数字、特殊字符
   - 不要使用简单密码

2. **定期更换 token**：
   - 如果怀疑泄露，立即更换
   - 更换后需要同时更新服务端和客户端

3. **不要将 token 提交到 Git**：
   - 确保 `.gitignore` 包含配置文件
   - 或使用环境变量
