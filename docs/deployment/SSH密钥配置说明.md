# SSH 密钥配置说明

## 问题说明

如果同步时出现 `Permission denied (publickey)` 错误，说明 SSH 密钥配置有问题。

## 解决方案

### 方案1：使用 SSH 密钥（推荐）

1. **获取密钥文件**
   - 从阿里云控制台下载密钥文件（.pem 格式）
   - 或使用已有的密钥文件

2. **放置密钥文件**
   - 将密钥文件放到项目根目录的 `aliyun-key` 文件夹中
   - 文件名可以是 `*.pem` 或 `*.key`
   - 例如：`aliyun-key/my-server-key.pem`

3. **设置密钥权限（Windows）**
   - 右键点击密钥文件 → 属性 → 安全
   - 确保当前用户有读取权限

4. **测试连接**
   ```bash
   ssh -i aliyun-key/your-key.pem root@121.43.143.59
   ```

### 方案2：使用密码认证

如果不想使用密钥，脚本会自动尝试密码认证：

1. **确保密钥文件不存在或不在 `aliyun-key` 目录中**
2. **运行同步脚本时，会提示输入密码**
3. **输入服务器 root 用户的密码**

### 方案3：配置 SSH 配置文件

在 `~/.ssh/config` 文件中添加：

```
Host aliyun
    HostName 121.43.143.59
    User root
    IdentityFile ~/.ssh/aliyun-key.pem
```

然后修改脚本中的服务器地址为 `aliyun`。

## 脚本自动检测

脚本会自动：
1. 检查默认密钥路径 `aliyun-key\your-key.pem`
2. 如果不存在，搜索 `aliyun-key` 目录中的所有 `.pem` 和 `.key` 文件
3. 如果找到，自动使用第一个找到的密钥文件
4. 如果找不到，使用密码认证

## 常见问题

### Q: 密钥文件在哪里？
A: 从阿里云控制台下载，或联系服务器管理员获取。

### Q: 如何生成新的密钥对？
A: 在服务器上运行：
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/aliyun-key
```

### Q: 密码认证总是失败？
A: 检查：
1. 服务器是否允许密码认证（`/etc/ssh/sshd_config` 中 `PasswordAuthentication yes`）
2. 密码是否正确
3. 用户是否有 SSH 登录权限

## 验证配置

运行以下命令测试连接：

```bash
# 使用密钥
ssh -i aliyun-key/your-key.pem root@121.43.143.59 "echo 'Connection successful'"

# 使用密码（会提示输入密码）
ssh root@121.43.143.59 "echo 'Connection successful'"
```

如果都能成功，说明配置正确。
