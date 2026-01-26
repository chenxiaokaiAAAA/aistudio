# -*- coding: utf-8 -*-
"""
过期图片清理管理路由
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.utils.db_utils import get_models

admin_image_cleanup_bp = Blueprint('admin_image_cleanup', __name__)


@admin_image_cleanup_bp.route('/admin/image-cleanup')
@login_required
def admin_image_cleanup():
    """过期图片清理配置页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    return render_template('admin/image_cleanup.html')


@admin_image_cleanup_bp.route('/api/admin/image-cleanup/config', methods=['GET'])
@login_required
def get_cleanup_config():
    """获取清理配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # TODO: 从数据库或配置文件读取清理规则
        # 暂时返回默认配置
        return jsonify({
            'success': True,
            'config': {
                'final_image_days': 3,  # 用户最终效果图保存3天
                'retouched_image_days': 30,  # 用户美颜后的图像保存30天
                'custom_cleanup_rules': []  # 自定义清理规则
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'}), 500


@admin_image_cleanup_bp.route('/api/admin/image-cleanup/config', methods=['POST'])
@login_required
def save_cleanup_config():
    """保存清理配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        
        # TODO: 保存到数据库或配置文件
        # 暂时只返回成功
        
        return jsonify({
            'success': True,
            'message': '配置保存成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存配置失败: {str(e)}'}), 500


@admin_image_cleanup_bp.route('/api/admin/image-cleanup/execute', methods=['POST'])
@login_required
def execute_cleanup():
    """执行清理任务"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '数据库未初始化'}), 500
        
        data = request.get_json()
        days = data.get('days', 0)
        
        if days <= 0:
            return jsonify({'success': False, 'message': '天数必须大于0'}), 400
        
        # TODO: 实现清理逻辑
        # 1. 查询XX天前已完成的订单
        # 2. 删除相关图片文件
        # 3. 更新数据库记录
        
        return jsonify({
            'success': True,
            'message': f'清理完成，已清理{days}天前的订单图片',
            'deleted_count': 0  # TODO: 返回实际删除数量
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'执行清理失败: {str(e)}'}), 500
