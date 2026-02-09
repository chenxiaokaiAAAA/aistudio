# -*- coding: utf-8 -*-
"""
管理后台支付管理路由模块
整合优惠券管理、退款审核、团购核销等功能
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
bp = Blueprint("admin_payment_management", __name__)


@bp.route("/admin/payment")
@login_required
@admin_required
def payment_management():
    """支付管理主页面"""
    return render_template("admin/payment_management.html")


@bp.route("/admin/payment/coupons")
@login_required
@admin_required
def payment_coupons():
    """优惠券管理（重定向到原优惠券页面）"""
    return redirect("/admin/coupons")


@bp.route("/admin/payment/refunds")
@login_required
@admin_required
def payment_refunds():
    """退款审核页面"""
    models = get_models(["Order", "FranchiseeAccount", "db"])
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin.admin_routes.admin_dashboard"))

    Order = models["Order"]
    FranchiseeAccount = models["FranchiseeAccount"]
    db = models["db"]

    # 获取筛选参数
    status = request.args.get("status", "all")  # all, pending, approved, rejected
    franchisee_id = request.args.get("franchisee_id", "")
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # 构建查询 - 检查字段是否存在
    try:
        # 检查refund_request_status字段是否存在
        inspector = db.inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("orders")]

        if "refund_request_status" in columns:
            query = Order.query.filter(Order.refund_request_status.isnot(None))
        else:
            # 如果字段不存在，返回空查询
            query = Order.query.filter(False)
    except Exception as e:
        logger.info(f"检查数据库字段失败: {e}")
        # 如果检查失败，尝试使用hasattr检查
        if hasattr(Order, "refund_request_status"):
            query = Order.query.filter(Order.refund_request_status.isnot(None))
        else:
            query = Order.query.filter(False)

    if status != "all":
        query = query.filter(Order.refund_request_status == status)

    if franchisee_id:
        query = query.filter(Order.franchisee_id == int(franchisee_id))

    # 分页
    total_count = query.count()
    total_pages = (total_count + per_page - 1) // per_page
    refund_requests = (
        query.order_by(Order.refund_request_time.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # 获取所有加盟商
    franchisees = (
        FranchiseeAccount.query.filter_by(status="active")
        .order_by(FranchiseeAccount.company_name)
        .all()
    )

    # 统计数据 - 检查字段是否存在
    try:
        inspector = db.inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("orders")]

        if "refund_request_status" in columns:
            pending_count = Order.query.filter(Order.refund_request_status == "pending").count()
            approved_count = Order.query.filter(Order.refund_request_status == "approved").count()
            rejected_count = Order.query.filter(Order.refund_request_status == "rejected").count()
        else:
            pending_count = 0
            approved_count = 0
            rejected_count = 0
    except Exception as e:
        logger.info(f"获取统计数据失败: {e}")
        pending_count = 0
        approved_count = 0
        rejected_count = 0

    return render_template(
        "admin/refund_audit.html",
        refund_requests=refund_requests,
        franchisees=franchisees,
        status=status,
        franchisee_id=franchisee_id,
        current_page=page,
        total_pages=total_pages,
        total_count=total_count,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )


@bp.route("/admin/payment/groupon")
@login_required
@admin_required
def payment_groupon():
    """团购核销页面（重定向到独立的团购核销记录页面）"""
    return redirect("/admin/groupon/verify")
