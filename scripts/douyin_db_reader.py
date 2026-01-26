#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音小店数据库直接连接（需要特殊权限）
"""

import pymysql
import sqlite3
import json
from datetime import datetime
from test_server import db, Order

class DouyinDatabaseReader:
    """抖音小店数据库读取器"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        try:
            if self.db_config['type'] == 'mysql':
                self.connection = pymysql.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['database'],
                    charset='utf8mb4'
                )
            elif self.db_config['type'] == 'sqlite':
                self.connection = sqlite3.connect(self.db_config['path'])
            
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def get_orders_from_db(self, limit=100):
        """从数据库获取订单"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            # 抖音小店订单表结构（需要根据实际情况调整）
            if self.db_config['type'] == 'mysql':
                query = """
                    SELECT 
                        order_id, buyer_name, buyer_phone, product_name,
                        product_size, total_amount, status, create_time,
                        receiver_name, shipping_address, remark, image_url
                    FROM douyin_orders 
                    WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    ORDER BY create_time DESC
                    LIMIT %s
                """
            else:  # SQLite
                query = """
                    SELECT 
                        order_id, buyer_name, buyer_phone, product_name,
                        product_size, total_amount, status, create_time,
                        receiver_name, shipping_address, remark, image_url
                    FROM douyin_orders 
                    WHERE create_time >= datetime('now', '-7 days')
                    ORDER BY create_time DESC
                    LIMIT ?
                """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (limit,))
            orders = cursor.fetchall()
            
            print(f"从数据库获取到 {len(orders)} 个订单")
            return orders
            
        except Exception as e:
            print(f"数据库查询失败: {e}")
            return []
    
    def sync_orders_to_system(self, orders):
        """同步订单到系统"""
        synced_count = 0
        
        for order_data in orders:
            try:
                # 解析订单数据
                order_id, buyer_name, buyer_phone, product_name, product_size, \
                total_amount, status, create_time, receiver_name, shipping_address, \
                remark, image_url = order_data
                
                # 检查订单是否已存在
                existing_order = Order.query.filter_by(
                    external_order_number=str(order_id)
                ).first()
                
                if existing_order:
                    print(f"订单已存在: {order_id}")
                    continue
                
                # 创建新订单
                order = Order(
                    order_number=f"DY{order_id}",
                    customer_name=buyer_name or '',
                    customer_phone=buyer_phone or '',
                    size=product_size or '',
                    style_name='',
                    product_name=product_name or '',
                    original_image=image_url or '',
                    status=self.map_status(status),
                    shipping_info=json.dumps({
                        'receiver': receiver_name or '',
                        'address': shipping_address or '',
                        'remark': remark or ''
                    }),
                    price=float(total_amount or 0),
                    external_platform='douyin',
                    external_order_number=str(order_id),
                    source_type='douyin',
                    created_at=create_time if create_time else datetime.now()
                )
                
                db.session.add(order)
                db.session.commit()
                synced_count += 1
                
                print(f"订单同步成功: {order_id}")
                
            except Exception as e:
                print(f"同步订单失败: {e}")
                db.session.rollback()
        
        print(f"同步完成: {synced_count} 个订单")
        return synced_count
    
    def map_status(self, douyin_status):
        """映射订单状态"""
        status_mapping = {
            'UNPAID': 'pending',
            'PAID': 'processing',
            'SHIPPED': 'shipped', 
            'COMPLETED': 'completed',
            'CANCELLED': 'cancelled'
        }
        return status_mapping.get(douyin_status, 'pending')
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

# 配置示例
DOUYIN_DB_CONFIG = {
    'type': 'mysql',  # 或 'sqlite'
    'host': 'localhost',
    'port': 3306,
    'user': 'douyin_user',
    'password': 'douyin_password',
    'database': 'douyin_shop',
    # SQLite配置
    'path': '/path/to/douyin.db'
}

def sync_douyin_orders_from_database():
    """从数据库同步抖音订单"""
    db_reader = DouyinDatabaseReader(DOUYIN_DB_CONFIG)
    
    try:
        # 获取订单数据
        orders = db_reader.get_orders_from_db()
        
        if orders:
            # 同步到系统
            synced_count = db_reader.sync_orders_to_system(orders)
            return synced_count
        else:
            print("没有获取到订单数据")
            return 0
    finally:
        db_reader.close()

if __name__ == "__main__":
    print("抖音小店数据库同步测试...")
    count = sync_douyin_orders_from_database()
    print(f"同步了 {count} 个订单")




