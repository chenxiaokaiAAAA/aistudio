#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音Webhook回调同步功能
"""

import json
import hmac
import hashlib
from flask import request, jsonify
from test_server import db, Order
from datetime import datetime

def verify_douyin_webhook_signature(payload, signature, secret):
    """验证抖音Webhook签名"""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        print(f"签名验证失败: {e}")
        return False

def handle_douyin_order_webhook():
    """处理抖音订单Webhook回调"""
    try:
        # 获取请求数据
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Douyin-Signature', '')
        
        # 验证签名
        webhook_secret = "your_webhook_secret"  # 从配置中获取
        if not verify_douyin_webhook_signature(payload, signature, webhook_secret):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # 解析订单数据
        order_data = json.loads(payload)
        event_type = order_data.get('event_type')
        
        if event_type == 'order.created':
            return handle_order_created(order_data)
        elif event_type == 'order.updated':
            return handle_order_updated(order_data)
        elif event_type == 'order.cancelled':
            return handle_order_cancelled(order_data)
        else:
            return jsonify({'message': 'Unknown event type'}), 400
            
    except Exception as e:
        print(f"处理Webhook失败: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def handle_order_created(order_data):
    """处理订单创建事件"""
    try:
        order_info = order_data.get('data', {})
        
        # 检查订单是否已存在
        existing_order = Order.query.filter_by(
            external_order_number=order_info['order_id']
        ).first()
        
        if existing_order:
            return jsonify({'message': 'Order already exists'}), 200
        
        # 创建新订单
        order = Order(
            order_number=f"DY{order_info['order_id']}",
            customer_name=order_info.get('buyer_name', ''),
            customer_phone=order_info.get('buyer_phone', ''),
            size=order_info.get('product_size', ''),
            style_name=order_info.get('style_name', ''),
            product_name=order_info.get('product_name', ''),
            original_image=order_info.get('image_url', ''),
            status='pending',
            shipping_info=json.dumps({
                'receiver': order_info.get('receiver_name', ''),
                'address': order_info.get('shipping_address', ''),
                'remark': order_info.get('remark', '')
            }),
            price=float(order_info.get('total_amount', 0)),
            external_platform='douyin',
            external_order_number=order_info['order_id'],
            source_type='douyin',
            created_at=datetime.now()
        )
        
        db.session.add(order)
        db.session.commit()
        
        print(f"抖音订单创建成功: {order_info['order_id']}")
        return jsonify({'message': 'Order created successfully'}), 200
        
    except Exception as e:
        print(f"处理订单创建失败: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create order'}), 500

def handle_order_updated(order_data):
    """处理订单更新事件"""
    try:
        order_info = order_data.get('data', {})
        
        # 查找现有订单
        order = Order.query.filter_by(
            external_order_number=order_info['order_id']
        ).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # 更新订单状态
        douyin_status = order_info.get('status')
        status_mapping = {
            'pending': 'pending',
            'paid': 'processing',
            'shipped': 'shipped',
            'completed': 'completed',
            'cancelled': 'cancelled'
        }
        
        order.status = status_mapping.get(douyin_status, 'pending')
        order.completed_at = datetime.now() if douyin_status == 'completed' else None
        
        db.session.commit()
        
        print(f"抖音订单更新成功: {order_info['order_id']} -> {order.status}")
        return jsonify({'message': 'Order updated successfully'}), 200
        
    except Exception as e:
        print(f"处理订单更新失败: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update order'}), 500

def handle_order_cancelled(order_data):
    """处理订单取消事件"""
    try:
        order_info = order_data.get('data', {})
        
        # 查找现有订单
        order = Order.query.filter_by(
            external_order_number=order_info['order_id']
        ).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # 更新订单状态为取消
        order.status = 'cancelled'
        db.session.commit()
        
        print(f"抖音订单取消成功: {order_info['order_id']}")
        return jsonify({'message': 'Order cancelled successfully'}), 200
        
    except Exception as e:
        print(f"处理订单取消失败: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel order'}), 500

# Flask路由注册
def register_douyin_webhook_routes(app):
    """注册抖音Webhook路由"""
    
    @app.route('/api/douyin/webhook', methods=['POST'])
    def douyin_webhook():
        """抖音Webhook回调接口"""
        return handle_douyin_order_webhook()
    
    @app.route('/api/douyin/webhook/test', methods=['POST'])
    def test_douyin_webhook():
        """测试抖音Webhook接口"""
        try:
            test_data = {
                'event_type': 'order.created',
                'data': {
                    'order_id': f'TEST_{int(time.time())}',
                    'buyer_name': '测试用户',
                    'buyer_phone': '13800138000',
                    'product_name': '测试产品',
                    'total_amount': 99.0,
                    'receiver_name': '测试收件人',
                    'shipping_address': '测试地址',
                    'image_url': 'https://example.com/test.jpg'
                }
            }
            
            return handle_order_created(test_data)
            
        except Exception as e:
            return jsonify({'error': f'测试失败: {str(e)}'}), 500

if __name__ == "__main__":
    print("抖音Webhook回调功能已准备就绪")
    print("需要在抖音开放平台配置Webhook URL: https://yourdomain.com/api/douyin/webhook")




