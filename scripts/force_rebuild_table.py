#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制重建photo_signup表
"""

import sqlite3

def force_rebuild_table():
    """强制重建PhotoSignup表"""
    
    try:
        conn = sqlite3.connect('pet_painting.db')
        cursor = conn.cursor()
        
        print("🗑️ 删除现有表...")
        cursor.execute("DROP TABLE IF EXISTS photo_signup")
        
        print("🔨 创建新表...")
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
        
        print("✅ 新表创建成功！")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(photo_signup)")
        columns = cursor.fetchall()
        
        print(f"📋 新表结构：{len(columns)} 个字段")
        for column in columns:
            print(f"   - {column[1]} ({column[2]})")
        
        # 插入测试数据
        cursor.execute("""
            INSERT INTO photo_signup (
                name, phone, pet_breed, pet_weight, pet_age, pet_character,
                available_date, additional_notes, pet_images, user_id,
                referrer_user_id, referrer_promotion_code, source, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '测试用户', '13800138000', '金毛', '1-5kg (小型)', '幼体 (0-6个月)',
            '温顺活泼', '2025-09-30', '测试备注', 
            '[{"url": "https://example.com/test.jpg", "filename": "test.jpg"}]',
            'TEST_USER', '', '', 'test', 'pending'
        ))
        
        print("✅ 测试数据插入成功！")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 强制重建photo_signup表...")
    
    if force_rebuild_table():
        print("🎉 表重建完成！现在应该可以正常提交报名了。")
    else:
        print("💥 表重建失败")
