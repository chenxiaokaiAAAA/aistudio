#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
移除 orders 表中 order_number 字段的唯一约束
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

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../../instance/pet_painting.db')

def remove_unique_constraint():
    """移除 order_number 的唯一约束"""
    if not os.path.exists(DATABASE_PATH):
        print(f"数据库文件不存在: {DATABASE_PATH}")
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查是否存在唯一索引
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' 
            AND tbl_name='orders' 
            AND sql LIKE '%UNIQUE%order_number%'
        """)
        unique_indexes = cursor.fetchall()
        
        # 删除所有与 order_number 相关的唯一索引
        for index in unique_indexes:
            index_name = index[0]
            print(f"删除唯一索引: {index_name}")
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
        
        # 检查表结构，如果 order_number 有 UNIQUE 约束，需要重建表
        cursor.execute("PRAGMA table_info(orders)")
        columns = cursor.fetchall()
        
        has_unique_constraint = False
        for col in columns:
            if col[1] == 'order_number' and col[5]:  # col[5] 是 notnull 标志，但我们需要检查 UNIQUE
                # SQLite 的 UNIQUE 约束可能在表定义中
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='orders'")
                table_sql = cursor.fetchone()
                if table_sql and 'UNIQUE' in table_sql[0].upper() and 'order_number' in table_sql[0]:
                    has_unique_constraint = True
                    break
        
        if has_unique_constraint:
            print("检测到 order_number 有 UNIQUE 约束，需要重建表...")
            
            # 创建新表（不带 UNIQUE 约束）
            cursor.execute("""
                CREATE TABLE orders_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    order_number VARCHAR(50) NOT NULL,
                    customer_name VARCHAR(100) NOT NULL,
                    customer_phone VARCHAR(20) NOT NULL,
                    size VARCHAR(20),
                    style_name VARCHAR(100),
                    product_name VARCHAR(100),
                    original_image VARCHAR(200),
                    final_image VARCHAR(200),
                    final_image_clean VARCHAR(200),
                    hd_image VARCHAR(200),
                    hd_image_clean VARCHAR(200),
                    status VARCHAR(20) DEFAULT 'paid',
                    shipping_info VARCHAR(500),
                    customer_address TEXT,
                    logistics_info TEXT,
                    merchant_id INTEGER,
                    created_at DATETIME,
                    shooting_completed_at DATETIME,
                    retouch_completed_at DATETIME,
                    completed_at DATETIME,
                    commission FLOAT DEFAULT 0.0,
                    price FLOAT DEFAULT 0.0,
                    payment_time DATETIME,
                    transaction_id VARCHAR(100),
                    external_platform VARCHAR(50),
                    external_order_number VARCHAR(100),
                    source_type VARCHAR(20) DEFAULT 'website',
                    printer_send_status VARCHAR(20) DEFAULT 'not_sent',
                    printer_send_time DATETIME,
                    printer_error_message TEXT,
                    printer_response_data TEXT,
                    promotion_code VARCHAR(20),
                    referrer_user_id VARCHAR(50),
                    franchisee_id INTEGER,
                    franchisee_deduction FLOAT DEFAULT 0.0,
                    product_type VARCHAR(20),
                    need_confirmation BOOLEAN DEFAULT 0,
                    franchisee_confirmed BOOLEAN DEFAULT 0,
                    franchisee_confirmed_at DATETIME,
                    confirmation_deadline DATETIME,
                    skipped_production BOOLEAN DEFAULT 0,
                    custom_fields TEXT,
                    store_name VARCHAR(100),
                    selfie_machine_id VARCHAR(100),
                    openid VARCHAR(100),
                    order_mode VARCHAR(20),
                    remark TEXT,
                    FOREIGN KEY(merchant_id) REFERENCES user (id),
                    FOREIGN KEY(franchisee_id) REFERENCES franchisee_accounts (id)
                )
            """)
            
            # 复制数据
            cursor.execute("""
                INSERT INTO orders_new 
                SELECT * FROM orders
            """)
            
            # 删除旧表
            cursor.execute("DROP TABLE orders")
            
            # 重命名新表
            cursor.execute("ALTER TABLE orders_new RENAME TO orders")
            
            print("表重建完成，已移除 order_number 的唯一约束")
        else:
            print("未检测到 order_number 的唯一约束，无需修改")
        
        conn.commit()
        print("[成功] 成功移除 order_number 的唯一约束")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[失败] 移除唯一约束失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("移除 orders 表中 order_number 字段的唯一约束")
    print("=" * 60)
    
    success = remove_unique_constraint()
    
    if success:
        print("\n[成功] 迁移完成！")
        sys.exit(0)
    else:
        print("\n[失败] 迁移失败！")
        sys.exit(1)
