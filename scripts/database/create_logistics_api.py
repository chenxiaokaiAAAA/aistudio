#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物流信息回传接口
供厂家回传物流单号等信息
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from datetime import datetime
from flask import request, jsonify

def create_logistics_callback_route():
    """创建物流信息回传接口"""
    
    @app.route('/api/logistics/callback', methods=['POST'])
    def logistics_callback():
        """
        物流信息回传接口
        厂家调用此接口回传物流信息
        
        请求参数:
        {
            "order_number": "订单号",
            "tracking_number": "物流单号",
            "logistics_company": "物流公司",
            "estimated_delivery": "预计送达时间(可选)",
            "status": "物流状态(可选)",
            "remark": "备注(可选)"
        }
        """
        try:
            # 获取请求数据
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空'
                }), 400
            
            # 验证必要参数
            order_number = data.get('order_number')
            tracking_number = data.get('tracking_number')
            logistics_company = data.get('logistics_company')
            
            if not all([order_number, tracking_number, logistics_company]):
                return jsonify({
                    'success': False,
                    'message': '缺少必要参数: order_number, tracking_number, logistics_company'
                }), 400
            
            # 查找订单
            order = Order.query.filter_by(order_number=order_number).first()
            if not order:
                return jsonify({
                    'success': False,
                    'message': f'订单 {order_number} 不存在'
                }), 404
            
            # 更新订单状态和物流信息
            order.status = 'shipped'  # 更新为已发货
            
            # 构建物流信息
            logistics_info = f"物流公司: {logistics_company}\n物流单号: {tracking_number}"
            
            estimated_delivery = data.get('estimated_delivery')
            if estimated_delivery:
                logistics_info += f"\n预计送达: {estimated_delivery}"
            
            status = data.get('status')
            if status:
                logistics_info += f"\n物流状态: {status}"
            
            remark = data.get('remark')
            if remark:
                logistics_info += f"\n备注: {remark}"
            
            order.shipping_info = logistics_info
            order.completed_at = datetime.now()
            
            # 重新计算佣金（因为状态变为shipped）
            if order.merchant and order.status in ['hd_ready', 'shipped']:
                base_price = order.price or 0.0
                order.commission = base_price * (order.merchant.commission_rate or 0.0)
            
            # 保存到数据库
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '物流信息更新成功',
                'data': {
                    'order_number': order.order_number,
                    'status': order.status,
                    'tracking_number': tracking_number,
                    'logistics_company': logistics_company,
                    'commission': order.commission
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }), 500
    
    @app.route('/api/logistics/test', methods=['GET'])
    def logistics_test():
        """测试物流接口"""
        return jsonify({
            'success': True,
            'message': '物流接口正常',
            'endpoint': '/api/logistics/callback',
            'method': 'POST',
            'required_params': [
                'order_number',
                'tracking_number', 
                'logistics_company'
            ],
            'optional_params': [
                'estimated_delivery',
                'status',
                'remark'
            ]
        })

def create_test_script():
    """创建测试脚本"""
    test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试物流信息回传接口
"""

import requests
import json

def test_logistics_callback():
    """测试物流信息回传"""
    
    # 接口地址
    url = "http://photogooo/api/logistics/callback"
    
    # 测试数据
    test_data = {
        "order_number": "PET20250917175858D53F",
        "tracking_number": "SF1234567890",
        "logistics_company": "顺丰速运",
        "estimated_delivery": "2025-09-20",
        "status": "已发货",
        "remark": "厂家冲印测试订单"
    }
    
    print("🧪 测试物流信息回传接口...")
    print(f"📋 请求数据:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"\\n📊 响应结果:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"  ✅ 物流信息回传成功!")
                print(f"  订单号: {result['data']['order_number']}")
                print(f"  状态: {result['data']['status']}")
                print(f"  物流单号: {result['data']['tracking_number']}")
                print(f"  佣金: ¥{result['data']['commission']:.2f}")
            else:
                print(f"  ❌ 回传失败: {result.get('message')}")
        else:
            print(f"  ❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == '__main__':
    test_logistics_callback()
'''
    
    with open('test_logistics_callback.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 测试脚本已创建: test_logistics_callback.py")

if __name__ == '__main__':
    print("🚀 创建物流信息回传接口...")
    
    # 创建接口
    create_logistics_callback_route()
    
    # 创建测试脚本
    create_test_script()
    
    print("✅ 物流信息回传接口已创建!")
    print("\\n📋 接口信息:")
    print("  URL: http://photogooo/api/logistics/callback")
    print("  方法: POST")
    print("  必要参数: order_number, tracking_number, logistics_company")
    print("  可选参数: estimated_delivery, status, remark")
    
    print("\\n🧪 测试接口:")
    print("  URL: http://photogooo/api/logistics/test")
    print("  方法: GET")
    
    print("\\n📝 厂家调用示例:")
    print("""
    POST http://photogooo/api/logistics/callback
    Content-Type: application/json
    
    {
        "order_number": "PET20250917175858D53F",
        "tracking_number": "SF1234567890",
        "logistics_company": "顺丰速运",
        "estimated_delivery": "2025-09-20",
        "status": "已发货",
        "remark": "厂家冲印测试订单"
    }
    """)
