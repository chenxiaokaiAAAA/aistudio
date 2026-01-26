# -*- coding: utf-8 -*-
"""
管理员团购核销API路由模块
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sys
import random
import string
import qrcode
import base64
from io import BytesIO

# 创建蓝图
admin_groupon_api_bp = Blueprint('admin_groupon_api', __name__, url_prefix='/api/admin/groupon')

def get_models():
    """延迟导入数据库模型，避免循环导入"""
    try:
        test_server = sys.modules.get('test_server')
        if test_server:
            return {
                'Coupon': test_server.Coupon,
                'UserCoupon': test_server.UserCoupon,
                'db': test_server.db
            }
        return None
    except Exception as e:
        print(f"⚠️ 获取数据库模型失败: {e}")
        return None

def generate_random_code(length=8):
    """生成随机码"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_qr_code(data):
    """生成二维码图片（base64编码）"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@admin_groupon_api_bp.route('/verify', methods=['POST'])
@login_required
def verify_groupon_order():
    """团购订单核销 - 生成随机码免拍券"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        UserCoupon = models['UserCoupon']
        db = models['db']
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['groupon_order_id', 'verify_amount', 'customer_phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        groupon_order_id = data['groupon_order_id']
        verify_amount = float(data['verify_amount'])
        customer_phone = data['customer_phone']
        customer_name = data.get('customer_name', '')
        expire_days = int(data.get('expire_days', 30))  # 默认30天有效期
        
        # 检查是否已存在该团购订单的优惠券
        existing_coupon = Coupon.query.filter_by(
            groupon_order_id=groupon_order_id,
            source_type='groupon'
        ).first()
        
        if existing_coupon:
            return jsonify({
                'status': 'error',
                'message': '该团购订单已核销，优惠券已生成'
            }), 400
        
        # 生成随机码
        random_code = generate_random_code(8)
        # 确保随机码唯一
        while Coupon.query.filter_by(code=random_code).first():
            random_code = generate_random_code(8)
        
        # 创建优惠券
        now = datetime.now()
        coupon = Coupon(
            name=f'团购核销券-{verify_amount}元',
            code=random_code,
            type='free',  # 免拍券类型
            value=verify_amount,
            min_amount=0.0,  # 无门槛
            total_count=1,  # 单个券
            used_count=0,
            per_user_limit=1,
            start_time=now,
            end_time=now + timedelta(days=expire_days),
            status='active',
            description=f'团购订单{groupon_order_id}核销券，金额{verify_amount}元',
            source_type='groupon',
            groupon_order_id=groupon_order_id,
            verify_amount=verify_amount,
            is_random_code=True
        )
        
        db.session.add(coupon)
        db.session.flush()
        
        # 生成领取二维码（包含优惠券代码）
        # 二维码内容：小程序页面路径 + 优惠券代码
        qr_data = f"coupon_code:{random_code}"
        qr_code_url = generate_qr_code(qr_data)
        coupon.qr_code_url = qr_code_url
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '团购核销成功，优惠券已生成',
            'data': {
                'coupon_id': coupon.id,
                'coupon_code': random_code,
                'coupon_name': coupon.name,
                'verify_amount': verify_amount,
                'qr_code_url': qr_code_url,
                'expire_time': coupon.end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        print(f"团购核销失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'团购核销失败: {str(e)}'
        }), 500

@admin_groupon_api_bp.route('/verify/list', methods=['GET'])
@login_required
def get_groupon_verify_list():
    """获取团购核销记录列表"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        
        # 查询所有团购核销券
        coupons = Coupon.query.filter_by(
            source_type='groupon'
        ).order_by(Coupon.create_time.desc()).all()
        
        result = []
        for coupon in coupons:
            result.append({
                'id': coupon.id,
                'groupon_order_id': coupon.groupon_order_id,
                'coupon_code': coupon.code,
                'coupon_name': coupon.name,
                'verify_amount': float(coupon.verify_amount) if coupon.verify_amount else 0,
                'status': coupon.status,
                'used_count': coupon.used_count,
                'create_time': coupon.create_time.strftime('%Y-%m-%d %H:%M:%S') if coupon.create_time else '',
                'expire_time': coupon.end_time.strftime('%Y-%m-%d %H:%M:%S') if coupon.end_time else '',
                'qr_code_url': coupon.qr_code_url
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取团购核销记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取团购核销记录失败: {str(e)}'
        }), 500
