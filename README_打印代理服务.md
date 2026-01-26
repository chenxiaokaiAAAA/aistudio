# 打印代理服务使用说明

## 概述

当项目部署到阿里云等远程服务器时，无法直接访问本地局域网打印机。打印代理服务解决了这个问题：

**架构：**
```
阿里云服务器 → HTTP API → 打印代理服务（本地） → 本地打印机
```

## 部署场景说明

### 场景1：服务器在阿里云，打印机在门店（无固定IP）✅ **您的情况**

**架构：**
```
阿里云服务器 → 内网穿透/动态DNS → 打印代理服务（门店本地） → 本地打印机
```

**解决方案：**
1. **在门店电脑运行打印代理服务**（`print_proxy_server.py`）
2. **使用内网穿透工具**将本地服务暴露到公网（推荐）
3. **或使用动态DNS服务**（如果有域名）

**推荐方案：内网穿透**
- **frp**（免费，开源）：https://github.com/fatedier/frp
- **ngrok**（免费版有限制）：https://ngrok.com
- **花生壳**（国内，有免费版）：https://hsk.oray.com
- **ZeroTier**（VPN方案，免费）：https://www.zerotier.com

### 场景2：服务器和打印机在同一局域网

直接使用本地打印机路径：`\\sm003\HP OfficeJet Pro 7730 series`

### 场景3：服务器和打印机通过VPN连接

使用内网IP：`http://192.168.1.100:8888`

---

## 部署步骤

### 1. 在门店本地运行打印代理服务

#### 方法一：直接运行（开发/测试）

```bash
# 安装依赖
pip install flask flask-cors pywin32 requests

# 设置环境变量（可选）
set LOCAL_PRINTER_PATH=\\sm003\HP OfficeJet Pro 7730 series
set PRINT_PROXY_PORT=8888
set PRINT_PROXY_API_KEY=your-secret-key

# 运行服务
python print_proxy_server.py
```

#### 方法二：作为Windows服务运行（生产环境）

1. 使用 `nssm`（Non-Sucking Service Manager）将Python脚本注册为Windows服务：

```bash
# 下载nssm: https://nssm.cc/download
# 安装服务
nssm install PrintProxyService "C:\Python\python.exe" "C:\path\to\print_proxy_server.py"
nssm set PrintProxyService AppEnvironmentExtra LOCAL_PRINTER_PATH=\\sm003\HP OfficeJet Pro 7730 series
nssm set PrintProxyService AppEnvironmentExtra PRINT_PROXY_PORT=8888
nssm set PrintProxyService AppEnvironmentExtra PRINT_PROXY_API_KEY=your-secret-key

# 启动服务
nssm start PrintProxyService
```

### 2. 配置网络访问（无固定IP的解决方案）

#### 方案A：使用frp内网穿透（推荐，免费开源）⭐

**步骤：**

1. **准备一台有公网IP的服务器**（可以是阿里云轻量应用服务器，最便宜的即可）

2. **在公网服务器安装frp服务端：**
```bash
# 下载frp: https://github.com/fatedier/frp/releases
# 解压后，编辑 frps.ini
[common]
bind_port = 7000  # frp服务端端口
token = your-secret-token  # 安全令牌

# 启动服务端
./frps -c frps.ini
```

3. **在门店电脑安装frp客户端：**
```bash
# 下载frp客户端
# 编辑 frpc.ini
[common]
server_addr = your-frp-server-ip  # 公网服务器IP
server_port = 7000
token = your-secret-token

[print_proxy]
type = tcp
local_ip = 127.0.0.1
local_port = 8888
remote_port = 18888  # 公网服务器上的端口

# 启动客户端
frpc.exe -c frpc.ini
```

4. **在阿里云配置中使用：**
```
http://your-frp-server-ip:18888
```

**优点：**
- 完全免费
- 稳定可靠
- 可以设置多个门店

#### 方案B：使用花生壳（国内，简单易用）

1. **注册花生壳账号**：https://hsk.oray.com
2. **下载花生壳客户端**并登录
3. **添加内网映射**：
   - 应用名称：打印代理服务
   - 内网主机：127.0.0.1
   - 内网端口：8888
   - 外网域名：系统自动分配（如：xxxxx.gicp.net）
   - 外网端口：系统分配

4. **在阿里云配置中使用：**
```
http://xxxxx.gicp.net:端口号
```

**优点：**
- 国内服务，速度快
- 操作简单
- 有免费版（有限制）

#### 方案C：使用ZeroTier（VPN方案，免费）

1. **注册ZeroTier账号**：https://www.zerotier.com
2. **创建网络**，获取Network ID
3. **在门店电脑和阿里云服务器都安装ZeroTier客户端**
4. **两台机器都加入同一个网络**
5. **获取门店电脑的ZeroTier IP**（如：10.147.20.100）

6. **在阿里云配置中使用：**
```
http://10.147.20.100:8888
```

**优点：**
- 完全免费
- 安全性高（加密VPN）
- 不需要公网服务器

#### 方案D：使用ngrok（简单但有限制）

```bash
# 下载ngrok: https://ngrok.com
# 注册账号获取authtoken
ngrok authtoken your-token

# 启动隧道
ngrok http 8888

# 会得到一个公网地址，如：https://xxxxx.ngrok.io
# 在阿里云配置中使用：https://xxxxx.ngrok.io
```

**注意：** 免费版每次重启地址会变化，需要手动更新配置

### 3. 在阿里云服务器配置

1. 登录管理后台
2. 访问"打印配置"页面
3. 填写"打印代理服务地址"：
   - **frp方案**：`http://your-frp-server-ip:18888`
   - **花生壳方案**：`http://xxxxx.gicp.net:端口号`
   - **ZeroTier方案**：`http://10.147.20.100:8888`（ZeroTier内网IP）
   - **ngrok方案**：`https://xxxxx.ngrok.io`
4. 填写"打印代理服务API密钥"（如果设置了，建议设置以提高安全性）
5. 点击"测试打印空白页"按钮，验证配置是否正确
6. 保存配置

### 4. 测试连接

在打印配置页面，点击"测试打印空白页"按钮：
- ✅ 如果成功：会打印一张空白测试页，说明配置正确
- ❌ 如果失败：检查网络连接、防火墙、内网穿透服务是否正常运行

## 安全建议

1. **使用API密钥**：设置 `PRINT_PROXY_API_KEY` 环境变量
2. **使用HTTPS**：如果通过公网访问，建议使用HTTPS（需要配置SSL证书）
3. **防火墙规则**：只允许特定IP访问打印代理服务端口
4. **内网穿透**：优先使用内网穿透，避免直接暴露到公网

## 测试

### 测试打印代理服务

```bash
# 健康检查
curl http://localhost:8888/health

# 测试打印（需要提供图片URL）
curl -X POST http://localhost:8888/print \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "image_url": "http://example.com/image.jpg",
    "copies": 1
  }'
```

### 从阿里云测试

在管理后台的打印配置页面，点击"测试连接"按钮（如果实现了该功能）。

## 故障排查

1. **无法连接打印代理服务**
   - 检查服务是否运行：`netstat -an | findstr 8888`
   - 检查防火墙是否开放端口
   - 检查网络连接（VPN、内网穿透等）

2. **打印失败**
   - 检查打印机是否在线
   - 检查打印机路径是否正确
   - 查看打印代理服务日志

3. **权限问题**
   - 确保运行服务的用户有打印权限
   - 检查打印机共享设置

## 依赖安装

```bash
pip install flask flask-cors pywin32 requests
```

## 注意事项

- 打印代理服务必须运行在可以访问打印机的Windows机器上
- 确保图片URL可以从打印代理服务所在机器访问（可能需要配置内网访问）
- 建议使用内网穿透或VPN，避免直接暴露到公网
