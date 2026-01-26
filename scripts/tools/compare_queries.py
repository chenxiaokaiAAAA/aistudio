#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
import sqlite3

def compare_orm_vs_sql():
    """比较ORM查询和SQL查询的结果"""
    with app.app_context():
        print('=== 比较ORM查询和SQL查询的结果 ===')
        
        # ORM查询
        print('\n1. ORM查询订单1:')
        order_orm = Order.query.get(1)
        if order_orm:
            print(f'   ORM - 订单ID: {order_orm.id}')
            print(f'   ORM - 订单号: {order_orm.order_number}')
            print(f'   ORM - 尺寸字段: "{order_orm.size}"')
            print(f'   ORM - 产品名称: {order_orm.product_name}')
        
        # SQL查询
        print('\n2. SQL查询订单1:')
        conn = sqlite3.connect('pet_painting.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, order_number, size, product_name FROM "order" WHERE id = 1')
        order_sql = cursor.fetchone()
        if order_sql:
            print(f'   SQL - 订单ID: {order_sql[0]}')
            print(f'   SQL - 订单号: {order_sql[1]}')
            print(f'   SQL - 尺寸字段: "{order_sql[2]}"')
            print(f'   SQL - 产品名称: {order_sql[3]}')
        conn.close()
        
        # 检查数据库文件
        print('\n3. 检查数据库文件:')
        import os
        main_db = 'pet_painting.db'
        instance_db = 'instance/pet_painting.db'
        
        if os.path.exists(main_db):
            print(f'   主数据库存在: {main_db}')
        if os.path.exists(instance_db):
            print(f'   instance数据库存在: {instance_db}')

if __name__ == "__main__":
    compare_orm_vs_sql()
