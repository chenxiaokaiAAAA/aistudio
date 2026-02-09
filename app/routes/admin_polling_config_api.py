# -*- coding: utf-8 -*-
"""
轮询配置管理API路由模块
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
admin_polling_config_api_bp = Blueprint(
    "admin_polling_config_api", __name__, url_prefix="/api/admin/polling-config"
)


@admin_polling_config_api_bp.route("/list", methods=["GET"])
@login_required
def get_polling_configs():
    """获取所有轮询配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        PollingConfig = models["PollingConfig"]

        # 优化：虽然配置数量通常很少，但为了保持一致性，仍然支持分页
        # 但默认返回所有配置（因为配置数量通常<10）
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 100))  # 默认100，足够覆盖所有配置

        # 查询配置（数据库层面分页）
        query = PollingConfig.query

        # 支持筛选参数
        task_type = request.args.get("task_type", "")
        if task_type:
            query = query.filter_by(task_type=task_type)

        # 分页查询
        pagination = query.order_by(PollingConfig.id).paginate(
            page=page, per_page=per_page, error_out=False
        )

        configs = pagination.items
        config_dict = {config.task_type: config.to_dict() for config in configs}

        # 确保返回所有三种任务类型的配置（缺失的用默认值）
        default_configs = {
            "api_task": {
                "id": None,
                "task_type": "api_task",
                "task_type_name": "API任务",
                "polling_interval": 10,
                "polling_interval_with_tasks": 5,
                "wait_before_polling": 30,
                "wait_before_polling_test": 0,
                "timeout_seconds": 3600,
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            },
            "workflow_task": {
                "id": None,
                "task_type": "workflow_task",
                "task_type_name": "工作流任务",
                "polling_interval": 10,
                "polling_interval_with_tasks": 5,
                "wait_before_polling": 30,
                "wait_before_polling_test": 0,
                "timeout_seconds": 3600,
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            },
            "comfyui_task": {
                "id": None,
                "task_type": "comfyui_task",
                "task_type_name": "API-ComfyUI工作流任务",
                "polling_interval": 10,
                "polling_interval_with_tasks": 5,
                "wait_before_polling": 30,
                "wait_before_polling_test": 0,
                "timeout_seconds": 3600,
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            },
        }

        # 合并数据库配置和默认配置
        result = []
        for task_type in ["api_task", "workflow_task", "comfyui_task"]:
            if task_type in config_dict:
                result.append(config_dict[task_type])
            else:
                result.append(default_configs[task_type])

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
        logger.info(f"获取轮询配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取轮询配置失败: {str(e)}"}), 500


@admin_polling_config_api_bp.route("/<int:config_id>", methods=["GET"])
@login_required
def get_polling_config(config_id):
    """获取单个轮询配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        PollingConfig = models["PollingConfig"]

        config = PollingConfig.query.get(config_id)
        if not config:
            return jsonify({"status": "error", "message": "轮询配置不存在"}), 404

        return jsonify({"status": "success", "data": config.to_dict()})

    except Exception as e:
        logger.info(f"获取轮询配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取轮询配置失败: {str(e)}"}), 500


@admin_polling_config_api_bp.route("/save", methods=["POST"])
@login_required
def save_polling_config():
    """保存轮询配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求数据为空"}), 400

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        PollingConfig = models["PollingConfig"]
        db = models["db"]

        config_id = data.get("id")
        # 处理空字符串或None的情况
        if config_id == "" or config_id is None:
            config_id = None

        if config_id:
            # 更新现有配置
            config = PollingConfig.query.get(config_id)
            if not config:
                return jsonify({"status": "error", "message": "轮询配置不存在"}), 404
        else:
            # 创建新配置
            task_type = data.get("task_type")
            if not task_type:
                return jsonify({"status": "error", "message": "任务类型不能为空"}), 400

            # 检查是否已存在
            existing = PollingConfig.query.filter_by(task_type=task_type).first()
            if existing:
                return (
                    jsonify({"status": "error", "message": f"任务类型 {task_type} 的配置已存在"}),
                    400,
                )

            config = PollingConfig(task_type=task_type)
            db.session.add(config)

        # 更新字段
        if "task_type_name" in data:
            config.task_type_name = data["task_type_name"]
        if "polling_interval" in data:
            config.polling_interval = int(data["polling_interval"])
        if "polling_interval_with_tasks" in data:
            config.polling_interval_with_tasks = int(data["polling_interval_with_tasks"])
        if "wait_before_polling" in data:
            config.wait_before_polling = int(data["wait_before_polling"])
        if "wait_before_polling_test" in data:
            config.wait_before_polling_test = int(data["wait_before_polling_test"])
        if "timeout_seconds" in data:
            config.timeout_seconds = int(data["timeout_seconds"])
        if "is_active" in data:
            config.is_active = bool(data["is_active"])

        config.updated_at = datetime.now()

        db.session.commit()

        return jsonify({"status": "success", "message": "保存成功", "data": config.to_dict()})

    except Exception as e:
        logger.info(f"保存轮询配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        db.session.rollback()
        return jsonify({"status": "error", "message": f"保存失败: {str(e)}"}), 500


@admin_polling_config_api_bp.route("/<int:config_id>", methods=["DELETE"])
@login_required
def delete_polling_config(config_id):
    """删除轮询配置"""
    try:
        if current_user.role not in ["admin"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        PollingConfig = models["PollingConfig"]
        db = models["db"]

        config = PollingConfig.query.get(config_id)
        if not config:
            return jsonify({"status": "error", "message": "轮询配置不存在"}), 404

        db.session.delete(config)
        db.session.commit()

        return jsonify({"status": "success", "message": "删除成功"})

    except Exception as e:
        logger.info(f"删除轮询配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        db.session.rollback()
        return jsonify({"status": "error", "message": f"删除失败: {str(e)}"}), 500
