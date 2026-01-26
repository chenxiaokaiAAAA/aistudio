# 多门店frp配置方案

## 问题

如果多个门店都使用同一个frp服务端地址（如 `http://192.168.2.54:18888`），后台无法区分打印任务应该发送到哪个门店的打印机。

## 解决方案：每个门店使用不同的frp远程端口

### 架构图

```
阿里云服务器（frp服务端）
├── 端口 18888 → 映射到门店A的打印代理服务
├── 端口 18889 → 映射到门店B的打印代理服务
├── 端口 18890 → 映射到门店C的打印代理服务
└── ...

门店A（sm003）
├── frp客户端：本地8888 → 远程18888
├── print_proxy_server：监听8888端口
└── 打印机：\\sm003\HP OfficeJet Pro 7730 series

门店B（printer-bj）
├── frp客户端：本地8888 → 远程18889
├── print_proxy_server：监听8888端口
└── 打印机：\\printer-bj\Canon PIXMA
```

## 配置步骤

### 步骤1：在阿里云服务器上配置frp服务端

**文件：`frps.toml`**

```toml
bindPort = 7000
auth.token = "your-secret-token-123456"
```

**说明：**
- frp服务端只需要监听一个端口（7000）用于客户端连接
- 远程端口（18888, 18889等）由客户端配置时指定

### 步骤2：为每个门店配置frp客户端

#### 门店A（sm003）配置

**文件：`frpc.toml`（门店A）**

```toml
serverAddr = "192.168.2.54"
serverPort = 7000
auth.token = "your-secret-token-123456"

[[proxies]]
name = "print_proxy_store_a"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888  # 门店A使用18888端口
```

**后台配置：**
- 自拍机序列号：`XMSM_001`
- 打印代理服务地址：`http://192.168.2.54:18888`
- API密钥：`test-key-123`

#### 门店B配置

**文件：`frpc.toml`（门店B）**

```toml
serverAddr = "192.168.2.54"
serverPort = 7000
auth.token = "your-secret-token-123456"

[[proxies]]
name = "print_proxy_store_b"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18889  # 门店B使用18889端口（不同）
```

**后台配置：**
- 自拍机序列号：`BJSM_001`
- 打印代理服务地址：`http://192.168.2.54:18889`  （不同的端口）
- API密钥：`test-key-123`

#### 门店C配置

**文件：`frpc.toml`（门店C）**

```toml
serverAddr = "192.168.2.54"
serverPort = 7000
auth.token = "your-secret-token-123456"

[[proxies]]
name = "print_proxy_store_c"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18890  # 门店C使用18890端口（不同）
```

**后台配置：**
- 自拍机序列号：`SHSM_001`
- 打印代理服务地址：`http://192.168.2.54:18890`  （不同的端口）
- API密钥：`test-key-123`

## 完整配置示例

### 门店A（sm003）完整配置

#### 1. frp客户端配置

**文件：`frpc.toml`**

```toml
serverAddr = "192.168.2.54"
serverPort = 7000
auth.token = "your-secret-token-123456"

[[proxies]]
name = "print_proxy_sm003"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888
```

#### 2. 启动frp客户端

**文件：`启动客户端.bat`**

```batch
chcp 65001 >nul
@echo off
echo ========================================
echo 启动frp客户端（sm003门店）
echo ========================================
echo.
echo 连接服务端: 192.168.2.54:7000
echo 本地打印服务: 127.0.0.1:8888
echo 映射到远程端口: 18888
echo.
echo 按 Ctrl+C 停止服务
echo.
cd /d %~dp0
frpc.exe -c frpc.toml
pause
```

#### 3. 启动打印代理服务

**文件：`start_print_proxy.bat`**

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo 启动打印代理服务
echo ========================================
echo.
echo 打印机路径: \\sm003\HP OfficeJet Pro 7730 series
echo 服务端口: 8888
echo API密钥: test-key-123
echo.
echo 正在启动服务...
echo.

set LOCAL_PRINTER_PATH=\\sm003\HP OfficeJet Pro 7730 series
set PRINT_PROXY_PORT=8888
set PRINT_PROXY_API_KEY=test-key-123

python print_proxy_server.py

pause
```

#### 4. 后台配置

**访问：** `/admin/printer`

**门店打印机配置：**
- 自拍机序列号：`XMSM_001`
- 打印代理服务地址：`http://192.168.2.54:18888`
- API密钥：`test-key-123`

### 门店B完整配置

#### 1. frp客户端配置

**文件：`frpc.toml`**

```toml
serverAddr = "192.168.2.54"
serverPort = 7000
auth.token = "your-secret-token-123456"

[[proxies]]
name = "print_proxy_store_b"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18889  # 注意：使用不同的端口
```

#### 2. 启动打印代理服务

**文件：`start_print_proxy.bat`**

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo 启动打印代理服务（门店B）
echo ========================================
echo.
echo 打印机路径: \\printer-bj\Canon PIXMA
echo 服务端口: 8888
echo API密钥: test-key-123
echo.

set LOCAL_PRINTER_PATH=\\printer-bj\Canon PIXMA
set PRINT_PROXY_PORT=8888
set PRINT_PROXY_API_KEY=test-key-123

python print_proxy_server.py

pause
```

#### 3. 后台配置

**访问：** `/admin/printer`

**门店打印机配置：**
- 自拍机序列号：`BJSM_001`
- 打印代理服务地址：`http://192.168.2.54:18889`  （注意：不同的端口）
- API密钥：`test-key-123`

## 工作流程

### 订单打印流程

1. **订单关联自拍机**
   - 订单：`order.selfie_machine_id = 'XMSM_001'`

2. **查找打印机配置**
   - 根据 `XMSM_001` 查找配置
   - 返回：`http://192.168.2.54:18888`

3. **发送打印请求**
   - 请求发送到：`http://192.168.2.54:18888`
   - frp服务端将请求转发到门店A的frp客户端
   - frp客户端将请求转发到本地8888端口的print_proxy_server
   - print_proxy_server使用门店A的打印机打印

### 区分不同门店

**后台通过不同的frp远程端口来区分：**

- 门店A（XMSM_001）：
  - 后台配置：`http://192.168.2.54:18888`
  - frp映射：18888 → 门店A的8888端口
  - 打印机：`\\sm003\HP OfficeJet Pro 7730 series`

- 门店B（BJSM_001）：
  - 后台配置：`http://192.168.2.54:18889`  （不同的端口）
  - frp映射：18889 → 门店B的8888端口
  - 打印机：`\\printer-bj\Canon PIXMA`

## 端口分配建议

### 端口范围

建议使用 `18888` 开始的端口范围，每个门店递增：

- 门店A：`18888`
- 门店B：`18889`
- 门店C：`18890`
- 门店D：`18891`
- ...

### 端口冲突检查

在配置前，确保端口未被占用：

```bash
# Windows
netstat -an | findstr "18888"
netstat -an | findstr "18889"

# Linux
netstat -tuln | grep 18888
netstat -tuln | grep 18889
```

## 配置检查清单

### 门店A（sm003）

- [ ] frp客户端配置：`remotePort = 18888`
- [ ] print_proxy_server配置：`LOCAL_PRINTER_PATH=\\sm003\HP OfficeJet Pro 7730 series`
- [ ] 后台配置：打印代理服务地址 = `http://192.168.2.54:18888`
- [ ] frp客户端已启动并连接成功
- [ ] print_proxy_server已启动并监听8888端口

### 门店B

- [ ] frp客户端配置：`remotePort = 18889`  （不同的端口）
- [ ] print_proxy_server配置：`LOCAL_PRINTER_PATH=\\printer-bj\Canon PIXMA`
- [ ] 后台配置：打印代理服务地址 = `http://192.168.2.54:18889`  （不同的端口）
- [ ] frp客户端已启动并连接成功
- [ ] print_proxy_server已启动并监听8888端口

## 测试步骤

### 1. 测试门店A的打印

1. 创建一个订单，关联到 `XMSM_001`
2. 在后台点击"开始打印"
3. 检查打印请求是否发送到 `http://192.168.2.54:18888`
4. 检查门店A的打印机是否收到打印任务

### 2. 测试门店B的打印

1. 创建一个订单，关联到 `BJSM_001`
2. 在后台点击"开始打印"
3. 检查打印请求是否发送到 `http://192.168.2.54:18889`
4. 检查门店B的打印机是否收到打印任务

## 常见问题

### Q1: 如果两个门店使用相同的frp远程端口会怎样？

**A:** frp服务端会报错，提示端口已被占用。必须为每个门店分配不同的远程端口。

### Q2: 可以动态分配端口吗？

**A:** 可以，但需要修改frp服务端配置，支持动态端口分配。建议使用固定端口，便于管理和排查问题。

### Q3: 如果门店的打印代理服务端口不是8888怎么办？

**A:** 修改frp客户端的 `localPort` 配置，例如：
```toml
localPort = 9999  # 如果print_proxy_server监听9999端口
```

### Q4: 如何查看当前有哪些端口被占用？

**A:** 
```bash
# Windows
netstat -an | findstr "1888"

# Linux
netstat -tuln | grep 1888
```

## 总结

**关键点：**
1. ✅ 每个门店使用**不同的frp远程端口**（18888, 18889, 18890...）
2. ✅ 每个门店运行**独立的print_proxy_server实例**，配置各自的打印机
3. ✅ 后台根据订单的 `selfie_machine_id` 查找对应的打印代理服务地址
4. ✅ 通过不同的端口地址自然区分不同门店的打印任务

**配置示例：**
- 门店A：`http://192.168.2.54:18888` → 门店A的打印机
- 门店B：`http://192.168.2.54:18889` → 门店B的打印机
- 门店C：`http://192.168.2.54:18890` → 门店C的打印机
