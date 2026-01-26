# -*- coding: utf-8 -*-
"""
支付业务逻辑服务
从 test_server.py 迁移支付相关业务逻辑
"""
import time
import requests
from datetime import datetime
from app.utils.config_loader import get_brand_name

# 延迟获取数据库模型和db实例
def get_db_models():
    """延迟获取数据库模型（避免循环导入）"""
    try:
        from app.models import Order, UserCoupon
        return {
            'Order': Order,
            'UserCoupon': UserCoupon
        }
    except ImportError:
        return None

def get_db():
    """延迟获取db实例"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                return test_server_module.db
    except (ImportError, AttributeError):
        pass
    return None

def get_wechat_pay_config():
    """获取微信支付配置"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'WECHAT_PAY_CONFIG'):
                return test_server_module.WECHAT_PAY_CONFIG
    except (ImportError, AttributeError):
        pass
    return None

def create_payment_order(order_id, total_price, openid, coupon_code=None, user_id=None, discount_amount=0, skip_payment=False, remote_addr='127.0.0.1'):
    """
    创建支付订单
    
    Args:
        order_id: 订单号
        total_price: 总价
        openid: 用户openid
        coupon_code: 优惠券代码（可选）
        user_id: 用户ID（可选）
        discount_amount: 优惠金额（可选）
        skip_payment: 是否跳过支付（开发模式）
    
    Returns:
        tuple: (success: bool, result: dict, error_message: str)
    """
    models = get_db_models()
    db = get_db()
    config = get_wechat_pay_config()
    
    if not models or not db:
        return False, None, "数据库模型或db实例未初始化"
    
    if not config:
        return False, None, "微信支付配置未初始化"
    
    Order = models['Order']
    UserCoupon = models['UserCoupon']
    
    from app.utils.helpers import (
        generate_sign, generate_nonce_str, dict_to_xml, xml_to_dict
    )
    
    try:
        # 查找订单
        order = Order.query.filter_by(order_number=order_id).first()
        if not order:
            return False, None, '订单不存在'
        
        # 开发模式：如果skipPayment为true，直接标记订单为已支付
        if skip_payment:
            try:
                order.status = 'paid'
                order.payment_time = datetime.now()
                order.transaction_id = f"DEV_{order_id}_{int(time.time())}"
                db.session.commit()
                return True, {
                    'isZeroPayment': True,
                    'data': {
                        'orderId': order_id,
                        'status': 'paid',
                        'paymentTime': order.payment_time.isoformat(),
                        'transactionId': order.transaction_id
                    }
                }, None
            except Exception as e:
                db.session.rollback()
                return False, None, f'开发模式：标记订单为已支付失败: {str(e)}'
        
        # 计算最终支付金额
        final_amount = float(total_price) - float(discount_amount)
        
        # 处理优惠券验证
        if coupon_code and user_id:
            user_coupon = UserCoupon.query.filter_by(
                user_id=user_id,
                coupon_code=coupon_code,
                status='unused'
            ).first()
            
            if not user_coupon:
                return False, None, '优惠券不存在或已使用'
            
            coupon = user_coupon.coupon
            now = datetime.now()
            
            if coupon.status != 'active':
                return False, None, '优惠券已失效'
            
            if now < coupon.start_time or now > coupon.end_time:
                return False, None, '优惠券不在有效期内'
            
            if now > user_coupon.expire_time:
                return False, None, '优惠券已过期'
            
            if order.price < coupon.min_amount:
                return False, None, f'订单金额需满{coupon.min_amount}元才能使用此优惠券'
        
        # 0元订单处理
        if final_amount <= 0:
            try:
                order.status = 'paid'
                order.payment_time = datetime.now()
                order.transaction_id = f"FREE_{order_id}_{int(time.time())}"
                
                if coupon_code and user_id:
                    user_coupon = UserCoupon.query.filter_by(
                        user_id=user_id,
                        coupon_code=coupon_code,
                        status='unused'
                    ).first()
                    if user_coupon:
                        user_coupon.status = 'used'
                        user_coupon.order_id = order.id
                        user_coupon.use_time = datetime.now()
                        
                        coupon = user_coupon.coupon
                        coupon.used_count += 1
                
                db.session.commit()
                
                return True, {
                    'isZeroPayment': True,
                    'data': {
                        'orderId': order_id,
                        'status': 'paid',
                        'paymentTime': order.payment_time.isoformat(),
                        'transactionId': order.transaction_id,
                        'couponCode': coupon_code,
                        'couponUsed': True if coupon_code else False
                    }
                }, None
            except Exception as e:
                db.session.rollback()
                return False, None, f'0元订单处理失败: {str(e)}'
        
        # 正常支付流程（金额大于0）
        params = {
            'appid': config['appid'],
            'mch_id': config['mch_id'],
            'nonce_str': generate_nonce_str(),
            'body': f'{get_brand_name()}-订单-{order_id}',
            'out_trade_no': order_id,
            'total_fee': int(final_amount * 100),
            'spbill_create_ip': remote_addr,
            'notify_url': config['notify_url'],
            'trade_type': 'JSAPI',
            'openid': openid
        }
        
        params['sign'] = generate_sign(params, config['api_key'])
        xml_data = dict_to_xml(params)
        
        # 调用微信支付接口
        response = requests.post(
            'https://api.mch.weixin.qq.com/pay/unifiedorder',
            data=xml_data.encode('utf-8'),
            headers={'Content-Type': 'application/xml'},
            timeout=(10, 30)
        )
        
        result = xml_to_dict(response.text)
        
        if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
            pay_params = {
                'appId': config['appid'],
                'timeStamp': str(int(time.time())),
                'nonceStr': generate_nonce_str(),
                'package': f"prepay_id={result['prepay_id']}",
                'signType': 'MD5'
            }
            pay_params['paySign'] = generate_sign(pay_params, config['api_key'])
            
            return True, {
                'paymentParams': pay_params,
                'isZeroPayment': False,
                'couponInfo': {
                    'couponCode': coupon_code,
                    'discountAmount': discount_amount,
                    'finalAmount': final_amount
                } if coupon_code else None
            }, None
        else:
            return False, None, result.get('err_code_des', '支付创建失败')
            
    except Exception as e:
        return False, None, f'创建支付订单失败: {str(e)}'

def handle_payment_notify(xml_data):
    """
    处理支付结果通知
    
    Args:
        xml_data: 微信支付通知的XML数据（bytes或str）
    
    Returns:
        tuple: (success: bool, response_xml: str, error_message: str)
    """
    models = get_db_models()
    db = get_db()
    config = get_wechat_pay_config()
    
    if not models or not db:
        return False, None, "数据库模型或db实例未初始化"
    
    if not config:
        return False, None, "微信支付配置未初始化"
    
    Order = models['Order']
    UserCoupon = models['UserCoupon']
    
    from app.utils.helpers import (
        verify_sign, dict_to_xml, xml_to_dict
    )
    
    try:
        # 解析XML数据
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode('utf-8')
        
        result = xml_to_dict(xml_data)
        
        # 验证签名
        sign = result.pop('sign', '')
        if not verify_sign(result, config['api_key'], sign):
            return False, dict_to_xml({'return_code': 'FAIL', 'return_msg': '签名验证失败'}), None
        
        # 处理支付结果
        if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
            order_id = result.get('out_trade_no')
            transaction_id = result.get('transaction_id')
            
            try:
                order = Order.query.filter_by(order_number=order_id).first()
                if order:
                    if order.status == 'unpaid':
                        order.status = 'pending'
                        order.payment_time = datetime.now()
                        order.transaction_id = transaction_id
                        
                        # 处理优惠券标记
                        user_coupons = UserCoupon.query.filter_by(order_id=order.id).all()
                        if user_coupons:
                            for user_coupon in user_coupons:
                                if user_coupon.status == 'unused':
                                    user_coupon.status = 'used'
                                    user_coupon.use_time = datetime.now()
                                    
                                    coupon = user_coupon.coupon
                                    if coupon:
                                        coupon.used_count += 1
                        
                        db.session.commit()
            except Exception as e:
                print(f"更新订单状态失败: {str(e)}")
            
            return True, dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}), None
        else:
            return False, dict_to_xml({'return_code': 'FAIL', 'return_msg': '支付失败'}), None
            
    except Exception as e:
        return False, dict_to_xml({'return_code': 'FAIL', 'return_msg': f'处理失败: {str(e)}'}), None

def get_user_openid(code, dev_mode=False):
    """
    获取用户openid
    
    Args:
        code: 微信小程序登录code
        dev_mode: 是否启用开发模式（跳过真实openid验证）
    
    Returns:
        tuple: (success: bool, result: dict, error_message: str)
    """
    config = get_wechat_pay_config()
    
    if not config:
        return False, None, "微信支付配置未初始化"
    
    # 开发模式
    if dev_mode:
        test_openid = "test_openid_dev_mode_fixed"
        return True, {
            'openid': test_openid,
            'message': '开发模式：使用测试openid'
        }, None
    
    try:
        if not code:
            return False, None, '缺少code参数'
        
        # 调用微信接口获取openid
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': config['appid'],
            'secret': config['app_secret'],
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.get(url, params=params, timeout=(10, 30))
        result = response.json()
        
        if 'openid' in result:
            return True, {
                'openid': result['openid'],
                'session_key': result.get('session_key', '')
            }, None
        else:
            return False, None, result.get('errmsg', '获取openid失败')
            
    except Exception as e:
        return False, None, f'获取openid失败: {str(e)}'
