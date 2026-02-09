# -*- coding: utf-8 -*-
"""
选片页面 - 提交选片
"""

import logging

logger = logging.getLogger(__name__)
import glob
import os
import time

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.utils.admin_helpers import get_models

from .utils import get_app_instance

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_submit", __name__)


@bp.route("/admin/photo-selection/<int:order_id>/submit", methods=["POST"])
def photo_selection_submit(order_id):
    """提交选片结果"""
    models = get_models(
        ["Order", "AITask", "Product", "ProductSize", "SelectionOrder", "db"]
    )
    if not models:
        return jsonify({"success": False, "message": "系统未初始化"}), 500

    Order = models["Order"]
    AITask = models["AITask"]
    Product = models["Product"]
    ProductSize = models["ProductSize"]
    SelectionOrder = models["SelectionOrder"]
    db = models["db"]

    try:
        data = request.get_json()
        selected_image_ids = data.get("selected_image_ids", [])  # 选中的效果图ID列表（AITask的ID）
        image_product_mappings = data.get(
            "image_product_mappings", {}
        )  # 每张照片的产品关联信息 {imageId: [{product_id, size_id, quantity}, ...]}
        # 兼容旧版本（如果没有image_product_mappings，使用旧的selected_product_id和selected_size_id）
        selected_product_id = data.get("selected_product_id")
        selected_size_id = data.get("selected_size_id")

        if not selected_image_ids:
            return jsonify({"success": False, "message": "请至少选择一张照片"}), 400

        # 产品关联是可选的（增项），不再强制要求
        # 如果有产品关联信息，会为关联的照片创建商城订单
        # 如果没有产品关联，只完成选片，不创建商城订单

        # 获取订单
        order = Order.query.get_or_404(order_id)

        # 检查用户权限：如果是加盟商，只能操作自己的订单
        from flask import session

        session_franchisee_id = session.get("franchisee_id")

        # 如果session中有加盟商ID，检查订单是否属于该加盟商
        if session_franchisee_id:
            if getattr(order, "franchisee_id", None) != session_franchisee_id:
                return jsonify({"success": False, "message": "无权操作此订单"}), 403
        else:
            # 管理员需要登录且是admin或operator角色
            if not current_user.is_authenticated:
                return jsonify({"success": False, "message": "未登录"}), 401
            if current_user.role not in ["admin", "operator"]:
                return jsonify({"success": False, "message": "权限不足"}), 403

        # 获取产品的免费选片张数和额外照片价格
        free_selection_count = 1  # 默认1张
        extra_photo_price = 10.0  # 默认10元/张
        if order.product_name:
            product = Product.query.filter_by(name=order.product_name, is_active=True).first()
            if product:
                if hasattr(product, "free_selection_count"):
                    free_selection_count = product.free_selection_count or 1
                if hasattr(product, "extra_photo_price"):
                    extra_photo_price = product.extra_photo_price or 10.0

        # 计算超出费用
        extra_count = max(0, len(selected_image_ids) - free_selection_count)
        extra_fee = extra_count * extra_photo_price

        # 获取选中的效果图路径（取第一张作为主图）
        # 分离AITask ID和文件系统图片（ID为0）
        task_ids = [img_id for img_id in selected_image_ids if img_id != 0]
        file_system_images = [img_id for img_id in selected_image_ids if img_id == 0]

        main_image_path = None

        # 1. 从AITask获取效果图
        if task_ids:
            selected_tasks = AITask.query.filter(
                AITask.id.in_(task_ids), AITask.order_id == order_id
            ).all()

            if selected_tasks:
                main_image_path = selected_tasks[0].output_image_path

        # 2. 如果包含文件系统的图片（ID为0），从文件系统查找
        if file_system_images or (not task_ids and selected_image_ids):
            # 获取应用实例
            app_instance = get_app_instance()

            if app_instance is not None:
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
                        effect_files.sort(key=os.path.getmtime, reverse=True)

                        if effect_files and not main_image_path:
                            # 使用第一张文件作为主图
                            main_image_path = os.path.basename(effect_files[0])
                except Exception as e:
                    logger.warning(f"从文件系统获取效果图失败: {e}")
            else:
                logger.warning("无法获取应用实例，跳过文件系统查找")

        if not main_image_path:
            return jsonify({"success": False, "message": "选中的效果图不存在"}), 400

        # 创建选片订单（使用产品馆 Product/ProductSize）
        created_orders = []

        # 新版本：为每张关联了产品的照片创建订单（支持每张照片关联多个产品）
        if image_product_mappings:
            # 优化N+1查询：收集所有需要查询的ID
            all_product_ids = set()
            all_size_ids = set()
            all_task_ids = set()

            for mapping_key, mapping in image_product_mappings.items():
                try:
                    image_id = int(mapping_key)
                    if image_id != 0:
                        all_task_ids.add(image_id)
                except (ValueError, TypeError):
                    continue

                if isinstance(mapping, list):
                    for product_mapping in mapping:
                        product_id = product_mapping.get("product_id")
                        size_id = product_mapping.get("size_id")
                        if product_id:
                            all_product_ids.add(product_id)
                        if size_id and size_id > 0:
                            all_size_ids.add(size_id)
                elif isinstance(mapping, dict):
                    product_id = mapping.get("product_id")
                    size_id = mapping.get("size_id")
                    if product_id:
                        all_product_ids.add(product_id)
                    if size_id and size_id > 0:
                        all_size_ids.add(size_id)

            # 批量查询所有产品馆产品、尺寸和任务
            products_map = {}
            if all_product_ids:
                all_products = Product.query.filter(Product.id.in_(all_product_ids)).all()
                for product in all_products:
                    products_map[product.id] = product

            sizes_map = {}
            if all_size_ids:
                all_sizes = ProductSize.query.filter(ProductSize.id.in_(all_size_ids)).all()
                for size in all_sizes:
                    sizes_map[size.id] = size

            tasks_map = {}
            if all_task_ids:
                all_tasks = AITask.query.filter(
                    AITask.id.in_(all_task_ids), AITask.order_id == order_id
                ).all()
                for task in all_tasks:
                    tasks_map[task.id] = task

            # 处理映射
            for mapping_key, mapping in image_product_mappings.items():
                try:
                    image_id = int(mapping_key)
                except (ValueError, TypeError):
                    continue

                # 支持新格式：mapping是产品列表（数组）
                if isinstance(mapping, list):
                    # 新格式：一个图片关联多个产品
                    for product_mapping in mapping:
                        product_id = product_mapping.get("product_id")
                        size_id = product_mapping.get("size_id")
                        quantity = product_mapping.get("quantity", 1)

                        if not product_id or size_id is None:
                            continue

                        # 从批量查询的映射中获取（避免N+1查询）
                        product = products_map.get(product_id)
                        size = sizes_map.get(size_id) if size_id > 0 else None

                        if not product or not size:
                            continue

                        # 获取该图片的路径（从批量查询的映射中获取）
                        image_path = None
                        if image_id != 0:
                            task = tasks_map.get(image_id)
                            if task and task.output_image_path:
                                image_path = task.output_image_path
                                logger.info(
                                    f"选片提交 - 从AITask获取图片路径: {image_path} (task_id={image_id})"
                                )

                        # 如果没找到，使用main_image_path作为后备
                        if not image_path:
                            image_path = main_image_path
                            logger.info(f"选片提交 - 使用main_image_path: {image_path}")

                        # 如果还是没有，跳过这个订单
                        if not image_path:
                            logger.info(
                                f"选片提交 - 警告: 无法获取图片路径，跳过订单创建 (image_id={image_id})"
                            )
                            continue

                        # 生成选片订单号
                        order_number = f"SEL{int(time.time() * 1000) + len(created_orders)}"
                        size_price = float(size.price)
                        total_price = size_price * quantity

                        # 创建选片订单（产品馆）
                        selection_order = SelectionOrder(
                            order_number=order_number,
                            original_order_id=order.id,
                            original_order_number=order.order_number,
                            customer_name=order.customer_name or "",
                            customer_phone=order.customer_phone or "",
                            openid=order.openid,
                            customer_address=order.customer_address or "",
                            product_id=product.id,
                            product_name=product.name,
                            size_id=size.id,
                            size_name=size.size_name,
                            image_url=image_path,
                            quantity=quantity,
                            price=size_price,
                            total_price=total_price,
                            status="pending",
                            customer_note=f"选片订单，照片ID: {image_id}, 产品: {product.name}",
                        )

                        db.session.add(selection_order)
                        created_orders.append(order_number)
                        logger.info(
                            f"选片提交 - 创建选片订单: {order_number}, 产品: {product.name}, 数量: {quantity}, 总价: {total_price}"
                        )

                # 支持旧格式：mapping是单个对象
                elif isinstance(mapping, dict):
                    if "imageId" in mapping:
                        image_id = mapping.get("imageId")
                        product_id = mapping.get("productId")
                        size_id = mapping.get("sizeId")
                    else:
                        product_id = mapping.get("productId") or mapping.get("product_id")
                        size_id = mapping.get("sizeId") or mapping.get("size_id")

                    if not product_id or size_id is None:
                        continue

                    product = products_map.get(product_id)
                    size = sizes_map.get(size_id) if size_id > 0 else None

                    if not product or not size:
                        continue

                    image_path = None
                    if image_id != 0:
                        task = tasks_map.get(image_id)
                        if task and task.output_image_path:
                            image_path = task.output_image_path

                    if not image_path:
                        image_path = main_image_path
                    if not image_path:
                        continue

                    order_number = f"SEL{int(time.time() * 1000) + len(created_orders)}"
                    size_price = float(size.price)

                    selection_order = SelectionOrder(
                        order_number=order_number,
                        original_order_id=order.id,
                        original_order_number=order.order_number,
                        customer_name=order.customer_name or "",
                        customer_phone=order.customer_phone or "",
                        openid=order.openid,
                        customer_address=order.customer_address or "",
                        product_id=product.id,
                        product_name=product.name,
                        size_id=size.id,
                        size_name=size.size_name,
                        image_url=image_path,
                        quantity=1,
                        price=size_price,
                        total_price=size_price,
                        status="pending",
                        customer_note=f"选片订单，照片ID: {image_id}, 产品: {product.name}",
                    )

                    db.session.add(selection_order)
                    created_orders.append(order_number)
        # 旧版本兼容：使用统一的产品和规格（产品馆）
        elif selected_product_id and selected_size_id:
            product = Product.query.get(selected_product_id)
            size = ProductSize.query.get(selected_size_id)

            if not product or not size:
                return jsonify({"success": False, "message": "产品或规格不存在"}), 400

            image_path = main_image_path
            if not image_path:
                return jsonify({"success": False, "message": "无法获取效果图路径"}), 400

            total_price = float(size.price) + extra_fee
            order_number = f"SEL{int(time.time() * 1000)}"

            selection_order = SelectionOrder(
                order_number=order_number,
                original_order_id=order.id,
                original_order_number=order.order_number,
                customer_name=order.customer_name or "",
                customer_phone=order.customer_phone or "",
                openid=order.openid,
                customer_address=order.customer_address or "",
                product_id=product.id,
                product_name=product.name,
                size_id=size.id,
                size_name=size.size_name,
                image_url=image_path,
                quantity=1,
                price=float(size.price),
                total_price=total_price,
                status="pending",
                customer_note=f"选片订单，选中{len(selected_image_ids)}张照片，免费{free_selection_count}张，超出{extra_count}张",
            )

            db.session.add(selection_order)
            created_orders.append(order_number)

        db.session.commit()

        # 更新原订单的选片状态（添加备注）
        if hasattr(order, "customer_note"):
            current_note = order.customer_note or ""
            selection_note = f"已选片：{len(selected_image_ids)}张，创建选片订单：{', '.join(created_orders)}"
            if current_note:
                order.customer_note = f"{current_note}\n{selection_note}"
            else:
                order.customer_note = selection_note

        # 更新订单状态为"选片已完成"
        if order.status in [
            "pending_selection",
            "ai_processing",
            "completed",
            "hd_ready",
            "processing",
            "manufacturing",
        ]:
            order.status = "selection_completed"

        db.session.commit()

        # 优化N+1查询：批量查询所有订单和尺寸，计算总价
        total_price = 0
        if created_orders and SelectionOrder and ProductSize:
            selection_orders = SelectionOrder.query.filter(
                SelectionOrder.order_number.in_(created_orders)
            ).all()
            if selection_orders:
                size_ids = [so.size_id for so in selection_orders if so.size_id]
                if size_ids:
                    sizes_map = {
                        s.id: s
                        for s in ProductSize.query.filter(ProductSize.id.in_(size_ids)).all()
                    }
                    total_price = sum(
                        [
                            float(sizes_map.get(so.size_id).price) * so.quantity
                            for so in selection_orders
                            if so.size_id and so.size_id in sizes_map
                        ]
                    )

        return jsonify(
            {
                "success": True,
                "message": f"选片成功，已创建{len(created_orders)}个选片订单",
                "selected_count": len(selected_image_ids),
                "free_count": free_selection_count,
                "extra_count": extra_count,
                "extra_fee": extra_fee,
                "created_orders": created_orders,
                "total_price": total_price,
            }
        )

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"提交选片结果失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"提交失败: {str(e)}"}), 500
