#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
产品配置同步管理界面
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from test_server import db, Product, ProductSize
from product_config_sync import product_sync

# 创建蓝图
sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/admin/sync-config')
@login_required
def sync_config_page():
    """产品配置同步管理页面"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    # 检查同步状态
    sync_status = product_sync.check_sync_status()
    
    return render_template('admin/sync_config.html', sync_status=sync_status)

@sync_bp.route('/admin/sync-config', methods=['POST'])
@login_required
def sync_config_action():
    """执行同步操作"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    action = request.form.get('action')
    
    if action == 'manual_sync':
        try:
            success = product_sync.sync_to_printer_config()
            if success:
                flash('手动同步成功！', 'success')
            else:
                flash('手动同步失败！', 'error')
        except Exception as e:
            flash(f'手动同步失败: {str(e)}', 'error')
    
    elif action == 'check_status':
        try:
            sync_status = product_sync.check_sync_status()
            if sync_status:
                flash('同步状态检查完成，配置一致', 'success')
            else:
                flash('同步状态检查完成，发现配置不一致', 'warning')
        except Exception as e:
            flash(f'状态检查失败: {str(e)}', 'error')
    
    return redirect(url_for('sync.sync_config_page'))

@sync_bp.route('/api/sync-status')
@login_required
def api_sync_status():
    """API接口：获取同步状态"""
    if current_user.role != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    try:
        sync_status = product_sync.check_sync_status()
        return jsonify({
            'status': 'success',
            'sync_status': sync_status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@sync_bp.route('/api/manual-sync', methods=['POST'])
@login_required
def api_manual_sync():
    """API接口：手动同步"""
    if current_user.role != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    try:
        success = product_sync.sync_to_printer_config()
        if success:
            return jsonify({
                'status': 'success',
                'message': '同步成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '同步失败'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



