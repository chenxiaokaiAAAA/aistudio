# -*- coding: utf-8 -*-
"""
用户信息管理相关API路由
包含：更新用户信息、获取/更新手机号
"""

import logging

logger = logging.getLogger(__name__)
import base64
import sys
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

# 导入主蓝图
from . import user_api_bp


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

        # 使用小程序登录配置（appid+app_secret），不依赖支付配置
        from app.services.payment_service import get_miniprogram_login_config

        login_config = get_miniprogram_login_config()

        if not login_config or not login_config.get("appid") or not login_config.get("app_secret"):
            return jsonify({"success": False, "message": "小程序AppID或AppSecret未配置，请在管理后台「小程序配置」中填写"}), 500

        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": login_config.get("appid", ""),
            "secret": login_config.get("app_secret", ""),
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
                import json

                phone_data = json.loads(decrypted_data.decode("utf-8"))
                phone_number = phone_data.get("phoneNumber", "")

                return jsonify({"success": True, "phoneNumber": phone_number})
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f'获取session_key失败: {result.get("errmsg", "未知错误")}',
                        }
                    ),
                    400,
                )
        else:
            return (
                jsonify({"success": False, "message": f"请求微信API失败: {response.status_code}"}),
                500,
            )

    except Exception as e:
        logger.info(f"解密手机号失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"解密手机号失败: {str(e)}"}), 500


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
