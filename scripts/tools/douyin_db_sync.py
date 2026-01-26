#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音数据库直接同步功能
"""

import sqlite3
import pymysql
import json
from datetime import datetime
from test_server import db, Order

class DouyinDatabaseSync:
    """抖音数据库同步类"""
    
    def __init__(self, douyin_db_config):
        self.douyin_db_config = douyin_db_config
        self.connection = None
    
    def connect_douyin_db(self):
        """连接抖音数据库"""
        try:
            if self.douyin_db_config['type'] == 'mysql':
                self.connection = pymysql.connect(
                    host=self.douyin_db_config['host'],
                    port=self.douyin_db_config['port'],
                    user=self.douyin_db_config['user'],
                    password=self.douyin_db_config['password'],
                    database=self.douyin_db_config['database'],
                    charset='utf8mb4'
                )
            elif self.douyin_db_config['type'] == 'sqlite':
                self.connection = sqlite3.connect(self.douyin_db_config['path'])
            
            print("抖音数据库连接成功")
            return True
        except Exception as e:
            print(f"连接抖音数据库失败: {e}")
            return False
    
    def sync_orders_from_douyin_db(self):
        """从抖音数据库同步订单"""
        try:
            if not self.connection:
                if not self.connect_douyin_db():
                    return False
            
            # 查询抖音订单表
            if self.douyin_db_config['type'] == 'mysql':
                query = """
                    SELECT order_id, buyer_name, buyer_phone, product_name, 
                           product_size, total_amount, status, create_time,
                           receiver_name, shipping_address, remark, image_url
                    FROM douyin_orders 
                    WHERE create_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                    ORDER BY create_time DESC
                """
            else:  # SQLite
                query = """
                    SELECT order_id, buyer_name, buyer_phone, product_name, 
                           product_size, total_amount, status, create_time,
                           receiver_name, shipping_address, remark, image_url
                    FROM douyin_orders 
                    WHERE create_time >= datetime('now', '-1 day')
                    ORDER BY create_time DESC
                """
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            douyin_orders = cursor.fetchall()
            
            synced_count = 0
            for order_data in douyin_orders:
                if self.sync_single_order_from_db(order_data):
                    synced_count += 1
            
            print(f"从抖音数据库同步订单完成: {synced_count}/{len(douyin_orders)}")
            return True
            
        except Exception as e:
            print(f"从抖音数据库同步订单失败: {e}")
            return False
    
    def sync_single_order_from_db(self, order_data):
        """同步单个订单从数据库"""
        try:
            # 解析订单数据
            if self.douyin_db_config['type'] == 'mysql':
                order_id, buyer_name, buyer_phone, product_name, product_size, \
                total_amount, status, create_time, receiver_name, shipping_address, \
                remark, image_url = order_data
            else:  # SQLite
                order_id, buyer_name, buyer_phone, product_name, product_size, \
                total_amount, status, create_time, receiver_name, shipping_address, \
                remark, image_url = order_data
            
            # 检查订单是否已存在
            existing_order = Order.query.filter_by(
                external_order_number=str(order_id)
            ).first()
            
            if existing_order:
                print(f"订单已存在: {order_id}")
                return True
            
            # 创建新订单
            order = Order(
                order_number=f"DY{order_id}",
                customer_name=buyer_name or '',
                customer_phone=buyer_phone or '',
                size=product_size or '',
                style_name='',  # 抖音订单可能没有风格信息
                product_name=product_name or '',
                original_image=image_url or '',
                status=self.map_douyin_status(status),
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
            
            print(f"抖音订单同步成功: {order_id}")
            return True
            
        except Exception as e:
            print(f"同步单个订单失败: {e}")
            db.session.rollback()
            return False
    
    def map_douyin_status(self, douyin_status):
        """映射抖音订单状态到系统状态"""
        status_mapping = {
            'pending': 'pending',
            'paid': 'processing',
            'shipped': 'shipped',
            'completed': 'completed',
            'cancelled': 'cancelled',
            'refunded': 'cancelled'
        }
        return status_mapping.get(douyin_status, 'pending')
    
    def close_connection(self):
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
    """从抖音数据库同步订单的主函数"""
    sync_client = DouyinDatabaseSync(DOUYIN_DB_CONFIG)
    
    try:
        if sync_client.sync_orders_from_douyin_db():
            print("抖音数据库同步成功")
            return True
        else:
            print("抖音数据库同步失败")
            return False
    finally:
        sync_client.close_connection()

# Flask路由
def create_douyin_db_sync_routes(app):
    """创建抖音数据库同步路由"""
    
    @app.route('/api/douyin/sync/database', methods=['POST'])
    def sync_douyin_database():
        """手动同步抖音数据库"""
        try:
            if sync_douyin_orders_from_database():
                return jsonify({
                    'success': True,
                    'message': '抖音数据库同步成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '抖音数据库同步失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'同步异常: {str(e)}'
            }), 500

if __name__ == "__main__":
    print("抖音数据库同步功能测试...")
    if sync_douyin_orders_from_database():
        print("同步测试成功")
    else:
        print("同步测试失败")




