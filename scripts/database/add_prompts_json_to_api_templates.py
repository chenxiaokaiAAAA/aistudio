# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 api_templates 表添加 prompts_json 字段
"""
import os
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入 Flask 应用和数据库
from test_server import app, db

def migrate_database():
    """添加 prompts_json 字段到 api_templates 表"""
    
    with app.app_context():
        try:
            # 获取数据库 URI
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"✅ 数据库 URI: {db_uri}")
            
            # 检查字段是否已存在
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            
            # 检查表是否存在
            existing_tables = inspector.get_table_names()
            if 'api_templates' not in existing_tables:
                print("❌ api_templates 表不存在，请先创建表")
                return False
            
            columns = [col['name'] for col in inspector.get_columns('api_templates')]
            
            if 'prompts_json' in columns:
                print("✅ prompts_json 字段已存在，跳过迁移")
                return True
            
            print("🔄 开始添加 prompts_json 字段到 api_templates 表...")
            
            # 添加字段
            with db.engine.connect() as conn:
                # SQLite 使用 ALTER TABLE ADD COLUMN
                conn.execute(text("""
                    ALTER TABLE api_templates 
                    ADD COLUMN prompts_json TEXT
                """))
                conn.commit()
            
            print("✅ prompts_json 字段添加成功")
            
            # 验证字段是否添加成功
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('api_templates')]
            if 'prompts_json' in columns:
                print("✅ 验证成功: prompts_json 字段已存在于 api_templates 表")
                return True
            else:
                print("❌ 验证失败: prompts_json 字段未找到")
                return False
                
        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("数据库迁移：添加 prompts_json 字段")
    print("=" * 50)
    print()
    
    success = migrate_database()
    
    if success:
        print()
        print("=" * 50)
        print("✅ 迁移完成")
        print("=" * 50)
        sys.exit(0)
    else:
        print()
        print("=" * 50)
        print("❌ 迁移失败")
        print("=" * 50)
        sys.exit(1)
