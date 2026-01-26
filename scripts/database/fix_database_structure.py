#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def fix_database_structure():
    """修复数据库表结构"""
    db_path = os.path.join('instance', 'pet_painting.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查franchisee_recharges表结构
        cursor.execute('PRAGMA table_info(franchisee_recharges)')
        columns = cursor.fetchall()
        print("修复前的franchisee_recharges表结构:")
        for col in columns:
            print(f"  {col}")
        
        # 检查是否有错误的字段
        has_visitor_user_id = any(col[1] == 'visitor_user_id' for col in columns)
        has_visit_time = any(col[1] == 'visit_time' for col in columns)
        has_create_time = any(col[1] == 'create_time' for col in columns)
        
        if has_visitor_user_id or has_visit_time or has_create_time:
            print("\n发现错误字段，开始修复...")
            
            # 创建新表结构
            cursor.execute('''
                CREATE TABLE franchisee_recharges_new (
                    id INTEGER PRIMARY KEY,
                    franchisee_id INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    admin_user_id INTEGER NOT NULL,
                    recharge_type VARCHAR(20) DEFAULT 'manual',
                    description TEXT,
                    created_at DATETIME,
                    FOREIGN KEY (franchisee_id) REFERENCES franchisee_accounts (id),
                    FOREIGN KEY (admin_user_id) REFERENCES user (id)
                )
            ''')
            
            # 复制数据（只复制正确的字段）
            cursor.execute('''
                INSERT INTO franchisee_recharges_new 
                (id, franchisee_id, amount, admin_user_id, recharge_type, description, created_at)
                SELECT id, franchisee_id, amount, admin_user_id, recharge_type, description, created_at
                FROM franchisee_recharges
            ''')
            
            # 删除旧表
            cursor.execute('DROP TABLE franchisee_recharges')
            
            # 重命名新表
            cursor.execute('ALTER TABLE franchisee_recharges_new RENAME TO franchisee_recharges')
            
            conn.commit()
            print("✅ 表结构修复完成")
        else:
            print("✅ 表结构正确，无需修复")
        
        # 验证修复结果
        cursor.execute('PRAGMA table_info(franchisee_recharges)')
        columns = cursor.fetchall()
        print("\n修复后的franchisee_recharges表结构:")
        for col in columns:
            print(f"  {col}")
        
        conn.close()
        
    except Exception as e:
        print(f"修复失败: {e}")

if __name__ == '__main__':
    fix_database_structure()






