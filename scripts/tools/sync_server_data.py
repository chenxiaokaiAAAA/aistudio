#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从服务器数据库同步订单和加盟商数据到本地数据库
只导入新数据，不覆盖现有数据
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# 设置标准输出编码（Windows兼容）
import sys
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def get_table_columns(conn, table_name):
    """获取表的列信息"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [col[1] for col in columns]  # 返回列名列表

def get_existing_ids(conn, table_name, id_column='id'):
    """获取表中已存在的ID列表"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT {id_column} FROM {table_name}")
        return set(row[0] for row in cursor.fetchall())
    except sqlite3.OperationalError:
        return set()

def sync_franchisee_accounts(source_conn, target_conn, dry_run=True):
    """同步加盟商账户表"""
    print("\n" + "=" * 80)
    print("同步加盟商账户 (franchisee_accounts)")
    print("=" * 80)
    
    # 检查表是否存在
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='franchisee_accounts'")
        if not source_cursor.fetchone():
            print("源数据库中没有 franchisee_accounts 表，跳过")
            return {}
        
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='franchisee_accounts'")
        if not target_cursor.fetchone():
            print("目标数据库中没有 franchisee_accounts 表，跳过")
            return {}
    except:
        print("检查表时出错，跳过")
        return {}
    
    # 获取列信息
    source_columns = get_table_columns(source_conn, 'franchisee_accounts')
    target_columns = get_table_columns(target_conn, 'franchisee_accounts')
    
    # 找出共同的列
    common_columns = [col for col in source_columns if col in target_columns]
    if 'id' not in common_columns:
        print("错误: 表结构不匹配，缺少id列")
        return {}
    
    print(f"共同列: {', '.join(common_columns)}")
    
    # 获取已存在的ID
    existing_ids = get_existing_ids(target_conn, 'franchisee_accounts')
    print(f"目标数据库中已有 {len(existing_ids)} 条记录")
    
    # 获取源数据
    source_cursor.execute(f"SELECT {', '.join(common_columns)} FROM franchisee_accounts")
    source_rows = source_cursor.fetchall()
    
    # ID映射表（源ID -> 目标ID）
    id_mapping = {}
    
    # 同步数据
    new_count = 0
    updated_count = 0
    
    for row in source_rows:
        row_dict = dict(zip(common_columns, row))
        source_id = row_dict['id']
        
        if source_id in existing_ids:
            # 已存在，记录映射关系
            id_mapping[source_id] = source_id
            if not dry_run:
                # 更新现有记录（除了id和password）
                update_columns = [col for col in common_columns if col not in ['id', 'password']]
                if update_columns:
                    set_clause = ', '.join([f"{col} = ?" for col in update_columns])
                    values = [row_dict[col] for col in update_columns] + [source_id]
                    target_cursor.execute(f"UPDATE franchisee_accounts SET {set_clause} WHERE id = ?", values)
                    updated_count += 1
        else:
            # 新记录，插入
            if not dry_run:
                insert_columns = [col for col in common_columns if col != 'id']
                placeholders = ', '.join(['?' for _ in insert_columns])
                values = [row_dict[col] for col in insert_columns]
                
                # 先插入获取新ID
                target_cursor.execute(f"INSERT INTO franchisee_accounts ({', '.join(insert_columns)}) VALUES ({placeholders})", values)
                new_id = target_cursor.lastrowid
                id_mapping[source_id] = new_id
                new_count += 1
                print(f"  新增: ID {source_id} -> {new_id}, 用户名: {row_dict.get('username', 'N/A')}")
            else:
                print(f"  [预览] 将新增: ID {source_id}, 用户名: {row_dict.get('username', 'N/A')}")
                new_count += 1
    
    print(f"\n统计: 新增 {new_count} 条, 更新 {updated_count} 条")
    return id_mapping

def sync_franchisee_recharges(source_conn, target_conn, franchisee_id_mapping, dry_run=True):
    """同步加盟商充值记录表"""
    print("\n" + "=" * 80)
    print("同步加盟商充值记录 (franchisee_recharges)")
    print("=" * 80)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='franchisee_recharges'")
        if not source_cursor.fetchone():
            print("源数据库中没有 franchisee_recharges 表，跳过")
            return
        
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='franchisee_recharges'")
        if not target_cursor.fetchone():
            print("目标数据库中没有 franchisee_recharges 表，跳过")
            return
    except:
        print("检查表时出错，跳过")
        return
    
    # 获取列信息
    source_columns = get_table_columns(source_conn, 'franchisee_recharges')
    target_columns = get_table_columns(target_conn, 'franchisee_recharges')
    common_columns = [col for col in source_columns if col in target_columns]
    
    print(f"共同列: {', '.join(common_columns)}")
    
    # 获取已存在的记录（基于franchisee_id和created_at判断）
    existing_records = set()
    if 'franchisee_id' in target_columns and 'created_at' in target_columns:
        target_cursor.execute("SELECT franchisee_id, created_at FROM franchisee_recharges")
        existing_records = set(target_cursor.fetchall())
    
    # 获取源数据
    source_cursor.execute(f"SELECT {', '.join(common_columns)} FROM franchisee_recharges")
    source_rows = source_cursor.fetchall()
    
    new_count = 0
    skipped_count = 0
    
    for row in source_rows:
        row_dict = dict(zip(common_columns, row))
        source_franchisee_id = row_dict.get('franchisee_id')
        created_at = row_dict.get('created_at')
        
        # 检查franchisee_id是否在映射表中
        if source_franchisee_id not in franchisee_id_mapping:
            skipped_count += 1
            continue
        
        target_franchisee_id = franchisee_id_mapping[source_franchisee_id]
        
        # 检查是否已存在
        if (target_franchisee_id, created_at) in existing_records:
            skipped_count += 1
            continue
        
        if not dry_run:
            # 插入新记录
            insert_columns = [col for col in common_columns if col != 'id']
            # 替换franchisee_id为映射后的ID
            values = []
            for col in insert_columns:
                if col == 'franchisee_id':
                    values.append(target_franchisee_id)
                else:
                    values.append(row_dict[col])
            
            placeholders = ', '.join(['?' for _ in insert_columns])
            target_cursor.execute(f"INSERT INTO franchisee_recharges ({', '.join(insert_columns)}) VALUES ({placeholders})", values)
            new_count += 1
            print(f"  新增: 加盟商ID {source_franchisee_id} -> {target_franchisee_id}, 金额: {row_dict.get('amount', 'N/A')}")
        else:
            print(f"  [预览] 将新增: 加盟商ID {source_franchisee_id} -> {target_franchisee_id}, 金额: {row_dict.get('amount', 'N/A')}")
            new_count += 1
    
    print(f"\n统计: 新增 {new_count} 条, 跳过 {skipped_count} 条")

def sync_orders(source_conn, target_conn, franchisee_id_mapping, dry_run=True):
    """同步订单表"""
    print("\n" + "=" * 80)
    print("同步订单 (order)")
    print("=" * 80)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
        if not source_cursor.fetchone():
            print("源数据库中没有 order 表，跳过")
            return {}
        
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
        if not target_cursor.fetchone():
            print("目标数据库中没有 order 表，跳过")
            return {}
    except:
        print("检查表时出错，跳过")
        return {}
    
    # 获取列信息
    source_columns = get_table_columns(source_conn, 'order')
    target_columns = get_table_columns(target_conn, 'order')
    common_columns = [col for col in source_columns if col in target_columns]
    
    print(f"共同列: {', '.join(common_columns)}")
    
    # 获取已存在的订单号
    target_cursor.execute("SELECT order_number FROM order")
    existing_order_numbers = set(row[0] for row in target_cursor.fetchall() if row[0])
    print(f"目标数据库中已有 {len(existing_order_numbers)} 条订单")
    
    # 获取源数据
    source_cursor.execute(f"SELECT {', '.join(common_columns)} FROM order ORDER BY id")
    source_rows = source_cursor.fetchall()
    
    # ID映射表（源ID -> 目标ID）
    order_id_mapping = {}
    new_count = 0
    skipped_count = 0
    
    for row in source_rows:
        row_dict = dict(zip(common_columns, row))
        source_id = row_dict['id']
        order_number = row_dict.get('order_number')
        
        # 检查订单号是否已存在
        if order_number and order_number in existing_order_numbers:
            # 获取目标数据库中的ID
            target_cursor.execute("SELECT id FROM order WHERE order_number = ?", (order_number,))
            target_row = target_cursor.fetchone()
            if target_row:
                order_id_mapping[source_id] = target_row[0]
                skipped_count += 1
                continue
        
        if not dry_run:
            # 插入新订单
            insert_columns = [col for col in common_columns if col != 'id']
            # 替换franchisee_id为映射后的ID
            values = []
            for col in insert_columns:
                if col == 'franchisee_id' and row_dict.get(col) and row_dict[col] in franchisee_id_mapping:
                    values.append(franchisee_id_mapping[row_dict[col]])
                else:
                    values.append(row_dict.get(col))
            
            placeholders = ', '.join(['?' for _ in insert_columns])
            target_cursor.execute(f"INSERT INTO order ({', '.join(insert_columns)}) VALUES ({placeholders})", values)
            new_id = target_cursor.lastrowid
            order_id_mapping[source_id] = new_id
            new_count += 1
            print(f"  新增: 订单ID {source_id} -> {new_id}, 订单号: {order_number}")
        else:
            print(f"  [预览] 将新增: 订单ID {source_id}, 订单号: {order_number}")
            new_count += 1
    
    print(f"\n统计: 新增 {new_count} 条, 跳过 {skipped_count} 条")
    return order_id_mapping

def sync_order_images(source_conn, target_conn, order_id_mapping, dry_run=True):
    """同步订单图片表"""
    print("\n" + "=" * 80)
    print("同步订单图片 (order_image)")
    print("=" * 80)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_image'")
        if not source_cursor.fetchone():
            print("源数据库中没有 order_image 表，跳过")
            return
        
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_image'")
        if not target_cursor.fetchone():
            print("目标数据库中没有 order_image 表，跳过")
            return
    except:
        print("检查表时出错，跳过")
        return
    
    # 获取列信息
    source_columns = get_table_columns(source_conn, 'order_image')
    target_columns = get_table_columns(target_conn, 'order_image')
    common_columns = [col for col in source_columns if col in target_columns]
    
    print(f"共同列: {', '.join(common_columns)}")
    
    # 获取源数据
    source_cursor.execute(f"SELECT {', '.join(common_columns)} FROM order_image")
    source_rows = source_cursor.fetchall()
    
    new_count = 0
    skipped_count = 0
    
    for row in source_rows:
        row_dict = dict(zip(common_columns, row))
        source_order_id = row_dict.get('order_id')
        
        # 检查order_id是否在映射表中
        if source_order_id not in order_id_mapping:
            skipped_count += 1
            continue
        
        target_order_id = order_id_mapping[source_order_id]
        
        if not dry_run:
            # 插入新记录
            insert_columns = [col for col in common_columns if col != 'id']
            values = []
            for col in insert_columns:
                if col == 'order_id':
                    values.append(target_order_id)
                else:
                    values.append(row_dict.get(col))
            
            placeholders = ', '.join(['?' for _ in insert_columns])
            target_cursor.execute(f"INSERT INTO order_image ({', '.join(insert_columns)}) VALUES ({placeholders})", values)
            new_count += 1
        else:
            print(f"  [预览] 将新增: 订单ID {source_order_id} -> {target_order_id}, 路径: {row_dict.get('path', 'N/A')}")
            new_count += 1
    
    print(f"\n统计: 新增 {new_count} 条, 跳过 {skipped_count} 条")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='从服务器数据库同步订单和加盟商数据')
    parser.add_argument('--source-db', default='instance/服务器pet_painting.db', help='源数据库路径')
    parser.add_argument('--target-db', default=None, help='目标数据库路径（默认: 自动查找）')
    parser.add_argument('--execute', action='store_true', help='执行同步（默认是预览模式）')
    args = parser.parse_args()
    
    # 自动查找目标数据库
    if args.target_db is None:
        if os.path.exists('instance/pet_painting.db'):
            args.target_db = 'instance/pet_painting.db'
        elif os.path.exists('pet_painting.db'):
            args.target_db = 'pet_painting.db'
        else:
            print("错误: 未找到目标数据库文件，请使用 --target-db 参数指定")
            return
    
    dry_run = not args.execute
    
    print("=" * 80)
    print("数据库同步工具")
    print("=" * 80)
    print(f"源数据库: {args.source_db}")
    print(f"目标数据库: {args.target_db}")
    print(f"模式: {'预览模式（不会实际修改）' if dry_run else '执行模式（将修改数据库）'}")
    print()
    
    if not os.path.exists(args.source_db):
        print(f"错误: 源数据库文件不存在: {args.source_db}")
        return
    
    if not os.path.exists(args.target_db):
        print(f"错误: 目标数据库文件不存在: {args.target_db}")
        return
    
    # 连接数据库
    try:
        source_conn = sqlite3.connect(args.source_db)
        target_conn = sqlite3.connect(args.target_db)
        
        # 启用外键约束
        target_conn.execute("PRAGMA foreign_keys = ON")
        
        print("数据库连接成功")
        print()
        
        # 1. 同步加盟商账户
        franchisee_id_mapping = sync_franchisee_accounts(source_conn, target_conn, dry_run)
        
        # 2. 同步加盟商充值记录
        sync_franchisee_recharges(source_conn, target_conn, franchisee_id_mapping, dry_run)
        
        # 3. 同步订单
        order_id_mapping = sync_orders(source_conn, target_conn, franchisee_id_mapping, dry_run)
        
        # 4. 同步订单图片
        sync_order_images(source_conn, target_conn, order_id_mapping, dry_run)
        
        # 提交事务
        if not dry_run:
            target_conn.commit()
            print("\n" + "=" * 80)
            print("同步完成！")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("预览完成！使用 --execute 参数来执行实际同步")
            print("=" * 80)
        
        source_conn.close()
        target_conn.close()
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            target_conn.rollback()

if __name__ == '__main__':
    main()

