# -*- coding: utf-8 -*-
"""
加盟商API路由
包含额度检查、扣除、账户信息等API接口
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.routes.franchisee.common import get_models, get_wechat_notification

# 创建API路由子蓝图
bp = Blueprint('franchisee_api', __name__)


@bp.route('/api/check-quota', methods=['POST'])
def api_check_quota():
    """检查加盟商额度API"""
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    FranchiseeAccount = models['FranchiseeAccount']
    
    try:
        data = request.get_json()
        qr_code = data.get('qr_code')
        order_amount = float(data.get('order_amount', 0))
        
        if not qr_code or order_amount <= 0:
            return jsonify({'success': False, 'message': '参数错误'}), 400
        
        account = FranchiseeAccount.query.filter_by(qr_code=qr_code, status='active').first()
        
        if not account:
            return jsonify({'success': False, 'message': '加盟商账户不存在或已禁用'}), 404
        
        if account.remaining_quota < order_amount:
            return jsonify({
                'success': False, 
                'message': f'额度不足，当前剩余额度: {account.remaining_quota} 元',
                'remaining_quota': account.remaining_quota
            }), 400
        
        return jsonify({
            'success': True,
            'franchisee_id': account.id,
            'company_name': account.company_name,
            'remaining_quota': account.remaining_quota
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500


@bp.route('/api/deduct-quota', methods=['POST'])
def api_deduct_quota():
    """扣除加盟商额度API"""
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    FranchiseeAccount = models['FranchiseeAccount']
    Order = models['Order']
    db = models['db']
    
    try:
        data = request.get_json()
        franchisee_id = data.get('franchisee_id')
        order_id = data.get('order_id')
        amount = float(data.get('amount', 0))
        
        if not franchisee_id or not order_id or amount <= 0:
            return jsonify({'success': False, 'message': '参数错误'}), 400
        
        account = FranchiseeAccount.query.get(franchisee_id)
        if not account or account.status != 'active':
            return jsonify({'success': False, 'message': '加盟商账户不存在或已禁用'}), 404
        
        if account.remaining_quota < amount:
            return jsonify({'success': False, 'message': '额度不足'}), 400
        
        account.used_quota += amount
        account.remaining_quota -= amount
        
        order = Order.query.get(order_id)
        if order:
            order.franchisee_id = franchisee_id
            order.franchisee_deduction = amount
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'remaining_quota': account.remaining_quota,
            'message': f'成功扣除 {amount} 元，剩余额度: {account.remaining_quota} 元'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500


@bp.route('/api/account-info/<qr_code>')
def api_account_info(qr_code):
    """获取加盟商账户信息API"""
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    FranchiseeAccount = models['FranchiseeAccount']
    
    try:
        account = FranchiseeAccount.query.filter_by(qr_code=qr_code, status='active').first()
        
        if not account:
            return jsonify({'success': False, 'message': '加盟商账户不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': account.id,
                'company_name': account.company_name,
                'contact_person': account.contact_person,
                'contact_phone': account.contact_phone,
                'remaining_quota': account.remaining_quota,
                'total_quota': account.total_quota,
                'used_quota': account.used_quota
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500


@bp.route('/api/cancel-order/<int:order_id>', methods=['POST'])
@login_required
def cancel_franchisee_order(order_id):
    """取消加盟商订单并返还资金"""
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    FranchiseeAccount = models['FranchiseeAccount']
    FranchiseeRecharge = models['FranchiseeRecharge']
    db = models['db']
    
    try:
        order = Order.query.get_or_404(order_id)
        
        if not order.franchisee_id:
            return jsonify({
                'success': False,
                'message': '该订单不是加盟商订单'
            }), 400
        
        if order.status == 'cancelled':
            return jsonify({
                'success': False,
                'message': '订单已经取消'
            }), 400
        
        if order.status == 'completed' or order.status == 'shipped':
            return jsonify({
                'success': False,
                'message': '已完成的订单不能取消'
            }), 400
        
        data = request.get_json()
        reason = data.get('reason', '管理员取消订单') if data else '管理员取消订单'
        
        account = FranchiseeAccount.query.get(order.franchisee_id)
        if not account:
            return jsonify({
                'success': False,
                'message': '加盟商账户不存在'
            }), 400
        
        refund_amount = order.franchisee_deduction or order.price
        account.used_quota -= refund_amount
        account.remaining_quota += refund_amount
        
        recharge_record = FranchiseeRecharge(
            franchisee_id=order.franchisee_id,
            amount=refund_amount,
            admin_user_id=current_user.id,
            recharge_type='refund',
            description=f'订单 {order.order_number} 取消退款 - {reason}'
        )
        db.session.add(recharge_record)
        
        order.status = 'cancelled'
        
        db.session.commit()
        
        print(f"✅ 订单已取消: {order.order_number}, 返还金额: {refund_amount}")
        
        return jsonify({
            'success': True,
            'message': '订单已取消，资金已返还',
            'refund_amount': refund_amount
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 取消订单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'取消订单失败: {str(e)}'
        }), 500
