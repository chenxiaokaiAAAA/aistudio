# -*- coding: utf-8 -*-
"""
AI配置管理API路由模块
提供AI配置的获取和更新功能
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models

# 创建蓝图
ai_config_api_bp = Blueprint("ai_config_api", __name__)


@ai_config_api_bp.route("/api/config", methods=["GET"])
@login_required
def get_ai_config():
    """获取AI配置"""
    try:
        models = get_models(["AIConfig"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        AIConfig = models["AIConfig"]

        configs = AIConfig.query.all()
        config_data = {}
        for config in configs:
            config_data[config.config_key] = {
                "value": config.config_value,
                "description": config.description,
            }

        return jsonify({"status": "success", "data": config_data})

    except Exception as e:
        logger.info(f"获取AI配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取配置失败: {str(e)}"}), 500


@ai_config_api_bp.route("/api/config", methods=["PUT"])
@login_required
def update_ai_config():
    """更新AI配置"""
    try:
        if current_user.role != "admin":
            return jsonify({"status": "error", "message": "权限不足"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求数据为空"}), 400

        models = get_models(["AIConfig", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        AIConfig = models["AIConfig"]

        updated_configs = []
        for config_key, config_value in data.items():
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = str(config_value)
                config.updated_at = datetime.now()
                updated_configs.append(config_key)
            else:
                # 创建新配置
                new_config = AIConfig(
                    config_key=config_key, config_value=str(config_value), description=""
                )
                db.session.add(new_config)
                updated_configs.append(config_key)

        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": "配置更新成功",
                "data": {"updated_keys": updated_configs},
            }
        )

    except Exception as e:
        logger.info(f"更新AI配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"更新配置失败: {str(e)}"}), 500
