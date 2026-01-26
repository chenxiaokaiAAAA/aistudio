#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为ProductSize表添加multi_pet_additional_price字段的迁移脚本
"""
import sys
import os

# 设置输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db
from sqlalchemy import text

def add_multi_pet_price_field():
    """为ProductSize表添加multi_pet_additional_price字段"""
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'product_sizes' in existing_tables:
                # 检查字段是否已存在
                columns = [col['name'] for col in inspector.get_columns('product_sizes')]
                if 'multi_pet_additional_price' not in columns:
                    print("正在为 product_sizes 表添加 multi_pet_additional_price 字段...")
                    db.engine.execute(text("""
                        ALTER TABLE product_sizes ADD COLUMN multi_pet_additional_price FLOAT DEFAULT 0.0
                    """))
                    print("product_sizes 表的 multi_pet_additional_price 字段添加成功")
                else:
                    print("product_sizes 表的 multi_pet_additional_price 字段已存在，跳过添加")
            else:
                print("product_sizes 表不存在，将在应用启动时自动创建")
            
            print("迁移完成")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("开始数据库迁移...")
    if add_multi_pet_price_field():
        print("迁移成功完成")
    else:
        print("迁移失败")
        sys.exit(1)


