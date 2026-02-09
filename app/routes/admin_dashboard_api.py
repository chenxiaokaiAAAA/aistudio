# -*- coding: utf-8 -*-
"""
仪表盘API接口
"""

import logging

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from app.utils.admin_helpers import get_models

admin_dashboard_api_bp = Blueprint("admin_dashboard_api", __name__)


@admin_dashboard_api_bp.route("/api/admin/dashboard/revenue", methods=["GET"])
@login_required
def get_revenue_detail():
    """获取业绩详情"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        Order = models["Order"]

        period = request.args.get("period", "today")
        today = datetime.now().date()

        # 根据时间段设置查询条件
        if period == "yesterday":
            start_date = today - timedelta(days=1)
            end_date = today
        elif period == "today":
            start_date = today
            end_date = today + timedelta(days=1)
        elif period == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = today + timedelta(days=1)
        elif period == "month":
            start_date = today.replace(day=1)
            end_date = today + timedelta(days=1)
        else:
            return jsonify({"success": False, "message": "无效的时间段"}), 400

        # 使用数据库聚合函数计算总金额（优化：避免在内存中计算）
        total_revenue = (
            Order.query.filter(
                func.date(Order.completed_at) >= start_date,
                func.date(Order.completed_at) < end_date,
                Order.status == "completed",
            )
            .with_entities(func.sum(Order.price))
            .scalar()
            or 0.0
        )

        # 查询订单列表（限制100条用于展示）
        orders = (
            Order.query.filter(
                func.date(Order.completed_at) >= start_date,
                func.date(Order.completed_at) < end_date,
                Order.status == "completed",
            )
            .order_by(Order.completed_at.desc())
            .limit(100)
            .all()
        )

        # 获取订单总数（用于统计）
        order_count = Order.query.filter(
            func.date(Order.completed_at) >= start_date,
            func.date(Order.completed_at) < end_date,
            Order.status == "completed",
        ).count()

        orders_list = []
        for order in orders:
            orders_list.append(
                {
                    "order_number": order.order_number,
                    "price": float(order.price or 0),
                    "completed_at": (
                        order.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                        if order.completed_at
                        else None
                    ),
                }
            )

        return jsonify(
            {
                "success": True,
                "total_revenue": float(total_revenue),
                "order_count": order_count,
                "orders": orders_list,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"获取业绩详情失败: {str(e)}"}), 500


@admin_dashboard_api_bp.route("/api/admin/dashboard/processing-orders", methods=["GET"])
@login_required
def get_processing_orders():
    """获取处理中订单列表（包含任务进度）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        Order = models["Order"]
        AITask = models.get("AITask")

        # 查询处理中的订单
        orders = (
            Order.query.filter(Order.status == "processing")
            .order_by(Order.created_at.desc())
            .limit(50)
            .all()
        )

        # 批量查询所有订单的AI任务（优化N+1查询）
        order_ids = [order.id for order in orders]
        ai_tasks_map = {}
        if AITask and order_ids:
            # 为每个订单获取最新的AI任务
            subquery = (
                db.session.query(
                    AITask.order_id, func.max(AITask.created_at).label("max_created_at")
                )
                .filter(AITask.order_id.in_(order_ids))
                .group_by(AITask.order_id)
                .subquery()
            )

            latest_tasks = AITask.query.join(
                subquery,
                db.and_(
                    AITask.order_id == subquery.c.order_id,
                    AITask.created_at == subquery.c.max_created_at,
                ),
            ).all()

            # 构建映射：order_id -> ai_task
            for task in latest_tasks:
                if task.order_id not in ai_tasks_map:
                    ai_tasks_map[task.order_id] = task

        orders_list = []
        for order in orders:
            # 从映射中获取AI任务（避免N+1查询）
            ai_task = ai_tasks_map.get(order.id)
            ai_task_status = None
            ai_task_retry_count = 0
            ai_task_error_message = None
            if ai_task:
                ai_task_status = ai_task.status
                ai_task_retry_count = getattr(ai_task, "retry_count", 0) or 0
                ai_task_error_message = getattr(ai_task, "error_message", None)

            orders_list.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "created_at": (
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None
                    ),
                    "shooting_completed_at": (
                        order.shooting_completed_at.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(order, "shooting_completed_at") and order.shooting_completed_at
                        else None
                    ),
                    "retouch_completed_at": (
                        order.retouch_completed_at.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(order, "retouch_completed_at") and order.retouch_completed_at
                        else None
                    ),
                    "completed_at": (
                        order.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                        if order.completed_at
                        else None
                    ),
                    "ai_task_status": ai_task_status,
                    "ai_task_retry_count": ai_task_retry_count,
                    "ai_task_error_message": ai_task_error_message,
                }
            )

        return jsonify({"success": True, "orders": orders_list})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取处理中订单失败: {str(e)}"}), 500


@admin_dashboard_api_bp.route("/api/admin/dashboard/completed-orders", methods=["GET"])
@login_required
def get_completed_orders():
    """获取已完成订单列表"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        Order = models["Order"]

        # 查询已完成的订单（最近50条）
        orders = (
            Order.query.filter(Order.status == "completed")
            .order_by(Order.completed_at.desc())
            .limit(50)
            .all()
        )

        orders_list = []
        for order in orders:
            orders_list.append(
                {
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "price": float(order.price or 0),
                    "status": order.status,
                    "created_at": (
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None
                    ),
                    "completed_at": (
                        order.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                        if order.completed_at
                        else None
                    ),
                }
            )

        return jsonify({"success": True, "orders": orders_list})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取已完成订单失败: {str(e)}"}), 500


@admin_dashboard_api_bp.route("/api/admin/dashboard/error-orders", methods=["GET"])
@login_required
def get_error_orders():
    """获取异常订单列表"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        db = models["db"]
        Order = models["Order"]
        AITask = models.get("AITask")

        # 查询异常订单：状态为failed或error，或者有printer错误信息
        orders = (
            Order.query.filter(
                or_(Order.status.in_(["failed", "error"]), Order.printer_error_message.isnot(None))
            )
            .order_by(Order.created_at.desc())
            .limit(50)
            .all()
        )

        # 批量查询所有订单的AI任务（优化N+1查询）
        order_ids = [order.id for order in orders]
        ai_tasks_map = {}
        if AITask and order_ids:
            # 为每个订单获取最新的AI任务（包含错误信息）
            subquery = (
                db.session.query(
                    AITask.order_id, func.max(AITask.created_at).label("max_created_at")
                )
                .filter(AITask.order_id.in_(order_ids))
                .group_by(AITask.order_id)
                .subquery()
            )

            latest_tasks = AITask.query.join(
                subquery,
                db.and_(
                    AITask.order_id == subquery.c.order_id,
                    AITask.created_at == subquery.c.max_created_at,
                ),
            ).all()

            # 构建映射：order_id -> ai_task
            for task in latest_tasks:
                if task.order_id not in ai_tasks_map:
                    ai_tasks_map[task.order_id] = task

        orders_list = []
        for order in orders:
            # 获取错误信息（从printer_error_message或AI任务错误信息）
            error_message = getattr(order, "printer_error_message", None)
            if not error_message:
                # 从映射中获取AI任务（避免N+1查询）
                ai_task = ai_tasks_map.get(order.id)
                if ai_task and ai_task.error_message:
                    error_message = ai_task.error_message

            orders_list.append(
                {
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "price": float(order.price or 0),
                    "status": order.status,
                    "error_message": error_message or "状态异常",
                    "created_at": (
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None
                    ),
                }
            )

        return jsonify({"success": True, "orders": orders_list})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取异常订单失败: {str(e)}"}), 500
