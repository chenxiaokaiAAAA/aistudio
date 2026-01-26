#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面查找订单35
"""

import sqlite3
import os
from datetime import datetime

def find_order_35_comprehensive():
    """全面查找订单35"""
    
    print("🔍 全面查找订单35...")
    print("=" * 60)
    
    # 1. 检查所有数据库文件
    db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    
    for db_file in db_files:
        print(f"\n📁 检查数据库: {db_file}")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 检查是否有order表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
            if cursor.fetchone():
                # 查询订单35
                cursor.execute('SELECT COUNT(*) FROM "order" WHERE id = 35')
                count = cursor.fetchone()[0]
                
                if count > 0:
                    cursor.execute('SELECT * FROM "order" WHERE id = 35')
                    order = cursor.fetchone()
                    print(f"✅ 在 {db_file} 中找到订单35!")
                    print(f"   订单数据: {order}")
                else:
                    print(f"❌ {db_file} 中没有订单35")
                    
                    # 检查最大ID
                    cursor.execute('SELECT MAX(id) FROM "order"')
                    max_id = cursor.fetchone()[0]
                    print(f"   最大订单ID: {max_id}")
                    
                    # 检查订单总数
                    cursor.execute('SELECT COUNT(*) FROM "order"')
                    total = cursor.fetchone()[0]
                    print(f"   订单总数: {total}")
            else:
                print(f"❌ {db_file} 中没有order表")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 检查 {db_file} 失败: {e}")
    
    # 2. 检查应用是否在使用内存数据库
    print(f"\n🔍 检查应用配置...")
    print("应用可能使用了内存数据库或不同的数据库文件")
    
    # 3. 检查是否有其他数据库文件
    print(f"\n🔍 检查其他可能的数据库位置...")
    
    # 检查当前目录下的所有文件
    all_files = os.listdir('.')
    db_like_files = [f for f in all_files if 'db' in f.lower() or f.endswith('.sqlite') or f.endswith('.sqlite3')]
    
    if db_like_files:
        print("找到可能的数据库文件:")
        for file in db_like_files:
            print(f"  - {file}")
    
    # 4. 检查环境变量
    print(f"\n🔍 检查环境变量...")
    import os
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"DATABASE_URL: {database_url}")
    else:
        print("DATABASE_URL: 未设置")

if __name__ == '__main__':
    find_order_35_comprehensive()
