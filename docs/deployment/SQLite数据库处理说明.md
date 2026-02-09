# SQLite数据库处理说明

**更新日期**: 2026-02-04  
**状态**: 已迁移到PostgreSQL

---

## 📋 当前状态

### 数据库使用情况

- ✅ **PostgreSQL**: 正在使用（生产数据库）
- ⚠️ **SQLite (`pet_painting.db`)**: 已不再使用，但文件仍存在

### 配置检查

应用会根据环境变量 `DATABASE_URL` 自动选择数据库：

```python
# app/__init__.py
database_url = os.environ.get('DATABASE_URL', 'sqlite:///pet_painting.db')
```

**如果配置了PostgreSQL**（`.env` 文件中有 `DATABASE_URL=postgresql://...`）：
- ✅ 应用使用PostgreSQL
- ❌ SQLite不会被使用

**如果没有配置PostgreSQL**：
- ⚠️ 应用会回退到SQLite（默认值）

---

## 🔍 如何确认当前使用的数据库

### 方法1: 检查环境变量

```bash
# Windows PowerShell
$env:DATABASE_URL

# Linux/Mac
echo $DATABASE_URL

# 或检查.env文件
cat .env | grep DATABASE_URL
```

### 方法2: 查看应用启动日志

应用启动时会显示使用的数据库类型：
- 如果看到 "数据库表创建完成" 且没有SQLite相关错误 → 使用PostgreSQL
- 如果看到SQLite相关错误 → 仍在使用SQLite

### 方法3: 直接查询数据库

```bash
# 如果使用PostgreSQL
psql -U aistudio_user -d pet_painting -c "SELECT COUNT(*) FROM orders;"

# 如果使用SQLite
sqlite3 instance/pet_painting.db "SELECT COUNT(*) FROM orders;"
```

---

## 📦 SQLite数据库处理建议

### 选项1: 保留作为备份（推荐）⭐

**优点**:
- 数据安全（双重备份）
- 可以随时回退
- 不影响当前运行

**操作**:
1. 将 `pet_painting.db` 移动到备份目录
2. 定期备份PostgreSQL数据库

```bash
# 创建备份目录
mkdir -p data/backups/sqlite

# 移动SQLite数据库到备份目录（带时间戳）
mv instance/pet_painting.db data/backups/sqlite/pet_painting.db.backup_$(date +%Y%m%d)
```

### 选项2: 删除SQLite数据库

**前提条件**:
- ✅ PostgreSQL运行正常
- ✅ 数据已完全迁移到PostgreSQL
- ✅ 已创建PostgreSQL备份
- ✅ 确认应用不再使用SQLite

**操作步骤**:

1. **确认PostgreSQL正常运行**
   ```bash
   # 检查PostgreSQL服务
   # Windows: services.msc 查看PostgreSQL服务
   # Linux: sudo systemctl status postgresql
   
   # 测试连接
   psql -U aistudio_user -d pet_painting -c "SELECT 1;"
   ```

2. **确认数据已迁移**
   ```bash
   # 对比数据量
   # PostgreSQL
   psql -U aistudio_user -d pet_painting -c "SELECT COUNT(*) FROM orders;"
   
   # SQLite（如果文件还在）
   sqlite3 instance/pet_painting.db "SELECT COUNT(*) FROM orders;"
   ```

3. **创建PostgreSQL备份**
   ```bash
   python scripts/database/backup_postgresql.py --backup
   ```

4. **删除SQLite数据库**
   ```bash
   # 先移动到备份目录（以防万一）
   mkdir -p data/backups/sqlite
   mv instance/pet_painting.db data/backups/sqlite/pet_painting.db.deleted_$(date +%Y%m%d)
   
   # 或直接删除（不推荐）
   # rm instance/pet_painting.db
   ```

### 选项3: 保留但重命名（折中方案）

```bash
# 重命名，避免被误用
mv instance/pet_painting.db instance/pet_painting.db.backup
```

---

## ⚠️ 重要注意事项

### 1. 不要立即删除

即使已迁移到PostgreSQL，也建议：
- 保留SQLite数据库至少1-2周
- 确认PostgreSQL稳定运行
- 确认所有功能正常

### 2. 定期备份PostgreSQL

```bash
# 设置定时备份（每天）
python scripts/database/backup_postgresql.py --backup --cleanup
```

### 3. 检查代码中的SQLite引用

虽然应用已使用PostgreSQL，但代码中可能仍有SQLite的默认值：

```python
# app/__init__.py:50
database_url = os.environ.get('DATABASE_URL', 'sqlite:///pet_painting.db')
```

这个默认值不会影响使用，因为：
- 如果配置了 `DATABASE_URL`，会使用PostgreSQL
- 如果没有配置，才会使用SQLite默认值

---

## 🔄 迁移验证清单

在删除SQLite之前，确认以下事项：

- [ ] PostgreSQL服务正常运行
- [ ] 应用可以正常连接PostgreSQL
- [ ] 数据已完全迁移（对比数据量）
- [ ] 所有功能测试通过
- [ ] 已创建PostgreSQL备份
- [ ] 已运行至少1-2周无问题
- [ ] 已通知团队成员

---

## 📚 相关文档

- [PostgreSQL使用说明](./PostgreSQL使用说明.md)
- [PostgreSQL迁移完成总结](./PostgreSQL迁移完成总结.md)
- [PostgreSQL备份快速参考](./PostgreSQL备份快速参考.md)

---

**建议**: 保留SQLite数据库作为备份，至少1-2周后再考虑删除。

**最后更新**: 2026-02-04
