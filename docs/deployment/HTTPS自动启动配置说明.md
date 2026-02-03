# HTTPS服务自动启动配置说明

## 问题描述
每次电脑重启后，IIS服务会自动启动并占用80端口，导致Nginx无法启动，HTTPS服务无法访问。

## 解决方案
已创建多个自动启动脚本，您可以选择其中一种方式：

### 方案1：手动启动脚本（推荐）
- **文件**: `auto_start_nginx.bat`
- **使用方法**: 双击运行即可
- **特点**: 简单易用，有详细的状态提示

### 方案2：PowerShell版本
- **文件**: `auto_start_nginx.ps1`
- **使用方法**: 右键选择"使用PowerShell运行"
- **特点**: 更详细的错误处理和状态显示

### 方案3：开机自动启动
- **文件**: `startup_https.bat` + `add_to_startup.bat`
- **使用方法**: 
  1. 以管理员身份运行 `add_to_startup.bat`
  2. 重启电脑测试
- **特点**: 完全自动化，无需手动操作

### 方案4：Windows服务（高级）
- **文件**: `install_nginx_service.bat` + `nginx_service.bat`
- **使用方法**: 以管理员身份运行 `install_nginx_service.bat`
- **特点**: 作为系统服务运行，更稳定

## 脚本功能
所有脚本都会自动执行以下操作：
1. 停止IIS服务 (W3SVC)
2. 停止Windows HTTP服务
3. 终止占用80端口的进程
4. 启动Nginx服务
5. 验证服务是否正常启动

## 推荐使用方案
**建议使用方案3（开机自动启动）**，这样每次重启后都会自动处理，无需手动操作。

## 故障排除
如果自动启动失败，请：
1. 检查 `logs\error.log` 文件
2. 手动运行 `auto_start_nginx.bat` 查看错误信息
3. 确认SSL证书文件存在：`C:\nginx\ssl\photogooo.pem` 和 `C:\nginx\ssl\photogooo.key`

## 服务管理命令
```bash
# 查看服务状态
sc query NginxHTTPS

# 启动服务
sc start NginxHTTPS

# 停止服务
sc stop NginxHTTPS

# 删除服务
sc delete NginxHTTPS
```
