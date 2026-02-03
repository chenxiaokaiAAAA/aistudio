# -*- coding: utf-8 -*-
"""
优惠券相关API路由
包含：获取用户可领取的优惠券数量
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
        'Coupon': getattr(test_server_module, 'Coupon', None),
        'UserCoupon': getattr(test_server_module, 'UserCoupon', None),
    }


@user_api_bp.route('/coupons/available-count', methods=['GET'])
def get_available_coupon_count():
    """获取用户可领取的优惠券数量"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': True,
                'availableCount': 0
            })
        
        Coupon = models.get('Coupon')
        UserCoupon = models.get('UserCoupon')
        
        # 如果优惠券模型不存在，返回0
        if not Coupon or not UserCoupon:
            return jsonify({
                'success': True,
                'availableCount': 0
            })
        
        db = models['db']
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': True,
                'availableCount': 0
            })
        
        # 查询可领取的优惠券（状态为active，在有效期内，还有剩余数量）
        now = datetime.now()
        available_coupons = Coupon.query.filter(
            Coupon.status == 'active',
            Coupon.start_time <= now,
            Coupon.end_time > now
        ).all()
        
        available_count = 0
        for coupon in available_coupons:
            # 检查用户是否已经领取过
            user_coupon_count = UserCoupon.query.filter_by(
                user_id=user_id,
                coupon_id=coupon.id
            ).count()
            
            # 检查是否达到每用户限领数量
            if user_coupon_count < coupon.per_user_limit:
                # 计算剩余数量
                claimed_count = UserCoupon.query.filter_by(coupon_id=coupon.id).count()
                remaining_count = max(0, (coupon.total_count or 0) - claimed_count)
                
                # 如果还有剩余数量，则计入可领取数量
                if remaining_count > 0:
                    available_count += 1
        
        return jsonify({
            'success': True,
            'availableCount': available_count
        })
        
    except Exception as e:
        print(f'❌ 获取可用优惠券数量失败: {str(e)}')
        # 即使出错也返回0，避免前端报错
        return jsonify({
            'success': True,
            'availableCount': 0
        })
