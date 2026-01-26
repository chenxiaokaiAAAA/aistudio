#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加物流信息字段到订单表
将客户地址和快递物流信息分开存储
"""

import sqlite3
import os
from datetime import datetime

def migrate_logistics_field():
    """添加物流信息字段"""
    db_path = 'pet_painting.db'
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return

    # 备份数据库
    backup_path = f"pet_painting_backup_logistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    print(f"备份数据库到: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("PRAGMA table_info(`order`)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"当前order表字段: {columns}")

        # 添加新字段
        new_fields = [
            ('customer_address', 'TEXT'),  # 客户收货地址
            ('logistics_info', 'TEXT'),    # 快递物流信息（JSON格式）
        ]

        for field_name, field_type in new_fields:
            if field_name not in columns:
                print(f"添加字段 {field_name} ({field_type})...")
                cursor.execute(f"ALTER TABLE `order` ADD COLUMN {field_name} {field_type}")
                conn.commit()
                print(f"✅ {field_name} 字段添加成功")
            else:
                print(f"⚠️ {field_name} 字段已存在，跳过")

        # 迁移现有数据
        print("\n迁移现有数据...")
        cursor.execute("SELECT id, shipping_info FROM `order` WHERE shipping_info IS NOT NULL AND shipping_info != ''")
        orders = cursor.fetchall()
        
        for order_id, shipping_info in orders:
            if shipping_info and not shipping_info.startswith('{'):
                # 旧格式：纯文本地址，移动到customer_address
                print(f"迁移订单 {order_id} 的地址信息...")
                cursor.execute("UPDATE `order` SET customer_address = ? WHERE id = ?", (shipping_info, order_id))
                conn.commit()
                print(f"✅ 订单 {order_id} 地址信息已迁移")

        print("\n数据库迁移完成")

        # 显示更新后的表结构
        print("\n更新后的order表结构:")
        cursor.execute("PRAGMA table_info(`order`)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")

    except Exception as e:
        print(f"迁移失败: {str(e)}")
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print("已恢复备份数据库")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_logistics_field()
