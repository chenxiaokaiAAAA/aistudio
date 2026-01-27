# 查找SSH密钥和Git凭据

## 重要说明

### 之前上传GitHub使用的是HTTPS，不是SSH！

从您的Git配置看：
- 远程仓库地址：`https://github.com/chenxiaokaiAAAA/aistudio.git`（HTTPS方式）
- 凭据存储：`credential.helper=store`（用户名密码存储在本地）

**所以之前上传到GitHub时，您可能输入过GitHub的用户名和密码，这些凭据被保存在本地文件中。**

---

## 查找Git凭据（HTTPS方式）

### Windows上Git凭据存储位置

```powershell
# 方式1：检查Git凭据文件
$env:USERPROFILE\.git-credentials

# 方式2：检查Windows凭据管理器
# 打开：控制面板 -> 凭据管理器 -> Windows凭据
# 查找：git:https://github.com
```

### 查看Git凭据

```powershell
# 在PowerShell中执行
if (Test-Path "$env:USERPROFILE\.git-credentials") {
    Write-Host "找到Git凭据文件："
    Get-Content "$env:USERPROFILE\.git-credentials"
} else {
    Write-Host "未找到.git-credentials文件"
    Write-Host "可能存储在Windows凭据管理器中"
}
```

---

## 查找SSH密钥（用于连接服务器）

### Windows上SSH密钥常见位置

```powershell
# 1. 用户.ssh目录
%USERPROFILE%\.ssh\
# 通常是：C:\Users\您的用户名\.ssh\

# 2. 项目目录
aliyun-key\
# 当前项目目录下

# 3. 下载文件夹
%USERPROFILE%\Downloads\

# 4. 桌面
%USERPROFILE%\Desktop\

# 5. 文档文件夹
%USERPROFILE%\Documents\
```

### 搜索SSH密钥文件

```powershell
# 在PowerShell中搜索所有.pem和.key文件
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.pem" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.key" -ErrorAction SilentlyContinue | Select-Object FullName

# 搜索特定名称的文件
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*aliyun*" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*ssh*" -ErrorAction SilentlyContinue | Select-Object FullName
```

---

## 两种不同的密钥/凭据

### 1. GitHub SSH密钥（用于Git操作）

**用途**：用于 `git clone git@github.com:...` 这种SSH方式的Git操作

**位置**：
- `%USERPROFILE%\.ssh\id_rsa` 或 `id_ed25519`
- 公钥：`%USERPROFILE%\.ssh\id_rsa.pub` 或 `id_ed25519.pub`

**检查方法**：
```powershell
# 检查是否有GitHub SSH密钥
if (Test-Path "$env:USERPROFILE\.ssh\id_rsa") {
    Write-Host "找到SSH私钥: $env:USERPROFILE\.ssh\id_rsa"
}
if (Test-Path "$env:USERPROFILE\.ssh\id_ed25519") {
    Write-Host "找到SSH私钥: $env:USERPROFILE\.ssh\id_ed25519"
}
```

### 2. 阿里云服务器SSH密钥（用于连接服务器）

**用途**：用于 `ssh -i key.pem root@121.43.143.59` 连接服务器

**位置**：可能在以下位置
- `aliyun-key\*.pem` 或 `*.key`
- `%USERPROFILE%\Downloads\*.pem`
- `%USERPROFILE%\Desktop\*.pem`

**检查方法**：
```powershell
# 搜索所有.pem文件
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.pem" -ErrorAction SilentlyContinue
```

---

## 当前情况分析

### 您的情况

1. **GitHub上传**：使用的是HTTPS方式，凭据可能存储在：
   - `%USERPROFILE%\.git-credentials` 文件中
   - 或Windows凭据管理器中

2. **服务器连接**：需要SSH密钥（`.pem`或`.key`文件），但您忘记了位置

### 解决方案

#### 方案1：使用GitHub Token（推荐，最简单）

既然您已经创建了GitHub Token，可以直接使用：

```bash
# 在服务器上克隆代码时使用Token
git clone https://YOUR_GITHUB_TOKEN@github.com/chenxiaokaiAAAA/aistudio.git .
```

#### 方案2：使用密码连接服务器

如果忘记了SSH密钥，可以使用密码：

```bash
ssh root@121.43.143.59
# 输入服务器密码
```

#### 方案3：重新生成SSH密钥

如果需要SSH密钥，可以重新生成：

```bash
# 在本地生成新的SSH密钥对
ssh-keygen -t rsa -b 4096 -f aliyun-key/new-key -C "aliyun-server-2026"

# 这会生成：
# - aliyun-key/new-key (私钥，用于连接)
# - aliyun-key/new-key.pub (公钥，需要添加到服务器)
```

然后将公钥添加到服务器：

```bash
# 在服务器上执行
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# 粘贴 new-key.pub 的内容
chmod 600 ~/.ssh/authorized_keys
```

---

## 快速查找脚本

创建一个PowerShell脚本来查找所有相关文件：

```powershell
# 查找SSH密钥和Git凭据
Write-Host "=== 查找SSH密钥 ===" -ForegroundColor Green
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.pem" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.key" -ErrorAction SilentlyContinue | Select-Object FullName

Write-Host "`n=== 查找Git凭据 ===" -ForegroundColor Green
if (Test-Path "$env:USERPROFILE\.git-credentials") {
    Write-Host "找到: $env:USERPROFILE\.git-credentials" -ForegroundColor Green
} else {
    Write-Host "未找到.git-credentials文件" -ForegroundColor Yellow
}

Write-Host "`n=== 检查.ssh目录 ===" -ForegroundColor Green
if (Test-Path "$env:USERPROFILE\.ssh") {
    Get-ChildItem "$env:USERPROFILE\.ssh" | Select-Object Name
} else {
    Write-Host ".ssh目录不存在" -ForegroundColor Yellow
}
```

---

## 总结

1. **GitHub上传**：使用的是HTTPS，不是SSH，所以不需要SSH密钥
2. **服务器连接**：需要SSH密钥，但可以用密码替代
3. **推荐方案**：使用GitHub Token + 密码连接服务器（最简单）

现在您可以直接使用GitHub Token部署，不需要找SSH密钥了！
