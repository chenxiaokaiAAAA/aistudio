#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限检查辅助函数
"""

from functools import wraps
from flask import redirect, url_for, flash, abort

def is_full_admin(current_user):
    """检查是否为超级管理员"""
    return current_user.role == 'admin'

def is_admin_or_operator(current_user):
    """检查是否为管理员或营运管理员"""
    return current_user.role in ['admin', 'operator']

def require_full_admin(f):
    """装饰器：要求超级管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not is_full_admin(current_user):
            flash('权限不足：此功能需要超级管理员权限', 'error')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """装饰器：要求管理员权限（包括营运管理员）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not is_admin_or_operator(current_user):
            flash('权限不足', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def can_manage_franchisee(current_user):
    """检查是否可以管理加盟商"""
    return is_full_admin(current_user)

def can_recharge_franchisee(current_user):
    """检查是否可以充值加盟商"""
    return is_full_admin(current_user)


