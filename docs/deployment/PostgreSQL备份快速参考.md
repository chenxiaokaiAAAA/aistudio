# PostgreSQL数据库备份快速参考

**更新日期**: 2026-02-04  
**数据库**: PostgreSQL (pet_painting)

---

## 🚀 快速备份（推荐）

### Windows用户

**最简单的方法:**
```bash
# 双击运行或命令行执行
batch\maintenance\backup_postgresql.bat
```

**命令行方法:**
```bash
# 完整备份
python scripts\database\backup_postgresql.py --backup

# 备份并清理旧备份
python scripts\database\backup_postgresql.py --backup --cleanup --stats
```

### Linux/Mac用户

```bash
# 完整备份
python3 scripts/database/backup_postgresql.py --backup

# 备份并清理旧备份
python3 scripts/database/backup_postgresql.py --backup --cleanup --stats
```

---

## 📋 备份命令选项

### 基本命令

```bash
# 完整备份（默认）
python scripts/database/backup_postgresql.py --backup

# 只备份表结构
python scripts/database/backup_postgresql.py --backup --type schema

# 只备份数据
python scripts/database/backup_postgresql.py --backup --type data

# 查看备份列表
python scripts/database/backup_postgresql.py --list

# 查看统计信息
python scripts/database/backup_postgresql.py --stats

# 清理旧备份
python scripts/database/backup_postgresql.py --cleanup
```

### 组合使用

```bash
# 备份 + 清理 + 统计（推荐）
python scripts/database/backup_postgresql.py --backup --cleanup --stats
```

---

## 📁 备份文件位置

- **备份目录**: `data/backups/postgresql/`
- **文件命名**: `pet_painting_full_YYYYMMDD_HHMMSS.sql`
- **日志文件**: `data/backups/postgresql/backup_log.json`

---

## 🔄 恢复数据库

### 方法1: 使用psql命令

**Windows PowerShell:**
```powershell
$env:PGPASSWORD="a3183683"
psql -U aistudio_user -h localhost -d pet_painting -f data\backups\postgresql\pet_painting_full_20260204_120000.sql
```

**Linux/Mac:**
```bash
PGPASSWORD=a3183683 psql -U aistudio_user -h localhost -d pet_painting -f data/backups/postgresql/pet_painting_full_20260204_120000.sql
```

### 方法2: 使用pgAdmin

1. 打开pgAdmin
2. 连接到PostgreSQL服务器
3. 右键点击数据库 `pet_painting` → `Restore...`
4. 选择备份文件
5. 点击 `Restore`

---

## ⚙️ 配置选项

### 环境变量配置

可以在 `.env` 文件中设置：

```bash
# 数据库连接（备份脚本会自动读取）
DATABASE_URL=postgresql://aistudio_user:a3183683@localhost:5432/pet_painting

# 备份配置（可选）
PG_BACKUP_DIR=data/backups/postgresql
PG_BACKUP_RETENTION_DAYS=30
```

### 命令行参数

```bash
# 指定备份目录
python scripts/database/backup_postgresql.py --backup --backup-dir custom/backup/path

# 指定保留天数
python scripts/database/backup_postgresql.py --backup --retention-days 60
```

---

## ⏰ 设置定时备份

### Windows任务计划程序

1. 打开"任务计划程序" (`taskschd.msc`)
2. 创建基本任务
3. **名称**: PostgreSQL每日备份
4. **触发器**: 每天 03:00
5. **操作**: 启动程序
   - **程序**: `batch\maintenance\backup_postgresql.bat`
   - **起始于**: 项目根目录（如 `E:\AI-STUDIO\aistudio -V14`）

### Linux Cron

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨3点备份
0 3 * * * cd /path/to/project && python3 scripts/database/backup_postgresql.py --backup --cleanup >> /var/log/postgresql_backup.log 2>&1
```

---

## 📊 备份统计示例

运行 `--stats` 选项会显示：

```
============================================================
📊 备份统计信息
============================================================
备份目录: data/backups/postgresql
备份文件数: 15
总大小: 245.67 MB (257,698,304 字节)
保留天数: 30 天

最新备份:
  1. pet_painting_full_20260204_120000.sql
     时间: 2026-02-04 12:00:00
     大小: 18.45 MB
  2. pet_painting_full_20260203_120000.sql
     时间: 2026-02-03 12:00:00
     大小: 18.42 MB
...
============================================================
```

---

## ⚠️ 重要提示

1. **恢复前备份**: 恢复数据库前，务必先备份当前数据
2. **停止应用**: 恢复时建议停止应用服务
3. **测试恢复**: 定期测试备份文件是否可以正常恢复
4. **异地备份**: 定期将备份文件复制到其他位置（云存储、外部硬盘等）
5. **检查备份**: 定期检查备份文件是否完整

---

## 🆘 常见问题

### Q: 备份失败，提示"未找到 pg_dump"

**A:** PostgreSQL未安装或未添加到PATH环境变量
- Windows: 通常位于 `C:\Program Files\PostgreSQL\XX\bin\`
- 将PostgreSQL的bin目录添加到系统PATH
- 或使用完整路径: `"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"`

### Q: 备份失败，提示"密码认证失败"

**A:** 检查数据库连接信息
- 确认 `.env` 文件中的 `DATABASE_URL` 配置正确
- 或手动设置环境变量 `PGPASSWORD`

### Q: 如何查看备份文件内容？

**A:** 备份文件是SQL文本格式，可以用文本编辑器打开查看

### Q: 备份文件太大怎么办？

**A:** 
- 使用 `--type schema` 只备份表结构（较小）
- 使用 `--type data` 只备份数据
- 考虑使用压缩格式（需要修改脚本）

---

## 📚 相关文档

- [PostgreSQL使用说明](./PostgreSQL使用说明.md) - 完整使用指南
- [PostgreSQL迁移指南](./PostgreSQL迁移指南.md) - 迁移步骤
- [PostgreSQL迁移完成总结](./PostgreSQL迁移完成总结.md) - 迁移总结

---

**最后更新**: 2026-02-04  
**状态**: ✅ 备份脚本已创建并可用
