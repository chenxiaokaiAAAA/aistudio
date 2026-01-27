# 使用GitHub Token部署（无需SSH密钥）

## 您的GitHub Token

**注意**：请将下面的 `YOUR_GITHUB_TOKEN` 替换为您的实际 Token

```
YOUR_GITHUB_TOKEN
```

## 部署步骤

### 第一步：连接服务器（使用密码）

如果忘记了SSH密钥，可以使用密码连接：

```bash
# 使用密码连接
ssh root@121.43.143.59
# 输入服务器密码
```

### 第二步：在服务器上克隆代码（使用Token）

```bash
# 进入项目目录
cd /root/project_code

# 使用Token克隆仓库（替换YOUR_TOKEN为您的token）
git clone https://YOUR_TOKEN@github.com/chenxiaokaiAAAA/aistudio.git .

# 或使用环境变量（更安全）
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
git clone https://${GITHUB_TOKEN}@github.com/chenxiaokaiAAAA/aistudio.git .
```

### 第三步：配置Git使用Token

```bash
# 配置Git凭据（避免每次输入token）
git config --global credential.helper store
echo "https://YOUR_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

### 第四步：执行部署脚本

```bash
# 上传部署脚本（从本地）
# 或直接在服务器上创建
nano /root/deploy_aliyun.sh
# 粘贴部署脚本内容

chmod +x /root/deploy_aliyun.sh
/root/deploy_aliyun.sh
```

---

## 方案2：查找SSH密钥

### Windows上常见位置

```powershell
# 1. 用户目录下的.ssh文件夹
%USERPROFILE%\.ssh\

# 2. 项目目录
aliyun-key\

# 3. 下载文件夹
%USERPROFILE%\Downloads\

# 4. 桌面
%USERPROFILE%\Desktop\
```

### 搜索命令

```powershell
# 在PowerShell中搜索
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.pem" -ErrorAction SilentlyContinue
Get-ChildItem -Path C:\Users\$env:USERNAME -Recurse -Filter "*.key" -ErrorAction SilentlyContinue
```

---

## 方案3：重新生成SSH密钥（如果需要）

如果确实需要SSH密钥连接服务器：

```bash
# 在本地生成新的SSH密钥对
ssh-keygen -t rsa -b 4096 -f aliyun-key/new-key -C "aliyun-server"

# 这会生成两个文件：
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

## 推荐方案：使用GitHub Token + 密码连接

最简单的方式：

1. **连接服务器**：使用密码 `ssh root@121.43.143.59`
2. **克隆代码**：使用GitHub Token
3. **上传文件**：使用密码连接 + SCP，或使用WinSCP图形工具
