#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def debug_tables():
    """调试数据库表结构"""
    
    current_db = 'instance/pet_painting.db'
    backup_db = 'instance/9.29back-pet_painting.db'
    
    print("🔍 调试数据库表结构")
    print("=" * 50)
    
    try:
        # 连接数据库
        current_conn = sqlite3.connect(current_db)
        current_cursor = current_conn.cursor()
        
        backup_conn = sqlite3.connect(backup_db)
        backup_cursor = backup_conn.cursor()
        
        print(f"\n📊 当前数据库表结构:")
        current_cursor.execute("PRAGMA table_info('products');")
        current_products_info = current_cursor.fetchall()
        
        for col in current_products_info:
            print(f"   {col[1]:15} {col[2]:15} {'NOT NULL' if col[3] else ''}")
        
        print(f"\n📊 备份数据库表结构:")
        backup_cursor.execute("PRAGMA table_info('products');")
        backup_products_info = backup_cursor.fetchall()
        
        for col in backup_products_info:
            print(f"   {col[1]:15} {col[2]:15} {'NOT NULL' if col[3] else ''}")
        
        print(f"\n📦 备份中的电子档产品:")
        backup_cursor.execute("SELECT * FROM products WHERE id = 9;")
        result = backup_cursor.fetchone()
        if result:
            print(f"   找到电子档产品: {result}")
        else:
            print(f"   在id=9处未找到电子档产品")
        
        # 尝试查找electronic相关产品
        print(f"\n🔍 查找photo或electronic相关产品:")
        backup_cursor.execute("SELECT id, code, name FROM products WHERE code LIKE '%photo%' OR code LIKE '%electronic%' OR name LIKE '%电子%';")
        results = backup_cursor.fetchall()
        
        for result in results:
            print(f"   🎁 ID:{result[0]} 代码:{result[1]} 名称:{result[2]}")
        
        current_conn.close()
        backup_conn.close()
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")

def main():
    debug_tables()

if __name__ == "__main__":
    main()
