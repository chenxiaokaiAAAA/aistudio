#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加产品和风格分类关联表的数据库迁移脚本
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db
from sqlalchemy import text

def add_product_style_category_table():
    """创建产品和风格分类关联表"""
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'product_style_categories' not in existing_tables:
                # 创建表
                db.engine.execute(text("""
                    CREATE TABLE product_style_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        style_category_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (style_category_id) REFERENCES style_category(id),
                        UNIQUE(product_id, style_category_id)
                    )
                """))
                print("[成功] 产品和风格分类关联表创建成功")
            else:
                print("[信息] 产品和风格分类关联表已存在")
            
            # 检查唯一约束是否存在
            try:
                db.engine.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS _product_style_category_uc 
                    ON product_style_categories(product_id, style_category_id)
                """))
                print("[成功] 唯一约束创建成功")
            except Exception as e:
                print(f"[警告] 唯一约束可能已存在: {e}")
            
            print("[完成] 数据库迁移完成")
            
        except Exception as e:
            print(f"[失败] 数据库迁移失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_product_style_category_table()

