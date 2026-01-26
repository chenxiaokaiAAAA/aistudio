#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

# 检查主数据库
print("=== 主数据库 ===")
conn = sqlite3.connect('pet_painting.db')
cursor = conn.cursor()
cursor.execute('SELECT id, size_name, printer_product_id FROM product_sizes WHERE printer_product_id = "33673"')
result = cursor.fetchone()
if result:
    print(f"找到33673: ID={result[0]}, 尺寸={result[1]}")
else:
    print("主数据库中没有33673")
conn.close()

# 检查instance数据库
print("\n=== instance数据库 ===")
conn = sqlite3.connect('instance/pet_painting.db')
cursor = conn.cursor()
cursor.execute('SELECT id, size_name, printer_product_id FROM product_sizes WHERE printer_product_id = "33673"')
result = cursor.fetchone()
if result:
    print(f"找到33673: ID={result[0]}, 尺寸={result[1]}")
else:
    print("instance数据库中没有33673")
conn.close()
