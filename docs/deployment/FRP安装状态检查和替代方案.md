# FRP 安装状态检查和替代方案

## 🔍 检查安装状态

在服务器上执行以下命令检查：

```bash
# 1. 检查 FRP 是否已安装
which frps
/usr/local/bin/frps --version 2>/dev/null || echo "FRP 未安装"

# 2. 检查配置文件是否存在
ls -la /etc/frp/frps.toml 2>/dev/null || echo "配置文件不存在"

# 3. 检查服务状态
systemctl status frps 2>/dev/null || echo "服务未安装"

# 4. 检查端口是否监听
netstat -tlnp | grep 7000 || echo "端口 7000 未监听"
```

---

## 🔧 如果下载失败，使用替代方案

### 方案1：手动上传 FRP 文件（推荐）

如果 GitHub 下载失败，可以：

1. **在本地 Windows 下载**：
   - 访问：https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz
   - 下载到本地

2. **上传到服务器**：
   - 使用 WinSCP 或其他工具
   - 上传到：`/root/frp_0.66.0_linux_amd64.tar.gz`

3. **在服务器上安装**：
   ```bash
   cd /root
   tar -xzf frp_0.66.0_linux_amd64.tar.gz
   mkdir -p /etc/frp
   cp frp_0.66.0_linux_amd64/frps /usr/local/bin/
   chmod +x /usr/local/bin/frps
   ```

### 方案2：使用国内镜像源

```bash
# 使用 Gitee 镜像（如果可用）
cd /root
wget https://gitee.com/mirrors/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz

# 或使用其他镜像源
# 如果还是失败，使用方案1手动上传
```

### 方案3：使用已安装的 FRP（如果存在）

```bash
# 检查是否已有 FRP
find /root -name "frps" -type f 2>/dev/null
find /root -name "frp_*" -type d 2>/dev/null

# 如果找到，直接使用
```

---

## 🎯 完整安装脚本（包含检查）

在服务器上执行：

```bash
#!/bin/bash
echo "=========================================="
echo "检查并安装 FRP 服务端"
echo "=========================================="
echo ""

# 1. 检查是否已安装
echo "[1/6] 检查是否已安装..."
if [ -f "/usr/local/bin/frps" ]; then
    echo "✅ FRP 已安装"
    /usr/local/bin/frps --version
else
    echo "⚠️  FRP 未安装，开始安装..."
    
    # 2. 检查是否已有下载的文件
    echo ""
    echo "[2/6] 检查本地文件..."
    if [ -f "/root/frp_0.66.0_linux_amd64.tar.gz" ]; then
        echo "✅ 找到本地文件，使用本地文件"
        cd /root
    else
        echo "⚠️  本地文件不存在，尝试下载..."
        cd /root
        wget https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz
        
        if [ $? -ne 0 ]; then
            echo "❌ 下载失败"
            echo ""
            echo "请手动下载并上传："
            echo "  1. 访问: https://github.com/fatedier/frp/releases/download/v0.66.0/frp_0.66.0_linux_amd64.tar.gz"
            echo "  2. 下载到本地"
            echo "  3. 上传到服务器: /root/frp_0.66.0_linux_amd64.tar.gz"
            echo "  4. 重新运行此脚本"
            exit 1
        fi
    fi
    
    # 3. 解压
    echo ""
    echo "[3/6] 解压 FRP..."
    tar -xzf frp_0.66.0_linux_amd64.tar.gz
    
    # 4. 安装
    echo ""
    echo "[4/6] 安装 FRP..."
    mkdir -p /etc/frp
    cp frp_0.66.0_linux_amd64/frps /usr/local/bin/
    chmod +x /usr/local/bin/frps
    echo "✅ FRP 安装完成"
fi

# 5. 配置
echo ""
echo "[5/6] 配置 FRP..."
if [ ! -f "/etc/frp/frps.toml" ]; then
    cat > /etc/frp/frps.toml << 'EOF'
bindPort = 7000
auth.token = "your-secret-token-123456"
EOF
    echo "✅ 配置文件已创建"
    echo "⚠️  请修改 token: nano /etc/frp/frps.toml"
else
    echo "✅ 配置文件已存在"
fi

# 6. 创建 systemd 服务
echo ""
echo "[6/6] 创建 systemd 服务..."
if [ ! -f "/etc/systemd/system/frps.service" ]; then
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
    echo "✅ 服务已创建并启用"
else
    echo "✅ 服务已存在"
fi

# 7. 启动服务
echo ""
echo "启动服务..."
systemctl start frps
sleep 2

# 8. 检查状态
echo ""
echo "=========================================="
echo "安装完成，检查状态"
echo "=========================================="
systemctl status frps --no-pager -l | head -15

echo ""
echo "检查端口..."
netstat -tlnp | grep 7000 || echo "⚠️  端口 7000 未监听"

echo ""
echo "=========================================="
echo "下一步："
echo "  1. 修改 token: nano /etc/frp/frps.toml"
echo "  2. 重启服务: systemctl restart frps"
echo "  3. 在本地 Windows 修改 frpc.toml"
echo "  4. 在管理后台修改打印代理服务地址"
echo "=========================================="
```

---

## 📝 快速检查命令

执行以下命令快速检查：

```bash
# 一键检查
echo "=== FRP 安装状态 ===" && \
echo "FRP 可执行文件:" && \
ls -la /usr/local/bin/frps 2>/dev/null || echo "❌ 未安装" && \
echo "" && \
echo "配置文件:" && \
ls -la /etc/frp/frps.toml 2>/dev/null || echo "❌ 配置文件不存在" && \
echo "" && \
echo "服务状态:" && \
systemctl status frps --no-pager -l 2>/dev/null | head -5 || echo "❌ 服务未安装" && \
echo "" && \
echo "端口监听:" && \
netstat -tlnp | grep 7000 || echo "❌ 端口未监听"
```
