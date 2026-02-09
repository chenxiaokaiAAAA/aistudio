# -*- coding: utf-8 -*-
"""
优惠券相关API路由
包含：获取用户可领取的优惠券数量
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 导入主蓝图
from . import user_api_bp


@user_api_bp.route("/coupons/available-count", methods=["GET"])
def get_available_coupon_count():
    """获取用户可领取的优惠券数量"""
    try:
        models = get_models()
        if not models:
            return jsonify({"success": True, "availableCount": 0})

        Coupon = models.get("Coupon")
        UserCoupon = models.get("UserCoupon")

        # 如果优惠券模型不存在，返回0
        if not Coupon or not UserCoupon:
            return jsonify({"success": True, "availableCount": 0})

        db = models["db"]
        user_id = request.args.get("userId")

        if not user_id:
            return jsonify({"success": True, "availableCount": 0})

        # 查询可领取的优惠券（状态为active，在有效期内，还有剩余数量）
        now = datetime.now()
        available_coupons = Coupon.query.filter(
            Coupon.status == "active", Coupon.start_time <= now, Coupon.end_time > now
        ).all()

        # 优化N+1查询：批量查询用户已领取的优惠券数量
        coupon_ids = [coupon.id for coupon in available_coupons]
        user_coupon_counts_map = {}
        claimed_counts_map = {}
        if coupon_ids:
            from sqlalchemy import func

            # 批量查询用户已领取的优惠券数量
            user_coupon_counts = (
                db.session.query(UserCoupon.coupon_id, func.count(UserCoupon.id).label("count"))
                .filter(UserCoupon.user_id == user_id, UserCoupon.coupon_id.in_(coupon_ids))
                .group_by(UserCoupon.coupon_id)
                .all()
            )
            user_coupon_counts_map = {coupon_id: count for coupon_id, count in user_coupon_counts}

            # 批量查询所有优惠券的已领取数量
            claimed_counts = (
                db.session.query(UserCoupon.coupon_id, func.count(UserCoupon.id).label("count"))
                .filter(UserCoupon.coupon_id.in_(coupon_ids))
                .group_by(UserCoupon.coupon_id)
                .all()
            )
            claimed_counts_map = {coupon_id: count for coupon_id, count in claimed_counts}

        available_count = 0
        for coupon in available_coupons:
            # 从批量查询的映射中获取用户已领取数量（避免N+1查询）
            user_coupon_count = user_coupon_counts_map.get(coupon.id, 0)

            # 检查是否达到每用户限领数量
            if user_coupon_count < coupon.per_user_limit:
                # 从批量查询的映射中获取已领取数量（避免N+1查询）
                claimed_count = claimed_counts_map.get(coupon.id, 0)
                remaining_count = max(0, (coupon.total_count or 0) - claimed_count)

                # 如果还有剩余数量，则计入可领取数量
                if remaining_count > 0:
                    available_count += 1

        return jsonify({"success": True, "availableCount": available_count})

    except Exception as e:
        logger.error("获取可用优惠券数量失败: {str(e)}")
        # 即使出错也返回0，避免前端报错
        return jsonify({"success": True, "availableCount": 0})
