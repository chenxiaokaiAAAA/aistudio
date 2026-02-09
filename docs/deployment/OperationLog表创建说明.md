# OperationLog 操作日志表创建说明

## 说明

新增 `OperationLog` 模型用于记录管理员操作日志。需创建表后，操作日志功能方可正常使用。

## 创建方式

### 方式一：PostgreSQL / SQLite 通用

**请在项目根目录执行**（`create_postgresql_tables.py` 在根目录，不在 app/routes 下）：

```bash
cd E:\AI-STUDIO\aistudio -V14
python create_postgresql_tables.py
```

或若已在其他目录：

```bash
python "E:\AI-STUDIO\aistudio -V14\create_postgresql_tables.py"
```

或使用 Flask 应用上下文：

```python
from app import create_app, db
import app.models  # 确保导入所有模型

app = create_app()
with app.app_context():
    db.create_all()
```

### 方式二：手动 SQL（PostgreSQL）

```sql
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id),
    username VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id VARCHAR(50),
    extra TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| user_id | int | 操作用户ID |
| username | string | 用户名（冗余） |
| action | string | 操作类型：login, user_update, order_update 等 |
| target_type | string | 操作对象类型：order, user, product 等 |
| target_id | string | 操作对象ID |
| extra | text | 扩展信息（JSON） |
| ip_address | string | IP 地址 |
| created_at | datetime | 创建时间 |

## 记录日志

在需要记录操作的地方调用：

```python
from app.models import OperationLog
from app import db

log = OperationLog(
    user_id=current_user.id,
    username=current_user.username,
    action="order_update",
    target_type="order",
    target_id=str(order_id),
    extra=json.dumps({"status": "completed"}),
    ip_address=request.remote_addr,
)
db.session.add(log)
db.session.commit()
```

---

**最后更新**: 2026-02-09
