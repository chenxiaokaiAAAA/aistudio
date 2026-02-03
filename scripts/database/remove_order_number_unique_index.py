#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
移除 orders 表中 order_number 字段的唯一索引
支持追加产品功能：多个订单记录可以使用相同的订单号
"""

import sqlite3
import sys
import os

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../../instance/pet_painting.db')

def remove_unique_index():
    """移除 order_number 的唯一索引"""
    if not os.path.exists(DATABASE_PATH):
        print(f"数据库文件不存在: {DATABASE_PATH}")
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取所有索引
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='orders'")
        indexes = cursor.fetchall()
        
        print("当前 orders 表的所有索引:")
        for idx_name, idx_sql in indexes:
            print(f"  - {idx_name}: {idx_sql}")
        
        # 查找与 order_number 相关的唯一索引
        order_number_indexes = []
        for idx_name, idx_sql in indexes:
            if idx_sql and ('order_number' in idx_sql.upper() or 'UNIQUE' in idx_sql.upper()):
                order_number_indexes.append(idx_name)
        
        if order_number_indexes:
            print(f"\n找到 {len(order_number_indexes)} 个与 order_number 相关的索引，准备删除...")
            for idx_name in order_number_indexes:
                print(f"  删除索引: {idx_name}")
                cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
            conn.commit()
            print("[成功] 已删除所有与 order_number 相关的唯一索引")
        else:
            print("\n未找到与 order_number 相关的唯一索引")
        
        # 检查表结构中的 UNIQUE 约束（SQLite 中 UNIQUE 约束可能直接在列定义中）
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='orders'")
        table_sql = cursor.fetchone()
        
        if table_sql:
            table_sql_str = table_sql[0]
            # 检查是否有 UNIQUE(order_number) 或 order_number UNIQUE
            if 'UNIQUE' in table_sql_str.upper() and 'order_number' in table_sql_str.upper():
                print("\n检测到表定义中有 UNIQUE 约束，需要重建表...")
                print("注意：这需要手动处理，因为重建表可能影响数据完整性")
                print("建议：直接修改 app/models.py 中的模型定义，移除 unique=True")
                return False
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[失败] 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("移除 orders 表中 order_number 字段的唯一索引")
    print("=" * 60)
    
    success = remove_unique_index()
    
    if success:
        print("\n[成功] 处理完成！")
        print("\n注意：如果仍有 UNIQUE 约束错误，请确保：")
        print("1. app/models.py 中 Order 模型的 order_number 字段已移除 unique=True")
        print("2. 重启应用服务器以使模型更改生效")
        sys.exit(0)
    else:
        print("\n[失败] 处理失败！")
        sys.exit(1)
