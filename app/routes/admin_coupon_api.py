"""
管理员优惠券API路由模块
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
import sys

# 创建蓝图
admin_coupon_api_bp = Blueprint('admin_coupon_api', __name__, url_prefix='/api/admin/coupons')

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
        from app.utils.helpers import create_coupon
        return {
            'create_coupon': create_coupon
        }
    except ImportError as e:
        print(f"⚠️ 导入工具函数失败: {e}")
        return None

@admin_coupon_api_bp.route('/create', methods=['POST'])
@login_required
def create_coupon_admin():
    """管理员创建优惠券"""
    try:
        utils = get_utils()
        if not utils:
            return jsonify({
                'success': False,
                'message': '工具函数未初始化'
            }), 500
        
        create_coupon = utils['create_coupon']
        
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

@admin_coupon_api_bp.route('/<int:coupon_id>', methods=['GET'])
@login_required
def get_coupon_admin(coupon_id):
    """获取优惠券详情"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        
        coupon = Coupon.query.get(coupon_id)
        if not coupon:
            return jsonify({
                'success': False,
                'message': '优惠券不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'coupon': {
                'id': coupon.id,
                'name': coupon.name,
                'code': coupon.code,
                'type': coupon.type,
                'value': float(coupon.value),
                'min_amount': float(coupon.min_amount) if coupon.min_amount else 0,
                'max_discount': float(coupon.max_discount) if coupon.max_discount else None,
                'total_count': coupon.total_count,
                'used_count': coupon.used_count,
                'per_user_limit': coupon.per_user_limit,
                'start_time': coupon.start_time.isoformat() if coupon.start_time else None,
                'end_time': coupon.end_time.isoformat() if coupon.end_time else None,
                'status': coupon.status,
                'description': coupon.description
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取优惠券详情失败: {str(e)}'
        }), 500

@admin_coupon_api_bp.route('/<int:coupon_id>/update', methods=['PUT'])
@login_required
def update_coupon_admin(coupon_id):
    """管理员更新优惠券"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        db = models['db']
        
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

@admin_coupon_api_bp.route('/<int:coupon_id>/delete', methods=['DELETE'])
@login_required
def delete_coupon_admin(coupon_id):
    """管理员删除优惠券"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '数据库模型未初始化'
            }), 500
        
        Coupon = models['Coupon']
        UserCoupon = models['UserCoupon']
        db = models['db']
        
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
