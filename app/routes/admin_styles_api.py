# -*- coding: utf-8 -*-
"""
管理后台风格管理API路由模块（主文件）
整合所有风格管理相关的子模块
"""
from flask import Blueprint

# 创建主蓝图
admin_styles_api_bp = Blueprint('admin_styles_api', __name__, url_prefix='/api/admin/styles')

# 导入并注册所有子模块
from app.routes.admin_styles_categories_api import admin_styles_categories_bp
from app.routes.admin_styles_images_api import admin_styles_images_bp
from app.routes.admin_styles_workflow_api import admin_styles_workflow_bp

# 注册子蓝图到主蓝图
# 注意：workflow_bp 必须先注册，因为它的路由更具体（/images/<id>/api-template）
# 如果 images_bp 先注册，它的 /images/<id> 可能会拦截 workflow_bp 的 /images/<id>/api-template
admin_styles_api_bp.register_blueprint(admin_styles_categories_bp)
admin_styles_api_bp.register_blueprint(admin_styles_workflow_bp)  # 先注册更具体的路由
admin_styles_api_bp.register_blueprint(admin_styles_images_bp)  # 后注册通用路由

# 导出主蓝图（供test_server.py使用）
__all__ = ['admin_styles_api_bp']
