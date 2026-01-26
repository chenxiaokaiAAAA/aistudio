# -*- coding: utf-8 -*-
import sqlite3
import os

# 找到数据库文件（按优先级）
db_paths = [
    'pet_painting.db',
    os.path.join('instance', 'pet_painting.db'),
    os.path.join('aistudio', 'pet_painting.db'),
    os.path.join('aistudio', 'instance', 'pet_painting.db')
]

db_path = None
for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("ERROR: Cannot find database file")
    print("Tried paths:", db_paths)
    exit(1)

print(f"Using database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查字段是否存在
cursor.execute("PRAGMA table_info(products)")
columns = [row[1] for row in cursor.fetchall()]

if 'free_selection_count' in columns:
    print("OK: Field already exists")
else:
    # 添加字段
    print("Adding field...")
    cursor.execute("ALTER TABLE products ADD COLUMN free_selection_count INTEGER DEFAULT 1")
    cursor.execute("UPDATE products SET free_selection_count = 1 WHERE free_selection_count IS NULL")
    conn.commit()
    print("OK: Field added successfully")

conn.close()
