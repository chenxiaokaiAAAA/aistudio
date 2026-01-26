#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 photo_signup 表的 pet_weight 和 pet_age 字段从 nullable=False 改为 nullable=True
"""

import sqlite3
import os
from datetime import datetime

def migrate_photo_signup_fields():
    """迁移 photo_signup 表的 pet_weight 和 pet_age 字段"""
    
    # 数据库路径
    db_files = [
        'instance/pet_painting.db',
        'pet_painting.db'
    ]
    
    db_path = None
    for path in db_files:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 未找到数据库文件")
        return False
    
    print(f"📂 找到数据库文件: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='photo_signup'")
        if not cursor.fetchone():
            print("❌ photo_signup 表不存在，无需迁移")
            return False
        
        # 获取现有数据
        cursor.execute("SELECT * FROM photo_signup")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        
        print(f"📊 找到 {len(rows)} 条现有记录")
        
        # 备份表
        backup_table_name = f"photo_signup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE TABLE {backup_table_name} AS SELECT * FROM photo_signup")
        print(f"✅ 创建备份表: {backup_table_name}")
        
        # 创建新表结构（pet_weight 和 pet_age 允许为 NULL）
        cursor.execute("DROP TABLE photo_signup")
        
        new_table_sql = """
        CREATE TABLE photo_signup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            pet_breed VARCHAR(50) NOT NULL,
            pet_weight VARCHAR(50),
            pet_age VARCHAR(50),
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
            contact_no_answer BOOLEAN DEFAULT 0,
            contact_success BOOLEAN DEFAULT 0,
            submit_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            contact_time DATETIME,
            schedule_time DATETIME,
            store_visit_time VARCHAR(50),
            complete_time DATETIME
        )
        """
        
        cursor.execute(new_table_sql)
        print("✅ 创建新表结构")
        
        # 恢复数据
        if rows:
            # 构建插入语句
            placeholders = ', '.join(['?' for _ in column_names])
            insert_sql = f"INSERT INTO photo_signup ({', '.join(column_names)}) VALUES ({placeholders})"
            
            for row in rows:
                cursor.execute(insert_sql, row)
            
            print(f"✅ 恢复 {len(rows)} 条数据")
        
        conn.commit()
        conn.close()
        
        print(f"✅ 迁移完成！pet_weight 和 pet_age 字段现在可以为 NULL")
        print(f"📦 备份表: {backup_table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False

if __name__ == '__main__':
    print("开始迁移 photo_signup 表...")
    migrate_photo_signup_fields()
    print("迁移完成")



