#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优惠券系统实现 - 适配当前系统架构
基于SQLAlchemy ORM和现有数据库结构
"""

from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import string

# 优惠券相关的数据库模型
class Coupon(db.Model):
    """优惠券表"""
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 优惠券名称
    code = db.Column(db.String(20), unique=True, nullable=False)  # 优惠券代码
    type = db.Column(db.String(20), nullable=False)  # 类型：discount(折扣), cash(现金), free(免费)
    value = db.Column(db.Float, nullable=False)  # 优惠金额或折扣比例
    min_amount = db.Column(db.Float, default=0.0)  # 最低消费金额
    max_discount = db.Column(db.Float)  # 最大折扣金额（折扣券使用）
    total_count = db.Column(db.Integer, nullable=False)  # 总发放数量
    used_count = db.Column(db.Integer, default=0)  # 已使用数量
    per_user_limit = db.Column(db.Integer, default=1)  # 每用户限领数量
    start_time = db.Column(db.DateTime, nullable=False)  # 开始时间
    end_time = db.Column(db.DateTime, nullable=False)  # 结束时间
    status = db.Column(db.String(20), default='active')  # 状态：active, inactive, expired
    description = db.Column(db.Text)  # 优惠券描述
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class UserCoupon(db.Model):
    """用户优惠券表"""
    __tablename__ = 'user_coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # 用户ID
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)  # 优惠券ID
    coupon_code = db.Column(db.String(20), nullable=False)  # 优惠券代码
    status = db.Column(db.String(20), default='unused')  # 状态：unused, used, expired
    order_id = db.Column(db.String(50))  # 使用的订单ID
    get_time = db.Column(db.DateTime, default=datetime.now)  # 领取时间
    use_time = db.Column(db.DateTime)  # 使用时间
    expire_time = db.Column(db.DateTime)  # 过期时间
    
    # 关联关系
    coupon = db.relationship('Coupon', backref='user_coupons')

def generate_coupon_code():
    """生成优惠券代码"""
    # 生成8位随机代码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return code

def validate_coupon_code(code):
    """验证优惠券代码是否已存在"""
    existing_coupon = Coupon.query.filter_by(code=code).first()
    return existing_coupon is None

def create_coupon(name, coupon_type, value, min_amount=0.0, max_discount=None, 
                 total_count=100, per_user_limit=1, start_time=None, end_time=None, 
                 description=None):
    """创建优惠券"""
    # 生成唯一代码
    while True:
        code = generate_coupon_code()
        if validate_coupon_code(code):
            break
    
    # 设置默认时间
    if not start_time:
        start_time = datetime.now()
    if not end_time:
        end_time = start_time + timedelta(days=30)
    
    coupon = Coupon(
        name=name,
        code=code,
        type=coupon_type,
        value=value,
        min_amount=min_amount,
        max_discount=max_discount,
        total_count=total_count,
        per_user_limit=per_user_limit,
        start_time=start_time,
        end_time=end_time,
        description=description
    )
    
    db.session.add(coupon)
    db.session.commit()
    return coupon

def get_user_coupons(user_id, status=None):
    """获取用户优惠券列表"""
    query = UserCoupon.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    
    coupons = query.join(Coupon).all()
    return coupons

def can_user_get_coupon(user_id, coupon_id):
    """检查用户是否可以领取优惠券"""
    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        return False, "优惠券不存在"
    
    # 检查优惠券状态
    if coupon.status != 'active':
        return False, "优惠券已失效"
    
    # 检查时间
    now = datetime.now()
    if now < coupon.start_time or now > coupon.end_time:
        return False, "优惠券不在有效期内"
    
    # 检查库存
    if coupon.used_count >= coupon.total_count:
        return False, "优惠券已领完"
    
    # 检查用户领取限制
    user_coupon_count = UserCoupon.query.filter_by(
        user_id=user_id, 
        coupon_id=coupon_id
    ).count()
    
    if user_coupon_count >= coupon.per_user_limit:
        return False, f"已达到领取限制（最多{coupon.per_user_limit}张）"
    
    return True, "可以领取"

def user_get_coupon(user_id, coupon_id):
    """用户领取优惠券"""
    can_get, message = can_user_get_coupon(user_id, coupon_id)
    if not can_get:
        return False, message
    
    coupon = Coupon.query.get(coupon_id)
    
    # 创建用户优惠券记录
    user_coupon = UserCoupon(
        user_id=user_id,
        coupon_id=coupon_id,
        coupon_code=coupon.code,
        expire_time=coupon.end_time
    )
    
    db.session.add(user_coupon)
    db.session.commit()
    
    return True, "领取成功"

def can_use_coupon(user_id, coupon_code, order_amount):
    """检查优惠券是否可以使用"""
    user_coupon = UserCoupon.query.filter_by(
        user_id=user_id,
        coupon_code=coupon_code,
        status='unused'
    ).first()
    
    if not user_coupon:
        return False, "优惠券不存在或已使用"
    
    coupon = user_coupon.coupon
    
    # 检查时间
    now = datetime.now()
    if now > coupon.end_time or now > user_coupon.expire_time:
        return False, "优惠券已过期"
    
    # 检查最低消费
    if order_amount < coupon.min_amount:
        return False, f"订单金额需满{coupon.min_amount}元"
    
    return True, "可以使用"

def calculate_discount_amount(coupon_code, order_amount):
    """计算优惠金额"""
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if not coupon:
        return 0
    
    if coupon.type == 'cash':
        # 现金券直接减免
        discount_amount = coupon.value
    elif coupon.type == 'discount':
        # 折扣券按比例计算
        discount_amount = order_amount * (coupon.value / 100)
        # 检查最大折扣限制
        if coupon.max_discount and discount_amount > coupon.max_discount:
            discount_amount = coupon.max_discount
    elif coupon.type == 'free':
        # 免费券
        discount_amount = order_amount
    else:
        discount_amount = 0
    
    return min(discount_amount, order_amount)  # 不能超过订单金额

def use_coupon(user_id, coupon_code, order_id):
    """使用优惠券"""
    can_use, message = can_use_coupon(user_id, coupon_code, 0)  # 这里不检查金额，在订单中使用时再检查
    if not can_use:
        return False, message
    
    user_coupon = UserCoupon.query.filter_by(
        user_id=user_id,
        coupon_code=coupon_code,
        status='unused'
    ).first()
    
    # 更新用户优惠券状态
    user_coupon.status = 'used'
    user_coupon.order_id = order_id
    user_coupon.use_time = datetime.now()
    
    # 更新优惠券使用计数
    coupon = user_coupon.coupon
    coupon.used_count += 1
    
    db.session.commit()
    return True, "使用成功"

# API接口函数
def init_coupon_routes(app, db):
    """初始化优惠券相关路由"""
    
    @app.route('/api/coupons/list', methods=['GET'])
    def get_coupons_list():
        """获取优惠券列表"""
        try:
            status = request.args.get('status', 'active')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            
            query = Coupon.query
            if status != 'all':
                query = query.filter_by(status=status)
            
            coupons = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            result = []
            for coupon in coupons.items:
                result.append({
                    'id': coupon.id,
                    'name': coupon.name,
                    'code': coupon.code,
                    'type': coupon.type,
                    'value': coupon.value,
                    'min_amount': coupon.min_amount,
                    'max_discount': coupon.max_discount,
                    'total_count': coupon.total_count,
                    'used_count': coupon.used_count,
                    'per_user_limit': coupon.per_user_limit,
                    'start_time': coupon.start_time.isoformat(),
                    'end_time': coupon.end_time.isoformat(),
                    'status': coupon.status,
                    'description': coupon.description,
                    'remaining_count': coupon.total_count - coupon.used_count
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'total': coupons.total,
                'page': page,
                'per_page': per_page,
                'pages': coupons.pages
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取优惠券列表失败: {str(e)}'
            }), 500
    
    @app.route('/api/coupons/user/<user_id>', methods=['GET'])
    def get_user_coupons_api(user_id):
        """获取用户优惠券列表"""
        try:
            status = request.args.get('status', 'unused')
            
            query = UserCoupon.query.filter_by(user_id=user_id)
            if status != 'all':
                query = query.filter_by(status=status)
            
            user_coupons = query.join(Coupon).all()
            
            result = []
            for uc in user_coupons:
                coupon = uc.coupon
                result.append({
                    'id': uc.id,
                    'coupon_id': coupon.id,
                    'coupon_name': coupon.name,
                    'coupon_code': coupon.code,
                    'coupon_type': coupon.type,
                    'coupon_value': coupon.value,
                    'min_amount': coupon.min_amount,
                    'max_discount': coupon.max_discount,
                    'status': uc.status,
                    'get_time': uc.get_time.isoformat(),
                    'use_time': uc.use_time.isoformat() if uc.use_time else None,
                    'expire_time': uc.expire_time.isoformat(),
                    'order_id': uc.order_id,
                    'description': coupon.description
                })
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'获取用户优惠券失败: {str(e)}'
            }), 500
    
    @app.route('/api/coupons/get', methods=['POST'])
    def get_coupon():
        """用户领取优惠券"""
        try:
            data = request.get_json()
            user_id = data.get('userId')
            coupon_id = data.get('couponId')
            
            if not user_id or not coupon_id:
                return jsonify({
                    'success': False,
                    'message': '用户ID和优惠券ID不能为空'
                }), 400
            
            success, message = user_get_coupon(user_id, coupon_id)
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'领取优惠券失败: {str(e)}'
            }), 500
    
    @app.route('/api/coupons/validate', methods=['POST'])
    def validate_coupon():
        """验证优惠券"""
        try:
            data = request.get_json()
            user_id = data.get('userId')
            coupon_code = data.get('couponCode')
            order_amount = float(data.get('orderAmount', 0))
            
            if not user_id or not coupon_code:
                return jsonify({
                    'success': False,
                    'message': '用户ID和优惠券代码不能为空'
                }), 400
            
            can_use, message = can_use_coupon(user_id, coupon_code, order_amount)
            
            if can_use:
                discount_amount = calculate_discount_amount(coupon_code, order_amount)
                return jsonify({
                    'success': True,
                    'message': message,
                    'discount_amount': discount_amount,
                    'final_amount': order_amount - discount_amount
                })
            else:
                return jsonify({
                    'success': False,
                    'message': message
                })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'验证优惠券失败: {str(e)}'
            }), 500
    
    @app.route('/api/coupons/use', methods=['POST'])
    def use_coupon_api():
        """使用优惠券"""
        try:
            data = request.get_json()
            user_id = data.get('userId')
            coupon_code = data.get('couponCode')
            order_id = data.get('orderId')
            
            if not user_id or not coupon_code or not order_id:
                return jsonify({
                    'success': False,
                    'message': '用户ID、优惠券代码和订单ID不能为空'
                }), 400
            
            success, message = use_coupon(user_id, coupon_code, order_id)
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'使用优惠券失败: {str(e)}'
            }), 500
    
    @app.route('/api/admin/coupons/create', methods=['POST'])
    def create_coupon_admin():
        """管理员创建优惠券"""
        try:
            data = request.get_json()
            
            required_fields = ['name', 'type', 'value', 'total_count']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }), 400
            
            # 解析时间
            start_time = None
            end_time = None
            if data.get('start_time'):
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            if data.get('end_time'):
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            
            coupon = create_coupon(
                name=data['name'],
                coupon_type=data['type'],
                value=float(data['value']),
                min_amount=float(data.get('min_amount', 0)),
                max_discount=float(data.get('max_discount')) if data.get('max_discount') else None,
                total_count=int(data['total_count']),
                per_user_limit=int(data.get('per_user_limit', 1)),
                start_time=start_time,
                end_time=end_time,
                description=data.get('description')
            )
            
            return jsonify({
                'success': True,
                'message': '优惠券创建成功',
                'data': {
                    'id': coupon.id,
                    'name': coupon.name,
                    'code': coupon.code,
                    'type': coupon.type,
                    'value': coupon.value
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'创建优惠券失败: {str(e)}'
            }), 500
    
    @app.route('/api/admin/coupons/<int:coupon_id>/update', methods=['PUT'])
    def update_coupon_admin(coupon_id):
        """管理员更新优惠券"""
        try:
            coupon = Coupon.query.get(coupon_id)
            if not coupon:
                return jsonify({
                    'success': False,
                    'message': '优惠券不存在'
                }), 404
            
            data = request.get_json()
            
            # 更新字段
            if 'name' in data:
                coupon.name = data['name']
            if 'type' in data:
                coupon.type = data['type']
            if 'value' in data:
                coupon.value = float(data['value'])
            if 'min_amount' in data:
                coupon.min_amount = float(data['min_amount'])
            if 'max_discount' in data:
                coupon.max_discount = float(data['max_discount']) if data['max_discount'] else None
            if 'total_count' in data:
                coupon.total_count = int(data['total_count'])
            if 'per_user_limit' in data:
                coupon.per_user_limit = int(data['per_user_limit'])
            if 'start_time' in data:
                coupon.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            if 'end_time' in data:
                coupon.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            if 'status' in data:
                coupon.status = data['status']
            if 'description' in data:
                coupon.description = data['description']
            
            coupon.update_time = datetime.now()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '优惠券更新成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新优惠券失败: {str(e)}'
            }), 500
    
    @app.route('/api/admin/coupons/<int:coupon_id>/delete', methods=['DELETE'])
    def delete_coupon_admin(coupon_id):
        """管理员删除优惠券"""
        try:
            coupon = Coupon.query.get(coupon_id)
            if not coupon:
                return jsonify({
                    'success': False,
                    'message': '优惠券不存在'
                }), 404
            
            # 检查是否有用户已领取
            user_coupon_count = UserCoupon.query.filter_by(coupon_id=coupon_id).count()
            if user_coupon_count > 0:
                return jsonify({
                    'success': False,
                    'message': '该优惠券已有用户领取，无法删除'
                }), 400
            
            db.session.delete(coupon)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '优惠券删除成功'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'删除优惠券失败: {str(e)}'
            }), 500








