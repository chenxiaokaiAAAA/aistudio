#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库修复脚本：为现有数据库添加缺失的字段
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'pet_painting.db'

def fix_database_schema():
    """为现有数据库添加缺失的字段"""
    
    if not os.path.exists(DATABASE_PATH):
        print("数据库文件不存在！")
        return

    # 备份当前数据库
    backup_path = f"pet_painting_backup_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.rename(DATABASE_PATH, backup_path)
    print(f"备份数据库到: {backup_path}")

    conn_backup = sqlite3.connect(backup_path)
    cursor_backup = conn_backup.cursor()

    conn_new = sqlite3.connect(DATABASE_PATH)
    cursor_new = conn_new.cursor()

    # 创建新的Order表结构（包含所有字段）
    cursor_new.execute('''
        CREATE TABLE "order" (
            id INTEGER NOT NULL,
            order_number VARCHAR(50) NOT NULL,
            customer_name VARCHAR(100) NOT NULL,
            customer_phone VARCHAR(20) NOT NULL,
            size VARCHAR(20),
            style_name VARCHAR(100),
            product_name VARCHAR(100),
            original_image VARCHAR(200) NOT NULL,
            final_image VARCHAR(200),
            hd_image VARCHAR(200),
            status VARCHAR(20) DEFAULT 'pending',
            shipping_info VARCHAR(500),
            merchant_id INTEGER,
            created_at DATETIME,
            completed_at DATETIME,
            commission FLOAT DEFAULT 0.0,
            price FLOAT DEFAULT 0.0,
            external_platform VARCHAR(50),
            external_order_number VARCHAR(100),
            source_type VARCHAR(20) DEFAULT 'website',
            printer_send_status VARCHAR(20) DEFAULT 'not_sent',
            printer_send_time DATETIME,
            printer_error_message TEXT,
            printer_response_data TEXT,
            PRIMARY KEY (id),
            UNIQUE (order_number),
            FOREIGN KEY(merchant_id) REFERENCES user (id)
        )
    ''')
    print("创建新的Order表结构...")

    # 复制数据
    cursor_backup.execute('PRAGMA table_info("order")')
    columns_backup = [col[1] for col in cursor_backup.fetchall()]
    print(f"备份表中的字段: {columns_backup}")

    # 要复制的字段（排除新增的字段）
    columns_to_copy = [col for col in columns_backup if col not in ['hd_image', 'printer_send_status', 'printer_send_time', 'printer_error_message', 'printer_response_data']]
    columns_str = ", ".join(columns_to_copy)
    placeholders = ", ".join(["?" for _ in columns_to_copy])

    cursor_backup.execute(f'SELECT {columns_str} FROM "order"')
    rows = cursor_backup.fetchall()

    for row in rows:
        # 插入数据到新表，新增字段使用默认值
        insert_sql = f'INSERT INTO "order" ({columns_str}, hd_image, printer_send_status, printer_send_time, printer_error_message, printer_response_data) VALUES ({placeholders}, NULL, "not_sent", NULL, NULL, NULL)'
        cursor_new.execute(insert_sql, row)
    print(f"复制了 {len(rows)} 条订单数据...")

    # 复制其他表
    tables_to_copy = ['user', 'order_image', 'style_category', 'style_image', 'homepage_banner', 'homepage_config']
    for table in tables_to_copy:
        try:
            cursor_backup.execute(f'SELECT * FROM {table}')
            rows = cursor_backup.fetchall()
            
            if rows:
                # 获取列名
                cursor_backup.execute(f'PRAGMA table_info({table})')
                columns = [col[1] for col in cursor_backup.fetchall()]
                columns_str = ", ".join(columns)
                placeholders = ", ".join(["?" for _ in columns])
                
                # 创建表
                cursor_backup.execute(f'SELECT sql FROM sqlite_master WHERE type="table" AND name="{table}"')
                create_sql = cursor_backup.fetchone()[0]
                cursor_new.execute(create_sql)
                
                # 插入数据
                insert_sql = f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})'
                for row in rows:
                    cursor_new.execute(insert_sql, row)
                print(f"复制了 {len(rows)} 条 {table} 数据...")
        except Exception as e:
            print(f"复制表 {table} 时出错: {e}")

    conn_new.commit()
    conn_backup.close()
    conn_new.close()
    print("数据库修复完成！")
    
    # 验证修复结果
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM "order"')
    order_count = cursor.fetchone()[0]
    print(f'修复后的订单数量: {order_count}')
    
    cursor.execute('SELECT COUNT(*) FROM user')
    user_count = cursor.fetchone()[0]
    print(f'修复后的用户数量: {user_count}')
    
    # 检查新字段是否存在
    cursor.execute('PRAGMA table_info("order")')
    columns = [col[1] for col in cursor.fetchall()]
    print(f'Order表字段: {columns}')
    
    conn.close()

if __name__ == '__main__':
    fix_database_schema()

