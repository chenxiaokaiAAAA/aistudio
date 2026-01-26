# -*- coding: utf-8 -*-
"""
店员权限管理路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import json
from app.routes.franchisee.common import get_models

bp = Blueprint('staff_permission', __name__, url_prefix='/staff-permission')


def require_admin():
    """检查管理员权限"""
    if current_user.role != 'admin':
        flash('权限不足', 'error')
        return redirect(url_for('admin_dashboard'))
    return None


@bp.route('/franchisee/<int:franchisee_id>/staff')
@login_required
def staff_list(franchisee_id):
    """店员列表页面"""
    if require_admin():
        return require_admin()
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db = models['db']
    FranchiseeAccount = models['FranchiseeAccount']
    StaffUser = models.get('StaffUser')
    
    if not StaffUser:
        flash('店员用户模型未找到', 'error')
        return redirect(url_for('franchisee.franchisee_admin.admin_franchisee_list'))
    
    franchisee = FranchiseeAccount.query.get_or_404(franchisee_id)
    staff_users = StaffUser.query.filter_by(franchisee_id=franchisee_id).order_by(StaffUser.created_at.desc()).all()
    
    return render_template('admin/staff_list.html', 
                         franchisee=franchisee, 
                         staff_users=staff_users)


@bp.route('/franchisee/<int:franchisee_id>/staff/add', methods=['GET', 'POST'])
@login_required
def staff_add(franchisee_id):
    """添加店员"""
    if require_admin():
        return require_admin()
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db = models['db']
    FranchiseeAccount = models['FranchiseeAccount']
    StaffUser = models.get('StaffUser')
    
    if not StaffUser:
        flash('店员用户模型未找到', 'error')
        return redirect(url_for('franchisee.franchisee_admin.admin_franchisee_list'))
    
    franchisee = FranchiseeAccount.query.get_or_404(franchisee_id)
    
    if request.method == 'POST':
        try:
            phone = request.form.get('phone', '').strip()
            openid = request.form.get('openid', '').strip()
            name = request.form.get('name', '').strip()
            role = request.form.get('role', 'staff').strip()
            notes = request.form.get('notes', '').strip()
            
            # 验证：至少需要手机号或openid之一
            if not phone and not openid:
                flash('请至少填写手机号或openid之一', 'error')
                return render_template('admin/staff_add.html', franchisee=franchisee)
            
            # 检查是否已存在
            existing = None
            if phone:
                existing = StaffUser.query.filter_by(franchisee_id=franchisee_id, phone=phone).first()
            elif openid:
                existing = StaffUser.query.filter_by(franchisee_id=franchisee_id, openid=openid).first()
            
            if existing:
                flash('该用户已存在', 'error')
                return render_template('admin/staff_add.html', franchisee=franchisee)
            
            # 权限配置
            permissions = {
                'view_today_orders': request.form.get('view_today_orders') == 'on',
                'view_store_images': request.form.get('view_store_images') == 'on',
                'view_all_orders': request.form.get('view_all_orders') == 'on',
                'view_statistics': request.form.get('view_statistics') == 'on',
                'groupon_verify': request.form.get('groupon_verify') == 'on',
            }
            
            staff_user = StaffUser(
                franchisee_id=franchisee_id,
                phone=phone if phone else None,
                openid=openid if openid else None,
                name=name,
                role=role,
                permissions=json.dumps(permissions, ensure_ascii=False),
                notes=notes,
                status='active'
            )
            
            db.session.add(staff_user)
            db.session.commit()
            
            flash('店员添加成功', 'success')
            return redirect(url_for('staff_permission.staff_list', franchisee_id=franchisee_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'error')
    
    return render_template('admin/staff_add.html', franchisee=franchisee)


@bp.route('/franchisee/<int:franchisee_id>/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@login_required
def staff_edit(franchisee_id, staff_id):
    """编辑店员"""
    if require_admin():
        return require_admin()
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db = models['db']
    FranchiseeAccount = models['FranchiseeAccount']
    StaffUser = models.get('StaffUser')
    
    if not StaffUser:
        flash('店员用户模型未找到', 'error')
        return redirect(url_for('franchisee.franchisee_admin.admin_franchisee_list'))
    
    franchisee = FranchiseeAccount.query.get_or_404(franchisee_id)
    staff_user = StaffUser.query.filter_by(id=staff_id, franchisee_id=franchisee_id).first_or_404()
    
    if request.method == 'POST':
        try:
            phone = request.form.get('phone', '').strip()
            openid = request.form.get('openid', '').strip()
            name = request.form.get('name', '').strip()
            role = request.form.get('role', 'staff').strip()
            status = request.form.get('status', 'active').strip()
            notes = request.form.get('notes', '').strip()
            
            # 验证：至少需要手机号或openid之一
            if not phone and not openid:
                flash('请至少填写手机号或openid之一', 'error')
                return render_template('admin/staff_edit.html', franchisee=franchisee, staff_user=staff_user)
            
            # 检查是否与其他用户冲突
            existing = None
            if phone and phone != staff_user.phone:
                existing = StaffUser.query.filter(
                    StaffUser.franchisee_id == franchisee_id,
                    StaffUser.phone == phone,
                    StaffUser.id != staff_id
                ).first()
            elif openid and openid != staff_user.openid:
                existing = StaffUser.query.filter(
                    StaffUser.franchisee_id == franchisee_id,
                    StaffUser.openid == openid,
                    StaffUser.id != staff_id
                ).first()
            
            if existing:
                flash('该用户已存在', 'error')
                return render_template('admin/staff_edit.html', franchisee=franchisee, staff_user=staff_user)
            
            # 更新信息
            staff_user.phone = phone if phone else None
            staff_user.openid = openid if openid else None
            staff_user.name = name
            staff_user.role = role
            staff_user.status = status
            staff_user.notes = notes
            
            # 权限配置
            permissions = {
                'view_today_orders': request.form.get('view_today_orders') == 'on',
                'view_store_images': request.form.get('view_store_images') == 'on',
                'view_all_orders': request.form.get('view_all_orders') == 'on',
                'view_statistics': request.form.get('view_statistics') == 'on',
                'groupon_verify': request.form.get('groupon_verify') == 'on',
            }
            staff_user.permissions = json.dumps(permissions, ensure_ascii=False)
            staff_user.updated_at = datetime.now()
            
            db.session.commit()
            
            flash('店员信息更新成功', 'success')
            return redirect(url_for('staff_permission.staff_list', franchisee_id=franchisee_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'error')
    
    # 解析权限
    try:
        permissions = json.loads(staff_user.permissions) if staff_user.permissions else {}
    except:
        permissions = {}
    
    return render_template('admin/staff_edit.html', 
                         franchisee=franchisee, 
                         staff_user=staff_user,
                         permissions=permissions)


@bp.route('/franchisee/<int:franchisee_id>/staff/<int:staff_id>/delete', methods=['POST'])
@login_required
def staff_delete(franchisee_id, staff_id):
    """删除店员"""
    if require_admin():
        return require_admin()
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db = models['db']
    StaffUser = models.get('StaffUser')
    
    if not StaffUser:
        flash('店员用户模型未找到', 'error')
        return redirect(url_for('franchisee.franchisee_admin.admin_franchisee_list'))
    
    staff_user = StaffUser.query.filter_by(id=staff_id, franchisee_id=franchisee_id).first_or_404()
    
    try:
        db.session.delete(staff_user)
        db.session.commit()
        flash('店员删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('staff_permission.staff_list', franchisee_id=franchisee_id))
