# -*- coding: utf-8 -*-
"""
佣金提现相关API路由
包含：获取用户分佣数据、获取用户提现申请记录
"""

import logging

logger = logging.getLogger(__name__)
import sys

from flask import Blueprint, jsonify, request

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 导入主蓝图
from . import user_api_bp


@user_api_bp.route("/commission", methods=["GET"])
def get_user_commission():
    """获取用户分佣数据"""
    try:
        user_id = request.args.get("userId")
        logger.info(f"查询用户分佣: userId={user_id}")

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        PromotionUser = models["PromotionUser"]
        Commission = models["Commission"]
        Order = models["Order"]
        Withdrawal = models["Withdrawal"]

        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        commissions = (
            Commission.query.filter_by(referrer_user_id=user_id)
            .order_by(Commission.create_time.desc())
            .all()
        )

        # 优化N+1查询：批量查询所有订单
        order_numbers = [c.order_id for c in commissions if c.order_id]
        orders_map = {}
        if order_numbers:
            all_orders = Order.query.filter(Order.order_number.in_(order_numbers)).all()
            orders_map = {order.order_number: order for order in all_orders}

        orders = []
        total_commission = 0

        for commission in commissions:
            order = orders_map.get(commission.order_id)
            if order:
                if order.status == "delivered":
                    commission_status = "completed"
                    commission_status_text = "已结算"
                    total_commission += commission.amount
                else:
                    commission_status = "pending"
                    commission_status_text = "待结算"

                orders.append(
                    {
                        "orderId": commission.order_id,
                        "productName": order.size or "定制产品",
                        "totalPrice": float(order.price or 0),
                        "commissionAmount": float(commission.amount),
                        "commissionStatus": commission_status,
                        "commissionStatusText": commission_status_text,
                        "createTime": (
                            commission.create_time.strftime("%Y-%m-%d %H:%M:%S")
                            if commission.create_time
                            else ""
                        ),
                        "completeTime": (
                            commission.complete_time.strftime("%Y-%m-%d %H:%M:%S")
                            if commission.complete_time
                            else ""
                        ),
                    }
                )

        withdrawals = Withdrawal.query.filter_by(user_id=user_id).all()
        total_withdrawn = sum(
            withdrawal.amount for withdrawal in withdrawals if withdrawal.status == "approved"
        )
        available_earnings = total_commission - total_withdrawn

        return jsonify(
            {
                "success": True,
                "totalEarnings": available_earnings,
                "totalCommission": total_commission,
                "totalWithdrawn": total_withdrawn,
                "totalOrders": user.total_orders,
                "orders": orders,
                "commissions": [
                    {
                        "id": c.id,
                        "orderId": c.order_id,
                        "amount": c.amount,
                        "rate": c.rate,
                        "status": c.status,
                        "createTime": c.create_time.isoformat() if c.create_time else None,
                        "completeTime": c.complete_time.isoformat() if c.complete_time else None,
                    }
                    for c in commissions
                ],
            }
        )

    except Exception as e:
        logger.info(f"获取分佣数据失败: {e}")
        return jsonify({"success": False, "message": f"获取分佣数据失败: {str(e)}"}), 500


@user_api_bp.route("/withdrawals", methods=["GET"])
def get_user_withdrawals():
    """获取用户提现申请记录"""
    try:
        user_id = request.args.get("userId")
        logger.info(f"查询用户提现记录: userId={user_id}")

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        Withdrawal = models["Withdrawal"]

        withdrawals = (
            Withdrawal.query.filter_by(user_id=user_id).order_by(Withdrawal.apply_time.desc()).all()
        )

        status_map = {
            "pending": "待审核",
            "approved": "审核通过",
            "rejected": "审核拒绝",
            "completed": "已完成",
        }

        withdrawal_list = []
        for withdrawal in withdrawals:
            withdrawal_list.append(
                {
                    "id": withdrawal.id,
                    "amount": float(withdrawal.amount),
                    "status": withdrawal.status,
                    "statusText": status_map.get(withdrawal.status, "未知状态"),
                    "applyTime": (
                        withdrawal.apply_time.strftime("%Y-%m-%d %H:%M:%S")
                        if withdrawal.apply_time
                        else ""
                    ),
                    "approveTime": (
                        withdrawal.approve_time.strftime("%Y-%m-%d %H:%M:%S")
                        if withdrawal.approve_time
                        else ""
                    ),
                    "adminNotes": withdrawal.admin_notes or "",
                }
            )

        return jsonify({"success": True, "withdrawals": withdrawal_list})

    except Exception as e:
        logger.info(f"获取提现记录失败: {e}")
        return jsonify({"success": False, "message": f"获取提现记录失败: {str(e)}"}), 500
