# -*- coding: utf-8 -*-
"""
加盟商权限配置列表路由模块
在加盟商管理页面统一配置所有加盟商和子用户的权限
"""

import logging

logger = logging.getLogger(__name__)
import json
import sys
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
bp = Blueprint("franchisee_permissions_list", __name__, url_prefix="/franchisee/admin")


def require_admin():
    """检查管理员权限"""
    if not current_user.is_authenticated or current_user.role != "admin":
        flash("权限不足", "error")
        return redirect(url_for("admin_dashboard"))
    return None


@bp.route("/permissions", methods=["GET", "POST"])
@login_required
def franchisee_permissions_list():
    """加盟商权限配置列表页面"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("franchisee.franchisee_admin.admin_franchisee_list"))

    FranchiseeAccount = models["FranchiseeAccount"]
    StaffUser = models.get("StaffUser")
    db = models["db"]

    # 获取所有加盟商
    franchisees = FranchiseeAccount.query.order_by(FranchiseeAccount.company_name).all()

    # 定义可配置的权限列表
    admin_permissions = [
        {"key": "dashboard", "name": "仪表盘", "description": "查看管理后台仪表盘"},
        {"key": "orders", "name": "订单管理", "description": "查看和管理订单"},
        {"key": "payment", "name": "支付管理", "description": "优惠券、退款审核、团购核销"},
        {"key": "products", "name": "产品管理", "description": "查看和管理产品"},
        {
            "key": "franchisee",
            "name": "加盟商管理",
            "description": "查看加盟商信息（仅限自己的账户）",
        },
    ]

    miniprogram_permissions = [
        {
            "key": "view_today_orders",
            "name": "查看今日订单",
            "description": "在小程序中查看今天的订单",
        },
        {"key": "view_all_orders", "name": "查看全部订单", "description": "在小程序中查看所有订单"},
        {
            "key": "view_store_images",
            "name": "查看门店图片",
            "description": "查看门店用户生成的图片",
        },
        {
            "key": "groupon_verify",
            "name": "团购核销",
            "description": "在小程序中生成团购核销优惠券",
        },
        {"key": "refund_request", "name": "退款申请", "description": "针对异常订单申请退款"},
    ]

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form

        # 更新加盟商权限
        account_permissions_data = data.get("account_permissions", {})
        for account_id_str, permissions in account_permissions_data.items():
            try:
                account_id = int(account_id_str)
                account = FranchiseeAccount.query.get(account_id)
                if account:
                    account_admin_perms = permissions.get("admin", {})
                    account_miniprogram_perms = permissions.get("miniprogram", {})
                    account_permissions = {
                        "admin": account_admin_perms,
                        "miniprogram": account_miniprogram_perms,
                    }
                    account.notes = json.dumps(account_permissions) if account_permissions else None
            except (ValueError, TypeError):
                continue

        # 更新子用户权限
        if StaffUser:
            staff_permissions_data = data.get("staff_permissions", {})
            for staff_id_str, permissions in staff_permissions_data.items():
                try:
                    staff_id = int(staff_id_str)
                    staff = StaffUser.query.get(staff_id)
                    if staff:
                        staff_admin_perms = permissions.get("admin", {})
                        staff_miniprogram_perms = permissions.get("miniprogram", {})
                        staff_permissions = {
                            "admin": staff_admin_perms,
                            "miniprogram": staff_miniprogram_perms,
                        }
                        staff.permissions = (
                            json.dumps(staff_permissions) if staff_permissions else "{}"
                        )
                except (ValueError, TypeError):
                    continue

        db.session.commit()

        if request.is_json:
            return jsonify({"status": "success", "message": "权限配置已保存"})
        else:
            flash("权限配置已保存", "success")
            return redirect(url_for("franchisee.franchisee_admin.admin_franchisee_list"))

    # 读取现有权限
    franchisee_data = []
    for franchisee in franchisees:
        account_permissions = {"admin": {}, "miniprogram": {}}
        if franchisee.notes:
            try:
                account_permissions = json.loads(franchisee.notes)
            except Exception:
                pass

        # 获取该加盟商的子用户
        staff_users = []
        if StaffUser:
            staff_users = (
                StaffUser.query.filter_by(franchisee_id=franchisee.id)
                .order_by(StaffUser.created_at.desc())
                .all()
            )

        staff_permissions_dict = {}
        for staff in staff_users:
            staff_perms = {"admin": {}, "miniprogram": {}}
            if staff.permissions:
                try:
                    staff_perms = json.loads(staff.permissions)
                except Exception:
                    pass
            staff_permissions_dict[staff.id] = staff_perms

        franchisee_data.append(
            {
                "franchisee": franchisee,
                "account_permissions": account_permissions,
                "staff_users": staff_users,
                "staff_permissions_dict": staff_permissions_dict,
            }
        )

    return render_template(
        "admin/franchisee_permissions_list.html",
        franchisee_data=franchisee_data,
        admin_permissions=admin_permissions,
        miniprogram_permissions=miniprogram_permissions,
    )
