# -*- coding: utf-8 -*-
"""
用户相关API路由模块
从 test_server.py 迁移所有 /api/user/* 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
import json
import time
import random
import string
import requests
import base64

# 尝试导入 Crypto（可选）
try:
    from Crypto.Cipher import AES
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  Crypto模块未安装，手机号解密功能将不可用。请安装: pip install pycryptodome")

# 创建蓝图
user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/user')


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'User': test_server_module.User,
        'Order': test_server_module.Order,
        'PromotionUser': test_server_module.PromotionUser,
        'PromotionTrack': test_server_module.PromotionTrack,
        'Commission': test_server_module.Commission,
        'Withdrawal': test_server_module.Withdrawal,
        'UserVisit': test_server_module.UserVisit,
        'WECHAT_PAY_CONFIG': test_server_module.WECHAT_PAY_CONFIG,
        'get_user_openid_service': test_server_module.get_user_openid_service,
    }


def get_utils():
    """获取工具函数（延迟导入）"""
    from app.utils.helpers import (
        check_user_has_placed_order,
        validate_promotion_code,
        generate_promotion_code,
        generate_stable_promotion_code,
        generate_stable_user_id,
    )
    return {
        'check_user_has_placed_order': check_user_has_placed_order,
        'validate_promotion_code': validate_promotion_code,
        'generate_promotion_code': generate_promotion_code,
        'generate_stable_promotion_code': generate_stable_promotion_code,
        'generate_stable_user_id': generate_stable_user_id,
    }


@user_api_bp.route('/openid', methods=['POST'])
def get_user_openid():
    """获取用户openid接口"""
    # ========== 开发模式：跳过真实openid验证 ==========
    DEV_MODE_SKIP_OPENID = True  # ⚠️ 上线前改为 False
    # ========== 开发模式结束 ==========
    
    try:
        data = request.get_json()
        code = data.get('code')
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        get_user_openid_service = models['get_user_openid_service']
        
        # 调用服务层函数
        success, result, error_message = get_user_openid_service(code, dev_mode=DEV_MODE_SKIP_OPENID)
        
        if success:
            return jsonify({
                'success': True,
                **result
            })
        else:
            return jsonify({
                'success': False,
                'message': error_message
            }), 400
            
    except Exception as e:
        print(f"获取openid异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取openid失败: {str(e)}'
        }), 500


@user_api_bp.route('/register', methods=['POST'])
def register_user():
    """小程序用户注册接口"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        promotion_code = data.get('promotionCode')
        open_id = data.get('openId')
        user_info = data.get('userInfo', {})
        promotion_params = data.get('promotion_params')
        
        print(f"用户注册请求: userId={user_id}, open_id={open_id}, promotion_params={promotion_params}")
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        PromotionTrack = models['PromotionTrack']
        Order = models['Order']
        
        utils = get_utils()
        check_user_has_placed_order = utils['check_user_has_placed_order']
        validate_promotion_code = utils['validate_promotion_code']
        generate_promotion_code = utils['generate_promotion_code']
        generate_stable_promotion_code = utils['generate_stable_promotion_code']
        generate_stable_user_id = utils['generate_stable_user_id']
        
        # 优先使用小程序传入的userId
        if user_id:
            print(f"使用小程序传入的userId: {user_id}")
            existing_user = PromotionUser.query.filter_by(user_id=user_id).first()
            if existing_user:
                print(f"用户已存在: {existing_user.user_id}, 推广码: {existing_user.promotion_code}")
                # 处理推广参数（如果存在）
                if promotion_params:
                    try:
                        params = {}
                        for item in promotion_params.split('&'):
                            if '=' in item:
                                key, value = item.split('=', 1)
                                params[key] = value
                        referrer_promotion_code = params.get('p')
                        referrer_user_id = params.get('u')
                        if referrer_promotion_code and referrer_user_id:
                            if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                                existing_track = PromotionTrack.query.filter_by(
                                    visitor_user_id=existing_user.user_id,
                                    referrer_user_id=referrer_user_id
                                ).first()
                                if not existing_track:
                                    track = PromotionTrack(
                                        promotion_code=referrer_promotion_code,
                                        referrer_user_id=referrer_user_id,
                                        visitor_user_id=existing_user.user_id,
                                        visit_time=int(time.time())
                                    )
                                    db.session.add(track)
                                    db.session.commit()
                    except Exception as e:
                        print(f"处理已存在用户推广参数失败: {e}")
                
                return jsonify({
                    'success': True,
                    'message': '用户已存在',
                    'userId': existing_user.user_id,
                    'promotionCode': existing_user.promotion_code,
                    'isStable': False
                })
        
        # 如果没有userId，使用OpenID进行稳定绑定
        elif open_id:
            print(f"未提供userId，使用OpenID进行稳定绑定: {open_id}")
            existing_user = PromotionUser.query.filter_by(open_id=open_id).first()
            if existing_user:
                print(f"OpenID用户已存在: {existing_user.user_id}, 推广码: {existing_user.promotion_code}")
                # 处理推广参数（类似上面的逻辑）
                if promotion_params:
                    try:
                        params = {}
                        for item in promotion_params.split('&'):
                            if '=' in item:
                                key, value = item.split('=', 1)
                                params[key] = value
                        referrer_promotion_code = params.get('p')
                        referrer_user_id = params.get('u')
                        if referrer_promotion_code and referrer_user_id:
                            if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                                existing_track = PromotionTrack.query.filter_by(
                                    visitor_user_id=existing_user.user_id,
                                    referrer_user_id=referrer_user_id
                                ).first()
                                if not existing_track:
                                    track = PromotionTrack(
                                        promotion_code=referrer_promotion_code,
                                        referrer_user_id=referrer_user_id,
                                        visitor_user_id=existing_user.user_id,
                                        visit_time=int(time.time())
                                    )
                                    db.session.add(track)
                                    db.session.commit()
                    except Exception as e:
                        print(f"处理已存在用户推广参数失败: {e}")
                
                return jsonify({
                    'success': True,
                    'message': '用户已存在',
                    'userId': existing_user.user_id,
                    'promotionCode': existing_user.promotion_code,
                    'isStable': True
                })
            
            # 基于OpenID生成稳定的用户ID和推广码
            stable_user_id = generate_stable_user_id(open_id)
            stable_promotion_code = generate_stable_promotion_code(open_id)
            
            if not stable_user_id or not stable_promotion_code:
                return jsonify({
                    'success': False,
                    'message': '生成稳定用户信息失败'
                }), 500
            
            # 检查是否已存在
            existing_user_id = PromotionUser.query.filter_by(user_id=stable_user_id).first()
            existing_promotion_code = PromotionUser.query.filter_by(promotion_code=stable_promotion_code).first()
            
            if existing_user_id or existing_promotion_code:
                if existing_user_id:
                    return jsonify({
                        'success': True,
                        'message': '用户已存在',
                        'userId': existing_user_id.user_id,
                        'promotionCode': existing_user_id.promotion_code,
                        'isStable': True
                    })
            
            user_id = stable_user_id
            promotion_code = stable_promotion_code
            print(f"使用稳定用户信息: user_id={user_id}, promotion_code={promotion_code}")
        else:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        # 生成推广码（如果未提供）
        if not promotion_code:
            promotion_code = generate_promotion_code(user_id)
        
        # 只有下过单的用户才能享受推广码功能
        can_generate_promotion_code = check_user_has_placed_order(user_id)
        
        print(f"=== 用户推广资格检查 ===")
        print(f"用户ID: {user_id}")
        print(f"是否有下单记录: {can_generate_promotion_code}")
        
        # 创建用户记录
        final_promotion_code = promotion_code if can_generate_promotion_code else f"TEMP_{user_id[-6:]}"
        
        new_user = PromotionUser(
            user_id=user_id,
            promotion_code=final_promotion_code,
            open_id=open_id,
            nickname=user_info.get('nickName', ''),
            avatar_url=user_info.get('avatarUrl', ''),
            phone_number=data.get('phoneNumber', ''),
            total_earnings=0.0,
            total_orders=0,
            eligible_for_promotion=can_generate_promotion_code
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # 处理推广参数
        if promotion_params:
            try:
                params = {}
                for item in promotion_params.split('&'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        params[key] = value
                referrer_promotion_code = params.get('p')
                referrer_user_id = params.get('u')
                if referrer_promotion_code and referrer_user_id:
                    if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                        track = PromotionTrack(
                            promotion_code=referrer_promotion_code,
                            referrer_user_id=referrer_user_id,
                            visitor_user_id=user_id,
                            visit_time=int(time.time())
                        )
                        db.session.add(track)
                        db.session.commit()
            except Exception as e:
                print(f"处理推广参数失败: {e}")
        
        return jsonify({
            'success': True,
            'message': '用户注册成功',
            'userId': user_id,
            'promotionCode': promotion_code
        })
        
    except Exception as e:
        print(f"用户注册失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'用户注册失败: {str(e)}'
        }), 500


@user_api_bp.route('/update-info', methods=['POST'])
def update_user_info():
    """更新用户信息接口"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        user_info = data.get('userInfo', {})
        
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
        
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if user:
            if user_info.get('nickName'):
                user.nickname = user_info['nickName']
            if user_info.get('avatarUrl'):
                user.avatar_url = user_info['avatarUrl']
            user.update_time = datetime.now()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '用户信息更新成功',
                'data': {
                    'userId': user_id,
                    'nickname': user.nickname,
                    'avatarUrl': user.avatar_url
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
    except Exception as e:
        print(f"用户信息更新失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


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


@user_api_bp.route('/phone', methods=['POST'])
def get_user_phone():
    """解密获取用户手机号"""
    if not CRYPTO_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Crypto模块未安装，无法解密手机号。请安装: pip install pycryptodome'
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code')
        encrypted_data = data.get('encryptedData')
        iv = data.get('iv')
        
        if not all([code, encrypted_data, iv]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        WECHAT_PAY_CONFIG = models['WECHAT_PAY_CONFIG']
        
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': WECHAT_PAY_CONFIG['appid'],
            'secret': WECHAT_PAY_CONFIG['app_secret'],
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.get(url, params=params, timeout=(10, 30))
        
        if response.status_code == 200:
            result = response.json()
            if 'session_key' in result:
                session_key = result['session_key']
                
                # Base64解码
                encrypted_data_bytes = base64.b64decode(encrypted_data)
                iv_bytes = base64.b64decode(iv)
                session_key_bytes = base64.b64decode(session_key)
                
                # AES解密
                cipher = AES.new(session_key_bytes, AES.MODE_CBC, iv_bytes)
                decrypted_data = cipher.decrypt(encrypted_data_bytes)
                
                # 去除填充
                padding_length = decrypted_data[-1]
                decrypted_data = decrypted_data[:-padding_length]
                
                # 解析JSON
                phone_data = json.loads(decrypted_data.decode('utf-8'))
                phone_number = phone_data.get('phoneNumber')
                
                if phone_number:
                    return jsonify({
                        'success': True,
                        'phoneNumber': phone_number
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '解密失败，未获取到手机号'
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': result.get('errmsg', '获取session_key失败')
                }), 400
        else:
            return jsonify({
                'success': False,
                'message': '微信接口调用失败'
            }), 500
            
    except Exception as e:
        print(f"获取手机号失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取手机号失败: {str(e)}'
        }), 500


@user_api_bp.route('/subscription-status', methods=['POST'])
def update_subscription_status():
    """更新用户订阅状态 - 支付后订阅"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        open_id = data.get('openId')
        is_subscribed = data.get('isSubscribed')
        subscription_result = data.get('subscriptionResult')
        order_number = data.get('orderNumber')
        template_ids = data.get('templateIds', [])
        
        if not user_id and not open_id:
            return jsonify({
                'success': False,
                'message': '用户ID或OpenID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        Order = models['Order']
        
        utils = get_utils()
        check_user_has_placed_order = utils['check_user_has_placed_order']
        generate_stable_promotion_code = utils['generate_stable_promotion_code']
        
        promotion_user = None
        if open_id:
            promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
        elif user_id:
            promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        
        if promotion_user:
            if order_number:
                order = Order.query.filter_by(order_number=order_number).first()
                if order and order.status == 'pending':
                    has_order = check_user_has_placed_order(promotion_user.user_id)
                    if not promotion_user.eligible_for_promotion and has_order:
                        promotion_user.eligible_for_promotion = True
                        if not promotion_user.promotion_code:
                            promotion_code = generate_stable_promotion_code(promotion_user.open_id)
                            promotion_user.promotion_code = promotion_code
            promotion_user.update_time = datetime.now()
            db.session.commit()
        
        if is_subscribed:
            message = f"订阅成功！您将收到订单 {order_number} 的制作进度通知。"
            if promotion_user and promotion_user.eligible_for_promotion:
                message += f"同时恭喜您获得推广资格，推广码: {promotion_user.promotion_code}"
        else:
            message = "如需接收订单进度通知，请允许订阅消息。您也可以手动关注订单状态。"
        
        return jsonify({
            'success': True,
            'message': message,
            'subscriptionStatus': is_subscribed,
            'orderNumber': order_number,
            'promotionCode': promotion_user.promotion_code if promotion_user else None,
            'eligibleForPromotion': promotion_user.eligible_for_promotion if promotion_user else False
        })
        
    except Exception as e:
        print(f"更新订阅状态失败: {str(e)}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新订阅状态失败: {str(e)}'
        }), 500


@user_api_bp.route('/update-phone', methods=['POST'])
def update_user_phone():
    """更新用户手机号"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        phone_number = data.get('phoneNumber')
        
        if not user_id or not phone_number:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        
        promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        if promotion_user:
            promotion_user.phone_number = phone_number
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '手机号更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
    except Exception as e:
        print(f"更新手机号失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新手机号失败: {str(e)}'
        }), 500


@user_api_bp.route('/visit', methods=['POST'])
def record_user_visit():
    """记录用户访问（支持完整访问追踪）"""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        openid = data.get('openId')
        user_id = data.get('userId')
        visit_type = data.get('visitType', 'launch')
        promotion_code = data.get('promotionCode')
        referrer_user_id = data.get('referrerUserId')
        scene = data.get('scene')
        user_info = data.get('userInfo', {})
        page_path = data.get('pagePath', '')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': '会话ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        PromotionTrack = models['PromotionTrack']
        
        assigned_promotion_code = None
        
        if openid:
            user_result = db.session.execute(
                db.text("SELECT promotion_code FROM promotion_users WHERE open_id = :openid"),
                {'openid': openid}
            ).fetchone()
            
            if user_result:
                assigned_promotion_code = user_result[0]
            else:
                if promotion_code:
                    assigned_promotion_code = promotion_code
                else:
                    assigned_promotion_code = f"PET{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
                    try:
                        db.session.execute(
                            db.text("""
                                INSERT INTO promotion_users 
                                (user_id, promotion_code, open_id, nickname, avatar_url, phone_number, 
                                 total_earnings, total_orders, eligible_for_promotion, create_time, update_time)
                                VALUES (:user_id, :promotion_code, :open_id, :nickname, :avatar_url, :phone_number,
                                        0.0, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """),
                            {
                                'user_id': user_id or f"USER{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}",
                                'promotion_code': assigned_promotion_code,
                                'open_id': openid,
                                'nickname': user_info.get('nickName', ''),
                                'avatar_url': user_info.get('avatarUrl', ''),
                                'phone_number': ''
                            }
                        )
                        db.session.commit()
                    except Exception as e:
                        print(f"⚠️ 创建用户记录失败: {e}")
        
        visit_id = None
        try:
            existing_visit = db.session.execute(
                db.text("""
                    SELECT id FROM user_access_logs 
                    WHERE session_id = :session_id 
                    AND visit_type = :visit_type 
                    AND visit_time >= datetime('now', '-5 minutes')
                """),
                {'session_id': session_id, 'visit_type': visit_type}
            ).fetchone()
            
            if existing_visit:
                visit_id = existing_visit[0]
            else:
                result = db.session.execute(
                    db.text("""
                        INSERT INTO user_access_logs 
                        (session_id, openid, user_id, temp_promotion_code, final_promotion_code,
                         visit_time, visit_type, source, scene, user_info, is_authorized, 
                         is_registered, has_ordered, ip_address, user_agent, page_path)
                        VALUES (:session_id, :openid, :user_id, :temp_promotion_code, :final_promotion_code,
                                CURRENT_TIMESTAMP, :visit_type, :source, :scene, :user_info, :is_authorized, 
                                :is_registered, :has_ordered, :ip_address, :user_agent, :page_path)
                    """),
                    {
                        'session_id': session_id, 'openid': openid, 'user_id': user_id,
                        'temp_promotion_code': promotion_code, 'final_promotion_code': assigned_promotion_code,
                        'visit_type': visit_type, 'source': 'miniprogram', 'scene': scene,
                        'user_info': json.dumps(user_info) if user_info else None,
                        'is_authorized': bool(openid), 'is_registered': bool(user_id),
                        'has_ordered': (visit_type == 'order'), 'ip_address': ip_address,
                        'user_agent': user_agent, 'page_path': page_path
                    }
                )
                db.session.commit()
                visit_id = db.session.execute(db.text("SELECT last_insert_rowid()")).fetchone()[0]
        except Exception as e:
            print(f"❌ 记录访问失败: {e}")
            db.session.rollback()
        
        if visit_type == 'scan' and assigned_promotion_code:
            try:
                existing_track = db.session.execute(
                    db.text("SELECT id FROM promotion_tracks WHERE promotion_code = :code AND visitor_user_id = :visitor"),
                    {'code': assigned_promotion_code, 'visitor': session_id}
                ).fetchone()
                
                if not existing_track:
                    track = PromotionTrack(
                        promotion_code=assigned_promotion_code,
                        referrer_user_id=referrer_user_id or 'OFFICIAL',
                        visitor_user_id=session_id,
                        visit_time=int(datetime.now().timestamp() * 1000)
                    )
                    db.session.add(track)
                    db.session.commit()
            except Exception as e:
                print(f"⚠️ 推广追踪记录失败: {e}")
                db.session.rollback()
        
        return jsonify({
            'success': True,
            'message': '用户访问记录成功',
            'visitId': visit_id,
            'promotionCode': assigned_promotion_code,
            'isNewUser': assigned_promotion_code is not None
        })
        
    except Exception as e:
        print(f"❌ 记录用户访问失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'记录用户访问失败: {str(e)}'
        }), 500


@user_api_bp.route('/visit/stats', methods=['GET'])
def get_user_visit_stats():
    """获取用户访问统计"""
    try:
        from sqlalchemy import func
        
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        UserVisit = models['UserVisit']
        db = models['db']
        
        query = UserVisit.query
        
        if start_date:
            query = query.filter(UserVisit.visit_time >= start_date)
        if end_date:
            query = query.filter(UserVisit.visit_time <= end_date)
        
        total_visits = query.count()
        authorized_visits = query.filter(UserVisit.is_authorized == True).count()
        registered_visits = query.filter(UserVisit.is_registered == True).count()
        ordered_visits = query.filter(UserVisit.has_ordered == True).count()
        
        daily_stats = db.session.query(
            func.date(UserVisit.visit_time).label('date'),
            func.count(UserVisit.id).label('total'),
            func.count(func.case([(UserVisit.is_authorized == True, 1)])).label('authorized'),
            func.count(func.case([(UserVisit.is_registered == True, 1)])).label('registered'),
            func.count(func.case([(UserVisit.has_ordered == True, 1)])).label('ordered')
        ).group_by(func.date(UserVisit.visit_time)).order_by('date').all()
        
        return jsonify({
            'success': True,
            'data': {
                'totalVisits': total_visits,
                'authorizedVisits': authorized_visits,
                'registeredVisits': registered_visits,
                'orderedVisits': ordered_visits,
                'dailyStats': [
                    {
                        'date': str(stat.date),
                        'total': stat.total,
                        'authorized': stat.authorized,
                        'registered': stat.registered,
                        'ordered': stat.ordered
                    }
                    for stat in daily_stats
                ]
            }
        })
        
    except Exception as e:
        print(f"❌ 获取用户访问统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户访问统计失败: {str(e)}'
        }), 500


@user_api_bp.route('/messages/unread-count', methods=['GET'])
def get_unread_message_count():
    """获取用户未读消息数量"""
    try:
        user_id = request.args.get('userId')
        session_id = request.args.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        result = db.session.execute(
            db.text("""
                SELECT COUNT(*) FROM user_messages 
                WHERE (user_id = :user_id OR session_id = :session_id) 
                AND is_read = 0
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        count = result.fetchone()[0]
        
        return jsonify({
            "success": True,
            "unreadCount": count
        })
        
    except Exception as e:
        print(f"❌ 获取未读消息数量失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_api_bp.route('/messages', methods=['GET'])
def get_user_messages():
    """获取用户消息列表"""
    try:
        user_id = request.args.get('userId')
        session_id = request.args.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        result = db.session.execute(
            db.text("""
                SELECT 
                    id,
                    title,
                    content,
                    message_type,
                    action,
                    url,
                    is_read,
                    created_at
                FROM user_messages 
                WHERE user_id = :user_id OR session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        messages = []
        for row in result.fetchall():
            messages.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "type": row[3],
                "action": row[4],
                "url": row[5],
                "isRead": bool(row[6]),
                "time": row[7]
            })
        
        return jsonify({
            "success": True,
            "messages": messages
        })
        
    except Exception as e:
        print(f"❌ 获取消息列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_api_bp.route('/messages/read', methods=['POST'])
def mark_messages_as_read():
    """标记消息为已读"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        session_id = data.get('sessionId')
        
        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        
        result = db.session.execute(
            db.text("""
                UPDATE user_messages 
                SET is_read = 1, read_at = CURRENT_TIMESTAMP
                WHERE (user_id = :user_id OR session_id = :session_id) 
                AND is_read = 0
            """),
            {'user_id': user_id, 'session_id': session_id}
        )
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "消息已标记为已读",
            "updatedCount": result.rowcount
        })
        
    except Exception as e:
        print(f"❌ 标记消息为已读失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
