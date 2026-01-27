# 服务器克隆GitHub问题解决

## 问题分析

从您的截图看到：
1. **HTTPS方式**：连接超时（`Connection timed out`）
2. **SSH方式**：权限被拒绝（`Permission denied (publickey)`）
3. **Token方式**：可能还在执行或网络问题

## 解决方案

### 方案1：检查网络连接

```bash
# 测试GitHub连接
ping github.com

# 测试HTTPS端口
curl -I https://github.com

# 如果无法连接，可能需要配置代理或检查防火墙
```

### 方案2：使用Token克隆（正确格式）

```bash
# 方式1：直接在URL中使用Token（请替换 YOUR_GITHUB_TOKEN）
git clone https://YOUR_GITHUB_TOKEN@github.com/chenxiaokaiAAAA/aistudio.git .

# 方式2：使用环境变量（更安全）
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
git clone https://${GITHUB_TOKEN}@github.com/chenxiaokaiAAAA/aistudio.git .
```

### 方案3：配置Git代理（如果网络受限）

```bash
# 如果服务器在中国大陆，可能需要配置代理
# 设置HTTP代理（如果有）
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080

# 或使用GitHub镜像（如果可用）
```

### 方案4：使用本地压缩包上传（推荐，如果网络不稳定）

如果GitHub连接不稳定，可以从本地打包上传：

**在本地执行：**
```powershell
# 1. 打包项目代码（排除不需要的文件）
Compress-Archive -Path app, templates, static, config, docs, scripts, *.py, requirements.txt, gunicorn.conf.py, start_production.py, .gitignore -DestinationPath aistudio_code.zip -Force

# 2. 上传到服务器
scp aistudio_code.zip root@121.43.143.59:/root/project_code/
```

**在服务器上执行：**
```bash
cd /root/project_code
unzip aistudio_code.zip
```

---

## 完整操作步骤（推荐）

### 步骤1：在服务器上测试网络

```bash
# 测试GitHub连接
ping -c 3 github.com

# 如果ping不通，可能需要配置DNS或使用代理
```

### 步骤2：尝试使用Token克隆（完整命令）

```bash
cd /root/project_code

# 如果目录不为空，先清空
rm -rf * .git 2>/dev/null

# 使用Token克隆
git clone https://YOUR_GITHUB_TOKEN@github.com/chenxiaokaiAAAA/aistudio.git .

# 如果还是超时，等待更长时间或使用代理
```

### 步骤3：如果网络问题持续，使用本地打包上传

**在本地Windows执行：**

```powershell
# 创建打包脚本
$filesToInclude = @(
    "app",
    "templates", 
    "static",
    "config",
    "docs",
    "scripts",
    "*.py",
    "requirements.txt",
    "gunicorn.conf.py",
    "start_production.py",
    ".gitignore",
    "README.md"
)

# 创建临时目录
$tempDir = "temp_package"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# 复制文件
foreach ($item in $filesToInclude) {
    if (Test-Path $item) {
        Copy-Item -Path $item -Destination $tempDir -Recurse -Force
    }
}

# 打包
Compress-Archive -Path "$tempDir\*" -DestinationPath "aistudio_code.zip" -Force

# 清理
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "打包完成: aistudio_code.zip"
Write-Host "现在上传到服务器:"
Write-Host "  scp aistudio_code.zip root@121.43.143.59:/root/project_code/"
```

**上传并解压：**

```bash
# 在服务器上
cd /root/project_code
unzip -o aistudio_code.zip
```

---

## 快速解决方案

如果Token克隆没有反应，可能是：
1. **网络超时**：等待更长时间，或使用代理
2. **命令格式问题**：确保Token完整且正确
3. **权限问题**：确保有写入权限

**立即尝试：**

```bash
# 在服务器上执行
cd /root/project_code
rm -rf * .git 2>/dev/null  # 清空目录

# 使用完整URL克隆
git clone https://YOUR_GITHUB_TOKEN@github.com/chenxiaokaiAAAA/aistudio.git .

# 如果还是没反应，按Ctrl+C取消，然后使用本地打包方式
```
