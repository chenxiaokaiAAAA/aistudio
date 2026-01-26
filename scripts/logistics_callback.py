#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物流信息回传接口
厂家通过此接口回传物流信息
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

# 物流信息回传接口
@app.route('/api/printer/logistics-callback', methods=['POST'])
def printer_logistics_callback():
    """
    冲印系统物流信息回传接口
    厂家完成制作后，通过此接口回传物流信息
    
    请求格式:
    {
        "order_id": "YT_123",  # 我们发送给厂家的订单ID
        "logistics_company": "顺丰快递",
        "tracking_number": "SF1234567890",
        "status": "shipped",  # shipped: 已发货, delivered: 已送达
        "remark": "订单已完成制作并发出"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '缺少请求数据'}), 400
        
        # 验证必要字段
        required_fields = ['order_id', 'logistics_company', 'tracking_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        order_id = data['order_id']
        logistics_company = data['logistics_company']
        tracking_number = data['tracking_number']
        status = data.get('status', 'shipped')
        remark = data.get('remark', '')
        
        # 查找对应的订单
        # order_id格式: YT_123，需要提取数字部分
        if order_id.startswith('YT_'):
            order_number = order_id[3:]  # 移除YT_前缀
            try:
                order_id_int = int(order_number)
                order = Order.query.get(order_id_int)
            except ValueError:
                return jsonify({'success': False, 'message': '订单ID格式错误'}), 400
        else:
            return jsonify({'success': False, 'message': '订单ID格式错误'}), 400
        
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        # 更新订单物流信息
        logistics_info = {
            'company': logistics_company,
            'tracking_number': tracking_number,
            'status': status,
            'remark': remark,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 更新订单状态和物流信息
        order.shipping_info = json.dumps(logistics_info, ensure_ascii=False)
        order.status = 'processing'  # 已发货
        order.printer_send_status = 'logistics_updated'  # 新增状态：物流已更新
        
        db.session.commit()
        
        print(f"✅ 订单 {order.order_number} 物流信息已更新:")
        print(f"   快递公司: {logistics_company}")
        print(f"   快递单号: {tracking_number}")
        print(f"   状态: {status}")
        
        return jsonify({
            'success': True,
            'message': '物流信息更新成功',
            'order_number': order.order_number
        })
        
    except Exception as e:
        print(f"物流信息回传失败: {str(e)}")
        return jsonify({'success': False, 'message': f'处理失败: {str(e)}'}), 500

# 查询订单物流状态接口（供小程序和网页使用）
@app.route('/api/order/<int:order_id>/logistics', methods=['GET'])
def get_order_logistics(order_id):
    """获取订单物流信息"""
    try:
        order = Order.query.get_or_404(order_id)
        
        logistics_info = None
        if order.shipping_info:
            try:
                logistics_info = json.loads(order.shipping_info)
            except:
                # 兼容旧格式
                logistics_info = {
                    'company': '未知',
                    'tracking_number': order.shipping_info,
                    'status': 'shipped',
                    'remark': '',
                    'update_time': order.updated_at.strftime('%Y-%m-%d %H:%M:%S') if order.updated_at else ''
                }
        
        return jsonify({
            'success': True,
            'order_number': order.order_number,
            'status': order.status,
            'logistics': logistics_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500
