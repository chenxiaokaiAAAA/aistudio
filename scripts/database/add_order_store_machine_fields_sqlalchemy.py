# add_order_store_machine_fields_sqlalchemy.py
# 使用 SQLAlchemy 为订单表添加门店信息和自拍机信息字段
# 这样可以确保使用与 Flask 应用相同的数据库配置

import os
import sys
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 Flask 应用和数据库
from test_server import app, db, Order

def add_order_fields_with_sqlalchemy():
    """使用 SQLAlchemy 为 order 表添加新字段"""
    
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
                print(f"⚠️  非 SQLite 数据库，使用原始 SQL 方式")
                db_path = None
            
            # 使用原始 SQL 添加字段（SQLAlchemy 不支持 ALTER TABLE ADD COLUMN）
            from sqlalchemy import text
            
            # 需要添加的字段
            fields_to_add = {
                'store_name': 'VARCHAR(100)',  # 门店名称
                'selfie_machine_id': 'VARCHAR(100)'  # 自拍机序列号
            }
            
            # 检查表是否存在
            try:
                # 尝试查询表结构
                result = db.session.execute(text("PRAGMA table_info([order])"))
                existing_columns = [row[1] for row in result.fetchall()]
                print(f"✅ 找到 order 表，当前包含 {len(existing_columns)} 个字段")
            except Exception as e:
                print(f"❌ 无法访问 order 表: {e}")
                return False
            
            added_fields = []
            
            for field_name, field_type in fields_to_add.items():
                if field_name not in existing_columns:
                    try:
                        # 使用原始 SQL 添加字段
                        alter_sql = f"ALTER TABLE [order] ADD COLUMN {field_name} {field_type}"
                        db.session.execute(text(alter_sql))
                        db.session.commit()
                        added_fields.append(field_name)
                        print(f"✅ 已添加字段: {field_name}")
                    except Exception as e:
                        db.session.rollback()
                        error_msg = str(e).lower()
                        if "duplicate column name" in error_msg or "already exists" in error_msg:
                            print(f"⚠️  字段 {field_name} 已存在，跳过")
                        else:
                            print(f"❌ 添加字段 {field_name} 失败: {e}")
                            # 尝试其他引用方式
                            try:
                                alter_sql = f'ALTER TABLE "order" ADD COLUMN {field_name} {field_type}'
                                db.session.execute(text(alter_sql))
                                db.session.commit()
                                added_fields.append(field_name)
                                print(f"✅ 已添加字段: {field_name} (使用双引号)")
                            except Exception as e2:
                                db.session.rollback()
                                print(f"❌ 使用双引号也失败: {e2}")
                else:
                    print(f"ℹ️  字段 {field_name} 已存在，跳过")
            
            if added_fields:
                print(f"\n✅ 成功添加 {len(added_fields)} 个字段: {', '.join(added_fields)}")
                return True
            else:
                print("\nℹ️  所有字段已存在，无需添加")
                return True
                
        except Exception as e:
            print(f"❌ 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("订单表字段添加脚本 (使用 SQLAlchemy)")
    print("=" * 50)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = add_order_fields_with_sqlalchemy()
    
    print()
    if success:
        print("✅ 脚本执行完成")
    else:
        print("❌ 脚本执行失败")
    
    print("=" * 50)
