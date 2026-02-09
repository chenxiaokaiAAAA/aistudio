# -*- coding: utf-8 -*-
"""
调试和测试API路由模块
用于开发和调试阶段的测试接口
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
debug_api_bp = Blueprint("debug_api", __name__, url_prefix="/api")


def get_server_config():
    """获取服务器配置函数"""
    try:
        test_server = sys.modules.get("test_server")
        if test_server and hasattr(test_server, "get_static_url"):
            return {"get_static_url": test_server.get_static_url}

        # 如果不可用，使用默认值
        def default_get_static_url():
            return "http://127.0.0.1:8000/static"

        return {"get_static_url": default_get_static_url}
    except Exception as e:
        logger.warning("获取服务器配置失败: {e}")

        def default_get_static_url():
            return "http://127.0.0.1:8000/static"

        return {"get_static_url": default_get_static_url}


# ==================== 支付调试接口 ====================


@debug_api_bp.route("/debug/payment", methods=["POST"])
def debug_payment():
    """调试支付接口 - 记录所有请求参数"""
    try:
        data = request.get_json()
        logger.info("🔍 收到支付请求:")
        logger.info(f"  原始数据: {data}")
        logger.info(f"  请求头: {dict(request.headers)}")
        logger.info(f"  请求方法: {request.method}")
        logger.info(f"  请求路径: {request.path}")

        return jsonify({"success": True, "message": "调试信息已记录", "received_data": data})
    except Exception as e:
        logger.error("调试接口错误: {str(e)}")
        return jsonify({"success": False, "message": f"调试接口错误: {str(e)}"}), 500


# ==================== 优惠券调试接口 ====================


@debug_api_bp.route("/coupons/test", methods=["GET"])
def test_coupons():
    """测试优惠券接口 - 返回固定数据"""
    try:
        logger.info("🔍 收到优惠券测试请求")

        # 返回测试数据
        test_coupons = [
            {
                "id": 1,
                "name": "新用户专享券",
                "code": "NEWUSER001",
                "type": "cash",
                "value": 49.0,
                "min_amount": 0.0,
                "description": "新用户专享，无门槛使用",
                "end_time": "2025-12-31T23:59:59",
                "can_claim": True,
                "remaining_count": 100,
                "per_user_limit": 1,
                "user_claimed_count": 0,
            },
            {
                "id": 2,
                "name": "限时优惠券",
                "code": "LIMITED001",
                "type": "cash",
                "value": 29.0,
                "min_amount": 100.0,
                "description": "满100元可用",
                "end_time": "2025-11-30T23:59:59",
                "can_claim": True,
                "remaining_count": 50,
                "per_user_limit": 2,
                "user_claimed_count": 0,
            },
        ]

        return jsonify(
            {
                "success": True,
                "data": test_coupons,
                "total": len(test_coupons),
                "message": "测试数据",
            }
        )

    except Exception as e:
        logger.error("测试接口错误: {str(e)}")
        return jsonify({"success": False, "message": f"测试接口错误: {str(e)}"}), 500


@debug_api_bp.route("/coupons/debug", methods=["GET"])
def debug_coupons():
    """调试优惠券接口 - 记录所有请求信息"""
    try:
        user_id = request.args.get("userId")
        logger.info("🔍 收到优惠券调试请求:")
        logger.info(f"  用户ID: {user_id}")
        logger.info(f"  请求头: {dict(request.headers)}")
        logger.info(f"  请求参数: {request.args}")
        logger.info(f"  请求方法: {request.method}")
        logger.info(f"  请求路径: {request.path}")

        # 返回调试信息
        return jsonify(
            {
                "success": True,
                "message": "调试信息已记录",
                "debug_info": {
                    "user_id": user_id,
                    "request_args": dict(request.args),
                    "request_headers": dict(request.headers),
                    "request_method": request.method,
                    "request_path": request.path,
                    "timestamp": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error("调试接口错误: {str(e)}")
        return jsonify({"success": False, "message": f"调试接口错误: {str(e)}"}), 500


# ==================== 示例图片接口 ====================


@debug_api_bp.route("/example-images", methods=["GET"])
def get_example_images():
    """获取示例图片"""
    try:
        config = get_server_config()
        get_static_url = config["get_static_url"]

        # 从 static/images/works 目录获取示例图片
        example_images = [
            {"url": f"{get_static_url()}/images/works/example1.jpg", "label": "全身正面示例"},
            {"url": f"{get_static_url()}/images/works/example2.jpg", "label": "半身示例"},
            {"url": f"{get_static_url()}/images/works/example3.jpg", "label": "头像示例"},
        ]

        return jsonify({"success": True, "data": example_images, "total": len(example_images)})

    except Exception as e:
        logger.error("获取示例图片错误: {str(e)}")
        return jsonify({"success": False, "message": f"获取示例图片失败: {str(e)}"}), 500
