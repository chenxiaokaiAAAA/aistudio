#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从服务器数据库同步订单数据到本地数据库
只同步订单相关表，不破坏现有结构
"""

import sqlite3
import os
from datetime import datetime

# 设置标准输出编码（Windows兼容）
import sys
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

SOURCE_DB = 'instance/服务器pet_painting.db'
TARGET_DB = 'instance/pet_painting.db'

def get_table_columns(conn, table_name):
    """获取表的列信息"""
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    columns = cursor.fetchall()
    return [col[1] for col in columns]  # 返回列名列表

def sync_table(source_conn, target_conn, table_name, key_column='id', skip_existing=True):
    """
    同步表数据
    
    Args:
        source_conn: 源数据库连接
        target_conn: 目标数据库连接
        table_name: 表名
        key_column: 主键列名
        skip_existing: 是否跳过已存在的记录（基于主键）
    """
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    # 检查表是否存在
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not source_cursor.fetchone():
        print(f"  源数据库中不存在表: {table_name}")
        return 0
    
    target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not target_cursor.fetchone():
        print(f"  目标数据库中不存在表: {table_name}，跳过")
        return 0
    
    # 获取列信息
    source_columns = get_table_columns(source_conn, table_name)
    target_columns = get_table_columns(target_conn, table_name)
    
    # 找出共同的列
    common_columns = [col for col in source_columns if col in target_columns]
    if not common_columns:
        print(f"  表 {table_name} 没有共同列，跳过")
        return 0
    
    print(f"  表 {table_name}: 共同列 {len(common_columns)} 个")
    
    # 如果跳过已存在的记录，先获取目标表中已有的主键值
    existing_keys = set()
    if skip_existing and key_column in target_columns:
        try:
            target_cursor.execute(f'SELECT {key_column} FROM "{table_name}"')
            existing_keys = {row[0] for row in target_cursor.fetchall()}
        except Exception as e:
            print(f"  获取已有记录时出错: {str(e)}")
    
    # 构建查询和插入语句
    columns_str = ", ".join([f'"{col}"' for col in common_columns])
    placeholders = ", ".join(["?" for _ in common_columns])
    
    source_cursor.execute(f'SELECT {columns_str} FROM "{table_name}"')
    rows = source_cursor.fetchall()
    
    inserted_count = 0
    skipped_count = 0
    updated_count = 0
    
    for row in rows:
        row_dict = dict(zip(common_columns, row))
        
        # 检查是否已存在
        if skip_existing and key_column in row_dict:
            key_value = row_dict[key_column]
            if key_value in existing_keys:
                skipped_count += 1
                continue
        
        # 插入数据
        try:
            target_cursor.execute(
                f'INSERT OR REPLACE INTO "{table_name}" ({columns_str}) VALUES ({placeholders})',
                row
            )
            if key_column in row_dict and row_dict[key_column] in existing_keys:
                updated_count += 1
            else:
                inserted_count += 1
        except Exception as e:
            print(f"  插入数据失败: {str(e)}")
            print(f"  数据: {row_dict}")
    
    target_conn.commit()
    
    print(f"    插入: {inserted_count} 条, 更新: {updated_count} 条, 跳过: {skipped_count} 条")
    return inserted_count + updated_count

def main():
    print("=" * 80)
    print("同步订单数据")
    print("=" * 80)
    print(f"源数据库: {SOURCE_DB}")
    print(f"目标数据库: {TARGET_DB}")
    print()
    
    # 检查文件是否存在
    if not os.path.exists(SOURCE_DB):
        print(f"错误: 源数据库文件不存在: {SOURCE_DB}")
        return
    
    if not os.path.exists(TARGET_DB):
        print(f"错误: 目标数据库文件不存在: {TARGET_DB}")
        return
    
    # 连接数据库
    try:
        source_conn = sqlite3.connect(SOURCE_DB)
        target_conn = sqlite3.connect(TARGET_DB)
        
        print("已连接数据库")
        print()
        
        # 要同步的表（订单相关）
        tables_to_sync = [
            ('order', 'id'),  # 订单主表
            ('order_image', 'id'),  # 订单图片表
        ]
        
        total_synced = 0
        
        for table_name, key_column in tables_to_sync:
            print(f"同步表: {table_name}")
            print("-" * 80)
            count = sync_table(source_conn, target_conn, table_name, key_column, skip_existing=True)
            total_synced += count
            print()
        
        print("=" * 80)
        print(f"同步完成！共同步 {total_synced} 条记录")
        print("=" * 80)
        
        # 关闭连接
        source_conn.close()
        target_conn.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

