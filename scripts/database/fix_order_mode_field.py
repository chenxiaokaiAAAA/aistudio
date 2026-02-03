#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复orders表的order_mode字段
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


def fix_order_mode_field():
    """为orders表添加order_mode字段"""
    with app.app_context():
        try:
            # 检查字段是否已存在
            try:
                result = db.session.execute(text("PRAGMA table_info(orders)"))
                existing_columns = [row[1] for row in result.fetchall()]
                print(f"[INFO] orders表当前包含 {len(existing_columns)} 个字段")
            except Exception as e:
                print(f"[ERROR] 无法访问orders表: {e}")
                return False
            
            # 需要添加的字段
            field_name = 'order_mode'
            field_type = 'VARCHAR(20)'
            
            if field_name not in existing_columns:
                try:
                    # 添加字段
                    alter_sql = f"ALTER TABLE orders ADD COLUMN {field_name} {field_type}"
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
                        print(f"[ERROR] 添加字段 {field_name} 失败: {e}")
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
    print("修复 orders 表的 order_mode 字段")
    print("=" * 50)
    
    if fix_order_mode_field():
        print("\n[OK] 修复完成！")
        sys.exit(0)
    else:
        print("\n[ERROR] 修复失败！")
        sys.exit(1)
