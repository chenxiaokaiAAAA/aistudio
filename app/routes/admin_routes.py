# -*- coding: utf-8 -*-
"""
管理后台页面路由模块
提供管理后台各个页面的渲染路由
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.utils.decorators import admin_required

# 创建蓝图
admin_routes_bp = Blueprint("admin_routes", __name__)


@admin_routes_bp.route("/admin/styles")
@login_required
@admin_required
def admin_styles():
    """风格分类管理页面"""
    return render_template("admin/styles.html")


@admin_routes_bp.route("/admin/homepage")
@login_required
def admin_homepage():
    """首页配置管理页面"""
    if current_user.role != "admin":
        return redirect(url_for("auth.login"))
    return render_template("admin/homepage.html")


@admin_routes_bp.route("/admin/miniprogram-config")
@login_required
@admin_required
def admin_miniprogram_config():
    """小程序配置管理页面"""
    return render_template("admin/miniprogram_config.html")


@admin_routes_bp.route("/admin/system-config")
@login_required
@admin_required
def admin_system_config():
    """系统配置管理页面"""
    return render_template("admin/system_config.html")


@admin_routes_bp.route("/admin/polling-config")
@login_required
@admin_required
def admin_polling_config():
    """轮询配置管理页面"""
    return render_template("admin/polling_config.html")


@admin_routes_bp.route("/admin")
@login_required
def admin_index():
    """管理后台首页 - 根据角色重定向"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))
    # 操作员跳转到 playground，管理员跳转到仪表盘
    if current_user.role == "operator":
        return redirect(url_for("base.playground"))
    return redirect(url_for("admin.admin_routes.admin_dashboard"))


@admin_routes_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    """管理后台仪表盘大屏"""
    if current_user.role not in ["admin", "operator"]:
        # 如果是商家，跳转到商家控制台
        if current_user.is_authenticated and current_user.role == "merchant":
            return redirect("/merchant/dashboard")
        return redirect(url_for("auth.login"))

    # 检查页面权限（操作员需要检查）
    if current_user.role == "operator":
        from app.utils.permission_utils import has_page_permission

        if not has_page_permission(current_user, "/admin/dashboard"):
            flash("您没有权限访问此页面", "error")
            from app.routes.admin_profile import admin_profile_bp

            return redirect(url_for("admin_profile.admin_profile"))

    from app.utils.admin_helpers import get_models

    models = get_models(
        ["Order", "User", "FranchiseeAccount", "AITask", "AIConfig", "MeituAPICallLog", "db"]
    )
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    db = models["db"]
    Order = models["Order"]
    User = models["User"]
    FranchiseeAccount = models.get("FranchiseeAccount")
    AITask = models.get("AITask")
    MeituAPICallLog = models.get("MeituAPICallLog")
    AIConfig = models.get("AIConfig")

    from datetime import datetime, timedelta

    from sqlalchemy import func, or_

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)

    # 订单统计
    total_orders = Order.query.filter(Order.status != "unpaid").count()
    daily_orders = Order.query.filter(
        func.date(Order.created_at) == today, Order.status != "unpaid"
    ).count()
    yesterday_orders = Order.query.filter(
        func.date(Order.created_at) == yesterday, Order.status != "unpaid"
    ).count()
    week_orders = Order.query.filter(
        func.date(Order.created_at) >= this_week_start, Order.status != "unpaid"
    ).count()
    month_orders = Order.query.filter(
        func.date(Order.created_at) >= this_month_start, Order.status != "unpaid"
    ).count()

    # 业绩统计
    daily_revenue = (
        Order.query.filter(func.date(Order.completed_at) == today, Order.status == "completed")
        .with_entities(func.sum(Order.price))
        .scalar()
        or 0.0
    )

    yesterday_revenue = (
        Order.query.filter(func.date(Order.completed_at) == yesterday, Order.status == "completed")
        .with_entities(func.sum(Order.price))
        .scalar()
        or 0.0
    )

    week_revenue = (
        Order.query.filter(
            func.date(Order.completed_at) >= this_week_start, Order.status == "completed"
        )
        .with_entities(func.sum(Order.price))
        .scalar()
        or 0.0
    )

    month_revenue = (
        Order.query.filter(
            func.date(Order.completed_at) >= this_month_start, Order.status == "completed"
        )
        .with_entities(func.sum(Order.price))
        .scalar()
        or 0.0
    )

    total_revenue = (
        Order.query.filter(Order.status == "completed")
        .with_entities(func.sum(Order.price))
        .scalar()
        or 0.0
    )

    # 订单状态统计
    pending_orders = Order.query.filter(Order.status.in_(["pending", "已支付"])).count()
    processing_orders = Order.query.filter(Order.status == "processing").count()
    completed_orders = Order.query.filter(Order.status == "completed").count()
    # 异常订单：状态为failed或error，或者有printer错误信息的订单
    error_orders = Order.query.filter(
        or_(Order.status.in_(["failed", "error"]), Order.printer_error_message.isnot(None))
    ).count()

    # AI任务统计
    ai_task_stats = {}
    if AITask:
        try:
            total_tasks = AITask.query.count()
            pending_tasks = AITask.query.filter(AITask.status == "pending").count()
            processing_tasks = AITask.query.filter(AITask.status == "processing").count()
            completed_tasks = AITask.query.filter(AITask.status == "completed").count()
            failed_tasks = AITask.query.filter(AITask.status == "failed").count()

            ai_task_stats = {
                "total": total_tasks,
                "pending": pending_tasks,
                "processing": processing_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
            }
        except Exception as e:
            logger.info(f"获取AI任务统计失败: {e}")
            ai_task_stats = {"total": 0, "pending": 0, "processing": 0, "completed": 0, "failed": 0}

    # 美图API调用统计
    meitu_stats = {}
    if MeituAPICallLog:
        try:
            today_calls = MeituAPICallLog.query.filter(
                func.date(MeituAPICallLog.created_at) == today
            ).count()
            total_calls = MeituAPICallLog.query.count()

            meitu_stats = {"today_calls": today_calls, "total_calls": total_calls}
        except Exception as e:
            logger.info(f"获取美图API统计失败: {e}")
            meitu_stats = {"today_calls": 0, "total_calls": 0}

    # 获取品牌名称
    brand_name = "AI拍照机"
    if AIConfig:
        try:
            brand_config = AIConfig.query.filter_by(config_key="brand_name").first()
            if brand_config and brand_config.config_value:
                brand_name = brand_config.config_value
        except Exception as e:
            logger.info(f"获取品牌名称失败: {e}")

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        daily_orders=daily_orders,
        yesterday_orders=yesterday_orders,
        week_orders=week_orders,
        month_orders=month_orders,
        daily_revenue=float(daily_revenue),
        yesterday_revenue=float(yesterday_revenue),
        week_revenue=float(week_revenue),
        month_revenue=float(month_revenue),
        total_revenue=float(total_revenue),
        pending_orders=pending_orders,
        processing_orders=processing_orders,
        completed_orders=completed_orders,
        error_orders=error_orders,
        ai_task_stats=ai_task_stats,
        meitu_stats=meitu_stats,
        brand_name=brand_name,
    )


@admin_routes_bp.route("/admin/promotion")
@login_required
@admin_required
def admin_promotion():
    """推广管理页面"""
    return render_template("admin/promotion_management.html")


@admin_routes_bp.route("/admin/coupons")
@login_required
@admin_required
def admin_coupons():
    """优惠券管理页面"""
    return render_template("admin/coupons.html")


@admin_routes_bp.route("/admin/users")
@login_required
@admin_required
def admin_users():
    """用户管理页面"""
    return render_template("admin/all_users.html")


@admin_routes_bp.route("/admin/print-config")
@login_required
@admin_required
def admin_print_config():
    """打印配置管理页面"""
    return render_template("admin/print_config.html")


@admin_routes_bp.route("/admin/printer")
@login_required
@admin_required
def admin_printer():
    """打印机管理页面"""
    return render_template("admin/printer.html")
