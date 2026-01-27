# FRP 从 Windows 迁移到 Linux 服务器

## 📋 迁移概述

**之前配置：**
- FRP 服务端：本地 Windows（192.168.2.54）
- 打印代理服务地址：`http://192.168.2.54:18888`

**现在配置：**
- FRP 服务端：Linux 服务器（121.43.143.59）
- 打印代理服务地址：`http://121.43.143.59:18888`

---

## 🔧 迁移步骤

### 步骤1：在 Linux 服务器上安装 FRP 服务端

```bash
# 1. 下载 FRP（Linux 版本）
cd /root
wget https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz

# 2. 解压
tar -xzf frp_0.66.0_linux_amd64.tar.gz
cd frp_0.66.0_linux_amd64

# 3. 创建配置目录
mkdir -p /etc/frp
cp frps /usr/local/bin/
chmod +x /usr/local/bin/frps
```

### 步骤2：配置 FRP 服务端（Linux）

```bash
# 创建配置文件
cat > /etc/frp/frps.toml << 'EOF'
bindPort = 7000
auth.token = "your-secret-token-123456"  # 使用之前的 token，或生成新的
EOF

# 或者使用 ini 格式（如果版本较旧）
cat > /etc/frp/frps.ini << 'EOF'
[common]
bind_port = 7000
token = your-secret-token-123456
EOF
```

### 步骤3：创建 Systemd 服务（Linux）

```bash
# 创建 systemd 服务文件
cat > /etc/systemd/system/frps.service << 'EOF'
[Unit]
Description=FRP Server
After=network.target

[Service]
Type=simple
User=root
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
systemctl daemon-reload

# 启动并启用开机自启
systemctl enable frps
systemctl start frps

# 检查状态
systemctl status frps
```

### 步骤4：配置防火墙（Linux）

```bash
# 开放 FRP 服务端端口（7000）
ufw allow 7000/tcp

# 开放 FRP 远程端口（18888，根据你的配置调整）
ufw allow 18888/tcp

# 如果使用阿里云，还需要在安全组中开放这些端口
```

### 步骤5：修改本地 Windows FRP 客户端配置

**文件：`frpc.toml`（在本地 Windows 电脑上）**

```toml
serverAddr = "121.43.143.59"  # 改为服务器IP
serverPort = 7000
auth.token = "your-secret-token-123456"  # 使用相同的 token

[[proxies]]
name = "print_proxy"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888  # 远程端口保持不变
```

**或者使用 ini 格式：**

```ini
[common]
server_addr = 121.43.143.59  # 改为服务器IP
server_port = 7000
token = your-secret-token-123456

[print_proxy]
type = tcp
local_ip = 127.0.0.1
local_port = 8888
remote_port = 18888
```

### 步骤6：修改管理后台配置

1. **登录管理后台**：`http://121.43.143.59/admin/`
2. **进入**：系统配置 → 打印配置
3. **修改打印代理服务地址**：
   - 从：`http://192.168.2.54:18888`
   - 改为：`http://121.43.143.59:18888`
4. **保存配置**

---

## 🎯 完整迁移脚本（Linux 服务器端）

在 Linux 服务器上执行：

```bash
#!/bin/bash
echo "=========================================="
echo "在 Linux 服务器上安装 FRP 服务端"
echo "=========================================="
echo ""

# 1. 下载 FRP
echo "[1/5] 下载 FRP..."
cd /root
if [ ! -f "frp_0.66.0_linux_amd64.tar.gz" ]; then
    wget https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz
else
    echo "✅ FRP 已下载"
fi

# 2. 解压
echo ""
echo "[2/5] 解压 FRP..."
if [ ! -d "frp_0.66.0_linux_amd64" ]; then
    tar -xzf frp_0.66.0_linux_amd64.tar.gz
else
    echo "✅ FRP 已解压"
fi

# 3. 安装
echo ""
echo "[3/5] 安装 FRP..."
mkdir -p /etc/frp
cp frp_0.66.0_linux_amd64/frps /usr/local/bin/
chmod +x /usr/local/bin/frps

# 4. 配置
echo ""
echo "[4/5] 配置 FRP 服务端..."
cat > /etc/frp/frps.toml << 'EOF'
bindPort = 7000
auth.token = "your-secret-token-123456"
EOF

echo "✅ 配置文件已创建: /etc/frp/frps.toml"
echo ""
echo "⚠️  请修改 token："
echo "   nano /etc/frp/frps.toml"
echo ""

# 5. 创建 systemd 服务
echo "[5/5] 创建 systemd 服务..."
cat > /etc/systemd/system/frps.service << 'EOF'
[Unit]
Description=FRP Server
After=network.target

[Service]
Type=simple
User=root
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable frps
systemctl start frps

echo ""
echo "检查服务状态..."
systemctl status frps --no-pager -l | head -15

echo ""
echo "=========================================="
echo "✅ FRP 服务端安装完成"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 修改 /etc/frp/frps.toml 中的 token"
echo "  2. 在本地 Windows 修改 frpc.toml，将 serverAddr 改为 121.43.143.59"
echo "  3. 在管理后台修改打印代理服务地址为 http://121.43.143.59:18888"
echo "  4. 重启本地 Windows 的 FRP 客户端"
```

---

## 📝 验证配置

### 在 Linux 服务器上验证

```bash
# 1. 检查 FRP 服务端是否运行
systemctl status frps

# 2. 检查端口是否监听
netstat -tlnp | grep 7000

# 3. 查看日志
journalctl -u frps -f
```

### 在本地 Windows 上验证

1. **启动打印代理服务**：`start_print_proxy.bat`
2. **启动 FRP 客户端**：`启动客户端.bat`
3. **检查连接**：
   - 应该看到 "login to server success"
   - 应该看到 "[print_proxy] start proxy success"

### 在管理后台验证

1. **测试连接**：
   ```bash
   # 在服务器上测试
   curl http://121.43.143.59:18888/health
   ```
   应该返回 JSON 响应

2. **在管理后台测试打印**：
   - 进入订单管理
   - 选择一个订单
   - 点击打印
   - 检查是否成功

---

## 🔄 如果之前使用的是 ini 格式

如果之前使用的是 `frps.ini` 格式，可以继续使用：

```bash
# 创建 ini 格式配置
cat > /etc/frp/frps.ini << 'EOF'
[common]
bind_port = 7000
token = your-secret-token-123456
EOF

# 修改 systemd 服务
sed -i 's|frps.toml|frps.ini|' /etc/systemd/system/frps.service

# 重启服务
systemctl restart frps
```

---

## ⚠️ 重要提示

1. **Token 必须一致**：
   - Linux 服务器上的 `frps.toml` 中的 token
   - 本地 Windows 上的 `frpc.toml` 中的 token
   - 必须完全相同

2. **防火墙配置**：
   - Linux 服务器：开放 7000 和 18888 端口
   - 阿里云安全组：也需要开放这些端口

3. **本地 Windows 配置**：
   - 修改 `frpc.toml` 中的 `serverAddr` 为 `121.43.143.59`
   - 重启 FRP 客户端

4. **管理后台配置**：
   - 修改打印代理服务地址为 `http://121.43.143.59:18888`
   - 保存配置

---

## 🎯 快速迁移命令

在 Linux 服务器上执行：

```bash
cd /root && \
wget -q https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz && \
tar -xzf frp_0.66.0_linux_amd64.tar.gz && \
mkdir -p /etc/frp && \
cp frp_0.66.0_linux_amd64/frps /usr/local/bin/ && \
chmod +x /usr/local/bin/frps && \
cat > /etc/frp/frps.toml << 'EOF'
bindPort = 7000
auth.token = "your-secret-token-123456"
EOF
cat > /etc/systemd/system/frps.service << 'EOF'
[Unit]
Description=FRP Server
After=network.target
[Service]
Type=simple
User=root
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && \
systemctl enable frps && \
systemctl start frps && \
systemctl status frps --no-pager -l | head -10
```

**⚠️ 记得修改 token！**
