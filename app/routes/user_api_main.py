# -*- coding: utf-8 -*-
"""
用户相关API路由模块（主文件）
整合所有用户相关的子模块
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint

# 创建主蓝图
user_api_bp = Blueprint("user_api", __name__, url_prefix="/api/user")

# 导入并注册所有子模块
from app.routes.user_auth_api import user_auth_api_bp

# 注册子蓝图到主蓝图
user_api_bp.register_blueprint(user_auth_api_bp)

# 导出主蓝图（供test_server.py使用）
__all__ = ["user_api_bp"]
