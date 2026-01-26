# AI-Studio v3

## 📋 项目简介

AI 工作室管理系统，支持 AI 图片生成、订单管理、模板管理等功能。

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境

1. 复制配置文件：
   ```bash
   cp config/config.yml.example config/config.yml
   ```

2. 编辑 `config/config.yml`，配置数据库、API 密钥等

3. 初始化数据库：
   ```bash
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

### 启动项目

```bash
# Windows开发环境
python start.py

# 或使用脚本
start_with_proxy.bat

# Linux生产环境
python start_production.py

# 或使用systemd服务
sudo systemctl start aistudio
```

### 生产环境部署

详细的生产环境部署指南请参考：[生产环境部署指南](docs/deployment/生产环境部署指南.md)

快速部署：
```bash
# 1. 运行部署脚本
bash scripts/deployment/deploy_linux.sh

# 2. 配置Nginx和SSL证书
# 3. 创建systemd服务
# 4. 启动服务
```

主要特性：
- ✅ Flask + Gunicorn + Nginx 标准架构
- ✅ 支持图片路径统一配置管理
- ✅ 支持本地存储和OSS存储切换
- ✅ 完整的生产环境优化配置

## 📥 更新代码

```bash
# 拉取最新代码
git pull origin main
```

## 📤 提交代码

```bash
# 添加修改
git add .

# 提交
git commit -m "提交说明"

# 推送
git push origin main
```

## 📁 项目结构

```
AI-studio/
├── app/              # 应用主目录
│   ├── routes/      # 路由
│   ├── services/    # 业务服务
│   └── utils/       # 工具函数
├── templates/       # HTML 模板
├── static/          # 静态资源
├── config/          # 配置文件
├── scripts/         # 脚本文件
└── docs/            # 文档
```

## 📚 相关文档

- [API 服务商集成说明](API服务商集成说明.md)
- [API 模板管理模块说明](API模板管理模块说明.md)
- [代码拆分分析报告](代码拆分分析报告.md)
- [数据库迁移说明](数据库迁移说明.md)

## 🔐 注意事项

- 配置文件 `config/config.yml` 包含敏感信息，不会提交到 Git
- 数据库文件（`.db`）不会提交到 Git
- 请勿提交包含 API 密钥的文件

---

**GitHub 仓库**: https://github.com/chenxiaokaiAAAA/aistudio
