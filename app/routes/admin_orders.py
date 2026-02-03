# -*- coding: utf-8 -*-
"""
订单管理路由模块（主文件）
整合所有订单管理相关的子模块
"""
from flask import Blueprint

# 创建主蓝图
admin_orders_bp = Blueprint('admin_orders', __name__)

# 导入并注册所有子模块
from app.routes.admin_orders_list_api import admin_orders_list_bp
from app.routes.admin_orders_detail_api import admin_orders_detail_bp
from app.routes.admin_orders_operations_api import admin_orders_operations_bp

# 注册子蓝图到主蓝图
admin_orders_bp.register_blueprint(admin_orders_list_bp)
admin_orders_bp.register_blueprint(admin_orders_detail_bp)
admin_orders_bp.register_blueprint(admin_orders_operations_bp)

# 导出主蓝图（供test_server.py使用）
__all__ = ['admin_orders_bp']
