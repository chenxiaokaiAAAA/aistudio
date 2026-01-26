# add_retouch_completed_at_field.py
# 数据库迁移脚本：为订单表添加精修美颜完成时间字段

import os
import sys
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 Flask 应用和数据库
from test_server import app, db

def add_retouch_completed_at_field():
    """为order表添加精修美颜完成时间字段"""
    
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
                    # 如果文件不存在，尝试在instance目录下查找
                    instance_db_path = os.path.join(app.root_path, 'instance', 'moeart.db')
                    if os.path.exists(instance_db_path):
                        db_path = instance_db_path
                        print(f"✅ 找到 instance 目录下的数据库文件: {db_path}")
                    else:
                        print("❌ 未找到任何数据库文件，请检查配置。")
                        return False
            else:
                print(f"⚠️  非 SQLite 数据库，使用 SQLAlchemy 方式")
                db_path = None
            
            # 使用原始 SQL 添加字段（SQLAlchemy 不支持 ALTER TABLE ADD COLUMN）
            from sqlalchemy import text
            
            # 检查order表是否存在
            order_table_exists = False
            table_names = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%order%'")).fetchall()
            
            # 尝试匹配 'order' 或 '"order"'
            actual_order_table_name = None
            for row in table_names:
                if row[0] == 'order' or row[0] == '"order"':
                    actual_order_table_name = row[0]
                    order_table_exists = True
                    break
            
            if not order_table_exists:
                print("❌ 未找到订单表(包含'order'的表)")
                print("数据库中的所有表:")
                for row in table_names:
                    print(f"- {row[0]}")
                return False
            
            print(f"✅ 找到订单表: {actual_order_table_name}")

            # 检查字段是否已存在
            # 使用方括号或双引号包裹表名，因为order是SQLite保留关键字
            # 先尝试使用方括号（兼容SQL Server语法）
            try:
                columns_info = db.session.execute(text("PRAGMA table_info([order])")).fetchall()
                existing_columns = [column[1] for column in columns_info]
                print(f"✅ 找到 order 表，当前包含 {len(existing_columns)} 个字段")
            except Exception as e:
                # 如果方括号失败，尝试双引号
                try:
                    columns_info = db.session.execute(text('PRAGMA table_info("order")')).fetchall()
                    existing_columns = [column[1] for column in columns_info]
                    print(f"✅ 找到 order 表，当前包含 {len(existing_columns)} 个字段")
                except Exception as e2:
                    print(f"❌ 无法访问 order 表: {e2}")
                    return False
            
            # 需要添加的字段
            field_name = 'retouch_completed_at'
            field_type = 'DATETIME'
            
            if field_name not in existing_columns:
                try:
                    # 先尝试使用方括号
                    alter_sql = f"ALTER TABLE [order] ADD COLUMN {field_name} {field_type}"
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    print(f"✅ 已添加字段: {field_name}")
                    return True
                except Exception as e:
                    db.session.rollback()
                    error_msg = str(e).lower()
                    if "duplicate column name" in error_msg or "already exists" in error_msg:
                        print(f"⚠️  字段 {field_name} 已存在，跳过")
                        return True
                    else:
                        # 尝试使用双引号
                        try:
                            alter_sql = f'ALTER TABLE "order" ADD COLUMN {field_name} {field_type}'
                            db.session.execute(text(alter_sql))
                            db.session.commit()
                            print(f"✅ 已添加字段: {field_name} (使用双引号)")
                            return True
                        except Exception as e2:
                            db.session.rollback()
                            print(f"❌ 添加字段 {field_name} 失败: {e2}")
                            import traceback
                            traceback.print_exc()
                            return False
            else:
                print(f"ℹ️  字段 {field_name} 已存在，跳过")
                return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("订单表添加精修美颜完成时间字段脚本")
    print("=" * 50)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = add_retouch_completed_at_field()
    
    print()
    if success:
        print("✅ 脚本执行完成")
    else:
        print("❌ 脚本执行失败")
    
    print("=" * 50)
