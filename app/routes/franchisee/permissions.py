# -*- coding: utf-8 -*-
"""
加盟商权限配置路由模块
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import json
import sys

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
bp = Blueprint('franchisee_permissions', __name__, url_prefix='/franchisee/admin/accounts')

def require_admin():
    """检查管理员权限"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('权限不足', 'error')
        return redirect(url_for('admin_dashboard'))
    return None

@bp.route('/<int:account_id>/permissions', methods=['GET', 'POST'])
@login_required
def franchisee_permissions(account_id):
    """加盟商权限配置页面"""
    if require_admin():
        return require_admin()
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_admin.admin_franchisee_list'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    StaffUser = models.get('StaffUser')
    db = models['db']
    
    account = FranchiseeAccount.query.get_or_404(account_id)
    
    # 获取子用户列表
    staff_users = []
    if StaffUser:
        staff_users = StaffUser.query.filter_by(franchisee_id=account_id).order_by(StaffUser.created_at.desc()).all()
    
    # 定义可配置的权限列表
    admin_permissions = [
        {'key': 'dashboard', 'name': '仪表盘', 'description': '查看管理后台仪表盘'},
        {'key': 'orders', 'name': '订单管理', 'description': '查看和管理订单'},
        {'key': 'payment', 'name': '支付管理', 'description': '优惠券、退款审核、团购核销'},
        {'key': 'products', 'name': '产品管理', 'description': '查看和管理产品'},
        {'key': 'franchisee', 'name': '加盟商管理', 'description': '查看加盟商信息（仅限自己的账户）'},
    ]
    
    miniprogram_permissions = [
        {'key': 'view_today_orders', 'name': '查看今日订单', 'description': '在小程序中查看今天的订单'},
        {'key': 'view_all_orders', 'name': '查看全部订单', 'description': '在小程序中查看所有订单'},
        {'key': 'view_store_images', 'name': '查看门店图片', 'description': '查看门店用户生成的图片'},
        {'key': 'groupon_verify', 'name': '团购核销', 'description': '在小程序中生成团购核销优惠券'},
        {'key': 'refund_request', 'name': '退款申请', 'description': '针对异常订单申请退款'},
    ]
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # 更新加盟商权限
        account_admin_permissions = data.get('account_admin_permissions', {})
        account_miniprogram_permissions = data.get('account_miniprogram_permissions', {})
        
        # 保存到账户的备注字段或扩展字段（可以扩展FranchiseeAccount模型添加permissions字段）
        # 目前先保存到notes字段（JSON格式）
        account_permissions = {
            'admin': account_admin_permissions,
            'miniprogram': account_miniprogram_permissions
        }
        account.notes = json.dumps(account_permissions) if account_permissions else None
        
        # 更新子用户权限
        if StaffUser:
            staff_permissions_data = data.get('staff_permissions', {})
            for staff_id_str, permissions in staff_permissions_data.items():
                try:
                    staff_id = int(staff_id_str)
                    staff = StaffUser.query.get(staff_id)
                    if staff and staff.franchisee_id == account_id:
                        staff_admin_perms = permissions.get('admin', {})
                        staff_miniprogram_perms = permissions.get('miniprogram', {})
                        staff_permissions = {
                            'admin': staff_admin_perms,
                            'miniprogram': staff_miniprogram_perms
                        }
                        staff.permissions = json.dumps(staff_permissions) if staff_permissions else '{}'
                except (ValueError, TypeError):
                    continue
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'status': 'success',
                'message': '权限配置已保存'
            })
        else:
            flash('权限配置已保存', 'success')
            return redirect(url_for('franchisee.franchisee_admin.admin_franchisee_detail', account_id=account_id))
    
    # 读取现有权限
    account_permissions = {'admin': {}, 'miniprogram': {}}
    if account.notes:
        try:
            account_permissions = json.loads(account.notes)
        except:
            pass
    
    staff_permissions_dict = {}
    for staff in staff_users:
        staff_perms = {'admin': {}, 'miniprogram': {}}
        if staff.permissions:
            try:
                staff_perms = json.loads(staff.permissions)
            except:
                pass
        staff_permissions_dict[staff.id] = staff_perms
    
    return render_template('admin/franchisee_permissions.html',
                         account=account,
                         staff_users=staff_users,
                         admin_permissions=admin_permissions,
                         miniprogram_permissions=miniprogram_permissions,
                         account_permissions=account_permissions,
                         staff_permissions_dict=staff_permissions_dict)
