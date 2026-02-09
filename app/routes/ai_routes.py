# -*- coding: utf-8 -*-
"""
AI任务管理页面路由模块
提供AI任务和配置管理的页面渲染
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

# 创建蓝图
ai_routes_bp = Blueprint("ai_routes", __name__)


@ai_routes_bp.route("/tasks")
@login_required
def ai_tasks():
    """AI任务管理页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))
    return render_template("admin/ai_tasks.html")


@ai_routes_bp.route("/config")
@login_required
def ai_config():
    """AI配置管理页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))
    return render_template("admin/ai_config.html")
