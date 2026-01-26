# frp快速配置指南（Windows版本）

## ⚠️ 重要提示

**您当前下载的是macOS版本（`frp_0.66.0_darwin_amd64`），Windows系统需要下载Windows版本！**

## 第一步：下载正确的Windows版本

1. **访问下载页面**：https://github.com/fatedier/frp/releases
2. **下载Windows版本**：`frp_0.66.0_windows_amd64.zip`
3. **解压到项目目录**或 `C:\frp\`

---

## 第二步：服务端配置（192.168.2.54）

### 1. 创建配置文件 `frps.toml`

在frp目录下创建 `frps.toml` 文件：

```toml
bindPort = 7000
token = "your-secret-token-123456"

# 日志配置（可选）
log.to = "frps.log"
log.level = "info"
log.maxDays = 3
```

### 2. 启动服务端

```cmd
cd C:\frp
frps.exe -c frps.toml
```

**预期输出：**
```
[I] [service.go:200] frps tcp listen on 0.0.0.0:7000
[I] [root.go:210] start frps success
```

---

## 第三步：客户端配置（sm003）

### 1. 创建配置文件 `frpc.toml`

在frp目录下创建 `frpc.toml` 文件：

```toml
serverAddr = "192.168.2.54"
serverPort = 7000
token = "your-secret-token-123456"

[[proxies]]
name = "print_proxy"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8888
remotePort = 18888
```

### 2. 启动客户端

```cmd
cd C:\frp
frpc.exe -c frpc.toml
```

**预期输出：**
```
[I] [service.go:301] login to server success
[I] [proxy_manager.go:144] [print_proxy] start proxy success
```

---

## 第四步：管理后台配置

在管理后台（`http://192.168.2.54:8002/admin/print-config`）配置：

- **打印代理服务地址**：`http://192.168.2.54:18888`
- **API密钥**：（如果设置了）

---

## 关键配置说明

### TOML格式注意事项

1. **字符串必须用引号**：
   ```toml
   token = "your-secret-token-123456"  ✅ 正确
   token = your-secret-token-123456    ❌ 错误
   ```

2. **代理配置使用数组格式**：
   ```toml
   [[proxies]]  # 注意是双中括号
   name = "print_proxy"
   type = "tcp"
   ```

3. **端口和数字不需要引号**：
   ```toml
   bindPort = 7000        ✅ 正确
   bindPort = "7000"     ❌ 错误（虽然也能工作，但不规范）
   ```

---

## 版本差异说明

| 项目 | 旧版本（0.52.x） | 新版本（0.66.x） |
|------|----------------|----------------|
| 配置文件格式 | INI（.ini） | TOML（.toml） |
| 服务端配置 | `frps.ini` | `frps.toml` |
| 客户端配置 | `frpc.ini` | `frpc.toml` |
| 配置语法 | `[common]` 节 | 直接配置项 |
| 代理配置 | `[print_proxy]` | `[[proxies]]` 数组 |

---

## 快速检查清单

- [ ] 已下载Windows版本的frp（不是darwin版本）
- [ ] 服务端 `frps.toml` 已配置（bindPort、token）
- [ ] 客户端 `frpc.toml` 已配置（serverAddr、token、proxies）
- [ ] 服务端正在运行（端口7000监听）
- [ ] 客户端正在运行并已连接
- [ ] 管理后台已配置：`http://192.168.2.54:18888`

---

## 常见错误

### 错误1：找不到配置文件

**错误信息：** `config file not found`

**解决：** 确保配置文件名称正确：`frps.toml` 或 `frpc.toml`（不是.ini）

### 错误2：配置文件格式错误

**错误信息：** `parse config file error`

**解决：** 
- 检查TOML格式是否正确
- 确保字符串用引号括起来
- 确保使用 `[[proxies]]`（双中括号）而不是 `[proxies]`

### 错误3：token不匹配

**错误信息：** `token mismatch`

**解决：** 确保服务端和客户端的token完全相同（包括引号）
