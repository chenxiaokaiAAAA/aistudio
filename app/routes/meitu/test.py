# -*- coding: utf-8 -*-
"""
美图API测试模块
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from .utils import get_table_columns

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("meitu_test", __name__)


@bp.route("/api/test", methods=["POST"])
@login_required
def test_meitu_api():
    """测试美图API调用"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        MeituAPIConfig = test_server_module.MeituAPIConfig
        MeituAPICallLog = test_server_module.MeituAPICallLog

        # 获取预设ID
        preset_id = request.form.get("preset_id", "").strip()
        if not preset_id:
            return jsonify({"status": "error", "message": "请输入预设ID"}), 400

        # 获取API配置（优先使用原始SQL，避免列不存在的问题）
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
            logger.warning(f"查询配置失败，尝试使用原始SQL: {str(e)}")
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
                try:
                    config = MeituAPIConfig.query.get(config_id)
                except Exception:
                    # 如果还是失败，使用原始SQL构建配置对象
                    columns = get_table_columns(db, "meitu_api_config")

                    # 构建SELECT语句，只选择存在的列
                    select_cols = ["id"]
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
                        "api_base_url",
                        "api_endpoint",
                        "repost_url",
                        "is_active",
                        "enable_in_workflow",
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

                    sql = f"SELECT {', '.join(select_cols)} FROM meitu_api_config WHERE id = {config_id}"
                    result = db.session.execute(db.text(sql)).fetchone()

                    if result:
                        result_dict = (
                            dict(result._mapping)
                            if hasattr(result, "_mapping")
                            else dict(
                                zip(
                                    [
                                        c.split(" AS ")[-1] if " AS " in c else c
                                        for c in select_cols
                                    ],
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
            else:
                config = None

        if not config:
            return jsonify({"status": "error", "message": "请先配置美图API密钥"}), 400

        # 生成测试订单号
        test_order_number = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 检查是否提供了云端URL（如果前端开启了"先上传到云服务器"开关）
        cloud_image_url = request.form.get("cloud_image_url", "").strip()
        image_url = None

        if cloud_image_url:
            # 如果提供了云端URL，直接使用
            image_url = cloud_image_url
            logger.info(f"✅ 使用云端URL（已上传到云服务器）: {image_url}")
        else:
            # 否则使用原来的逻辑：上传到本地，然后获取公网URL
            if "image" not in request.files:
                return jsonify({"status": "error", "message": "请上传测试图片"}), 400

            image_file = request.files["image"]
            if image_file.filename == "":
                return jsonify({"status": "error", "message": "请选择图片文件"}), 400

            # 保存上传的图片到临时目录
            uploads_dir = "uploads"
            test_dir = os.path.join(uploads_dir, "meitu_test")
            os.makedirs(test_dir, exist_ok=True)

            filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(image_file.filename)}"
            test_image_path = os.path.join(test_dir, filename)
            image_file.save(test_image_path)

            # 调用美图API
            from app.services.meitu_api_service import call_meitu_api, get_public_image_url

            # 获取图片的公开URL（美图API需要图片URL）
            # 测试环境：自动上传到OSS获取公网URL
            # 如果OSS未配置，会返回错误提示
            logger.info(f"📤 开始获取图片公网URL: {test_image_path}")
            image_url = get_public_image_url(
                test_image_path, use_oss=True, order_number=test_order_number  # 测试环境使用OSS
            )

            if not image_url:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": '无法获取图片的公网URL。请配置OSS（scripts/oss_config.py）或开启"先上传到云服务器"开关',
                            "hint": '测试环境需要将图片上传到OSS/CDN等公网可访问的存储服务，或开启"先上传到云服务器"开关',
                        }
                    ),
                    400,
                )

        # 调用美图API
        from app.services.meitu_api_service import call_meitu_api

        # 获取API密钥（根据美图API文档：api_key对应APIKEY，api_secret对应SECRETID）
        # 注意：不要使用app_id，应该直接使用api_key和api_secret
        api_key_value = getattr(config, "api_key", None) or ""
        api_secret_value = getattr(config, "api_secret", None) or ""

        # 如果api_key或api_secret为空，尝试从旧字段获取（兼容旧数据）
        if not api_key_value:
            api_key_value = getattr(config, "app_id", "") or ""
        if not api_secret_value:
            api_secret_value = getattr(config, "secret_id", "") or ""

        # 获取API基础URL和端点（确保使用正确的默认值）
        api_base_url = getattr(config, "api_base_url", None) or "https://api.yunxiu.meitu.com"
        api_endpoint = getattr(config, "api_endpoint", None) or "/openapi/realphotolocal_async"

        logger.info("📋 美图API配置:")
        logger.info(f"   - API Key (api_key): {api_key_value[:10] if api_key_value else 'None'}...")
        logger.info(
            f"   - API Secret (api_secret): {api_secret_value[:10] if api_secret_value else 'None'}..."
        )
        logger.info(f"   - API Base URL: {api_base_url}")
        logger.info(f"   - API Endpoint: {api_endpoint}")
        logger.info(f"   - 预设ID: {preset_id}")
        logger.info(f"   - 图片URL: {image_url}")

        # 验证API密钥
        if not api_key_value or not api_secret_value:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"API密钥配置不完整：api_key={bool(api_key_value)}, api_secret={bool(api_secret_value)}。请检查配置页面，确保填写了正确的APIKEY和SECRETID。",
                    }
                ),
                400,
            )

        success, result_image_path, error_message, call_log = call_meitu_api(
            image_path=image_url,  # 传递图片URL而不是本地路径
            preset_id=preset_id,
            api_key=api_key_value,
            api_secret=api_secret_value,
            api_base_url=api_base_url,
            api_endpoint=api_endpoint,
            repost_url=config.repost_url if hasattr(config, "repost_url") else None,
            db=db,
            MeituAPICallLog=MeituAPICallLog,
            order_id=None,
            order_number=test_order_number,
            product_id=None,
        )

        # 提交数据库更改
        db.session.commit()

        if success:
            return jsonify(
                {
                    "status": "success",
                    "message": "测试成功",
                    "data": {
                        "task_id": call_log.id if call_log else None,
                        "order_number": test_order_number,
                        "result_image_url": call_log.result_image_url if call_log else None,
                        "result_image_path": result_image_path,
                        "duration_ms": call_log.duration_ms if call_log else None,
                        "response_status": call_log.response_status if call_log else None,
                    },
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": error_message or "测试失败",
                        "data": {
                            "task_id": call_log.id if call_log else None,
                            "order_number": test_order_number,
                            "error_message": error_message,
                        },
                    }
                ),
                400,
            )

    except Exception as e:
        logger.info(f"测试美图API失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"测试失败: {str(e)}"}), 500
