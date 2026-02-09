# -*- coding: utf-8 -*-
"""
选片页面 - 订单列表
"""

import logging

logger = logging.getLogger(__name__)
import glob
import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.utils.admin_helpers import get_models

from .utils import get_app_instance

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_list", __name__)


@bp.route("/admin/photo-selection")
def photo_selection_list():
    """选片页面 - 订单列表"""
    models = get_models(["Order", "AITask"])
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    Order = models["Order"]
    AITask = models["AITask"]

    # 检查用户权限：如果是加盟商，只能查看自己的订单
    from flask import session

    session_franchisee_id = session.get("franchisee_id")

    # 获取筛选参数
    franchisee_id = request.args.get("franchisee_id", type=int)

    # 如果session中有加盟商ID，说明是加盟商登录
    if session_franchisee_id:
        # 加盟商只能查看自己的订单，忽略URL参数中的franchisee_id
        franchisee_id = session_franchisee_id
    else:
        # 管理员需要登录且是admin或operator角色
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role not in ["admin", "operator"]:
            flash("权限不足", "error")
            return redirect(url_for("auth.login"))

    # 构建查询
    query = Order.query.filter(Order.status != "unpaid")

    # 如果指定了加盟商ID，则只显示该加盟商的订单
    if franchisee_id:
        query = query.filter(Order.franchisee_id == franchisee_id)

    # 获取订单列表
    orders = query.order_by(Order.created_at.desc()).all()

    # 优化N+1查询：批量查询所有订单的AI任务
    order_ids = [order.id for order in orders]
    ai_tasks_map = {}
    if order_ids:
        all_ai_tasks = AITask.query.filter(AITask.order_id.in_(order_ids)).all()
        for task in all_ai_tasks:
            if task.order_id not in ai_tasks_map:
                ai_tasks_map[task.order_id] = []
            ai_tasks_map[task.order_id].append(task)

    # 获取应用实例以访问配置
    from .utils import get_app_instance

    try:
        app_instance = get_app_instance()
        # 验证app_instance是否有效
        if app_instance is None or not hasattr(app_instance, "config"):
            logger.warning("无法获取有效的应用实例，将跳过文件系统读取")
            app_instance = None
    except Exception as e:
        logger.warning(f"获取应用实例失败: {e}，将跳过文件系统读取")
        app_instance = None

    # 为每个订单检查任务状态
    orders_data = []
    for order in orders:
        try:
            # 从批量查询的映射中获取该订单的AI任务（避免N+1查询）
            ai_tasks = ai_tasks_map.get(order.id, [])

            # 检查是否所有任务都已完成
            # 如果有任务，则检查是否全部完成；如果没有任务，检查订单状态和效果图
            if len(ai_tasks) > 0:
                all_completed = all(task.status == "completed" for task in ai_tasks)
            else:
                # 如果没有AI任务记录，但有效果图（手动上传），也认为可以选片
                # 检查订单是否有效果图文件
                has_effect_image = bool(order.hd_image)
                all_completed = has_effect_image and order.status in ["completed", "hd_ready"]

            # 获取效果图数量 - 首先从AITask统计，如果数量为0则从文件系统读取
            effect_images_count = 0

            # 1. 从AITask统计已完成且有效果图的任务
            if len(ai_tasks) > 0:
                completed_tasks_with_images = [
                    task
                    for task in ai_tasks
                    if task.status == "completed" and task.output_image_path
                ]
                effect_images_count = len(completed_tasks_with_images)
                logger.info(
                    f"订单 {order.order_number}: 从AITask找到 {effect_images_count} 个已完成且有效果图的任务"
                )

            # 2. 如果AITask中没有效果图，尝试从文件系统读取（与订单详情页面逻辑一致）
            if effect_images_count == 0 and app_instance is not None:
                try:
                    hd_folder = app_instance.config.get(
                        "HD_FOLDER", os.path.join(app_instance.root_path, "hd_images")
                    )
                    if not os.path.isabs(hd_folder):
                        hd_folder = os.path.join(app_instance.root_path, hd_folder)

                    if os.path.exists(hd_folder):
                        # 查找该订单的所有效果图文件
                        pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                        effect_files = glob.glob(pattern)
                        effect_images_count = len(effect_files)
                        if effect_images_count > 0:
                            logger.info(
                                f"订单 {order.order_number}: 从文件系统找到 {effect_images_count} 张效果图"
                            )
                except Exception as e:
                    logger.warning(f"订单 {order.order_number}: 从文件系统读取效果图失败: {e}")

            # 3. 如果仍然为0，但订单有hd_image字段，计数为1（兼容旧数据）
            if effect_images_count == 0 and order.hd_image:
                effect_images_count = 1
                logger.info(f"订单 {order.order_number}: 使用hd_image字段，效果图数量: 1")

            # 状态映射
            status_map = {
                "unpaid": "未支付",
                "paid": "已支付",
                "shooting": "正在拍摄",
                "retouching": "美颜处理中",
                "ai_processing": "AI任务处理中",
                "pending_selection": "待选片",
                "selection_completed": "已选片",
                "printing": "打印中",
                "pending_shipment": "待发货",
                "shipped": "已发货",
                "pending": "待制作",
                "processing": "处理中",
                "manufacturing": "制作中",
                "completed": "已完成",
                "delivered": "已送达",
                "cancelled": "已取消",
                "refunded": "已退款",
                "hd_ready": "高清放大",
            }

            orders_data.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name or "",
                    "customer_phone": order.customer_phone or "",
                    "status": order.status,
                    "status_text": status_map.get(order.status, order.status or "未知"),
                    "product_name": order.product_name or "",
                    "franchisee_id": getattr(order, "franchisee_id", None),
                    "all_tasks_completed": all_completed,
                    "effect_images_count": effect_images_count,
                    "created_at": order.created_at,
                }
            )
        except Exception as e:
            logger.error(
                f"处理订单 {order.order_number if order else 'Unknown'} 时出错: {e}", exc_info=True
            )
            # 即使出错也添加基本信息，避免页面完全无法显示
            try:
                orders_data.append(
                    {
                        "id": order.id if order else 0,
                        "order_number": order.order_number if order else "Unknown",
                        "customer_name": getattr(order, "customer_name", "") or "",
                        "customer_phone": getattr(order, "customer_phone", "") or "",
                        "status": getattr(order, "status", "unknown"),
                        "status_text": "处理出错",
                        "product_name": getattr(order, "product_name", "") or "",
                        "franchisee_id": getattr(order, "franchisee_id", None),
                        "all_tasks_completed": False,
                        "effect_images_count": 0,
                        "created_at": getattr(order, "created_at", None),
                    }
                )
            except Exception as e2:
                logger.error(f"添加错误订单信息时再次出错: {e2}")

    # 获取加盟商信息（如果指定了加盟商ID）
    franchisee_info = None
    if franchisee_id:
        FranchiseeAccount = models.get("FranchiseeAccount")
        if FranchiseeAccount:
            franchisee = FranchiseeAccount.query.get(franchisee_id)
            if franchisee:
                franchisee_info = {"id": franchisee.id, "company_name": franchisee.company_name}

    return render_template(
        "admin/photo_selection_list.html",
        orders=orders_data,
        franchisee_id=franchisee_id,
        franchisee_info=franchisee_info,
    )
