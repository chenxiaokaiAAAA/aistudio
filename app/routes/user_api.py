# -*- coding: utf-8 -*-
"""
用户相关API路由模块
从 test_server.py 迁移所有 /api/user/* 路由
"""

import logging

logger = logging.getLogger(__name__)
import base64
import json
import random
import string
import sys
import time
from datetime import datetime

import requests
from flask import Blueprint, jsonify, request

# 尝试导入 Crypto（可选）
try:
    from Crypto.Cipher import AES

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("Crypto模块未安装，手机号解密功能将不可用。请安装: pip install pycryptodome")

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
user_api_bp = Blueprint("user_api", __name__, url_prefix="/api/user")


def get_utils():
    """获取工具函数（延迟导入）"""
    from app.utils.helpers import (
        check_user_has_placed_order,
        generate_promotion_code,
        generate_stable_promotion_code,
        generate_stable_user_id,
        validate_promotion_code,
    )

    return {
        "check_user_has_placed_order": check_user_has_placed_order,
        "validate_promotion_code": validate_promotion_code,
        "generate_promotion_code": generate_promotion_code,
        "generate_stable_promotion_code": generate_stable_promotion_code,
        "generate_stable_user_id": generate_stable_user_id,
    }


@user_api_bp.route("/check", methods=["POST"])
def check_user():
    """检查用户是否存在接口"""
    try:
        data = request.get_json()
        phone_number = data.get("phoneNumber")
        open_id = data.get("openId")

        if not phone_number and not open_id:
            return (
                jsonify({"success": False, "message": "缺少必要参数：phoneNumber 或 openId"}),
                400,
            )

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        # 优先通过手机号查找（PromotionUser表中有phone_number字段）
        if phone_number:
            promotion_user = PromotionUser.query.filter_by(phone_number=phone_number).first()
            if promotion_user:
                return jsonify(
                    {
                        "success": True,
                        "exists": True,
                        "userId": promotion_user.user_id,
                        "promotionCode": promotion_user.promotion_code,
                    }
                )

        # 通过openId查找
        if open_id:
            promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
            if promotion_user:
                return jsonify(
                    {
                        "success": True,
                        "exists": True,
                        "userId": promotion_user.user_id,
                        "promotionCode": promotion_user.promotion_code,
                    }
                )

        # 用户不存在
        return jsonify({"success": True, "exists": False, "userId": None})

    except Exception as e:
        logger.info(f"检查用户异常: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"检查用户失败: {str(e)}"}), 500


@user_api_bp.route("/openid", methods=["POST"])
def get_user_openid():
    """获取用户openid接口"""
    # ========== 开发模式：跳过真实openid验证 ==========
    DEV_MODE_SKIP_OPENID = True  # ⚠️ 上线前改为 False
    # ========== 开发模式结束 ==========

    try:
        data = request.get_json()
        code = data.get("code")

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        get_user_openid_service = models["get_user_openid_service"]

        # 调用服务层函数
        success, result, error_message = get_user_openid_service(
            code, dev_mode=DEV_MODE_SKIP_OPENID
        )

        if success:
            return jsonify({"success": True, **result})
        else:
            return jsonify({"success": False, "message": error_message}), 400

    except Exception as e:
        logger.info(f"获取openid异常: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取openid失败: {str(e)}"}), 500


@user_api_bp.route("/register", methods=["POST"])
def register_user():
    """小程序用户注册接口"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        promotion_code = data.get("promotionCode")
        open_id = data.get("openId")
        user_info = data.get("userInfo") or {}
        promotion_params = data.get("promotion_params")

        logger.info(
            f"用户注册请求: userId={user_id}, open_id={open_id}, promotion_params={promotion_params}"
        )

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]
        PromotionTrack = models["PromotionTrack"]
        Order = models["Order"]

        utils = get_utils()
        check_user_has_placed_order = utils["check_user_has_placed_order"]
        validate_promotion_code = utils["validate_promotion_code"]
        generate_promotion_code = utils["generate_promotion_code"]
        generate_stable_promotion_code = utils["generate_stable_promotion_code"]
        generate_stable_user_id = utils["generate_stable_user_id"]

        # 优先使用小程序传入的userId
        if user_id:
            logger.info(f"使用小程序传入的userId: {user_id}")
            existing_user = PromotionUser.query.filter_by(user_id=user_id).first()
            if existing_user:
                logger.info(
                    f"用户已存在: {existing_user.user_id}, 推广码: {existing_user.promotion_code}"
                )
                # 处理推广参数（如果存在）
                if promotion_params:
                    try:
                        params = {}
                        for item in promotion_params.split("&"):
                            if "=" in item:
                                key, value = item.split("=", 1)
                                params[key] = value
                        referrer_promotion_code = params.get("p")
                        referrer_user_id = params.get("u")
                        if referrer_promotion_code and referrer_user_id:
                            if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                                existing_track = PromotionTrack.query.filter_by(
                                    visitor_user_id=existing_user.user_id,
                                    referrer_user_id=referrer_user_id,
                                ).first()
                                if not existing_track:
                                    track = PromotionTrack(
                                        promotion_code=referrer_promotion_code,
                                        referrer_user_id=referrer_user_id,
                                        visitor_user_id=existing_user.user_id,
                                        visit_time=int(time.time()),
                                    )
                                    db.session.add(track)
                                    db.session.commit()
                    except Exception as e:
                        logger.info(f"处理已存在用户推广参数失败: {e}")

                return jsonify(
                    {
                        "success": True,
                        "message": "用户已存在",
                        "userId": existing_user.user_id,
                        "promotionCode": existing_user.promotion_code,
                        "isStable": False,
                    }
                )

        # 如果没有userId，使用OpenID进行稳定绑定
        elif open_id:
            logger.info(f"未提供userId，使用OpenID进行稳定绑定: {open_id}")
            existing_user = PromotionUser.query.filter_by(open_id=open_id).first()
            if existing_user:
                logger.info(
                    f"OpenID用户已存在: {existing_user.user_id}, 推广码: {existing_user.promotion_code}"
                )
                # 处理推广参数（类似上面的逻辑）
                if promotion_params:
                    try:
                        params = {}
                        for item in promotion_params.split("&"):
                            if "=" in item:
                                key, value = item.split("=", 1)
                                params[key] = value
                        referrer_promotion_code = params.get("p")
                        referrer_user_id = params.get("u")
                        if referrer_promotion_code and referrer_user_id:
                            if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                                existing_track = PromotionTrack.query.filter_by(
                                    visitor_user_id=existing_user.user_id,
                                    referrer_user_id=referrer_user_id,
                                ).first()
                                if not existing_track:
                                    track = PromotionTrack(
                                        promotion_code=referrer_promotion_code,
                                        referrer_user_id=referrer_user_id,
                                        visitor_user_id=existing_user.user_id,
                                        visit_time=int(time.time()),
                                    )
                                    db.session.add(track)
                                    db.session.commit()
                    except Exception as e:
                        logger.info(f"处理已存在用户推广参数失败: {e}")

                return jsonify(
                    {
                        "success": True,
                        "message": "用户已存在",
                        "userId": existing_user.user_id,
                        "promotionCode": existing_user.promotion_code,
                        "isStable": True,
                    }
                )

            # 基于OpenID生成稳定的用户ID和推广码
            stable_user_id = generate_stable_user_id(open_id)
            stable_promotion_code = generate_stable_promotion_code(open_id)

            if not stable_user_id or not stable_promotion_code:
                return jsonify({"success": False, "message": "生成稳定用户信息失败"}), 500

            # 检查是否已存在
            existing_user_id = PromotionUser.query.filter_by(user_id=stable_user_id).first()
            existing_promotion_code = PromotionUser.query.filter_by(
                promotion_code=stable_promotion_code
            ).first()

            if existing_user_id or existing_promotion_code:
                if existing_user_id:
                    return jsonify(
                        {
                            "success": True,
                            "message": "用户已存在",
                            "userId": existing_user_id.user_id,
                            "promotionCode": existing_user_id.promotion_code,
                            "isStable": True,
                        }
                    )

            user_id = stable_user_id
            promotion_code = stable_promotion_code
            logger.info(f"使用稳定用户信息: user_id={user_id}, promotion_code={promotion_code}")
        else:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        # 生成推广码（如果未提供）
        if not promotion_code:
            promotion_code = generate_promotion_code(user_id)

        # 只有下过单的用户才能享受推广码功能
        can_generate_promotion_code = check_user_has_placed_order(user_id)

        logger.info("=== 用户推广资格检查 ===")
        logger.info(f"用户ID: {user_id}")
        logger.info(f"是否有下单记录: {can_generate_promotion_code}")

        # 创建用户记录
        final_promotion_code = (
            promotion_code if can_generate_promotion_code else f"TEMP_{user_id[-6:]}"
        )

        new_user = PromotionUser(
            user_id=user_id,
            promotion_code=final_promotion_code,
            open_id=open_id,
            nickname=user_info.get("nickName", ""),
            avatar_url=user_info.get("avatarUrl", ""),
            phone_number=data.get("phoneNumber", ""),
            total_earnings=0.0,
            total_orders=0,
            eligible_for_promotion=can_generate_promotion_code,
        )

        db.session.add(new_user)
        db.session.commit()

        # 处理推广参数
        if promotion_params:
            try:
                params = {}
                for item in promotion_params.split("&"):
                    if "=" in item:
                        key, value = item.split("=", 1)
                        params[key] = value
                referrer_promotion_code = params.get("p")
                referrer_user_id = params.get("u")
                if referrer_promotion_code and referrer_user_id:
                    if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                        track = PromotionTrack(
                            promotion_code=referrer_promotion_code,
                            referrer_user_id=referrer_user_id,
                            visitor_user_id=user_id,
                            visit_time=int(time.time()),
                        )
                        db.session.add(track)
                        db.session.commit()
            except Exception as e:
                logger.info(f"处理推广参数失败: {e}")

        return jsonify(
            {
                "success": True,
                "message": "用户注册成功",
                "userId": user_id,
                "promotionCode": promotion_code,
            }
        )

    except Exception as e:
        logger.info(f"用户注册失败: {e}")
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"用户注册失败: {str(e)}"}), 500


@user_api_bp.route("/update-info", methods=["POST"])
def update_user_info():
    """更新用户信息接口"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        user_info = data.get("userInfo") or {}

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        user = PromotionUser.query.filter_by(user_id=user_id).first()
        if user:
            if user_info.get("nickName"):
                user.nickname = user_info["nickName"]
            if user_info.get("avatarUrl"):
                user.avatar_url = user_info["avatarUrl"]
            user.update_time = datetime.now()
            db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "message": "用户信息更新成功",
                    "data": {
                        "userId": user_id,
                        "nickname": user.nickname,
                        "avatarUrl": user.avatar_url,
                    },
                }
            )
        else:
            return jsonify({"success": False, "message": "用户不存在"}), 404

    except Exception as e:
        logger.info(f"用户信息更新失败: {e}")
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"}), 500


@user_api_bp.route("/check-promotion-eligibility", methods=["POST"])
def check_promotion_eligibility():
    """检查用户推广资格（是否下过单）"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        open_id = data.get("openId")

        logger.info(f"检查用户推广资格: user_id={user_id}, open_id={open_id}")

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        utils = get_utils()
        check_user_has_placed_order = utils["check_user_has_placed_order"]
        generate_stable_promotion_code = utils["generate_stable_promotion_code"]
        generate_promotion_code = utils["generate_promotion_code"]

        if not user_id and open_id:
            promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
            if promotion_user:
                user_id = promotion_user.user_id

        if not user_id:
            return jsonify({"success": False, "message": "用户ID或OpenID不能为空"}), 400

        promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not promotion_user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        has_order = check_user_has_placed_order(user_id)
        promotion_user.eligible_for_promotion = has_order

        if has_order and not promotion_user.promotion_code:
            if open_id:
                promotion_code = generate_stable_promotion_code(open_id)
            else:
                promotion_code = generate_promotion_code(user_id)

            while PromotionUser.query.filter_by(promotion_code=promotion_code).first():
                if open_id:
                    promotion_code = generate_stable_promotion_code(open_id + "_retry")
                else:
                    promotion_code = generate_promotion_code(user_id + "_retry")

            promotion_user.promotion_code = promotion_code

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "hasOrders": has_order,
                "eligibleForPromotion": promotion_user.eligible_for_promotion,
                "promotionCode": promotion_user.promotion_code,
                "message": "资格检查完成",
            }
        )

    except Exception as e:
        logger.info(f"检查推广资格失败: {e}")
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"检查失败: {str(e)}"}), 500


@user_api_bp.route("/update-promotion-eligibility", methods=["POST"])
def update_promotion_eligibility():
    """更新用户推广资格"""
    try:
        data = request.get_json()
        user_id = data.get("userId")

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        utils = get_utils()
        check_user_has_placed_order = utils["check_user_has_placed_order"]
        generate_stable_promotion_code = utils["generate_stable_promotion_code"]
        generate_promotion_code = utils["generate_promotion_code"]

        promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        if not promotion_user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        has_order = check_user_has_placed_order(user_id)
        promotion_user.eligible_for_promotion = has_order

        if has_order and not promotion_user.promotion_code:
            if promotion_user.open_id:
                promotion_code = generate_stable_promotion_code(promotion_user.open_id)
            else:
                promotion_code = generate_promotion_code(user_id)

            while PromotionUser.query.filter_by(promotion_code=promotion_code).first():
                if promotion_user.open_id:
                    promotion_code = generate_stable_promotion_code(
                        promotion_user.open_id + "_retry"
                    )
                else:
                    promotion_code = generate_promotion_code(user_id + "_retry")

            promotion_user.promotion_code = promotion_code

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "eligibleForPromotion": promotion_user.eligible_for_promotion,
                "promotionCode": promotion_user.promotion_code,
                "message": "推广资格更新成功",
            }
        )

    except Exception as e:
        logger.info(f"更新推广资格失败: {e}")
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"}), 500


@user_api_bp.route("/request-subscription-after-payment", methods=["POST"])
def request_subscription_after_payment():
    """支付成功后请求订阅消息"""
    try:
        data = request.get_json()
        open_id = data.get("openId")
        order_number = data.get("orderNumber")

        if not open_id or not order_number:
            return jsonify({"success": False, "message": "OpenID和订单号不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        Order = models["Order"]
        PromotionUser = models["PromotionUser"]

        utils = get_utils()
        check_user_has_placed_order = utils["check_user_has_placed_order"]
        generate_stable_promotion_code = utils["generate_stable_promotion_code"]

        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({"success": False, "message": "订单不存在"}), 404

        if order.status != "pending":
            return jsonify({"success": False, "message": "订单未完成支付或状态异常"}), 400

        if order.openid != open_id:
            return jsonify({"success": False, "message": "订单用户身份验证失败"}), 400

        current_time = datetime.now()
        if order.payment_time:
            time_diff = (current_time - order.payment_time).total_seconds()
            if time_diff > 3600:
                return (
                    jsonify(
                        {"success": False, "message": "订单完成支付时间过长，无法执行订阅操作"}
                    ),
                    400,
                )

        promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
        if promotion_user:
            has_order = check_user_has_placed_order(promotion_user.user_id)
            if not promotion_user.eligible_for_promotion and has_order:
                promotion_user.eligible_for_promotion = True
                if not promotion_user.promotion_code:
                    promotion_code = generate_stable_promotion_code(open_id)
                    promotion_user.promotion_code = promotion_code
                db.session.commit()

        subscription_templates = [
            {
                "template_id": "BOy7pDiq-pM1qiJHJfP9jUjAbi9o0bZG5-mEKZbnYT8",
                "name": "订单制作完成通知",
                "description": "当您的订单制作完成时，我们会通过此模板通知您",
                "example_data": {
                    "character_string13": {"value": order_number},
                    "thing1": {"value": order.product_name or "定制产品"},
                    "time17": {"value": "2025年12月31日 14:30"},
                },
            },
            {
                "template_id": "R7mHvK2wP8fLjSs4dJqTn1cVyRbA6eZ9uI3oM5pN0xQ",
                "name": "订单状态更新通知",
                "description": "当您的订单状态发生重要变化时，我们会通过此模板通知您",
                "example_data": {
                    "thing1": {"value": order_number},
                    "phrase2": {"value": "制作中"},
                    "time3": {"value": "2025年12月31日 14:30"},
                },
            },
        ]

        return jsonify(
            {
                "success": True,
                "message": "验证通过，可以请求订阅消息",
                "canSubscribe": True,
                "orderStatus": order.status,
                "paymentTime": order.payment_time.isoformat() if order.payment_time else None,
                "subscriptionTemplates": subscription_templates,
                "userPromotionCode": promotion_user.promotion_code if promotion_user else None,
                "eligibleForPromotion": (
                    promotion_user.eligible_for_promotion if promotion_user else False
                ),
            }
        )

    except Exception as e:
        logger.info(f"支付后订阅验证失败: {str(e)}")
        return jsonify({"success": False, "message": f"验证失败: {str(e)}"}), 500


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

        orders = []
        total_commission = 0

        for commission in commissions:
            order = Order.query.filter_by(order_number=commission.order_id).first()
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


@user_api_bp.route("/phone", methods=["POST"])
def get_user_phone():
    """解密获取用户手机号"""
    if not CRYPTO_AVAILABLE:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Crypto模块未安装，无法解密手机号。请安装: pip install pycryptodome",
                }
            ),
            500,
        )

    try:
        data = request.get_json()
        code = data.get("code")
        encrypted_data = data.get("encryptedData")
        iv = data.get("iv")

        if not all([code, encrypted_data, iv]):
            return jsonify({"success": False, "message": "缺少必要参数"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        # 优先从数据库读取配置，如果没有则使用test_server.py中的默认配置
        from app.services.payment_service import get_wechat_pay_config

        WECHAT_PAY_CONFIG = get_wechat_pay_config()

        if not WECHAT_PAY_CONFIG:
            return jsonify({"success": False, "message": "微信支付配置未初始化"}), 500

        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": WECHAT_PAY_CONFIG.get("appid", ""),
            "secret": WECHAT_PAY_CONFIG.get("app_secret", ""),
            "js_code": code,
            "grant_type": "authorization_code",
        }

        response = requests.get(url, params=params, timeout=(10, 30))

        if response.status_code == 200:
            result = response.json()
            if "session_key" in result:
                session_key = result["session_key"]

                # Base64解码
                encrypted_data_bytes = base64.b64decode(encrypted_data)
                iv_bytes = base64.b64decode(iv)
                session_key_bytes = base64.b64decode(session_key)

                # AES解密
                cipher = AES.new(session_key_bytes, AES.MODE_CBC, iv_bytes)
                decrypted_data = cipher.decrypt(encrypted_data_bytes)

                # 去除填充
                padding_length = decrypted_data[-1]
                decrypted_data = decrypted_data[:-padding_length]

                # 解析JSON
                phone_data = json.loads(decrypted_data.decode("utf-8"))
                phone_number = phone_data.get("phoneNumber")

                if phone_number:
                    return jsonify({"success": True, "phoneNumber": phone_number})
                else:
                    return jsonify({"success": False, "message": "解密失败，未获取到手机号"}), 400
            else:
                return (
                    jsonify(
                        {"success": False, "message": result.get("errmsg", "获取session_key失败")}
                    ),
                    400,
                )
        else:
            return jsonify({"success": False, "message": "微信接口调用失败"}), 500

    except Exception as e:
        logger.info(f"获取手机号失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取手机号失败: {str(e)}"}), 500


@user_api_bp.route("/subscription-status", methods=["POST"])
def update_subscription_status():
    """更新用户订阅状态 - 支付后订阅"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        open_id = data.get("openId")
        is_subscribed = data.get("isSubscribed")
        subscription_result = data.get("subscriptionResult")
        order_number = data.get("orderNumber")
        template_ids = data.get("templateIds", [])

        if not user_id and not open_id:
            return jsonify({"success": False, "message": "用户ID或OpenID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]
        Order = models["Order"]

        utils = get_utils()
        check_user_has_placed_order = utils["check_user_has_placed_order"]
        generate_stable_promotion_code = utils["generate_stable_promotion_code"]

        promotion_user = None
        if open_id:
            promotion_user = PromotionUser.query.filter_by(open_id=open_id).first()
        elif user_id:
            promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()

        if promotion_user:
            if order_number:
                order = Order.query.filter_by(order_number=order_number).first()
                if order and order.status == "pending":
                    has_order = check_user_has_placed_order(promotion_user.user_id)
                    if not promotion_user.eligible_for_promotion and has_order:
                        promotion_user.eligible_for_promotion = True
                        if not promotion_user.promotion_code:
                            promotion_code = generate_stable_promotion_code(promotion_user.open_id)
                            promotion_user.promotion_code = promotion_code
            promotion_user.update_time = datetime.now()
            db.session.commit()

        if is_subscribed:
            message = f"订阅成功！您将收到订单 {order_number} 的制作进度通知。"
            if promotion_user and promotion_user.eligible_for_promotion:
                message += f"同时恭喜您获得推广资格，推广码: {promotion_user.promotion_code}"
        else:
            message = "如需接收订单进度通知，请允许订阅消息。您也可以手动关注订单状态。"

        return jsonify(
            {
                "success": True,
                "message": message,
                "subscriptionStatus": is_subscribed,
                "orderNumber": order_number,
                "promotionCode": promotion_user.promotion_code if promotion_user else None,
                "eligibleForPromotion": (
                    promotion_user.eligible_for_promotion if promotion_user else False
                ),
            }
        )

    except Exception as e:
        logger.info(f"更新订阅状态失败: {str(e)}")
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"更新订阅状态失败: {str(e)}"}), 500


@user_api_bp.route("/update-phone", methods=["POST"])
def update_user_phone():
    """更新用户手机号"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        phone_number = data.get("phoneNumber")

        if not user_id or not phone_number:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        PromotionUser = models["PromotionUser"]

        promotion_user = PromotionUser.query.filter_by(user_id=user_id).first()
        if promotion_user:
            promotion_user.phone_number = phone_number
            db.session.commit()

            return jsonify({"success": True, "message": "手机号更新成功"})
        else:
            return jsonify({"success": False, "message": "用户不存在"}), 404

    except Exception as e:
        logger.info(f"更新手机号失败: {str(e)}")
        return jsonify({"success": False, "message": f"更新手机号失败: {str(e)}"}), 500


@user_api_bp.route("/visit", methods=["POST", "OPTIONS"])
def record_user_visit():
    """记录用户访问（支持完整访问追踪）- 优化版本：快速响应，避免超时"""
    # 处理 OPTIONS 预检请求
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        # CORS头由after_request统一处理，这里不需要重复设置
        return response

    # 先快速返回响应，避免小程序超时
    response_data = {
        "success": True,
        "message": "用户访问记录成功",
        "visitId": None,
        "promotionCode": None,
        "isNewUser": False,
    }

    try:
        # 添加调试日志
        logger.info(f"📥 [用户访问记录] 收到请求: {request.method} {request.path}")
        logger.info(f"📥 [用户访问记录] Content-Type: {request.content_type}")
        logger.info(f"📥 [用户访问记录] Content-Length: {request.content_length}")

        # 安全地获取JSON数据，避免JSONDecodeError
        try:
            data = request.get_json(force=True, silent=True) or {}
        except Exception as json_error:
            logger.warning("[用户访问记录] JSON解析失败: {json_error}")
            # 尝试从原始数据获取
            try:
                raw_data = request.get_data(as_text=True)
                logger.info(f"📥 [用户访问记录] 原始数据: {raw_data[:200]}")
                if raw_data:
                    import json

                    data = json.loads(raw_data)
                else:
                    data = {}
            except Exception:
                data = {}

        session_id = data.get("sessionId") or data.get("session_id")
        openid = data.get("openId") or data.get("openid")
        user_id = data.get("userId") or data.get("user_id")
        visit_type = data.get("visitType") or data.get("type", "launch")
        promotion_code = data.get("promotionCode") or data.get("promotion_code")
        referrer_user_id = data.get("referrerUserId") or data.get("referrer_user_id")
        scene = data.get("scene")
        user_info = data.get("userInfo") or data.get("user_info") or {}
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")

        logger.info(
            f"📥 [用户访问记录] 数据: sessionId={session_id}, type={visit_type}, userId={user_id}"
        )

        if not session_id:
            logger.warning("[用户访问记录] 缺少sessionId")
            return jsonify({"success": False, "message": "会话ID不能为空"}), 400

        models = get_models()
        if not models:
            logger.warning("[用户访问记录] 系统未初始化，返回默认响应")
            # 即使系统未初始化，也返回成功，避免阻塞小程序
            return jsonify(response_data)

        # ⚡ 优化：先快速返回响应，避免超时
        # 数据库操作在后台异步处理，不阻塞响应
        logger.info("✅ [用户访问记录] 准备快速返回响应")

        # 使用线程异步处理数据库操作
        import threading

        from flask import current_app

        def save_visit_async():
            # 在异步线程中需要创建应用上下文
            try:
                # 获取应用实例
                if "test_server" in sys.modules:
                    test_server_module = sys.modules["test_server"]
                    app_instance = test_server_module.app
                else:
                    logger.warning("[用户访问记录] 异步保存：无法获取应用实例")
                    return

                # 在应用上下文中执行数据库操作
                with app_instance.app_context():
                    # 重新获取models，确保线程安全
                    async_models = get_models()
                    if not async_models:
                        logger.warning("[用户访问记录] 异步保存：系统未初始化")
                        return

                    db = async_models["db"]
                    UserVisit = async_models.get("UserVisit")

                    if UserVisit:
                        # 使用 ORM 快速插入
                        new_visit = UserVisit(
                            session_id=session_id,
                            openid=openid if openid and openid != "anonymous" else None,
                            user_id=user_id if user_id and user_id != "anonymous" else None,
                            visit_type=visit_type,
                            source="miniprogram",
                            scene=scene,
                            user_info=json.dumps(user_info) if user_info else None,
                            is_authorized=bool(openid and openid != "anonymous"),
                            is_registered=bool(user_id and user_id != "anonymous"),
                            has_ordered=(visit_type == "order"),
                            ip_address=ip_address,
                            user_agent=user_agent,
                            promotion_code=promotion_code,
                            referrer_user_id=referrer_user_id,
                        )
                        db.session.add(new_visit)
                        db.session.commit()
                        logger.info(f"✅ [用户访问记录] 异步保存成功: visitId={new_visit.id}")
                    else:
                        # 使用原始 SQL（如果模型不存在）
                        result = db.session.execute(
                            db.text("""
                                INSERT INTO user_visits
                                (session_id, openid, user_id, promotion_code, referrer_user_id,
                                 visit_time, visit_type, source, scene, user_info, is_authorized,
                                 is_registered, has_ordered, ip_address, user_agent)
                                VALUES (:session_id, :openid, :user_id, :promotion_code, :referrer_user_id,
                                        CURRENT_TIMESTAMP, :visit_type, :source, :scene, :user_info, :is_authorized,
                                        :is_registered, :has_ordered, :ip_address, :user_agent)
                            """),
                            {
                                "session_id": session_id,
                                "openid": openid if openid and openid != "anonymous" else None,
                                "user_id": user_id if user_id and user_id != "anonymous" else None,
                                "promotion_code": promotion_code,
                                "referrer_user_id": referrer_user_id,
                                "visit_type": visit_type,
                                "source": "miniprogram",
                                "scene": scene,
                                "user_info": json.dumps(user_info) if user_info else None,
                                "is_authorized": bool(openid and openid != "anonymous"),
                                "is_registered": bool(user_id and user_id != "anonymous"),
                                "has_ordered": (visit_type == "order"),
                                "ip_address": ip_address,
                                "user_agent": user_agent,
                            },
                        )
                        db.session.commit()
                        logger.info("✅ [用户访问记录] 异步保存成功（SQL方式）")
            except Exception as e:
                # 如果是重复记录错误，忽略
                if "UNIQUE" not in str(e) and "duplicate" not in str(e).lower():
                    logger.warning("[用户访问记录] 异步保存失败: {e}")
                    import traceback

                    traceback.print_exc()

        # 启动异步保存线程
        thread = threading.Thread(target=save_visit_async, daemon=True)
        thread.start()

        # 立即返回响应，不等待数据库操作完成
        logger.info("✅ [用户访问记录] 快速返回响应")
        response = jsonify(response_data)
        # 确保响应头正确设置（使用set避免重复，让after_request处理CORS）
        # Content-Type由jsonify自动设置，这里只确保CORS头
        # 注意：不要在这里设置CORS头，让after_request统一处理，避免重复
        logger.info(f"✅ [用户访问记录] 响应已准备: {response_data}")
        return response

    except Exception as e:
        logger.error("[用户访问记录] 异常: {e}")
        import traceback

        traceback.print_exc()
        # 即使异常也返回成功，避免阻塞小程序
        logger.warning("[用户访问记录] 返回默认成功响应")
        response = jsonify(response_data)
        # CORS头由after_request统一处理，这里不需要重复设置
        return response


@user_api_bp.route("/visit/stats", methods=["GET"])
def get_user_visit_stats():
    """获取用户访问统计"""
    try:
        from sqlalchemy import func

        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        UserVisit = models["UserVisit"]
        db = models["db"]

        query = UserVisit.query

        if start_date:
            query = query.filter(UserVisit.visit_time >= start_date)
        if end_date:
            query = query.filter(UserVisit.visit_time <= end_date)

        total_visits = query.count()
        authorized_visits = query.filter(UserVisit.is_authorized is True).count()
        registered_visits = query.filter(UserVisit.is_registered is True).count()
        ordered_visits = query.filter(UserVisit.has_ordered is True).count()

        daily_stats = (
            db.session.query(
                func.date(UserVisit.visit_time).label("date"),
                func.count(UserVisit.id).label("total"),
                func.count(func.case([(UserVisit.is_authorized is True, 1)])).label("authorized"),
                func.count(func.case([(UserVisit.is_registered is True, 1)])).label("registered"),
                func.count(func.case([(UserVisit.has_ordered is True, 1)])).label("ordered"),
            )
            .group_by(func.date(UserVisit.visit_time))
            .order_by("date")
            .all()
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "totalVisits": total_visits,
                    "authorizedVisits": authorized_visits,
                    "registeredVisits": registered_visits,
                    "orderedVisits": ordered_visits,
                    "dailyStats": [
                        {
                            "date": str(stat.date),
                            "total": stat.total,
                            "authorized": stat.authorized,
                            "registered": stat.registered,
                            "ordered": stat.ordered,
                        }
                        for stat in daily_stats
                    ],
                },
            }
        )

    except Exception as e:
        logger.error("获取用户访问统计失败: {e}")
        return jsonify({"success": False, "message": f"获取用户访问统计失败: {str(e)}"}), 500


@user_api_bp.route("/messages/unread-count", methods=["GET"])
def get_unread_message_count():
    """获取用户未读消息数量"""
    try:
        user_id = request.args.get("userId")
        session_id = request.args.get("sessionId")

        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]

        result = db.session.execute(
            db.text("""
                SELECT COUNT(*) FROM user_messages
                WHERE (user_id = :user_id OR session_id = :session_id)
                AND is_read = 0
            """),
            {"user_id": user_id, "session_id": session_id},
        )

        count = result.fetchone()[0]

        return jsonify({"success": True, "unreadCount": count})

    except Exception as e:
        logger.error("获取未读消息数量失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_api_bp.route("/messages", methods=["GET"])
def get_user_messages():
    """获取用户消息列表"""
    try:
        user_id = request.args.get("userId")
        session_id = request.args.get("sessionId")

        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]

        result = db.session.execute(
            db.text("""
                SELECT
                    id,
                    title,
                    content,
                    message_type,
                    action,
                    url,
                    is_read,
                    created_at
                FROM user_messages
                WHERE user_id = :user_id OR session_id = :session_id
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"user_id": user_id, "session_id": session_id},
        )

        messages = []
        for row in result.fetchall():
            messages.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "type": row[3],
                    "action": row[4],
                    "url": row[5],
                    "isRead": bool(row[6]),
                    "time": row[7],
                }
            )

        return jsonify({"success": True, "messages": messages})

    except Exception as e:
        logger.error("获取消息列表失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_api_bp.route("/messages/check", methods=["GET"])
def check_user_messages():
    """检查用户是否有新消息"""
    try:
        user_id = request.args.get("userId")
        session_id = request.args.get("sessionId")

        if not user_id and not session_id:
            return (
                jsonify(
                    {"success": False, "hasNewMessage": False, "message": "用户ID或会话ID不能为空"}
                ),
                400,
            )

        models = get_models()
        if not models:
            return (
                jsonify({"success": False, "hasNewMessage": False, "message": "系统未初始化"}),
                500,
            )

        db = models["db"]

        # 查询是否有未读消息
        result = db.session.execute(
            db.text("""
                SELECT
                    id,
                    title,
                    content,
                    message_type,
                    action,
                    url
                FROM user_messages
                WHERE (user_id = :user_id OR session_id = :session_id)
                AND is_read = 0
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"user_id": user_id, "session_id": session_id},
        )

        row = result.fetchone()

        if row:
            return jsonify(
                {
                    "success": True,
                    "hasNewMessage": True,
                    "message": {
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "type": row[3],
                        "action": row[4],
                        "url": row[5],
                    },
                }
            )
        else:
            return jsonify({"success": True, "hasNewMessage": False})

    except Exception as e:
        logger.error("检查消息失败: {e}")
        return jsonify({"success": False, "hasNewMessage": False, "message": str(e)}), 500


@user_api_bp.route("/messages/read", methods=["POST"])
def mark_messages_as_read():
    """标记消息为已读"""
    try:
        data = request.get_json()
        user_id = data.get("userId")
        session_id = data.get("sessionId")

        if not user_id and not session_id:
            return jsonify({"success": False, "message": "用户ID或会话ID不能为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]

        result = db.session.execute(
            db.text("""
                UPDATE user_messages
                SET is_read = 1, read_at = CURRENT_TIMESTAMP
                WHERE (user_id = :user_id OR session_id = :session_id)
                AND is_read = 0
            """),
            {"user_id": user_id, "session_id": session_id},
        )

        db.session.commit()

        return jsonify(
            {"success": True, "message": "消息已标记为已读", "updatedCount": result.rowcount}
        )

    except Exception as e:
        logger.error("标记消息为已读失败: {e}")
        models = get_models()
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


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

        available_count = 0
        for coupon in available_coupons:
            # 检查用户是否已经领取过
            user_coupon_count = UserCoupon.query.filter_by(
                user_id=user_id, coupon_id=coupon.id
            ).count()

            # 检查是否达到每用户限领数量
            if user_coupon_count < coupon.per_user_limit:
                # 计算剩余数量
                claimed_count = UserCoupon.query.filter_by(coupon_id=coupon.id).count()
                remaining_count = max(0, (coupon.total_count or 0) - claimed_count)

                # 如果还有剩余数量，则计入可领取数量
                if remaining_count > 0:
                    available_count += 1

        return jsonify({"success": True, "availableCount": available_count})

    except Exception as e:
        logger.error("获取可用优惠券数量失败: {str(e)}")
        # 即使出错也返回0，避免前端报错
        return jsonify({"success": True, "availableCount": 0})
