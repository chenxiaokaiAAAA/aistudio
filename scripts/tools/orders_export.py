#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
订单数据导出功能
管理员可以导出所有订单数据作为备份
"""

import csv
import io
from datetime import datetime
from flask import make_response, jsonify
from flask_login import login_required, current_user

def create_orders_export_routes(app, db, Order, User):
    """创建订单导出相关的路由"""
    
    @app.route('/admin/orders/export', methods=['GET'])
    @login_required
    def export_orders():
        """导出所有订单数据为CSV格式"""
        try:
            # 检查管理员权限
            if current_user.role != 'admin':
                return jsonify({'success': False, 'message': '权限不足'}), 403
            
            # 获取所有订单数据
            orders = Order.query.order_by(Order.created_at.desc()).all()
            
            # 创建CSV内容
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入CSV头部
            headers = [
                '订单ID', '订单号', '客户姓名', '客户手机', '客户地址',
                '产品名称', '尺寸', '艺术风格', '订单状态', '订单价格',
                '佣金金额', '支付时间', '交易号', '下单时间', '完成时间',
                '商家', '来源类型', '外部平台', '外部订单号',
                '物流信息', '快递公司', '快递单号', '物流状态',
                '原图路径', '成品图路径', '高清图路径',
                '冲印发送状态', '加盟商ID', '备注'
            ]
            writer.writerow(headers)
            
            # 写入订单数据
            for order in orders:
                # 解析物流信息
                logistics_info = None
                logistics_company = ''
                tracking_number = ''
                logistics_status = ''
                
                if order.logistics_info:
                    try:
                        import json
                        logistics_info = json.loads(order.logistics_info)
                        logistics_company = logistics_info.get('company', '')
                        tracking_number = logistics_info.get('tracking_number', '')
                        logistics_status = logistics_info.get('status', '')
                    except:
                        pass
                
                # 获取商家信息
                merchant_name = ''
                if order.merchant:
                    merchant_name = order.merchant.username
                elif order.franchisee_id:
                    merchant_name = f"加盟商ID:{order.franchisee_id}"
                
                # 写入一行数据
                row = [
                    order.id,
                    order.order_number,
                    order.customer_name,
                    order.customer_phone or '',
                    order.customer_address or '',
                    order.product_name or '',
                    order.size or '',
                    order.style_name or '',
                    order.status or '',
                    order.price or 0,
                    order.commission or 0,
                    order.payment_time.strftime('%Y-%m-%d %H:%M:%S') if order.payment_time else '',
                    order.transaction_id or '',
                    order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
                    order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else '',
                    merchant_name,
                    order.source_type or '',
                    order.external_platform or '',
                    order.external_order_number or '',
                    order.shipping_info or '',
                    logistics_company,
                    tracking_number,
                    logistics_status,
                    order.original_image or '',
                    order.final_image or '',
                    order.hd_image or '',
                    order.printer_send_status or '',
                    order.franchisee_id or '',
                    order.customer_note or ''
                ]
                writer.writerow(row)
            
            # 准备响应
            output.seek(0)
            csv_content = output.getvalue()
            output.close()
            
            # 创建响应
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
            
        except Exception as e:
            print(f"导出订单数据失败: {str(e)}")
            return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500
    
    @app.route('/admin/orders/export/json', methods=['GET'])
    @login_required
    def export_orders_json():
        """导出所有订单数据为JSON格式"""
        try:
            # 检查管理员权限
            if current_user.role != 'admin':
                return jsonify({'success': False, 'message': '权限不足'}), 403
            
            # 获取所有订单数据
            orders = Order.query.order_by(Order.created_at.desc()).all()
            
            # 构建JSON数据
            orders_data = []
            for order in orders:
                # 解析物流信息
                logistics_info = None
                if order.logistics_info:
                    try:
                        import json
                        logistics_info = json.loads(order.logistics_info)
                    except:
                        pass
                
                order_data = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'customer_phone': order.customer_phone,
                    'customer_address': order.customer_address,
                    'product_name': order.product_name,
                    'size': order.size,
                    'style_name': order.style_name,
                    'status': order.status,
                    'price': float(order.price) if order.price else 0,
                    'commission': float(order.commission) if order.commission else 0,
                    'payment_time': order.payment_time.isoformat() if order.payment_time else None,
                    'transaction_id': order.transaction_id,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'completed_at': order.completed_at.isoformat() if order.completed_at else None,
                    'merchant': order.merchant.username if order.merchant else None,
                    'source_type': order.source_type,
                    'external_platform': order.external_platform,
                    'external_order_number': order.external_order_number,
                    'shipping_info': order.shipping_info,
                    'logistics_info': logistics_info,
                    'original_image': order.original_image,
                    'final_image': order.final_image,
                    'hd_image': order.hd_image,
                    'printer_send_status': order.printer_send_status,
                    'franchisee_id': order.franchisee_id,
                    'customer_note': order.customer_note
                }
                orders_data.append(order_data)
            
            # 创建响应
            response = make_response(jsonify({
                'success': True,
                'export_time': datetime.now().isoformat(),
                'total_orders': len(orders_data),
                'orders': orders_data
            }))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            return response
            
        except Exception as e:
            print(f"导出订单数据失败: {str(e)}")
            return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("订单数据导出功能模块")
    print("包含CSV和JSON两种导出格式")




