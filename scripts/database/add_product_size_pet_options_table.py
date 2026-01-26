#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建ProductSizePetOption表的迁移脚本
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

def add_pet_options_table():
    """创建ProductSizePetOption表"""
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'product_size_pet_options' not in existing_tables:
                print("正在创建 product_size_pet_options 表...")
                db.engine.execute(text("""
                    CREATE TABLE product_size_pet_options (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        size_id INTEGER NOT NULL,
                        pet_count_name VARCHAR(50) NOT NULL,
                        price FLOAT NOT NULL,
                        sort_order INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (size_id) REFERENCES product_sizes (id)
                    )
                """))
                print("product_size_pet_options 表创建成功")
            else:
                print("product_size_pet_options 表已存在，跳过创建")
            
            print("迁移完成")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("开始数据库迁移...")
    if add_pet_options_table():
        print("迁移成功完成")
    else:
        print("迁移失败")
        sys.exit(1)


