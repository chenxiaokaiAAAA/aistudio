# -*- coding: utf-8 -*-
"""
管理后台推广管理API路由模块
从 test_server.py 迁移所有 /api/admin/promotion/* 路由
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime
import sys
import json

# 创建蓝图
admin_promotion_api_bp = Blueprint('admin_promotion_api', __name__, url_prefix='/admin')


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'Order': test_server_module.Order,
        'PromotionUser': test_server_module.PromotionUser,
        'Commission': test_server_module.Commission,
        'PromotionTrack': test_server_module.PromotionTrack,
        'send_commission_notification_auto': test_server_module.send_commission_notification_auto if hasattr(test_server_module, 'send_commission_notification_auto') else None
    }


@admin_promotion_api_bp.route('/promotion')
@login_required
def admin_promotion_management():
    """后台分佣管理页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/promotion_management.html')


@admin_promotion_api_bp.route('/api/promotion/commissions', methods=['GET'])
@login_required
def get_admin_commissions():
    """获取分佣记录列表（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        Commission = models['Commission']
        PromotionUser = models['PromotionUser']
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        date_from = request.args.get('dateFrom', '')
        date_to = request.args.get('dateTo', '')
        
        # 构建查询
        query = db.session.query(Commission, PromotionUser).join(
            PromotionUser, Commission.referrer_user_id == PromotionUser.user_id
        )
        
        # 搜索条件
        if search:
            query = query.filter(
                db.or_(
                    PromotionUser.user_id.like(f'%{search}%'),
                    PromotionUser.promotion_code.like(f'%{search}%'),
                    PromotionUser.nickname.like(f'%{search}%'),
                    Commission.order_id.like(f'%{search}%')
                )
            )
        
        # 状态筛选
        if status:
            query = query.filter(Commission.status == status)
        
        # 日期筛选
        if date_from:
            query = query.filter(Commission.create_time >= date_from)
        if date_to:
            query = query.filter(Commission.create_time <= date_to + ' 23:59:59')
        
        # 排序
        query = query.order_by(Commission.create_time.desc())
        
        # 分页
        total = query.count()
        commissions = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 格式化数据
        commission_list = []
        for commission, user in commissions:
            # 根据订单状态计算分佣状态
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order and order.status == 'delivered':
                calculated_status = 'completed'
            else:
                calculated_status = 'pending'
            
            commission_list.append({
                'id': commission.id,
                'order_id': commission.order_id,
                'amount': commission.amount,
                'rate': commission.rate,
                'status': calculated_status,  # 使用计算出的状态
                'original_status': commission.status,  # 保留原始状态
                'order_status': order.status if order else None,  # 订单状态
                'create_time': commission.create_time.isoformat() if commission.create_time else None,
                'complete_time': commission.complete_time.isoformat() if commission.complete_time else None,
                'user': {
                    'user_id': user.user_id,
                    'promotion_code': user.promotion_code,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'phone_number': user.phone_number  # 添加手机号字段
                }
            })
        
        # 计算统计信息
        total_users = PromotionUser.query.count()
        
        # 根据订单状态计算总佣金
        total_commissions = 0
        all_commissions = Commission.query.all()
        for commission in all_commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
            if order and order.status == 'shipped':
                total_commissions += commission.amount
        
        total_orders = Commission.query.count()
        avg_commission = total_commissions / total_orders if total_orders > 0 else 0
        
        return jsonify({
            'success': True,
            'commissions': commission_list,
            'pagination': {
                'currentPage': page,
                'pageSize': page_size,
                'totalPages': (total + page_size - 1) // page_size,
                'total': total
            },
            'statistics': {
                'totalUsers': total_users,
                'totalCommissions': float(total_commissions),
                'totalOrders': total_orders,
                'avgCommission': float(avg_commission)
            }
        })
        
    except Exception as e:
        print(f"获取分佣记录失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取分佣记录失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/users', methods=['GET'])
@login_required
def get_admin_promotion_users():
    """获取推广用户列表（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        
        print("=" * 50)
        print("开始获取推广用户列表...")
        print(f"数据库模型: {PromotionUser}")
        print(f"表名: {PromotionUser.__tablename__}")
        
        # 先直接查询所有用户，看看数据库中有没有数据
        try:
            all_users_count = PromotionUser.query.count()
            print(f"数据库中用户总数: {all_users_count}")
            if all_users_count > 0:
                sample_user = PromotionUser.query.first()
                print(f"示例用户: user_id={sample_user.user_id}, promotion_code={sample_user.promotion_code}")
        except Exception as e:
            print(f"查询用户总数失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 获取排序参数
        sort_by = request.args.get('sortBy', 'create_time')  # 默认按创建时间排序
        sort_order = request.args.get('sortOrder', 'desc')  # 默认降序
        print(f"排序参数: sortBy={sort_by}, sortOrder={sort_order}")
        
        # 构建排序
        if sort_by == 'visits':
            # 按访问数排序需要特殊处理
            users = PromotionUser.query.all()
            user_list = []
            
            for user in users:
                try:
                    # 查询该用户的访问统计
                    total_stats = db.session.execute(
                        db.text("""
                            SELECT COUNT(*) as total_visits 
                            FROM user_access_logs 
                            WHERE final_promotion_code = :promotion_code
                        """),
                        {'promotion_code': user.promotion_code}
                    ).fetchone()
                    
                    # 查询用户自己的订单数、支付金额（通过openid查询已支付的订单）
                    order_stats = db.session.execute(
                        db.text("""
                            SELECT 
                                COUNT(*) as paid_orders,
                                COALESCE(SUM(price), 0) as total_paid_amount
                            FROM orders 
                            WHERE openid = :open_id 
                                AND source_type = 'miniprogram'
                                AND status IN ('paid', 'processing', 'shipped', 'delivered', 'completed')
                        """),
                        {'open_id': user.open_id if user.open_id else ''}
                    ).fetchone()
                    
                    # 查询用户优惠券数量
                    coupon_count = db.session.execute(
                        db.text("""
                            SELECT COUNT(*) as coupon_count
                            FROM user_coupons 
                            WHERE user_id = :user_id
                        """),
                        {'user_id': user.user_id}
                    ).fetchone()
                    
                    user_data = {
                        'user_id': user.user_id,
                        'open_id': user.open_id,
                        'promotion_code': user.promotion_code,
                        'nickname': user.nickname,
                        'avatar_url': user.avatar_url,
                        'phone_number': user.phone_number,
                        'total_earnings': user.total_earnings,
                        'total_orders': user.total_orders,
                        'own_orders': order_stats[0] if order_stats else 0,
                        'paid_amount': float(order_stats[1]) if order_stats else 0.0,
                        'coupon_count': coupon_count[0] if coupon_count else 0,
                        'create_time': user.create_time.isoformat() if user.create_time else None,
                        'update_time': user.update_time.isoformat() if user.update_time else None,
                        'visit_stats': {
                            'total_visits': total_stats[0] if total_stats else 0
                        },
                        'recent_visits': []
                    }
                    user_list.append(user_data)
                except Exception as e:
                    print(f"处理用户失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # 按访问数排序
            if sort_order == 'desc':
                user_list.sort(key=lambda x: x['visit_stats']['total_visits'], reverse=True)
            else:
                user_list.sort(key=lambda x: x['visit_stats']['total_visits'], reverse=False)
                
        else:
            # 其他排序方式
            if sort_by == 'create_time':
                order_column = PromotionUser.create_time
            elif sort_by == 'update_time':
                order_column = PromotionUser.update_time
            elif sort_by == 'total_earnings':
                order_column = PromotionUser.total_earnings
            elif sort_by == 'total_orders':
                order_column = PromotionUser.total_orders
            else:
                order_column = PromotionUser.create_time
            
            if sort_order == 'desc':
                users = PromotionUser.query.order_by(order_column.desc()).all()
            else:
                users = PromotionUser.query.order_by(order_column.asc()).all()
            
            user_list = []
            for i, user in enumerate(users):
                try:
                    # 查询该用户的访问统计
                    total_stats = db.session.execute(
                        db.text("""
                            SELECT COUNT(*) as total_visits 
                            FROM user_access_logs 
                            WHERE final_promotion_code = :promotion_code
                        """),
                        {'promotion_code': user.promotion_code}
                    ).fetchone()
                    
                    # 查询用户自己的订单数、支付金额（通过openid查询已支付的订单）
                    order_stats = db.session.execute(
                        db.text("""
                            SELECT 
                                COUNT(*) as paid_orders,
                                COALESCE(SUM(price), 0) as total_paid_amount
                            FROM orders 
                            WHERE openid = :open_id 
                                AND source_type = 'miniprogram'
                                AND status IN ('paid', 'processing', 'shipped', 'delivered', 'completed')
                        """),
                        {'open_id': user.open_id if user.open_id else ''}
                    ).fetchone()
                    
                    # 查询用户优惠券数量
                    coupon_count = db.session.execute(
                        db.text("""
                            SELECT COUNT(*) as coupon_count
                            FROM user_coupons 
                            WHERE user_id = :user_id
                        """),
                        {'user_id': user.user_id}
                    ).fetchone()
                    
                    user_data = {
                        'user_id': user.user_id,
                        'open_id': user.open_id,
                        'promotion_code': user.promotion_code,
                        'nickname': user.nickname,
                        'avatar_url': user.avatar_url,
                        'phone_number': user.phone_number,
                        'total_earnings': user.total_earnings,
                        'total_orders': user.total_orders,
                        'own_orders': order_stats[0] if order_stats else 0,
                        'paid_amount': float(order_stats[1]) if order_stats else 0.0,
                        'coupon_count': coupon_count[0] if coupon_count else 0,
                        'create_time': user.create_time.isoformat() if user.create_time else None,
                        'update_time': user.update_time.isoformat() if user.update_time else None,
                        'visit_stats': {
                            'total_visits': total_stats[0] if total_stats else 0
                        },
                        'recent_visits': []
                    }
                    user_list.append(user_data)
                except Exception as e:
                    print(f"处理用户 {i+1} 失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        print(f"成功处理 {len(user_list)} 个用户")
        
        # 计算今日和昨日活跃用户数
        from datetime import datetime, timedelta
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start
        
        today_active_users = db.session.execute(
            db.text("""
                SELECT COUNT(DISTINCT final_promotion_code) as active_count
                FROM user_access_logs 
                WHERE visit_time >= :start_time AND visit_time < :end_time
                AND final_promotion_code IS NOT NULL
            """),
            {'start_time': today_start, 'end_time': today_end}
        ).fetchone()
        
        yesterday_active_users = db.session.execute(
            db.text("""
                SELECT COUNT(DISTINCT final_promotion_code) as active_count
                FROM user_access_logs 
                WHERE visit_time >= :start_time AND visit_time < :end_time
                AND final_promotion_code IS NOT NULL
            """),
            {'start_time': yesterday_start, 'end_time': yesterday_end}
        ).fetchone()
        
        print("=" * 50)
        return jsonify({
            'success': True,
            'users': user_list,
            'total_count': len(user_list),
            'statistics': {
                'today_active_users': today_active_users[0] if today_active_users else 0,
                'yesterday_active_users': yesterday_active_users[0] if yesterday_active_users else 0
            }
        })
        
    except Exception as e:
        print(f"获取推广用户列表失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取推广用户列表失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/user/own-orders', methods=['GET'])
@login_required
def get_user_own_orders():
    """获取用户自己的订单（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
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
                FROM orders 
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


@admin_promotion_api_bp.route('/api/promotion/visits/detail', methods=['GET'])
@login_required
def get_admin_promotion_visits_detail():
    """获取推广访问详细记录（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        
        promotion_code = request.args.get('promotionCode')
        
        if not promotion_code:
            return jsonify({
                'success': False,
                'message': '推广码不能为空'
            }), 400
        
        # 查询该推广码的访问记录（使用新的user_access_logs表）
        visits_result = db.session.execute(
            db.text("""
                SELECT session_id, openid, visit_type, visit_time, page_path, user_info, is_authorized
                FROM user_access_logs 
                WHERE final_promotion_code = :promotion_code
                ORDER BY visit_time DESC
                LIMIT 50
            """),
            {'promotion_code': promotion_code}
        ).fetchall()
        
        visit_list = []
        for visit in visits_result:
            # 解析用户信息
            user_info = {}
            if visit[5]:  # user_info字段
                try:
                    user_info = json.loads(visit[5])
                except:
                    user_info = {}
            
            # 转换时间为本地时间
            visit_time = visit[3]
            if visit_time:
                try:
                    import pytz
                    # 如果时间格式是字符串，转换为datetime对象
                    if isinstance(visit_time, str):
                        # SQLite存储的是UTC时间字符串，需要解析并转换
                        dt = datetime.fromisoformat(visit_time)
                        # 假设数据库存储的是UTC时间，转换为本地时间
                        utc_dt = pytz.utc.localize(dt)
                        local_dt = utc_dt.astimezone(pytz.timezone('Asia/Shanghai'))
                        visit_time_str = local_dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        visit_time_str = str(visit_time)
                except Exception as e:
                    print(f"时间转换失败: {e}, 原始时间: {visit_time}")
                    visit_time_str = str(visit_time)
            else:
                visit_time_str = None
            
            visit_list.append({
                'id': visit[0],  # session_id作为ID
                'promotion_code': promotion_code,
                'visitor_user_id': visit[0],  # session_id
                'openid': visit[1],
                'visit_time': visit_time_str,  # 本地时间
                'visit_type': visit[2],  # visit_type
                'page_path': visit[4],  # page_path
                'user_info': user_info,
                'is_authorized': bool(visit[6])  # is_authorized
            })
        
        return jsonify({
            'success': True,
            'visits': visit_list,
            'total': len(visit_list)
        })
        
    except Exception as e:
        print(f"获取推广访问详细记录失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取推广访问详细记录失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/visits', methods=['GET'])
@login_required
def get_admin_promotion_visits():
    """获取推广访问统计（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        PromotionTrack = models['PromotionTrack']
        
        # 获取总体访问统计
        try:
            from sqlalchemy import case
            total_stats = db.session.query(
                db.func.count(PromotionTrack.id).label('total_visits'),
                db.func.count(case([(PromotionTrack.visitor_user_id == 'anonymous', 1)], else_=0)).label('anonymous_visits'),
                db.func.count(case([(PromotionTrack.visitor_user_id != 'anonymous', 1)], else_=0)).label('real_visits')
            ).first()
        except Exception as e:
            print(f"总体访问统计查询失败: {e}")
            total_stats = None
        
        # 获取17-19号期间的访问统计
        try:
            october_stats = db.session.query(
                db.func.count(PromotionTrack.id).label('october_visits'),
                db.func.count(case([(PromotionTrack.visitor_user_id == 'anonymous', 1)], else_=0)).label('october_anonymous_visits'),
                db.func.count(case([(PromotionTrack.visitor_user_id != 'anonymous', 1)], else_=0)).label('october_real_visits')
            ).filter(
                PromotionTrack.visit_time >= 1760630400000,  # 2025-10-17 00:00:00
                PromotionTrack.visit_time <= 1760889599000   # 2025-10-19 23:59:59
            ).first()
        except Exception as e:
            print(f"17-19号访问统计查询失败: {e}")
            october_stats = None
        
        # 获取推广码访问排行
        try:
            promotion_ranking = db.session.query(
                PromotionTrack.promotion_code,
                db.func.count(PromotionTrack.id).label('visit_count'),
                db.func.count(case([(PromotionTrack.visitor_user_id == 'anonymous', 1)], else_=0)).label('anonymous_count')
            ).group_by(PromotionTrack.promotion_code).order_by(db.func.count(PromotionTrack.id).desc()).limit(10).all()
        except Exception as e:
            print(f"推广码排行查询失败: {e}")
            promotion_ranking = []
        
        # 获取最近的访问记录
        recent_visits = PromotionTrack.query.order_by(PromotionTrack.visit_time.desc()).limit(20).all()
        
        recent_visit_list = []
        for visit in recent_visits:
            visit_time = datetime.fromtimestamp(visit.visit_time / 1000) if visit.visit_time else None
            recent_visit_list.append({
                'id': visit.id,
                'promotion_code': visit.promotion_code,
                'referrer_user_id': visit.referrer_user_id,
                'visitor_id': visit.visitor_user_id,
                'visit_time': visit_time.strftime('%Y-%m-%d %H:%M:%S') if visit_time else None,
                'is_anonymous': visit.visitor_user_id == 'anonymous',
                'create_time': visit.create_time.isoformat() if visit.create_time else None
            })
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_visits': total_stats.total_visits if total_stats else 0,
                'anonymous_visits': total_stats.anonymous_visits if total_stats else 0,
                'real_visits': total_stats.real_visits if total_stats else 0,
                'october_17_19_visits': october_stats.october_visits if october_stats else 0,
                'october_anonymous_visits': october_stats.october_anonymous_visits if october_stats else 0,
                'october_real_visits': october_stats.october_real_visits if october_stats else 0
            },
            'promotion_ranking': [
                {
                    'promotion_code': item.promotion_code,
                    'visit_count': item.visit_count,
                    'anonymous_count': item.anonymous_count
                } for item in promotion_ranking
            ],
            'recent_visits': recent_visit_list
        })
        
    except Exception as e:
        print(f"获取推广访问统计失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取推广访问统计失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/commission/<int:commission_id>', methods=['GET'])
@login_required
def get_admin_commission_detail(commission_id):
    """获取分佣详情（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        Commission = models['Commission']
        PromotionUser = models['PromotionUser']
        
        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({
                'success': False,
                'message': '分佣记录不存在'
            }), 404
        
        user = PromotionUser.query.filter_by(user_id=commission.referrer_user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '推广用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'commission': {
                'id': commission.id,
                'order_id': commission.order_id,
                'amount': commission.amount,
                'rate': commission.rate,
                'status': commission.status,
                'create_time': commission.create_time.isoformat() if commission.create_time else None,
                'complete_time': commission.complete_time.isoformat() if commission.complete_time else None,
                'user': {
                    'user_id': user.user_id,
                    'promotion_code': user.promotion_code,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'total_earnings': user.total_earnings,
                    'total_orders': user.total_orders
                }
            }
        })
        
    except Exception as e:
        print(f"获取分佣详情失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取分佣详情失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/commission/<int:commission_id>/status', methods=['PUT'])
@login_required
def update_commission_status(commission_id):
    """更新分佣状态（后台管理）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        Commission = models['Commission']
        send_commission_notification_auto = models.get('send_commission_notification_auto')
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'completed', 'cancelled']:
            return jsonify({
                'success': False,
                'message': '无效的状态值'
            }), 400
        
        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({
                'success': False,
                'message': '分佣记录不存在'
            }), 404
        
        old_status = commission.status
        commission.status = new_status
        
        # 如果状态变为completed，更新完成时间
        if new_status == 'completed' and not commission.complete_time:
            commission.complete_time = datetime.now()
            
            # 自动发送推广收益通知
            if send_commission_notification_auto:
                try:
                    send_commission_notification_auto(commission)
                except Exception as e:
                    print(f"发送分佣通知失败: {e}")
        
        db.session.commit()
        
        print(f"分佣状态更新: {commission_id} {old_status} -> {new_status}")
        
        return jsonify({
            'success': True,
            'message': '分佣状态更新成功'
        })
        
    except Exception as e:
        print(f"更新分佣状态失败: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新分佣状态失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/commission/<int:commission_id>', methods=['DELETE'])
@login_required
def delete_commission(commission_id):
    """删除分佣记录（后台管理）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        Commission = models['Commission']
        
        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({
                'success': False,
                'message': '分佣记录不存在'
            }), 404
        
        db.session.delete(commission)
        db.session.commit()
        
        print(f"分佣记录删除成功: ID={commission_id}")
        
        return jsonify({
            'success': True,
            'message': '分佣记录删除成功'
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"删除分佣记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'删除分佣记录失败: {str(e)}'
        }), 500


@admin_promotion_api_bp.route('/api/promotion/user/<user_id>', methods=['DELETE'])
@login_required
def delete_promotion_user(user_id):
    """删除推广用户（后台管理）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        PromotionUser = models['PromotionUser']
        Commission = models['Commission']
        PromotionTrack = models['PromotionTrack']
        
        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '推广用户不存在'
            }), 404
        
        # 删除相关的分佣记录
        Commission.query.filter_by(referrer_user_id=user_id).delete()
        
        # ⭐ 提现功能已删除，不再删除提现记录
        
        # 删除相关的推广访问记录
        PromotionTrack.query.filter_by(referrer_user_id=user_id).delete()
        PromotionTrack.query.filter_by(visitor_user_id=user_id).delete()
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        print(f"推广用户删除成功: user_id={user_id}, 推广码={user.promotion_code}")
        
        return jsonify({
            'success': True,
            'message': '推广用户删除成功'
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"删除推广用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'删除推广用户失败: {str(e)}'
        }), 500
