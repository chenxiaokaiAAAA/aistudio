#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def add_missing_fields_to_order():
    """添加order表缺少的字段"""
    db_file = 'instance/pet_painting.db'
    
    missing_fields = [
        ('franchisee_id', 'INTEGER', '加盟商ID'),
        ('franchisee_deduction', 'FLOAT', '加盟商扣费'),
        ('product_type', 'VARCHAR(50)', '产品类型'),
        ('openid', 'VARCHAR(100)', '用户openid')
    ]
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print("🔧 开始添加order表缺少的字段")
        print("=" * 50)
        
        for field_name, field_type, description in missing_fields:
            try:
                # 检查字段是否已存在
                cursor.execute("PRAGMA table_info('order');")
                columns = cursor.fetchall()
                existing_fields = [col[1] for col in columns]
                
                if field_name in existing_fields:
                    print(f"   ✅ {field_name} - 已存在")
                    continue
                
                # 添加字段
                sql = f"ALTER TABLE 'order' ADD COLUMN {field_name} {field_type};"
                cursor.execute(sql)
                conn.commit()
                
                print(f"   ✅ {field_name} - 添加成功 ({description})")
                
            except Exception as e:
                print(f"   ❌ {field_name} - 添加失败: {e}")
        
        # 验证结果
        print(f"\n🔍 验证表结构:")
        cursor.execute("PRAGMA table_info('order');")
        columns = cursor.fetchall()
        print(f"   order表现在有 {len(columns)} 个字段")
        
        # 检查关键字段
        field_names = [col[1] for col in columns] 
        critical_fields = ['franchisee_id', 'franchisee_deduction', 'product_type', 'openid']
        for field in critical_fields:
            if field in field_names:
                print(f"   ✅ {field}")
            else:
                print(f"   ❌ {field} - 仍然缺失")
        
        conn.close()
        print(f"\n🎉 order表字段修复完成!")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def main():
    success = add_missing_fields_to_order()
    
    if success:
        print(f"\n💡 建议现在重启服务器，让修改生效")

if __name__ == "__main__":
    main()
