#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加产品分类表的数据库迁移脚本
创建一级分类和二级分类表，并在Product表中添加分类字段
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_server import app, db
from sqlalchemy import text, inspect

def add_product_categories():
    """创建产品分类表并添加分类字段到Product表"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # 1. 创建一级分类表
            if 'product_categories' not in existing_tables:
                print("正在创建 product_categories 表（一级分类）...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE product_categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(50) NOT NULL,
                            code VARCHAR(50) UNIQUE NOT NULL,
                            icon VARCHAR(10),
                            image_url VARCHAR(500),
                            sort_order INTEGER DEFAULT 0,
                            is_active BOOLEAN DEFAULT 1,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.commit()
                print("✅ product_categories 表创建成功")
                
                # 插入默认分类
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO product_categories (name, code, icon, sort_order) VALUES
                        ('证件照', 'idphoto', '📷', 1),
                        ('水杯', 'cup', '☕', 2),
                        ('挂件', 'keychain', '🔑', 3),
                        ('相框', 'frame', '🖼️', 4),
                        ('T恤', 'tshirt', '👕', 5),
                        ('抱枕', 'pillow', '🛋️', 6)
                    """))
                    conn.commit()
                print("✅ 默认一级分类插入成功")
            else:
                print("ℹ️ product_categories 表已存在")
            
            # 2. 创建二级分类表
            if 'product_subcategories' not in existing_tables:
                print("正在创建 product_subcategories 表（二级分类）...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE product_subcategories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category_id INTEGER NOT NULL,
                            name VARCHAR(50) NOT NULL,
                            code VARCHAR(50) NOT NULL,
                            icon VARCHAR(10),
                            image_url VARCHAR(500),
                            sort_order INTEGER DEFAULT 0,
                            is_active BOOLEAN DEFAULT 1,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (category_id) REFERENCES product_categories(id),
                            UNIQUE(category_id, code)
                        )
                    """))
                    conn.commit()
                print("✅ product_subcategories 表创建成功")
                
                # 插入默认二级分类（证件照的二级分类）
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO product_subcategories (category_id, name, code, sort_order) 
                        SELECT id, '标准证件照', 'standard', 1 FROM product_categories WHERE code = 'idphoto'
                        UNION ALL
                        SELECT id, '艺术证件照', 'artistic', 2 FROM product_categories WHERE code = 'idphoto'
                    """))
                    conn.commit()
                print("✅ 默认二级分类插入成功")
            else:
                print("ℹ️ product_subcategories 表已存在")
            
            # 3. 检查Product表是否有分类字段
            product_columns = [col['name'] for col in inspector.get_columns('products')]
            
            if 'category_id' not in product_columns:
                print("正在添加 category_id 字段到 products 表...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE products ADD COLUMN category_id INTEGER
                    """))
                    conn.commit()
                print("✅ category_id 字段添加成功")
            else:
                print("ℹ️ category_id 字段已存在")
            
            if 'subcategory_id' not in product_columns:
                print("正在添加 subcategory_id 字段到 products 表...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE products ADD COLUMN subcategory_id INTEGER
                    """))
                    conn.commit()
                print("✅ subcategory_id 字段添加成功")
            else:
                print("ℹ️ subcategory_id 字段已存在")
            
            print("\n✅ 产品分类系统初始化完成！")
            return True
            
        except Exception as e:
            print(f"❌ 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    add_product_categories()
