# -*- coding: utf-8 -*-
"""
创建店员用户表（StaffUser）的数据库迁移脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_server import app, db
from app.models import StaffUser

def create_staff_user_table():
    """创建店员用户表"""
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'staff_users' in existing_tables:
                print("⚠️  表 'staff_users' 已存在，跳过创建")
                return
            
            # 创建表
            db.create_all()
            print("✅ 店员用户表 'staff_users' 创建成功")
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_staff_user_table()
