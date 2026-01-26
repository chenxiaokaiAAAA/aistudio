#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加冲印系统发送状态跟踪字段
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'pet_painting.db'

def migrate_printer_status():
    """添加冲印系统发送状态跟踪字段"""
    
    if not os.path.exists(DATABASE_PATH):
        print("数据库文件不存在，跳过迁移。")
        return

    # 备份现有数据库
    backup_path = f"pet_painting_backup_printer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.rename(DATABASE_PATH, backup_path)
    print(f"备份数据库到: {backup_path}")

    conn_backup = sqlite3.connect(backup_path)
    cursor_backup = conn_backup.cursor()

    conn_new = sqlite3.connect(DATABASE_PATH)
    cursor_new = conn_new.cursor()

    # 创建新的Order表结构（包含冲印系统字段）
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
    print("创建新的Order表结构（包含冲印系统字段）...")

    # 复制数据
    cursor_backup.execute('PRAGMA table_info("order")')
    columns_backup = [col[1] for col in cursor_backup.fetchall()]

    # 要复制的字段（排除新增的冲印系统字段）
    columns_to_copy = [col for col in columns_backup if col not in ['printer_send_status', 'printer_send_time', 'printer_error_message', 'printer_response_data']]
    columns_str = ", ".join(columns_to_copy)
    placeholders = ", ".join(["?" for _ in columns_to_copy])

    cursor_backup.execute(f'SELECT {columns_str} FROM "order"')
    rows = cursor_backup.fetchall()

    for row in rows:
        # 插入数据到新表，冲印系统字段使用默认值
        insert_sql = f'INSERT INTO "order" ({columns_str}, printer_send_status, printer_send_time, printer_error_message, printer_response_data) VALUES ({placeholders}, "not_sent", NULL, NULL, NULL)'
        cursor_new.execute(insert_sql, row)
    print("复制旧数据到新表...")

    conn_new.commit()
    conn_backup.close()
    conn_new.close()
    print("数据库迁移完成，冲印系统发送状态跟踪字段已添加。")
    print("新增字段：")
    print("- printer_send_status: 发送状态 (not_sent, sending, sent_success, sent_failed)")
    print("- printer_send_time: 发送时间")
    print("- printer_error_message: 错误信息")
    print("- printer_response_data: 冲印系统响应数据")

if __name__ == '__main__':
    migrate_printer_status()
