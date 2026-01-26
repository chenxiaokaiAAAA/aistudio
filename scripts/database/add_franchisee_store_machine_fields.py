# add_franchisee_store_machine_fields.py
# 数据库迁移脚本：为加盟商账户表添加门店信息和自拍机信息字段

import sqlite3
import os
from datetime import datetime

def add_franchisee_fields():
    """为franchisee_accounts表添加新字段"""
    
    # 数据库路径
    db_path = 'pet_painting.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(franchisee_accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 需要添加的字段
        fields_to_add = {
            'store_name': 'TEXT',  # 门店名称
            'machine_name': 'TEXT',  # 自拍机名称
            'machine_serial_number': 'TEXT'  # 自拍机序列号
        }
        
        added_fields = []
        
        for field_name, field_type in fields_to_add.items():
            if field_name not in columns:
                try:
                    # 添加字段
                    alter_sql = f"ALTER TABLE franchisee_accounts ADD COLUMN {field_name} {field_type}"
                    cursor.execute(alter_sql)
                    added_fields.append(field_name)
                    print(f"✅ 已添加字段: {field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️  字段 {field_name} 已存在，跳过")
                    else:
                        print(f"❌ 添加字段 {field_name} 失败: {e}")
            else:
                print(f"ℹ️  字段 {field_name} 已存在，跳过")
        
        conn.commit()
        conn.close()
        
        if added_fields:
            print(f"\n✅ 成功添加 {len(added_fields)} 个字段: {', '.join(added_fields)}")
            return True
        else:
            print("\nℹ️  所有字段已存在，无需添加")
            return True
            
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("加盟商账户表字段添加脚本")
    print("=" * 50)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = add_franchisee_fields()
    
    print()
    if success:
        print("✅ 脚本执行完成")
    else:
        print("❌ 脚本执行失败")
    
    print("=" * 50)
