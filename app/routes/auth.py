# -*- coding: utf-8 -*-
"""
认证相关路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import sys

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if 'test_server' not in sys.modules:
        flash('系统未初始化', 'error')
        return render_template('login.html')
    
    test_server_module = sys.modules['test_server']
    User = test_server_module.User
    db = test_server_module.db
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # 记住登录，维持会话
            login_user(user, remember=True)
            if user.role in ['admin', 'operator']:
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('merchant.merchant_dashboard'))
        # 兼容旧数据：若存的是明文密码，首次登录时自动迁移为哈希
        if user and user.password == password:
            user.password = generate_password_hash(password)
            db.session.commit()
            login_user(user, remember=True)
            if user.role in ['admin', 'operator']:
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('merchant.merchant_dashboard'))
        flash('用户名或密码错误', 'error')
        return render_template('login.html')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('base.index'))
