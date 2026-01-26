# -*- coding: utf-8 -*-
"""
管理员个人中心相关路由
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from app.utils.db_utils import get_models

admin_profile_bp = Blueprint('admin_profile', __name__)


@admin_profile_bp.route('/admin/profile')
@login_required
def admin_profile():
    """个人中心页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    return render_template('admin/profile.html')


@admin_profile_bp.route('/api/admin/profile', methods=['GET'])
@login_required
def get_profile():
    """获取当前用户信息"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'role': current_user.role,
                'contact_person': getattr(current_user, 'contact_person', None),
                'contact_phone': getattr(current_user, 'contact_phone', None),
                'wechat_id': getattr(current_user, 'wechat_id', None)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户信息失败: {str(e)}'}), 500


@admin_profile_bp.route('/api/admin/profile', methods=['POST'])
@login_required
def update_profile():
    """更新用户信息"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
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
def change_password():
    """修改密码"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
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
def get_operation_logs():
    """获取操作日志"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
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
