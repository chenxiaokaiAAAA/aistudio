# -*- coding: utf-8 -*-
"""
AI任务管理API路由模块
提供AI任务的CRUD操作、上传、重试等功能
"""

import logging

logger = logging.getLogger(__name__)
import json
import os
import sys
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models

# 创建蓝图
ai_tasks_api_bp = Blueprint("ai_tasks_api", __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gi", "bmp", "webp"}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@ai_tasks_api_bp.route("/api/tasks", methods=["GET"])
@login_required
def get_ai_tasks():
    """获取AI任务列表"""
    try:
        models = get_models(
            ["AITask", "Order", "StyleCategory", "StyleImage", "APIProviderConfig", "db"]
        )
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        AITask = models["AITask"]
        Order = models["Order"]
        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        APIProviderConfig = models["APIProviderConfig"]

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        status = request.args.get("status")
        order_number = request.args.get("order_number")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        image_type = request.args.get("image_type")

        # 构建查询（使用joinedload预加载关联数据，避免N+1查询问题）
        from sqlalchemy.orm import joinedload

        query = AITask.query.options(
            joinedload(AITask.style_category), joinedload(AITask.style_image)
        )

        # 检查是否只查询Playground任务（通过order_number前缀或source_type）
        playground_only = request.args.get("playground_only", "false").lower() == "true"
        if playground_only:
            # 只查询Playground任务（订单号以PLAY_开头）
            # 如果用户已登录，可以进一步筛选只显示当前用户的任务
            query = query.join(Order, AITask.order_id == Order.id).filter(
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
        if image_type:
            query = query.filter_by(input_image_type=image_type)

        # 分页
        pagination = query.order_by(AITask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # 优化N+1查询：批量查询所有APIProviderConfig
        tasks_items = pagination.items
        api_config_ids = []
        api_info_list = []
        for task in tasks_items:
            if task.processing_log:
                try:
                    parsed_log = json.loads(task.processing_log)
                    if isinstance(parsed_log, dict) and parsed_log.get("api_config_id"):
                        api_config_ids.append(parsed_log["api_config_id"])
                        api_info_list.append((task, parsed_log))
                except Exception:
                    pass

        # 批量查询APIProviderConfig
        api_configs_map = {}
        if api_config_ids and APIProviderConfig:
            api_configs = APIProviderConfig.query.filter(
                APIProviderConfig.id.in_(api_config_ids)
            ).all()
            api_configs_map = {config.id: config for config in api_configs}

        tasks = []
        for task in tasks_items:
            # 获取关联信息（已通过joinedload预加载，不会触发额外查询）
            style_category_name = task.style_category.name if task.style_category else None
            style_image_name = task.style_image.name if task.style_image else None

            # 状态文本映射
            status_map = {
                "pending": "待处理",
                "processing": "处理中",
                "completed": "已完成",
                "failed": "失败",
                "cancelled": "已取消",
            }

            # 获取任务ID（comfyui_prompt_id或processing_log中的task_id）
            task_id = task.comfyui_prompt_id
            api_task_id = None  # API返回的任务ID（用于异步任务）
            api_info = {}
            if task.processing_log:
                try:
                    parsed_log = json.loads(task.processing_log)
                    # 检查是否是字典类型，如果是list则跳过
                    if isinstance(parsed_log, dict):
                        api_info = parsed_log
                        if not task_id:
                            task_id = api_info.get("task_id") or api_info.get("id")
                        # 提取API任务ID（异步API返回的taskId，如RunningHub）
                        api_task_id = (
                            api_info.get("api_task_id")
                            or api_info.get("taskId")
                            or api_info.get("task_id")
                        )
                    elif isinstance(parsed_log, list):
                        # 如果是list，记录警告但继续处理
                        logger.warning("任务 {task.id} 的 processing_log 是 list 类型，跳过解析")
                except Exception:
                    pass
            # 如果没有从processing_log中提取到，尝试从comfyui_prompt_id获取
            if not api_task_id and task.comfyui_prompt_id:
                api_task_id = task.comfyui_prompt_id
            # 如果还没有，尝试从notes中提取（T8Star格式：T8_API_TASK_ID:xxx）
            if not api_task_id and task.notes:
                try:
                    if "T8_API_TASK_ID:" in task.notes:
                        api_task_id = task.notes.split("T8_API_TASK_ID:")[1].split("|")[0].strip()
                except Exception:
                    pass
            if not task_id:
                task_id = f"TASK_{task.id}"

            # 获取API服务商信息（从批量查询的映射中获取，避免N+1查询）
            api_provider_name = None
            if isinstance(api_info, dict) and api_info.get("api_config_id"):
                api_config = api_configs_map.get(api_info["api_config_id"])
                if api_config:
                    api_provider_name = api_config.name
            elif api_info.get("api_config_name"):
                api_provider_name = api_info["api_config_name"]

            # 计算完成耗时（秒）
            duration_seconds = None
            if task.completed_at and task.created_at:
                duration = task.completed_at - task.created_at
                duration_seconds = int(duration.total_seconds())

            # 获取请求参数和结果数据
            request_params = api_info.get("request_params")
            response_data = api_info.get("response_data")

            task_data = {
                "id": task.id,
                "task_id": task_id,  # 添加任务ID
                "api_task_id": api_task_id,  # API返回的任务ID（用于异步任务，如RunningHub的taskId）
                "order_id": task.order_id,
                "order_number": task.order_number,
                # 统一路径格式（将反斜杠转为正斜杠）
                "input_image_path": (
                    task.input_image_path.replace("\\", "/") if task.input_image_path else None
                ),
                "input_image_type": task.input_image_type,
                "output_image_path": (
                    task.output_image_path.replace("\\", "/") if task.output_image_path else None
                ),
                "status": task.status,
                "status_text": status_map.get(task.status, task.status),
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "estimated_completion_time": (
                    task.estimated_completion_time.isoformat()
                    if task.estimated_completion_time
                    else None
                ),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message,
                "retry_count": task.retry_count,
                "notes": task.notes,  # 关键修复：添加notes字段，用于显示重试信息
                "workflow_name": task.workflow_name,
                "style_category_name": style_category_name,
                "style_image_name": style_image_name,
                # 新增字段
                "api_provider_name": api_provider_name,
                "duration_seconds": duration_seconds,
                "request_params": request_params,
                "response_data": response_data,
            }
            tasks.append(task_data)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "tasks": tasks,
                    "total": pagination.total,
                    "page": page,
                    "per_page": per_page,
                    "pages": pagination.pages,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取AI任务列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务列表失败: {str(e)}"}), 500


@ai_tasks_api_bp.route("/api/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_ai_task_detail(task_id):
    """获取AI任务详情"""
    try:
        models = get_models(["AITask", "StyleCategory", "StyleImage", "db"])
        if not models:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        db = models["db"]
        AITask = models["AITask"]
        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]

        # 使用joinedload预加载关联数据，避免N+1查询
        from sqlalchemy.orm import joinedload

        task = AITask.query.options(
            joinedload(AITask.style_category), joinedload(AITask.style_image)
        ).get_or_404(task_id)

        # 获取关联信息（已通过joinedload预加载，不会触发额外查询）
        style_category_name = task.style_category.name if task.style_category else None
        style_image_name = task.style_image.name if task.style_image else None

        # 解析处理日志
        processing_log = []
        if task.processing_log:
            try:
                processing_log = json.loads(task.processing_log)
            except Exception:
                pass

        task_data = {
            "id": task.id,
            "order_id": task.order_id,
            "order_number": task.order_number,
            "workflow_name": task.workflow_name,
            "workflow_file": task.workflow_file,
            "style_category_id": task.style_category_id,
            "style_category_name": style_category_name,
            "style_image_id": task.style_image_id,
            "style_image_name": style_image_name,
            # 统一路径格式（将反斜杠转为正斜杠，并处理路径）
            "input_image_path": (
                task.input_image_path.replace("\\", "/") if task.input_image_path else None
            ),
            "input_image_type": task.input_image_type,
            "output_image_path": (
                task.output_image_path.replace("\\", "/") if task.output_image_path else None
            ),
            "status": task.status,
            "comfyui_prompt_id": task.comfyui_prompt_id,
            "comfyui_node_id": task.comfyui_node_id,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "estimated_completion_time": (
                task.estimated_completion_time.isoformat()
                if task.estimated_completion_time
                else None
            ),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "error_code": task.error_code,
            "retry_count": task.retry_count,
            "processing_log": processing_log,
            "comfyui_response": (
                json.loads(task.comfyui_response) if task.comfyui_response else None
            ),
            "notes": task.notes,
        }

        return jsonify({"status": "success", "data": task_data})

    except Exception as e:
        logger.info(f"获取AI任务详情失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务详情失败: {str(e)}"}), 500
