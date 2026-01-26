#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新创建photo_signup表
"""

import sqlite3
import os

def recreate_table():
    """删除并重新创建PhotoSignup表"""
    
    # 数据库路径
    db_path = 'pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 删除现有表
        cursor.execute("DROP TABLE IF EXISTS photo_signup")
        print("✅ 删除现有表")
        
        # 重新创建表（完全按照API预期顺序）
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
        
        print("✅ PhotoSignup表重新创建成功！")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(photo_signup)")
        columns = cursor.fetchall()
        
        print(f"📋 新表结构：{len(columns)} 个字段")
        for column in columns:
            print(f"   - {column[1]} ({column[2]})")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False

if __name__ == "__main__":
    print("🗑️ 重新创建photo_signup表...")
    
    if recreate_table():
        print("🎉 表重新创建完成！现在可以提交报名了。")
    else:
        print("💥 表重新创建失败")
