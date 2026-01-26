#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查找包含8047447的订单
"""

import sqlite3
import json

def find_order_with_8047447():
    """查找包含8047447的订单"""
    try:
        conn = sqlite3.connect('pet_painting.db')
        cursor = conn.cursor()
        
        # 查找包含8047447的订单
        cursor.execute('''
            SELECT id, order_number, external_order_number, status, shipping_info, logistics_info, created_at
            FROM "order" 
            WHERE order_number LIKE ? OR external_order_number LIKE ?
        ''', ('%8047447%', '%8047447%'))
        
        orders = cursor.fetchall()
        
        if orders:
            print('🔍 找到包含8047447的订单:')
            for order in orders:
                print(f'  ID: {order[0]}')
                print(f'  订单号: {order[1]}')
                print(f'  外部订单号: {order[2]}')
                print(f'  状态: {order[3]}')
                print(f'  物流信息(shipping_info): {order[4]}')
                print(f'  物流信息(logistics_info): {order[5]}')
                print(f'  创建时间: {order[6]}')
                print('-' * 40)
        else:
            print('❌ 没有找到包含8047447的订单')
            
            # 查找所有订单号，看看是否有类似的
            cursor.execute('SELECT order_number, external_order_number FROM "order" ORDER BY id DESC LIMIT 10')
            recent_orders = cursor.fetchall()
            
            print('\\n🔍 最近的10个订单号:')
            for order in recent_orders:
                print(f'  订单号: {order[0]}, 外部订单号: {order[1]}')
        
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {str(e)}")

if __name__ == '__main__':
    find_order_with_8047447()
