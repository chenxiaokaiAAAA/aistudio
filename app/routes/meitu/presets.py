# -*- coding: utf-8 -*-
"""
美图API预设管理模块
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_api_required
from app.utils.performance_optimizer import ResponseOptimizer
from app.utils.type_hints import FlaskResponse, JsonDict

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("meitu_presets", __name__)


@bp.route("/api/presets", methods=["GET"])
@login_required
@admin_api_required
def get_meitu_presets() -> FlaskResponse:
    """
    获取美图API预设列表

    Returns:
        FlaskResponse: JSON响应，包含预设列表和分页信息
    """
    try:
        models = get_models(["MeituAPIPreset", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        MeituAPIPreset = models["MeituAPIPreset"]

        # 优化：添加分页支持
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        # 查询预设（数据库层面分页）
        query = MeituAPIPreset.query

        # 支持筛选参数
        search = request.args.get("search", "").strip()
        if search:
            query = query.filter(
                or_(
                    MeituAPIPreset.name.like(f"%{search}%"),
                    MeituAPIPreset.description.like(f"%{search}%"),
                )
            )

        # 分页查询
        pagination = query.order_by(MeituAPIPreset.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        presets = pagination.items

        # 优化N+1查询：批量查询所有风格分类和风格图片
        StyleCategory = models.get("StyleCategory")
        StyleImage = models.get("StyleImage")

        category_ids = [p.style_category_id for p in presets if p.style_category_id]
        image_ids = [p.style_image_id for p in presets if p.style_image_id]

        categories_map = {}
        if category_ids and StyleCategory:
            all_categories = StyleCategory.query.filter(StyleCategory.id.in_(category_ids)).all()
            for category in all_categories:
                categories_map[category.id] = category

        images_map = {}
        if image_ids and StyleImage:
            all_images = StyleImage.query.filter(StyleImage.id.in_(image_ids)).all()
            for image in all_images:
                images_map[image.id] = image
                # 同时收集图片的分类ID
                if image.category_id:
                    category_ids.append(image.category_id)

        # 再次查询图片分类（如果之前没有查询过）
        if category_ids and StyleCategory:
            additional_categories = StyleCategory.query.filter(
                StyleCategory.id.in_(category_ids)
            ).all()
            for category in additional_categories:
                if category.id not in categories_map:
                    categories_map[category.id] = category

        preset_list = []
        for preset in presets:
            if preset.style_category_id:
                # 映射到整个分类（从批量查询的映射中获取，避免N+1查询）
                mapping_type = "category"
                category = categories_map.get(preset.style_category_id)
                category_name = category.name if category else "N/A"
                image_name = None
            else:
                # 映射到单个图片（从批量查询的映射中获取，避免N+1查询）
                mapping_type = "image"
                image = images_map.get(preset.style_image_id) if preset.style_image_id else None
                if image:
                    category = categories_map.get(image.category_id) if image.category_id else None
                    category_name = category.name if category else "N/A"
                    image_name = image.name
                else:
                    category_name = "N/A"
                    image_name = "N/A"

            preset_list.append(
                {
                    "id": preset.id,
                    "style_category_id": preset.style_category_id,
                    "style_image_id": preset.style_image_id,
                    "mapping_type": mapping_type,
                    "category_name": category_name,
                    "image_name": image_name,
                    "preset_id": preset.preset_id,
                    "preset_name": preset.preset_name,
                    "description": preset.description,
                    "is_active": preset.is_active,
                }
            )

        # 使用响应优化（添加缓存头，5分钟缓存）
        response_data: JsonDict = {
            "status": "success",
            "data": preset_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }
        return ResponseOptimizer.optimize_json_response(response_data, max_age=300)

    except Exception as e:
        logger.info(f"获取预设列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取预设列表失败: {str(e)}"}), 500


@bp.route("/api/presets/<int:preset_id>", methods=["GET"])
@login_required
@admin_api_required
def get_meitu_preset(preset_id: int) -> FlaskResponse:
    """
    获取单个预设详情

    Args:
        preset_id: 预设ID

    Returns:
        FlaskResponse: JSON响应，包含预设详情
    """
    try:
        models = get_models(["MeituAPIPreset", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        MeituAPIPreset = models["MeituAPIPreset"]

        preset = MeituAPIPreset.query.get(preset_id)
        if not preset:
            return jsonify({"status": "error", "message": "预设不存在"}), 404

        # 使用响应优化（添加缓存头，5分钟缓存）
        response_data: JsonDict = {
            "status": "success",
            "data": {
                "id": preset.id,
                "style_category_id": preset.style_category_id,
                "style_image_id": preset.style_image_id,
                "mapping_type": "category" if preset.style_category_id else "image",
                "preset_id": preset.preset_id,
                "preset_name": preset.preset_name,
                "description": preset.description,
                "is_active": preset.is_active,
            },
        }
        return ResponseOptimizer.optimize_json_response(response_data, max_age=300)

    except Exception as e:
        logger.info(f"获取预设详情失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取预设详情失败: {str(e)}"}), 500


@bp.route("/api/presets", methods=["POST"])
@login_required
@admin_api_required
def create_meitu_preset():
    """创建美图API预设"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求数据为空"}), 400

        models = get_models(["MeituAPIPreset", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        MeituAPIPreset = models["MeituAPIPreset"]

        # 验证：必须指定分类或图片之一，但不能同时指定
        style_category_id = data.get("style_category_id")
        style_image_id = data.get("style_image_id")

        if not style_category_id and not style_image_id:
            return jsonify({"status": "error", "message": "必须指定风格分类或风格图片"}), 400

        if style_category_id and style_image_id:
            return (
                jsonify(
                    {"status": "error", "message": "不能同时指定风格分类和风格图片，请选择其一"}
                ),
                400,
            )

        preset = MeituAPIPreset(
            style_category_id=style_category_id if style_category_id else None,
            style_image_id=style_image_id if style_image_id else None,
            preset_id=data.get("preset_id", ""),
            preset_name=data.get("preset_name", ""),
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
        )

        db.session.add(preset)
        db.session.commit()

        return jsonify({"status": "success", "message": "预设创建成功", "data": {"id": preset.id}})

    except Exception as e:
        logger.info(f"创建预设失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"创建预设失败: {str(e)}"}), 500


@bp.route("/api/presets/<int:preset_id>", methods=["PUT"])
@login_required
@admin_api_required
def update_meitu_preset(preset_id):
    """更新美图API预设"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求数据为空"}), 400

        models = get_models(["MeituAPIPreset", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        MeituAPIPreset = models["MeituAPIPreset"]

        preset = MeituAPIPreset.query.get(preset_id)
        if not preset:
            return jsonify({"status": "error", "message": "预设不存在"}), 404

        # 验证：必须指定分类或图片之一，但不能同时指定
        style_category_id = data.get("style_category_id")
        style_image_id = data.get("style_image_id")

        if not style_category_id and not style_image_id:
            return jsonify({"status": "error", "message": "必须指定风格分类或风格图片"}), 400

        if style_category_id and style_image_id:
            return (
                jsonify(
                    {"status": "error", "message": "不能同时指定风格分类和风格图片，请选择其一"}
                ),
                400,
            )

        preset.style_category_id = style_category_id if style_category_id else None
        preset.style_image_id = style_image_id if style_image_id else None
        preset.preset_id = data.get("preset_id", preset.preset_id)
        preset.preset_name = data.get("preset_name", preset.preset_name)
        preset.description = data.get("description", preset.description)
        preset.is_active = data.get("is_active", preset.is_active)

        db.session.commit()

        return jsonify({"status": "success", "message": "预设更新成功", "data": {"id": preset.id}})

    except Exception as e:
        logger.info(f"更新预设失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"更新预设失败: {str(e)}"}), 500


@bp.route("/api/presets/<int:preset_id>", methods=["DELETE"])
@login_required
@admin_api_required
def delete_meitu_preset(preset_id):
    """删除美图API预设"""
    try:
        models = get_models(["MeituAPIPreset", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        MeituAPIPreset = models["MeituAPIPreset"]

        preset = MeituAPIPreset.query.get(preset_id)
        if not preset:
            return jsonify({"status": "error", "message": "预设不存在"}), 404

        db.session.delete(preset)
        db.session.commit()

        return jsonify({"status": "success", "message": "预设删除成功"})

    except Exception as e:
        logger.info(f"删除预设失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"删除预设失败: {str(e)}"}), 500


@bp.route("/api/style-categories", methods=["GET"])
@login_required
def get_style_categories() -> FlaskResponse:
    """
    获取风格分类列表（用于预设配置）

    Returns:
        FlaskResponse: JSON响应，包含风格分类列表
    """
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models(["StyleCategory"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        StyleCategory = models["StyleCategory"]

        categories = StyleCategory.query.filter_by(is_active=True).all()
        category_list = [{"id": cat.id, "name": cat.name} for cat in categories]

        return jsonify({"status": "success", "data": category_list})

    except Exception as e:
        logger.info(f"获取风格分类列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取风格分类列表失败: {str(e)}"}), 500


@bp.route("/api/style-images", methods=["GET"])
@login_required
def get_style_images() -> FlaskResponse:
    """
    获取风格图片列表（用于预设配置）

    Returns:
        FlaskResponse: JSON响应，包含风格图片列表和分页信息
    """
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models(["StyleImage", "StyleCategory"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        StyleImage = models["StyleImage"]
        StyleCategory = models["StyleCategory"]

        # 优化：添加分页支持
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        # 查询风格图片（数据库层面分页）
        query = StyleImage.query.filter_by(is_active=True)

        # 支持筛选参数
        category_id = request.args.get("category_id", type=int)
        if category_id:
            query = query.filter_by(category_id=category_id)

        # 分页查询
        pagination = query.order_by(StyleImage.sort_order).paginate(
            page=page, per_page=per_page, error_out=False
        )

        style_images = pagination.items

        # 优化N+1查询：批量查询所有风格分类
        category_ids = [img.category_id for img in style_images if img.category_id]
        categories_map = {}
        if category_ids:
            all_categories = StyleCategory.query.filter(StyleCategory.id.in_(category_ids)).all()
            for category in all_categories:
                categories_map[category.id] = category

        image_list = []
        for img in style_images:
            # 从批量查询的映射中获取分类（避免N+1查询）
            category = categories_map.get(img.category_id) if img.category_id else None
            image_list.append(
                {
                    "id": img.id,
                    "name": img.name,
                    "category_id": img.category_id,
                    "category_name": category.name if category else "N/A",
                }
            )

        # 使用响应优化（添加缓存头，5分钟缓存）
        response_data: JsonDict = {
            "status": "success",
            "data": image_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }
        return ResponseOptimizer.optimize_json_response(response_data, max_age=300)

    except Exception as e:
        logger.info(f"获取风格图片列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取风格图片列表失败: {str(e)}"}), 500
