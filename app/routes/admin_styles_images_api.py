# -*- coding: utf-8 -*-
"""
管理后台风格图片API路由模块
提供风格图片的CRUD操作
"""

import logging

logger = logging.getLogger(__name__)
import os
import shutil
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required
from werkzeug.utils import secure_filename

from app.utils.admin_helpers import get_models, get_style_code_helpers

# 创建蓝图（不设置url_prefix，因为会注册到主蓝图下）
admin_styles_images_bp = Blueprint("admin_styles_images", __name__)

# ============================================================================
# 风格图片API
# ============================================================================


@admin_styles_images_bp.route("/images/<int:image_id>", methods=["GET"])
@login_required
def admin_get_image(image_id):
    """获取单个风格图片详情"""
    try:
        models = get_models(["StyleImage", "StyleCategory", "APITemplate", "APIProviderConfig"])
        if not models or not models.get("StyleImage"):
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleImage = models["StyleImage"]
        StyleCategory = models.get("StyleCategory")
        APITemplate = models.get("APITemplate")
        APIProviderConfig = models.get("APIProviderConfig")

        image = StyleImage.query.get_or_404(image_id)

        # 查询API模板信息
        api_template_info = None
        api_template_type = None

        if APITemplate:
            api_template = APITemplate.query.filter_by(style_image_id=image_id).first()
            if api_template and api_template.is_active is True:
                is_comfyui = bool(api_template.request_body_template)

                if not is_comfyui and api_template.api_config_id and APIProviderConfig:
                    api_config = APIProviderConfig.query.get(api_template.api_config_id)
                    if api_config and api_config.api_type == "runninghub-comfyui-workflow":
                        is_comfyui = True

                if is_comfyui:
                    api_template_type = "comfyui"
                    api_provider_name = "ComfyUI工作流"
                    if api_template.api_config_id and APIProviderConfig:
                        api_config = APIProviderConfig.query.get(api_template.api_config_id)
                        if api_config:
                            api_provider_name = api_config.name or "ComfyUI工作流"

                    api_template_info = {
                        "api_template_id": api_template.id,
                        "api_config_id": api_template.api_config_id,
                        "api_provider": api_provider_name,
                        "api_type": "comfyui",
                    }
                else:
                    api_template_type = "api"
                    api_provider_name = "已配置"
                    if api_template.api_config_id and APIProviderConfig:
                        api_config = APIProviderConfig.query.get(api_template.api_config_id)
                        if api_config:
                            api_provider_name = api_config.name or "已配置"

                    api_template_info = {
                        "api_template_id": api_template.id,
                        "api_config_id": api_template.api_config_id,
                        "api_provider": api_provider_name,
                        "api_type": "api",
                    }

        # 获取分类信息
        category_info = None
        if StyleCategory and image.category_id:
            category = StyleCategory.query.get(image.category_id)
            if category:
                category_info = {"id": category.id, "name": category.name, "code": category.code}

        result = {
            "id": image.id,
            "category_id": image.category_id,
            "subcategory_id": image.subcategory_id,
            "category": category_info,
            "name": image.name,
            "code": image.code,
            "description": image.description,
            "image_url": image.image_url,
            "design_image_url": image.design_image_url or "",
            "sort_order": image.sort_order,
            "is_active": image.is_active,
            "created_at": image.created_at.isoformat() if image.created_at else None,
            # AI工作流配置字段
            "is_ai_enabled": image.is_ai_enabled,
            "workflow_name": image.workflow_name or "",
            "workflow_file": image.workflow_file or "",
            "workflow_input_ids": image.workflow_input_ids or "",
            "workflow_output_id": image.workflow_output_id or "",
            "workflow_ref_id": image.workflow_ref_id or "",
            "workflow_ref_image": image.workflow_ref_image or "",
            "workflow_custom_prompt_id": image.workflow_custom_prompt_id or "",
            "workflow_custom_prompt_content": image.workflow_custom_prompt_content or "",
            # API模板信息
            "api_template_id": api_template_info["api_template_id"] if api_template_info else None,
            "api_config_id": api_template_info["api_config_id"] if api_template_info else None,
            "api_provider": api_template_info["api_provider"] if api_template_info else None,
            "api_template_type": api_template_info["api_type"] if api_template_info else None,
        }

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        logger.info(f"获取图片详情失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取图片详情失败: {str(e)}"}), 500


@admin_styles_images_bp.route("/images", methods=["GET"])
def admin_get_images():
    """获取所有风格图片"""
    try:
        models = get_models(["StyleImage", "APITemplate", "APIProviderConfig"])
        if not models or not models.get("StyleImage"):
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleImage = models["StyleImage"]
        APITemplate = models.get("APITemplate")
        APIProviderConfig = models.get("APIProviderConfig")

        # 优化：添加分页支持
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # 查询风格图片（数据库层面分页）
        query = StyleImage.query

        # 支持筛选参数
        category_id = request.args.get("category_id", type=int)
        if category_id:
            query = query.filter_by(category_id=category_id)

        subcategory_id = request.args.get("subcategory_id", type=int)
        if subcategory_id:
            query = query.filter_by(subcategory_id=subcategory_id)

        is_active = request.args.get("is_active")
        if is_active is not None:
            is_active_bool = is_active.lower() == "true"
            query = query.filter_by(is_active=is_active_bool)

        search = request.args.get("search", "").strip()
        if search:
            from sqlalchemy import or_

            query = query.filter(
                or_(StyleImage.name.like(f"%{search}%"), StyleImage.code.like(f"%{search}%"))
            )

        # 分页查询
        pagination = query.order_by(StyleImage.sort_order).paginate(
            page=page, per_page=per_page, error_out=False
        )

        images = pagination.items

        # 优化N+1查询：批量查询所有图片的API模板
        image_ids = [image.id for image in images]
        api_templates_map = {}
        if APITemplate and image_ids:
            all_templates = APITemplate.query.filter(
                APITemplate.style_image_id.in_(image_ids)
            ).all()
            for template in all_templates:
                if template.style_image_id not in api_templates_map:
                    api_templates_map[template.style_image_id] = []
                api_templates_map[template.style_image_id].append(template)

        # 优化N+1查询：批量查询所有API配置
        api_config_ids = set()
        if APITemplate and image_ids:
            for templates in api_templates_map.values():
                for template in templates:
                    if template.api_config_id:
                        api_config_ids.add(template.api_config_id)

        api_configs_map = {}
        if APIProviderConfig and api_config_ids:
            all_configs = APIProviderConfig.query.filter(
                APIProviderConfig.id.in_(api_config_ids)
            ).all()
            for config in all_configs:
                api_configs_map[config.id] = config

        result = []
        for image in images:
            # 查询API模板信息（从批量查询的映射中获取，避免N+1查询）
            api_template_info = None
            api_template_type = None  # 'api' 或 'comfyui'

            if APITemplate:
                # 从批量查询的映射中获取API模板
                templates = api_templates_map.get(image.id, [])
                api_template = templates[0] if templates else None
                if api_template:
                    # 调试日志（对所有图片都输出，方便排查）
                    logger.info(f"🔍 图片ID {image.id} ({image.name}) API模板检查:")
                    logger.info(f"   - api_template存在: {api_template is not None}")
                    logger.info(
                        f"   - is_active: {api_template.is_active} (类型: {type(api_template.is_active)})"
                    )
                    logger.info(f"   - api_config_id: {api_template.api_config_id}")
                    logger.info(
                        f"   - request_body_template: {bool(api_template.request_body_template)}"
                    )

                    # 如果is_active不是True，输出警告
                    if api_template.is_active is not True:
                        logger.info(
                            f"   ⚠️ is_active不是True，当前值: {api_template.is_active}, 类型: {type(api_template.is_active)}"
                        )

                # 关键修复：检查 is_active，但也要考虑保存后立即查询的情况
                # 使用显式的True比较，避免None或False的情况
                if api_template and api_template.is_active is True:
                    # is_active 为 True，继续处理
                    # 判断是ComfyUI工作流还是普通API
                    is_comfyui = bool(api_template.request_body_template)

                    if not is_comfyui and api_template.api_config_id and APIProviderConfig:
                        api_config = APIProviderConfig.query.get(api_template.api_config_id)
                        if api_config and api_config.api_type == "runninghub-comfyui-workflow":
                            is_comfyui = True

                    if is_comfyui:
                        api_template_type = "comfyui"
                        # ComfyUI工作流
                        api_provider_name = "ComfyUI工作流"
                        if api_template.api_config_id and APIProviderConfig:
                            # 从批量查询的映射中获取API配置（避免N+1查询）
                            api_config = api_configs_map.get(api_template.api_config_id)
                            if api_config:
                                api_provider_name = api_config.name or "ComfyUI工作流"

                        api_template_info = {
                            "api_template_id": api_template.id,
                            "api_config_id": api_template.api_config_id,
                            "api_provider": api_provider_name,
                            "api_type": "comfyui",
                        }
                    else:
                        api_template_type = "api"
                        # 普通API编辑
                        api_provider_name = "已配置"
                        if api_template.api_config_id and APIProviderConfig:
                            # 从批量查询的映射中获取API配置（避免N+1查询）
                            api_config = api_configs_map.get(api_template.api_config_id)
                            if api_config:
                                api_provider_name = api_config.name or "已配置"

                        api_template_info = {
                            "api_template_id": api_template.id,
                            "api_config_id": api_template.api_config_id,
                            "api_provider": api_provider_name,
                            "api_type": "api",
                        }
                elif api_template and not api_template.is_active:
                    logger.info(
                        f"   ⚠️ 图片ID {image.id} ({image.name}) API模板存在但is_active=False，跳过"
                    )

            result.append(
                {
                    "id": image.id,
                    "category_id": image.category_id,
                    "subcategory_id": image.subcategory_id,
                    "name": image.name,
                    "code": image.code,
                    "description": image.description,
                    "image_url": image.image_url,
                    "design_image_url": image.design_image_url or "",
                    "sort_order": image.sort_order,
                    "is_active": image.is_active,
                    "created_at": image.created_at.isoformat(),
                    # AI工作流配置字段
                    "is_ai_enabled": image.is_ai_enabled,
                    "workflow_name": image.workflow_name or "",
                    "workflow_file": image.workflow_file or "",
                    "workflow_input_ids": image.workflow_input_ids or "",
                    "workflow_output_id": image.workflow_output_id or "",
                    "workflow_ref_id": image.workflow_ref_id or "",
                    "workflow_ref_image": image.workflow_ref_image or "",
                    "workflow_custom_prompt_id": image.workflow_custom_prompt_id or "",
                    "workflow_custom_prompt_content": image.workflow_custom_prompt_content or "",
                    # API模板信息
                    "api_template_id": (
                        api_template_info["api_template_id"] if api_template_info else None
                    ),
                    "api_config_id": (
                        api_template_info["api_config_id"] if api_template_info else None
                    ),
                    "api_provider": (
                        api_template_info["api_provider"] if api_template_info else None
                    ),
                    "api_template_type": (
                        api_template_info["api_type"] if api_template_info else None
                    ),
                }
            )

        # 调试：检查"西装"的数据
        xizhuang_data = next((img for img in result if img.get("name") == "西装"), None)
        if xizhuang_data:
            logger.info("🔍 返回数据中'西装'的API模板信息:")
            logger.info(f"   - api_template_id: {xizhuang_data.get('api_template_id')}")
            logger.info(f"   - api_config_id: {xizhuang_data.get('api_config_id')}")
            logger.info(f"   - api_provider: {xizhuang_data.get('api_provider')}")
            logger.info(f"   - api_template_type: {xizhuang_data.get('api_template_type')}")

        return jsonify(
            {
                "status": "success",
                "data": result,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取图片失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "获取图片失败"}), 500


@admin_styles_images_bp.route("/images", methods=["POST"])
@login_required
def admin_create_image():
    """创建风格图片"""
    try:
        models = get_models(["StyleCategory", "StyleImage", "db"])
        if not models or not models.get("StyleImage"):
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        db = models["db"]
        helpers = get_style_code_helpers()
        if not helpers:
            return jsonify({"status": "error", "message": "风格代码辅助函数未初始化"}), 500

        _sanitize_style_code = helpers["_sanitize_style_code"]
        _build_style_code = helpers["_build_style_code"]
        _ensure_unique_style_code = helpers["_ensure_unique_style_code"]

        data = request.get_json()

        # 检查必填字段
        required_fields = ["category_id", "name", "image_url"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400

        # 检查分类是否存在
        category = StyleCategory.query.get(data["category_id"])
        if not category:
            return jsonify({"status": "error", "message": "分类不存在"}), 400

        # 生成唯一风格代码
        raw_code = (data.get("code") or "").strip()
        sanitized_code = _sanitize_style_code(raw_code)
        if sanitized_code and sanitized_code == _sanitize_style_code(category.code):
            sanitized_code = ""
        if not sanitized_code:
            sanitized_code = _build_style_code(data["name"], category.code)
        final_code = _ensure_unique_style_code(sanitized_code)

        # 创建图片
        image = StyleImage(
            category_id=data["category_id"],
            subcategory_id=data.get("subcategory_id") or None,
            name=data["name"],
            code=final_code,
            description=data.get("description", ""),
            image_url=data["image_url"],
            design_image_url=data.get("design_image_url") or None,
            sort_order=data.get("sort_order", 0),
            is_active=data.get("is_active", True),
        )

        db.session.add(image)
        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": "图片创建成功",
                "data": {"id": image.id, "name": image.name, "code": image.code},
            }
        )

    except Exception as e:
        logger.info(f"创建图片失败: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": "创建图片失败"}), 500


@admin_styles_images_bp.route("/images/<int:image_id>", methods=["PUT"])
@login_required
def admin_update_image(image_id):
    """更新风格图片"""
    try:
        models = get_models(["StyleCategory", "StyleImage", "db"])
        if not models or not models.get("StyleImage"):
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        db = models["db"]
        helpers = get_style_code_helpers()
        if not helpers:
            return jsonify({"status": "error", "message": "风格代码辅助函数未初始化"}), 500

        _sanitize_style_code = helpers["_sanitize_style_code"]
        _build_style_code = helpers["_build_style_code"]
        _ensure_unique_style_code = helpers["_ensure_unique_style_code"]

        image = StyleImage.query.get_or_404(image_id)
        data = request.get_json()

        # 处理分类变更
        new_category_id = data.get("category_id", image.category_id)
        category = StyleCategory.query.get(new_category_id)
        if not category:
            return jsonify({"status": "error", "message": "分类不存在"}), 400

        # 更新字段
        if "category_id" in data:
            image.category_id = data["category_id"]
        if "subcategory_id" in data:
            image.subcategory_id = data["subcategory_id"] if data["subcategory_id"] else None
        if "name" in data:
            image.name = data["name"]
        if "description" in data:
            image.description = data["description"]
        if "image_url" in data:
            image.image_url = data["image_url"]
        if "design_image_url" in data:
            image.design_image_url = data["design_image_url"] or None
        if "sort_order" in data:
            image.sort_order = data["sort_order"]
        if "is_active" in data:
            image.is_active = data["is_active"]

        # AI工作流配置字段
        if "is_ai_enabled" in data:
            image.is_ai_enabled = data["is_ai_enabled"]

        if "workflow_name" in data:
            image.workflow_name = data["workflow_name"] or None

        if "workflow_file" in data:
            old_workflow_file = image.workflow_file
            new_workflow_file = data["workflow_file"] or None

            if not new_workflow_file:
                new_workflow_file = old_workflow_file
            elif new_workflow_file == old_workflow_file:
                new_workflow_file = old_workflow_file
            elif (
                new_workflow_file and image.workflow_name and new_workflow_file != old_workflow_file
            ):
                try:
                    workflows_dir = "workflows"
                    os.makedirs(workflows_dir, exist_ok=True)

                    safe_name = secure_filename(image.workflow_name)
                    new_filename = f"{safe_name}.json"
                    new_filepath = os.path.join(workflows_dir, new_filename)

                    if os.path.exists(new_filepath) and new_filename != new_workflow_file:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{safe_name}_{timestamp}.json"
                        new_filepath = os.path.join(workflows_dir, new_filename)

                    old_filepath = os.path.join(workflows_dir, new_workflow_file)
                    if os.path.exists(old_filepath) and old_filepath != new_filepath:
                        shutil.move(old_filepath, new_filepath)
                        new_workflow_file = new_filename
                        logger.info(f"✅ 工作流文件已重命名: {new_workflow_file} -> {new_filename}")
                    elif not os.path.exists(old_filepath):
                        if os.path.exists(new_filepath):
                            new_workflow_file = new_filename
                    else:
                        new_workflow_file = new_filename

                except Exception as e:
                    logger.warning("重命名工作流文件失败: {str(e)}")

            image.workflow_file = new_workflow_file
        if "workflow_input_ids" in data:
            image.workflow_input_ids = data["workflow_input_ids"] or None
        if "workflow_output_id" in data:
            image.workflow_output_id = data["workflow_output_id"] or None
        if "workflow_ref_id" in data:
            image.workflow_ref_id = data["workflow_ref_id"] or None
        if "workflow_ref_image" in data:
            image.workflow_ref_image = data["workflow_ref_image"] or None
        if "workflow_custom_prompt_id" in data:
            image.workflow_custom_prompt_id = data["workflow_custom_prompt_id"] or None
        if "workflow_custom_prompt_content" in data:
            image.workflow_custom_prompt_content = data["workflow_custom_prompt_content"] or None

        # 当 code 为空或与当前分类重复时自动重新生成
        requested_code = data.get("code") if "code" in data else image.code
        sanitized_code = _sanitize_style_code(requested_code)
        if sanitized_code and sanitized_code == _sanitize_style_code(category.code):
            sanitized_code = ""
        if not sanitized_code:
            sanitized_code = _build_style_code(image.name, category.code)
        final_code = _ensure_unique_style_code(sanitized_code, image_id=image_id)
        image.code = final_code

        db.session.commit()

        return jsonify({"status": "success", "message": "图片更新成功"})

    except Exception as e:
        logger.info(f"更新图片失败: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": "更新图片失败"}), 500


@admin_styles_images_bp.route("/images/<int:image_id>", methods=["DELETE"])
def admin_delete_image(image_id):
    """删除风格图片"""
    try:
        models = get_models(["StyleImage", "db"])
        if not models or not models.get("StyleImage"):
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleImage = models["StyleImage"]
        db = models["db"]

        image = StyleImage.query.get_or_404(image_id)

        db.session.delete(image)
        db.session.commit()

        return jsonify({"status": "success", "message": "图片删除成功"})

    except Exception as e:
        logger.info(f"删除图片失败: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": "删除图片失败"}), 500
