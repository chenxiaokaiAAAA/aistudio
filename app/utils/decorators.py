# -*- coding: utf-8 -*-
"""
装饰器模块
提供权限检查、错误处理等装饰器
"""
from functools import wraps
from flask import redirect, url_for, jsonify
from flask_login import current_user


def admin_required(f):
    """
    管理员权限装饰器
    要求用户必须是 admin 或 operator 角色
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'operator']:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def operator_required(f):
    """
    操作员权限装饰器
    要求用户必须是 operator 角色
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'operator':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_api_required(f):
    """
    管理员API权限装饰器（返回JSON响应）
    要求用户必须是 admin 或 operator 角色
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error', 'message': '未登录'}), 401
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated_function


def handle_api_errors(f):
    """
    API错误处理装饰器
    统一处理异常并返回JSON格式的错误响应
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
        except PermissionError as e:
            return jsonify({'status': 'error', 'message': str(e)}), 403
        except Exception as e:
            print(f"API错误: {str(e)}")
            return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500
    return decorated_function
