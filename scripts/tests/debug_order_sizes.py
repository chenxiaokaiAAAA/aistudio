#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_order_sizes():
    """检查订单中的尺寸字段"""
    conn = sqlite3.connect('pet_painting.db')
    cursor = conn.cursor()

    print('=== 检查订单表中的size字段 ===')
    cursor.execute('SELECT id, order_number, size, product_name FROM "order" LIMIT 5')
    orders = cursor.fetchall()
    for order in orders:
        print(f'订单ID: {order[0]}, 订单号: {order[1]}, 尺寸字段: "{order[2]}", 产品: {order[3]}')

    print('\n=== 检查ProductSize表中的实际数据 ===')
    cursor.execute('SELECT id, product_id, size_name, price, printer_product_id FROM product_sizes ORDER BY id')
    sizes = cursor.fetchall()
    for size in sizes:
        print(f'ID: {size[0]}, 产品ID: {size[1]}, 尺寸: {size[2]}, 价格: {size[3]}, 冲印ID: {size[4]}')

    conn.close()

if __name__ == "__main__":
    check_order_sizes()
