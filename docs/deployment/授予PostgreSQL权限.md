# 授予PostgreSQL用户权限

## 问题
用户 `aistudio_user` 没有在 `public` schema 中创建表的权限。

## 解决方案

### 方法1: 使用pgAdmin（推荐）

1. **连接到PostgreSQL服务器**（使用postgres用户）

2. **右键点击** `pet_painting` 数据库 → **Query Tool**

3. **执行以下SQL命令**:

```sql
-- 连接到pet_painting数据库
\c pet_painting

-- 授予schema权限
GRANT ALL ON SCHEMA public TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aistudio_user;

-- 授予创建表权限
GRANT CREATE ON SCHEMA public TO aistudio_user;

-- 如果表已存在，授予表权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aistudio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aistudio_user;
```

4. **点击执行按钮**（▶️）或按 `F5`

### 方法2: 使用命令行

找到PostgreSQL的bin目录，然后：

```bash
psql -U postgres -d pet_painting
```

然后执行上面的SQL命令。

### 方法3: 使用postgres用户创建表（临时方案）

如果需要立即创建表，可以临时使用postgres用户：

1. 修改 `.env` 文件或环境变量：
```
DATABASE_URL=postgresql://postgres:你的postgres密码@localhost:5432/pet_painting
```

2. 运行创建表脚本

3. 创建完成后，改回使用 `aistudio_user`

---

## 验证权限

执行以下SQL检查权限：

```sql
-- 查看用户权限
SELECT 
    grantee, 
    privilege_type 
FROM information_schema.role_table_grants 
WHERE grantee = 'aistudio_user';

-- 查看schema权限
SELECT 
    grantee, 
    privilege_type 
FROM information_schema.role_usage_grants 
WHERE grantee = 'aistudio_user' AND object_schema = 'public';
```
