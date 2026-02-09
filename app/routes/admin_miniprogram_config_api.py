# -*- coding: utf-8 -*-
"""
管理后台小程序配置API路由模块
"""

import logging

logger = logging.getLogger(__name__)
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_miniprogram_config_api_bp = Blueprint(
    "admin_miniprogram_config_api", __name__, url_prefix="/api/admin/miniprogram-config"
)


@admin_miniprogram_config_api_bp.route("", methods=["GET"])
@login_required
def get_miniprogram_config():
    """获取小程序配置（优先从数据库读取，如果数据库没有则使用test_server.py中的默认配置）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        AIConfig = models["AIConfig"]

        # 先尝试从test_server.py获取默认配置
        default_config = {}
        try:
            test_server = sys.modules.get("test_server")
            if test_server and hasattr(test_server, "WECHAT_PAY_CONFIG"):
                wechat_pay_config = test_server.WECHAT_PAY_CONFIG
                default_config = {
                    "appid": wechat_pay_config.get("appid", ""),
                    "app_secret": wechat_pay_config.get("app_secret", ""),
                    "pay_appid": wechat_pay_config.get(
                        "appid", ""
                    ),  # 支付AppID通常与小程序AppID相同
                    "pay_mch_id": wechat_pay_config.get("mch_id", ""),
                    "pay_api_key": wechat_pay_config.get("api_key", ""),
                    "pay_notify_url": wechat_pay_config.get(
                        "notify_url", "https://photogooo/api/payment/notify"
                    ),
                }
        except Exception as e:
            logger.warning("读取test_server.py默认配置失败: {str(e)}")

        # 从数据库获取配置（config_key -> 前端字段名 的映射）
        config_key_to_field = {
            "miniprogram_appid": "appid",
            "miniprogram_app_secret": "app_secret",
            "wechat_pay_appid": "pay_appid",
            "wechat_pay_mch_id": "pay_mch_id",
            "wechat_pay_api_key": "pay_api_key",
            "wechat_pay_notify_url": "pay_notify_url",
        }
        configs = {}
        ai_configs = AIConfig.query.filter(
            AIConfig.config_key.in_(list(config_key_to_field.keys()))
        ).all()

        for config in ai_configs:
            field_name = config_key_to_field.get(config.config_key)
            if field_name and config.config_value is not None:
                configs[field_name] = config.config_value

        # 合并配置：数据库配置优先（只要数据库有该键就用数据库值，包括空字符串）
        result = {}
        for key in [
            "appid",
            "app_secret",
            "pay_appid",
            "pay_mch_id",
            "pay_api_key",
            "pay_notify_url",
        ]:
            if key in configs:
                result[key] = configs[key] if configs[key] is not None else ""
            elif key in default_config:
                result[key] = default_config[key] or ""
            else:
                result[key] = ""

        # 如果pay_appid为空，使用appid的值
        if not result.get("pay_appid") and result.get("appid"):
            result["pay_appid"] = result["appid"]

        # 修复：当 appid 或 pay_mch_id 被错误保存为 admin/admin2222 等时，用 pay_appid 替代 appid 显示
        appid_val = result.get("appid") or ""
        if not appid_val.startswith("wx") and result.get("pay_appid", "").startswith("wx"):
            result["appid"] = result["pay_appid"]
        pay_mch_val = result.get("pay_mch_id") or ""
        if pay_mch_val.lower().startswith("admin"):
            result["pay_mch_id"] = ""  # 清空错误的 admin/admin2222 等

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取小程序配置失败: {str(e)}"}), 500


@admin_miniprogram_config_api_bp.route("", methods=["POST"])
@login_required
def save_miniprogram_config():
    """保存小程序配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        db = models["db"]
        AIConfig = models["AIConfig"]

        data = request.get_json()
        if data is None:
            logger.warning("保存小程序配置失败: 请求体为空或格式错误，请确保 Content-Type 为 application/json")
            return jsonify({"status": "error", "message": "请求数据格式错误，请刷新页面后重试"}), 400

        # 修复浏览器自动填充：当 appid 或 pay_mch_id 为 admin/admin2222 等无效值时，用 pay_appid 替代 appid，清空 pay_mch_id
        appid_val = (data.get("appid") or "").strip()
        pay_appid_val = (data.get("pay_appid") or "").strip()
        pay_mch_id_val = (data.get("pay_mch_id") or "").strip()
        if not appid_val.startswith("wx") and pay_appid_val.startswith("wx"):
            appid_val = pay_appid_val
            logger.info("自动修复: appid 从无效值替换为 pay_appid")
        if (pay_mch_id_val or "").lower().startswith("admin"):
            pay_mch_id_val = ""
            logger.info("自动修复: pay_mch_id 从 admin 清空")
        data = dict(data)
        data["appid"] = appid_val
        data["pay_mch_id"] = pay_mch_id_val

        # 配置项映射：前端字段名 -> 数据库config_key
        configs_to_save = [
            ("miniprogram_appid", data.get("appid", ""), "小程序AppID"),
            ("miniprogram_app_secret", data.get("app_secret", ""), "小程序AppSecret"),
            ("wechat_pay_appid", data.get("pay_appid", ""), "微信支付AppID"),
            ("wechat_pay_mch_id", data.get("pay_mch_id", ""), "微信支付商户号"),
            ("wechat_pay_api_key", data.get("pay_api_key", ""), "微信支付API密钥"),
            ("wechat_pay_notify_url", data.get("pay_notify_url", ""), "微信支付回调地址"),
        ]

        for config_key, config_value, description in configs_to_save:
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = str(config_value) if config_value else ""
                config.description = description
                config.updated_at = datetime.now()
            else:
                config = AIConfig(
                    config_key=config_key,
                    config_value=str(config_value) if config_value else "",
                    description=description,
                )
                db.session.add(config)

        db.session.commit()

        logger.info(
            "✅ 小程序配置已更新: appid=%s, pay_appid=%s",
            data.get("appid", "")[:10] + "..." if data.get("appid") else "(空)",
            data.get("pay_appid", "")[:10] + "..." if data.get("pay_appid") else "(空)",
        )

        return jsonify(
            {"status": "success", "message": "小程序配置保存成功（需要重启服务才能生效）"}
        )
    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"保存失败: {str(e)}"}), 500
