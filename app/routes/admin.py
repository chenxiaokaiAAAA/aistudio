# -*- coding: utf-8 -*-
"""
管理后台路由模块（主文件）
整合所有管理后台相关的子模块
"""
from flask import Blueprint

# 创建主蓝图
admin_bp = Blueprint('admin', __name__)

# 导入并注册所有子模块
from app.routes.admin_routes import admin_routes_bp
from app.routes.admin_system_api import admin_system_api_bp
from app.routes.admin_print_config_api import admin_print_config_api_bp

# 注册子蓝图到主蓝图
admin_bp.register_blueprint(admin_routes_bp)
admin_bp.register_blueprint(admin_system_api_bp)
admin_bp.register_blueprint(admin_print_config_api_bp)

# 导出主蓝图（供test_server.py使用）
__all__ = ['admin_bp']
