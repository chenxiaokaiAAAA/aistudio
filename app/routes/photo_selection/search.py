# -*- coding: utf-8 -*-
"""
选片页面 - 搜索相关功能
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint, jsonify, request

from app.utils.admin_helpers import get_models

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_search", __name__)


@bp.route("/api/photo-selection/search-orders", methods=["POST"])
def search_orders_for_selection():
    """通过手机号或订单号查询订单（用于选片）"""
    try:
        data = request.get_json() or {}
        phone = data.get("phone", "").strip()
        order_number = data.get("order_number", "").strip()
        franchisee_id = data.get("franchisee_id")

        if not phone and not order_number:
            return jsonify({"success": False, "message": "请提供手机号或订单号"}), 400

        if not franchisee_id:
            return jsonify({"success": False, "message": "缺少加盟商ID"}), 400

        models = get_models(["Order"])
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        Order = models["Order"]

        # 构建查询条件
        query = Order.query.filter(Order.franchisee_id == franchisee_id, Order.status != "unpaid")

        # 根据手机号或订单号查询
        if phone:
            # 验证手机号格式
            if not phone.isdigit() or len(phone) != 11:
                return (
                    jsonify({"success": False, "message": "手机号格式不正确（应为11位数字）"}),
                    400,
                )
            query = query.filter(Order.customer_phone == phone)

        if order_number:
            query = query.filter(Order.order_number.like(f"%{order_number}%"))

        # 查询订单
        orders = query.order_by(Order.created_at.desc()).limit(50).all()  # 最多返回50条

        if not orders:
            return jsonify({"success": False, "message": "未找到符合条件的订单"}), 404

        # 构建订单列表数据
        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name or "",
                    "customer_phone": order.customer_phone or "",
                    "status": order.status,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                }
            )

        return jsonify(
            {
                "success": True,
                "franchisee_id": franchisee_id,
                "orders": orders_data,
                "count": len(orders_data),
                "message": f"找到 {len(orders_data)} 个订单",
            }
        )

    except Exception as e:
        logger.info(f"查询订单失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"查询失败: {str(e)}"}), 500
