#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加产品表的 free_selection_count 字段
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_server import app, db
from app.models import Product

def add_free_selection_count_column():
    """添加 free_selection_count 字段到 products 表"""
    with app.app_context():
        try:
            # 检查字段是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            
            if 'free_selection_count' in columns:
                print("✅ free_selection_count 字段已存在，跳过添加")
                return
            
            # 添加字段
            print("正在添加 free_selection_count 字段到 products 表...")
            db.engine.execute("""
                ALTER TABLE products 
                ADD COLUMN free_selection_count INTEGER DEFAULT 1
            """)
            print("✅ free_selection_count 字段添加成功")
            
            # 更新现有记录的默认值
            db.session.execute("""
                UPDATE products 
                SET free_selection_count = 1 
                WHERE free_selection_count IS NULL
            """)
            db.session.commit()
            print("✅ 已更新现有记录的默认值")
            
        except Exception as e:
            print(f"❌ 添加字段失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    add_free_selection_count_column()
