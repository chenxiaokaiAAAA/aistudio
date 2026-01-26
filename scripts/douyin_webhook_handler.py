#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音Webhook处理服务
"""

import json
import hmac
import hashlib
from flask import request, jsonify
from test_server import db, Order
from douyin_config import get_config, map_order_status, DOUYIN_WEBHOOK_EVENTS
from douyin_sync_service import douyin_sync_service

class DouyinWebhookHandler:
    """抖音Webhook处理器"""
    
    def __init__(self):
        self.config = get_config()
    
    def verify_signature(self, payload, signature):
        """验证Webhook签名"""
        try:
            expected_signature = hmac.new(
                self.config['webhook_secret'].encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            print(f"签名验证失败: {e}")
            return False
    
    def handle_webhook(self):
        """处理Webhook请求"""
        try:
            # 获取请求数据
            payload = request.get_data(as_text=True)
            signature = request.headers.get('X-Douyin-Signature', '')
            
            # 验证签名
            if not self.verify_signature(payload, signature):
                print("Webhook签名验证失败")
                return jsonify({'error': 'Invalid signature'}), 401
            
            # 解析事件数据
            event_data = json.loads(payload)
            event_type = event_data.get('event_type')
            
            print(f"收到Webhook事件: {event_type}")
            
            # 处理不同类型的事件
            if event_type == 'order.created':
                return self.handle_order_created(event_data)
            elif event_type == 'order.paid':
                return self.handle_order_paid(event_data)
            elif event_type == 'order.shipped':
                return self.handle_order_shipped(event_data)
            elif event_type == 'order.completed':
                return self.handle_order_completed(event_data)
            elif event_type == 'order.cancelled':
                return self.handle_order_cancelled(event_data)
            elif event_type == 'order.refunded':
                return self.handle_order_refunded(event_data)
            else:
                print(f"未知事件类型: {event_type}")
                return jsonify({'message': 'Unknown event type'}), 400
                
        except Exception as e:
            print(f"处理Webhook失败: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def handle_order_created(self, event_data):
        """处理订单创建事件"""
        try:
            order_data = event_data.get('data', {})
            order_id = order_data.get('order_id')
            
            if not order_id:
                return jsonify({'error': 'Missing order_id'}), 400
            
            # 检查订单是否已存在
            existing_order = Order.query.filter_by(
                external_order_number=str(order_id)
            ).first()
            
            if existing_order:
                return jsonify({'message': 'Order already exists'}), 200
            
            # 创建新订单
            order = Order(
                order_number=f"DY{order_id}",
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
                external_order_number=str(order_id),
                source_type='douyin',
                created_at=datetime.now()
            )
            
            db.session.add(order)
            db.session.commit()
            
            print(f"订单创建成功: {order_id}")
            return jsonify({'message': 'Order created successfully'}), 200
            
        except Exception as e:
            print(f"处理订单创建失败: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create order'}), 500
    
    def handle_order_paid(self, event_data):
        """处理订单支付事件"""
        return self.update_order_status(event_data, 'processing')
    
    def handle_order_shipped(self, event_data):
        """处理订单发货事件"""
        return self.update_order_status(event_data, 'shipped')
    
    def handle_order_completed(self, event_data):
        """处理订单完成事件"""
        return self.update_order_status(event_data, 'completed')
    
    def handle_order_cancelled(self, event_data):
        """处理订单取消事件"""
        return self.update_order_status(event_data, 'cancelled')
    
    def handle_order_refunded(self, event_data):
        """处理订单退款事件"""
        return self.update_order_status(event_data, 'cancelled')
    
    def update_order_status(self, event_data, new_status):
        """更新订单状态"""
        try:
            order_data = event_data.get('data', {})
            order_id = order_data.get('order_id')
            
            if not order_id:
                return jsonify({'error': 'Missing order_id'}), 400
            
            # 查找订单
            order = Order.query.filter_by(
                external_order_number=str(order_id)
            ).first()
            
            if not order:
                print(f"订单不存在: {order_id}")
                return jsonify({'error': 'Order not found'}), 404
            
            # 更新状态
            old_status = order.status
            order.status = new_status
            
            # 如果订单完成，更新完成时间
            if new_status == 'completed' and not order.completed_at:
                order.completed_at = datetime.now()
            
            db.session.commit()
            
            print(f"订单状态更新: {order_id} {old_status} -> {new_status}")
            return jsonify({'message': 'Order status updated successfully'}), 200
            
        except Exception as e:
            print(f"更新订单状态失败: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to update order status'}), 500

# 全局Webhook处理器实例
douyin_webhook_handler = DouyinWebhookHandler()

# Flask路由
def create_douyin_webhook_routes(app):
    """创建抖音Webhook路由"""
    
    @app.route('/api/douyin/webhook', methods=['POST'])
    def douyin_webhook():
        """抖音Webhook回调接口"""
        return douyin_webhook_handler.handle_webhook()
    
    @app.route('/api/douyin/webhook/test', methods=['POST'])
    def test_douyin_webhook():
        """测试抖音Webhook接口"""
        try:
            # 模拟订单创建事件
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
            
            return douyin_webhook_handler.handle_order_created(test_data)
            
        except Exception as e:
            return jsonify({'error': f'测试失败: {str(e)}'}), 500
    
    @app.route('/api/douyin/webhook/status', methods=['GET'])
    def webhook_status():
        """获取Webhook状态"""
        try:
            status = douyin_sync_service.get_sync_status()
            if status:
                return jsonify({
                    'success': True,
                    'data': status
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '获取状态失败'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取状态失败: {str(e)}'
            }), 500

if __name__ == "__main__":
    print("抖音Webhook处理服务已准备就绪")
    print("使用方法:")
    print("1. 在抖音开放平台配置Webhook URL: https://yourdomain.com/api/douyin/webhook")
    print("2. 确保 webhook_secret 配置正确")
    print("3. 系统会自动处理订单事件")




