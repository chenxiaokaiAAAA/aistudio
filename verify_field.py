# -*- coding: utf-8 -*-
import sqlite3
import os
import sys

# 强制UTF-8输出
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

db_path = os.path.join('instance', 'pet_painting.db')
if not os.path.exists(db_path):
    print("Database not found at:", db_path)
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(products)")
cols = [r[1] for r in cursor.fetchall()]

print("Products table columns:")
for col in cols:
    marker = " <-- THIS ONE" if col == "extra_photo_price" else ""
    print(f"  {col}{marker}")

if 'extra_photo_price' in cols:
    print("\nSUCCESS: extra_photo_price field EXISTS!")
    cursor.execute("SELECT name, free_selection_count, extra_photo_price FROM products LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row[0]}: free={row[1]}, extra_price={row[2]}")
else:
    print("\nERROR: extra_photo_price field NOT FOUND")

conn.close()
