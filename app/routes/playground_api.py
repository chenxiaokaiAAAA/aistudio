# -*- coding: utf-8 -*-
"""
Playground API路由模块
提供模板列表、测试工作流等API接口
"""

import logging

logger = logging.getLogger(__name__)
import json
import os
import sys
import time

import requests
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
playground_api_bp = Blueprint("playground_api", __name__, url_prefix="/api/playground")


@playground_api_bp.route("/tasks", methods=["GET"])
def get_playground_tasks():
    """获取Playground任务列表（用户端，不需要登录）"""
    try:
        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        AITask = test_server_module.AITask
        Order = test_server_module.Order
        StyleCategory = test_server_module.StyleCategory
        StyleImage = test_server_module.StyleImage
        APIProviderConfig = test_server_module.APIProviderConfig

        import json
        from datetime import datetime

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        status = request.args.get("status")
        order_number = request.args.get("order_number")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # 构建查询：只查询Playground任务（订单号以PLAY_开头）
        query = AITask.query.join(Order, AITask.order_id == Order.id).filter(
            Order.order_number.like("PLAY_%")
        )

        # 如果用户已登录，只显示该用户的任务
        if current_user and current_user.is_authenticated:
            query = query.filter(Order.customer_name == current_user.username)

        if status:
            query = query.filter_by(status=status)
        if order_number:
            query = query.filter(AITask.order_number.like(f"%{order_number}%"))
        if start_date:
            query = query.filter(AITask.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(AITask.created_at <= datetime.fromisoformat(end_date))

        # 分页
        pagination = query.order_by(AITask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # 优化N+1查询：批量查询所有任务的关联信息
        category_ids = set()
        image_ids = set()
        api_config_ids = set()

        for task in pagination.items:
            if task.style_category_id:
                category_ids.add(task.style_category_id)
            if task.style_image_id:
                image_ids.add(task.style_image_id)
            if task.processing_log:
                try:
                    parsed_log = json.loads(task.processing_log)
                    if isinstance(parsed_log, dict):
                        api_config_id = parsed_log.get("api_config_id")
                        if api_config_id:
                            api_config_ids.add(api_config_id)
                except Exception:
                    pass

        # 批量查询所有风格分类
        categories_map = {}
        if category_ids:
            all_categories = StyleCategory.query.filter(
                StyleCategory.id.in_(list(category_ids))
            ).all()
            for cat in all_categories:
                categories_map[cat.id] = cat

        # 批量查询所有风格图片
        images_map = {}
        if image_ids:
            all_images = StyleImage.query.filter(StyleImage.id.in_(list(image_ids))).all()
            for img in all_images:
                images_map[img.id] = img

        # 批量查询所有API配置
        api_configs_map = {}
        if api_config_ids:
            all_configs = APIProviderConfig.query.filter(
                APIProviderConfig.id.in_(list(api_config_ids))
            ).all()
            for config in all_configs:
                api_configs_map[config.id] = config

        tasks = []
        for task in pagination.items:
            # 从批量查询的映射中获取关联信息（避免N+1查询）
            style_category_name = None
            style_image_name = None
            if task.style_category_id:
                category = categories_map.get(task.style_category_id)
                if category:
                    style_category_name = category.name
            if task.style_image_id:
                image = images_map.get(task.style_image_id)
                if image:
                    style_image_name = image.name

            # 获取任务ID和API信息
            task_id = task.comfyui_prompt_id
            api_task_id = None
            api_info = {}
            api_config_id = None
            if task.processing_log:
                try:
                    parsed_log = json.loads(task.processing_log)
                    if isinstance(parsed_log, dict):
                        api_info = parsed_log
                        if not task_id:
                            task_id = api_info.get("task_id") or api_info.get("id")
                        api_task_id = (
                            api_info.get("api_task_id")
                            or api_info.get("taskId")
                            or api_info.get("task_id")
                        )
                        # 从 processing_log 中获取 api_config_id
                        api_config_id = api_info.get("api_config_id")
                except Exception:
                    pass
            if not api_task_id and task.comfyui_prompt_id:
                api_task_id = task.comfyui_prompt_id

            # 从批量查询的映射中获取API配置名称（避免N+1查询）
            api_provider_name = None
            if api_config_id:
                api_config = api_configs_map.get(api_config_id)
                if api_config:
                    api_provider_name = api_config.name

            # 状态文本映射
            status_map = {
                "pending": "待处理",
                "processing": "处理中",
                "completed": "已完成",
                "failed": "失败",
                "cancelled": "已取消",
            }

            # 计算完成耗时（秒）
            duration_seconds = None
            if task.completed_at and task.created_at:
                duration = task.completed_at - task.created_at
                duration_seconds = int(duration.total_seconds())

            task_data = {
                "id": task.id,
                "task_id": task_id or api_task_id or f"TASK_{task.id}",
                "order_number": task.order_number or "",
                "workflow_name": style_category_name or style_image_name or "未知工作流",
                "api_provider_name": api_provider_name or "-",
                "input_image_path": task.input_image_path or "",
                "output_image_path": task.output_image_path or "",
                "status": task.status or "pending",
                "status_text": status_map.get(task.status, task.status),
                "duration_seconds": duration_seconds,
                "request_params": api_info.get("request_params") if api_info else None,
                "response_data": api_info.get("response_data") if api_info else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message,
            }
            tasks.append(task_data)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "tasks": tasks,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "page": page,
                    "per_page": per_page,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取Playground任务列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务列表失败: {str(e)}"}), 500


@playground_api_bp.route("/templates", methods=["GET"])
def get_templates():
    """获取所有可用的模板列表（按模式分类）"""
    try:
        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        APITemplate = models.get("APITemplate")

        mode = request.args.get("mode", "workflow")  # workflow, api, comfyui

        result = {
            "workflow": [],  # AI工作流模板
            "api": [],  # API编辑模板
            "comfyui": [],  # API-ComfyUI工作流模板
        }

        # 优化N+1查询：批量查询所有启用的风格分类和图片
        categories = (
            StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
        )

        # 批量查询所有风格图片
        category_ids = [cat.id for cat in categories]
        images_map = {}
        if category_ids:
            all_images = (
                StyleImage.query.filter(
                    StyleImage.category_id.in_(category_ids), StyleImage.is_active is True
                )
                .order_by(StyleImage.sort_order)
                .all()
            )
            for img in all_images:
                if img.category_id not in images_map:
                    images_map[img.category_id] = []
                images_map[img.category_id].append(img)

        # 批量查询所有API模板
        image_ids = [img.id for imgs in images_map.values() for img in imgs]
        api_templates_map = {}
        api_config_ids = []
        if APITemplate and image_ids:
            all_templates = APITemplate.query.filter(
                APITemplate.style_image_id.in_(image_ids), APITemplate.is_active is True
            ).all()
            for template in all_templates:
                api_templates_map[template.style_image_id] = template
                if template.api_config_id:
                    api_config_ids.append(template.api_config_id)

        # 批量查询所有API配置（避免N+1查询）
        api_configs_map = {}
        APIProviderConfig = models.get("APIProviderConfig")
        if APIProviderConfig and api_config_ids:
            unique_config_ids = list(set(api_config_ids))
            all_configs = APIProviderConfig.query.filter(
                APIProviderConfig.id.in_(unique_config_ids)
            ).all()
            for config in all_configs:
                api_configs_map[config.id] = config

        for category in categories:
            # 从批量查询的映射中获取图片（避免N+1查询）
            images = images_map.get(category.id, [])

            for image in images:
                # 检查是否有工作流配置
                # 修复：只有当明确启用时才认为有工作流
                has_workflow = False
                if image.is_ai_enabled is True:
                    # 图片级别明确启用，检查是否有工作流文件
                    if image.workflow_file:
                        has_workflow = True
                elif image.is_ai_enabled is None:
                    # 图片级别未设置，继承分类配置
                    if category.is_ai_enabled and category.workflow_file:
                        has_workflow = True
                # 如果 image.is_ai_enabled is False，则不启用工作流

                # 检查是否有API模板配置（区分普通API和ComfyUI工作流）
                has_api = False
                has_comfyui = False
                api_template_info = None
                workflow_tags = []  # 用于存储标签信息

                if APITemplate:
                    # 从批量查询的映射中获取API模板（避免N+1查询）
                    api_template = api_templates_map.get(image.id)

                    if api_template:
                        # 解析upload_config
                        upload_config = None
                        if api_template.upload_config:
                            try:
                                import json

                                upload_config = json.loads(api_template.upload_config)
                            except Exception:
                                pass

                        api_template_info = {
                            "id": api_template.id,
                            "api_config_id": api_template.api_config_id,
                            "upload_config": upload_config,  # 添加上传配置信息
                        }

                        # 判断是ComfyUI工作流还是普通API
                        # 方法1：检查 request_body_template 字段（ComfyUI工作流特有）
                        is_comfyui_by_template = bool(api_template.request_body_template)

                        # 方法2：检查关联的APIProviderConfig的api_type（从批量查询的映射中获取，避免N+1查询）
                        is_comfyui_by_config = False
                        if api_template.api_config_id:
                            api_config = api_configs_map.get(api_template.api_config_id)
                            if api_config and api_config.api_type == "runninghub-comfyui-workflow":
                                is_comfyui_by_config = True

                        # 如果满足任一条件，认为是ComfyUI工作流
                        if is_comfyui_by_template or is_comfyui_by_config:
                            has_comfyui = True
                            workflow_tags.append("API-ComfyUI工作流")
                        else:
                            # 否则是普通API编辑
                            has_api = True
                            workflow_tags.append("API编辑")

                # 构建工作流配置信息（用于测试时传递）
                workflow_config = None
                if has_workflow:
                    if image.is_ai_enabled is True:
                        # 图片级别配置
                        workflow_config = {
                            "workflow_file": image.workflow_file or "",
                            "workflow_name": image.workflow_name or "",
                            "workflow_input_ids": image.workflow_input_ids or "",
                            "workflow_output_id": image.workflow_output_id or "",
                            "workflow_ref_id": image.workflow_ref_id or "",
                            "workflow_ref_image": image.workflow_ref_image or "",
                            "workflow_custom_prompt_id": image.workflow_custom_prompt_id or "",
                            "workflow_custom_prompt_content": image.workflow_custom_prompt_content
                            or "",
                        }
                    elif image.is_ai_enabled is None and category.is_ai_enabled:
                        # 分类级别配置
                        workflow_config = {
                            "workflow_file": category.workflow_file or "",
                            "workflow_name": category.workflow_name or "",
                            "workflow_input_ids": category.workflow_input_ids or "",
                            "workflow_output_id": category.workflow_output_id or "",
                            "workflow_ref_id": category.workflow_ref_id or "",
                            "workflow_ref_image": category.workflow_ref_image or "",
                            "workflow_custom_prompt_id": category.workflow_custom_prompt_id or "",
                            "workflow_custom_prompt_content": category.workflow_custom_prompt_content
                            or "",
                        }

                # 构建模板信息（先不添加标签，根据模式决定）
                template_info = {
                    "id": image.id,
                    "name": image.name,
                    "code": image.code,
                    "description": image.description,
                    "image_url": image.image_url,
                    "category_id": category.id,
                    "category_name": category.name,
                    "category_code": category.code,
                    "category_icon": category.icon,
                    "has_workflow": has_workflow,
                    "has_api": has_api,
                    "has_comfyui": has_comfyui,
                    "api_template_info": api_template_info,
                    "workflow_config": workflow_config,  # 添加工作流配置信息
                }

                # 根据模式添加到对应列表，并设置对应的标签
                if mode == "workflow":
                    if has_workflow:
                        # 工作流模式：只显示AI工作流标签
                        template_info_copy = template_info.copy()
                        template_info_copy["workflow_tags"] = ["AI工作流"]
                        result["workflow"].append(template_info_copy)
                elif mode == "api":
                    if has_api:
                        # API编辑模式：只显示API编辑标签
                        template_info_copy = template_info.copy()
                        template_info_copy["workflow_tags"] = ["API编辑"]
                        result["api"].append(template_info_copy)
                elif mode == "comfyui":
                    if has_comfyui:
                        # ComfyUI工作流模式：只显示ComfyUI工作流标签
                        template_info_copy = template_info.copy()
                        template_info_copy["workflow_tags"] = ["API-ComfyUI工作流"]
                        result["comfyui"].append(template_info_copy)
                elif mode == "all":
                    # 如果模式是all，添加到所有匹配的列表，每个列表显示对应的标签
                    if has_workflow:
                        template_info_workflow = template_info.copy()
                        template_info_workflow["workflow_tags"] = ["AI工作流"]
                        result["workflow"].append(template_info_workflow)
                    if has_api:
                        template_info_api = template_info.copy()
                        template_info_api["workflow_tags"] = ["API编辑"]
                        result["api"].append(template_info_api)
                    if has_comfyui:
                        template_info_comfyui = template_info.copy()
                        template_info_comfyui["workflow_tags"] = ["API-ComfyUI工作流"]
                        result["comfyui"].append(template_info_comfyui)

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        logger.info(f"获取模板列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取模板列表失败: {str(e)}"}), 500


@playground_api_bp.route("/api-providers", methods=["GET"])
def get_api_providers():
    """获取所有API服务商配置"""
    try:
        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        APIProviderConfig = models.get("APIProviderConfig")
        if not APIProviderConfig:
            return jsonify({"status": "error", "message": "API服务商配置模型未找到"}), 500

        configs = (
            APIProviderConfig.query.filter_by(is_active=True)
            .order_by(
                APIProviderConfig.priority.desc(),
                APIProviderConfig.is_default.desc(),
                APIProviderConfig.id,
            )
            .all()
        )

        result = []
        for config in configs:
            result.append(
                {
                    "id": config.id,
                    "name": config.name,
                    "api_type": config.api_type,
                    "provider_name": getattr(config, "provider_name", config.name),
                    "model_name": config.model_name,
                    "is_default": config.is_default,
                }
            )

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        logger.info(f"获取API服务商列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取API服务商列表失败: {str(e)}"}), 500


@playground_api_bp.route("/test/workflow", methods=["POST"])
@login_required
def test_workflow():
    """测试AI工作流"""
    try:
        # 检查Playground使用次数限制
        from datetime import date

        from app.utils.db_utils import get_models

        models = get_models()
        if models:
            db = models["db"]
            User = models["User"]
            user = User.query.get(current_user.id)

            if user:
                today = date.today()

                # 检查是否需要重置每日使用次数
                if hasattr(user, "playground_last_reset_date"):
                    if (
                        not user.playground_last_reset_date
                        or user.playground_last_reset_date != today
                    ):
                        user.playground_used_today = 0
                        user.playground_last_reset_date = today
                        db.session.commit()

                # 检查使用次数限制
                if hasattr(user, "playground_daily_limit") and user.playground_daily_limit > 0:
                    used_today = getattr(user, "playground_used_today", 0) or 0
                    if used_today >= user.playground_daily_limit:
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"今日Playground使用次数已达上限（{user.playground_daily_limit}次），次数不足，请联系管理员增加使用次数",
                                }
                            ),
                            403,
                        )

        data = request.get_json()
        image_id = data.get("image_id")
        image_data = data.get("image_data", [])

        if not image_id:
            return jsonify({"status": "error", "message": "缺少图片ID"}), 400

        if not image_data:
            return jsonify({"status": "error", "message": "缺少图片数据"}), 400

        # 直接调用admin_styles_api中的test_workflow函数
        # 由于test_workflow会从request.get_json()读取数据，我们需要确保数据格式正确
        # 创建一个新的请求数据，然后调用函数
        from app.routes.admin_styles_api import test_workflow as admin_test_workflow

        # 临时修改request的json数据
        original_json = request.get_json()
        request._cached_json = {
            "image_data": image_data if isinstance(image_data, list) else [image_data]
        }

        try:
            # 临时设置current_user以跳过权限检查（如果未登录）
            if not current_user.is_authenticated:
                from flask_login import AnonymousUserMixin

                class TempUser(AnonymousUserMixin):
                    role = "admin"

                request._cached_user = TempUser()

            result = admin_test_workflow(image_id)
            return result
        finally:
            # 恢复原始数据
            request._cached_json = original_json
            if hasattr(request, "_cached_user"):
                delattr(request, "_cached_user")

    except Exception as e:
        logger.info(f"测试工作流失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"测试工作流失败: {str(e)}"}), 500


@playground_api_bp.route("/find-template", methods=["POST"])
def find_template():
    """查找可用的模板（用于手动模式）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求数据为空"}), 400

        api_config_id = data.get("api_config_id")
        if not api_config_id:
            return jsonify({"status": "error", "message": "请选择API服务商"}), 400

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        APITemplate = test_server_module.APITemplate

        # 查找一个可用的API模板（用于获取style_image_id）
        api_template = APITemplate.query.filter_by(
            api_config_id=api_config_id, is_active=True
        ).first()

        if not api_template:
            # 如果没有找到匹配的模板，使用第一个可用的模板
            api_template = APITemplate.query.filter_by(is_active=True).first()

        if not api_template or not api_template.style_image_id:
            return (
                jsonify(
                    {"status": "error", "message": "未找到可用的模板配置，请先配置一个API模板"}
                ),
                400,
            )

        return jsonify(
            {
                "status": "success",
                "data": {"image_id": api_template.style_image_id, "template_id": api_template.id},
            }
        )

    except Exception as e:
        logger.info(f"查找模板失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"查找模板失败: {str(e)}"}), 500


@playground_api_bp.route("/test/comfyui", methods=["POST"])
@login_required
def test_comfyui():
    """测试API-ComfyUI工作流"""
    try:
        # 检查Playground使用次数限制
        from datetime import date

        from app.utils.db_utils import get_models

        models = get_models()
        if models:
            db = models["db"]
            User = models["User"]
            user = User.query.get(current_user.id)

            if user:
                today = date.today()

                # 检查是否需要重置每日使用次数
                if hasattr(user, "playground_last_reset_date"):
                    if (
                        not user.playground_last_reset_date
                        or user.playground_last_reset_date != today
                    ):
                        user.playground_used_today = 0
                        user.playground_last_reset_date = today
                        db.session.commit()

                # 检查使用次数限制
                if hasattr(user, "playground_daily_limit") and user.playground_daily_limit > 0:
                    used_today = getattr(user, "playground_used_today", 0) or 0
                    if used_today >= user.playground_daily_limit:
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": f"今日Playground使用次数已达上限（{user.playground_daily_limit}次），次数不足，请联系管理员增加使用次数",
                                }
                            ),
                            403,
                        )

        data = request.get_json()
        image_id = data.get("image_id")
        image_urls = data.get("image_urls", [])

        if not image_id:
            return jsonify({"status": "error", "message": "缺少图片ID"}), 400

        if not image_urls:
            return jsonify({"status": "error", "message": "缺少图片URL"}), 400

        # test_api_comfyui_template需要从request.form获取数据
        from werkzeug.datastructures import ImmutableMultiDict

        # 创建form数据（支持多图，使用getlist方式）
        form_items = []
        if isinstance(image_urls, list):
            for url in image_urls:
                form_items.append(("cloud_image_url", url))
        else:
            form_items.append(("cloud_image_url", image_urls))

        # 临时修改request的form数据
        # Flask的request.form是一个属性，需要同时修改_form和_cached_form
        original_form = getattr(request, "_form", None)
        original_cached_form = getattr(request, "_cached_form", None)

        # 创建新的ImmutableMultiDict
        new_form = ImmutableMultiDict(form_items)

        # 同时设置_form和_cached_form，确保request.form属性能正确读取
        request._form = new_form
        request._cached_form = new_form

        try:
            from app.routes.admin_styles_api import test_api_comfyui_template as admin_test_comfyui

            # 临时设置current_user以跳过权限检查（如果未登录）
            if not current_user.is_authenticated:
                from flask_login import AnonymousUserMixin

                class TempUser(AnonymousUserMixin):
                    role = "admin"

                request._cached_user = TempUser()

            result = admin_test_comfyui(image_id)
            return result
        finally:
            # 恢复原始form数据
            if original_form is not None:
                request._form = original_form
            else:
                if hasattr(request, "_form"):
                    delattr(request, "_form")

            if original_cached_form is not None:
                request._cached_form = original_cached_form
            else:
                if hasattr(request, "_cached_form"):
                    delattr(request, "_cached_form")

            if hasattr(request, "_cached_user"):
                delattr(request, "_cached_user")

    except Exception as e:
        logger.info(f"测试ComfyUI工作流失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"测试ComfyUI工作流失败: {str(e)}"}), 500


@playground_api_bp.route("/upload", methods=["POST"])
def upload_image():
    """上传图片到云服务器（支持单图或多图）"""
    try:
        # 支持多文件上传
        if "images[]" in request.files:
            files = request.files.getlist("images[]")
        elif "image" in request.files:
            files = [request.files["image"]]
        else:
            return jsonify({"status": "error", "message": "请上传图片"}), 400

        # 获取图片上传配置
        import sys

        from app.utils.config_loader import get_image_upload_config, should_upload_to_grsai

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        AIConfig = test_server_module.AIConfig

        upload_config = get_image_upload_config(db, AIConfig)
        need_upload_to_grsai = upload_config["strategy"] == "grsai"

        # 如果配置为直接使用云端URL（云端生产环境），且图片已经是云端URL，则直接返回
        # 注意：Playground上传的是文件，不是URL，所以这里仍然需要保存文件
        # 但如果是云端生产环境，文件应该已经通过CDN或其他方式可访问，这里先保存到本地
        # 实际使用中，云端环境可能需要通过其他方式（如OSS直传）来处理
        if not need_upload_to_grsai and upload_config["environment"] == "production":
            # 云端生产环境：保存到本地，但返回的URL应该是云端可访问的URL
            # 这里假设文件保存后，通过CDN或OSS可以访问
            uploads_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)

            uploaded_files = []
            for idx, file in enumerate(files):
                if file.filename == "":
                    continue

                filename = secure_filename(file.filename)
                timestamp = int(time.time())
                unique_filename = f"playground_{timestamp}_{idx}_{filename}"
                filepath = os.path.join(uploads_dir, unique_filename)
                file.save(filepath)

                # 返回本地URL（云端环境应该配置CDN或OSS，使这个URL可访问）
                image_url = f"/uploads/{unique_filename}"
                uploaded_files.append(
                    {"url": image_url, "filename": filename, "original_filename": filename}
                )

            if not uploaded_files:
                return jsonify({"status": "error", "message": "没有成功上传的图片"}), 400

            return jsonify(
                {
                    "status": "success",
                    "data": uploaded_files if len(uploaded_files) > 1 else uploaded_files[0],
                }
            )

        # 需要上传到GRSAI的逻辑
        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        APIProviderConfig = test_server_module.APIProviderConfig

        # 获取API配置（优先使用默认配置）
        api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True).first()

        if not api_config or not api_config.api_key:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "未找到可用的API配置或API Key，请先在API服务商配置中设置API Key",
                    }
                ),
                400,
            )

        uploaded_files = []

        for idx, file in enumerate(files):
            if file.filename == "":
                continue

            # 获取文件扩展名
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower().lstrip(".")
            if ext not in ["jpg", "jpeg", "png", "gi", "webp"]:
                continue

            logger.info(f"📤 [Playground上传] 开始上传图片 {idx + 1}/{len(files)}: {filename}")

            # 第一步：获取上传token
            token_url = "https://grsai.dakka.com.cn/client/resource/newUploadTokenZH"
            proxies = {"http": None, "https": None}  # 强制禁用代理

            headers = {
                "Authorization": f"Bearer {api_config.api_key}",
                "Content-Type": "application/json",
            }
            data = {"sux": ext}

            token_response = requests.post(
                url=token_url, headers=headers, json=data, proxies=proxies, timeout=30
            )

            if token_response.status_code != 200:
                logger.error("[Playground上传] 获取token失败: HTTP {token_response.status_code}")
                continue

            token_result = token_response.json()
            if token_result.get("code") != 0:
                logger.error(
                    "[Playground上传] 获取token失败: {token_result.get('msg', '未知错误')}"
                )
                continue

            upload_info = token_result.get("data", {})
            upload_url = upload_info.get("url")
            token = upload_info.get("token")
            key = upload_info.get("key")
            domain = upload_info.get("domain")

            if not all([upload_url, token, key, domain]):
                logger.error("[Playground上传] 上传token响应数据不完整")
                continue

            # 第二步：上传文件到七牛云
            file.seek(0)  # 重置文件指针
            files_data = {"file": (filename, file, f"image/{ext}")}
            form_data = {"key": key, "token": token}

            upload_response = requests.post(
                url=upload_url, files=files_data, data=form_data, proxies=proxies, timeout=60
            )

            if upload_response.status_code not in [200, 204]:
                logger.error("[Playground上传] 上传文件失败: HTTP {upload_response.status_code}")
                continue

            # 构建云端URL
            cloud_url = f"{domain.rstrip('/')}/{key}"
            logger.info(f"✅ [Playground上传] 上传成功: {cloud_url}")

            uploaded_files.append(
                {"url": cloud_url, "filename": filename, "original_filename": filename}
            )

        if not uploaded_files:
            return jsonify({"status": "error", "message": "没有成功上传的图片"}), 400

        return jsonify(
            {
                "status": "success",
                "data": uploaded_files if len(uploaded_files) > 1 else uploaded_files[0],
            }
        )

    except Exception as e:
        logger.error("[Playground上传] 上传图片失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"上传失败: {str(e)}"}), 500
