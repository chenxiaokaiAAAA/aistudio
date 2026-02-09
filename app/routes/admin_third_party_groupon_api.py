# -*- coding: utf-8 -*-
"""
第三方团购核销API路由模块
"""

import logging

logger = logging.getLogger(__name__)
import json
import random
import string
import sys
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_third_party_groupon_api_bp = Blueprint(
    "admin_third_party_groupon_api", __name__, url_prefix="/api/admin/third-party-groupon"
)


def generate_random_code(length=8):
    """生成随机码"""
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))


@admin_third_party_groupon_api_bp.route("/config", methods=["GET"])
@login_required
def get_third_party_config():
    """获取第三方团购API配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库模型未初始化"}), 500

        AIConfig = models["AIConfig"]

        config = AIConfig.query.filter_by(config_key="third_party_groupon_api").first()

        if config and config.config_value:
            try:
                config_data = json.loads(config.config_value)
                return jsonify({"success": True, "data": config_data})
            except Exception:
                pass

        return jsonify({"success": True, "data": None})

    except Exception as e:
        logger.info(f"获取配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取配置失败: {str(e)}"}), 500


@admin_third_party_groupon_api_bp.route("/config", methods=["POST"])
@login_required
def save_third_party_config():
    """保存第三方团购API配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库模型未初始化"}), 500

        AIConfig = models["AIConfig"]
        db = models["db"]

        data = request.get_json()

        # 验证必填字段
        if not data.get("platform") or not data.get("api_base_url"):
            return jsonify({"success": False, "message": "请填写平台和API基础地址"}), 400

        # 保存配置到AIConfig表
        config = AIConfig.query.filter_by(config_key="third_party_groupon_api").first()

        config_data = {
            "platform": data.get("platform"),
            "api_base_url": data.get("api_base_url"),
            "verify_endpoint": data.get("verify_endpoint", "/api/v1/verify"),
            "redeem_endpoint": data.get("redeem_endpoint", "/api/v1/redeem"),
            "query_endpoint": data.get("query_endpoint", "/api/v1/query"),
            "api_key": data.get("api_key", ""),
            "api_secret": data.get("api_secret", ""),
            "status": data.get("status", "active"),
            "notes": data.get("notes", ""),
            "updated_at": datetime.now().isoformat(),
        }

        if config:
            config.config_value = json.dumps(config_data, ensure_ascii=False)
            config.description = f'第三方团购API配置 - {data.get("platform")}'
        else:
            config = AIConfig(
                config_key="third_party_groupon_api",
                config_value=json.dumps(config_data, ensure_ascii=False),
                description=f'第三方团购API配置 - {data.get("platform")}',
            )
            db.session.add(config)

        db.session.commit()

        return jsonify({"success": True, "message": "配置保存成功"})

    except Exception as e:
        logger.info(f"保存配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"success": False, "message": f"保存配置失败: {str(e)}"}), 500


@admin_third_party_groupon_api_bp.route("/test", methods=["POST"])
@login_required
def test_third_party_api():
    """测试第三方API连接"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        data = request.get_json()
        api_base_url = data.get("api_base_url")

        if not api_base_url:
            return jsonify({"success": False, "message": "请提供API基础地址"}), 400

        # 简单的连接测试（发送HEAD请求）
        try:
            response = requests.head(api_base_url, timeout=5)
            return jsonify({"success": True, "message": "API连接测试成功"})
        except requests.exceptions.RequestException as e:
            return jsonify({"success": False, "message": f"API连接失败: {str(e)}"}), 400

    except Exception as e:
        logger.info(f"测试API失败: {str(e)}")
        return jsonify({"success": False, "message": f"测试失败: {str(e)}"}), 500
