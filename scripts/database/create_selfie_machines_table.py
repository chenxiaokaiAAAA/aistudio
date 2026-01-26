# create_selfie_machines_table.py
# 数据库迁移脚本：创建自拍机设备表

import os
import sys
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 Flask 应用和数据库
from test_server import app, db

def create_selfie_machines_table():
    """创建自拍机设备表"""
    
    with app.app_context():
        try:
            # 获取数据库 URI
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"✅ 数据库 URI: {db_uri}")
            
            # 如果是 SQLite，提取实际文件路径
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                if not os.path.isabs(db_path):
                    # 相对路径，需要转换为绝对路径
                    db_path = os.path.join(os.getcwd(), db_path)
                print(f"✅ 数据库文件路径: {db_path}")
                
                if not os.path.exists(db_path):
                    print(f"❌ 数据库文件不存在: {db_path}")
                    return False
            else:
                print(f"⚠️  非 SQLite 数据库，使用 SQLAlchemy 创建表")
                db_path = None
            
            # 使用 SQLAlchemy 创建表（如果不存在）
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'selfie_machines' not in existing_tables:
                # 创建表
                from test_server import SelfieMachine
                db.create_all()
                print(f"✅ 已创建 selfie_machines 表")
            else:
                print(f"ℹ️  selfie_machines 表已存在")
            
            # 验证表结构
            if 'selfie_machines' in existing_tables or 'selfie_machines' in inspector.get_table_names():
                columns = inspector.get_columns('selfie_machines')
                print(f"✅ 表结构验证成功，包含 {len(columns)} 个字段:")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
            
            return True
                
        except Exception as e:
            print(f"❌ 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("创建自拍机设备表脚本")
    print("=" * 50)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = create_selfie_machines_table()
    
    print()
    if success:
        print("✅ 脚本执行完成")
    else:
        print("❌ 脚本执行失败")
    
    print("=" * 50)
