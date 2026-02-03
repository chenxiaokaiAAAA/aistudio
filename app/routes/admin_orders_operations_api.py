# -*- coding: utf-8 -*-
"""
管理后台订单操作API路由模块
提供订单打印、发货、删除等操作功能
"""
from flask import Blueprint, request, jsonify, flash, current_app
from flask_login import login_required, current_user
import os
import sys

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
admin_orders_operations_bp = Blueprint('admin_orders_operations', __name__)

@admin_orders_operations_bp.route('/admin/order/<int:order_id>/send-to-printer', methods=['POST'])
@login_required
def admin_send_to_printer(order_id):
    """管理员手动发送订单到冲印系统"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models(['Order', 'db', 'PRINTER_SYSTEM_AVAILABLE', 'PRINTER_SYSTEM_CONFIG', 'PrinterSystemClient'])
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    PRINTER_SYSTEM_AVAILABLE = models.get('PRINTER_SYSTEM_AVAILABLE', False)
    PRINTER_SYSTEM_CONFIG = models.get('PRINTER_SYSTEM_CONFIG', {})
    PrinterSystemClient = models.get('PrinterSystemClient')
    db = models['db']
    
    order = Order.query.get_or_404(order_id)
    
    # 检查订单状态和高清图片
    if order.status != 'hd_ready':
        return jsonify({'success': False, 'message': '订单状态必须是"高清放大"才能发送'}), 400
    
    if not order.hd_image:
        return jsonify({'success': False, 'message': '订单没有高清图片'}), 400
    
    # 检查冲印系统配置
    if not PRINTER_SYSTEM_AVAILABLE or not PRINTER_SYSTEM_CONFIG.get('enabled', False):
        return jsonify({'success': False, 'message': '冲印系统未启用'}), 400
    
    try:
        # 检查高清图片文件
        hd_image_path = os.path.join(current_app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            return jsonify({'success': False, 'message': f'高清图片文件不存在: {hd_image_path}'}), 400
        
        # 发送到冲印系统
        if PrinterSystemClient:
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            result = printer_client.send_order_to_printer(order, hd_image_path, order_obj=order)
            
            # 提交数据库更改
            db.session.commit()
            
            if result['success']:
                # 发送成功后，更新状态为"厂家制作中"
                order.status = 'manufacturing'  # 新增状态：厂家制作中
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': '订单已成功发送到厂家',
                    'new_status': 'manufacturing'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': f'发送失败: {result.get("message", "未知错误")}'
                })
        else:
            return jsonify({'success': False, 'message': '冲印系统客户端未初始化'}), 500
            
    except Exception as e:
        print(f"发送订单到冲印系统时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'}), 500

@admin_orders_operations_bp.route('/admin/order/<int:order_id>/delete', methods=['POST'])
@login_required
def admin_order_delete(order_id):
    """删除订单"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models(['Order', 'db'])
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    db = models['db']
    
    order = Order.query.get_or_404(order_id)
    
    try:
        db.session.delete(order)
        db.session.commit()
        flash('订单删除成功', 'success')
        return jsonify({'success': True, 'message': '订单删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除订单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@admin_orders_operations_bp.route('/admin/order/<int:order_id>/send-data', methods=['GET'])
@login_required
@admin_required
def admin_view_send_data(order_id):
    """管理员查看订单发送数据包"""
    models = get_models(['Order', 'PrinterSystemClient', 'PRINTER_SYSTEM_CONFIG', 'db'])
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    PrinterSystemClient = models.get('PrinterSystemClient')
    PRINTER_SYSTEM_CONFIG = models.get('PRINTER_SYSTEM_CONFIG', {})
    
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # 检查高清图片
        if not order.hd_image:
            return jsonify({'success': False, 'message': '订单没有高清图片'}), 400
        
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            return jsonify({'success': False, 'message': f'高清图片文件不存在: {hd_image_path}'}), 400
        
        # 构建发送数据包（不实际发送）
        if not PrinterSystemClient:
            return jsonify({'success': False, 'message': '冲印系统客户端不可用'}), 500
        
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 获取图片信息
        image_info = printer_client._get_image_info(hd_image_path, order)
        
        # 构建订单数据
        order_data = printer_client._build_order_data(order, hd_image_path)
        
        # 订单基本信息
        order_info = {
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'product_name': order.product_name,
            'size': order.size,
            'status': order.status,
            'hd_image': order.hd_image
        }
        
        return jsonify({
            'success': True,
            'order_info': order_info,
            'image_info': image_info,
            'send_data': order_data
        })
        
    except Exception as e:
        print(f"获取发送数据包时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@admin_orders_operations_bp.route('/admin/order/<int:order_id>/check-image-size', methods=['GET'])
@login_required
@admin_required
def admin_check_image_size(order_id):
    """管理员检查订单图片尺寸"""
    models = get_models(['Order', 'PrinterSystemClient', 'PRINTER_SYSTEM_CONFIG'])
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    PrinterSystemClient = models.get('PrinterSystemClient')
    PRINTER_SYSTEM_CONFIG = models.get('PRINTER_SYSTEM_CONFIG', {})
    
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # 检查高清图片
        if not order.hd_image:
            return jsonify({'success': False, 'message': '订单没有高清图片'}), 400
        
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            return jsonify({'success': False, 'message': f'高清图片文件不存在: {hd_image_path}'}), 400
        
        # 验证图片尺寸
        if not PrinterSystemClient:
            return jsonify({'success': False, 'message': '冲印系统客户端不可用'}), 500
        
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        validation_result = printer_client._validate_image_size(hd_image_path, order)
        
        return jsonify({
            'success': True,
            'validation_result': validation_result
        })
        
    except Exception as e:
        print(f"检查图片尺寸时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'检查失败: {str(e)}'}), 500

@admin_orders_operations_bp.route('/admin/order/<int:order_id>/manual-logistics', methods=['POST'])
@login_required
@admin_required
def admin_manual_logistics(order_id):
    """管理员或营运管理员手动录入快递单号"""
    from datetime import datetime
    import json
    
    models = get_models(['Order', 'db'])
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    db = models['db']
    
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 验证必要字段
        company = data.get('company')
        tracking_number = data.get('tracking_number')
        status = data.get('status', 'shipped')
        remark = data.get('remark', '')
        
        if not company or not tracking_number:
            return jsonify({'success': False, 'message': '快递公司和快递单号不能为空'}), 400
        
        # 查找订单
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        # 构建物流信息（JSON格式）
        logistics_data = {
            'company': company,
            'tracking_number': tracking_number,
            'status': status,
            'remark': remark,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'manual'  # 标记为手动录入
        }
        
        # 更新订单物流信息
        order.logistics_info = json.dumps(logistics_data, ensure_ascii=False)
        
        # 如果订单状态不是已发货相关状态，更新为已发货
        if order.status not in ['shipped', 'delivered']:
            order.status = 'shipped'  # 已发货
        
        # 添加发货时间字段（如果不存在则使用当前时间）
        if hasattr(order, 'shipped_at'):
            order.shipped_at = datetime.now()
        
        db.session.commit()
        
        print(f"✅ 订单 {order.order_number} 手动录入快递信息成功:")
        print(f"   快递公司: {company}")
        print(f"   快递单号: {tracking_number}")
        print(f"   状态: {status}")
        print(f"   备注: {remark}")
        
        return jsonify({
            'success': True,
            'message': '快递单号录入成功',
            'logistics_info': logistics_data
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"手动录入快递单号失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'录入失败: {str(e)}'}), 500
