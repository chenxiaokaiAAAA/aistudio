#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音店铺数据同步功能
"""

import requests
import json
import time
from datetime import datetime
from flask import Blueprint, request, jsonify
from test_server import db, Order, User

# 抖音API配置
DOUYIN_CONFIG = {
    'app_key': 'your_app_key',
    'app_secret': 'your_app_secret',
    'base_url': 'https://open.douyin.com',
    'access_token': None,
    'token_expires_at': None
}

def get_douyin_access_token():
    """获取抖音访问令牌"""
    try:
        url = f"{DOUYIN_CONFIG['base_url']}/oauth/access_token/"
        data = {
            'client_key': DOUYIN_CONFIG['app_key'],
            'client_secret': DOUYIN_CONFIG['app_secret'],
            'grant_type': 'client_credential'
        }
        
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('data'):
            DOUYIN_CONFIG['access_token'] = result['data']['access_token']
            DOUYIN_CONFIG['token_expires_at'] = time.time() + result['data']['expires_in']
            return True
        else:
            print(f"获取抖音access_token失败: {result}")
            return False
            
    except Exception as e:
        print(f"获取抖音access_token异常: {e}")
        return False

def sync_douyin_orders():
    """同步抖音订单数据"""
    try:
        # 检查token是否过期
        if not DOUYIN_CONFIG['access_token'] or time.time() > DOUYIN_CONFIG['token_expires_at']:
            if not get_douyin_access_token():
                return False
        
        # 获取订单列表
        url = f"{DOUYIN_CONFIG['base_url']}/api/shop/order/list/"
        headers = {
            'Authorization': f"Bearer {DOUYIN_CONFIG['access_token']}",
            'Content-Type': 'application/json'
        }
        
        # 获取最近24小时的订单
        params = {
            'start_time': int((time.time() - 86400) * 1000),  # 24小时前
            'end_time': int(time.time() * 1000),  # 当前时间
            'page': 1,
            'size': 100
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get('data'):
            orders = result['data'].get('orders', [])
            synced_count = 0
            
            for order_data in orders:
                if sync_single_douyin_order(order_data):
                    synced_count += 1
            
            print(f"抖音订单同步完成: {synced_count}/{len(orders)}")
            return True
        else:
            print(f"获取抖音订单失败: {result}")
            return False
            
    except Exception as e:
        print(f"同步抖音订单异常: {e}")
        return False

def sync_single_douyin_order(order_data):
    """同步单个抖音订单"""
    try:
        # 检查订单是否已存在
        existing_order = Order.query.filter_by(
            external_order_number=order_data['order_id']
        ).first()
        
        if existing_order:
            print(f"订单已存在: {order_data['order_id']}")
            return True
        
        # 创建新订单
        order = Order(
            order_number=f"DY{order_data['order_id']}",
            customer_name=order_data.get('buyer_name', ''),
            customer_phone=order_data.get('buyer_phone', ''),
            size=order_data.get('product_size', ''),
            style_name=order_data.get('style_name', ''),
            product_name=order_data.get('product_name', ''),
            original_image=order_data.get('image_url', ''),
            status='pending',
            shipping_info=json.dumps({
                'receiver': order_data.get('receiver_name', ''),
                'address': order_data.get('shipping_address', ''),
                'remark': order_data.get('remark', '')
            }),
            price=float(order_data.get('total_amount', 0)),
            external_platform='douyin',
            external_order_number=order_data['order_id'],
            source_type='douyin',
            created_at=datetime.fromtimestamp(order_data['create_time'] / 1000)
        )
        
        db.session.add(order)
        db.session.commit()
        
        print(f"抖音订单同步成功: {order_data['order_id']}")
        return True
        
    except Exception as e:
        print(f"同步单个订单失败: {e}")
        db.session.rollback()
        return False

# Flask路由
def create_douyin_sync_routes(app):
    """创建抖音同步路由"""
    
    @app.route('/api/douyin/sync/orders', methods=['POST'])
    def sync_douyin_orders_api():
        """手动同步抖音订单"""
        try:
            if sync_douyin_orders():
                return jsonify({
                    'success': True,
                    'message': '抖音订单同步成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '抖音订单同步失败'
                }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'同步异常: {str(e)}'
            }), 500
    
    @app.route('/api/douyin/sync/status', methods=['GET'])
    def get_sync_status():
        """获取同步状态"""
        try:
            # 统计抖音订单数量
            douyin_orders = Order.query.filter_by(source_type='douyin').count()
            
            # 统计最近同步的订单
            recent_orders = Order.query.filter(
                Order.source_type == 'douyin',
                Order.created_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            return jsonify({
                'success': True,
                'data': {
                    'total_douyin_orders': douyin_orders,
                    'recent_synced_orders': recent_orders,
                    'last_sync_time': DOUYIN_CONFIG.get('last_sync_time'),
                    'token_status': 'valid' if DOUYIN_CONFIG['access_token'] else 'invalid'
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取状态失败: {str(e)}'
            }), 500

# 定时同步任务
def start_douyin_sync_scheduler():
    """启动抖音数据同步定时任务"""
    import threading
    import schedule
    
    def sync_job():
        print("开始执行抖音数据同步...")
        sync_douyin_orders()
        DOUYIN_CONFIG['last_sync_time'] = datetime.now().isoformat()
    
    # 每5分钟同步一次
    schedule.every(5).minutes.do(sync_job)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    # 在后台线程中运行
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("抖音数据同步定时任务已启动")

if __name__ == "__main__":
    # 测试同步功能
    print("测试抖音数据同步...")
    if sync_douyin_orders():
        print("同步测试成功")
    else:
        print("同步测试失败")




