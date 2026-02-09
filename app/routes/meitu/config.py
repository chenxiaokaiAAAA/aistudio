# -*- coding: utf-8 -*-
"""
美图API配置管理模块
"""

import logging

logger = logging.getLogger(__name__)
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_api_required, admin_required

from .utils import get_table_columns

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("meitu_config", __name__)


@bp.route("/config")
@login_required
@admin_required
def meitu_config():
    """美图API配置页面"""
    return render_template("admin/meitu_api_config.html")


@bp.route("/api/config", methods=["GET"])
@login_required
@admin_api_required
def get_meitu_config():
    """获取美图API配置"""
    try:
        models = get_models(["MeituAPIConfig", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        MeituAPIConfig = models["MeituAPIConfig"]

        # 优先使用原始SQL查询，避免SQLAlchemy自动访问不存在的列
        config = None
        try:
            # 先检查表结构，判断是否可以直接使用ORM
            columns = get_table_columns(db, "meitu_api_config")

            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ["api_key", "api_secret", "api_base_url", "api_endpoint"]
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            # 如果查询失败（可能是列不存在），使用原始SQL
            logger.warning(f"使用SQLAlchemy查询失败，尝试使用原始SQL: {str(e)}")
            try:
                # 先检查表结构
                columns = get_table_columns(db, "meitu_api_config")

                # 构建SELECT语句，只选择存在的列
                select_cols = []
                if "api_key" in columns:
                    select_cols.append("api_key")
                elif "app_id" in columns:
                    select_cols.append("app_id AS api_key")
                else:
                    select_cols.append("'' AS api_key")

                if "api_secret" in columns:
                    select_cols.append("api_secret")
                elif "secret_id" in columns:
                    select_cols.append("secret_id AS api_secret")
                else:
                    select_cols.append("'' AS api_secret")

                # 添加其他可能存在的列
                for col in [
                    "id",
                    "api_base_url",
                    "api_endpoint",
                    "repost_url",
                    "is_active",
                    "enable_in_workflow",
                    "created_at",
                    "updated_at",
                ]:
                    if col in columns:
                        select_cols.append(col)
                    elif col == "api_endpoint":
                        select_cols.append("'/openapi/realphotolocal_async' AS api_endpoint")
                    elif col == "api_base_url":
                        select_cols.append("'https://api.yunxiu.meitu.com' AS api_base_url")
                    elif col == "is_active":
                        select_cols.append("1 AS is_active")
                    elif col == "enable_in_workflow":
                        select_cols.append("0 AS enable_in_workflow")

                sql = f"SELECT {', '.join(select_cols)} FROM meitu_api_config WHERE is_active = 1 LIMIT 1"
                result = db.session.execute(db.text(sql)).fetchone()

                if result:
                    # 手动构建配置对象
                    result_dict = (
                        dict(result._mapping)
                        if hasattr(result, "_mapping")
                        else dict(
                            zip(
                                [c.split(" AS ")[-1] if " AS " in c else c for c in select_cols],
                                result,
                            )
                        )
                    )

                    class SimpleConfig:
                        def __init__(self, data):
                            self.id = data.get("id")
                            self.api_key = data.get("api_key", "")
                            self.api_secret = data.get("api_secret", "")
                            self.api_base_url = data.get(
                                "api_base_url", "https://api.yunxiu.meitu.com"
                            )
                            self.api_endpoint = data.get(
                                "api_endpoint", "/openapi/realphotolocal_async"
                            )
                            self.repost_url = data.get("repost_url")
                            self.is_active = data.get("is_active", True)
                            self.enable_in_workflow = data.get("enable_in_workflow", False)
                            self.created_at = data.get("created_at")
                            self.updated_at = data.get("updated_at")

                        @property
                        def app_id(self):
                            return self.api_key

                        @property
                        def app_key(self):
                            return self.api_key

                        @property
                        def secret_id(self):
                            return self.api_secret

                    config = SimpleConfig(result_dict)
                else:
                    config = None
            except Exception as sql_error:
                logger.error(f"使用原始SQL查询也失败: {str(sql_error)}")
                config = None
        if not config:
            return jsonify(
                {
                    "status": "success",
                    "data": {
                        "app_id": "",
                        "app_key": "",
                        "secret_id": "",
                        "api_base_url": "https://api.yunxiu.meitu.com",
                        "is_active": False,
                    },
                }
            )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "id": config.id,
                    "app_id": config.app_id or "",
                    "app_key": config.app_key or "",
                    "secret_id": config.secret_id or "",
                    "api_base_url": config.api_base_url or "https://api.yunxiu.meitu.com",
                    "api_endpoint": (
                        config.api_endpoint
                        if hasattr(config, "api_endpoint")
                        else "/api/v1/image/retouch"
                    ),
                    "is_active": config.is_active,
                    "enable_in_workflow": getattr(config, "enable_in_workflow", False),
                },
            }
        )

    except Exception as e:
        logger.info(f"获取美图API配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取配置失败: {str(e)}"}), 500


@bp.route("/api/config", methods=["POST"])
@login_required
@admin_api_required
def save_meitu_config():
    """保存美图API配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求数据为空"}), 400

        models = get_models(["MeituAPIConfig", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        MeituAPIConfig = models["MeituAPIConfig"]

        # 查找现有配置（优先使用原始SQL，避免列不存在的问题）
        config = None
        try:
            # 先检查表结构
            columns = get_table_columns(db, "meitu_api_config")

            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ["api_key", "api_secret", "api_base_url", "api_endpoint"]
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            logger.warning("查询配置失败，尝试使用原始SQL: {str(e)}")
            # 如果查询失败，使用原始SQL查找
            result = db.session.execute(
                db.text("SELECT id FROM meitu_api_config WHERE is_active = 1 LIMIT 1")
            ).fetchone()
            if result:
                # SQLAlchemy 2.0 的 Row 对象需要用索引访问，或者转换为字典
                if hasattr(result, "_mapping"):
                    config_id = result._mapping["id"]
                elif isinstance(result, tuple):
                    config_id = result[0]
                else:
                    config_id = result[0]  # 默认使用索引0
                config = MeituAPIConfig.query.get(config_id)
            else:
                config = None

        app_id_value = data.get("app_id", "")
        api_key_value = data.get("api_key", "")
        api_secret_value = data.get("api_secret") or data.get("secret_id", "")

        if config:
            # 更新现有配置（使用setattr避免列不存在的问题）
            # 先检查列是否存在，如果不存在则使用原始SQL更新
            try:
                # 尝试使用属性设置（如果列存在）
                if hasattr(config, "app_id"):
                    config.app_id = app_id_value
                if hasattr(config, "api_key"):
                    config.api_key = api_key_value

                if hasattr(config, "api_secret"):
                    config.api_secret = api_secret_value
                elif hasattr(config, "secret_id"):
                    config.secret_id = api_secret_value

                config.api_base_url = data.get("api_base_url", "https://api.yunxiu.meitu.com")
                if hasattr(config, "api_endpoint"):
                    config.api_endpoint = data.get("api_endpoint", "/openapi/realphotolocal_async")
                if hasattr(config, "repost_url"):
                    config.repost_url = data.get("repost_url") or None
                config.is_active = data.get("is_active", True)
                if hasattr(config, "enable_in_workflow"):
                    config.enable_in_workflow = data.get("enable_in_workflow", False)
                if hasattr(config, "updated_at"):
                    config.updated_at = datetime.now()
            except Exception as update_error:
                # 如果属性设置失败，使用原始SQL更新
                logger.warning(f"使用属性更新失败，尝试使用原始SQL: {str(update_error)}")
                # 检查表结构，确定使用哪个字段名
                columns = get_table_columns(db, "meitu_api_config")

                # 构建UPDATE语句
                update_parts = []
                if "app_id" in columns:
                    update_parts.append(
                        f"app_id = '{app_id_value.replace(chr(39), chr(39) + chr(39))}'"
                    )
                if "api_key" in columns:
                    update_parts.append(
                        f"api_key = '{api_key_value.replace(chr(39), chr(39) + chr(39))}'"
                    )

                if "api_secret" in columns:
                    update_parts.append(
                        f"api_secret = '{api_secret_value.replace(chr(39), chr(39) + chr(39))}'"
                    )
                elif "secret_id" in columns:
                    update_parts.append(
                        f"secret_id = '{api_secret_value.replace(chr(39), chr(39) + chr(39))}'"
                    )

                if "api_base_url" in columns:
                    update_parts.append(
                        f"api_base_url = '{data.get('api_base_url', 'https://api.yunxiu.meitu.com').replace(chr(39), chr(39) + chr(39))}'"
                    )
                if "api_endpoint" in columns:
                    update_parts.append(
                        f"api_endpoint = '{data.get('api_endpoint', '/openapi/realphotolocal_async').replace(chr(39), chr(39) + chr(39))}'"
                    )
                if "repost_url" in columns:
                    repost_url = data.get("repost_url") or ""
                    if repost_url:
                        update_parts.append(
                            f"repost_url = '{repost_url.replace(chr(39), chr(39) + chr(39))}'"
                        )
                    else:
                        update_parts.append("repost_url = NULL")
                if "is_active" in columns:
                    update_parts.append(f"is_active = {1 if data.get('is_active', True) else 0}")
                if "enable_in_workflow" in columns:
                    update_parts.append(
                        f"enable_in_workflow = {1 if data.get('enable_in_workflow', False) else 0}"
                    )
                if "updated_at" in columns:
                    update_parts.append("updated_at = datetime('now')")

                if update_parts:
                    sql = f"UPDATE meitu_api_config SET {', '.join(update_parts)} WHERE id = {config.id}"
                    db.session.execute(db.text(sql))
        else:
            # 创建新配置（使用原始SQL，避免列不存在的问题）
            try:
                # 先检查表结构
                columns = get_table_columns(db, "meitu_api_config")

                # 确定字段名
                key_field = (
                    "api_key"
                    if "api_key" in columns
                    else ("app_id" if "app_id" in columns else None)
                )
                secret_field = (
                    "api_secret"
                    if "api_secret" in columns
                    else ("secret_id" if "secret_id" in columns else None)
                )

                if not key_field or not secret_field:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "数据库表结构不完整，请运行迁移脚本添加 api_key 和 api_secret 字段",
                            }
                        ),
                        500,
                    )

                # 构建INSERT语句
                insert_cols = [key_field, secret_field]
                insert_vals = [
                    f"'{api_key_value.replace(chr(39), chr(39) + chr(39))}'",
                    f"'{api_secret_value.replace(chr(39), chr(39) + chr(39))}'",
                ]

                # 如果存在 app_id 字段，添加到INSERT语句
                if "app_id" in columns:
                    insert_cols.append("app_id")
                    insert_vals.append(f"'{app_id_value.replace(chr(39), chr(39) + chr(39))}'")

                if "api_base_url" in columns:
                    insert_cols.append("api_base_url")
                    insert_vals.append(
                        f"'{data.get('api_base_url', 'https://api.yunxiu.meitu.com').replace(chr(39), chr(39) + chr(39))}'"
                    )
                if "api_endpoint" in columns:
                    insert_cols.append("api_endpoint")
                    insert_vals.append(
                        f"'{data.get('api_endpoint', '/openapi/realphotolocal_async').replace(chr(39), chr(39) + chr(39))}'"
                    )
                if "repost_url" in columns:
                    insert_cols.append("repost_url")
                    repost_url = data.get("repost_url") or ""
                    if repost_url:
                        insert_vals.append(f"'{repost_url.replace(chr(39), chr(39) + chr(39))}'")
                    else:
                        insert_vals.append("NULL")
                if "is_active" in columns:
                    insert_cols.append("is_active")
                    insert_vals.append(str(1 if data.get("is_active", True) else 0))
                if "enable_in_workflow" in columns:
                    insert_cols.append("enable_in_workflow")
                    insert_vals.append(str(1 if data.get("enable_in_workflow", False) else 0))

                sql = f"INSERT INTO meitu_api_config ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})"
                db.session.execute(db.text(sql))
                db.session.commit()

                # 获取新创建的配置ID
                result = db.session.execute(
                    db.text(
                        "SELECT id FROM meitu_api_config WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
                    )
                ).fetchone()
                # SQLAlchemy 2.0 的 Row 对象需要用索引访问，或者转换为字典
                if hasattr(result, "_mapping"):
                    config_id = result._mapping["id"]
                elif isinstance(result, tuple):
                    config_id = result[0]
                else:
                    config_id = result[0]  # 默认使用索引0
                config = MeituAPIConfig.query.get(config_id)
            except Exception as create_error:
                # 如果原始SQL也失败，尝试使用模型创建（可能会失败，但至少尝试一下）
                logger.warning("使用原始SQL创建失败，尝试使用模型: {str(create_error)}")
                config = MeituAPIConfig(
                    api_key=api_key_value,
                    api_secret=api_secret_value,
                    api_base_url=data.get("api_base_url", "https://api.yunxiu.meitu.com"),
                    api_endpoint=data.get("api_endpoint", "/openapi/realphotolocal_async"),
                    repost_url=data.get("repost_url") or None,
                    is_active=data.get("is_active", True),
                    enable_in_workflow=data.get("enable_in_workflow", False),
                )
                db.session.add(config)

        db.session.commit()

        return jsonify({"status": "success", "message": "配置保存成功", "data": {"id": config.id}})

    except Exception as e:
        logger.info(f"保存美图API配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"保存配置失败: {str(e)}"}), 500
