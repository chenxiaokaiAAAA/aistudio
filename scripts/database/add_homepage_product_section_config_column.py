#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
为 homepage_product_section 表添加 config 字段
用于存储当季主推、时光旅程、IP联名、作品展示等模块的配置数据
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_server import app, db

def add_config_column():
    """为 homepage_product_section 表添加 config 字段"""
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('homepage_product_section')]
            
            if 'config' in columns:
                print('✅ config 字段已存在，无需添加')
                return
            
            # 添加 config 字段
            db.engine.execute("""
                ALTER TABLE homepage_product_section 
                ADD COLUMN config TEXT
            """)
            
            print('✅ 成功为 homepage_product_section 表添加 config 字段')
            
        except Exception as e:
            print(f'❌ 添加字段失败: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    add_config_column()
