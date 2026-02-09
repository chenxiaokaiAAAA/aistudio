# -*- coding: utf-8 -*-
"""
用户认证相关API路由模块
提供用户检查、注册、OpenID获取等功能
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

from app.utils.admin_helpers import get_models

# 创建蓝图
user_auth_api_bp = Blueprint("user_auth_api", __name__)

# 尝试导入 Crypto（可选）
try:
    from Crypto.Cipher import AES

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("Crypto模块未安装，手机号解密功能将不可用。请安装: pip install pycryptodome")


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


@user_auth_api_bp.route("/check", methods=["POST"])
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

        models = get_models(["PromotionUser", "db"])
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


@user_auth_api_bp.route("/openid", methods=["POST"])
def get_user_openid():
    """获取用户openid接口"""
    # ========== 开发模式：跳过真实openid验证 ==========
    DEV_MODE_SKIP_OPENID = True  # ⚠️ 上线前改为 False
    # ========== 开发模式结束 ==========

    try:
        data = request.get_json()
        code = data.get("code")

        models = get_models(["get_user_openid_service"])
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


@user_auth_api_bp.route("/register", methods=["POST"])
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

        models = get_models(["PromotionUser", "PromotionTrack", "Order", "db"])
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
        models = get_models(["db"])
        if models:
            models["db"].session.rollback()
        return jsonify({"success": False, "message": f"用户注册失败: {str(e)}"}), 500
