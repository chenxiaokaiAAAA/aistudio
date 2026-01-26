# add_order_store_machine_fields.py
# 数据库迁移脚本：为订单表添加门店信息和自拍机信息字段

import sqlite3
import os
from datetime import datetime

def add_order_fields():
    """为order表添加新字段"""
    
    # 可能的数据库路径（按优先级排序）
    possible_db_paths = [
        'pet_painting.db',
        'instance/moeart.db',
        'instance/pet_painting.db'
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            print(f"✅ 找到数据库文件: {db_path}")
            break
    
    if not db_path:
        print("❌ 未找到数据库文件，请检查以下路径:")
        for path in possible_db_paths:
            print(f"   - {path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 首先查找订单表名（可能的大小写变体）
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%order%'")
        order_tables = cursor.fetchall()
        
        if not order_tables:
            # 如果没找到，尝试查找所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = cursor.fetchall()
            print("数据库中的所有表:")
            for table in all_tables:
                print(f"  - {table[0]}")
            print("\n❌ 未找到订单表（包含'order'的表）")
            return False
        
        # 使用找到的第一个订单表
        order_table_name = order_tables[0][0]
        print(f"✅ 找到订单表: {order_table_name}")
        
        # 检查字段是否已存在（尝试不同的引用方式）
        try:
            cursor.execute(f"PRAGMA table_info([{order_table_name}])")
        except:
            try:
                cursor.execute(f'PRAGMA table_info("{order_table_name}")')
            except:
                cursor.execute(f"PRAGMA table_info({order_table_name})")
        
        columns = [column[1] for column in cursor.fetchall()]
        print(f"当前表包含 {len(columns)} 个字段")
        
        # 需要添加的字段
        fields_to_add = {
            'store_name': 'VARCHAR(100)',  # 门店名称
            'selfie_machine_id': 'VARCHAR(100)'  # 自拍机序列号
        }
        
        added_fields = []
        
        for field_name, field_type in fields_to_add.items():
            if field_name not in columns:
                try:
                    # 添加字段（尝试不同的引用方式）
                    try:
                        alter_sql = f"ALTER TABLE [{order_table_name}] ADD COLUMN {field_name} {field_type}"
                        cursor.execute(alter_sql)
                    except:
                        try:
                            alter_sql = f'ALTER TABLE "{order_table_name}" ADD COLUMN {field_name} {field_type}'
                            cursor.execute(alter_sql)
                        except:
                            alter_sql = f"ALTER TABLE {order_table_name} ADD COLUMN {field_name} {field_type}"
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
    print("订单表字段添加脚本")
    print("=" * 50)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = add_order_fields()
    
    print()
    if success:
        print("✅ 脚本执行完成")
    else:
        print("❌ 脚本执行失败")
    
    print("=" * 50)
