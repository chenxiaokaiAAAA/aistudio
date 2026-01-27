# frp内网穿透配置说明

## 场景说明

- **frp服务端（模拟阿里云）**：`192.168.2.54`（Windows系统）
- **frp客户端（门店）**：`sm003`（Windows系统）
- **打印代理服务**：运行在 `sm003:8888`

## 目标

将 `sm003:8888` 的打印代理服务通过 frp 暴露到 `192.168.2.54`，使得 `192.168.2.54` 可以通过公网端口访问门店的打印服务。

---

## 第一部分：服务端配置（192.168.2.54）

### 1. 下载frp服务端

**⚠️ 重要：您当前下载的是macOS版本，Windows系统需要下载Windows版本！**

1. **访问frp下载页面**
   - 地址：https://github.com/fatedier/frp/releases
   - **下载Windows版本**：`frp_0.66.0_windows_amd64.zip`（或最新版本）
   - ⚠️ 不要下载 `darwin_amd64`（macOS版本）或 `linux_amd64`（Linux版本）

2. **解压文件**
   - 解压到任意目录，例如：`C:\frp\` 或当前项目目录
   - 解压后会看到以下文件：
     ```
     frps.exe          # 服务端程序
     frps.toml         # 配置文件（新版本使用TOML格式）
     frpc.exe          # 客户端程序（不需要）
     frpc.toml         # 客户端配置示例
     ```

### 2. 配置frp服务端

**注意：frp 0.66.0版本使用TOML格式配置文件，不是INI格式！**

1. **编辑配置文件 `frps.toml`**
   
   在frp目录下，编辑或创建 `frps.toml` 文件，内容如下：

   ```toml
   bindPort = 7000
   token = "your-secret-token-123456"
   
   # 可选：设置日志
   log.to = "frps.log"
   log.level = "info"
   log.maxDays = 3
   ```

   **说明：**
   - `bindPort = 7000`：frp服务端监听端口（客户端连接此端口）
   - `token = "your-secret-token-123456"`：安全令牌（请修改为您的密钥，必须用引号）
   - 其他为日志配置（可选）

2. **保存配置文件**

### 3. 启动frp服务端

**方法一：命令行启动（测试用）**

1. 打开命令提示符（CMD）或PowerShell
2. 进入frp目录：
   ```cmd
   cd C:\frp
   ```
3. 启动服务端：
   ```cmd
   frps.exe -c frps.ini
   ```

4. **预期输出：**
   ```
   [I] [service.go:200] frps tcp listen on 0.0.0.0:7000
   [I] [root.go:210] start frps success
   ```

5. **保持窗口打开**（不要关闭）

**方法二：作为Windows服务运行（推荐，开机自启）**

1. **下载NSSM**（Non-Sucking Service Manager）
   - 下载地址：https://nssm.cc/download
   - 解压到 `C:\nssm\`

2. **安装服务**
   
   以管理员身份打开命令提示符，执行：

   ```cmd
   cd C:\nssm\win64
   nssm install FrpServer "C:\frp\frps.exe" "-c" "C:\frp\frps.toml"
   ```
   
   **注意：** 新版本使用 `frps.toml`，不是 `frps.ini`

3. **设置服务属性**
   ```cmd
   # 设置服务描述
   nssm set FrpServer Description "frp内网穿透服务端"
   
   # 设置启动目录
   nssm set FrpServer AppDirectory "C:\frp"
   ```

4. **启动服务**
   ```cmd
   nssm start FrpServer
   ```

5. **查看服务状态**
   ```cmd
   nssm status FrpServer
   ```

### 4. 开放防火墙端口

1. **打开Windows防火墙设置**
   - 控制面板 → Windows Defender 防火墙 → 高级设置

2. **添加入站规则**
   - 点击"入站规则" → "新建规则"
   - 选择"端口" → 下一步
   - 选择"TCP"，输入端口：`7000` → 下一步
   - 选择"允许连接" → 下一步
   - 勾选所有配置文件 → 下一步
   - 名称：`frp服务端端口7000` → 完成

3. **同样添加端口 `18888`**（用于打印代理服务）

### 5. 验证服务端运行

在 `192.168.2.54` 上执行：

```cmd
netstat -an | findstr 7000
```

应该看到：
```
TCP    0.0.0.0:7000           0.0.0.0:0              LISTENING
```

---

## 第二部分：客户端配置（sm003门店电脑）

### 1. 下载frp客户端

1. **访问frp下载页面**
   - 地址：https://github.com/fatedier/frp/releases
   - 下载最新版本的Windows版本
   - 文件名类似：`frp_0.52.3_windows_amd64.zip`

2. **解压文件**
   - 解压到任意目录，例如：`C:\frp\`
   - 解压后会看到以下文件：
     ```
     frpc.exe          # 客户端程序（需要）
     frpc_full.ini     # 完整配置示例
     frpc.ini          # 配置文件（需要编辑）
     frps.exe          # 服务端程序（不需要）
     ```

### 2. 配置frp客户端

1. **编辑配置文件 `frpc.toml`**
   
   **注意：frp 0.66.0版本使用TOML格式配置文件！**
   
   在 `C:\frp\` 目录下，编辑或创建 `frpc.toml` 文件，内容如下：

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

   **说明：**
   - `serverAddr = "192.168.2.54"`：frp服务端地址（必须用引号）
   - `serverPort = 7000`：frp服务端端口
   - `token = "your-secret-token-123456"`：必须与服务端一致（必须用引号）
   - `localIP = "127.0.0.1"`：本地打印代理服务地址
   - `localPort = 8888`：本地打印代理服务端口
   - `remotePort = 18888`：在服务端上暴露的端口（阿里云通过此端口访问）

2. **保存配置文件**

### 3. 启动frp客户端

**方法一：命令行启动（测试用）**

1. 打开命令提示符（CMD）或PowerShell
2. 进入frp目录：
   ```cmd
   cd C:\frp
   ```
3. 启动客户端：
   ```cmd
   frpc.exe -c frpc.toml
   ```
   
   **注意：** 新版本使用 `frpc.toml`，不是 `frpc.ini`

4. **预期输出：**
   ```
   [I] [service.go:301] login to server success, get run id [xxxxx]
   [I] [proxy_manager.go:144] [print_proxy] start proxy success
   ```

5. **保持窗口打开**（不要关闭）

**方法二：作为Windows服务运行（推荐，开机自启）**

1. **下载NSSM**（如果还没有）
   - 下载地址：https://nssm.cc/download
   - 解压到 `C:\nssm\`

2. **安装服务**
   
   以管理员身份打开命令提示符，执行：

   ```cmd
   cd C:\nssm\win64
   nssm install FrpClient "C:\frp\frpc.exe" "-c" "C:\frp\frpc.toml"
   ```
   
   **注意：** 新版本使用 `frpc.toml`，不是 `frpc.ini`

3. **设置服务属性**
   ```cmd
   # 设置服务描述
   nssm set FrpClient Description "frp内网穿透客户端（打印代理）"
   
   # 设置启动目录
   nssm set FrpClient AppDirectory "C:\frp"
   ```

4. **启动服务**
   ```cmd
   nssm start FrpClient
   ```

5. **查看服务状态**
   ```cmd
   nssm status FrpClient
   ```

### 4. 验证客户端连接

在 `sm003` 上查看客户端日志，应该看到：
```
[I] [service.go:301] login to server success
[I] [proxy_manager.go:144] [print_proxy] start proxy success
```

在 `192.168.2.54` 上查看服务端日志，应该看到：
```
[I] [control.go:446] [print_proxy] new proxy [print_proxy] success
```

---

## 第三部分：在管理后台配置

### 1. 访问管理后台

在 `192.168.2.54` 上访问：
```
http://192.168.2.54:8002/admin/print-config
```

### 2. 配置打印代理服务地址

在"本地打印机配置"部分：

- **打印代理服务地址（远程部署）**：`http://192.168.2.54:18888`
  - 格式：`http://服务端IP:remote_port`
  - 注意：使用 `18888` 端口（不是 `8888`）

- **打印代理服务API密钥（可选）**：如果设置了，填写对应的密钥

### 3. 测试连接

1. 点击"测试打印"按钮
2. 上传一个测试文件（如txt文件）
3. 如果成功，会打印测试文件

---

## 配置检查清单

### 服务端（192.168.2.54）检查

- [ ] frp服务端已下载并解压
- [ ] `frps.ini` 配置文件已正确设置
- [ ] frp服务端正在运行（端口7000监听）
- [ ] 防火墙已开放端口 7000 和 18888
- [ ] 服务端日志显示客户端已连接

### 客户端（sm003）检查

- [ ] frp客户端已下载并解压
- [ ] `frpc.ini` 配置文件已正确设置（server_addr、token等）
- [ ] 打印代理服务正在运行（端口8888）
- [ ] frp客户端正在运行并已连接服务端
- [ ] 客户端日志显示连接成功

### 管理后台检查

- [ ] 打印代理服务地址已配置：`http://192.168.2.54:18888`
- [ ] API密钥已配置（如果设置了）
- [ ] 测试打印功能正常

---

## 常见问题

### Q1: 客户端连接失败，提示"connection refused"

**原因：** 服务端未启动或端口未开放

**解决：**
1. 检查服务端是否运行：`netstat -an | findstr 7000`
2. 检查防火墙是否开放端口7000
3. 检查服务端日志是否有错误

### Q2: 客户端连接失败，提示"token mismatch"

**原因：** 客户端和服务端的token不一致

**解决：**
1. 检查 `frps.toml` 和 `frpc.toml` 中的token是否一致
2. 确保两个配置文件中的token完全相同（注意TOML格式需要用引号）

### Q3: 测试打印失败，提示"无法连接到打印代理服务"

**原因：** 管理后台配置的地址不正确

**解决：**
1. 确认使用的是 `http://192.168.2.54:18888`（不是8888）
2. 确认frp客户端正在运行
3. 在服务端测试：`curl http://192.168.2.54:18888/health`

### Q4: 如何查看frp日志？

**服务端日志：**
- 如果使用命令行启动：直接在控制台查看
- 如果使用NSSM服务：查看 `C:\frp\frps.log`

**客户端日志：**
- 如果使用命令行启动：直接在控制台查看
- 如果使用NSSM服务：在NSSM中查看输出日志

### Q5: 如何设置开机自启动？

**服务端：**
```cmd
nssm start FrpServer
nssm set FrpServer Start SERVICE_AUTO_START
```

**客户端：**
```cmd
nssm start FrpClient
nssm set FrpClient Start SERVICE_AUTO_START
```

---

## 文件清单

### 服务端（192.168.2.54）需要的文件

```
C:\frp\
├── frps.exe          # frp服务端程序
├── frps.toml         # 服务端配置文件（新版本使用TOML格式）
└── frps.log          # 服务端日志（运行后生成）
```

### 客户端（sm003）需要的文件

```
C:\frp\
├── frpc.exe          # frp客户端程序
├── frpc.toml         # 客户端配置文件（新版本使用TOML格式）
└── (日志在控制台或NSSM中查看)
```

---

## 下一步

配置完成后：

1. ✅ 确保服务端和客户端都在运行
2. ✅ 在管理后台配置打印代理服务地址
3. ✅ 测试打印功能
4. ✅ 设置开机自启动（可选，但推荐）

## 注意事项

- **token安全**：请将 `your-secret-token-123456` 替换为您自己的安全密钥
- **端口冲突**：确保端口 7000 和 18888 没有被其他程序占用
- **防火墙**：确保防火墙允许这些端口的通信
- **服务持续运行**：建议使用NSSM将frp设置为Windows服务，确保开机自启
