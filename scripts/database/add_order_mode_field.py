#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为orders表添加order_mode字段
用于标记订单类型：shooting（立即拍摄）或 making（立即制作）
"""

import sys
import os

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_server import app, db
from sqlalchemy import text


def add_order_mode_field():
    """为orders表添加order_mode字段"""
    with app.app_context():
        try:
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # 查找订单表名（可能是orders或order）
            order_table_name = None
            for table_name in existing_tables:
                if table_name.lower() in ['orders', 'order']:
                    order_table_name = table_name
                    break
            
            if not order_table_name:
                print("[ERROR] 未找到订单表（orders或order）")
                return False
            
            print(f"[OK] 找到订单表: {order_table_name}")
            
            # 检查字段是否已存在
            try:
                # 尝试查询表结构
                result = db.session.execute(text(f"PRAGMA table_info([{order_table_name}])"))
                existing_columns = [row[1] for row in result.fetchall()]
                print(f"[OK] 当前表包含 {len(existing_columns)} 个字段")
            except Exception as e:
                print(f"[ERROR] 无法访问 {order_table_name} 表: {e}")
                return False
            
            # 需要添加的字段
            field_name = 'order_mode'
            field_type = 'VARCHAR(20)'
            
            if field_name not in existing_columns:
                try:
                    # 先尝试使用方括号
                    alter_sql = f"ALTER TABLE [{order_table_name}] ADD COLUMN {field_name} {field_type}"
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    print(f"[OK] 已添加字段: {field_name}")
                    return True
                except Exception as e:
                    db.session.rollback()
                    error_msg = str(e).lower()
                    if "duplicate column name" in error_msg or "already exists" in error_msg:
                        print(f"[WARN] 字段 {field_name} 已存在，跳过")
                        return True
                    else:
                        # 尝试使用双引号
                        try:
                            alter_sql = f'ALTER TABLE "{order_table_name}" ADD COLUMN {field_name} {field_type}'
                            db.session.execute(text(alter_sql))
                            db.session.commit()
                            print(f"[OK] 已添加字段: {field_name} (使用双引号)")
                            return True
                        except Exception as e2:
                            db.session.rollback()
                            print(f"[ERROR] 添加字段 {field_name} 失败: {e2}")
                            import traceback
                            traceback.print_exc()
                            return False
            else:
                print(f"[INFO] 字段 {field_name} 已存在，跳过")
                return True
                
        except Exception as e:
            print(f"[ERROR] 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    print("=" * 50)
    print("添加 order_mode 字段到订单表")
    print("=" * 50)
    
    if add_order_mode_field():
        print("\n[OK] 迁移完成！")
        sys.exit(0)
    else:
        print("\n[ERROR] 迁移失败！")
        sys.exit(1)
