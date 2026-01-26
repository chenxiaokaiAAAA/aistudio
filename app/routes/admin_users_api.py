# -*- coding: utf-8 -*-
"""
管理后台用户管理API路由模块
从 test_server.py 迁移用户管理相关路由
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime
import sys

# 创建蓝图
admin_users_api_bp = Blueprint('admin_users_api', __name__)


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'Order': test_server_module.Order,
        'PromotionUser': test_server_module.PromotionUser,
        'calculate_visit_frequency': getattr(test_server_module, 'calculate_visit_frequency', None),
    }


@admin_users_api_bp.route('/admin/users')
@login_required
def admin_all_users():
    """所有用户访问统计页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/all_users.html')


@admin_users_api_bp.route('/api/admin/users/all', methods=['GET'])
@login_required
def get_all_users_access():
    """获取所有用户访问统计（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        calculate_visit_frequency = models.get('calculate_visit_frequency')
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        
        # 构建查询
        query = """
            SELECT 
                openid,
                total_visits,
                first_visit,
                last_visit,
                authorized_visits,
                registered_visits,
                ordered_visits,
                temp_promotion_code,
                final_promotion_code,
                has_ordered_flag
            FROM user_access_stats
        """
        
        params = []
        if search:
            query += " WHERE openid LIKE ? OR temp_promotion_code LIKE ? OR final_promotion_code LIKE ?"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY total_visits DESC, last_visit DESC"
        
        # 执行查询
        cursor = db.connection.cursor()
        cursor.execute(query, params)
        all_users = cursor.fetchall()
        
        # 分页
        total = len(all_users)
        start = (page - 1) * per_page
        end = start + per_page
        users = all_users[start:end]
        
        # 格式化数据
        user_list = []
        for user in users:
            user_data = {
                'openid': user[0],
                'total_visits': user[1],
                'first_visit': user[2],
                'last_visit': user[3],
                'authorized_visits': user[4],
                'registered_visits': user[5],
                'ordered_visits': user[6],
                'temp_promotion_code': user[7],
                'final_promotion_code': user[8],
                'has_ordered': bool(user[9]),
            }
            
            # 计算访问频率
            if calculate_visit_frequency:
                user_data['visit_frequency'] = calculate_visit_frequency(user[2], user[3], user[1])
            else:
                user_data['visit_frequency'] = "未知"
            
            user_list.append(user_data)
        
        return jsonify({
            'success': True,
            'users': user_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        print(f"获取所有用户访问统计失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取所有用户访问统计失败: {str(e)}'
        }), 500


@admin_users_api_bp.route('/api/admin/promotion/user/own-orders', methods=['GET'])
@login_required
def get_user_own_orders():
    """获取用户自己的订单（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        
        user_id = request.args.get('userId')
        promotion_code = request.args.get('promotionCode')
        
        if not user_id and not promotion_code:
            return jsonify({
                'success': False,
                'message': '用户ID或推广码不能为空'
            }), 400
        
        # 获取用户信息
        if user_id:
            user = PromotionUser.query.filter_by(user_id=user_id).first()
        else:
            user = PromotionUser.query.filter_by(promotion_code=promotion_code).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 查询用户自己的订单
        own_orders = db.session.execute(
            db.text("""
                SELECT order_number, customer_name, customer_phone, size, style_name, 
                       product_name, status, created_at, completed_at, customer_address
                FROM "order" 
                WHERE customer_phone = :phone_number
                ORDER BY created_at DESC
            """),
            {'phone_number': user.phone_number}
        ).fetchall()
        
        orders_list = []
        for order in own_orders:
            orders_list.append({
                'order_number': order[0],
                'customer_name': order[1],
                'customer_phone': order[2],
                'size': order[3],
                'style_name': order[4],
                'product_name': order[5],
                'status': order[6],
                'created_at': order[7].isoformat() if order[7] else None,
                'completed_at': order[8].isoformat() if order[8] else None,
                'customer_address': order[9]
            })
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': user.user_id,
                'promotion_code': user.promotion_code,
                'nickname': user.nickname,
                'phone_number': user.phone_number
            },
            'own_orders': orders_list,
            'total_count': len(orders_list)
        })
        
    except Exception as e:
        print(f"获取用户自己订单失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取用户自己订单失败: {str(e)}'
        }), 500
