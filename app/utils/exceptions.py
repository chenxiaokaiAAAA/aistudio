# -*- coding: utf-8 -*-
"""
统一异常类定义
"""

import logging

logger = logging.getLogger(__name__)
from flask import jsonify


class APIError(Exception):
    """API错误基类"""

    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(APIError):
    """数据验证错误"""

    def __init__(self, message, error_code="VALIDATION_ERROR"):
        super().__init__(message, status_code=400, error_code=error_code)


class AuthenticationError(APIError):
    """认证错误"""

    def __init__(self, message="未授权访问", error_code="AUTH_ERROR"):
        super().__init__(message, status_code=401, error_code=error_code)


class PermissionError(APIError):
    """权限错误"""

    def __init__(self, message="权限不足", error_code="PERMISSION_ERROR"):
        super().__init__(message, status_code=403, error_code=error_code)


class NotFoundError(APIError):
    """资源未找到错误"""

    def __init__(self, message="资源未找到", error_code="NOT_FOUND"):
        super().__init__(message, status_code=404, error_code=error_code)


class ServerError(APIError):
    """服务器内部错误"""

    def __init__(self, message="服务器内部错误", error_code="SERVER_ERROR"):
        super().__init__(message, status_code=500, error_code=error_code)


def handle_api_error(error):
    """统一处理API错误"""
    response = {"status": "error", "message": error.message, "error_code": error.error_code}
    return jsonify(response), error.status_code
