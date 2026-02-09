# PostgreSQL 快速设置步骤

**适用场景**: 已安装PostgreSQL，需要快速设置数据库

---

## ✅ 步骤1: 安装Python驱动（已完成）

```bash
pip install psycopg2-binary
```

✅ **已完成！** `psycopg2-binary` 已安装

---

## 📝 步骤2: 创建数据库和用户

### 方法A: 使用pgAdmin（图形界面，推荐）

1. 打开 **pgAdmin**
2. 连接到PostgreSQL服务器
3. 右键点击 **Databases** → **Create** → **Database**
   - **Name**: `pet_painting`
   - 点击 **Save**

4. 右键点击 **Login/Group Roles** → **Create** → **Login/Group Role**
   - **General** 标签:
     - **Name**: `aistudio_user`
   - **Definition** 标签:
     - **Password**: 输入你的密码
   - **Privileges** 标签:
     - 勾选所有权限
   - 点击 **Save**

5. 右键点击 `pet_painting` 数据库 → **Properties** → **Security** 标签
   - 点击 **+** 添加权限
   - **Grantee**: 选择 `aistudio_user`
   - 勾选所有权限
   - 点击 **Save**

### 方法B: 使用命令行（需要找到psql.exe）

找到PostgreSQL安装目录（通常在 `C:\Program Files\PostgreSQL\XX\bin\`），然后：

```bash
# 进入PostgreSQL bin目录
cd "C:\Program Files\PostgreSQL\15\bin"

# 连接到PostgreSQL（使用postgres用户）
psql -U postgres

# 在psql中执行以下SQL命令：
CREATE DATABASE pet_painting;
CREATE USER aistudio_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE pet_painting TO aistudio_user;

# 连接到新数据库
\c pet_painting

# 授予schema权限
GRANT ALL ON SCHEMA public TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aistudio_user;

# 退出
\q
```

### 方法C: 使用Python脚本（自动）

```bash
python scripts\database\setup_postgresql.py
```

选择选项 **1** 创建数据库和用户

---

## 🔧 步骤3: 设置环境变量

### Windows PowerShell:
```powershell
$env:DATABASE_URL="postgresql://aistudio_user:your_password@localhost:5432/pet_painting"
```

### Windows CMD:
```cmd
set DATABASE_URL=postgresql://aistudio_user:your_password@localhost:5432/pet_painting
```

### 永久设置（推荐）:

创建或编辑 `.env` 文件（项目根目录）:
```bash
DATABASE_URL=postgresql://aistudio_user:your_password@localhost:5432/pet_painting
```

---

## 🗄️ 步骤4: 创建表结构

设置好环境变量后，运行：

```bash
python scripts\database\setup_postgresql.py
```

选择选项 **2** 创建表结构

或者直接运行：

```python
# 在Python中执行
from app import create_app, db
import app.models  # 导入所有模型

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ 表结构创建成功！")
```

---

## 📦 步骤5: 迁移数据（可选）

如果你有SQLite数据库需要迁移：

```bash
python scripts\database\migrate_sqlite_to_postgresql.py
```

选择选项 **3** 完整迁移（导出+导入）

---

## ✅ 验证设置

### 测试连接:

```python
# test_connection.py
import os
from app import create_app, db

app = create_app()
with app.app_context():
    try:
        # 测试连接
        db.engine.connect()
        print("✅ PostgreSQL连接成功！")
        
        # 查看表
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✅ 找到 {len(tables)} 个表")
        for table in sorted(tables):
            print(f"   - {table}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
```

运行：
```bash
python test_connection.py
```

---

## 🔍 常见问题

### 1. 找不到psql命令

**解决方案**: 
- 找到PostgreSQL安装目录（通常在 `C:\Program Files\PostgreSQL\XX\bin\`）
- 将该目录添加到系统PATH环境变量
- 或使用pgAdmin图形界面

### 2. 连接被拒绝

**检查**:
- PostgreSQL服务是否启动
- 端口是否正确（默认5432）
- 防火墙是否阻止连接

**启动服务**:
```powershell
# 在服务管理器中启动 "postgresql-x64-XX" 服务
# 或使用命令行：
net start postgresql-x64-15
```

### 3. 认证失败

**检查**:
- 用户名和密码是否正确
- `pg_hba.conf` 配置是否正确（允许本地连接）

---

## 📋 快速检查清单

- [ ] PostgreSQL已安装
- [ ] Python驱动已安装 (`psycopg2-binary`)
- [ ] 数据库已创建 (`pet_painting`)
- [ ] 用户已创建 (`aistudio_user`)
- [ ] 权限已授予
- [ ] 环境变量已设置 (`DATABASE_URL`)
- [ ] 表结构已创建
- [ ] 连接测试通过

---

**下一步**: 完成以上步骤后，可以开始使用PostgreSQL数据库了！
