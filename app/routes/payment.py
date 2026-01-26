# -*- coding: utf-8 -*-
"""
支付相关路由
从 test_server.py 迁移支付相关路由
"""
from flask import Blueprint, request, jsonify
from app.services.payment_service import (
    create_payment_order,
    handle_payment_notify,
    get_user_openid as get_user_openid_service
)

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

@payment_bp.route('/create', methods=['POST'])
def create_payment():
    """创建支付订单接口"""
    try:
        data = request.get_json()
        order_id = data.get('orderId')
        total_price = data.get('totalPrice')
        openid = data.get('openid')
        coupon_code = data.get('couponCode')
        user_id = data.get('userId')
        discount_amount = data.get('discountAmount', 0)
        skip_payment = data.get('skipPayment', False)
        
        print(f"🎫 支付请求参数: orderId={order_id}, totalPrice={total_price}, couponCode={coupon_code}, discountAmount={discount_amount}, userId={user_id}, skipPayment={skip_payment}")
        
        if not all([order_id, total_price, openid]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        # 调用服务层函数
        success, result, error_message = create_payment_order(
            order_id=order_id,
            total_price=total_price,
            openid=openid,
            coupon_code=coupon_code,
            user_id=user_id,
            discount_amount=discount_amount,
            skip_payment=skip_payment,
            remote_addr=request.remote_addr
        )
        
        if success:
            return jsonify({
                'success': True,
                **result
            })
        else:
            status_code = 400 if '不存在' in error_message or '不足' in error_message else 500
            return jsonify({
                'success': False,
                'message': error_message
            }), status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建支付订单失败: {str(e)}'
        }), 500

@payment_bp.route('/notify', methods=['POST'])
def payment_notify():
    """支付结果通知接口"""
    try:
        # 获取微信支付通知数据
        xml_data = request.get_data()
        
        # 调用服务层函数处理支付通知
        success, response_xml, error_message = handle_payment_notify(xml_data)
        
        if success:
            return response_xml, 200, {'Content-Type': 'application/xml'}
        else:
            return response_xml or f'<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[{error_message or "处理失败"}]]></return_msg></xml>', 200, {'Content-Type': 'application/xml'}
            
    except Exception as e:
        from app.utils.helpers import dict_to_xml
        return dict_to_xml({'return_code': 'FAIL', 'return_msg': f'处理失败: {str(e)}'}), 200, {'Content-Type': 'application/xml'}

# ⭐ 用户openid接口已迁移到 app.routes.user_api
# user_bp 已移除，请使用 user_api_bp
