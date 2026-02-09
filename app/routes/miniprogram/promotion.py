# -*- coding: utf-8 -*-
"""
小程序推广码路由
"""

import logging

logger = logging.getLogger(__name__)
import base64
import hashlib

import requests
from flask import Blueprint, jsonify, request

from app.routes.miniprogram.common import get_helper_functions

# 创建推广码相关的子蓝图
bp = Blueprint("promotion", __name__)


@bp.route("/promotion-code", methods=["GET"])
def miniprogram_get_promotion_code():
    """小程序获取用户推广码 - 使用微信API生成小程序码"""
    try:
        helpers = get_helper_functions()
        if not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        get_access_token = helpers.get("get_access_token")

        phone = request.args.get("phone")
        if not phone:
            return jsonify({"status": "error", "message": "缺少手机号参数"}), 400

        # 生成推广码（基于手机号）
        promotion_code = hashlib.md5(phone.encode()).hexdigest()[:8].upper()

        # 生成用户ID（基于手机号）
        user_id = f"USER{hashlib.md5(phone.encode()).hexdigest()[:10].upper()}"

        # 获取access_token
        if not get_access_token:
            return jsonify({"status": "error", "message": "获取access_token函数不可用"}), 500

        access_token = get_access_token()
        if not access_token:
            return jsonify({"status": "error", "message": "获取access_token失败"}), 500

        # 使用微信API生成小程序码
        url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}"
        scene = f"p={promotion_code}&u={user_id}"

        params = {
            "scene": scene,
            "page": "pages/index/index",
            "env_version": "release",  # 指向正式版
            "width": 300,
            "auto_color": False,
            "line_color": {"r": 0, "g": 0, "b": 0},
        }

        logger.info(
            f"生成推广码小程序码: promotionCode={promotion_code}, userId={user_id}, env_version=release"
        )

        response = requests.post(url, json=params, timeout=(10, 30))

        if response.status_code == 200:
            # 检查响应内容类型
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                # 如果返回JSON，说明有错误
                error_data = response.json()
                logger.info(f"微信API返回错误: {error_data}")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f'生成小程序码失败: {error_data.get("errmsg", "未知错误")}',
                        }
                    ),
                    500,
                )

            # 转换为base64
            qr_base64 = base64.b64encode(response.content).decode("utf-8")

            # ⭐ 推广码功能保留，后续将改为分享作品获得优惠券的逻辑
            return jsonify(
                {
                    "status": "success",
                    "data": {
                        "promotionCode": promotion_code,
                        "qrCode": f"data:image/png;base64,{qr_base64}",
                        "qrUrl": f"https://servicewechat.com/wx01e841dfc50052a9/0/page-frame.html?promotion={promotion_code}",
                        "promotionInstructions": [
                            "分享您的作品给朋友",
                            "朋友通过您的推广码进入小程序",
                            "朋友成功下单后，您将获得优惠券",
                            "推广码长期有效，可分享给多个朋友",
                        ],
                    },
                }
            )
        else:
            logger.info(f"微信API调用失败: HTTP {response.status_code}")
            return (
                jsonify(
                    {"status": "error", "message": f"生成小程序码失败: HTTP {response.status_code}"}
                ),
                500,
            )

    except Exception as e:
        logger.info(f"获取推广码失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取推广码失败: {str(e)}"}), 500
