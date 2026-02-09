# -*- coding: utf-8 -*-
"""
选片页面 - 二维码相关功能
包含：生成选片登录二维码、验证token
"""

import logging

logger = logging.getLogger(__name__)
import base64
import uuid
from datetime import datetime, timedelta
from io import BytesIO

import qrcode
from flask import Blueprint, jsonify, request, session
from flask_login import current_user

from app.utils.admin_helpers import get_models

from .utils import (
    create_selection_token,
    create_short_token,
    mark_token_as_used,
    verify_selection_token,
)

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_qrcode", __name__)


@bp.route("/admin/photo-selection/generate-qrcode", methods=["POST"])
def generate_selection_qrcode():
    """生成选片登录二维码"""
    try:
        # 检查用户权限：加盟商或管理员
        session_franchisee_id = session.get("franchisee_id")

        if not session_franchisee_id and (
            not current_user.is_authenticated or current_user.role not in ["admin", "operator"]
        ):
            return jsonify({"success": False, "message": "权限不足"}), 403

        # 获取加盟商ID（如果是加盟商登录，使用session中的ID；如果是管理员，从请求参数获取）
        data = request.get_json() or {}
        franchisee_id = session_franchisee_id or data.get("franchisee_id")

        if not franchisee_id:
            return jsonify({"success": False, "message": "缺少加盟商ID"}), 400

        # 生成临时token（有效期5分钟）
        token, expires_at = create_selection_token(franchisee_id, expires_minutes=5)

        # 使用微信小程序码API生成小程序码（推荐方式）
        # 获取微信access_token
        from app.routes.qrcode_api import get_access_token

        access_token = get_access_token()

        if access_token:
            try:
                # 使用微信小程序码API
                import requests

                url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}"

                # 构建参数：scene参数使用短格式（微信限制32字符）
                short_token = create_short_token(token)
                scene = f"st={short_token}"  # st=selection_token的缩写

                # 验证长度
                if len(scene) > 32:
                    # 如果还是太长，进一步缩短
                    short_token = token.replace("-", "")[:12]
                    scene = f"st={short_token}"

                logger.info(
                    f"调用微信小程序码API生成二维码，scene: {scene} (长度: {len(scene)}字符)"
                )
                logger.info(f"完整token: {token} (将映射到短token: {short_token})")

                # 尝试不同的环境版本和页面路径
                attempts = [
                    {"page": "pages/orders/orders", "env_version": "trial"},  # 体验版
                    {"page": "pages/index/index", "env_version": "trial"},  # 体验版首页
                    {"page": "pages/orders/orders", "env_version": "release"},  # 正式版
                    {"page": "pages/index/index", "env_version": "release"},  # 正式版首页
                ]

                response = None
                last_error = None
                success = False

                for attempt in attempts:
                    params = {
                        "scene": scene,
                        "page": attempt["page"],
                        "env_version": attempt["env_version"],
                        "width": 300,
                        "auto_color": False,
                        "line_color": {"r": 0, "g": 0, "b": 0},
                    }

                    logger.info(
                        f"尝试生成小程序码: page={attempt['page']}, env_version={attempt['env_version']}, scene={params['scene']}"
                    )
                    try:
                        response = requests.post(url, json=params, timeout=(10, 30))

                        if response.status_code == 200:
                            content_type = response.headers.get("content-type", "")

                            if "application/json" in content_type:
                                # 如果返回JSON，说明有错误
                                error_data = response.json()
                                logger.warning(f"尝试失败: {error_data.get('errmsg', '未知错误')}")
                                last_error = error_data.get("errmsg", "未知错误")
                                continue  # 尝试下一个配置
                            else:
                                # 成功生成图片
                                logger.info(
                                    f"✅ 使用配置成功生成: page={attempt['page']}, env_version={attempt['env_version']}"
                                )
                                success = True
                                break  # 成功，退出循环
                    except Exception as e:
                        logger.warning(f"请求异常: {str(e)}")
                        last_error = str(e)
                        continue

                if not success:
                    # 所有尝试都失败，抛出异常
                    raise Exception(f'生成小程序码失败: {last_error or "所有配置尝试均失败"}')

                # 如果成功，response已经在循环中设置
                # 转换为base64
                img_base64 = base64.b64encode(response.content).decode("utf-8")
                logger.info("✅ 使用微信小程序码API生成成功")
                qrcode_content = f"pages/orders/orders?selection_token={token}"

            except Exception as e:
                logger.warning(f"使用微信小程序码API失败，回退到普通二维码: {e}")
                # 回退到普通二维码
                # 构建小程序页面路径（用于普通二维码）
                qrcode_content = f"pages/orders/orders?selection_token={token}"

                # 生成二维码图片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qrcode_content)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                # 转换为base64
                img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        else:
            # 如果没有access_token，使用普通二维码
            logger.warning("无法获取access_token，使用普通二维码")
            qrcode_content = f"pages/orders/orders?selection_token={token}"

            # 生成二维码图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qrcode_content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # 转换为base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify(
            {
                "success": True,
                "token": token,
                "qrcode": f"data:image/png;base64,{img_base64}",
                "expires_at": expires_at.isoformat(),
                "qrcode_content": qrcode_content,
            }
        )

    except Exception as e:
        logger.info(f"生成选片二维码失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"生成二维码失败: {str(e)}"}), 500


@bp.route("/api/photo-selection/verify-token", methods=["POST"])
def verify_selection_token_api():
    """验证选片登录token"""
    try:
        data = request.get_json()
        token = data.get("token")
        openid = data.get("openid")  # 小程序用户的openid

        if not token:
            return jsonify({"success": False, "message": "缺少token"}), 400

        # 严格检查openid，不允许匿名用户
        if not openid or openid == "anonymous" or len(openid) < 10:
            return jsonify({"success": False, "message": "请先登录"}), 401

        # 检查token是否存在且未过期
        token_info, error_msg = verify_selection_token(token)
        if not token_info:
            return jsonify({"success": False, "message": error_msg}), 400

        # 获取加盟商ID
        franchisee_id = token_info["franchisee_id"]

        # 获取该加盟商的所有订单（通过openid匹配）
        models = get_models(["Order"])
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        Order = models["Order"]

        # 查询该用户的订单（通过openid匹配，且属于该加盟商）
        orders = (
            Order.query.filter(
                Order.openid == openid,
                Order.franchisee_id == franchisee_id,
                Order.status != "unpaid",
            )
            .order_by(Order.created_at.desc())
            .all()
        )

        # 标记token为已使用
        mark_token_as_used(token, openid)

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
                "message": "验证成功",
            }
        )

    except Exception as e:
        logger.info(f"验证选片token失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"验证失败: {str(e)}"}), 500
