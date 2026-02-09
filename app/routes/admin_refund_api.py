# -*- coding: utf-8 -*-
"""
退款审核API路由模块
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
bp = Blueprint("admin_refund_api", __name__, url_prefix="/api/admin/refund")


@bp.route("/list", methods=["GET"])
@login_required
@admin_required
def get_refund_list():
    """获取退款申请列表"""
    try:
        models = get_models(["Order", "FranchiseeAccount", "db"])
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Order = models["Order"]
        FranchiseeAccount = models["FranchiseeAccount"]

        # 获取筛选参数
        status = request.args.get("status", "all")
        franchisee_id = request.args.get("franchisee_id", "")
        page = request.args.get("page", 1, type=int)
        per_page = 20

        # 构建查询
        query = Order.query.filter(Order.refund_request_status.isnot(None))

        if status != "all":
            query = query.filter(Order.refund_request_status == status)

        if franchisee_id:
            query = query.filter(Order.franchisee_id == int(franchisee_id))

        # 优化：使用数据库层面分页
        pagination = query.order_by(Order.refund_request_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        refund_requests = pagination.items

        # 优化N+1查询：批量查询所有加盟商信息
        franchisee_ids = [order.franchisee_id for order in refund_requests if order.franchisee_id]
        franchisee_map = {}
        if franchisee_ids:
            all_franchisees = FranchiseeAccount.query.filter(
                FranchiseeAccount.id.in_(franchisee_ids)
            ).all()
            for franchisee in all_franchisees:
                franchisee_map[franchisee.id] = franchisee

        result = []
        for order in refund_requests:
            # 从批量查询的映射中获取加盟商信息（避免N+1查询）
            franchisee_name = ""
            if order.franchisee_id:
                franchisee = franchisee_map.get(order.franchisee_id)
                if franchisee:
                    franchisee_name = franchisee.company_name

            result.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "customer_phone": order.customer_phone,
                    "price": float(order.price or 0),
                    "franchisee_deduction": float(order.franchisee_deduction or 0),
                    "franchisee_name": franchisee_name,
                    "refund_request_reason": order.refund_request_reason,
                    "refund_request_time": (
                        order.refund_request_time.strftime("%Y-%m-%d %H:%M:%S")
                        if order.refund_request_time
                        else ""
                    ),
                    "refund_request_status": order.refund_request_status,
                    "status": order.status,
                    "created_at": (
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else ""
                    ),
                }
            )

        return jsonify(
            {
                "status": "success",
                "data": result,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取退款申请列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取退款申请列表失败: {str(e)}"}), 500


@bp.route("/approve/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def approve_refund(order_id):
    """批准退款申请"""
    try:
        models = get_models(["Order", "FranchiseeAccount", "FranchiseeRecharge", "db"])
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Order = models["Order"]
        FranchiseeAccount = models["FranchiseeAccount"]
        FranchiseeRecharge = models["FranchiseeRecharge"]
        db = models["db"]

        order = Order.query.get_or_404(order_id)

        if not order.refund_request_status or order.refund_request_status != "pending":
            return jsonify({"status": "error", "message": "该订单没有待处理的退款申请"}), 400

        if not order.franchisee_id:
            return jsonify({"status": "error", "message": "该订单不是加盟商订单，无法退款"}), 400

        account = FranchiseeAccount.query.get(order.franchisee_id)
        if not account:
            return jsonify({"status": "error", "message": "加盟商账户不存在"}), 404

        # 计算退款金额
        refund_amount = order.franchisee_deduction or order.price

        # 返还资金到加盟商账户
        account.remaining_quota += refund_amount
        account.used_quota = max(0, account.used_quota - refund_amount)

        # 创建退款记录
        recharge_record = FranchiseeRecharge(
            franchisee_id=order.franchisee_id,
            amount=refund_amount,
            admin_user_id=current_user.id,
            recharge_type="refund",
            description=f"订单 {order.order_number} 退款 - {order.refund_request_reason}",
        )
        db.session.add(recharge_record)

        # 更新订单状态
        order.refund_request_status = "approved"
        order.status = "cancelled"

        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": "退款已批准，资金已返还到加盟商账户",
                "data": {
                    "refund_amount": refund_amount,
                    "remaining_quota": account.remaining_quota,
                },
            }
        )

    except Exception as e:
        logger.info(f"批准退款失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"批准退款失败: {str(e)}"}), 500


@bp.route("/reject/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def reject_refund(order_id):
    """拒绝退款申请"""
    try:
        models = get_models(["Order", "db"])
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Order = models["Order"]
        db = models["db"]

        order = Order.query.get_or_404(order_id)

        if not order.refund_request_status or order.refund_request_status != "pending":
            return jsonify({"status": "error", "message": "该订单没有待处理的退款申请"}), 400

        data = request.get_json() or {}
        reject_reason = data.get("reason", "管理员拒绝退款申请")

        # 更新订单状态
        order.refund_request_status = "rejected"
        if not order.refund_request_reason:
            order.refund_request_reason = reject_reason
        else:
            order.refund_request_reason += f"\n[拒绝原因: {reject_reason}]"

        db.session.commit()

        return jsonify({"status": "success", "message": "退款申请已拒绝"})

    except Exception as e:
        logger.info(f"拒绝退款失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"拒绝退款失败: {str(e)}"}), 500
