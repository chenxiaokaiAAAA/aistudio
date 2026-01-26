#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音开放平台API客户端
"""

import requests
import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from douyin_config import get_config, get_api_endpoint, map_order_status, get_error_message

class DouyinOpenAPI:
    """抖音开放平台API客户端"""
    
    def __init__(self):
        self.config = get_config()
        self.access_token = None
        self.token_expires_at = None
        self.refresh_token = None
        
    def get_access_token(self):
        """获取访问令牌"""
        try:
            url = f"{self.config['base_url']}{get_api_endpoint('access_token')}"
            
            data = {
                'client_key': self.config['app_id'],
                'client_secret': self.config['app_secret'],
                'grant_type': 'client_credential'
            }
            
            response = requests.post(url, json=data, timeout=self.config['timeout'])
            result = response.json()
            
            if result.get('data'):
                self.access_token = result['data']['access_token']
                self.token_expires_at = time.time() + result['data']['expires_in']
                print(f"获取access_token成功: {self.access_token[:20]}...")
                return True
            else:
                error_code = result.get('error_code', 0)
                error_msg = get_error_message(error_code)
                print(f"获取access_token失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"获取access_token异常: {e}")
            return False
    
    def refresh_access_token(self):
        """刷新访问令牌"""
        try:
            if not self.refresh_token:
                return self.get_access_token()
            
            url = f"{self.config['base_url']}{get_api_endpoint('refresh_token')}"
            
            data = {
                'client_key': self.config['app_id'],
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(url, json=data, timeout=self.config['timeout'])
            result = response.json()
            
            if result.get('data'):
                self.access_token = result['data']['access_token']
                self.token_expires_at = time.time() + result['data']['expires_in']
                self.refresh_token = result['data'].get('refresh_token', self.refresh_token)
                print(f"刷新access_token成功: {self.access_token[:20]}...")
                return True
            else:
                error_code = result.get('error_code', 0)
                error_msg = get_error_message(error_code)
                print(f"刷新access_token失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"刷新access_token异常: {e}")
            return False
    
    def is_token_valid(self):
        """检查令牌是否有效"""
        if not self.access_token:
            return False
        
        if self.token_expires_at and time.time() >= self.token_expires_at - 300:  # 提前5分钟刷新
            return False
        
        return True
    
    def ensure_valid_token(self):
        """确保令牌有效"""
        if not self.is_token_valid():
            if not self.refresh_access_token():
                return False
        return True
    
    def make_request(self, endpoint, method='GET', params=None, data=None):
        """发起API请求"""
        try:
            if not self.ensure_valid_token():
                return None
            
            url = f"{self.config['base_url']}{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.config['timeout'])
            else:
                response = requests.post(url, headers=headers, json=data, timeout=self.config['timeout'])
            
            result = response.json()
            
            if result.get('error_code') == 0:
                return result.get('data')
            else:
                error_code = result.get('error_code', 0)
                error_msg = get_error_message(error_code)
                print(f"API请求失败: {error_msg}")
                return None
                
        except Exception as e:
            print(f"API请求异常: {e}")
            return None
    
    def get_orders(self, start_time=None, end_time=None, page=1, page_size=100):
        """获取订单列表"""
        try:
            if not start_time:
                start_time = datetime.now() - timedelta(days=7)
            if not end_time:
                end_time = datetime.now()
            
            params = {
                'shop_id': self.config['shop_id'],
                'start_time': int(start_time.timestamp()),
                'end_time': int(end_time.timestamp()),
                'page': page,
                'page_size': page_size
            }
            
            data = self.make_request(get_api_endpoint('order_list'), 'GET', params=params)
            
            if data:
                orders = data.get('orders', [])
                print(f"获取到 {len(orders)} 个订单")
                return orders
            else:
                return []
                
        except Exception as e:
            print(f"获取订单列表失败: {e}")
            return []
    
    def get_order_detail(self, order_id):
        """获取订单详情"""
        try:
            params = {
                'shop_id': self.config['shop_id'],
                'order_id': order_id
            }
            
            data = self.make_request(get_api_endpoint('order_detail'), 'GET', params=params)
            return data
            
        except Exception as e:
            print(f"获取订单详情失败: {e}")
            return None
    
    def get_products(self, page=1, page_size=100):
        """获取商品列表"""
        try:
            params = {
                'shop_id': self.config['shop_id'],
                'page': page,
                'page_size': page_size
            }
            
            data = self.make_request(get_api_endpoint('product_list'), 'GET', params=params)
            
            if data:
                products = data.get('products', [])
                print(f"获取到 {len(products)} 个商品")
                return products
            else:
                return []
                
        except Exception as e:
            print(f"获取商品列表失败: {e}")
            return []
    
    def get_shop_info(self):
        """获取店铺信息"""
        try:
            params = {
                'shop_id': self.config['shop_id']
            }
            
            data = self.make_request(get_api_endpoint('shop_info'), 'GET', params=params)
            return data
            
        except Exception as e:
            print(f"获取店铺信息失败: {e}")
            return None
    
    def register_webhook(self, webhook_url, events):
        """注册Webhook"""
        try:
            data = {
                'shop_id': self.config['shop_id'],
                'webhook_url': webhook_url,
                'events': events
            }
            
            result = self.make_request(get_api_endpoint('webhook_register'), 'POST', data=data)
            return result is not None
            
        except Exception as e:
            print(f"注册Webhook失败: {e}")
            return False

# 使用示例
def test_douyin_api():
    """测试抖音API"""
    api_client = DouyinOpenAPI()
    
    # 测试获取访问令牌
    if api_client.get_access_token():
        print("✅ 获取访问令牌成功")
        
        # 测试获取店铺信息
        shop_info = api_client.get_shop_info()
        if shop_info:
            print(f"✅ 店铺信息: {shop_info.get('shop_name', '未知')}")
        
        # 测试获取订单
        orders = api_client.get_orders()
        if orders:
            print(f"✅ 获取到 {len(orders)} 个订单")
        
        # 测试获取商品
        products = api_client.get_products()
        if products:
            print(f"✅ 获取到 {len(products)} 个商品")
    else:
        print("❌ 获取访问令牌失败")

if __name__ == "__main__":
    print("抖音开放平台API客户端已准备就绪")
    print("使用方法:")
    print("1. 在 douyin_config.py 中配置您的应用信息")
    print("2. 调用 test_douyin_api() 测试API连接")
    print("3. 使用 api_client.get_orders() 获取订单数据")




