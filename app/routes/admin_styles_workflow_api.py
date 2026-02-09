# -*- coding: utf-8 -*-
"""
管理后台风格工作流API路由模块
提供工作流测试、API模板管理等功能
"""

import base64
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlparse

import requests
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.routes.admin_styles_utils import _get_test_order_info
from app.utils.admin_helpers import get_models, get_style_code_helpers

logger = logging.getLogger(__name__)

# 创建蓝图（不设置url_prefix，因为会注册到主蓝图下）
admin_styles_workflow_bp = Blueprint("admin_styles_workflow", __name__)

# ============================================================================
# 工作流测试API
# ============================================================================


@admin_styles_workflow_bp.route("/test-workflow/<int:image_id>", methods=["POST"])
@login_required
def test_workflow(image_id):
    """测试工作流API调用"""
    try:
        # 检查权限
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        # 检查Playground使用次数限制
        models = get_models(
            [
                "StyleCategory",
                "StyleImage",
                "AIConfig",
                "User",
                "Order",
                "OrderImage",
                "AITask",
                "APITemplate",
                "db",
            ]
        )
        if models:
            db = models["db"]
            User = models["User"]
            user = User.query.get(current_user.id)

            if user:
                from datetime import date

                today = date.today()

                # 检查是否需要重置每日使用次数
                if hasattr(user, "playground_last_reset_date"):
                    if user.playground_last_reset_date != today:
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

                # 增加使用次数
                if hasattr(user, "playground_used_today"):
                    user.playground_used_today = (
                        getattr(user, "playground_used_today", 0) or 0
                    ) + 1
                    if (
                        not hasattr(user, "playground_last_reset_date")
                        or not user.playground_last_reset_date
                    ):
                        user.playground_last_reset_date = today
                    db.session.commit()

        # 检查Playground使用次数限制
        models = get_models(
            [
                "StyleCategory",
                "StyleImage",
                "AIConfig",
                "User",
                "Order",
                "OrderImage",
                "AITask",
                "APITemplate",
                "db",
            ]
        )
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        db = models["db"]
        User = models["User"]
        user = User.query.get(current_user.id)

        if user:
            from datetime import date

            today = date.today()

            # 检查是否需要重置每日使用次数
            if hasattr(user, "playground_last_reset_date"):
                if not user.playground_last_reset_date or user.playground_last_reset_date != today:
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
                                "message": f"今日Playground使用次数已达上限（{user.playground_daily_limit}次），请明日再试",
                            }
                        ),
                        403,
                    )

        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        AIConfig = models["AIConfig"]

        # 获取图片配置
        image = StyleImage.query.get_or_404(image_id)
        category = StyleCategory.query.get_or_404(image.category_id)

        # 获取工作流配置
        from app.services.workflow_service import (
            get_comfyui_config,
            get_workflow_config,
            load_workflow_file,
        )

        # 尝试从请求中获取临时配置
        data = request.get_json()
        temp_config = data.get("workflow_config") if data else None

        if temp_config:
            workflow_config = {
                "workflow_name": temp_config.get("workflow_name"),
                "workflow_file": temp_config.get("workflow_file"),
                "workflow_input_ids": temp_config.get("workflow_input_ids"),
                "workflow_output_id": temp_config.get("workflow_output_id"),
                "workflow_ref_id": temp_config.get("workflow_ref_id"),
                "workflow_ref_image": temp_config.get("workflow_ref_image"),
                "workflow_custom_prompt_id": temp_config.get("workflow_custom_prompt_id"),
                "workflow_custom_prompt_content": temp_config.get("workflow_custom_prompt_content"),
            }
            if not workflow_config.get("workflow_file"):
                return (
                    jsonify({"status": "error", "message": "工作流文件未配置，请先上传工作流文件"}),
                    400,
                )
            if not workflow_config.get("workflow_input_ids"):
                return jsonify({"status": "error", "message": "输入节点ID未配置"}), 400
            if not workflow_config.get("workflow_output_id"):
                return jsonify({"status": "error", "message": "输出节点ID未配置"}), 400
            # 处理workflow_input_ids（如果是字符串，转换为数组）
            if isinstance(workflow_config["workflow_input_ids"], str):
                try:
                    workflow_config["workflow_input_ids"] = json.loads(
                        workflow_config["workflow_input_ids"]
                    )
                except Exception:
                    workflow_config["workflow_input_ids"] = [
                        id.strip()
                        for id in workflow_config["workflow_input_ids"].split(",")
                        if id.strip()
                    ]
        else:
            workflow_config = get_workflow_config(
                category.id, image.id, db=db, StyleCategory=StyleCategory, StyleImage=StyleImage
            )

            if not workflow_config:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "工作流未启用或配置不存在。请确保：\n1. 分类已启用AI工作流\n2. 或图片已启用独立AI工作流\n3. 工作流文件、输入节点ID、输出节点ID已配置",
                        }
                    ),
                    400,
                )

        # 获取请求数据（支持多图）
        if not data or "image_data" not in data:
            return jsonify({"status": "error", "message": "缺少图片数据"}), 400

        # 处理base64图片数据（支持数组或单个）
        image_data_list = data["image_data"]
        if not isinstance(image_data_list, list):
            # 向后兼容：如果是单个图片，转换为数组
            image_data_list = [image_data_list]

        if len(image_data_list) == 0:
            return jsonify({"status": "error", "message": "请至少上传一张图片"}), 400

        # 保存所有图片文件
        import base64
        import time

        from flask import current_app

        uploads_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        temp_filepaths = []

        try:
            for idx, image_data in enumerate(image_data_list):
                # 处理base64数据
                if image_data.startswith("data:image"):
                    image_data = image_data.split(",", 1)[1]

                temp_filename = f"test_workflow_{image_id}_{int(time.time())}_{idx}.jpg"
                temp_filepath = os.path.join(uploads_dir, temp_filename)

                with open(temp_filepath, "wb") as f:
                    f.write(base64.b64decode(image_data))
                temp_filepaths.append(temp_filepath)
                logger.info(f"✅ 测试图片 {idx + 1} 已保存: {temp_filepath}")
        except Exception as e:
            # 清理已保存的文件
            for fp in temp_filepaths:
                try:
                    if os.path.exists(fp):
                        os.remove(fp)
                except Exception:
                    pass
            return jsonify({"status": "error", "message": f"图片数据解析失败: {str(e)}"}), 400

        # 优化：移除重复的图片上传和工作流加载操作
        # 这些操作会在create_ai_task中统一处理，避免重复上传图片（节省8-10秒）
        # 直接创建测试订单，然后调用create_ai_task处理图片上传和工作流提交

        # 创建正式测试订单（保存所有上传的图片）
        import time as time_module

        test_workflow_start_time = time_module.time()
        test_workflow_step_times = {}

        # 获取Order和OrderImage模型
        step_start = time_module.time()
        import sys

        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            Order = getattr(test_server_module, "Order", None)
            OrderImage = getattr(test_server_module, "OrderImage", None)
            AITask = getattr(test_server_module, "AITask", None)
        else:
            Order = None
            OrderImage = None
            AITask = None
        test_workflow_step_times["获取模型"] = time_module.time() - step_start

        if not all([Order, OrderImage, AITask]):
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        try:
            import random
            import uuid
            from datetime import datetime

            # 创建订单
            step_start = time_module.time()

            # 生成测试订单号（根据来源使用不同的前缀）
            order_number, customer_name, source_type = _get_test_order_info(request)

            # 获取风格图片信息
            style_image_name = image.name if image else "测试风格"
            style_category_name = category.name if category else "测试分类"

            # 创建Order记录
            test_order = Order(
                order_number=order_number,
                customer_name=customer_name,
                customer_phone="00000000000",
                style_name=style_image_name,
                product_name=f"{style_category_name} - {style_image_name}",
                price=0.0,  # 测试订单价格为0
                status="ai_processing",  # 测试订单状态为AI任务处理中
                source_type=source_type,  # 标记为后台测试或Playground测试
                original_image=(
                    f"/uploads/{os.path.basename(temp_filepaths[0])}" if temp_filepaths else ""
                ),  # 使用第一张图片作为原图
                created_at=datetime.now(),
            )
            db.session.add(test_order)
            db.session.flush()  # 获取order.id

            # 创建OrderImage记录（保存所有上传的图片）
            order_images = []
            for idx, temp_filepath in enumerate(temp_filepaths):
                img_filename = os.path.basename(temp_filepath)
                order_image = OrderImage(
                    order_id=test_order.id,
                    path=img_filename,
                    is_main=(idx == 0),  # 第一张图片设为主图
                )
                db.session.add(order_image)
                order_images.append(order_image)

            db.session.commit()
            test_workflow_step_times["创建订单和OrderImage"] = time_module.time() - step_start
            logger.info(
                f"✅ 创建测试订单成功: order_id={test_order.id}, order_number={order_number}, 图片数量={len(temp_filepaths)}"
            )

            # 增加Playground使用次数
            if user and hasattr(user, "playground_used_today"):
                user.playground_used_today = (getattr(user, "playground_used_today", 0) or 0) + 1
                if (
                    not hasattr(user, "playground_last_reset_date")
                    or not user.playground_last_reset_date
                ):
                    from datetime import date

                    user.playground_last_reset_date = date.today()
                db.session.commit()
                limit_text = (
                    f"{user.playground_daily_limit}"
                    if user.playground_daily_limit > 0
                    else "无限制"
                )
                logger.info(
                    f"📊 Playground使用次数已更新: {user.playground_used_today}/{limit_text}"
                )

            # 为每张图片创建AI任务
            step_start = time_module.time()
            from app.services.workflow_service import create_ai_task

            created_tasks = []
            task_errors = []

            # 准备工作流配置（使用前面已经获取的workflow_config）
            # workflow_config 已经在函数前面部分获取了，直接使用
            if not workflow_config:
                return (
                    jsonify({"status": "error", "message": "工作流配置不存在，请先配置工作流"}),
                    400,
                )

            for idx, order_image in enumerate(order_images):
                try:
                    logger.info(
                        f"📸 为图片 {idx + 1}/{len(order_images)} 创建AI任务: order_image_id={order_image.id}"
                    )
                    success, ai_task, error_message = create_ai_task(
                        order_id=test_order.id,
                        style_category_id=category.id,
                        style_image_id=image_id,
                        order_image_id=order_image.id,  # 为每张图片创建独立任务
                        db=db,
                        Order=Order,
                        AITask=AITask,
                        StyleCategory=StyleCategory,
                        StyleImage=StyleImage,
                        OrderImage=OrderImage,
                        workflow_config=workflow_config,  # 传入工作流配置（已在前面获取）
                    )

                    if success and ai_task:
                        created_tasks.append(
                            {
                                "task_id": ai_task.id,
                                "comfyui_prompt_id": ai_task.comfyui_prompt_id,
                                "status": ai_task.status,
                                "order_image_id": order_image.id,
                            }
                        )
                        logger.info(
                            f"✅ 图片 {idx + 1} 的AI任务创建成功: task_id={ai_task.id}, prompt_id={ai_task.comfyui_prompt_id}"
                        )
                    else:
                        error_msg = error_message or "未知错误"
                        task_errors.append(f"图片 {idx + 1}: {error_msg}")
                        logger.error("图片 {idx + 1} 的AI任务创建失败: {error_msg}")
                except Exception as e:
                    error_msg = f"创建AI任务异常: {str(e)}"
                    task_errors.append(f"图片 {idx + 1}: {error_msg}")
                    logger.error("图片 {idx + 1} 的AI任务创建异常: {error_msg}")
                    import traceback

                    traceback.print_exc()

            test_workflow_step_times["创建AI任务"] = time_module.time() - step_start

            # 打印性能统计
            total_duration = time_module.time() - test_workflow_start_time
            logger.info("\n⏱️ test_workflow函数性能统计:")
            logger.info(f"   总耗时: {total_duration:.2f} 秒")
            for step_name, step_time in test_workflow_step_times.items():
                percentage = (step_time / total_duration * 100) if total_duration > 0 else 0
                logger.info(f"   {step_name}: {step_time:.3f} 秒 ({percentage:.1f}%)")
            logger.info()

            # 返回结果
            if len(created_tasks) > 0:
                return jsonify(
                    {
                        "status": "success",
                        "message": f"工作流测试成功，已为 {len(created_tasks)} 张图片创建AI任务",
                        "data": {
                            "order_id": test_order.id,
                            "order_number": order_number,
                            "tasks": created_tasks,
                            "errors": task_errors if task_errors else None,
                            "total_images": len(temp_filepaths),
                            "success_count": len(created_tasks),
                            "failed_count": len(task_errors),
                        },
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "所有图片的AI任务创建失败",
                            "errors": task_errors,
                        }
                    ),
                    500,
                )

        except Exception as e:
            logger.warning("创建测试订单或AI任务失败: {str(e)}")
            import traceback

            traceback.print_exc()
            if "db" in locals():
                db.session.rollback()
            return (
                jsonify(
                    {"status": "error", "message": f"创建测试订单失败: {str(e)}", "error": str(e)}
                ),
                500,
            )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"测试失败: {str(e)}", "error": str(e)}), 500


@admin_styles_workflow_bp.route("/test-workflow-category/<int:category_id>", methods=["POST"])
@login_required
def test_workflow_category(category_id):
    """测试工作流API调用（使用分类配置）"""
    try:
        # 检查权限
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models(
            [
                "StyleCategory",
                "StyleImage",
                "AIConfig",
                "User",
                "Order",
                "OrderImage",
                "AITask",
                "APITemplate",
                "db",
            ]
        )
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        StyleCategory = models["StyleCategory"]
        AIConfig = models["AIConfig"]
        db = models["db"]

        # 获取分类配置
        category = StyleCategory.query.get_or_404(category_id)

        # 获取请求数据
        data = request.get_json()
        if not data or "image_data" not in data:
            return jsonify({"status": "error", "message": "缺少图片数据"}), 400

        # 获取工作流配置
        from app.services.workflow_service import get_comfyui_config, load_workflow_file

        temp_config = data.get("workflow_config")

        if temp_config:
            workflow_config = temp_config
            if isinstance(workflow_config.get("workflow_input_ids"), str):
                try:
                    workflow_config["workflow_input_ids"] = json.loads(
                        workflow_config["workflow_input_ids"]
                    )
                except Exception:
                    workflow_config["workflow_input_ids"] = [
                        id.strip()
                        for id in workflow_config["workflow_input_ids"].split(",")
                        if id.strip()
                    ]
        else:
            if not category.is_ai_enabled:
                return jsonify({"status": "error", "message": "分类未启用AI工作流"}), 400

            workflow_config = {
                "workflow_name": category.workflow_name,
                "workflow_file": category.workflow_file,
                "workflow_input_ids": (
                    json.loads(category.workflow_input_ids) if category.workflow_input_ids else []
                ),
                "workflow_output_id": category.workflow_output_id,
                "workflow_ref_id": category.workflow_ref_id,
                "workflow_ref_image": category.workflow_ref_image,
                "workflow_custom_prompt_id": category.workflow_custom_prompt_id,
                "workflow_custom_prompt_content": category.workflow_custom_prompt_content,
            }

        # 验证必要字段
        if not workflow_config.get("workflow_file"):
            return jsonify({"status": "error", "message": "工作流文件未配置"}), 400
        if not workflow_config.get("workflow_input_ids"):
            return jsonify({"status": "error", "message": "输入节点ID未配置"}), 400
        if not workflow_config.get("workflow_output_id"):
            return jsonify({"status": "error", "message": "输出节点ID未配置"}), 400

        # 处理base64图片数据
        image_data = data["image_data"]
        if image_data.startswith("data:image"):
            image_data = image_data.split(",", 1)[1]

        # 保存临时图片文件
        uploads_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        temp_filename = f"test_workflow_cat_{category_id}_{int(time.time())}.jpg"
        temp_filepath = os.path.join(uploads_dir, temp_filename)

        try:
            with open(temp_filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
            logger.info(f"✅ 测试图片已保存: {temp_filepath}")
        except Exception as e:
            return jsonify({"status": "error", "message": f"图片数据解析失败: {str(e)}"}), 400

        # 加载工作流文件
        try:
            workflow_data = load_workflow_file(workflow_config["workflow_file"])
        except Exception as e:
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except Exception:
                pass
            return jsonify({"status": "error", "message": f"加载工作流文件失败: {str(e)}"}), 400

        # 替换工作流参数（需要先上传图片到ComfyUI）
        input_ids = workflow_config["workflow_input_ids"]
        if input_ids and len(input_ids) > 0:
            if isinstance(workflow_data, dict) and input_ids[0] in workflow_data:
                # 获取ComfyUI配置
                comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)
                comfyui_base_url = comfyui_config.get("base_url", "http://127.0.0.1:8188")
                comfyui_upload_url = f"{comfyui_base_url.rstrip('/')}/upload/image"

                comfyui_image_filename = None
                try:
                    logger.info(f"📤 开始上传图片到ComfyUI: {comfyui_upload_url}")
                    logger.info(f"   本地图片路径: {temp_filepath}")

                    # 读取图片文件
                    with open(temp_filepath, "rb") as f:
                        # 生成唯一的文件名（避免冲突）
                        original_filename = os.path.basename(temp_filepath)
                        name, ext = os.path.splitext(original_filename)
                        upload_filename = f"{name}{ext}"

                        # 上传文件（ComfyUI的/upload/image API）
                        files = {
                            "image": (
                                upload_filename,
                                f,
                                "image/jpeg" if ext.lower() in [".jpg", ".jpeg"] else "image/png",
                            )
                        }

                        upload_response = requests.post(
                            comfyui_upload_url,
                            files=files,
                            timeout=60,
                            proxies={"http": None, "https": None},  # 禁用代理
                        )

                        if upload_response.status_code == 200:
                            upload_result = upload_response.json()
                            # ComfyUI返回格式通常是: {"name": "filename.jpg", "subfolder": "", "type": "input"}
                            comfyui_image_filename = upload_result.get("name", upload_filename)
                            logger.info(f"✅ 图片已上传到ComfyUI: {comfyui_image_filename}")
                        else:
                            error_msg = f"上传图片到ComfyUI失败: HTTP {upload_response.status_code}, {upload_response.text}"
                            logger.error("{error_msg}")
                            # 如果上传失败，尝试使用原始文件名（可能文件已存在）
                            comfyui_image_filename = upload_filename
                            logger.warning("使用文件名作为后备方案: {comfyui_image_filename}")

                except Exception as e:
                    error_msg = f"上传图片到ComfyUI异常: {str(e)}"
                    logger.error("{error_msg}")
                    import traceback

                    traceback.print_exc()
                    # 如果上传失败，使用原始文件名作为后备
                    comfyui_image_filename = os.path.basename(temp_filepath)
                    logger.warning("使用原始文件名作为后备方案: {comfyui_image_filename}")

                # 在工作流中使用上传后的文件名
                workflow_data[input_ids[0]]["inputs"]["image"] = comfyui_image_filename
                logger.info(f"📸 设置ComfyUI图片路径: {comfyui_image_filename}")

        if workflow_config.get("workflow_ref_id") and workflow_config.get("workflow_ref_image"):
            ref_id = workflow_config["workflow_ref_id"]
            if isinstance(workflow_data, dict) and ref_id in workflow_data:
                workflow_data[ref_id]["inputs"]["image"] = workflow_config["workflow_ref_image"]

        if workflow_config.get("workflow_custom_prompt_id") and workflow_config.get(
            "workflow_custom_prompt_content"
        ):
            prompt_id = workflow_config["workflow_custom_prompt_id"]
            if isinstance(workflow_data, dict) and prompt_id in workflow_data:
                workflow_data[prompt_id]["inputs"]["text"] = workflow_config[
                    "workflow_custom_prompt_content"
                ]

        # 获取ComfyUI配置
        comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)
        comfyui_url = f"{comfyui_config['base_url']}{comfyui_config['api_endpoint']}"

        logger.info(f"🔗 使用ComfyUI地址: {comfyui_url}")

        # 提交到ComfyUI
        request_body = {
            "prompt": workflow_data,
            "client_id": f"test_category_{category_id}_{int(time.time())}",
        }

        try:
            response = requests.post(
                comfyui_url,
                json=request_body,
                timeout=int(comfyui_config.get("timeout", 300)),
                proxies={"http": None, "https": None},
            )

            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")

                return jsonify(
                    {
                        "status": "success",
                        "message": "工作流测试成功，已提交到ComfyUI",
                        "data": {
                            "task_id": f"test_cat_{category_id}_{int(time.time())}",
                            "status": "processing",
                            "comfyui_prompt_id": prompt_id,
                            "comfyui_response": result,
                            "output_id": workflow_config["workflow_output_id"],
                        },
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"ComfyUI返回错误: HTTP {response.status_code}",
                            "error": response.text[:500],
                        }
                    ),
                    400,
                )

        except requests.exceptions.RequestException as e:
            return (
                jsonify(
                    {"status": "error", "message": f"连接ComfyUI失败: {str(e)}", "error": str(e)}
                ),
                500,
            )
        finally:
            # 清理临时文件
            def cleanup_temp_file():
                import time as time_module

                time_module.sleep(5)
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                        logger.info(f"✅ 临时测试图片已清理: {temp_filepath}")
                except Exception:
                    pass

            threading.Thread(target=cleanup_temp_file, daemon=True).start()

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"测试失败: {str(e)}", "error": str(e)}), 500


@admin_styles_workflow_bp.route("/test-workflow-result/<prompt_id>", methods=["GET"])
@login_required
def api_get_test_workflow_result(prompt_id):
    """查询ComfyUI测试结果"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        AIConfig = models["AIConfig"]
        db = models["db"]

        output_id = request.args.get("output_id")
        if not output_id:
            return jsonify({"status": "error", "message": "缺少输出节点ID"}), 400

        # 获取ComfyUI配置
        from app.services.workflow_service import get_comfyui_config

        comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)

        # 查询ComfyUI历史记录
        history_url = f"{comfyui_config['base_url']}/history/{prompt_id}"

        try:
            response = requests.get(history_url, timeout=10, proxies={"http": None, "https": None})

            if response.status_code == 200:
                history_data = response.json()

                # 检查是否有结果
                if prompt_id in history_data:
                    outputs = history_data[prompt_id].get("outputs", {})
                    if output_id in outputs:
                        output_images = outputs[output_id].get("images", [])
                        if output_images and len(output_images) > 0:
                            image_info = output_images[0]
                            image_filename = image_info.get("filename")
                            image_subfolder = image_info.get("subfolder", "")
                            image_type = image_info.get("type", "output")

                            # 构建图片URL
                            if image_subfolder:
                                image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&subfolder={image_subfolder}&type={image_type}"
                            else:
                                image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&type={image_type}"

                            return jsonify(
                                {
                                    "status": "success",
                                    "message": "处理完成",
                                    "data": {
                                        "image_url": image_url,
                                        "image_filename": image_filename,
                                        "image_subfolder": image_subfolder,
                                        "image_type": image_type,
                                    },
                                }
                            )
                        else:
                            return jsonify(
                                {"status": "processing", "message": "处理中，暂无输出图片"}
                            )
                    else:
                        return jsonify(
                            {"status": "processing", "message": "处理中，输出节点尚未完成"}
                        )
                else:
                    return jsonify({"status": "processing", "message": "处理中，任务尚未完成"})
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"查询ComfyUI历史失败: HTTP {response.status_code}",
                        }
                    ),
                    500,
                )

        except requests.exceptions.RequestException as e:
            return jsonify({"status": "error", "message": f"连接ComfyUI失败: {str(e)}"}), 500

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"查询失败: {str(e)}"}), 500


# ============================================================================
# 工作流文件上传API
# ============================================================================


@admin_styles_workflow_bp.route("/workflow/upload", methods=["POST"])
@login_required
def admin_upload_workflow():
    """上传ComfyUI工作流JSON文件"""
    try:
        # 检查权限
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        # 检查是否有文件
        if "workflow" not in request.files:
            return jsonify({"status": "error", "message": "没有上传文件"}), 400

        file = request.files["workflow"]

        # 检查文件名
        if file.filename == "":
            return jsonify({"status": "error", "message": "文件名为空"}), 400

        # 检查文件扩展名
        if not file.filename.lower().endswith(".json"):
            return jsonify({"status": "error", "message": "只支持JSON格式文件"}), 400

        # 读取文件内容并验证JSON格式
        try:
            file_content = file.read()
            workflow_data = json.loads(file_content.decode("utf-8"))

            # 验证是否是有效的JSON对象
            if not isinstance(workflow_data, dict):
                return (
                    jsonify({"status": "error", "message": "无效的工作流格式：必须是JSON对象"}),
                    400,
                )

            if len(workflow_data) == 0:
                return (
                    jsonify({"status": "error", "message": "无效的工作流格式：工作流文件不能为空"}),
                    400,
                )

        except json.JSONDecodeError as e:
            return jsonify({"status": "error", "message": f"JSON格式错误: {str(e)}"}), 400
        except UnicodeDecodeError:
            return jsonify({"status": "error", "message": "文件编码错误：必须是UTF-8格式"}), 400

        # 确保workflows目录存在
        workflows_dir = "workflows"
        os.makedirs(workflows_dir, exist_ok=True)

        # 获取原始文件名
        from werkzeug.utils import secure_filename

        original_filename = file.filename
        safe_filename = secure_filename(original_filename)

        # 如果secure_filename处理后文件名无效，使用时间戳作为文件名
        if (
            not safe_filename
            or safe_filename == ".json"
            or (safe_filename.startswith(".") and len(safe_filename) <= 5)
        ):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}.json"
        else:
            # 确保文件名以.json结尾
            if not safe_filename.lower().endswith(".json"):
                safe_filename = safe_filename + ".json"
            # 如果文件已存在，添加时间戳避免覆盖
            filepath = os.path.join(workflows_dir, safe_filename)
            if os.path.exists(filepath):
                name, ext = os.path.splitext(safe_filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{name}_{timestamp}{ext}"

        filename = safe_filename
        filepath = os.path.join(workflows_dir, filename)

        # 保存文件
        file.seek(0)  # 重置文件指针
        file.save(filepath)

        logger.info(f"✅ 工作流文件上传成功: {filename} (原始文件名: {original_filename})")

        return jsonify(
            {
                "status": "success",
                "message": "工作流文件上传成功",
                "filename": filename,
                "original_filename": original_filename,
            }
        )

    except Exception as e:
        logger.error("上传工作流文件失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"上传失败: {str(e)}"}), 500


# ============================================================================
# API模板管理API
# ============================================================================


@admin_styles_workflow_bp.route("/images/<int:image_id>/api-template", methods=["GET"])
@login_required
def get_api_template(image_id):
    """获取风格图片的API模板配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models(
            [
                "StyleCategory",
                "StyleImage",
                "AIConfig",
                "User",
                "Order",
                "OrderImage",
                "AITask",
                "APITemplate",
                "db",
            ]
        )
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        # 获取APITemplate模型
        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        APITemplate = test_server_module.APITemplate
        StyleImage = models["StyleImage"]

        # 检查图片是否存在
        image = StyleImage.query.get(image_id)
        if not image:
            return jsonify({"status": "error", "message": "风格图片不存在"}), 404

        # 获取API模板（图片级别优先）
        # 注意：编辑时查询所有模板（包括 is_active=False），以便正确显示禁用状态
        api_template = APITemplate.query.filter_by(style_image_id=image_id).first()

        if api_template:
            template_dict = api_template.to_dict()
            logger.info(
                f"📥 返回API模板数据: api_config_id={template_dict.get('api_config_id')}, request_body_template={'存在' if template_dict.get('request_body_template') else '不存在'}"
            )
            return jsonify({"status": "success", "data": template_dict})
        else:
            logger.warning("未找到API模板，image_id={image_id}")
            return jsonify({"status": "success", "data": None})

    except Exception as e:
        logger.info(f"获取API模板失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取API模板失败: {str(e)}"}), 500


@admin_styles_workflow_bp.route("/images/<int:image_id>/test-api-comfyui", methods=["POST"])
@login_required
def test_api_comfyui_template(image_id):
    """测试API-ComfyUI工作流模板"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        APITemplate = test_server_module.APITemplate
        APIProviderConfig = test_server_module.APIProviderConfig
        AITask = test_server_module.AITask
        StyleImage = models["StyleImage"]

        # 检查图片是否存在
        image = StyleImage.query.get(image_id)
        if not image:
            return jsonify({"status": "error", "message": "风格图片不存在"}), 404

        # 获取API模板配置
        api_template = APITemplate.query.filter_by(style_image_id=image_id, is_active=True).first()
        if not api_template:
            return jsonify({"status": "error", "message": "未配置API-ComfyUI工作流模板"}), 400

        # 获取API配置
        api_config = None
        if api_template.api_config_id:
            api_config = APIProviderConfig.query.filter_by(
                id=api_template.api_config_id, is_active=True
            ).first()

        if not api_config:
            return jsonify({"status": "error", "message": "未找到可用的API配置"}), 400

        # 检查是否是 runninghub-comfyui-workflow 类型
        if api_config.api_type != "runninghub-comfyui-workflow":
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "当前API配置不是 runninghub-comfyui-workflow 类型",
                    }
                ),
                400,
            )

        # 处理上传的图片（支持多图）
        uploaded_images = []
        # 获取所有cloud_image_url（支持多图）
        cloud_image_urls = request.form.getlist("cloud_image_url")
        if not cloud_image_urls or len(cloud_image_urls) == 0:
            return jsonify({"status": "error", "message": "请上传测试图片"}), 400

        uploaded_images = cloud_image_urls

        # 获取提示词（API测试时，如果为空则使用批量提示词）
        prompt = request.form.get("prompt", "").strip()
        # 注意：如果prompt为空，create_api_task会优先使用批量提示词（prompts_json）

        # 创建常规订单信息
        import random
        import uuid
        from datetime import datetime

        Order = test_server_module.Order
        OrderImage = test_server_module.OrderImage

        # 生成测试订单号（根据来源使用不同的前缀）
        test_task_id = str(uuid.uuid4())
        order_number, customer_name, source_type = _get_test_order_info(request)

        # 获取风格图片信息
        style_image_name = image.name if image else "测试风格"
        style_category_name = image.category.name if image and image.category else "测试分类"

        # 创建Order记录
        test_order = Order(
            order_number=order_number,
            customer_name=customer_name,
            customer_phone="00000000000",
            style_name=style_image_name,
            product_name=f"{style_category_name} - {style_image_name}",
            price=0.0,  # 测试订单价格为0
            status="ai_processing",  # 测试订单状态为AI任务处理中（创建任务后会自动更新）
            source_type=source_type,  # 标记为后台测试或Playground测试
            original_image=(
                uploaded_images[0] if uploaded_images else ""
            ),  # 使用第一张上传的图片作为原图
            created_at=datetime.now(),
        )
        db.session.add(test_order)
        db.session.flush()  # 获取order.id

        # 创建OrderImage记录（保存所有上传的图片）
        for idx, img_url in enumerate(uploaded_images):
            # 如果是本地路径，提取文件名
            if img_url.startswith("/uploads/"):
                img_path = img_url.replace("/uploads/", "")
            else:
                # 云端URL，保存完整URL
                img_path = img_url

            order_image = OrderImage(
                order_id=test_order.id, path=img_path, is_main=(idx == 0)  # 第一张图片设为主图
            )
            db.session.add(order_image)

        db.session.commit()
        logger.info(f"✅ 创建测试订单成功: order_id={test_order.id}, order_number={order_number}")

        # 调用API服务
        from app.services.ai_provider_service import create_api_task

        # 使用真实订单ID和订单号
        create_api_task._test_order_id = test_order.id
        create_api_task._test_order_number = order_number

        success, task, error_message = create_api_task(
            style_image_id=image_id,
            prompt=prompt,
            image_size=None,  # RunningHub ComfyUI 工作流不使用 size
            aspect_ratio=None,  # RunningHub ComfyUI 工作流不使用 aspect_ratio
            uploaded_images=uploaded_images,
            upload_config=None,
            api_config_id=api_config.id,
            db=db,
            AITask=AITask,
            APITemplate=APITemplate,
            APIProviderConfig=APIProviderConfig,
            StyleImage=StyleImage,
        )

        if not success:
            # 如果任务创建失败，删除已创建的测试订单（可选，也可以保留用于调试）
            try:
                # 可以选择删除测试订单，或者保留用于调试
                # db.session.delete(test_order)
                # db.session.commit()
                logger.warning("测试任务创建失败，但保留测试订单用于调试: order_id={test_order.id}")
            except Exception as e:
                logger.warning("删除测试订单失败: {str(e)}")
            return jsonify({"status": "error", "message": error_message or "创建测试任务失败"}), 500

        # 从processing_log中获取API信息
        api_info = {}
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
            except Exception:
                pass

        # 获取task_id
        task_id = task.comfyui_prompt_id or api_info.get("api_task_id") or api_info.get("task_id")

        # 检查是否是同步API
        is_sync_api = api_config.is_sync_api if hasattr(api_config, "is_sync_api") else False

        # 如果是同步API且任务已完成，直接返回结果
        if is_sync_api and task.status == "success" and task.output_image_path:
            return jsonify(
                {
                    "status": "success",
                    "message": "测试成功",
                    "data": {
                        "task_id": task_id,
                        "is_sync_api": True,
                        "status": "completed",
                        "result_image_url": task.output_image_path,
                    },
                }
            )

        # 异步API，返回任务ID用于轮询
        return jsonify(
            {
                "status": "success",
                "message": "测试任务已创建",
                "data": {"task_id": task_id, "is_sync_api": False, "status": task.status},
            }
        )

    except Exception as e:
        logger.info(f"测试API-ComfyUI工作流失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"测试失败: {str(e)}"}), 500


@admin_styles_workflow_bp.route("/images/test-api-comfyui/task/<task_id>", methods=["GET"])
@login_required
def get_test_api_comfyui_task_status(task_id):
    """获取API-ComfyUI工作流测试任务状态"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        AITask = test_server_module.AITask
        APIProviderConfig = test_server_module.APIProviderConfig

        # 查找任务（通过 comfyui_prompt_id 或 notes 中的 T8_API_TASK_ID）
        task = None
        if task_id.startswith("TEST_"):
            # 测试任务，通过 order_number 查找
            task = AITask.query.filter_by(order_number=task_id).first()
        else:
            # 通过 comfyui_prompt_id 查找
            task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
            if not task:
                # 通过 notes 中的 T8_API_TASK_ID 查找
                task = AITask.query.filter(AITask.notes.like(f"%T8_API_TASK_ID:{task_id}%")).first()

        if not task:
            return jsonify({"status": "error", "message": "任务不存在"}), 404

        # 获取API配置
        api_config = None
        if task.notes and "T8_API_TASK_ID:" in task.notes:
            # RunningHub API，需要查询结果
            api_task_id = task.notes.split("T8_API_TASK_ID:")[1].split("|")[0].strip()

            # 从 processing_log 中获取 API 配置信息
            api_info = {}
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                except Exception:
                    pass

            # 获取API配置（从任务关联的配置或默认配置）
            api_config_id = api_info.get("api_config_id")
            if api_config_id:
                api_config = APIProviderConfig.query.get(api_config_id)

            if not api_config:
                api_config = APIProviderConfig.query.filter_by(
                    is_active=True, is_default=True
                ).first()

            if api_config and api_config.api_type in [
                "runninghub-rhart-edit",
                "runninghub-comfyui-workflow",
            ]:
                # RunningHub API，查询任务结果
                host = api_config.host_domestic or api_config.host_overseas
                result_endpoint = api_config.result_endpoint or "/openapi/v2/task/outputs"
                result_url = f"{host.rstrip('/')}{result_endpoint}"

                headers = {
                    "Authorization": f"Bearer {api_config.api_key}",
                    "Content-Type": "application/json",
                }

                try:
                    response = requests.get(
                        result_url,
                        params={"taskId": api_task_id},
                        headers=headers,
                        timeout=(10, 30),
                    )
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get("status", "")

                        if status == "SUCCESS" and result.get("results"):
                            # 任务完成，更新任务状态
                            task.status = "success"
                            if result["results"] and len(result["results"]) > 0:
                                image_url = result["results"][0].get("url")
                                if image_url:
                                    task.output_image_path = image_url
                                    task.completed_at = datetime.now()
                                    db.session.commit()

                            return jsonify(
                                {
                                    "status": "success",
                                    "data": {
                                        "task_id": api_task_id,
                                        "status": "completed",
                                        "result_image_url": task.output_image_path,
                                    },
                                }
                            )
                        elif status == "FAILED":
                            task.status = "failed"
                            task.error_message = result.get("errorMessage", "任务执行失败")
                            db.session.commit()

                            return jsonify(
                                {
                                    "status": "success",
                                    "data": {
                                        "task_id": api_task_id,
                                        "status": "failed",
                                        "error_message": result.get("errorMessage", "任务执行失败"),
                                    },
                                }
                            )
                        else:
                            return jsonify(
                                {
                                    "status": "success",
                                    "data": {
                                        "task_id": api_task_id,
                                        "status": "processing",
                                        "api_status": status,
                                    },
                                }
                            )
                    else:
                        return jsonify(
                            {
                                "status": "success",
                                "data": {
                                    "task_id": api_task_id,
                                    "status": "processing",
                                    "message": f"查询API状态失败: HTTP {response.status_code}",
                                },
                            }
                        )
                except Exception as e:
                    logger.info(f"查询RunningHub API结果失败: {str(e)}")
                    return jsonify(
                        {
                            "status": "success",
                            "data": {
                                "task_id": api_task_id,
                                "status": task.status,
                                "message": f"查询失败: {str(e)}",
                            },
                        }
                    )

        # 返回任务状态
        return jsonify(
            {
                "status": "success",
                "data": {
                    "task_id": task.comfyui_prompt_id or task_id,
                    "status": task.status,
                    "result_image_url": (
                        task.output_image_path if task.status == "success" else None
                    ),
                    "error_message": task.error_message if task.status == "failed" else None,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取API-ComfyUI工作流测试任务状态失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务状态失败: {str(e)}"}), 500


@admin_styles_workflow_bp.route("/images/upload-to-grsai", methods=["POST"])
@login_required
def upload_image_to_grsai():
    """上传图片到grsai文件服务器（用于API测试，支持文件上传或URL上传）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        # 支持两种方式：文件上传或URL上传
        file = None
        image_url = None
        ext = "jpg"  # 默认扩展名

        # 方式1：文件上传
        if "image" in request.files:
            file = request.files["image"]
            if file.filename:
                filename = file.filename
                ext = os.path.splitext(filename)[1].lower().lstrip(".")
                if ext not in ["jpg", "jpeg", "png", "gi", "webp"]:
                    return jsonify({"status": "error", "message": "不支持的图片格式"}), 400
        # 方式2：URL上传（JSON格式）
        elif request.is_json:
            data = request.get_json()
            image_url = data.get("image_url")
            if not image_url:
                return jsonify({"status": "error", "message": "请提供图片URL"}), 400

            # 从URL中提取扩展名
            if "." in image_url:
                ext = os.path.splitext(image_url.split("?")[0])[1].lower().lstrip(".")
                if ext not in ["jpg", "jpeg", "png", "gi", "webp"]:
                    ext = "jpg"  # 默认使用jpg
            else:
                ext = "jpg"
        else:
            return jsonify({"status": "error", "message": "请上传图片或提供图片URL"}), 400

        # 获取API配置（用于获取api_key）
        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
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

        logger.info(f"第一步：获取上传token（文件扩展名: {ext})")

        # 第一步：获取上传token（使用POST方法，需要Authorization header和JSON数据）
        token_url = "https://grsai.dakka.com.cn/client/resource/newUploadTokenZH"
        logger.info(f"📤 请求上传token URL: {token_url}")

        # 禁用代理（grsai是国内服务器，直连速度更快）
        proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        proxies = {"http": None, "https": None}  # 强制禁用代理
        if has_proxy:
            logger.info("📤 代理设置: 已强制禁用（grsai是国内服务器，直连速度更快）")

        # 使用POST方法，添加Authorization header和JSON数据
        headers = {
            "Authorization": f"Bearer {api_config.api_key}",
            "Content-Type": "application/json",
        }
        data = {"sux": ext}

        token_response = requests.post(
            url=token_url, headers=headers, json=data, proxies=proxies, timeout=30
        )
        logger.info(f"📤 Token请求响应状态码: {token_response.status_code}")

        if token_response.status_code != 200:
            error_text = (
                token_response.text[:500]
                if hasattr(token_response, "text")
                else str(token_response.content[:500])
            )
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"获取上传token失败: HTTP {token_response.status_code}",
                        "error": error_text,
                    }
                ),
                500,
            )

        token_result = token_response.json()
        logger.info(f"📤 Token响应内容: {token_result}")

        if token_result.get("code") != 0:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"获取上传token失败: {token_result.get('msg', '未知错误')}",
                    }
                ),
                500,
            )

        upload_info = token_result.get("data", {})
        upload_url = upload_info.get("url")  # https://up-z2.qiniup.com
        token = upload_info.get("token")
        key = upload_info.get("key")  # 文件key
        domain = upload_info.get("domain")  # https://grsai-file.dakka.com.cn

        if not all([upload_url, token, key, domain]):
            return jsonify({"status": "error", "message": "上传token响应数据不完整"}), 500

        logger.info("✅ 获取上传token成功")
        logger.info(f"第二步：上传文件到 {upload_url}")

        # 第二步：上传文件到七牛云
        logger.info(f"📤 上传文件到: {upload_url}")
        logger.info("📤 代理设置: 已强制禁用（grsai是国内服务器，直连速度更快）")

        # 读取文件内容（支持文件上传或URL下载）
        file_content = None
        upload_filename = None

        if file:
            # 方式1：文件上传
            file_content = file.read()
            upload_filename = file.filename
        elif image_url:
            # 方式2：URL上传（需要先下载图片）
            try:
                logger.info(f"📥 从URL下载图片: {image_url}")
                # 下载图片
                download_response = requests.get(image_url, proxies=proxies, timeout=30)
                if download_response.status_code != 200:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"下载图片失败: HTTP {download_response.status_code}",
                            }
                        ),
                        400,
                    )

                file_content = download_response.content
                # 从URL中提取文件名
                parsed_url = urlparse(image_url)
                upload_filename = os.path.basename(parsed_url.path) or f"image.{ext}"
                logger.info(f"✅ 图片下载成功: {len(file_content)} 字节")
            except Exception as e:
                return jsonify({"status": "error", "message": f"下载图片失败: {str(e)}"}), 400

        if not file_content:
            return jsonify({"status": "error", "message": "无法获取图片内容"}), 400

        file_size = len(file_content)
        logger.info(f"📤 文件大小: {file_size / 1024 / 1024:.2f} MB")

        # 准备上传数据（参考bk-photo-v4的实现）
        # 注意：token和key应该放在data中，file放在files中
        upload_data = {"token": token, "key": key}
        upload_files = {"file": (upload_filename, file_content, f"image/{ext}")}

        upload_response = requests.post(
            url=upload_url, data=upload_data, files=upload_files, proxies=proxies, timeout=120
        )
        logger.info(f"📤 上传响应状态码: {upload_response.status_code}")

        if upload_response.status_code != 200:
            error_text = (
                upload_response.text[:500]
                if hasattr(upload_response, "text")
                else str(upload_response.content[:500])
            )
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"文件上传失败: HTTP {upload_response.status_code}",
                        "error": error_text,
                    }
                ),
                500,
            )

        # 构建文件URL
        file_url = f"{domain}/{key}"
        logger.info(f"文件上传到grsai成功: {file_url}")

        return jsonify(
            {
                "status": "success",
                "message": "图片上传成功",
                "data": {"url": file_url, "key": key, "domain": domain},
            }
        )

    except Exception as e:
        logger.info(f"上传图片到grsai失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"上传失败: {str(e)}"}), 500


@admin_styles_workflow_bp.route("/images/test-api/task/<task_id>", methods=["GET"])
@login_required
def get_api_test_task_status(task_id):
    """获取API测试任务状态"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        import sys

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        AITask = test_server_module.AITask

        # 获取任务（使用comfyui_prompt_id存储task_id）
        task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
        if not task:
            return jsonify({"status": "error", "message": "任务不存在"}), 404

        # 检查任务状态
        if task.status == "success" and task.output_image_path:
            return jsonify(
                {
                    "status": "success",
                    "data": {"status": "completed", "result_image_url": task.output_image_path},
                }
            )
        elif task.status == "failed":
            return jsonify(
                {
                    "status": "success",
                    "data": {"status": "failed", "error_message": task.error_message or "任务失败"},
                }
            )
        else:
            return jsonify(
                {"status": "success", "data": {"status": "processing", "message": "任务处理中..."}}
            )

    except Exception as e:
        logger.info(f"获取测试任务状态失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务状态失败: {str(e)}"}), 500
