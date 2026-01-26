#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加product_type字段到订单表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def add_product_type_field():
    """添加product_type字段到订单表"""
    print("🔧 添加product_type字段到订单表...")
    
    try:
        from test_server import app, db
        
        with app.app_context():
            # 检查字段是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('order')]
            
            if 'product_type' in columns:
                print("✅ product_type字段已存在")
                return True
            
            # 添加字段
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE `order` ADD COLUMN product_type VARCHAR(20)"))
                conn.commit()
            print("✅ 成功添加product_type字段")
            
            return True
            
    except Exception as e:
        print(f"❌ 添加字段失败: {str(e)}")
        return False

if __name__ == '__main__':
    success = add_product_type_field()
    if success:
        print("🎉 数据库更新完成！")
    else:
        print("⚠️ 数据库更新失败！")
