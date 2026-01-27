# GitHub 仓库内容说明

## ✅ 会上传到 GitHub 的内容

### 1. 核心代码文件
- ✅ **Python 源代码**：`app/`、`scripts/`、`test_server.py`、`start_production.py` 等
- ✅ **配置文件**：`gunicorn.conf.py`、`requirements.txt`、`config/`（不含敏感信息）
- ✅ **模板文件**：`templates/` 目录下的所有 HTML 模板
- ✅ **静态资源**：`static/css/`、`static/js/`（CSS 和 JavaScript 文件）
- ✅ **文档文件**：`docs/`、`README.md`、所有 `.md` 文档
- ✅ **脚本文件**：`.bat`、`.sh`、`.ps1` 等脚本文件

### 2. 项目结构
- ✅ 所有目录结构
- ✅ `.gitignore` 文件
- ✅ 版本标签和提交历史

## ❌ 不会上传到 GitHub 的内容

### 1. 数据库文件
- ❌ `*.db` - 所有 SQLite 数据库文件
- ❌ `instance/pet_painting.db` - 主数据库文件
- ❌ `moeart_paintings.db` - 历史遗留数据库
- ❌ `*.sqlite`、`*.sqlite3` - 其他数据库格式
- ❌ `*.db-shm`、`*.db-wal` - SQLite 临时文件

### 2. 图片和媒体文件
- ❌ `uploads/` - 用户上传的图片
- ❌ `final_works/` - AI 生成的效果图
- ❌ `hd_images/` - 高清图片
- ❌ `static/images/**/*.jpg`、`*.png` 等 - 静态图片资源
- ❌ `static/qrcodes/*.jpg`、`*.png` - 二维码图片
- ❌ 根目录的二维码图片（`merchant_*.png`、`website_qrcode.png` 等）

### 3. 敏感配置文件
- ❌ `server_config.py` - 包含服务器地址配置
- ❌ `printer_config.py` - 可能包含 API 密钥
- ❌ `size_config.py` - 配置信息
- ❌ `.env`、`.env.*` - 环境变量文件
- ❌ `*.key`、`*.pem` - 密钥文件
- ❌ `aliyun-key/` - 阿里云密钥目录

### 4. 日志和临时文件
- ❌ `*.log` - 所有日志文件
- ❌ `logs/` - 日志目录
- ❌ `app.log` - 应用日志
- ❌ `*.tmp`、`*.temp` - 临时文件
- ❌ `*.bak` - 备份文件

### 5. 其他
- ❌ `instance/` - 实例目录（包含数据库）
- ❌ `workflows/*.json` - 工作流文件（可能包含敏感信息）
- ❌ `__pycache__/` - Python 缓存
- ❌ `frp_*/` - FRP 内网穿透工具（二进制文件）
- ❌ `*.exe` - 可执行文件

## 📋 总结

**GitHub 上包含：**
- ✅ 所有源代码（Python、HTML、CSS、JavaScript）
- ✅ 所有文档（Markdown、说明文档）
- ✅ 所有脚本（批处理、Shell、PowerShell）
- ✅ 项目结构和配置文件（不含敏感信息）

**GitHub 上不包含：**
- ❌ 数据库文件（`.db`）
- ❌ 图片文件（`.jpg`、`.png` 等）
- ❌ 敏感配置文件（`server_config.py`、`.env` 等）
- ❌ 日志和临时文件

## 🔄 部署时需要单独上传的内容

部署到服务器时，需要单独上传：
1. **数据库文件**：`instance/pet_painting.db`
2. **图片文件**：`uploads/`、`final_works/`、`hd_images/`
3. **配置文件**：`server_config.py`、`.env`（根据实际情况）

## 📝 注意事项

- 数据库和图片文件需要手动上传到服务器
- 敏感配置文件不要提交到 GitHub
- 使用 `.gitignore` 确保这些文件不会被意外提交
