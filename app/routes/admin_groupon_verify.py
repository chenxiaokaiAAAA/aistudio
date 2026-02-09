# -*- coding: utf-8 -*-
"""
管理后台团购核销路由模块
用于记录和管理团购核销操作
"""

import logging

logger = logging.getLogger(__name__)
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import desc, func, or_

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
bp = Blueprint("admin_groupon_verify", __name__)


@bp.route("/admin/groupon/verify")
@login_required
@admin_required
def groupon_verify_list():
    """团购核销记录列表页面"""
    models = get_models(["Coupon", "FranchiseeAccount", "StaffUser", "db"])
    if not models:
        return render_template("admin/error.html", message="系统未初始化"), 500

    Coupon = models["Coupon"]
    FranchiseeAccount = models["FranchiseeAccount"]
    StaffUser = models.get("StaffUser")
    db = models["db"]

    # 获取筛选参数
    platform = request.args.get("platform", "")
    franchisee_id = request.args.get("franchisee_id", "")
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # 构建查询 - 只查询团购核销券
    query = Coupon.query.filter(Coupon.source_type == "groupon")

    # 平台筛选（使用groupon_platform字段）
    if platform:
        query = query.filter(Coupon.groupon_platform == platform)

    # 加盟商筛选
    if franchisee_id:
        query = query.filter(Coupon.franchisee_id == int(franchisee_id))

    # 搜索
    if search:
        query = query.filter(
            or_(
                Coupon.groupon_order_id.like(f"%{search}%"),
                Coupon.name.like(f"%{search}%"),
                Coupon.code.like(f"%{search}%"),
            )
        )

    # 分页
    pagination = query.order_by(desc(Coupon.create_time)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    coupons = pagination.items

    # 获取GrouponPackage模型
    GrouponPackage = models.get("GrouponPackage")

    # 获取每个核销记录的详细信息
    verify_records = []
    for coupon in coupons:
        # 获取创建人信息
        creator_info = "系统"
        franchisee_name = ""
        staff_name = ""

        if coupon.creator_type == "franchisee":
            if coupon.franchisee_id:
                franchisee = FranchiseeAccount.query.get(coupon.franchisee_id)
                if franchisee:
                    franchisee_name = franchisee.company_name or franchisee.username
                    creator_info = franchisee_name
            elif coupon.creator_name:
                creator_info = coupon.creator_name
        elif coupon.creator_type == "staf":
            # 优先通过staff_user_id查找
            if coupon.staff_user_id and StaffUser:
                staff = StaffUser.query.get(coupon.staff_user_id)
                if staff:
                    staff_name = staff.name
                    creator_info = f"{staff.name}（店员）"
                    if staff.franchisee_id:
                        franchisee = FranchiseeAccount.query.get(staff.franchisee_id)
                        if franchisee:
                            franchisee_name = franchisee.company_name or franchisee.username
            # 如果通过staff_user_id没找到，尝试使用creator_name
            if not creator_info or creator_info == "系统":
                if coupon.creator_name:
                    creator_info = coupon.creator_name
                else:
                    creator_info = "店员（未知）"
        elif coupon.creator_type == "admin":
            creator_info = "管理员"
            if coupon.creator_name:
                creator_info = coupon.creator_name
        else:
            # creator_type为system或None，使用creator_name或默认值
            if coupon.creator_name:
                creator_info = coupon.creator_name

        # 获取平台和套餐信息
        platform_name = coupon.groupon_platform or ""
        package_name = ""
        if GrouponPackage and coupon.groupon_package_id:
            try:
                package_id_int = int(coupon.groupon_package_id)
                package = GrouponPackage.query.get(package_id_int)
                if package:
                    platform_name = package.platform
                    package_name = package.package_name
            except (ValueError, TypeError) as e:
                logger.info(f"获取套餐信息失败: {e}, package_id={coupon.groupon_package_id}")
                # 如果转换失败，至少使用已保存的平台信息
                pass

        verify_records.append(
            {
                "coupon": coupon,
                "creator_info": creator_info,
                "franchisee_name": franchisee_name,
                "staff_name": staff_name,
                "platform": platform_name,
                "package_name": package_name,
            }
        )

    # 获取所有加盟商
    franchisees = (
        FranchiseeAccount.query.filter_by(status="active")
        .order_by(FranchiseeAccount.company_name)
        .all()
    )

    # 获取所有平台
    platforms = []
    GrouponPackage = models.get("GrouponPackage")
    if GrouponPackage:
        platforms = db.session.query(GrouponPackage.platform).distinct().all()
        platforms = [p[0] for p in platforms if p[0]]

    # 统计数据
    total_verifies = Coupon.query.filter(Coupon.source_type == "groupon").count()
    today_verifies = Coupon.query.filter(
        Coupon.source_type == "groupon", func.date(Coupon.create_time) == datetime.now().date()
    ).count()

    return render_template(
        "admin/groupon_verify_list.html",
        verify_records=verify_records,
        pagination=pagination,
        franchisees=franchisees,
        platforms=platforms,
        platform=platform,
        franchisee_id=franchisee_id,
        search=search,
        total_verifies=total_verifies,
        today_verifies=today_verifies,
    )
