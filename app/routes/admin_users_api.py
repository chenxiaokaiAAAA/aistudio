# -*- coding: utf-8 -*-
"""
管理后台用户管理API路由模块
从 test_server.py 迁移用户管理相关路由
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_users_api_bp = Blueprint("admin_users_api", __name__)


@admin_users_api_bp.route("/admin/users")
@login_required
def admin_all_users():
    """所有用户访问统计页面"""
    if current_user.role not in ["admin", "operator"]:
        from flask import redirect, url_for

        return redirect(url_for("auth.login"))
    return render_template("admin/all_users.html")


@admin_users_api_bp.route("/api/admin/users/all", methods=["GET"])
@login_required
def get_all_users_access():
    """获取所有用户访问统计（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        calculate_visit_frequency = models.get("calculate_visit_frequency")

        # 获取查询参数
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        search = request.args.get("search", "")

        # 构建基础查询（使用SQLAlchemy的text()函数，PostgreSQL）
        from sqlalchemy import text

        # PostgreSQL使用%s占位符
        placeholder = "%s"

        # 构建WHERE子句
        where_clause = ""
        params = []
        if search:
            where_clause = f" WHERE openid LIKE {placeholder} OR temp_promotion_code LIKE {placeholder} OR final_promotion_code LIKE {placeholder}"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        # 优化：使用数据库层面的分页（LIMIT和OFFSET）
        # 先查询总数
        count_query = f"SELECT COUNT(*) FROM user_access_stats{where_clause}"
        total = db.session.execute(text(count_query), params).scalar()

        # 构建数据查询（带分页）
        # 注意：LIMIT和OFFSET不能使用参数绑定，需要直接使用值
        offset = (page - 1) * per_page
        data_query = """
            SELECT
                openid,
                total_visits,
                first_visit,
                last_visit,
                authorized_visits,
                registered_visits,
                ordered_visits,
                temp_promotion_code,
                final_promotion_code,
                has_ordered_flag
            FROM user_access_stats
            {where_clause}
            ORDER BY total_visits DESC, last_visit DESC
            LIMIT {per_page} OFFSET {offset}
        """
        data_params = params

        # 执行查询（只查询当前页的数据）
        result = db.session.execute(text(data_query), data_params)
        users = result.fetchall()

        # 格式化数据
        user_list = []
        for user in users:
            user_data = {
                "openid": user[0],
                "total_visits": user[1],
                "first_visit": user[2],
                "last_visit": user[3],
                "authorized_visits": user[4],
                "registered_visits": user[5],
                "ordered_visits": user[6],
                "temp_promotion_code": user[7],
                "final_promotion_code": user[8],
                "has_ordered": bool(user[9]),
            }

            # 计算访问频率
            if calculate_visit_frequency:
                user_data["visit_frequency"] = calculate_visit_frequency(user[2], user[3], user[1])
            else:
                user_data["visit_frequency"] = "未知"

            user_list.append(user_data)

        return jsonify(
            {
                "success": True,
                "users": user_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取所有用户访问统计失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取所有用户访问统计失败: {str(e)}"}), 500


@admin_users_api_bp.route("/api/admin/users/miniprogram/clear", methods=["POST"])
@login_required
def clear_miniprogram_users():
    """清空所有小程序用户数据（仅admin）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足，仅管理员可执行此操作"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]
        PromotionTrack = models["PromotionTrack"]
        Commission = models["Commission"]
        Withdrawal = models["Withdrawal"]
        UserVisit = models["UserVisit"]

        # 获取确认参数
        data = request.get_json() or {}
        confirm = data.get("confirm", False)

        if not confirm:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "请确认要清空所有小程序用户数据",
                        "requiresConfirm": True,
                    }
                ),
                400,
            )

        # 统计要删除的数据
        user_count = PromotionUser.query.count()
        track_count = PromotionTrack.query.count()
        commission_count = Commission.query.count()
        withdrawal_count = Withdrawal.query.count()
        visit_count = UserVisit.query.count()

        logger.info("准备清空小程序用户数据:")
        logger.info(f"  - 用户数: {user_count}")
        logger.info(f"  - 推广追踪记录: {track_count}")
        logger.info(f"  - 分佣记录: {commission_count}")
        logger.info(f"  - 提现记录: {withdrawal_count}")
        logger.info(f"  - 访问记录: {visit_count}")

        # 删除数据（按依赖关系顺序）
        deleted_counts = {}

        # 1. 删除提现记录（依赖用户）
        deleted_counts["withdrawals"] = Withdrawal.query.delete()

        # 2. 删除分佣记录（依赖用户）
        deleted_counts["commissions"] = Commission.query.delete()

        # 3. 删除推广追踪记录（依赖用户）
        deleted_counts["tracks"] = PromotionTrack.query.delete()

        # 4. 删除用户访问记录
        deleted_counts["visits"] = UserVisit.query.delete()

        # 5. 删除用户（最后删除）
        deleted_counts["users"] = PromotionUser.query.delete()

        db.session.commit()

        logger.info("✅ 清空完成:")
        logger.info(f"  - 已删除用户: {deleted_counts['users']}")
        logger.info(f"  - 已删除推广追踪: {deleted_counts['tracks']}")
        logger.info(f"  - 已删除分佣记录: {deleted_counts['commissions']}")
        logger.info(f"  - 已删除提现记录: {deleted_counts['withdrawals']}")
        logger.info(f"  - 已删除访问记录: {deleted_counts['visits']}")

        return jsonify(
            {"success": True, "message": "小程序用户数据已清空", "deleted": deleted_counts}
        )

    except Exception as e:
        logger.info(f"清空小程序用户数据失败: {e}")
        import traceback

        traceback.print_exc()
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"清空数据失败: {str(e)}"}), 500


@admin_users_api_bp.route("/api/admin/promotion/user/own-orders", methods=["GET"])
@login_required
def get_user_own_orders():
    """获取用户自己的订单（后台管理）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

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
            # PostgreSQL使用orders表
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
            # SQLite使用orders表
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
