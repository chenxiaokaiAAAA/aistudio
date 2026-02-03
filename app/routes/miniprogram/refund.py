# -*- coding: utf-8 -*-
"""
小程序退款申请API路由模块
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
import traceback

# 创建蓝图
bp = Blueprint('miniprogram_refund', __name__, url_prefix='/api/miniprogram')

def get_models():
    """延迟导入数据库模型，避免循环导入"""
    try:
        test_server = sys.modules.get('test_server')
        if test_server:
            models = {
                'Order': test_server.Order,
                'StaffUser': test_server.StaffUser,
                'FranchiseeAccount': test_server.FranchiseeAccount,
                'db': test_server.db
            }
            return models
        return None
    except Exception as e:
        print(f"⚠️ 获取数据库模型失败: {e}")
        return None

def check_staff_permission(openid, user_id, phone=None):
    """检查用户是否有退款申请权限（从StaffUser表中检查）"""
    try:
        models = get_models()
        if not models:
            return False
        
        StaffUser = models.get('StaffUser')
        if not StaffUser:
            return False
        
        import json
        
        # 优先通过手机号匹配
        if phone:
            staff_user = StaffUser.query.filter_by(
                phone=phone,
                status='active'
            ).first()
            if staff_user:
                try:
                    permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
                    if permissions.get('refund_request'):
                        return True
                except:
                    pass
        
        # 通过openid匹配
        if openid:
            staff_user = StaffUser.query.filter_by(
                openid=openid,
                status='active'
            ).first()
            if staff_user:
                try:
                    permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
                    if permissions.get('refund_request'):
                        return True
                except:
                    pass
        
        # 通过user_id匹配（如果user_id是手机号）
        if user_id and len(user_id) == 11 and user_id.isdigit():
            staff_user = StaffUser.query.filter_by(
                phone=user_id,
                status='active'
            ).first()
            if staff_user:
                try:
                    permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
                    if permissions.get('refund_request'):
                        return True
                except:
                    pass
        
        return False
    except Exception as e:
        print(f"检查店员权限失败: {e}")
        traceback.print_exc()
        return False

@bp.route('/refund/request', methods=['POST'])
def request_refund():
    """申请退款（针对异常订单）"""
    try:
        data = request.get_json()
        openid = data.get('openid')
        user_id = data.get('user_id')
        phone = data.get('phone')
        
        # 检查权限
        if not check_staff_permission(openid, user_id, phone):
            return jsonify({
                'status': 'error',
                'message': '权限不足，只有授权的店员可以申请退款'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Order = models['Order']
        db = models['db']
        
        # 验证必填字段
        required_fields = ['order_id', 'reason']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        order_id = int(data['order_id'])
        reason = data['reason'].strip()
        
        if not reason:
            return jsonify({
                'status': 'error',
                'message': '退款原因不能为空'
            }), 400
        
        # 获取订单
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'status': 'error',
                'message': '订单不存在'
            }), 404
        
        # 检查订单状态（只有特定状态的订单可以申请退款）
        if order.status in ['cancelled', 'refunded']:
            return jsonify({
                'status': 'error',
                'message': '该订单已取消或已退款'
            }), 400
        
        # 检查是否已有退款申请
        # 这里可以扩展为创建退款申请记录表，目前先简单处理
        # 可以通过订单的备注字段或其他方式记录退款申请
        
        # 创建退款申请记录（可以扩展为独立的RefundRequest表）
        # 目前先通过订单状态和备注来记录
        order.refund_request_reason = reason
        order.refund_request_time = datetime.now()
        order.refund_request_status = 'pending'  # pending待处理, approved已批准, rejected已拒绝
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '退款申请已提交，等待管理员审核',
            'data': {
                'order_id': order.id,
                'order_number': order.order_number,
                'refund_request_status': 'pending'
            }
        })
        
    except Exception as e:
        print(f"申请退款失败: {str(e)}")
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'申请退款失败: {str(e)}'
        }), 500

@bp.route('/refund/check-order', methods=['GET'])
def check_order():
    """检查订单是否存在（用于退款申请）- 支持订单号或手机号查询"""
    try:
        order_number = request.args.get('order_number', '').strip()
        phone = request.args.get('phone', '').strip()
        
        if not order_number and not phone:
            return jsonify({
                'status': 'error',
                'message': '订单号或手机号不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Order = models['Order']
        
        # 查询订单（优先按订单号，否则按手机号）
        if order_number:
            order = Order.query.filter_by(order_number=order_number).first()
        else:
            # 按手机号查询，取最新的订单
            order = Order.query.filter_by(customer_phone=phone).order_by(Order.created_at.desc()).first()
        
        if not order:
            return jsonify({
                'status': 'error',
                'message': '订单不存在'
            }), 404
        
        # 返回订单基本信息
        status_map = {
            'pending': '待支付',
            'paid': '已支付',
            'processing': '处理中',
            'completed': '已完成',
            'cancelled': '已取消',
            'error': '异常'
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': order.id,
                'order_number': order.order_number,
                'product_name': order.product_name or '未知产品',
                'price': float(order.price) if order.price else 0.0,
                'status': order.status,
                'status_text': status_map.get(order.status, order.status)
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'查询订单失败: {str(e)}'
        }), 500

@bp.route('/refund/check-permission', methods=['GET'])
def check_refund_permission():
    """检查用户是否有退款申请权限"""
    try:
        openid = request.args.get('openid', '')
        user_id = request.args.get('user_id', '')
        phone = request.args.get('phone', '')
        
        is_staff = check_staff_permission(openid, user_id, phone)
        
        return jsonify({
            'status': 'success',
            'data': {
                'has_permission': is_staff
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'检查权限失败: {str(e)}'
        }), 500
