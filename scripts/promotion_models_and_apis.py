#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推广码功能实现 - 适配当前系统架构
基于SQLAlchemy ORM和现有数据库结构
"""

from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
import time
import json

# 推广码相关的数据库模型
class PromotionUser(db.Model):
    """推广用户表 - 小程序用户"""
    __tablename__ = 'promotion_users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)  # 小程序用户ID
    promotion_code = db.Column(db.String(20), unique=True, nullable=False)  # 推广码
    open_id = db.Column(db.String(100))  # 微信OpenID
    nickname = db.Column(db.String(100))  # 用户昵称
    avatar_url = db.Column(db.String(200))  # 头像URL
    total_earnings = db.Column(db.Float, default=0.0)  # 总收益
    total_orders = db.Column(db.Integer, default=0)  # 推广订单数
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Commission(db.Model):
    """分佣记录表"""
    __tablename__ = 'commissions'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), nullable=False)  # 订单ID
    referrer_user_id = db.Column(db.String(50), nullable=False)  # 推广者用户ID
    amount = db.Column(db.Float, nullable=False)  # 佣金金额
    rate = db.Column(db.Float, nullable=False)  # 佣金比例
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    create_time = db.Column(db.DateTime, default=datetime.now)
    complete_time = db.Column(db.DateTime)  # 完成时间

class PromotionTrack(db.Model):
    """推广访问追踪表"""
    __tablename__ = 'promotion_tracks'
    
    id = db.Column(db.Integer, primary_key=True)
    promotion_code = db.Column(db.String(20), nullable=False)  # 推广码
    referrer_user_id = db.Column(db.String(50), nullable=False)  # 推广者用户ID
    visitor_user_id = db.Column(db.String(50))  # 访问者用户ID
    visit_time = db.Column(db.BigInteger, nullable=False)  # 访问时间戳
    create_time = db.Column(db.DateTime, default=datetime.now)

def generate_promotion_code(user_id):
    """生成推广码"""
    # 基于用户ID生成8位推广码
    hash_obj = hashlib.md5(user_id.encode())
    promotion_code = hash_obj.hexdigest()[:8].upper()
    return promotion_code

def validate_promotion_code(promotion_code):
    """验证推广码有效性"""
    user = PromotionUser.query.filter_by(promotion_code=promotion_code).first()
    return user.user_id if user else None

# 用户注册接口
@app.route('/api/user/register', methods=['POST'])
def register_user():
    """小程序用户注册接口"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        promotion_code = data.get('promotionCode')
        open_id = data.get('openId')
        user_info = data.get('userInfo', {})
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        # 检查用户是否已存在
        existing_user = PromotionUser.query.filter_by(user_id=user_id).first()
        
        if existing_user:
            return jsonify({
                'success': True,
                'message': '用户已存在',
                'userId': user_id,
                'promotionCode': existing_user.promotion_code
            })
        
        # 生成推广码（如果未提供）
        if not promotion_code:
            promotion_code = generate_promotion_code(user_id)
        
        # 创建新用户
        # 确保promotion_code不为None
        final_promotion_code = promotion_code if promotion_code else f"TEMP_{user_id[-6:]}"
        
        new_user = PromotionUser(
            user_id=user_id,
            promotion_code=final_promotion_code,
            open_id=open_id,
            nickname=user_info.get('nickName', ''),
            avatar_url=user_info.get('avatarUrl', ''),
            total_earnings=0.0,
            total_orders=0
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户注册成功',
            'userId': user_id,
            'promotionCode': promotion_code
        })
        
    except Exception as e:
        print(f"用户注册失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'用户注册失败: {str(e)}'
        }), 500

# 获取用户分佣数据
@app.route('/api/user/commission', methods=['GET'])
def get_user_commission():
    """获取用户分佣数据"""
    try:
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        # 获取用户信息
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 获取分佣记录
        commissions = Commission.query.filter_by(referrer_user_id=user_id).order_by(Commission.create_time.desc()).all()
        
        total_earnings = sum(commission.amount for commission in commissions if commission.status == 'completed')
        
        return jsonify({
            'success': True,
            'totalEarnings': total_earnings,
            'totalOrders': user.total_orders,
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

# 推广访问追踪
@app.route('/api/promotion/track', methods=['POST'])
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
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'推广访问记录失败: {str(e)}'
        }), 500

# 测试分佣功能
@app.route('/api/test/commission', methods=['POST'])
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
        
        # 检查用户是否存在
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 创建测试订单
        order_id = f'TEST{int(time.time())}'
        commission_rate = 0.1  # 10%
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
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'测试分佣失败: {str(e)}'
        }), 500

# 验证推广码接口
@app.route('/api/promotion/validate', methods=['POST'])
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

# 获取推广统计
@app.route('/api/promotion/stats', methods=['GET'])
def get_promotion_stats():
    """获取推广统计信息"""
    try:
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
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
