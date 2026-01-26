# -*- coding: utf-8 -*-
"""
小程序团购核销相关路由
"""
from flask import Blueprint, request, jsonify
from app.routes.miniprogram.common import get_models, get_helper_functions
from datetime import datetime, timedelta
import sys
import random
import string
import qrcode
import base64
from io import BytesIO

bp = Blueprint('groupon', __name__)

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

def check_staff_permission(openid, user_id, phone=None):
    """检查用户是否有团购核销权限（从StaffUser表中检查）"""
    try:
        models = get_models()
        if not models:
            return False
        
        StaffUser = models.get('StaffUser')
        if not StaffUser:
            return False
        
        import json
        
        # 优先通过手机号匹配
        if phone:
            staff_user = StaffUser.query.filter_by(
                phone=phone,
                status='active'
            ).first()
            if staff_user:
                try:
                    permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
                    if permissions.get('groupon_verify'):
                        return True
                except:
                    pass
        
        # 通过openid匹配
        if openid:
            staff_user = StaffUser.query.filter_by(
                openid=openid,
                status='active'
            ).first()
            if staff_user:
                try:
                    permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
                    if permissions.get('groupon_verify'):
                        return True
                except:
                    pass
        
        # 通过user_id匹配（如果user_id是手机号）
        if user_id and len(user_id) == 11 and user_id.isdigit():
            staff_user = StaffUser.query.filter_by(
                phone=user_id,
                status='active'
            ).first()
            if staff_user:
                try:
                    permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
                    if permissions.get('groupon_verify'):
                        return True
                except:
                    pass
        
        # 兼容旧方式：从系统配置中读取店员openid列表（保留向后兼容）
        try:
            AIConfig = models.get('AIConfig')
            if AIConfig:
                staff_config = AIConfig.query.filter_by(config_key='staff_openids').first()
                if staff_config and staff_config.config_value:
                    staff_openids = json.loads(staff_config.config_value)
                    if isinstance(staff_openids, list):
                        if openid in staff_openids or user_id in staff_openids:
                            return True
        except:
            pass
        
        return False
    except Exception as e:
        print(f"检查店员权限失败: {e}")
        import traceback
        traceback.print_exc()
        return False

@bp.route('/groupon/verify', methods=['POST'])
def miniprogram_verify_groupon():
    """小程序团购订单核销"""
    try:
        data = request.get_json()
        openid = data.get('openid')
        user_id = data.get('user_id')
        
        # 检查权限
        if not check_staff_permission(openid, user_id):
            return jsonify({
                'status': 'error',
                'message': '权限不足，只有店员可以操作'
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
        expire_days = int(data.get('expire_days', 30))
        
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
        while Coupon.query.filter_by(code=random_code).first():
            random_code = generate_random_code(8)
        
        # 创建优惠券
        now = datetime.now()
        coupon = Coupon(
            name=f'团购核销券-{verify_amount}元',
            code=random_code,
            type='free',
            value=verify_amount,
            min_amount=0.0,
            total_count=1,
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
        
        # 生成领取二维码
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
        print(f"小程序团购核销失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'团购核销失败: {str(e)}'
        }), 500

@bp.route('/groupon/check-staff', methods=['GET'])
def check_staff():
    """检查用户是否有团购核销权限"""
    try:
        openid = request.args.get('openid', '')
        user_id = request.args.get('user_id', '')
        phone = request.args.get('phone', '')  # 获取手机号参数
        
        is_staff = check_staff_permission(openid, user_id, phone)
        
        return jsonify({
            'status': 'success',
            'data': {
                'is_staff': is_staff
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'检查权限失败: {str(e)}'
        }), 500
