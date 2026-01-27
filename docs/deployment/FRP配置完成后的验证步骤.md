# FRP 配置完成后的验证步骤

## ✅ 当前状态

从你的输出看：
- ✅ FRP 服务已启动：`active (running)`
- ✅ 防火墙端口已开放：7000 和 18888
- ✅ 服务已启用开机自启：`enabled`

---

## 🔍 验证配置

### 步骤1：检查端口监听

```bash
# 检查 FRP 服务端端口（7000）
netstat -tlnp | grep 7000

# 应该看到类似：
# tcp  0  0  0.0.0.0:7000  0.0.0.0:*  LISTEN  15992/frps
```

### 步骤2：检查配置文件

```bash
# 查看服务端配置
cat /etc/frp/frps.toml

# 应该看到：
# bindPort = 7000
# auth.token = "your-secret-token-123456"
```

### 步骤3：查看服务日志

```bash
# 查看 FRP 服务日志
journalctl -u frps -n 20 --no-pager

# 或实时查看
journalctl -u frps -f
```

---

## 🔧 下一步操作

### 步骤1：修改本地 Windows FRP 客户端配置

在本地 Windows 电脑上，编辑 `frpc.toml`：

```toml
serverAddr = "121.43.143.59"  # 改为服务器IP
serverPort = 7000
auth.token = "your-secret-token-123456"  # 必须与服务器端相同

[[proxies]]
name = "print_proxy"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888
```

**重要：**
- `serverAddr` 改为：`121.43.143.59`
- `auth.token` 必须与服务器端的 `/etc/frp/frps.toml` 中的 token 完全相同

### 步骤2：启动本地 Windows 服务

1. **启动打印代理服务**：
   ```cmd
   start_print_proxy.bat
   ```
   应该看到：`Running on http://0.0.0.0:8888`

2. **启动 FRP 客户端**：
   ```cmd
   cd frp_0.66.0_windows_amd64
   frpc.exe -c frpc.toml
   ```
   应该看到：
   - `login to server success`
   - `[print_proxy] start proxy success`

### 步骤3：修改管理后台配置

1. **登录管理后台**：`http://121.43.143.59/admin/`
2. **进入**：系统配置 → 打印配置
3. **修改打印代理服务地址**：
   - 从：`http://192.168.2.54:18888`
   - 改为：`http://121.43.143.59:18888`
4. **保存配置**

### 步骤4：配置阿里云安全组

在阿里云控制台：

1. **进入 ECS 实例** → **安全组** → **配置规则**
2. **添加入站规则**：
   - **端口 7000**（FRP 服务端）
     - 协议：TCP
     - 端口：7000
     - 授权对象：0.0.0.0/0
   - **端口 18888**（打印代理服务）
     - 协议：TCP
     - 端口：18888
     - 授权对象：0.0.0.0/0

---

## 🎯 完整验证流程

### 在服务器上验证

```bash
# 1. 检查服务状态
systemctl status frps --no-pager -l | head -10

# 2. 检查端口监听
netstat -tlnp | grep 7000

# 3. 查看日志（等待客户端连接）
journalctl -u frps -f
```

### 在本地 Windows 验证

1. **启动打印代理服务**：`start_print_proxy.bat`
2. **启动 FRP 客户端**：`frpc.exe -c frpc.toml`
3. **检查连接**：
   - 应该看到 "login to server success"
   - 应该看到 "[print_proxy] start proxy success"

### 测试连接

```bash
# 在服务器上测试（等待客户端连接后）
curl http://121.43.143.59:18888/health

# 应该返回 JSON 响应（如果打印代理服务正在运行）
```

---

## 📋 检查清单

- [ ] FRP 服务端已启动（`systemctl status frps` 显示 `active (running)`）
- [ ] 端口 7000 已监听（`netstat -tlnp | grep 7000`）
- [ ] 防火墙已开放端口（`ufw allow 7000/tcp` 和 `ufw allow 18888/tcp`）
- [ ] 阿里云安全组已开放端口 7000 和 18888
- [ ] 本地 Windows FRP 客户端配置已修改（`serverAddr = "121.43.143.59"`）
- [ ] 本地 Windows FRP 客户端 token 与服务器端一致
- [ ] 本地 Windows 打印代理服务已启动
- [ ] 本地 Windows FRP 客户端已启动并连接成功
- [ ] 管理后台打印代理服务地址已修改为 `http://121.43.143.59:18888`

---

## ⚠️ 常见问题

### 问题1：客户端连接失败

**检查：**
1. Token 是否一致
2. 服务器 IP 是否正确
3. 防火墙和安全组是否开放端口

### 问题2：端口未监听

**检查：**
```bash
# 检查服务是否运行
systemctl status frps

# 检查配置文件
cat /etc/frp/frps.toml

# 检查日志
journalctl -u frps -n 50
```

### 问题3：客户端显示 "token mismatch"

**解决：**
1. 检查服务器端 `/etc/frp/frps.toml` 中的 token
2. 检查客户端 `frpc.toml` 中的 token
3. 确保两者完全相同（包括引号）

---

## 🎉 配置完成

当所有步骤完成后：
1. 服务器端 FRP 服务运行正常
2. 本地 Windows FRP 客户端连接成功
3. 管理后台配置已更新
4. 可以正常使用打印功能
