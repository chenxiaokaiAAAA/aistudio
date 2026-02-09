# -*- coding: utf-8 -*-
"""
用户相关API路由模块
整合所有用户相关的子模块
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint

# 创建主蓝图
user_api_bp = Blueprint("user_api", __name__, url_prefix="/api/user")

# 导入所有子模块（导入时会自动注册路由到主蓝图）
# 注意：子模块需要使用 user_api_bp 来注册路由
from . import auth, commission, coupons, messages, profile, promotion, visit
