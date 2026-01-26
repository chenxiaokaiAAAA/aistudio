#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复photo_signup表结构
"""

import sqlite3
import os

def fix_table_structure():
    """修复PhotoSignup表结构"""
    
    # 数据库路径
    db_path = 'pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='photo_signup'
        """)
        
        if cursor.fetchone() is None:
            print("❌ PhotoSignup表不存在，正在创建...")
            create_table(cursor)
        else:
            print("✅ PhotoSignup表存在，检查字段...")
            
            # 检查是否缺少某些字段
            cursor.execute("PRAGMA table_info(photo_signup)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            missing_fields = []
            required_fields = [
                'id', 'name', 'phone', 'pet_breed', 'pet_weight', 'pet_age',
                'pet_character', 'available_date', 'additional_notes', 'pet_images',
                'user_id', 'referrer_user_id', 'referrer_promotion_code', 'source',
                'status', 'notes', 'submit_time', 'contact_time', 'schedule_time',
                'complete_time'
            ]
            
            for field in required_fields:
                if field not in column_names:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少字段: {missing_fields}")
                add_missing_fields(cursor, missing_fields)
            else:
                print("✅ 所有字段都存在")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(photo_signup)")
        columns = cursor.fetchall()
        
        print(f"📋 最终表结构：{len(columns)} 个字段")
        for column in columns:
            print(f"   - {column[1]} ({column[2]})")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False

def create_table(cursor):
    """创建完整的PhotoSignup表"""
    cursor.execute("""
        CREATE TABLE photo_signup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            pet_breed VARCHAR(50) NOT NULL,
            pet_weight VARCHAR(50) NOT NULL,
            pet_age VARCHAR(50) NOT NULL,
            pet_character VARCHAR(500),
            available_date VARCHAR(50),
            additional_notes VARCHAR(500),
            pet_images TEXT,
            user_id VARCHAR(100),
            referrer_user_id VARCHAR(100),
            referrer_promotion_code VARCHAR(50),
            source VARCHAR(50) DEFAULT 'miniprogram_carousel',
            status VARCHAR(20) DEFAULT 'pending',
            notes VARCHAR(1000),
            submit_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            contact_time DATETIME,
            schedule_time DATETIME,
            complete_time DATETIME
        )
    """)
    print("✅ PhotoSignup表创建成功！")

def add_missing_fields(cursor, missing_fields):
    """添加缺少的字段"""
    for field in missing_fields:
        try:
            if field == 'pet_images':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN pet_images TEXT")
            elif field == 'additional_notes':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN additional_notes VARCHAR(500)")
            elif field == 'pet_character':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN pet_character VARCHAR(500)")
            elif field == 'available_date':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN available_date VARCHAR(50)")
            elif field == 'user_id':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN user_id VARCHAR(100)")
            elif field == 'referrer_user_id':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN referrer_user_id VARCHAR(100)")
            elif field == 'referrer_promotion_code':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN referrer_promotion_code VARCHAR(50)")
            elif field == 'source':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN source VARCHAR(50)")
            elif field == 'status':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN status VARCHAR(20)")
            elif field == 'notes':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN notes VARCHAR(1000)")
            elif field == 'submit_time':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN submit_time DATETIME")
            elif field == 'contact_time':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN contact_time DATETIME")
            elif field == 'schedule_time':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN schedule_time DATETIME")
            elif field == 'complete_time':
                cursor.execute("ALTER TABLE photo_signup ADD COLUMN complete_time DATETIME")
            
            print(f"✅ 添加字段成功: {field}")
        except Exception as e:
            print(f"⚠️ 添加字段失败 {field}: {e}")

if __name__ == "__main__":
    print("🔧 修复photo_signup表结构...")
    
    if fix_table_structure():
        print("🎉 表结构修复完成！")
    else:
        print("💥 表结构修复失败")
