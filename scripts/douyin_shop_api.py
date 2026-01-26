#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音小店后台API直接读取
"""

import requests
import json
from datetime import datetime, timedelta
from test_server import db, Order

class DouyinShopAPI:
    """抖音小店API客户端"""
    
    def __init__(self):
        # 这些信息需要从抖音小店后台获取
        self.shop_id = "your_shop_id"  # 店铺ID
        self.access_token = "your_access_token"  # 访问令牌
        self.base_url = "https://fxg.jinritemai.com"  # 抖音小店API地址
        
    def get_orders_from_api(self, start_time=None, end_time=None):
        """从API获取订单数据"""
        try:
            if not start_time:
                start_time = datetime.now() - timedelta(days=7)
            if not end_time:
                end_time = datetime.now()
            
            url = f"{self.base_url}/api/order/list"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'shop_id': self.shop_id,
                'start_time': int(start_time.timestamp()),
                'end_time': int(end_time.timestamp()),
                'page': 1,
                'page_size': 100
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            result = response.json()
            
            if result.get('code') == 0:
                orders = result.get('data', {}).get('orders', [])
                print(f"从API获取到 {len(orders)} 个订单")
                return orders
            else:
                print(f"API调用失败: {result.get('message')}")
                return []
                
        except Exception as e:
            print(f"API调用异常: {e}")
            return []
    
    def sync_orders_to_system(self, orders):
        """将订单同步到系统"""
        synced_count = 0
        
        for order_data in orders:
            try:
                # 检查订单是否已存在
                existing_order = Order.query.filter_by(
                    external_order_number=order_data['order_id']
                ).first()
                
                if existing_order:
                    print(f"订单已存在: {order_data['order_id']}")
                    continue
                
                # 创建新订单
                order = Order(
                    order_number=f"DY{order_data['order_id']}",
                    customer_name=order_data.get('buyer_name', ''),
                    customer_phone=order_data.get('buyer_phone', ''),
                    size=order_data.get('product_size', ''),
                    style_name='',
                    product_name=order_data.get('product_name', ''),
                    original_image=order_data.get('image_url', ''),
                    status=self.map_status(order_data.get('status', '')),
                    shipping_info=json.dumps({
                        'receiver': order_data.get('receiver_name', ''),
                        'address': order_data.get('shipping_address', ''),
                        'remark': order_data.get('remark', '')
                    }),
                    price=float(order_data.get('total_amount', 0)),
                    external_platform='douyin',
                    external_order_number=order_data['order_id'],
                    source_type='douyin',
                    created_at=datetime.fromtimestamp(order_data.get('create_time', 0))
                )
                
                db.session.add(order)
                db.session.commit()
                synced_count += 1
                
                print(f"订单同步成功: {order_data['order_id']}")
                
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

# 使用示例
def sync_douyin_orders_from_api():
    """从API同步抖音订单"""
    api_client = DouyinShopAPI()
    
    # 获取订单数据
    orders = api_client.get_orders_from_api()
    
    if orders:
        # 同步到系统
        synced_count = api_client.sync_orders_to_system(orders)
        return synced_count
    else:
        print("没有获取到订单数据")
        return 0

if __name__ == "__main__":
    print("抖音小店API同步测试...")
    count = sync_douyin_orders_from_api()
    print(f"同步了 {count} 个订单")




