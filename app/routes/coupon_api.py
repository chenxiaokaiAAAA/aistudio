"""
优惠券相关API路由模块
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
import sys

# 创建蓝图
coupon_api_bp = Blueprint('coupon_api', __name__, url_prefix='/api/coupons')

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

def get_utils():
    """延迟导入工具函数"""
    try:
        from app.utils.helpers import (
            user_get_coupon,
            use_coupon,
            can_use_coupon,
            calculate_discount_amount,
            create_coupon
        )
        return {
            'user_get_coupon': user_get_coupon,
            'use_coupon': use_coupon,
            'can_use_coupon': can_use_coupon,
            'calculate_discount_amount': calculate_discount_amount,
            'create_coupon': create_coupon
        }
    except ImportError as e:
        print(f"⚠️ 导入工具函数失败: {e}")
        return None

@coupon_api_bp.route('/test', methods=['GET'])
def test_coupons():
    """测试优惠券接口 - 返回固定数据"""
    try:
        print("🔍 收到优惠券测试请求")
        
        # 返回测试数据
        test_coupons = [
            {
                "id": 1,
                "name": "新用户专享券",
                "code": "NEWUSER001",
                "type": "cash",
                "value": 49.0,
                "min_amount": 0.0,
                "description": "新用户专享，无门槛使用",
                "end_time": "2025-12-31T23:59:59",
                "can_claim": True,
                "remaining_count": 100,
                "per_user_limit": 1,
                "user_claimed_count": 0
            },
            {
                "id": 2,
                "name": "限时优惠券",
                "code": "LIMITED001",
                "type": "cash",
                "value": 29.0,
                "min_amount": 100.0,
                "description": "满100元可用",
                "end_time": "2025-11-30T23:59:59",
                "can_claim": True,
                "remaining_count": 50,
                "per_user_limit": 2,
                "user_claimed_count": 0
            }
        ]
        
        return jsonify({
            'success': True,
            'data': test_coupons,
            'total': len(test_coupons),
            'message': '测试数据'
        })
        
    except Exception as e:
        print(f"❌ 测试接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'测试接口错误: {str(e)}'
        }), 500

@coupon_api_bp.route('/debug', methods=['GET'])
def debug_coupons():
    """调试优惠券接口 - 记录所有请求信息"""
    try:
        user_id = request.args.get('userId')
        print(f"🔍 收到优惠券调试请求:")
        print(f"  用户ID: {user_id}")
        print(f"  请求头: {dict(request.headers)}")
        print(f"  请求参数: {request.args}")
        print(f"  请求方法: {request.method}")
        print(f"  请求路径: {request.path}")
        
        # 返回调试信息
        return jsonify({
            'success': True,
            'message': '调试信息已记录',
            'debug_info': {
                'user_id': user_id,
                'request_args': dict(request.args),
                'request_headers': dict(request.headers),
                'request_method': request.method,
                'request_path': request.path,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"❌ 调试接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'调试接口错误: {str(e)}'
        }), 500

@coupon_api_bp.route('/list', methods=['GET'])
def get_coupons_list():
    """获取优惠券列表"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        UserCoupon = models['UserCoupon']
        
        status = request.args.get('status', 'active')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        query = Coupon.query
        # 如果请求所有状态，不过滤；否则只过滤status字段
        # 注意：过期状态需要根据end_time判断，这里只过滤status字段
        if status != 'all':
            query = query.filter_by(status=status)
        
        coupons = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        result = []
        for coupon in coupons.items:
            # 已领取数量（claimed_count）：user_coupons 记录数
            # 获取source_type等新字段（如果存在）
            source_type = getattr(coupon, 'source_type', 'system')
            groupon_order_id = getattr(coupon, 'groupon_order_id', None)
            is_random_code = getattr(coupon, 'is_random_code', False)
            claimed_count = UserCoupon.query.filter_by(coupon_id=coupon.id).count()
            # 已使用数量（used_count）：保持现有字段含义
            used_count = coupon.used_count or 0
            # 剩余可领取数量：总数 - 已领取
            remaining_count = max(0, (coupon.total_count or 0) - claimed_count)

            result.append({
                'id': coupon.id,
                'name': coupon.name,
                'code': coupon.code,
                'type': coupon.type,
                'value': coupon.value,
                'min_amount': coupon.min_amount,
                'max_discount': coupon.max_discount,
                'total_count': coupon.total_count,
                'claimed_count': claimed_count,
                'used_count': used_count,
                'per_user_limit': coupon.per_user_limit,
                'start_time': coupon.start_time.isoformat(),
                'end_time': coupon.end_time.isoformat(),
                'status': coupon.status,
                'description': coupon.description,
                'remaining_count': remaining_count,
                # 新增字段
                'source_type': source_type,
                'groupon_order_id': groupon_order_id,
                'is_random_code': is_random_code
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

@coupon_api_bp.route('/user/<user_id>', methods=['GET'])
def get_user_coupons_api(user_id):
    """获取用户优惠券列表"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        UserCoupon = models['UserCoupon']
        
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
            'message': f'获取用户优惠券列表失败: {str(e)}'
        }), 500

@coupon_api_bp.route('/available', methods=['GET'])
def get_available_coupons():
    """获取可领取的优惠券列表"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        UserCoupon = models['UserCoupon']
        
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400
        
        # 查询可领取的优惠券
        now = datetime.now()
        available_coupons = Coupon.query.filter(
            Coupon.status == 'active',
            Coupon.start_time <= now,
            Coupon.end_time > now,
            Coupon.total_count > Coupon.used_count  # 还有剩余数量
        ).all()
        
        result_coupons = []
        for coupon in available_coupons:
            # 检查用户是否已经领取过
            user_coupon_count = UserCoupon.query.filter_by(
                user_id=user_id,
                coupon_id=coupon.id
            ).count()
            
            # 检查是否达到每用户限领数量
            can_claim = user_coupon_count < coupon.per_user_limit
            
            # 计算剩余数量
            remaining_count = max(0, coupon.total_count - coupon.used_count)
            
            # 计算已领取数量（claimed_count）
            claimed_count = UserCoupon.query.filter_by(coupon_id=coupon.id).count()
            
            coupon_info = {
                'id': coupon.id,
                'name': coupon.name,
                'code': coupon.code,
                'type': coupon.type,
                'value': coupon.value,
                'min_amount': coupon.min_amount,
                'max_discount': coupon.max_discount,
                'description': coupon.description,
                'start_time': coupon.start_time.isoformat(),
                'end_time': coupon.end_time.isoformat(),
                'total_count': coupon.total_count,
                'used_count': coupon.used_count,
                'claimed_count': claimed_count,
                'remaining_count': remaining_count,
                'per_user_limit': coupon.per_user_limit,
                'user_claimed_count': user_coupon_count,
                'can_claim': can_claim,
                'status': coupon.status
            }
            
            result_coupons.append(coupon_info)
        
        return jsonify({
            'success': True,
            'data': result_coupons,
            'total': len(result_coupons)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取可领取优惠券失败: {str(e)}'
        }), 500

@coupon_api_bp.route('/get', methods=['POST'])
def get_coupon():
    """用户领取优惠券"""
    try:
        utils = get_utils()
        if not utils:
            return jsonify({
                'success': False,
                'message': '工具函数未初始化'
            }), 500
        
        user_get_coupon = utils['user_get_coupon']
        
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

@coupon_api_bp.route('/validate', methods=['POST'])
def validate_coupon():
    """验证优惠券"""
    try:
        utils = get_utils()
        if not utils:
            return jsonify({
                'success': False,
                'message': '工具函数未初始化'
            }), 500
        
        can_use_coupon = utils['can_use_coupon']
        calculate_discount_amount = utils['calculate_discount_amount']
        
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

@coupon_api_bp.route('/use', methods=['POST'])
def use_coupon_api():
    """使用优惠券"""
    try:
        utils = get_utils()
        if not utils:
            return jsonify({
                'success': False,
                'message': '工具函数未初始化'
            }), 500
        
        use_coupon = utils['use_coupon']
        
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
