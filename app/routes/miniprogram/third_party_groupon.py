# -*- coding: utf-8 -*-
"""
小程序第三方团购核销API路由模块
"""
from flask import Blueprint, request, jsonify
from app.routes.miniprogram.common import get_models
from datetime import datetime, timedelta
import sys
import json
import requests
import random
import string

bp = Blueprint('third_party_groupon', __name__)

def generate_random_code(length=8):
    """生成随机码"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_third_party_config():
    """获取第三方团购API配置"""
    try:
        models = get_models()
        if not models:
            return None
        
        AIConfig = models.get('AIConfig')
        if not AIConfig:
            return None
        
        config = AIConfig.query.filter_by(config_key='third_party_groupon_api').first()
        
        if config and config.config_value:
            try:
                config_data = json.loads(config.config_value)
                if config_data.get('status') == 'active':
                    return config_data
            except:
                pass
        
        return None
    except Exception as e:
        print(f"获取第三方团购配置失败: {e}")
        return None

def call_third_party_api(endpoint, method='GET', data=None, config=None):
    """调用第三方API"""
    try:
        if not config:
            return None, '配置未找到'
        
        api_base_url = config.get('api_base_url', '').rstrip('/')
        api_key = config.get('api_key', '')
        api_secret = config.get('api_secret', '')
        
        url = f"{api_base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if api_key:
            headers['X-API-Key'] = api_key
        
        # TODO: 如果需要签名验证，在这里添加签名逻辑
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=10)
        
        response.raise_for_status()
        return response.json(), None
        
    except requests.exceptions.RequestException as e:
        return None, f'API调用失败: {str(e)}'
    except Exception as e:
        return None, f'处理响应失败: {str(e)}'

@bp.route('/third-party-groupon/query', methods=['POST'])
def query_groupon_codes():
    """根据手机号查询团购券码列表"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                'status': 'error',
                'message': '请提供手机号'
            }), 400
        
        config = get_third_party_config()
        if not config:
            return jsonify({
                'status': 'error',
                'message': '第三方团购API未配置或已禁用'
            }), 400
        
        query_endpoint = config.get('query_endpoint', '/api/v1/query')
        
        # 调用第三方API查询券码
        result, error = call_third_party_api(
            query_endpoint,
            method='POST',
            data={'phone': phone}
        )
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # 返回券码列表
        # 假设第三方API返回格式：{'success': True, 'data': [{'code': 'xxx', 'amount': 100, 'status': 'unused'}, ...]}
        codes = result.get('data', []) if result else []
        
        return jsonify({
            'status': 'success',
            'data': {
                'codes': codes
            }
        })
        
    except Exception as e:
        print(f"查询团购券码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500

@bp.route('/third-party-groupon/verify', methods=['POST'])
def verify_groupon_code():
    """验证团购券码是否有效"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({
                'status': 'error',
                'message': '请提供券码'
            }), 400
        
        config = get_third_party_config()
        if not config:
            return jsonify({
                'status': 'error',
                'message': '第三方团购API未配置或已禁用'
            }), 400
        
        verify_endpoint = config.get('verify_endpoint', '/api/v1/verify')
        
        # 调用第三方API验证券码
        result, error = call_third_party_api(
            verify_endpoint,
            method='POST',
            data={'code': code}
        )
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # 假设第三方API返回格式：{'success': True, 'data': {'code': 'xxx', 'amount': 100, 'status': 'unused', 'expire_time': '...'}}
        if result and result.get('success'):
            return jsonify({
                'status': 'success',
                'data': result.get('data', {})
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', '券码验证失败')
            }), 400
        
    except Exception as e:
        print(f"验证券码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'验证失败: {str(e)}'
        }), 500

@bp.route('/third-party-groupon/redeem', methods=['POST'])
def redeem_groupon_code():
    """核销团购券码并生成免费拍摄券"""
    try:
        data = request.get_json()
        code = data.get('code')
        phone = data.get('phone')
        openid = data.get('openid')
        user_id = data.get('user_id')
        expire_days = int(data.get('expire_days', 30))
        
        if not code:
            return jsonify({
                'status': 'error',
                'message': '请提供券码'
            }), 400
        
        config = get_third_party_config()
        if not config:
            return jsonify({
                'status': 'error',
                'message': '第三方团购API未配置或已禁用'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        UserCoupon = models['UserCoupon']
        db = models['db']
        
        # 先验证券码
        verify_endpoint = config.get('verify_endpoint', '/api/v1/verify')
        verify_result, verify_error = call_third_party_api(
            verify_endpoint,
            method='POST',
            data={'code': code}
        )
        
        if verify_error or not verify_result or not verify_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': verify_error or '券码验证失败'
            }), 400
        
        code_info = verify_result.get('data', {})
        amount = float(code_info.get('amount', 0))
        
        if amount <= 0:
            return jsonify({
                'status': 'error',
                'message': '券码金额无效'
            }), 400
        
        # 检查是否已核销过
        existing_coupon = Coupon.query.filter_by(
            groupon_order_id=code,
            source_type='groupon'
        ).first()
        
        if existing_coupon:
            return jsonify({
                'status': 'error',
                'message': '该券码已核销'
            }), 400
        
        # 调用第三方API核销券码
        redeem_endpoint = config.get('redeem_endpoint', '/api/v1/redeem')
        redeem_result, redeem_error = call_third_party_api(
            redeem_endpoint,
            method='POST',
            data={'code': code, 'phone': phone}
        )
        
        if redeem_error or not redeem_result or not redeem_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': redeem_error or '券码核销失败'
            }), 400
        
        # 生成随机码
        random_code = generate_random_code(8)
        while Coupon.query.filter_by(code=random_code).first():
            random_code = generate_random_code(8)
        
        # 创建免费拍摄券
        now = datetime.now()
        coupon = Coupon(
            name=f'团购核销券-{amount}元',
            code=random_code,
            type='free',
            value=amount,
            min_amount=0.0,
            total_count=1,
            used_count=0,
            per_user_limit=1,
            start_time=now,
            end_time=now + timedelta(days=expire_days),
            status='active',
            description=f'第三方团购券码{code}核销券，金额{amount}元',
            source_type='groupon',
            groupon_order_id=code,
            verify_amount=amount,
            is_random_code=True
        )
        
        db.session.add(coupon)
        db.session.flush()
        
        # 如果提供了用户信息，自动发放优惠券
        if openid or user_id:
            user_coupon = UserCoupon(
                user_id=user_id or openid,
                coupon_id=coupon.id,
                status='unused',
                obtained_at=now
            )
            db.session.add(user_coupon)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '核销成功，优惠券已生成',
            'data': {
                'coupon_id': coupon.id,
                'coupon_code': random_code,
                'coupon_name': coupon.name,
                'amount': amount,
                'expire_time': coupon.end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        print(f"核销券码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'核销失败: {str(e)}'
        }), 500
