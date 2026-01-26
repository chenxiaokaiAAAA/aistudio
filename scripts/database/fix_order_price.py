#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复订单价格
"""

import sqlite3

def fix_order_price():
    """修复订单价格"""
    
    print("🔧 修复订单 PET202509181014143793 的价格...")
    print("=" * 60)
    
    db_file = 'instance/pet_painting.db'
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 查找对应的尺寸配置
    cursor.execute('SELECT * FROM product_sizes WHERE size_name = ?', ('30x30cm肌理画框',))
    size_config = cursor.fetchone()
    
    if size_config:
        print(f"✅ 找到尺寸配置:")
        print(f"   ID: {size_config[0]}")
        print(f"   产品ID: {size_config[1]}")
        print(f"   尺寸名称: {size_config[2]}")
        print(f"   价格: {size_config[3]}")
        print(f"   打印机产品ID: {size_config[4]}")
        
        # 更新订单价格
        cursor.execute('UPDATE "order" SET price = ?, product_name = ? WHERE order_number = ?', 
                      (size_config[3], size_config[2], 'PET202509181014143793'))
        
        conn.commit()
        print(f"\\n✅ 订单价格已更新为: {size_config[3]}")
        
        # 验证更新
        cursor.execute('SELECT order_number, size, product_name, price FROM "order" WHERE order_number = ?', 
                      ('PET202509181014143793',))
        order = cursor.fetchone()
        
        if order:
            print(f"\\n📋 更新后的订单信息:")
            print(f"   订单号: {order[0]}")
            print(f"   尺寸: {order[1]}")
            print(f"   产品名称: {order[2]}")
            print(f"   价格: {order[3]}")
        
    else:
        print("❌ 未找到对应的尺寸配置")
    
    conn.close()

if __name__ == '__main__':
    fix_order_price()
