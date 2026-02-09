# PostgreSQL 使用说明

**更新日期**: 2026-02-04  
**数据库**: PostgreSQL (pet_painting)

---

## ✅ 确认：应用已切换到PostgreSQL

### 如何确认应用使用PostgreSQL？

1. **检查环境变量配置**
   - 应用启动时会自动从 `.env` 文件或环境变量读取 `DATABASE_URL`
   - 如果配置了PostgreSQL连接，应用就会使用PostgreSQL

2. **查看启动日志**
   - 应用启动时，如果看到 "数据库表创建完成" 且没有SQLite相关错误，说明已使用PostgreSQL

3. **验证方法**
   ```bash
   # 检查.env文件
   cat .env
   # 应该看到: DATABASE_URL=postgresql://aistudio_user:password@localhost:5432/pet_painting
   ```

---

## 🔧 配置PostgreSQL连接

### 方法1: 使用.env文件（推荐）

在项目根目录创建或编辑 `.env` 文件：

```bash
# PostgreSQL数据库配置
DATABASE_URL=postgresql://aistudio_user:a3183683@localhost:5432/pet_painting
```

**优点**: 
- 配置永久有效
- 不需要每次启动都设置环境变量
- 不会被意外覆盖

### 方法2: 设置环境变量

**Windows PowerShell:**
```powershell
$env:DATABASE_URL="postgresql://aistudio_user:a3183683@localhost:5432/pet_painting"
python start.py
```

**Windows CMD:**
```cmd
set DATABASE_URL=postgresql://aistudio_user:a3183683@localhost:5432/pet_painting
python start.py
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://aistudio_user:a3183683@localhost:5432/pet_painting"
python start.py
```

---

## 📊 查看新创建的订单

### 方法1: 通过Web管理界面查看

1. **管理员后台**
   - 访问: `http://localhost:5000/admin/orders`
   - 登录管理员账号
   - 查看所有订单列表

2. **加盟商后台**
   - 访问: `http://localhost:5000/franchisee/orders`
   - 登录加盟商账号
   - 查看该加盟商的订单

### 方法2: 通过pgAdmin查看（图形界面）

1. **打开pgAdmin**
   - 启动pgAdmin应用程序
   - 连接到PostgreSQL服务器

2. **查看订单表**
   - 展开: `Servers` → `PostgreSQL` → `Databases` → `pet_painting` → `Schemas` → `public` → `Tables`
   - 找到 `orders` 表
   - 右键 → `View/Edit Data` → `All Rows`

3. **查看最新订单**
   ```sql
   SELECT * FROM orders 
   ORDER BY created_at DESC 
   LIMIT 20;
   ```

### 方法3: 通过命令行查看（psql）

1. **连接到PostgreSQL**
   ```bash
   psql -U aistudio_user -d pet_painting
   ```

2. **查看订单**
   ```sql
   -- 查看所有订单
   SELECT * FROM orders ORDER BY created_at DESC LIMIT 20;
   
   -- 查看今天的订单
   SELECT * FROM orders 
   WHERE DATE(created_at) = CURRENT_DATE 
   ORDER BY created_at DESC;
   
   -- 查看订单统计
   SELECT 
       status, 
       COUNT(*) as count,
       SUM(price) as total_amount
   FROM orders 
   GROUP BY status;
   ```

3. **查看订单详情**
   ```sql
   -- 查看特定订单
   SELECT * FROM orders WHERE order_number = '订单号';
   
   -- 查看订单及其图片
   SELECT 
       o.id,
       o.order_number,
       o.customer_name,
       o.status,
       o.price,
       o.created_at,
       oi.path as image_path
   FROM orders o
   LEFT JOIN order_image oi ON o.id = oi.order_id
   WHERE o.order_number = '订单号';
   ```

### 方法4: 通过Python脚本查看

创建脚本 `view_orders.py`:

```python
# -*- coding: utf-8 -*-
"""查看订单数据"""
import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Order, OrderImage

app = create_app()

with app.app_context():
    # 查看最新10个订单
    orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    print("=" * 60)
    print("最新订单列表")
    print("=" * 60)
    
    for order in orders:
        print(f"\n订单号: {order.order_number}")
        print(f"客户: {order.customer_name} ({order.customer_phone})")
        print(f"产品: {order.product_name}")
        print(f"状态: {order.status}")
        print(f"金额: ¥{order.price}")
        print(f"创建时间: {order.created_at}")
        print(f"数据库ID: {order.id}")
        
        # 查看订单图片
        images = OrderImage.query.filter_by(order_id=order.id).all()
        if images:
            print(f"图片数量: {len(images)}")
            for img in images:
                print(f"  - {img.path}")

    print("\n" + "=" * 60)
    print(f"总订单数: {Order.query.count()}")
    print("=" * 60)
```

运行:
```bash
python view_orders.py
```

---

## 🔍 数据库位置和连接信息

### PostgreSQL数据库信息

- **数据库名称**: `pet_painting`
- **用户名**: `aistudio_user`
- **密码**: `a3183683`
- **主机**: `localhost`
- **端口**: `5432`
- **连接字符串**: `postgresql://aistudio_user:a3183683@localhost:5432/pet_painting`

### 数据库文件位置

PostgreSQL的数据文件通常位于：
- **Windows**: `C:\Program Files\PostgreSQL\XX\data\`
- **Linux**: `/var/lib/postgresql/XX/main/`

**注意**: PostgreSQL是服务型数据库，数据存储在服务器上，不是单个文件。

---

## 📋 常用数据库操作

### 1. 查看所有表

```sql
-- 在psql中
\dt

-- 或使用SQL
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

### 2. 查看表结构

```sql
-- 查看orders表结构
\d orders

-- 或使用SQL
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'orders';
```

### 3. 查看表数据量

```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### 4. 备份数据库

#### 方法1: 使用备份脚本（推荐）⭐

**Windows:**
```bash
# 运行批处理文件（最简单）
batch\maintenance\backup_postgresql.bat
```

**命令行:**
```bash
# 完整备份（默认）
python scripts\database\backup_postgresql.py --backup

# 只备份表结构
python scripts\database\backup_postgresql.py --backup --type schema

# 只备份数据
python scripts\database\backup_postgresql.py --backup --type data

# 备份并清理旧备份
python scripts\database\backup_postgresql.py --backup --cleanup

# 查看备份列表
python scripts\database\backup_postgresql.py --list

# 查看统计信息
python scripts\database\backup_postgresql.py --stats
```

**Linux/Mac:**
```bash
# 完整备份
python3 scripts/database/backup_postgresql.py --backup

# 备份并清理旧备份
python3 scripts/database/backup_postgresql.py --backup --cleanup --stats
```

**备份脚本功能:**
- ✅ 自动从 `.env` 文件读取数据库连接信息
- ✅ 自动生成带时间戳的备份文件
- ✅ 自动清理超过30天的旧备份（可配置）
- ✅ 记录备份日志
- ✅ 显示备份统计信息

**备份文件位置:**
- 默认路径: `data/backups/postgresql/`
- 文件命名: `pet_painting_full_YYYYMMDD_HHMMSS.sql`

#### 方法2: 使用pg_dump命令（手动）

**Windows PowerShell:**
```powershell
# 备份整个数据库
$env:PGPASSWORD="a3183683"
pg_dump -U aistudio_user -h localhost -d pet_painting -f "backup_$(Get-Date -Format 'yyyyMMdd').sql"

# 只备份表结构
pg_dump -U aistudio_user -h localhost -d pet_painting --schema-only -f schema_backup.sql

# 只备份数据
pg_dump -U aistudio_user -h localhost -d pet_painting --data-only -f data_backup.sql
```

**Linux/Mac:**
```bash
# 备份整个数据库
PGPASSWORD=a3183683 pg_dump -U aistudio_user -h localhost -d pet_painting -f backup_$(date +%Y%m%d).sql

# 只备份表结构
PGPASSWORD=a3183683 pg_dump -U aistudio_user -h localhost -d pet_painting --schema-only -f schema_backup.sql

# 只备份数据
PGPASSWORD=a3183683 pg_dump -U aistudio_user -h localhost -d pet_painting --data-only -f data_backup.sql
```

**Windows CMD:**
```cmd
set PGPASSWORD=a3183683
pg_dump -U aistudio_user -h localhost -d pet_painting -f backup_%date:~0,4%%date:~5,2%%date:~8,2%.sql
```

### 5. 恢复数据库

#### 方法1: 使用psql命令

**Windows PowerShell:**
```powershell
$env:PGPASSWORD="a3183683"
psql -U aistudio_user -h localhost -d pet_painting -f backup_20260204.sql
```

**Linux/Mac:**
```bash
PGPASSWORD=a3183683 psql -U aistudio_user -h localhost -d pet_painting -f backup_20260204.sql
```

**⚠️ 恢复前注意事项:**
1. **备份当前数据**: 恢复会覆盖现有数据，请先备份
2. **确认备份文件**: 检查备份文件是否完整
3. **停止应用**: 恢复时建议停止应用服务
4. **测试恢复**: 建议先在测试环境验证

#### 方法2: 使用pgAdmin（图形界面）

1. 打开pgAdmin
2. 连接到PostgreSQL服务器
3. 右键点击数据库 `pet_painting`
4. 选择 `Restore...`
5. 选择备份文件（.sql或.backup格式）
6. 点击 `Restore` 执行恢复

---

## ⚠️ 重要注意事项

### 1. 确认使用PostgreSQL

启动应用前，确保：
- ✅ `.env` 文件存在且配置了 `DATABASE_URL`
- ✅ PostgreSQL服务正在运行
- ✅ 数据库连接信息正确

### 2. 数据存储位置

- **新创建的订单**: 存储在PostgreSQL数据库的 `orders` 表中
- **不再使用SQLite**: 如果配置了PostgreSQL，应用不会使用SQLite

### 3. 数据备份

**备份策略建议:**
- ✅ **每日自动备份**: 建议设置定时任务每天自动备份
- ✅ **定期手动备份**: 重要操作前手动备份
- ✅ **保留多个版本**: 保留最近30天的备份（可配置）
- ✅ **异地备份**: 定期将备份文件复制到其他位置（如云存储）
- ✅ **测试恢复**: 定期测试备份文件是否可以正常恢复

**备份内容:**
- 数据库数据（使用备份脚本）
- 上传的图片文件（`uploads/`, `final_works/`, `hd_images/`）
- 配置文件（`.env`, `config/config.yml`）

**备份脚本位置:**
- Python脚本: `scripts/database/backup_postgresql.py`
- Windows批处理: `batch/maintenance/backup_postgresql.bat`
- 备份目录: `data/backups/postgresql/`

**设置定时备份（Windows任务计划程序）:**
1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 每天凌晨3:00
4. 操作: 启动程序 `batch\maintenance\backup_postgresql.bat`
5. 起始于: 项目根目录路径

**设置定时备份（Linux cron）:**
```bash
# 编辑crontab
crontab -e

# 添加每天凌晨3点备份任务
0 3 * * * cd /path/to/project && python3 scripts/database/backup_postgresql.py --backup --cleanup >> /var/log/postgresql_backup.log 2>&1
```

### 4. 性能优化

PostgreSQL相比SQLite的优势：
- ✅ 支持并发访问
- ✅ 性能更好
- ✅ 支持更复杂查询
- ✅ 适合生产环境

---

## 🆘 故障排查

### 问题1: 应用无法连接PostgreSQL

**检查项**:
1. PostgreSQL服务是否运行
   ```bash
   # Windows
   services.msc  # 查看PostgreSQL服务状态
   
   # Linux
   sudo systemctl status postgresql
   ```

2. 连接信息是否正确
   ```bash
   # 测试连接
   psql -U aistudio_user -d pet_painting -h localhost
   ```

3. 防火墙是否阻止连接

### 问题2: 找不到新创建的订单

**检查项**:
1. 确认应用使用的是PostgreSQL（检查启动日志）
2. 检查 `.env` 文件配置
3. 直接在PostgreSQL中查询：
   ```sql
   SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
   ```

### 问题3: 数据不一致

**检查项**:
1. 运行迁移进度检查：
   ```bash
   python scripts/database/check_migration_progress.py
   ```

2. 对比SQLite和PostgreSQL数据

---

## 📚 相关文档

- [PostgreSQL迁移详细报告](./PostgreSQL数据迁移详细报告.md)
- [PostgreSQL迁移完成总结](./PostgreSQL迁移完成总结.md)
- [数据迁移断点续传说明](./数据迁移断点续传说明.md)
- [pgAdmin操作指南](./pgAdmin操作指南.md)

---

**最后更新**: 2026-02-04  
**状态**: ✅ PostgreSQL已配置并运行
