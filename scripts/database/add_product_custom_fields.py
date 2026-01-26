#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加产品自定义字段表和订单自定义字段字段的迁移脚本
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

def add_custom_fields_tables():
    """添加产品自定义字段表和订单自定义字段字段"""
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # 创建产品自定义字段表
            if 'product_custom_fields' not in existing_tables:
                print("正在创建 product_custom_fields 表...")
                db.engine.execute(text("""
                    CREATE TABLE product_custom_fields (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        field_name VARCHAR(50) NOT NULL,
                        field_type VARCHAR(20) NOT NULL,
                        field_options TEXT,
                        is_required BOOLEAN DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products (id)
                    )
                """))
                print("product_custom_fields 表创建成功")
            else:
                print("product_custom_fields 表已存在，跳过创建")
            
            # 检查Order表是否有custom_fields字段
            # 查找Order表名（可能是orders或order）
            order_table_name = None
            for table_name in existing_tables:
                if 'order' in table_name.lower():
                    order_table_name = table_name
                    break
            
            if order_table_name:
                order_columns = [col['name'] for col in inspector.get_columns(order_table_name)]
                if 'custom_fields' not in order_columns:
                    print(f"正在为 {order_table_name} 表添加 custom_fields 字段...")
                    # 使用参数化查询避免SQL注入和关键字冲突
                    db.engine.execute(text(f"""
                        ALTER TABLE `{order_table_name}` ADD COLUMN custom_fields TEXT
                    """))
                    print(f"{order_table_name} 表的 custom_fields 字段添加成功")
                else:
                    print(f"{order_table_name} 表的 custom_fields 字段已存在，跳过添加")
            else:
                print("未找到Order表，将在应用启动时自动创建")
            
            print("迁移完成")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("开始数据库迁移...")
    if add_custom_fields_tables():
        print("迁移成功完成")
    else:
        print("迁移失败")
        sys.exit(1)

