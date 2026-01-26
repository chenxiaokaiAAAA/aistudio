#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加missing字段
"""

import sqlite3

def add_missing_field():
    """添加additional_notes字段"""
    
    try:
        conn = sqlite3.connect('pet_painting.db')
        cursor = conn.cursor()
        
        # 添加additional_notes字段
        try:
            cursor.execute("ALTER TABLE photo_signup ADD COLUMN additional_notes VARCHAR(500)")
            print("✅ additional_notes字段添加成功")
        except Exception as e:
            print(f"⚠️ additional_notes字段可能已存在: {e}")
        
        # 验证最终表结构
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
        
if __name__ == "__main__":
    print("➕ 添加missing字段...")
    add_missing_field()
    print("✅ 字段添加完成！")
