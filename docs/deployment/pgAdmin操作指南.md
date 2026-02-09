# pgAdmin 操作指南 - 创建数据库和用户

## 📋 步骤概览

1. 连接到PostgreSQL服务器
2. 创建数据库
3. 创建用户
4. 授予权限

---

## 🔌 步骤1: 连接到PostgreSQL服务器

1. **在左侧导航栏**，找到 "Servers (1)" → "PostgreSQL 18"
2. **如果显示红色X**，表示未连接，需要：
   - 右键点击 "PostgreSQL 18"
   - 选择 "Connect Server"
   - 输入密码（PostgreSQL安装时设置的postgres用户密码）
   - 点击 "OK"

3. **连接成功后**，左侧会显示绿色图标，可以展开查看

---

## 🗄️ 步骤2: 创建数据库

1. **展开服务器** "PostgreSQL 18"
2. **右键点击** "Databases"
3. **选择** "Create" → "Database..."

4. **在弹出窗口中填写**：
   - **General** 标签:
     - **Database**: `pet_painting`
     - **Owner**: 选择 `postgres`（默认）
     - **Comment**: （可选）"AI Studio 宠物绘画数据库"
   
   - **Definition** 标签:
     - **Encoding**: `UTF8`（默认）
     - **Template**: `template0`（推荐）
     - 其他保持默认

5. **点击 "Save"** 保存

---

## 👤 步骤3: 创建用户

1. **在左侧导航栏**，展开 "PostgreSQL 18"
2. **展开** "Login/Group Roles"
3. **右键点击** "Login/Group Roles"
4. **选择** "Create" → "Login/Group Role..."

5. **在弹出窗口中填写**：

   **General 标签**:
   - **Name**: `aistudio_user`
   - **Comment**: （可选）"AI Studio 应用数据库用户"

   **Definition 标签**:
   - **Password**: 输入一个强密码（记住这个密码！）
   - **Password expiration**: （可选）留空表示永不过期

   **Privileges 标签**:
   - ✅ **Can login?**: 勾选
   - ✅ **Create databases?**: 可选（如果需要）
   - ✅ **Create roles?**: 可选（如果需要）
   - 其他权限根据需要勾选

6. **点击 "Save"** 保存

---

## 🔐 步骤4: 授予数据库权限

### 方法A: 在数据库属性中设置（推荐）

1. **展开** "Databases"
2. **右键点击** `pet_painting` 数据库
3. **选择** "Properties..."

4. **切换到** "Security" 标签
5. **点击** "+" 按钮添加权限
6. **填写权限信息**:
   - **Grantee**: 选择 `aistudio_user`
   - **Privileges**: 勾选所有权限
     - ✅ **ALL**（或单独勾选：CONNECT, CREATE, TEMPORARY）
7. **点击 "Save"** 保存

### 方法B: 使用SQL查询工具

1. **右键点击** `pet_painting` 数据库
2. **选择** "Query Tool"

3. **在查询窗口中输入以下SQL**:
```sql
-- 授予数据库权限
GRANT ALL PRIVILEGES ON DATABASE pet_painting TO aistudio_user;

-- 连接到pet_painting数据库（需要先断开当前连接）
\c pet_painting

-- 授予schema权限
GRANT ALL ON SCHEMA public TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aistudio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aistudio_user;
```

4. **点击** 执行按钮（▶️）或按 `F5`

---

## ✅ 步骤5: 验证设置

### 测试连接

1. **右键点击** `pet_painting` 数据库
2. **选择** "Query Tool"
3. **输入测试SQL**:
```sql
-- 查看当前用户
SELECT current_user;

-- 查看数据库
SELECT current_database();

-- 查看权限
SELECT * FROM pg_roles WHERE rolname = 'aistudio_user';
```

4. **执行查询**，确认信息正确

---

## 🔧 步骤6: 获取连接信息

现在你需要记录以下信息，用于设置环境变量：

```
数据库名称: pet_painting
用户名: aistudio_user
密码: （你刚才设置的密码）
主机: localhost
端口: 5432（默认）
```

**连接字符串格式**:
```
postgresql://aistudio_user:你的密码@localhost:5432/pet_painting
```

---

## 📝 步骤7: 设置环境变量

### 在项目根目录创建 `.env` 文件:

```bash
DATABASE_URL=postgresql://aistudio_user:你的密码@localhost:5432/pet_painting
```

**注意**: 将 `你的密码` 替换为实际密码

### 或者在PowerShell中临时设置:

```powershell
$env:DATABASE_URL="postgresql://aistudio_user:你的密码@localhost:5432/pet_painting"
```

---

## 🎯 下一步

完成以上步骤后，运行测试脚本验证连接：

```bash
python test_postgresql_connection.py
```

如果测试通过，就可以继续创建表结构了！

---

## 🆘 常见问题

### Q1: 连接服务器时提示密码错误
- **解决**: 确认使用的是PostgreSQL安装时设置的postgres用户密码
- 如果忘记密码，可以重置（需要管理员权限）

### Q2: 创建用户时提示权限不足
- **解决**: 确保使用postgres用户（超级用户）连接

### Q3: 无法授予权限
- **解决**: 
  1. 确保用户已创建
  2. 确保数据库已创建
  3. 使用postgres用户执行授权操作

### Q4: 找不到某些选项
- **解决**: 确保已连接到服务器，并且展开相应的节点

---

## 📸 操作截图说明

1. **创建数据库**: Databases → 右键 → Create → Database
2. **创建用户**: Login/Group Roles → 右键 → Create → Login/Group Role
3. **授予权限**: 数据库 → 右键 → Properties → Security标签

---

**完成以上步骤后，告诉我，我会帮你继续下一步！** 🚀
