# GitHub上传指南

## 概述

本指南帮助您将AI拍照机系统的核心代码上传到GitHub，同时忽略数据库、图片等敏感文件。

## 已配置的忽略规则

`.gitignore` 文件已配置，会自动忽略以下内容：

### 数据库文件
- `*.db`, `*.sqlite`, `*.sqlite3`
- `instance/*.db`
- `unused_databases/`
- 数据库备份文件

### 图片和媒体文件
- `uploads/` - 用户上传的原图
- `final_works/` - AI生成的效果图
- `hd_images/` - 高清图片
- `static/images/**/*.jpg` 等图片文件
- `static/qrcodes/` 中的二维码图片

### 敏感配置文件
- `.env` - 环境变量文件
- `server_config.py` - 服务器配置
- `printer_config.py` - 打印机配置（可能包含密钥）
- `*.key`, `*.pem` - 证书和密钥文件
- `aliyun-key/` - 阿里云密钥目录

### 日志和临时文件
- `*.log` - 日志文件
- `logs/` - 日志目录
- `backups/` - 备份目录
- `__pycache__/` - Python缓存

## 上传步骤

### 方法1：首次上传（如果还没有Git仓库）

#### 1. 初始化Git仓库

```bash
# 初始化Git仓库
git init

# 添加远程仓库（替换为您的GitHub仓库地址）
git remote add origin https://github.com/your-username/your-repo.git
# 或使用SSH
# git remote add origin git@github.com:your-username/your-repo.git
```

#### 2. 检查忽略规则

```bash
# 检查哪些文件会被忽略
git status --ignored

# 验证特定文件是否被忽略
git check-ignore -v uploads/
git check-ignore -v *.db
```

#### 3. 添加文件

```bash
# 添加所有文件（.gitignore会自动过滤）
git add .

# 查看将要提交的文件
git status
```

#### 4. 提交更改

```bash
# 提交
git commit -m "生产环境优化：添加图片路径配置、Gunicorn配置、Nginx配置和部署文档"
```

#### 5. 推送到GitHub

```bash
# 推送到main分支
git push -u origin main

# 或推送到master分支（如果您的默认分支是master）
# git push -u origin master
```

---

### 方法2：已有Git仓库，更新代码

#### 1. 检查当前状态

```bash
# 查看更改
git status

# 查看具体更改内容
git diff
```

#### 2. 添加更改

```bash
# 添加所有更改
git add .

# 或选择性添加
git add app/
git add templates/
git add config/
git add docs/
git add *.py
git add *.md
git add .gitignore
```

#### 3. 提交更改

```bash
git commit -m "生产环境优化：添加图片路径配置、Gunicorn配置、Nginx配置和部署文档"
```

#### 4. 推送到GitHub

```bash
git push origin main
```

---

### 方法3：使用批处理脚本（Windows）

直接运行：

```bash
上传到GitHub_生产环境优化版.bat
```

脚本会自动：
1. 检查Git状态
2. 添加所有更改
3. 显示将要提交的文件
4. 提交更改
5. 推送到GitHub

---

## 核心代码文件清单

以下文件**会被上传**（核心代码）：

### 应用代码
- `app/` - 应用主目录
  - `app/routes/` - 路由
  - `app/services/` - 服务
  - `app/utils/` - 工具函数
  - `app/models.py` - 数据模型
- `test_server.py` - 主应用文件
- `start.py` - 开发环境启动脚本
- `start_production.py` - 生产环境启动脚本

### 配置文件
- `gunicorn.conf.py` - Gunicorn配置
- `config/nginx_linux.conf` - Nginx配置
- `requirements.txt` - Python依赖
- `.gitignore` - Git忽略规则

### 模板文件
- `templates/` - HTML模板（不含图片）

### 静态资源
- `static/css/` - CSS文件
- `static/js/` - JavaScript文件
- `static/images/.gitkeep` - 保留目录结构（但忽略图片）

### 文档
- `docs/` - 文档目录
- `README.md` - 项目说明

### 脚本
- `scripts/` - 脚本文件（不含敏感配置）

---

## 不会被上传的文件

以下文件**会被忽略**（不会上传）：

### 数据库
- `*.db` - 所有数据库文件
- `instance/*.db` - 实例数据库
- `pet_painting.db`
- `moeart_paintings.db`

### 图片文件
- `uploads/` - 用户上传的图片
- `final_works/` - 效果图
- `hd_images/` - 高清图
- `static/images/**/*.jpg` 等图片文件
- `static/qrcodes/*.jpg` 等二维码

### 敏感配置
- `.env` - 环境变量
- `server_config.py` - 服务器配置
- `printer_config.py` - 打印机配置
- `aliyun-key/` - 阿里云密钥

### 日志和备份
- `*.log` - 日志文件
- `logs/` - 日志目录
- `backups/` - 备份目录

---

## 验证上传内容

### 1. 本地验证

```bash
# 查看将要提交的文件
git status

# 查看具体文件列表
git ls-files

# 验证忽略规则
git check-ignore -v uploads/
git check-ignore -v *.db
```

### 2. 推送到GitHub后验证

1. 访问您的GitHub仓库
2. 检查文件列表，确认：
   - ✅ 核心代码已上传
   - ✅ 数据库文件未上传
   - ✅ 图片文件未上传
   - ✅ 敏感配置文件未上传

---

## 常见问题

### Q1: 如何确认某个文件是否会被忽略？

```bash
git check-ignore -v 文件路径
```

如果输出文件路径，说明该文件会被忽略。

### Q2: 如何强制添加被忽略的文件？

```bash
git add -f 文件路径
```

**注意**：不推荐这样做，特别是对于敏感文件。

### Q3: 如何从Git中移除已跟踪的文件？

如果某个文件已经被Git跟踪，但现在想忽略它：

```bash
# 从Git中移除，但保留本地文件
git rm --cached 文件路径

# 提交更改
git commit -m "移除敏感文件"
```

### Q4: 如何查看.gitignore是否生效？

```bash
# 查看所有被忽略的文件
git status --ignored

# 查看将要提交的文件
git status
```

---

## 安全建议

1. **检查敏感信息**：上传前检查代码中是否包含：
   - API密钥
   - 数据库密码
   - 服务器地址
   - 其他敏感信息

2. **使用环境变量**：将敏感配置放在 `.env` 文件中（已在.gitignore中）

3. **代码审查**：上传前检查 `git diff` 查看所有更改

4. **使用私有仓库**：如果包含商业代码，考虑使用私有仓库

---

## 快速命令参考

```bash
# 初始化仓库
git init
git remote add origin <your-repo-url>

# 添加文件
git add .

# 提交
git commit -m "提交信息"

# 推送
git push -u origin main

# 查看状态
git status

# 查看忽略的文件
git status --ignored
```

---

## 注意事项

1. **首次上传前**：确保 `.gitignore` 已正确配置
2. **检查敏感信息**：确认没有上传API密钥、密码等
3. **数据库文件**：确保所有 `.db` 文件都被忽略
4. **图片文件**：确认图片目录被忽略
5. **环境变量**：确认 `.env` 文件被忽略

---

## 后续更新

每次更新代码后：

```bash
# 1. 查看更改
git status

# 2. 添加更改
git add .

# 3. 提交
git commit -m "更新说明"

# 4. 推送
git push origin main
```

---

## 联系支持

如有问题，请检查：
- `.gitignore` 文件配置
- `git status` 输出
- GitHub仓库文件列表
