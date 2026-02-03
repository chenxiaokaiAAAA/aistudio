# -*- coding: utf-8 -*-
"""
佣金提现相关API路由
包含：获取用户分佣数据、获取用户提现申请记录
"""
from flask import Blueprint, request, jsonify
import sys

# 导入主蓝图
from . import user_api_bp


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'PromotionUser': test_server_module.PromotionUser,
        'Commission': test_server_module.Commission,
        'Order': test_server_module.Order,
        'Withdrawal': test_server_module.Withdrawal,
    }


@user_api_bp.route('/commission', methods=['GET'])
def get_user_commission():
    """获取用户分佣数据"""
    try:
        user_id = request.args.get('userId')
        print(f"查询用户分佣: userId={user_id}")
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        PromotionUser = models['PromotionUser']
        Commission = models['Commission']
        Order = models['Order']
        Withdrawal = models['Withdrawal']
        
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        commissions = Commission.query.filter_by(referrer_user_id=user_id).order_by(Commission.create_time.desc()).all()
        
        orders = []
        total_commission = 0
        
        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order:
                if order.status == 'delivered':
                    commission_status = 'completed'
                    commission_status_text = '已结算'
                    total_commission += commission.amount
                else:
                    commission_status = 'pending'
                    commission_status_text = '待结算'
                
                orders.append({
                    'orderId': commission.order_id,
                    'productName': order.size or '定制产品',
                    'totalPrice': float(order.price or 0),
                    'commissionAmount': float(commission.amount),
                    'commissionStatus': commission_status,
                    'commissionStatusText': commission_status_text,
                    'createTime': commission.create_time.strftime('%Y-%m-%d %H:%M:%S') if commission.create_time else '',
                    'completeTime': commission.complete_time.strftime('%Y-%m-%d %H:%M:%S') if commission.complete_time else ''
                })
        
        withdrawals = Withdrawal.query.filter_by(user_id=user_id).all()
        total_withdrawn = sum(withdrawal.amount for withdrawal in withdrawals if withdrawal.status == 'approved')
        available_earnings = total_commission - total_withdrawn
        
        return jsonify({
            'success': True,
            'totalEarnings': available_earnings,
            'totalCommission': total_commission,
            'totalWithdrawn': total_withdrawn,
            'totalOrders': user.total_orders,
            'orders': orders,
            'commissions': [
                {
                    'id': c.id,
                    'orderId': c.order_id,
                    'amount': c.amount,
                    'rate': c.rate,
                    'status': c.status,
                    'createTime': c.create_time.isoformat() if c.create_time else None,
                    'completeTime': c.complete_time.isoformat() if c.complete_time else None
                } for c in commissions
            ]
        })
        
    except Exception as e:
        print(f"获取分佣数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取分佣数据失败: {str(e)}'
        }), 500


@user_api_bp.route('/withdrawals', methods=['GET'])
def get_user_withdrawals():
    """获取用户提现申请记录"""
    try:
        user_id = request.args.get('userId')
        print(f"查询用户提现记录: userId={user_id}")
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Withdrawal = models['Withdrawal']
        
        withdrawals = Withdrawal.query.filter_by(user_id=user_id).order_by(Withdrawal.apply_time.desc()).all()
        
        status_map = {
            'pending': '待审核',
            'approved': '审核通过',
            'rejected': '审核拒绝',
            'completed': '已完成'
        }
        
        withdrawal_list = []
        for withdrawal in withdrawals:
            withdrawal_list.append({
                'id': withdrawal.id,
                'amount': float(withdrawal.amount),
                'status': withdrawal.status,
                'statusText': status_map.get(withdrawal.status, '未知状态'),
                'applyTime': withdrawal.apply_time.strftime('%Y-%m-%d %H:%M:%S') if withdrawal.apply_time else '',
                'approveTime': withdrawal.approve_time.strftime('%Y-%m-%d %H:%M:%S') if withdrawal.approve_time else '',
                'adminNotes': withdrawal.admin_notes or ''
            })
        
        return jsonify({
            'success': True,
            'withdrawals': withdrawal_list
        })
        
    except Exception as e:
        print(f"获取提现记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取提现记录失败: {str(e)}'
        }), 500
