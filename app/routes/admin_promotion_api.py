# -*- coding: utf-8 -*-
"""
管理后台推广管理API路由模块
从 test_server.py 迁移所有 /api/admin/promotion/* 路由
"""

import logging

logger = logging.getLogger(__name__)
import json
import sys
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_promotion_api_bp = Blueprint("admin_promotion_api", __name__, url_prefix="/admin")


@admin_promotion_api_bp.route("/promotion")
@login_required
def admin_promotion_management():
    """后台分佣管理页面"""
    if current_user.role not in ["admin", "operator"]:
        from flask import redirect, url_for

        return redirect(url_for("auth.login"))
    return render_template("admin/promotion_management.html")


@admin_promotion_api_bp.route("/api/promotion/commissions", methods=["GET"])
@login_required
def get_admin_commissions():
    """获取分佣记录列表（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        Order = models["Order"]
        Commission = models["Commission"]
        PromotionUser = models["PromotionUser"]

        # 获取查询参数
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 10))
        search = request.args.get("search", "")
        status = request.args.get("status", "")
        date_from = request.args.get("dateFrom", "")
        date_to = request.args.get("dateTo", "")

        # 构建查询
        query = db.session.query(Commission, PromotionUser).join(
            PromotionUser, Commission.referrer_user_id == PromotionUser.user_id
        )

        # 搜索条件
        if search:
            query = query.filter(
                db.or_(
                    PromotionUser.user_id.like(f"%{search}%"),
                    PromotionUser.promotion_code.like(f"%{search}%"),
                    PromotionUser.nickname.like(f"%{search}%"),
                    Commission.order_id.like(f"%{search}%"),
                )
            )

        # 状态筛选
        if status:
            query = query.filter(Commission.status == status)

        # 日期筛选
        if date_from:
            query = query.filter(Commission.create_time >= date_from)
        if date_to:
            query = query.filter(Commission.create_time <= date_to + " 23:59:59")

        # 排序
        query = query.order_by(Commission.create_time.desc())

        # 优化：使用数据库层面分页
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        commissions = pagination.items

        # 优化N+1查询：批量查询所有订单信息
        order_numbers = [comm.order_id for comm, _ in commissions]
        orders_map = {}
        if order_numbers:
            all_orders = Order.query.filter(Order.order_number.in_(order_numbers)).all()
            for order in all_orders:
                orders_map[order.order_number] = order

        # 格式化数据
        commission_list = []
        for commission, user in commissions:
            # 根据订单状态计算分佣状态（从批量查询的映射中获取，避免N+1查询）
            order = orders_map.get(commission.order_id)
            if order and order.status == "delivered":
                calculated_status = "completed"
            else:
                calculated_status = "pending"

            commission_list.append(
                {
                    "id": commission.id,
                    "order_id": commission.order_id,
                    "amount": commission.amount,
                    "rate": commission.rate,
                    "status": calculated_status,  # 使用计算出的状态
                    "original_status": commission.status,  # 保留原始状态
                    "order_status": order.status if order else None,  # 订单状态
                    "create_time": (
                        commission.create_time.isoformat() if commission.create_time else None
                    ),
                    "complete_time": (
                        commission.complete_time.isoformat() if commission.complete_time else None
                    ),
                    "user": {
                        "user_id": user.user_id,
                        "promotion_code": user.promotion_code,
                        "nickname": user.nickname,
                        "avatar_url": user.avatar_url,
                        "phone_number": user.phone_number,  # 添加手机号字段
                    },
                }
            )

        # 计算统计信息
        total_users = PromotionUser.query.count()

        # 优化N+1查询：根据订单状态计算总佣金（使用数据库聚合）
        from sqlalchemy import func

        # 批量查询所有佣金对应的订单
        commission_order_numbers = db.session.query(Commission.order_id).distinct().all()
        order_numbers_list = [row[0] for row in commission_order_numbers if row[0]]

        orders_map = {}
        if order_numbers_list:
            all_orders = Order.query.filter(Order.order_number.in_(order_numbers_list)).all()
            for order in all_orders:
                orders_map[order.order_number] = order

        # 使用数据库聚合计算总佣金（只计算已发货订单的佣金）
        total_commissions = (
            db.session.query(func.sum(Commission.amount))
            .join(Order, Commission.order_id == Order.order_number)
            .filter(Order.status == "shipped")
            .scalar()
            or 0
        )

        total_orders = Commission.query.count()
        avg_commission = total_commissions / total_orders if total_orders > 0 else 0

        return jsonify(
            {
                "success": True,
                "commissions": commission_list,
                "pagination": {
                    "page": page,
                    "per_page": page_size,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
                "statistics": {
                    "totalUsers": total_users,
                    "totalCommissions": float(total_commissions),
                    "totalOrders": total_orders,
                    "avgCommission": float(avg_commission),
                },
            }
        )

    except Exception as e:
        logger.info(f"获取分佣记录失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取分佣记录失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/users", methods=["GET"])
@login_required
def get_admin_promotion_users():
    """获取推广用户列表（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        # 检测数据库类型（如果环境变量未设置，可能仍在使用SQLite）
        database_url = str(db.engine.url)
        is_postgresql = "postgresql" in database_url.lower()

        logger.info("=" * 50)
        logger.info("开始获取推广用户列表...")
        logger.info(f"数据库模型: {PromotionUser}")
        logger.info(f"表名: {PromotionUser.__tablename__}")
        logger.info(f"数据库类型: {'PostgreSQL' if is_postgresql else 'SQLite'}")
        if not is_postgresql:
            logger.warning("⚠️ 检测到SQLite数据库，建议切换到PostgreSQL！")

        # 先直接查询所有用户，看看数据库中有没有数据
        try:
            all_users_count = PromotionUser.query.count()
            logger.info(f"数据库中用户总数: {all_users_count}")
            if all_users_count > 0:
                sample_user = PromotionUser.query.first()
                logger.info(
                    f"示例用户: user_id={sample_user.user_id}, promotion_code={sample_user.promotion_code}"
                )
        except Exception as e:
            logger.info(f"查询用户总数失败: {e}")
            import traceback

            traceback.print_exc()

        # 获取排序参数
        sort_by = request.args.get("sortBy", "create_time")  # 默认按创建时间排序
        sort_order = request.args.get("sortOrder", "desc")  # 默认降序
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        logger.info(
            f"排序参数: sortBy={sort_by}, sortOrder={sort_order}, page={page}, per_page={per_page}"
        )

        # 构建排序
        if sort_by == "visits":
            # 按访问数排序需要特殊处理
            # 优化：先获取所有用户，然后批量查询统计数据（避免N+1查询）
            users = PromotionUser.query.all()

            # 批量查询所有用户的访问统计
            promotion_codes = [user.promotion_code for user in users if user.promotion_code]
            visit_stats_map = {}
            if promotion_codes:
                visit_stats = []
                try:
                    # 先尝试使用ORM查询（如果UserAccessLog模型存在）
                    UserAccessLog = models.get("UserAccessLog")
                    PromotionTrack = models.get("PromotionTrack")
                    UserVisit = models.get("UserVisit")

                    if UserAccessLog and hasattr(UserAccessLog, "final_promotion_code"):
                        from sqlalchemy import func

                        visit_stats = (
                            db.session.query(
                                UserAccessLog.final_promotion_code,
                                func.count(UserAccessLog.id).label("total_visits"),
                            )
                            .filter(UserAccessLog.final_promotion_code.in_(promotion_codes))
                            .group_by(UserAccessLog.final_promotion_code)
                            .all()
                        )
                        visit_stats = [(row[0], row[1]) for row in visit_stats]
                    elif PromotionTrack and hasattr(PromotionTrack, "promotion_code"):
                        from sqlalchemy import func

                        visit_stats = (
                            db.session.query(
                                PromotionTrack.promotion_code,
                                func.count(PromotionTrack.id).label("total_visits"),
                            )
                            .filter(PromotionTrack.promotion_code.in_(promotion_codes))
                            .group_by(PromotionTrack.promotion_code)
                            .all()
                        )
                        visit_stats = [(row[0], row[1]) for row in visit_stats]
                    elif UserVisit and hasattr(UserVisit, "promotion_code"):
                        from sqlalchemy import func

                        visit_stats = (
                            db.session.query(
                                UserVisit.promotion_code,
                                func.count(UserVisit.id).label("total_visits"),
                            )
                            .filter(UserVisit.promotion_code.in_(promotion_codes))
                            .group_by(UserVisit.promotion_code)
                            .all()
                        )
                        visit_stats = [(row[0], row[1]) for row in visit_stats]
                    else:
                        # 如果所有模型都不存在，尝试使用原始SQL查询（先检查表是否存在）
                        if is_postgresql:
                            # 先检查表是否存在
                            table_check = db.session.execute(db.text("""
                                SELECT table_name
                                FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name IN ('user_access_logs', 'promotion_tracks', 'user_visits')
                                LIMIT 1
                            """)).fetchone()

                            if table_check:
                                table_name = table_check[0]
                                # 根据表名选择正确的字段名
                                if table_name == "promotion_tracks":
                                    code_field = "promotion_code"
                                elif table_name == "user_visits":
                                    code_field = "promotion_code"
                                else:
                                    code_field = "final_promotion_code"

                                visit_stats = db.session.execute(
                                    db.text("""
                                        SELECT {code_field}, COUNT(*) as total_visits
                                        FROM {table_name}
                                        WHERE {code_field} IN :promotion_codes
                                        GROUP BY {code_field}
                                    """),
                                    {"promotion_codes": tuple(promotion_codes)},
                                ).fetchall()
                            else:
                                logger.warning("未找到访问日志表，跳过访问统计查询")
                                visit_stats = []
                        else:
                            # SQLite: 使用ORM查询或跳过
                            logger.warning("未找到访问日志模型，跳过访问统计查询")
                            visit_stats = []
                except Exception as e:
                    logger.warning(f"查询访问统计失败: {str(e)}，跳过访问统计查询")
                    visit_stats = []

                visit_stats_map = {row[0]: row[1] for row in visit_stats}

            # 批量查询所有用户的订单统计
            open_ids = [user.open_id for user in users if user.open_id]
            order_stats_map = {}
            if open_ids:
                if is_postgresql:
                    order_stats = db.session.execute(
                        db.text("""
                            SELECT
                                openid,
                                COUNT(*) as paid_orders,
                                COALESCE(SUM(price), 0) as total_paid_amount
                            FROM orders
                            WHERE openid IN :open_ids
                                AND source_type = 'miniprogram'
                                AND status IN ('paid', 'processing', 'shipped', 'delivered', 'completed')
                            GROUP BY openid
                        """),
                        {"open_ids": tuple(open_ids)},
                    ).fetchall()
                else:
                    # SQLite使用ORM查询替代原始SQL，避免参数绑定问题
                    if len(open_ids) == 0:
                        order_stats = []
                    else:
                        Order = models.get("Order")
                        if Order:
                            from sqlalchemy import func

                            order_stats = (
                                db.session.query(
                                    Order.openid,
                                    func.count(Order.id).label("paid_orders"),
                                    func.coalesce(func.sum(Order.price), 0).label(
                                        "total_paid_amount"
                                    ),
                                )
                                .filter(
                                    Order.openid.in_(open_ids),
                                    Order.source_type == "miniprogram",
                                    Order.status.in_(
                                        ["paid", "processing", "shipped", "delivered", "completed"]
                                    ),
                                )
                                .group_by(Order.openid)
                                .all()
                            )
                            order_stats = [(row[0], row[1], row[2]) for row in order_stats]
                        else:
                            order_stats = []
                order_stats_map = {
                    row[0]: {"paid_orders": row[1], "total_paid_amount": float(row[2])}
                    for row in order_stats
                }

            # 批量查询所有用户的优惠券数量
            user_ids = [user.user_id for user in users if user.user_id]
            coupon_count_map = {}
            if user_ids:
                if is_postgresql:
                    coupon_counts = db.session.execute(
                        db.text("""
                            SELECT user_id, COUNT(*) as coupon_count
                            FROM user_coupons
                            WHERE user_id IN :user_ids
                            GROUP BY user_id
                        """),
                        {"user_ids": tuple(user_ids)},
                    ).fetchall()
                else:
                    # SQLite使用ORM查询替代原始SQL，避免参数绑定问题
                    if len(user_ids) == 0:
                        coupon_counts = []
                    else:
                        UserCoupon = models.get("UserCoupon")
                        if UserCoupon:
                            from sqlalchemy import func

                            coupon_counts = (
                                db.session.query(
                                    UserCoupon.user_id,
                                    func.count(UserCoupon.id).label("coupon_count"),
                                )
                                .filter(UserCoupon.user_id.in_(user_ids))
                                .group_by(UserCoupon.user_id)
                                .all()
                            )
                            coupon_counts = [(row[0], row[1]) for row in coupon_counts]
                        else:
                            coupon_counts = []
                coupon_count_map = {row[0]: row[1] for row in coupon_counts}

            # 构建用户列表（从批量查询的映射中获取数据，避免N+1查询）
            user_list = []
            for user in users:
                try:
                    visit_stats_data = visit_stats_map.get(user.promotion_code, 0)
                    order_stats_data = order_stats_map.get(
                        user.open_id, {"paid_orders": 0, "total_paid_amount": 0.0}
                    )
                    coupon_count_data = coupon_count_map.get(user.user_id, 0)

                    user_data = {
                        "user_id": user.user_id,
                        "open_id": user.open_id,
                        "promotion_code": user.promotion_code,
                        "nickname": user.nickname,
                        "avatar_url": user.avatar_url,
                        "phone_number": user.phone_number,
                        "total_earnings": user.total_earnings,
                        "total_orders": user.total_orders,
                        "own_orders": order_stats_data["paid_orders"],
                        "paid_amount": order_stats_data["total_paid_amount"],
                        "coupon_count": coupon_count_data,
                        "create_time": user.create_time.isoformat() if user.create_time else None,
                        "update_time": user.update_time.isoformat() if user.update_time else None,
                        "visit_stats": {"total_visits": visit_stats_data},
                        "recent_visits": [],
                    }
                    user_list.append(user_data)
                except Exception as e:
                    logger.info(f"处理用户失败: {e}")
                    import traceback

                    traceback.print_exc()
                    continue

            # 按访问数排序
            if sort_order == "desc":
                user_list.sort(key=lambda x: x["visit_stats"]["total_visits"], reverse=True)
            else:
                user_list.sort(key=lambda x: x["visit_stats"]["total_visits"], reverse=False)

            # 优化：添加分页支持（内存分页，因为需要先排序）
            total_users = len(user_list)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            user_list = user_list[start_idx:end_idx]

            # 创建分页对象（用于统一返回格式）
            class PaginationObj:
                def __init__(self, total, page, per_page):
                    self.total = total
                    self.page = page
                    self.per_page = per_page
                    self.pages = (total + per_page - 1) // per_page
                    self.has_next = page < self.pages
                    self.has_prev = page > 1

            pagination = PaginationObj(total_users, page, per_page)

        else:
            # 其他排序方式
            if sort_by == "create_time":
                order_column = PromotionUser.create_time
            elif sort_by == "update_time":
                order_column = PromotionUser.update_time
            elif sort_by == "total_earnings":
                order_column = PromotionUser.total_earnings
            elif sort_by == "total_orders":
                order_column = PromotionUser.total_orders
            else:
                order_column = PromotionUser.create_time

            # 优化：使用数据库层面分页
            query = PromotionUser.query
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            users = pagination.items

            # 优化N+1查询：批量查询所有用户的统计信息
            promotion_codes = [user.promotion_code for user in users if user.promotion_code]
            open_ids = [user.open_id for user in users if user.open_id]
            user_ids = [user.user_id for user in users]

            # 批量查询访问统计
            visits_map = {}
            if promotion_codes:
                visits_stats = []
                try:
                    # 先尝试使用ORM查询（如果UserAccessLog模型存在）
                    UserAccessLog = models.get("UserAccessLog")
                    if UserAccessLog:
                        from sqlalchemy import func

                        visits_stats = (
                            db.session.query(
                                UserAccessLog.final_promotion_code,
                                func.count(UserAccessLog.id).label("total_visits"),
                            )
                            .filter(UserAccessLog.final_promotion_code.in_(promotion_codes))
                            .group_by(UserAccessLog.final_promotion_code)
                            .all()
                        )
                        visits_stats = [(row[0], row[1]) for row in visits_stats]
                    else:
                        # 尝试使用PromotionTrack表（推广访问追踪表）
                        PromotionTrack = models.get("PromotionTrack")
                        if PromotionTrack:
                            from sqlalchemy import func

                            visits_stats = (
                                db.session.query(
                                    PromotionTrack.promotion_code,
                                    func.count(PromotionTrack.id).label("total_visits"),
                                )
                                .filter(PromotionTrack.promotion_code.in_(promotion_codes))
                                .group_by(PromotionTrack.promotion_code)
                                .all()
                            )
                            visits_stats = [(row[0], row[1]) for row in visits_stats]
                        else:
                            # 尝试使用UserVisit表（用户访问追踪表）
                            UserVisit = models.get("UserVisit")
                            if UserVisit:
                                from sqlalchemy import func

                                visits_stats = (
                                    db.session.query(
                                        UserVisit.promotion_code,
                                        func.count(UserVisit.id).label("total_visits"),
                                    )
                                    .filter(UserVisit.promotion_code.in_(promotion_codes))
                                    .group_by(UserVisit.promotion_code)
                                    .all()
                                )
                                visits_stats = [(row[0], row[1]) for row in visits_stats]
                            else:
                                # 如果所有模型都不存在，尝试使用原始SQL查询（先检查表是否存在）
                                if is_postgresql:
                                    # 先检查表是否存在
                                    table_check = db.session.execute(db.text("""
                                        SELECT table_name
                                        FROM information_schema.tables
                                        WHERE table_schema = 'public'
                                        AND table_name IN ('user_access_logs', 'promotion_tracks', 'user_visits')
                                        LIMIT 1
                                    """)).fetchone()

                                    if table_check:
                                        table_name = table_check[0]
                                        # 根据表名选择正确的字段名
                                        if table_name == "promotion_tracks":
                                            code_field = "promotion_code"
                                        elif table_name == "user_visits":
                                            code_field = "promotion_code"
                                        else:
                                            code_field = "final_promotion_code"

                                        visits_stats = db.session.execute(
                                            db.text("""
                                                SELECT {code_field}, COUNT(*) as total_visits
                                                FROM {table_name}
                                                WHERE {code_field} IN :promotion_codes
                                                GROUP BY {code_field}
                                            """),
                                            {"promotion_codes": tuple(promotion_codes)},
                                        ).fetchall()
                                    else:
                                        logger.warning("未找到访问日志表，跳过访问统计查询")
                                        visits_stats = []
                                else:
                                    # SQLite: 使用ORM查询或跳过
                                    logger.warning("未找到访问日志模型，跳过访问统计查询")
                                    visits_stats = []
                except Exception as e:
                    logger.warning(f"查询访问统计失败: {str(e)}，跳过访问统计查询")
                    visits_stats = []

                for code, count in visits_stats:
                    visits_map[code] = count

            # 批量查询订单统计
            orders_map = {}
            if open_ids:
                if is_postgresql:
                    orders_stats = db.session.execute(
                        db.text("""
                            SELECT
                                openid,
                                COUNT(*) as paid_orders,
                                COALESCE(SUM(price), 0) as total_paid_amount
                            FROM orders
                            WHERE openid IN :open_ids
                                AND source_type = 'miniprogram'
                                AND status IN ('paid', 'processing', 'shipped', 'delivered', 'completed')
                            GROUP BY openid
                        """),
                        {"open_ids": tuple(open_ids)},
                    ).fetchall()
                else:
                    placeholders = ",".join(["?"] * len(open_ids))
                    from sqlalchemy import text

                    orders_stats = db.session.execute(
                        text("""
                            SELECT
                                openid,
                                COUNT(*) as paid_orders,
                                COALESCE(SUM(price), 0) as total_paid_amount
                            FROM orders
                            WHERE openid IN ({placeholders})
                                AND source_type = 'miniprogram'
                                AND status IN ('paid', 'processing', 'shipped', 'delivered', 'completed')
                            GROUP BY openid
                        """),
                        tuple(open_ids),  # SQLite需要元组作为位置参数
                    ).fetchall()
                for open_id, paid_orders, total_paid_amount in orders_stats:
                    orders_map[open_id] = (paid_orders, float(total_paid_amount))

            # 批量查询优惠券数量
            coupons_map = {}
            if user_ids:
                if is_postgresql:
                    coupons_stats = db.session.execute(
                        db.text("""
                            SELECT user_id, COUNT(*) as coupon_count
                            FROM user_coupons
                            WHERE user_id IN :user_ids
                            GROUP BY user_id
                        """),
                        {"user_ids": tuple(user_ids)},
                    ).fetchall()
                else:
                    placeholders = ",".join(["?"] * len(user_ids))
                    from sqlalchemy import text

                    coupons_stats = db.session.execute(
                        text("""
                            SELECT user_id, COUNT(*) as coupon_count
                            FROM user_coupons
                            WHERE user_id IN ({placeholders})
                            GROUP BY user_id
                        """),
                        tuple(user_ids),  # SQLite需要元组作为位置参数
                    ).fetchall()
                for user_id, count in coupons_stats:
                    coupons_map[user_id] = count

            user_list = []
            for i, user in enumerate(users):
                try:
                    # 从批量查询的映射中获取统计信息（避免N+1查询）
                    total_visits = (
                        visits_map.get(user.promotion_code, 0) if user.promotion_code else 0
                    )
                    order_stats = (
                        orders_map.get(user.open_id, (0, 0.0)) if user.open_id else (0, 0.0)
                    )
                    coupon_count = coupons_map.get(user.user_id, 0)

                    user_data = {
                        "user_id": user.user_id,
                        "open_id": user.open_id,
                        "promotion_code": user.promotion_code,
                        "nickname": user.nickname,
                        "avatar_url": user.avatar_url,
                        "phone_number": user.phone_number,
                        "total_earnings": user.total_earnings,
                        "total_orders": user.total_orders,
                        "own_orders": order_stats[0],
                        "paid_amount": order_stats[1],
                        "coupon_count": coupon_count,
                        "create_time": user.create_time.isoformat() if user.create_time else None,
                        "update_time": user.update_time.isoformat() if user.update_time else None,
                        "visit_stats": {"total_visits": total_visits},
                        "recent_visits": [],
                    }
                    user_list.append(user_data)
                except Exception as e:
                    logger.info(f"处理用户 {i + 1} 失败: {e}")
                    import traceback

                    traceback.print_exc()
                    continue

        logger.info(f"成功处理 {len(user_list)} 个用户")

        # 计算今日和昨日活跃用户数
        from datetime import datetime, timedelta

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start

        # 查询活跃用户统计（尝试使用ORM或查找实际表名）
        today_active_users = [0]
        yesterday_active_users = [0]
        try:
            # 先尝试使用ORM查询
            UserAccessLog = models.get("UserAccessLog")
            PromotionTrack = models.get("PromotionTrack")
            UserVisit = models.get("UserVisit")

            if (
                UserAccessLog
                and hasattr(UserAccessLog, "final_promotion_code")
                and hasattr(UserAccessLog, "visit_time")
            ):
                from sqlalchemy import func

                today_result = (
                    db.session.query(func.count(func.distinct(UserAccessLog.final_promotion_code)))
                    .filter(
                        UserAccessLog.visit_time >= today_start,
                        UserAccessLog.visit_time < today_end,
                        UserAccessLog.final_promotion_code.isnot(None),
                    )
                    .scalar()
                )
                today_active_users = [today_result or 0]

                yesterday_result = (
                    db.session.query(func.count(func.distinct(UserAccessLog.final_promotion_code)))
                    .filter(
                        UserAccessLog.visit_time >= yesterday_start,
                        UserAccessLog.visit_time < yesterday_end,
                        UserAccessLog.final_promotion_code.isnot(None),
                    )
                    .scalar()
                )
                yesterday_active_users = [yesterday_result or 0]
            elif (
                PromotionTrack
                and hasattr(PromotionTrack, "promotion_code")
                and hasattr(PromotionTrack, "visit_time")
            ):
                from sqlalchemy import func

                today_result = (
                    db.session.query(func.count(func.distinct(PromotionTrack.promotion_code)))
                    .filter(
                        PromotionTrack.visit_time >= int(today_start.timestamp() * 1000),
                        PromotionTrack.visit_time < int(today_end.timestamp() * 1000),
                        PromotionTrack.promotion_code.isnot(None),
                    )
                    .scalar()
                )
                today_active_users = [today_result or 0]

                yesterday_result = (
                    db.session.query(func.count(func.distinct(PromotionTrack.promotion_code)))
                    .filter(
                        PromotionTrack.visit_time >= int(yesterday_start.timestamp() * 1000),
                        PromotionTrack.visit_time < int(yesterday_end.timestamp() * 1000),
                        PromotionTrack.promotion_code.isnot(None),
                    )
                    .scalar()
                )
                yesterday_active_users = [yesterday_result or 0]
            elif (
                UserVisit
                and hasattr(UserVisit, "promotion_code")
                and hasattr(UserVisit, "visit_time")
            ):
                from sqlalchemy import func

                today_result = (
                    db.session.query(func.count(func.distinct(UserVisit.promotion_code)))
                    .filter(
                        UserVisit.visit_time >= today_start,
                        UserVisit.visit_time < today_end,
                        UserVisit.promotion_code.isnot(None),
                    )
                    .scalar()
                )
                today_active_users = [today_result or 0]

                yesterday_result = (
                    db.session.query(func.count(func.distinct(UserVisit.promotion_code)))
                    .filter(
                        UserVisit.visit_time >= yesterday_start,
                        UserVisit.visit_time < yesterday_end,
                        UserVisit.promotion_code.isnot(None),
                    )
                    .scalar()
                )
                yesterday_active_users = [yesterday_result or 0]
            else:
                # 如果模型都不存在，尝试使用原始SQL查询（先检查表是否存在）
                if is_postgresql:
                    table_check = db.session.execute(db.text("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name IN ('user_access_logs', 'promotion_tracks', 'user_visits')
                        LIMIT 1
                    """)).fetchone()

                    if table_check:
                        table_name = table_check[0]
                        # 根据表名选择正确的字段名
                        if table_name == "promotion_tracks":
                            code_field = "promotion_code"
                            time_field = "visit_time"
                            today_result = db.session.execute(
                                db.text("""
                                    SELECT COUNT(DISTINCT {code_field}) as active_count
                                    FROM {table_name}
                                    WHERE {time_field} >= :start_time AND {time_field} < :end_time
                                    AND {code_field} IS NOT NULL
                                """),
                                {
                                    "start_time": int(today_start.timestamp() * 1000),
                                    "end_time": int(today_end.timestamp() * 1000),
                                },
                            ).fetchone()
                            today_active_users = [today_result[0] if today_result else 0]

                            yesterday_result = db.session.execute(
                                db.text("""
                                    SELECT COUNT(DISTINCT {code_field}) as active_count
                                    FROM {table_name}
                                    WHERE {time_field} >= :start_time AND {time_field} < :end_time
                                    AND {code_field} IS NOT NULL
                                """),
                                {
                                    "start_time": int(yesterday_start.timestamp() * 1000),
                                    "end_time": int(yesterday_end.timestamp() * 1000),
                                },
                            ).fetchone()
                            yesterday_active_users = [
                                yesterday_result[0] if yesterday_result else 0
                            ]
                        else:
                            code_field = (
                                "final_promotion_code"
                                if table_name == "user_access_logs"
                                else "promotion_code"
                            )
                            time_field = "visit_time"
                            today_result = db.session.execute(
                                db.text("""
                                    SELECT COUNT(DISTINCT {code_field}) as active_count
                                    FROM {table_name}
                                    WHERE {time_field} >= :start_time AND {time_field} < :end_time
                                    AND {code_field} IS NOT NULL
                                """),
                                {"start_time": today_start, "end_time": today_end},
                            ).fetchone()
                            today_active_users = [today_result[0] if today_result else 0]

                            yesterday_result = db.session.execute(
                                db.text("""
                                    SELECT COUNT(DISTINCT {code_field}) as active_count
                                    FROM {table_name}
                                    WHERE {time_field} >= :start_time AND {time_field} < :end_time
                                    AND {code_field} IS NOT NULL
                                """),
                                {"start_time": yesterday_start, "end_time": yesterday_end},
                            ).fetchone()
                            yesterday_active_users = [
                                yesterday_result[0] if yesterday_result else 0
                            ]
                    else:
                        logger.warning("未找到访问日志表，跳过活跃用户统计查询")
        except Exception as e:
            logger.warning(f"查询活跃用户统计失败: {str(e)}，跳过统计查询")

        logger.info("=" * 50)
        return jsonify(
            {
                "success": True,
                "users": user_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total if "pagination" in locals() else len(user_list),
                    "pages": pagination.pages if "pagination" in locals() else 1,
                    "has_next": pagination.has_next if "pagination" in locals() else False,
                    "has_prev": pagination.has_prev if "pagination" in locals() else False,
                },
                "total_count": len(user_list),
                "statistics": {
                    "today_active_users": today_active_users[0] if today_active_users else 0,
                    "yesterday_active_users": (
                        yesterday_active_users[0] if yesterday_active_users else 0
                    ),
                },
            }
        )

    except Exception as e:
        logger.info(f"获取推广用户列表失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取推广用户列表失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/user/own-orders", methods=["GET"])
@login_required
def get_user_own_orders():
    """获取用户自己的订单（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        user_id = request.args.get("userId")
        promotion_code = request.args.get("promotionCode")

        if not user_id and not promotion_code:
            return jsonify({"success": False, "message": "用户ID或推广码不能为空"}), 400

        # 获取用户信息
        if user_id:
            user = PromotionUser.query.filter_by(user_id=user_id).first()
        else:
            user = PromotionUser.query.filter_by(promotion_code=promotion_code).first()

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 查询用户自己的订单
        # 检测数据库类型
        database_url = str(db.engine.url)
        is_postgresql = "postgresql" in database_url.lower()

        if is_postgresql:
            own_orders = db.session.execute(
                db.text("""
                    SELECT order_number, customer_name, customer_phone, size, style_name,
                           product_name, status, created_at, completed_at, customer_address
                    FROM orders
                    WHERE customer_phone = :phone_number
                    ORDER BY created_at DESC
                """),
                {"phone_number": user.phone_number},
            ).fetchall()
        else:
            own_orders = db.session.execute(
                db.text("""
                    SELECT order_number, customer_name, customer_phone, size, style_name,
                           product_name, status, created_at, completed_at, customer_address
                    FROM orders
                    WHERE customer_phone = ?
                    ORDER BY created_at DESC
                """),
                (user.phone_number,),
            ).fetchall()

        orders_list = []
        for order in own_orders:
            orders_list.append(
                {
                    "order_number": order[0],
                    "customer_name": order[1],
                    "customer_phone": order[2],
                    "size": order[3],
                    "style_name": order[4],
                    "product_name": order[5],
                    "status": order[6],
                    "created_at": order[7].isoformat() if order[7] else None,
                    "completed_at": order[8].isoformat() if order[8] else None,
                    "customer_address": order[9],
                }
            )

        return jsonify(
            {
                "success": True,
                "user": {
                    "user_id": user.user_id,
                    "promotion_code": user.promotion_code,
                    "nickname": user.nickname,
                    "phone_number": user.phone_number,
                },
                "own_orders": orders_list,
                "total_count": len(orders_list),
            }
        )

    except Exception as e:
        logger.info(f"获取用户自己订单失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取用户自己订单失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/visits/detail", methods=["GET"])
@login_required
def get_admin_promotion_visits_detail():
    """获取推广访问详细记录（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        database_url = str(db.engine.url)
        is_postgresql = "postgresql" in database_url.lower()

        promotion_code = request.args.get("promotionCode")

        if not promotion_code:
            return jsonify({"success": False, "message": "推广码不能为空"}), 400

        # 查询该推广码的访问记录（尝试使用ORM或查找实际表名）
        visits_result = []
        try:
            # 先尝试使用ORM查询
            UserAccessLog = models.get("UserAccessLog")
            PromotionTrack = models.get("PromotionTrack")
            UserVisit = models.get("UserVisit")

            if UserAccessLog and hasattr(UserAccessLog, "final_promotion_code"):
                visits = (
                    UserAccessLog.query.filter_by(final_promotion_code=promotion_code)
                    .order_by(UserAccessLog.visit_time.desc())
                    .limit(50)
                    .all()
                )
                visits_result = [
                    (
                        getattr(v, "session_id", None),
                        getattr(v, "openid", None),
                        getattr(v, "visit_type", None),
                        getattr(v, "visit_time", None),
                        getattr(v, "page_path", None),
                        getattr(v, "user_info", None),
                        getattr(v, "is_authorized", False),
                    )
                    for v in visits
                ]
            elif PromotionTrack and hasattr(PromotionTrack, "promotion_code"):
                visits = (
                    PromotionTrack.query.filter_by(promotion_code=promotion_code)
                    .order_by(PromotionTrack.visit_time.desc())
                    .limit(50)
                    .all()
                )
                visits_result = [
                    (
                        None,  # session_id
                        None,  # openid
                        None,  # visit_type
                        (
                            datetime.fromtimestamp(v.visit_time / 1000) if v.visit_time else None
                        ),  # visit_time (时间戳转datetime)
                        None,  # page_path
                        None,  # user_info
                        False,  # is_authorized
                    )
                    for v in visits
                ]
            elif UserVisit and hasattr(UserVisit, "promotion_code"):
                visits = (
                    UserVisit.query.filter_by(promotion_code=promotion_code)
                    .order_by(UserVisit.visit_time.desc())
                    .limit(50)
                    .all()
                )
                visits_result = [
                    (
                        getattr(v, "session_id", None),
                        getattr(v, "openid", None),
                        getattr(v, "visit_type", None),
                        getattr(v, "visit_time", None),
                        None,  # page_path
                        getattr(v, "user_info", None),
                        getattr(v, "is_authorized", False),
                    )
                    for v in visits
                ]
            else:
                # 如果模型都不存在，尝试使用原始SQL查询（先检查表是否存在）
                if is_postgresql:
                    table_check = db.session.execute(db.text("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name IN ('user_access_logs', 'promotion_tracks', 'user_visits')
                        LIMIT 1
                    """)).fetchone()

                    if table_check:
                        table_name = table_check[0]
                        # 根据表名选择正确的字段名
                        if table_name == "promotion_tracks":
                            code_field = "promotion_code"
                            visits_result = db.session.execute(
                                db.text("""
                                    SELECT NULL as session_id, NULL as openid, NULL as visit_type,
                                           to_timestamp(visit_time / 1000) as visit_time,
                                           NULL as page_path, NULL as user_info, FALSE as is_authorized
                                    FROM {table_name}
                                    WHERE {code_field} = :promotion_code
                                    ORDER BY visit_time DESC
                                    LIMIT 50
                                """),
                                {"promotion_code": promotion_code},
                            ).fetchall()
                        else:
                            code_field = (
                                "final_promotion_code"
                                if table_name == "user_access_logs"
                                else "promotion_code"
                            )
                            visits_result = db.session.execute(
                                db.text("""
                                    SELECT session_id, openid, visit_type, visit_time, page_path, user_info, is_authorized
                                    FROM {table_name}
                                    WHERE {code_field} = :promotion_code
                                    ORDER BY visit_time DESC
                                    LIMIT 50
                                """),
                                {"promotion_code": promotion_code},
                            ).fetchall()
                    else:
                        logger.warning("未找到访问日志表，跳过访问记录查询")
        except Exception as e:
            logger.warning(f"查询访问记录失败: {str(e)}，跳过访问记录查询")

        visit_list = []
        for visit in visits_result:
            # 解析用户信息
            user_info = {}
            if visit[5]:  # user_info字段
                try:
                    user_info = json.loads(visit[5])
                except Exception:
                    user_info = {}

            # 转换时间为本地时间
            visit_time = visit[3]
            if visit_time:
                try:
                    import pytz

                    # 如果时间格式是字符串，转换为datetime对象
                    if isinstance(visit_time, str):
                        # SQLite存储的是UTC时间字符串，需要解析并转换
                        dt = datetime.fromisoformat(visit_time)
                        # 假设数据库存储的是UTC时间，转换为本地时间
                        utc_dt = pytz.utc.localize(dt)
                        local_dt = utc_dt.astimezone(pytz.timezone("Asia/Shanghai"))
                        visit_time_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        visit_time_str = str(visit_time)
                except Exception as e:
                    logger.info(f"时间转换失败: {e}, 原始时间: {visit_time}")
                    visit_time_str = str(visit_time)
            else:
                visit_time_str = None

            visit_list.append(
                {
                    "id": visit[0],  # session_id作为ID
                    "promotion_code": promotion_code,
                    "visitor_user_id": visit[0],  # session_id
                    "openid": visit[1],
                    "visit_time": visit_time_str,  # 本地时间
                    "visit_type": visit[2],  # visit_type
                    "page_path": visit[4],  # page_path
                    "user_info": user_info,
                    "is_authorized": bool(visit[6]),  # is_authorized
                }
            )

        return jsonify({"success": True, "visits": visit_list, "total": len(visit_list)})

    except Exception as e:
        logger.info(f"获取推广访问详细记录失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取推广访问详细记录失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/visits", methods=["GET"])
@login_required
def get_admin_promotion_visits():
    """获取推广访问统计（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        PromotionTrack = models["PromotionTrack"]

        # 获取总体访问统计
        try:
            from sqlalchemy import case

            total_stats = db.session.query(
                db.func.count(PromotionTrack.id).label("total_visits"),
                db.func.count(
                    case([(PromotionTrack.visitor_user_id == "anonymous", 1)], else_=0)
                ).label("anonymous_visits"),
                db.func.count(
                    case([(PromotionTrack.visitor_user_id != "anonymous", 1)], else_=0)
                ).label("real_visits"),
            ).first()
        except Exception as e:
            logger.info(f"总体访问统计查询失败: {e}")
            total_stats = None

        # 获取17-19号期间的访问统计
        try:
            october_stats = (
                db.session.query(
                    db.func.count(PromotionTrack.id).label("october_visits"),
                    db.func.count(
                        case([(PromotionTrack.visitor_user_id == "anonymous", 1)], else_=0)
                    ).label("october_anonymous_visits"),
                    db.func.count(
                        case([(PromotionTrack.visitor_user_id != "anonymous", 1)], else_=0)
                    ).label("october_real_visits"),
                )
                .filter(
                    PromotionTrack.visit_time >= 1760630400000,  # 2025-10-17 00:00:00
                    PromotionTrack.visit_time <= 1760889599000,  # 2025-10-19 23:59:59
                )
                .first()
            )
        except Exception as e:
            logger.info(f"17-19号访问统计查询失败: {e}")
            october_stats = None

        # 获取推广码访问排行
        try:
            promotion_ranking = (
                db.session.query(
                    PromotionTrack.promotion_code,
                    db.func.count(PromotionTrack.id).label("visit_count"),
                    db.func.count(
                        case([(PromotionTrack.visitor_user_id == "anonymous", 1)], else_=0)
                    ).label("anonymous_count"),
                )
                .group_by(PromotionTrack.promotion_code)
                .order_by(db.func.count(PromotionTrack.id).desc())
                .limit(10)
                .all()
            )
        except Exception as e:
            logger.info(f"推广码排行查询失败: {e}")
            promotion_ranking = []

        # 获取最近的访问记录
        recent_visits = (
            PromotionTrack.query.order_by(PromotionTrack.visit_time.desc()).limit(20).all()
        )

        recent_visit_list = []
        for visit in recent_visits:
            visit_time = (
                datetime.fromtimestamp(visit.visit_time / 1000) if visit.visit_time else None
            )
            recent_visit_list.append(
                {
                    "id": visit.id,
                    "promotion_code": visit.promotion_code,
                    "referrer_user_id": visit.referrer_user_id,
                    "visitor_id": visit.visitor_user_id,
                    "visit_time": visit_time.strftime("%Y-%m-%d %H:%M:%S") if visit_time else None,
                    "is_anonymous": visit.visitor_user_id == "anonymous",
                    "create_time": visit.create_time.isoformat() if visit.create_time else None,
                }
            )

        return jsonify(
            {
                "success": True,
                "statistics": {
                    "total_visits": total_stats.total_visits if total_stats else 0,
                    "anonymous_visits": total_stats.anonymous_visits if total_stats else 0,
                    "real_visits": total_stats.real_visits if total_stats else 0,
                    "october_17_19_visits": october_stats.october_visits if october_stats else 0,
                    "october_anonymous_visits": (
                        october_stats.october_anonymous_visits if october_stats else 0
                    ),
                    "october_real_visits": (
                        october_stats.october_real_visits if october_stats else 0
                    ),
                },
                "promotion_ranking": [
                    {
                        "promotion_code": item.promotion_code,
                        "visit_count": item.visit_count,
                        "anonymous_count": item.anonymous_count,
                    }
                    for item in promotion_ranking
                ],
                "recent_visits": recent_visit_list,
            }
        )

    except Exception as e:
        logger.info(f"获取推广访问统计失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取推广访问统计失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/commission/<int:commission_id>", methods=["GET"])
@login_required
def get_admin_commission_detail(commission_id):
    """获取分佣详情（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        Commission = models["Commission"]
        PromotionUser = models["PromotionUser"]

        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({"success": False, "message": "分佣记录不存在"}), 404

        user = PromotionUser.query.filter_by(user_id=commission.referrer_user_id).first()
        if not user:
            return jsonify({"success": False, "message": "推广用户不存在"}), 404

        return jsonify(
            {
                "success": True,
                "commission": {
                    "id": commission.id,
                    "order_id": commission.order_id,
                    "amount": commission.amount,
                    "rate": commission.rate,
                    "status": commission.status,
                    "create_time": (
                        commission.create_time.isoformat() if commission.create_time else None
                    ),
                    "complete_time": (
                        commission.complete_time.isoformat() if commission.complete_time else None
                    ),
                    "user": {
                        "user_id": user.user_id,
                        "promotion_code": user.promotion_code,
                        "nickname": user.nickname,
                        "avatar_url": user.avatar_url,
                        "total_earnings": user.total_earnings,
                        "total_orders": user.total_orders,
                    },
                },
            }
        )

    except Exception as e:
        logger.info(f"获取分佣详情失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取分佣详情失败: {str(e)}"}), 500


@admin_promotion_api_bp.route(
    "/api/promotion/commission/<int:commission_id>/status", methods=["PUT"]
)
@login_required
def update_commission_status(commission_id):
    """更新分佣状态（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        Commission = models["Commission"]
        send_commission_notification_auto = models.get("send_commission_notification_auto")

        data = request.get_json()
        new_status = data.get("status")

        if new_status not in ["pending", "completed", "cancelled"]:
            return jsonify({"success": False, "message": "无效的状态值"}), 400

        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({"success": False, "message": "分佣记录不存在"}), 404

        old_status = commission.status
        commission.status = new_status

        # 如果状态变为completed，更新完成时间
        if new_status == "completed" and not commission.complete_time:
            commission.complete_time = datetime.now()

            # 自动发送推广收益通知
            if send_commission_notification_auto:
                try:
                    send_commission_notification_auto(commission)
                except Exception as e:
                    logger.info(f"发送分佣通知失败: {e}")

        db.session.commit()

        logger.info(f"分佣状态更新: {commission_id} {old_status} -> {new_status}")

        return jsonify({"success": True, "message": "分佣状态更新成功"})

    except Exception as e:
        logger.info(f"更新分佣状态失败: {e}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"success": False, "message": f"更新分佣状态失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/commission/<int:commission_id>", methods=["DELETE"])
@login_required
def delete_commission(commission_id):
    """删除分佣记录（后台管理）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        Commission = models["Commission"]

        commission = Commission.query.get(commission_id)
        if not commission:
            return jsonify({"success": False, "message": "分佣记录不存在"}), 404

        db.session.delete(commission)
        db.session.commit()

        logger.info(f"分佣记录删除成功: ID={commission_id}")

        return jsonify({"success": True, "message": "分佣记录删除成功"})

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"删除分佣记录失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"删除分佣记录失败: {str(e)}"}), 500


@admin_promotion_api_bp.route("/api/promotion/user/<user_id>", methods=["DELETE"])
@login_required
def delete_promotion_user(user_id):
    """删除推广用户（后台管理）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]
        Commission = models["Commission"]
        PromotionTrack = models["PromotionTrack"]

        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"success": False, "message": "推广用户不存在"}), 404

        # 删除相关的分佣记录
        Commission.query.filter_by(referrer_user_id=user_id).delete()

        # ⭐ 提现功能已删除，不再删除提现记录

        # 删除相关的推广访问记录
        PromotionTrack.query.filter_by(referrer_user_id=user_id).delete()
        PromotionTrack.query.filter_by(visitor_user_id=user_id).delete()

        # 删除用户
        db.session.delete(user)
        db.session.commit()

        logger.info(f"推广用户删除成功: user_id={user_id}, 推广码={user.promotion_code}")

        return jsonify({"success": True, "message": "推广用户删除成功"})

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"删除推广用户失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"删除推广用户失败: {str(e)}"}), 500
