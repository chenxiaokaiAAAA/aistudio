# -*- coding: utf-8 -*-
"""
为StyleImage表添加design_image_url字段
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, StyleImage

def add_design_image_url_field():
    """为StyleImage表添加design_image_url字段"""
    with app.app_context():
        try:
            # 检查字段是否已存在
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('style_image')]
            
            if 'design_image_url' in columns:
                print("字段 design_image_url 已存在，跳过添加")
                return
            
            # 添加字段
            print("正在为 style_image 表添加 design_image_url 字段...")
            db.session.execute(text("""
                ALTER TABLE style_image 
                ADD COLUMN design_image_url VARCHAR(500)
            """))
            db.session.commit()
            print("✅ 字段添加成功")
            
        except Exception as e:
            print(f"❌ 添加字段失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    add_design_image_url_field()

