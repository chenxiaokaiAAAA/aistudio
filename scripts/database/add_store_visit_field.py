#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def add_store_visit_time_field():
    """添加店铺到达时间字段"""
    db_file = 'instance/pet_painting.db'
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("🔧 添加店铺到达时间字段到photo_signup表")
        print("=" * 50)
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info('photo_signup');")
        columns = cursor.fetchall()
        existing_fields = [col[1] for col in columns]
        
        print(f"📊 当前字段数: {len(columns)}")
        
        # 添加新字段
        new_fields = [
            ('store_visit_time', 'VARCHAR(50)', '到店时间'),
            ('contact_no_answer', 'BOOLEAN DEFAULT 0', '电话未打通标记'),
            ('contact_success', 'BOOLEAN DEFAULT 0', '电话已打通标记')
        ]
        
        for field_name, field_type, description in new_fields:
            if field_name in existing_fields:
                print(f"   ✅ {field_name} - 已存在")
                continue
            
            try:
                sql = f"ALTER TABLE photo_signup ADD COLUMN {field_name} {field_type};"
                cursor.execute(sql)
                conn.commit()
                print(f"   ✅ {field_name} - 添加成功 ({description})")
            except Exception as e:
                print(f"   ❌ {field_name} - 添加失败: {e}")
        
        # 验证结果
        cursor.execute("PRAGMA table_info('photo_signup');")
        new_columns = cursor.fetchall()
        print(f"\n📊 更新后字段数: {len(new_columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return False

def main():
    success = add_store_visit_time_field()
    
    if success:
        print(f"\n🎉 字段添加完成!")
        print(f"💡 现在可以支持到店时间记录")

if __name__ == "__main__":
    main()
