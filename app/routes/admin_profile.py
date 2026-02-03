# -*- coding: utf-8 -*-
"""
管理员个人中心相关路由
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, date
from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required, admin_api_required
import json

admin_profile_bp = Blueprint('admin_profile', __name__)


@admin_profile_bp.route('/admin/profile')
@login_required
@admin_required
def admin_profile():
    """个人中心页面"""
    return render_template('admin/profile.html')


@admin_profile_bp.route('/api/admin/profile', methods=['GET'])
@login_required
@admin_api_required
def get_profile():
    """获取当前用户信息"""
    try:
        models = get_models(['db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        
        # 检查并重置每日使用次数
        from datetime import date
        today = date.today()
        if hasattr(current_user, 'playground_last_reset_date'):
            if not current_user.playground_last_reset_date or current_user.playground_last_reset_date != today:
                current_user.playground_used_today = 0
                current_user.playground_last_reset_date = today
                db.session.commit()
        
        # 计算剩余次数
        daily_limit = getattr(current_user, 'playground_daily_limit', 0) or 0
        used_today = getattr(current_user, 'playground_used_today', 0) or 0
        remaining = daily_limit - used_today if daily_limit > 0 else -1  # -1 表示无限制
        
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'role': current_user.role,
                'contact_person': getattr(current_user, 'contact_person', None),
                'contact_phone': getattr(current_user, 'contact_phone', None),
                'wechat_id': getattr(current_user, 'wechat_id', None),
                'playground_daily_limit': daily_limit,
                'playground_used_today': used_today,
                'playground_remaining': remaining
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户信息失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/profile', methods=['POST'])
@login_required
@admin_api_required
def update_profile():
    """更新用户信息"""
    try:
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        
        data = request.get_json()
        user = User.query.get(current_user.id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 更新允许修改的字段
        if 'contact_person' in data:
            user.contact_person = data['contact_person']
        if 'contact_phone' in data:
            user.contact_phone = data['contact_phone']
        if 'wechat_id' in data:
            user.wechat_id = data['wechat_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '信息更新成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/profile/password', methods=['POST'])
@login_required
@admin_api_required
def change_password():
    """修改密码"""
    try:
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'message': '密码不能为空'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度至少6位'}), 400
        
        user = User.query.get(current_user.id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 验证旧密码
        if not check_password_hash(user.password, old_password):
            return jsonify({'success': False, 'message': '原密码错误'}), 400
        
        # 更新密码
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'修改密码失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/profile/logs', methods=['GET'])
@login_required
@admin_api_required
def get_operation_logs():
    """获取操作日志"""
    try:
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 这里需要根据实际的操作日志表来实现
        # 暂时返回空列表，后续可以添加操作日志表
        logs = []
        total = 0
        
        # TODO: 实现操作日志查询
        # 可以创建一个 OperationLog 模型来记录操作
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日志失败: {str(e)}'}), 500


# ============================================================================
# 管理员账户配置API（仅admin可访问）
# ============================================================================

@admin_profile_bp.route('/api/admin/users', methods=['GET'])
@login_required
@admin_api_required
def get_admin_users():
    """获取所有管理员账户列表（仅admin）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足，仅管理员可访问'}), 403
        
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        
        # 只获取admin和operator角色的用户
        users = User.query.filter(User.role.in_(['admin', 'operator'])).all()
        
        users_list = []
        today = date.today()
        for user in users:
            # 检查是否需要重置每日使用次数
            if hasattr(user, 'playground_last_reset_date'):
                if user.playground_last_reset_date != today:
                    user.playground_used_today = 0
                    user.playground_last_reset_date = today
                    db.session.commit()
            
            users_list.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'can_preview': getattr(user, 'can_preview', True),
                'playground_daily_limit': getattr(user, 'playground_daily_limit', 0),
                'playground_used_today': getattr(user, 'playground_used_today', 0),
                'page_permissions': getattr(user, 'page_permissions', None),
                'contact_person': getattr(user, 'contact_person', None),
                'contact_phone': getattr(user, 'contact_phone', None),
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
            })
        
        return jsonify({
            'success': True,
            'users': users_list
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取账户列表失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/users', methods=['POST'])
@login_required
@admin_api_required
def create_admin_user():
    """创建新的管理员账户（仅admin）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足，仅管理员可创建账户'}), 403
        
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'operator')
        can_preview = data.get('can_preview', True)
        playground_daily_limit = data.get('playground_daily_limit', 0)
        page_permissions = data.get('page_permissions', '[]')  # JSON字符串
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度至少6位'}), 400
        
        if role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '角色只能是admin或operator'}), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        new_user = User(
            username=username,
            password=password_hash,
            role=role,
            can_preview=can_preview,
            playground_daily_limit=playground_daily_limit,
            playground_used_today=0,
            playground_last_reset_date=date.today(),
            page_permissions=page_permissions if isinstance(page_permissions, str) else json.dumps(page_permissions)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # 验证密码哈希是否正确（用于调试）
        from werkzeug.security import check_password_hash
        if not check_password_hash(new_user.password, password):
            print(f"警告: 用户 {username} 的密码哈希验证失败")
        else:
            print(f"成功: 用户 {username} 创建成功，密码哈希验证通过")
        
        return jsonify({
            'success': True,
            'message': '账户创建成功',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'role': new_user.role
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建账户失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/users/<int:user_id>', methods=['GET'])
@login_required
@admin_api_required
def get_admin_user(user_id):
    """获取单个管理员账户信息（仅admin）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models(['User'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        User = models['User']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '只能查看管理员和操作员账户'}), 403
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'can_preview': getattr(user, 'can_preview', True),
                'playground_daily_limit': getattr(user, 'playground_daily_limit', 0),
                'playground_used_today': getattr(user, 'playground_used_today', 0),
                'page_permissions': getattr(user, 'page_permissions', None)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户信息失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_api_required
def update_admin_user(user_id):
    """更新管理员账户信息（仅admin）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '只能编辑管理员和操作员账户'}), 403
        
        data = request.get_json()
        
        # 更新用户名
        if 'username' in data:
            new_username = data['username']
            if new_username != user.username:
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    return jsonify({'success': False, 'message': '用户名已存在'}), 400
                user.username = new_username
        
        # 更新密码（如果提供）
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'success': False, 'message': '密码长度至少6位'}), 400
            user.password = generate_password_hash(data['password'])
        
        # 更新角色
        if 'role' in data:
            if data['role'] not in ['admin', 'operator']:
                return jsonify({'success': False, 'message': '角色只能是admin或operator'}), 400
            user.role = data['role']
        
        # 更新权限配置
        if 'can_preview' in data:
            user.can_preview = bool(data['can_preview'])
        
        if 'playground_daily_limit' in data:
            user.playground_daily_limit = int(data['playground_daily_limit']) if data['playground_daily_limit'] else 0
        
        if 'page_permissions' in data:
            page_permissions = data['page_permissions']
            if isinstance(page_permissions, str):
                user.page_permissions = page_permissions
            else:
                user.page_permissions = json.dumps(page_permissions)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '账户更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新账户失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_api_required
def delete_admin_user(user_id):
    """删除管理员账户（仅admin）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': '不能删除自己的账户'}), 400
        
        if user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '只能删除管理员和操作员账户'}), 403
        
        # 检查是否还有其他admin账户
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({'success': False, 'message': '至少需要保留一个管理员账户'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '账户删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除账户失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/users/<int:user_id>/password', methods=['PUT'])
@login_required
@admin_api_required
def change_user_password(user_id):
    """修改用户密码（仅admin）"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models(['User', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        db = models['db']
        User = models['User']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '只能修改管理员和操作员账户的密码'}), 403
        
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password:
            return jsonify({'success': False, 'message': '密码不能为空'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '密码长度至少6位'}), 400
        
        # 更新密码
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'修改密码失败: {str(e)}'}), 500
