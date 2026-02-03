#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加风格二级分类表的数据库迁移脚本
创建二级分类表，并在StyleImage表中添加subcategory_id字段
"""

import sqlite3
import os

# 假设数据库文件在项目根目录下的 instance 文件夹中
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance', 'pet_painting.db')

def add_style_subcategories():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='style_subcategories'")
        if not cursor.fetchone():
            print("正在创建 style_subcategories 表（二级分类）...")
            cursor.execute("""
                CREATE TABLE style_subcategories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    code VARCHAR(50) NOT NULL,
                    icon VARCHAR(10),
                    cover_image VARCHAR(500),
                    sort_order INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES style_category(id),
                    UNIQUE(category_id, code)
                )
            """)
            conn.commit()
            print("Successfully created style_subcategories table")
        else:
            print("style_subcategories table already exists")
        
        # 检查style_image表是否有subcategory_id字段
        cursor.execute("PRAGMA table_info(style_image)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'subcategory_id' not in columns:
            print("正在添加 subcategory_id 字段到 style_image 表...")
            cursor.execute("ALTER TABLE style_image ADD COLUMN subcategory_id INTEGER")
            conn.commit()
            print("Successfully added subcategory_id column to style_image table")
        else:
            print("subcategory_id column already exists in style_image table")
        
        print("\nMigration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    add_style_subcategories()
