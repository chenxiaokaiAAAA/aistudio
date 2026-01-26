# -*- coding: utf-8 -*-
"""
小程序分享奖励相关路由
"""
from flask import Blueprint, request, jsonify
from app.routes.miniprogram.common import get_models, get_helper_functions
from datetime import datetime, timedelta
import sys
import random
import string

bp = Blueprint('share_reward', __name__)

def generate_random_code(length=8):
    """生成随机码"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@bp.route('/share/record', methods=['POST'])
def record_share():
    """记录分享行为"""
    try:
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        ShareRecord = models.get('ShareRecord')
        Coupon = models.get('Coupon')
        UserCoupon = models.get('UserCoupon')
        db = models['db']
        
        if not ShareRecord:
            return jsonify({'status': 'error', 'message': '分享记录模型未初始化'}), 500
        
        data = request.get_json()
        sharer_user_id = data.get('sharer_user_id')
        work_id = data.get('work_id')
        share_type = data.get('share_type', 'work')
        
        if not sharer_user_id:
            return jsonify({'status': 'error', 'message': '缺少分享者用户ID'}), 400
        
        # 创建分享记录
        share_record = ShareRecord(
            sharer_user_id=sharer_user_id,
            share_type=share_type,
            work_id=work_id,
            status='pending'
        )
        
        db.session.add(share_record)
        db.session.commit()
        
        # 保存分享记录ID到本地存储（通过返回给前端）
        return jsonify({
            'status': 'success',
            'message': '分享记录已创建',
            'data': {
                'share_record_id': share_record.id
            }
        })
        
    except Exception as e:
        print(f"记录分享失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'记录分享失败: {str(e)}'}), 500

def process_share_reward_impl(data):
    """处理分享奖励的内部实现函数"""
    try:
        models = get_models()
        if not models:
            return {'status': 'error', 'message': '系统未初始化'}
        
        ShareRecord = models.get('ShareRecord')
        Coupon = models.get('Coupon')
        UserCoupon = models.get('UserCoupon')
        db = models['db']
        
        if not ShareRecord or not Coupon or not UserCoupon:
            return {'status': 'error', 'message': '数据库模型未初始化'}
        
        shared_user_id = data.get('shared_user_id')  # 被分享者（下单的用户）
        order_id = data.get('order_id')
        share_record_id = data.get('share_record_id')  # 分享记录ID（可选）
        work_id = data.get('work_id')  # 作品ID（可选）
        
        if not shared_user_id or not order_id:
            return {'status': 'error', 'message': '缺少必要参数'}
        
        # 查找分享记录
        share_record = None
        if share_record_id:
            share_record = ShareRecord.query.get(share_record_id)
        elif work_id:
            # 通过作品ID查找最近的分享记录
            share_record = ShareRecord.query.filter_by(
                work_id=work_id,
                status='pending'
            ).order_by(ShareRecord.created_at.desc()).first()
        
        if not share_record:
            # 如果没有找到分享记录，不发放奖励（可能是直接访问，不是通过分享）
            return {
                'status': 'success',
                'message': '未找到分享记录，不发放奖励',
                'data': {
                    'sharer_reward': False,
                    'shared_reward': False
                }
            }
        
        sharer_user_id = share_record.sharer_user_id
        
        # 检查是否已经处理过
        if share_record.status == 'completed':
            return {
                'status': 'success',
                'message': '该分享记录已处理',
                'data': {
                    'sharer_reward': False,
                    'shared_reward': False
                }
            }
        
        # 配置分享奖励金额（可以从系统配置中读取，这里使用默认值）
        sharer_reward_amount = 10.0  # 分享者奖励金额（可配置）
        shared_reward_amount = 5.0   # 被分享者奖励金额（可配置）
        expire_days = 30  # 优惠券有效期
        
        now = datetime.now()
        
        # 1. 为分享者创建优惠券
        sharer_coupon = None
        if sharer_user_id and sharer_user_id != shared_user_id:  # 不能自己分享给自己
            sharer_code = generate_random_code(8)
            while Coupon.query.filter_by(code=sharer_code).first():
                sharer_code = generate_random_code(8)
            
            sharer_coupon = Coupon(
                name=f'分享奖励券-{sharer_reward_amount}元',
                code=sharer_code,
                type='free',
                value=sharer_reward_amount,
                min_amount=0.0,
                total_count=1,
                used_count=0,
                per_user_limit=1,
                start_time=now,
                end_time=now + timedelta(days=expire_days),
                status='active',
                description=f'分享作品奖励，朋友下单后获得',
                source_type='share',
                share_reward_type='sharer',
                share_reward_amount=sharer_reward_amount
            )
            db.session.add(sharer_coupon)
            db.session.flush()
            
            # 发放给分享者
            sharer_user_coupon = UserCoupon(
                user_id=sharer_user_id,
                coupon_id=sharer_coupon.id,
                coupon_code=sharer_code,
                status='unused',
                expire_time=sharer_coupon.end_time
            )
            db.session.add(sharer_user_coupon)
        
        # 2. 为被分享者创建优惠券
        shared_coupon = None
        shared_code = generate_random_code(8)
        while Coupon.query.filter_by(code=shared_code).first():
            shared_code = generate_random_code(8)
        
        shared_coupon = Coupon(
            name=f'新用户专享券-{shared_reward_amount}元',
            code=shared_code,
            type='free',
            value=shared_reward_amount,
            min_amount=0.0,
            total_count=1,
            used_count=0,
            per_user_limit=1,
            start_time=now,
            end_time=now + timedelta(days=expire_days),
            status='active',
            description=f'通过朋友分享获得的新用户优惠券',
            source_type='share',
            share_reward_type='shared',
            share_reward_amount=shared_reward_amount
        )
        db.session.add(shared_coupon)
        db.session.flush()
        
        # 发放给被分享者
        shared_user_coupon = UserCoupon(
            user_id=shared_user_id,
            coupon_id=shared_coupon.id,
            coupon_code=shared_code,
            status='unused',
            expire_time=shared_coupon.end_time
        )
        db.session.add(shared_user_coupon)
        
        # 更新分享记录
        share_record.shared_user_id = shared_user_id
        share_record.order_id = order_id
        share_record.sharer_coupon_id = sharer_coupon.id if sharer_coupon else None
        share_record.shared_coupon_id = shared_coupon.id
        share_record.status = 'completed'
        
        db.session.commit()
        
        return {
            'status': 'success',
            'message': '分享奖励已发放',
            'data': {
                'sharer_reward': sharer_coupon is not None,
                'shared_reward': True,
                'sharer_coupon_code': sharer_code if sharer_coupon else None,
                'shared_coupon_code': shared_code
            }
        }
        
    except Exception as e:
        print(f"处理分享奖励失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return {'status': 'error', 'message': f'处理分享奖励失败: {str(e)}'}

@bp.route('/share/reward', methods=['POST'])
def process_share_reward():
    """处理分享奖励的HTTP接口"""
    data = request.get_json()
    result = process_share_reward_impl(data)
    if result.get('status') == 'error':
        return jsonify(result), 500
    return jsonify(result)
