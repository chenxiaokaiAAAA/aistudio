#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
排查物流回调问题
"""

import sqlite3
import json
from datetime import datetime

def investigate_logistics_issue():
    """排查物流回调问题"""
    
    print("🔍 排查物流回调问题...")
    print("=" * 60)
    
    db_file = 'instance/pet_painting.db'
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 1. 检查订单35的完整信息
    print("📋 订单35 (PET20250917192632FC98) 完整信息:")
    cursor.execute('SELECT * FROM "order" WHERE id = 35')
    order = cursor.fetchone()
    
    if order:
        print(f"   ID: {order[0]}")
        print(f"   订单号: {order[1]}")
        print(f"   客户姓名: {order[2]}")
        print(f"   客户电话: {order[3]}")
        print(f"   尺寸: {order[4]}")
        print(f"   风格名称: {order[5]}")
        print(f"   产品名称: {order[6]}")
        print(f"   原始图片: {order[7]}")
        print(f"   效果图: {order[8]}")
        print(f"   高清图: {order[9]}")
        print(f"   状态: {order[10]}")
        print(f"   收货信息: {order[11]}")
        print(f"   商家ID: {order[12]}")
        print(f"   创建时间: {order[13]}")
        print(f"   完成时间: {order[14]}")
        print(f"   佣金: {order[15]}")
        print(f"   价格: {order[16]}")
        print(f"   外部平台: {order[17]}")
        print(f"   外部订单号: {order[18]}")
        print(f"   来源类型: {order[19]}")
        print(f"   打印机发送状态: {order[20]}")
        print(f"   打印机发送时间: {order[21]}")
        print(f"   打印机错误信息: {order[22]}")
        print(f"   打印机响应数据: {order[23]}")
        print(f"   客户地址: {order[24]}")
        print(f"   物流信息: {order[25]}")
        print(f"   更新时间: {order[26] if len(order) > 26 else 'N/A'}")
    
    # 2. 检查数据库文件的修改时间
    import os
    stat = os.stat(db_file)
    print(f"\\n📁 数据库文件信息:")
    print(f"   文件路径: {db_file}")
    print(f"   文件大小: {stat.st_size} bytes")
    print(f"   最后修改时间: {datetime.fromtimestamp(stat.st_mtime)}")
    
    # 3. 检查所有订单的修改时间
    print(f"\\n📅 最近修改的订单:")
    cursor.execute('SELECT id, order_number, created_at, completed_at FROM "order" ORDER BY id DESC LIMIT 10')
    orders = cursor.fetchall()
    
    for order in orders:
        print(f"   ID: {order[0]}, 订单号: {order[1]}")
        print(f"      创建时间: {order[2]}")
        print(f"      完成时间: {order[3]}")
        print()
    
    # 4. 检查是否有物流信息的订单
    print(f"\\n📦 有物流信息的订单:")
    cursor.execute('SELECT id, order_number, shipping_info, logistics_info FROM "order" WHERE shipping_info IS NOT NULL AND shipping_info != "" OR logistics_info IS NOT NULL AND logistics_info != ""')
    logistics_orders = cursor.fetchall()
    
    for order in logistics_orders:
        print(f"   ID: {order[0]}, 订单号: {order[1]}")
        print(f"      收货信息: {order[2]}")
        print(f"      物流信息: {order[3]}")
        print()
    
    # 5. 检查订单35的图片
    print(f"\\n📷 订单35的图片:")
    cursor.execute('SELECT * FROM order_image WHERE order_id = 35')
    images = cursor.fetchall()
    
    for img in images:
        print(f"   ID: {img[0]}, 订单ID: {img[1]}, 路径: {img[2]}, 创建时间: {img[3]}")
    
    conn.close()

if __name__ == '__main__':
    investigate_logistics_issue()
