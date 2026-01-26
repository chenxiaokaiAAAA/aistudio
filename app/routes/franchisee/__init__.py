# -*- coding: utf-8 -*-
"""
加盟商路由模块
统一注册所有子模块的蓝图
"""
from flask import Blueprint

# 创建主蓝图
franchisee_bp = Blueprint('franchisee', __name__, url_prefix='/franchisee')

# 导入并注册所有子模块
from . import admin, frontend, api

# 注册子蓝图到主蓝图
franchisee_bp.register_blueprint(admin.bp)
franchisee_bp.register_blueprint(frontend.bp)
franchisee_bp.register_blueprint(api.bp)
