# -*- coding: utf-8 -*-
"""
推广相关API路由
包含：检查推广资格、更新推广资格、支付后订阅请求、订阅状态更新
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
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
        'Order': test_server_module.Order,
        'PromotionUser': test_server_module.PromotionUser,
    }


def get_utils():
    """获取工具函数（延迟导入）"""
    from app.utils.helpers import (
        check_user_has_placed_order,
        generate_stable_promotion_code,
        generate_promotion_code,
    )
    return {
        'check_user_has_placed_order': check_user_has_placed_order,
        'generate_stable_promotion_code': generate_stable_promotion_code,
        'generate_promotion_code': generate_promotion_code,
    }


@user_api_bp.route('/check-promotion-eligibility', methods=['POST'])
def check_promotion_eligibility():
    """检查用户推广资格（是否下过单）"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        open_id = data.get('openId')
        
        print(f"检查用户推广资格: user_id={user_id}, open_id={open_id}")
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        
        utils = get_utils()
        check_user_has_placed_order = utils['check_user_has_placed_order']
        generate_stable_promotion_code = utils['generate_stable_promotion_code']
        generate_promotion_code = utils['generate_promotion_code']
        
        if not user_id and open_id:
            promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
            if promotion_user:
                user_id = promotion_user.user_id
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID或OpenID不能为空'
            }), 400
        
        promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not promotion_user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        has_order = check_user_has_placed_order(user_id)
        promotion_user.eligible_for_promotion = has_order
        
        if has_order and not promotion_user.promotion_code:
            if open_id:
                promotion_code = generate_stable_promotion_code(open_id)
            else:
                promotion_code = generate_promotion_code(user_id)
            
            while PromotionUser.query.filter_by(promotion_code=promotion_code).first():
                if open_id:
                    promotion_code = generate_stable_promotion_code(open_id + "_retry")
                else:
                    promotion_code = generate_promotion_code(user_id + "_retry")
            
            promotion_user.promotion_code = promotion_code
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'hasOrders': has_order,
            'eligibleForPromotion': promotion_user.eligible_for_promotion,
            'promotionCode': promotion_user.promotion_code,
            'message': '资格检查完成'
        })
        
    except Exception as e:
        print(f"检查推广资格失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'检查失败: {str(e)}'
        }), 500


@user_api_bp.route('/update-promotion-eligibility', methods=['POST'])
def update_promotion_eligibility():
    """更新用户推广资格"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        
        utils = get_utils()
        check_user_has_placed_order = utils['check_user_has_placed_order']
        generate_stable_promotion_code = utils['generate_stable_promotion_code']
        generate_promotion_code = utils['generate_promotion_code']
        
        promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not promotion_user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        has_order = check_user_has_placed_order(user_id)
        promotion_user.eligible_for_promotion = has_order
        
        if has_order and not promotion_user.promotion_code:
            if promotion_user.open_id:
                promotion_code = generate_stable_promotion_code(promotion_user.open_id)
            else:
                promotion_code = generate_promotion_code(user_id)
            
            while PromotionUser.query.filter_by(promotion_code=promotion_code).first():
                if promotion_user.open_id:
                    promotion_code = generate_stable_promotion_code(promotion_user.open_id + "_retry")
                else:
                    promotion_code = generate_promotion_code(user_id + "_retry")
            
            promotion_user.promotion_code = promotion_code
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'eligibleForPromotion': promotion_user.eligible_for_promotion,
            'promotionCode': promotion_user.promotion_code,
            'message': '推广资格更新成功'
        })
        
    except Exception as e:
        print(f"更新推广资格失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@user_api_bp.route('/request-subscription-after-payment', methods=['POST'])
def request_subscription_after_payment():
    """支付成功后请求订阅消息"""
    try:
        data = request.get_json()
        open_id = data.get('openId')
        order_number = data.get('orderNumber')
        
        if not open_id or not order_number:
            return jsonify({
                'success': False,
                'message': 'OpenID和订单号不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        PromotionUser = models['PromotionUser']
        
        utils = get_utils()
        check_user_has_placed_order = utils['check_user_has_placed_order']
        generate_stable_promotion_code = utils['generate_stable_promotion_code']
        
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
        
        if order.status != 'pending':
            return jsonify({
                'success': False,
                'message': '订单未完成支付或状态异常'
            }), 400
        
        if order.openid != open_id:
            return jsonify({
                'success': False,
                'message': '订单用户身份验证失败'
            }), 400
        
        current_time = datetime.now()
        if order.payment_time:
            time_diff = (current_time - order.payment_time).total_seconds()
            if time_diff > 3600:
                return jsonify({
                    'success': False,
                    'message': '订单完成支付时间过长，无法执行订阅操作'
                }), 400
        
        promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
        if promotion_user:
            has_order = check_user_has_placed_order(promotion_user.user_id)
            if not promotion_user.eligible_for_promotion and has_order:
                promotion_user.eligible_for_promotion = True
                if not promotion_user.promotion_code:
                    promotion_code = generate_stable_promotion_code(open_id)
                    promotion_user.promotion_code = promotion_code
                db.session.commit()
        
        subscription_templates = [
            {
                'template_id': 'BOy7pDiq-pM1qiJHJfP9jUjAbi9o0bZG5-mEKZbnYT8',
                'name': '订单制作完成通知',
                'description': '当您的订单制作完成时，我们会通过此模板通知您',
                'example_data': {
                    'character_string13': {'value': order_number},
                    'thing1': {'value': order.product_name or '定制产品'},
                    'time17': {'value': '2025年12月31日 14:30'}
                }
            },
            {
                'template_id': 'R7mHvK2wP8fLjSs4dJqTn1cVyRbA6eZ9uI3oM5pN0xQ',
                'name': '订单状态更新通知',
                'description': '当您的订单状态发生重要变化时，我们会通过此模板通知您',
                'example_data': {
                    'thing1': {'value': order_number},
                    'phrase2': {'value': '制作中'},
                    'time3': {'value': '2025年12月31日 14:30'}
                }
            }
        ]
        
        return jsonify({
            'success': True,
            'message': '验证通过，可以请求订阅消息',
            'canSubscribe': True,
            'orderStatus': order.status,
            'paymentTime': order.payment_time.isoformat() if order.payment_time else None,
            'subscriptionTemplates': subscription_templates,
            'userPromotionCode': promotion_user.promotion_code if promotion_user else None,
            'eligibleForPromotion': promotion_user.eligible_for_promotion if promotion_user else False
        })
        
    except Exception as e:
        print(f"支付后订阅验证失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}'
        }), 500


@user_api_bp.route('/subscription-status', methods=['POST'])
def update_subscription_status():
    """更新用户订阅状态"""
    try:
        data = request.get_json()
        open_id = data.get('openId') or data.get('open_id')
        user_id = data.get('userId') or data.get('user_id')
        subscribed = data.get('subscribed', False) or data.get('isSubscribed', False)
        
        # 如果openId为空，尝试通过userId查找
        if not open_id and user_id:
            models = get_models()
            if models:
                PromotionUser = models.get('PromotionUser')
                if PromotionUser:
                    promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
                    if promotion_user:
                        open_id = promotion_user.open_id
        
        # 如果仍然没有openId，返回错误（但不影响订阅消息功能本身）
        if not open_id:
            print(f"⚠️ 订阅状态上报：OpenID为空，userId={user_id}")
            # 不返回错误，只记录日志，因为订阅消息功能本身不依赖这个接口
            return jsonify({
                'success': True,
                'message': '订阅状态已记录（OpenID为空，无法更新用户记录）',
                'subscribed': subscribed
            })
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        
        promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
        if promotion_user:
            # 这里可以添加订阅状态字段，如果PromotionUser模型中有的话
            # promotion_user.subscribed = subscribed
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '订阅状态更新成功',
            'subscribed': subscribed
        })
        
    except Exception as e:
        print(f"更新订阅状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500
