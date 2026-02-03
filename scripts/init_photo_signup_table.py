#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化宠物摄影报名表
如果表不存在，自动创建
"""

import sqlite3
import os

def init_photo_signup_table():
    """初始化PhotoSignup表"""
    
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
            print("PhotoSignup表不存在，正在创建...")
            
            # 创建PhotoSignup表
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
            
            # 插入一些测试数据
            cursor.execute("""
                INSERT INTO photo_signup (
                    name, phone, pet_breed, pet_weight, pet_age, 
                    pet_character, available_date, additional_notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                '测试用户', '13800138000', '金毛', '大型犬', '2岁',
                '温顺活泼', '周末', '这是一个测试数据', 'pending'
            ))
            
            print("✅ 测试数据插入成功！")
            
        else:
            print("✅ PhotoSignup表已存在")
            
        conn.commit()
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(photo_signup)")
        columns = cursor.fetchall()
        
        print(f"📋 表结构：{len(columns)} 个字段")
        for column in columns:
            print(f"   - {column[1]} ({column[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌<｜tool▁sep｜>数据库操作失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 初始化宠物摄影报名数据表...")
    
    if init_photo_signup_table():
        print("🎉 初始化完成！现在可以访问管理后台了。")
        print("📱 访问地址: https://photogooo/admin/photo-signups")
    else:
        print("💥 初始化失败，请检查数据库连接。")
