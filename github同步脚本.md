# GitHub 与阿里云同步脚本

## 根目录快捷入口（推荐）

在项目根目录 `E:\AI-STUDIO\aistudio -V14` 下可直接双击：

| 脚本 | 说明 |
|------|------|
| **完整同步到GitHub并部署.bat** | 提交→推送 GitHub→可选部署到阿里云 |
| **快速同步到阿里云.bat** | Python/PowerShell 增量同步到阿里云 |
| **部署到阿里云服务器.bat** | 上传部署脚本、数据库、图片等 |

以上脚本为快捷入口，实际逻辑在 `scripts/deployment/` 目录下。

---

## 使用方法

### 本地同步到 GitHub
```bash
# 双击根目录：完整同步到GitHub并部署.bat

# 或使用 Git 命令
git add .
git commit -m "更新说明"
git push origin main
```

### 服务器从 GitHub 同步
```bash
# 在阿里云服务器上执行
cd /root/project_code
git pull origin main
systemctl restart aistudio

# 或运行部署脚本
bash scripts/deployment/sync_from_github.sh
```

---

## 完整脚本列表（scripts/deployment/）

| 脚本 | 说明 |
|------|------|
| 完整同步到GitHub并部署.bat | 提交 + 推送 + 可选部署 |
| 快速同步到阿里云.bat | 同步代码/数据库/图片 |
| 部署到阿里云服务器.bat | 上传部署 |
| sync_to_aliyun.py | Python 同步工具 |
| sync_from_github.sh | 服务器端从 GitHub 拉取 |

详细说明请参考：`docs/deployment/代码同步完整指南.md`
