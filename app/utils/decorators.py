# -*- coding: utf-8 -*-
"""
装饰器模块
提供权限检查、错误处理等装饰器
"""

import logging
import os
from functools import wraps

from flask import jsonify, redirect, request, url_for
from flask_login import current_user

# 导入统一异常类
from app.utils.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    PermissionError,
    ServerError,
    ValidationError,
    handle_api_error,
)

logger = logging.getLogger(__name__)


def admin_required(f):
    """
    管理员权限装饰器
    要求用户必须是 admin 或 operator 角色
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role not in ["admin", "operator"]:
            return redirect(url_for("auth.login"))
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
            return redirect(url_for("auth.login"))
        if current_user.role != "operator":
            return redirect(url_for("auth.login"))
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
            return jsonify({"status": "error", "message": "未登录"}), 401
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403
        return f(*args, **kwargs)

    return decorated_function


def handle_api_errors(f):
    """
    API错误处理装饰器
    统一处理异常并返回JSON格式的错误响应
    生产环境隐藏详细错误信息，避免泄露敏感信息
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            # 使用统一异常处理
            return handle_api_error(e)
        except ValueError as e:
            logger.warning(f"数据验证错误: {str(e)}", extra={"path": request.path})
            return (
                jsonify({"status": "error", "message": str(e), "error_code": "VALIDATION_ERROR"}),
                400,
            )
        except PermissionError as e:
            logger.warning(
                f"权限错误: {str(e)}",
                extra={
                    "path": request.path,
                    "user": current_user.id if current_user.is_authenticated else None,
                },
            )
            return (
                jsonify({"status": "error", "message": str(e), "error_code": "PERMISSION_ERROR"}),
                403,
            )
        except Exception as e:
            # 生产环境隐藏详细错误
            is_production = (
                os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENV") == "production"
            )

            # 记录详细错误到日志
            logger.error(
                f"API错误: {str(e)}",
                exc_info=True,
                extra={
                    "path": request.path,
                    "method": request.method,
                    "user": current_user.id if current_user.is_authenticated else None,
                },
            )

            # 返回用户友好的错误信息
            if is_production:
                error_message = "服务器内部错误，请稍后重试"
            else:
                error_message = f"服务器错误: {str(e)}"

            return (
                jsonify(
                    {"status": "error", "message": error_message, "error_code": "SERVER_ERROR"}
                ),
                500,
            )

    return decorated_function
