# -*- coding: utf-8 -*-
"""
推广相关API路由模块
从 test_server.py 迁移所有 /api/promotion/* 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
import time

# 创建蓝图
promotion_api_bp = Blueprint('promotion_api', __name__, url_prefix='/api/promotion')


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'PromotionUser': test_server_module.PromotionUser,
        'PromotionTrack': test_server_module.PromotionTrack,
        'Commission': test_server_module.Commission,
    }


def get_utils():
    """获取工具函数（延迟导入）"""
    from app.utils.helpers import (
        validate_promotion_code,
    )
    return {
        'validate_promotion_code': validate_promotion_code,
    }


@promotion_api_bp.route('/bind', methods=['POST'])
def bind_promotion_relation():
    """推广关系绑定接口"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        promotion_params = data.get('promotion_params')
        
        print(f"推广关系绑定请求: userId={user_id}, promotion_params={promotion_params}")
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        if not promotion_params:
            return jsonify({
                'success': False,
                'message': '缺少推广参数'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionTrack = models['PromotionTrack']
        
        utils = get_utils()
        validate_promotion_code = utils['validate_promotion_code']
        
        # 解析推广参数
        params = {}
        for item in promotion_params.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                params[key] = value
        
        promotion_code = params.get('p')
        referrer_user_id = params.get('u')
        
        print(f"解析推广参数: promotion_code={promotion_code}, referrer_user_id={referrer_user_id}")
        
        if promotion_code and referrer_user_id:
            # 验证推广码有效性
            if validate_promotion_code(promotion_code) != referrer_user_id:
                return jsonify({
                    'success': False,
                    'message': '推广码无效'
                }), 400
            
            # 检查是否已经绑定过
            existing_track = PromotionTrack.query.filter_by(
                visitor_user_id=user_id,
                referrer_user_id=referrer_user_id
            ).first()
            
            if existing_track:
                print(f"推广关系已存在: {referrer_user_id} -> {user_id}")
                return jsonify({
                    'success': True,
                    'message': '推广关系已存在'
                })
            
            # 绑定推广关系
            track = PromotionTrack(
                promotion_code=promotion_code,
                referrer_user_id=referrer_user_id,
                visitor_user_id=user_id,
                visit_time=int(time.time())
            )
            
            db.session.add(track)
            db.session.commit()
            print(f'推广关系绑定成功：推广者={referrer_user_id}, 用户={user_id}')
            
            return jsonify({
                'success': True,
                'message': '推广关系绑定成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '推广参数解析失败'
            }), 400
            
    except Exception as e:
        print(f"推广关系绑定失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'绑定失败: {str(e)}'
        }), 500


@promotion_api_bp.route('/track', methods=['POST'])
def track_promotion():
    """推广访问追踪接口"""
    try:
        data = request.get_json()
        promotion_code = data.get('promotionCode')
        referrer_user_id = data.get('referrerUserId')
        visitor_user_id = data.get('visitorUserId')
        visit_time = data.get('visitTime', int(time.time()))
        
        if not promotion_code or not referrer_user_id:
            return jsonify({
                'success': False,
                'message': '推广码和推广者用户ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionTrack = models['PromotionTrack']
        
        # 记录推广访问
        track = PromotionTrack(
            promotion_code=promotion_code,
            referrer_user_id=referrer_user_id,
            visitor_user_id=visitor_user_id,
            visit_time=visit_time
        )
        
        db.session.add(track)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '推广访问记录成功'
        })
        
    except Exception as e:
        print(f"推广访问记录失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'推广访问记录失败: {str(e)}'
        }), 500


@promotion_api_bp.route('/validate', methods=['POST'])
def validate_promotion_code_api():
    """验证推广码有效性"""
    try:
        data = request.get_json()
        promotion_code = data.get('promotionCode')
        
        if not promotion_code:
            return jsonify({
                'success': False,
                'message': '推广码不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        PromotionUser = models['PromotionUser']
        
        utils = get_utils()
        validate_promotion_code = utils['validate_promotion_code']
        
        # 验证推广码
        user_id = validate_promotion_code(promotion_code)
        
        if user_id:
            user = PromotionUser.query.filter_by(user_id=user_id).first()
            return jsonify({
                'success': True,
                'message': '推广码有效',
                'promotionCode': promotion_code,
                'referrerUserId': user_id,
                'referrerInfo': {
                    'nickname': user.nickname,
                    'avatarUrl': user.avatar_url
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '推广码无效'
            }), 404
        
    except Exception as e:
        print(f"验证推广码失败: {e}")
        return jsonify({
            'success': False,
            'message': f'验证推广码失败: {str(e)}'
        }), 500


@promotion_api_bp.route('/stats', methods=['GET'])
def get_promotion_stats():
    """获取推广统计信息"""
    try:
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        PromotionUser = models['PromotionUser']
        PromotionTrack = models['PromotionTrack']
        Commission = models['Commission']
        
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 获取推广访问统计
        total_visits = PromotionTrack.query.filter_by(referrer_user_id=user_id).count()
        
        # 获取分佣统计
        total_commissions = Commission.query.filter_by(referrer_user_id=user_id).count()
        completed_commissions = Commission.query.filter_by(referrer_user_id=user_id, status='completed').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'promotionCode': user.promotion_code,
                'totalVisits': total_visits,
                'totalCommissions': total_commissions,
                'completedCommissions': completed_commissions,
                'totalEarnings': user.total_earnings,
                'totalOrders': user.total_orders
            }
        })
        
    except Exception as e:
        print(f"获取推广统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取推广统计失败: {str(e)}'
        }), 500


@promotion_api_bp.route('/test/commission', methods=['POST'])
def test_commission():
    """测试分佣功能"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        promotion_code = data.get('promotionCode')
        test_amount = data.get('testAmount', 100)
        
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
        Commission = models['Commission']
        
        # 检查用户是否存在
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 创建测试订单
        order_id = f'TEST{int(time.time())}'
        commission_rate = 0.2  # 20%
        commission_amount = test_amount * commission_rate
        
        # 插入分佣记录
        commission = Commission(
            order_id=order_id,
            referrer_user_id=user_id,
            amount=commission_amount,
            rate=commission_rate,
            status='completed',
            complete_time=datetime.now()
        )
        
        db.session.add(commission)
        
        # 更新用户总收益
        user.total_earnings += commission_amount
        user.total_orders += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '测试分佣创建成功',
            'orderId': order_id,
            'commissionAmount': commission_amount,
            'totalEarnings': user.total_earnings
        })
        
    except Exception as e:
        print(f"测试分佣失败: {e}")
        models = get_models()
        if models:
            models['db'].session.rollback()
        return jsonify({
            'success': False,
            'message': f'测试分佣失败: {str(e)}'
        }), 500
