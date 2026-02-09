# PostgreSQL 迁移指南

**创建日期**: 2026-02-03  
**当前数据库**: SQLite  
**目标数据库**: PostgreSQL

---

## 📋 迁移前准备

### 1. 安装PostgreSQL

#### Windows
```bash
# 下载并安装PostgreSQL
# https://www.postgresql.org/download/windows/

# 或使用Chocolatey
choco install postgresql
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Linux (CentOS/RHEL)
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. 创建数据库和用户

```bash
# 切换到postgres用户
sudo -u postgres psql

# 创建数据库
CREATE DATABASE pet_painting;

# 创建用户（可选，建议使用独立用户）
CREATE USER aistudio_user WITH PASSWORD 'your_secure_password';

# 授予权限
GRANT ALL PRIVILEGES ON DATABASE pet_painting TO aistudio_user;

# 退出
\q
```

### 3. 安装Python依赖

```bash
# 安装PostgreSQL适配器
pip install psycopg2-binary

# 或使用psycopg2（需要编译，性能更好）
pip install psycopg2
```

更新 `requirements.txt`:
```txt
psycopg2-binary>=2.9.0
# 或
psycopg2>=2.9.0
```

---

## 🔧 配置修改

### 1. 修改数据库连接配置

#### 方法1：使用环境变量（推荐）

**开发环境** (`.env` 文件):
```bash
DATABASE_URL=postgresql://aistudio_user:your_secure_password@localhost:5432/pet_painting
```

**生产环境** (服务器环境变量):
```bash
export DATABASE_URL=postgresql://aistudio_user:your_secure_password@localhost:5432/pet_painting
```

#### 方法2：修改代码配置

**`app/__init__.py`**:
```python
# 修改默认数据库URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://aistudio_user:your_secure_password@localhost:5432/pet_painting'
)
```

**`test_server.py`**:
```python
# 找到数据库配置部分，修改为：
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://aistudio_user:your_secure_password@localhost:5432/pet_painting'
)

# 移除SQLite特有的配置
# 删除或注释掉：
# app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
#     'connect_args': {
#         'timeout': 20,
#         'check_same_thread': False,  # SQLite特有
#         'isolation_level': None      # SQLite特有
#     }
# }

# PostgreSQL连接池配置（可选，但推荐）
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,  # 自动重连
    'max_overflow': 20
}
```

### 2. 修改SQLite特有代码

#### 检查并修改以下文件：

1. **`app/models.py`** - 检查是否有SQLite特有的语法
2. **`test_server.py`** - 检查数据库迁移脚本中的SQLite语法
3. **所有路由文件** - 检查是否有SQLite特有的查询

#### 常见需要修改的地方：

**SQLite特有语法**:
```python
# SQLite: PRAGMA table_info
# PostgreSQL: 使用 information_schema
```

**布尔值处理**:
```python
# SQLite可能将布尔值存储为整数
# PostgreSQL使用真正的BOOLEAN类型
# 检查代码中是否有类似：
# if status == 1:  # SQLite风格
# 改为：
# if status == True:  # PostgreSQL风格
```

**时间处理**:
```python
# SQLite存储UTC时间字符串
# PostgreSQL使用TIMESTAMP类型
# 确保使用datetime对象而不是字符串
```

---

## 📦 数据迁移

### 方法1：使用SQLAlchemy自动迁移（推荐）

```python
# 创建迁移脚本: scripts/database/migrate_to_postgresql.py
from app import create_app, db
from app.models import *  # 导入所有模型

app = create_app()

with app.app_context():
    # 创建所有表（PostgreSQL）
    db.create_all()
    print("✅ PostgreSQL表结构已创建")
```

### 方法2：导出SQLite数据并导入PostgreSQL

#### 步骤1：导出SQLite数据

```python
# scripts/database/export_sqlite_data.py
import sqlite3
import json
import csv

def export_sqlite_data():
    conn = sqlite3.connect('instance/pet_painting.db')
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        data[table] = {
            'columns': columns,
            'rows': rows
        }
    
    # 保存为JSON
    with open('sqlite_export.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ 已导出 {len(tables)} 个表的数据")
    conn.close()

if __name__ == '__main__':
    export_sqlite_data()
```

#### 步骤2：导入到PostgreSQL

```python
# scripts/database/import_to_postgresql.py
import json
from app import create_app, db
from app.models import *

app = create_app()

def import_to_postgresql():
    with app.app_context():
        # 读取导出的数据
        with open('sqlite_export.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建表结构
        db.create_all()
        
        # 导入数据（需要根据实际模型调整）
        # 注意：需要处理外键关系，按依赖顺序导入
        
        print("✅ 数据导入完成")

if __name__ == '__main__':
    import_to_postgresql()
```

### 方法3：使用pgloader（Linux推荐）

```bash
# 安装pgloader
sudo apt-get install pgloader  # Ubuntu/Debian
# 或
sudo yum install pgloader      # CentOS/RHEL

# 迁移数据
pgloader sqlite:///path/to/pet_painting.db postgresql://user:password@localhost/pet_painting
```

---

## ✅ 迁移后验证

### 1. 检查表结构

```bash
# 连接到PostgreSQL
psql -U aistudio_user -d pet_painting

# 查看所有表
\dt

# 查看表结构
\d orders
\d ai_tasks
# ... 检查所有表
```

### 2. 检查数据完整性

```python
# scripts/database/verify_migration.py
from app import create_app, db
from app.models import Order, AITask, User

app = create_app()

with app.app_context():
    # 检查数据数量
    order_count = Order.query.count()
    task_count = AITask.query.count()
    user_count = User.query.count()
    
    print(f"订单数量: {order_count}")
    print(f"AI任务数量: {task_count}")
    print(f"用户数量: {user_count}")
    
    # 检查关联关系
    order = Order.query.first()
    if order:
        print(f"订单 {order.order_number} 的AI任务: {len(order.ai_tasks)}")
```

### 3. 功能测试

- [ ] 用户登录
- [ ] 订单创建
- [ ] 订单查询
- [ ] AI任务创建和查询
- [ ] 数据统计
- [ ] 所有API接口

---

## 🔒 安全配置

### 1. 连接安全

**`pg_hba.conf`** (PostgreSQL配置文件):
```
# 只允许本地连接（生产环境）
host    pet_painting    aistudio_user    127.0.0.1/32    md5

# 或使用SSL（推荐）
hostssl pet_painting    aistudio_user    127.0.0.1/32    md5
```

### 2. 密码管理

- 使用强密码
- 不要在代码中硬编码密码
- 使用环境变量或密钥管理服务

### 3. 备份策略

```bash
# 创建备份脚本
pg_dump -U aistudio_user -d pet_painting > backup_$(date +%Y%m%d).sql

# 恢复备份
psql -U aistudio_user -d pet_painting < backup_20260203.sql
```

---

## 📊 性能优化

### 1. 索引优化

PostgreSQL会自动创建主键索引，但需要检查：

```sql
-- 查看所有索引
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public';

-- 添加缺失的索引（参考数据库优化总结.md）
CREATE INDEX idx_order_status ON orders(status);
CREATE INDEX idx_order_created_at ON orders(created_at);
-- ... 其他索引
```

### 2. 连接池配置

```python
# test_server.py 或 app/__init__.py
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,           # 连接池大小
    'pool_recycle': 3600,       # 连接回收时间（秒）
    'pool_pre_ping': True,     # 自动重连
    'max_overflow': 20,        # 最大溢出连接数
    'echo': False              # 是否打印SQL（生产环境设为False）
}
```

### 3. 查询优化

- 使用`EXPLAIN ANALYZE`分析慢查询
- 定期运行`VACUUM ANALYZE`优化数据库
- 监控数据库性能

---

## ⚠️ 注意事项

### 1. SQLite vs PostgreSQL 差异

| 特性 | SQLite | PostgreSQL |
|------|--------|------------|
| 数据类型 | 动态类型 | 严格类型 |
| 布尔值 | INTEGER (0/1) | BOOLEAN |
| 字符串比较 | 大小写敏感 | 可配置 |
| 日期时间 | TEXT/REAL | TIMESTAMP |
| 并发写入 | 有限 | 优秀 |
| 事务隔离 | 简单 | 完整支持 |

### 2. 需要修改的代码

- [ ] 检查所有使用`PRAGMA`的地方
- [ ] 检查布尔值比较（`== 1` 改为 `== True`）
- [ ] 检查时间字符串处理
- [ ] 检查SQLite特有的函数

### 3. 回滚方案

保留SQLite数据库备份，如果迁移失败可以快速回滚：

```bash
# 备份SQLite数据库
cp instance/pet_painting.db instance/pet_painting.db.backup

# 如果需要回滚，修改环境变量：
export DATABASE_URL=sqlite:///instance/pet_painting.db
```

---

## 📝 迁移检查清单

### 迁移前
- [ ] 备份SQLite数据库
- [ ] 安装PostgreSQL
- [ ] 创建数据库和用户
- [ ] 安装Python依赖（psycopg2）
- [ ] 测试PostgreSQL连接

### 迁移中
- [ ] 修改数据库连接配置
- [ ] 移除SQLite特有配置
- [ ] 创建PostgreSQL表结构
- [ ] 迁移数据
- [ ] 验证数据完整性

### 迁移后
- [ ] 功能测试
- [ ] 性能测试
- [ ] 配置备份策略
- [ ] 监控数据库性能
- [ ] 更新文档

---

## 🚀 快速迁移脚本

创建 `scripts/database/migrate_to_postgresql.sh`:

```bash
#!/bin/bash

echo "开始迁移到PostgreSQL..."

# 1. 备份SQLite数据库
echo "1. 备份SQLite数据库..."
cp instance/pet_painting.db instance/pet_painting.db.backup_$(date +%Y%m%d_%H%M%S)

# 2. 设置环境变量
echo "2. 设置环境变量..."
export DATABASE_URL=postgresql://aistudio_user:password@localhost:5432/pet_painting

# 3. 创建表结构
echo "3. 创建PostgreSQL表结构..."
python -c "from app import create_app, db; from app.models import *; app = create_app(); app.app_context().push(); db.create_all(); print('✅ 表结构创建完成')"

# 4. 迁移数据（使用pgloader或自定义脚本）
echo "4. 迁移数据..."
# pgloader sqlite:///$(pwd)/instance/pet_painting.db postgresql://aistudio_user:password@localhost:5432/pet_painting

echo "✅ 迁移完成！"
echo "⚠️  请记得："
echo "   1. 测试所有功能"
echo "   2. 验证数据完整性"
echo "   3. 配置备份策略"
```

---

**最后更新**: 2026-02-03  
**状态**: 待执行
