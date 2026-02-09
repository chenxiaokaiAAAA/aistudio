# -*- coding: utf-8 -*-
"""
选片页面 - 确认选片相关功能
包含：确认选片、审核、检查支付状态、跳过支付
"""

import logging

logger = logging.getLogger(__name__)
import glob
import os
from datetime import datetime
from urllib.parse import quote

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

from .utils import get_app_instance

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_confirm", __name__)


@bp.route("/admin/photo-selection/<int:order_id>/confirm")
@login_required
def photo_selection_confirm(order_id):
    """确认选片页面 - 选择产品和数量"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("photo_selection.photo_selection_list.photo_selection_list"))

    Order = models["Order"]
    AITask = models["AITask"]
    Product = models["Product"]
    ProductSize = models["ProductSize"]
    ProductStyleCategory = models.get("ProductStyleCategory")
    StyleImage = models.get("StyleImage")

    order = Order.query.get_or_404(order_id)

    # 获取选中的图片ID（从URL参数）
    selected_image_ids_str = request.args.get("images", "")
    if not selected_image_ids_str:
        flash("请先选择照片", "error")
        return redirect(
            url_for(
                "photo_selection.photo_selection_detail.photo_selection_detail", order_id=order_id
            )
        )

    selected_image_ids = [int(id) for id in selected_image_ids_str.split(",") if id.isdigit()]
    if not selected_image_ids:
        flash("请先选择照片", "error")
        return redirect(
            url_for(
                "photo_selection.photo_selection_detail.photo_selection_detail", order_id=order_id
            )
        )

    # 获取应用实例
    app = get_app_instance()

    # 获取选中的效果图
    effect_images = []
    task_ids = [img_id for img_id in selected_image_ids if img_id != 0]
    file_system_images = [img_id for img_id in selected_image_ids if img_id == 0]

    # 从AITask获取效果图
    if task_ids:
        selected_tasks = AITask.query.filter(
            AITask.id.in_(task_ids), AITask.order_id == order_id
        ).all()

        for task in selected_tasks:
            if task.output_image_path:
                logger.info(
                    f"🔍 [确认选片] 处理任务 {task.id}, output_image_path: {task.output_image_path}"
                )

                hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
                final_folder = app.config.get(
                    "FINAL_FOLDER", os.path.join(app.root_path, "final_works")
                )
                if not os.path.isabs(hd_folder):
                    hd_folder = os.path.join(app.root_path, hd_folder)
                if not os.path.isabs(final_folder):
                    final_folder = os.path.join(app.root_path, final_folder)

                # 检查是否是缩略图路径
                from app.utils.image_thumbnail import get_original_path, get_thumbnail_path

                original_path = get_original_path(task.output_image_path)
                thumbnail_path = get_thumbnail_path(original_path)

                # 尝试多个路径：原图、缩略图
                image_path = None
                image_filename = None

                # 1. 检查原图是否存在
                original_file = os.path.basename(original_path)
                if os.path.exists(os.path.join(hd_folder, original_file)):
                    image_path = os.path.join(hd_folder, original_file)
                    image_filename = original_file
                elif os.path.exists(os.path.join(final_folder, original_file)):
                    image_path = os.path.join(final_folder, original_file)
                    image_filename = original_file
                # 2. 检查缩略图是否存在
                elif task.output_image_path.endswith("_thumb.jpg"):
                    thumb_file = os.path.basename(task.output_image_path)
                    if os.path.exists(os.path.join(hd_folder, thumb_file)):
                        image_path = os.path.join(hd_folder, thumb_file)
                        image_filename = thumb_file
                    elif os.path.exists(os.path.join(final_folder, thumb_file)):
                        image_path = os.path.join(final_folder, thumb_file)
                        image_filename = thumb_file
                # 3. 直接使用output_image_path
                else:
                    direct_file = os.path.basename(task.output_image_path)
                    if os.path.exists(os.path.join(hd_folder, direct_file)):
                        image_path = os.path.join(hd_folder, direct_file)
                        image_filename = direct_file
                    elif os.path.exists(os.path.join(final_folder, direct_file)):
                        image_path = os.path.join(final_folder, direct_file)
                        image_filename = direct_file

                if image_path and image_filename:
                    from urllib.parse import quote

                    # 优先使用缩略图URL（如果存在）
                    thumbnail_filename = get_thumbnail_path(image_filename)
                    if thumbnail_filename and os.path.exists(
                        os.path.join(hd_folder, thumbnail_filename)
                    ):
                        encoded_filename = quote(thumbnail_filename, safe="")
                        image_url = f"/public/hd/{encoded_filename}"
                        logger.info(f"✅ [确认选片] 使用缩略图: {thumbnail_filename}")
                    else:
                        encoded_filename = quote(image_filename, safe="")
                        image_url = f"/public/hd/{encoded_filename}"
                        logger.info(f"✅ [确认选片] 使用原图: {image_filename}")

                    effect_images.append({
                        "id": task.id,
                        "url": image_url,
                        "path": image_filename,
                        "style_category_id": task.style_category_id,
                    })
                    logger.info(f"✅ [确认选片] 添加效果图: task_id={task.id}, style_category_id={task.style_category_id}, url={image_url}")
                else:
                    logger.warning(
                        f"[确认选片] 图片文件不存在: {task.output_image_path} (在HD_FOLDER和FINAL_FOLDER中均未找到)"
                    )
                    # 即使文件不存在，也添加（可能是云端文件，通过URL访问）
                    encoded_filename = quote(os.path.basename(task.output_image_path), safe="")
                    image_url = f"/public/hd/{encoded_filename}"
                    effect_images.append({
                        "id": task.id,
                        "url": image_url,
                        "path": os.path.basename(task.output_image_path),
                        "style_category_id": task.style_category_id,
                    })
                    logger.warning(
                        f"[确认选片] 添加效果图（文件不存在，可能是云端）: task_id={task.id}, url={image_url}"
                    )

    # 从文件系统获取效果图
    if file_system_images or (not task_ids and selected_image_ids):
        try:
            hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)

            if os.path.exists(hd_folder):
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                effect_files = glob.glob(pattern)
                effect_files.sort(key=os.path.getmtime, reverse=True)

                for filepath in effect_files[: len(selected_image_ids)]:
                    filename = os.path.basename(filepath)
                    encoded_filename = quote(filename, safe="")
                    image_url = f"/public/hd/{encoded_filename}"

                    # 文件系统图片：尝试从订单 style_name 解析风格分类
                    style_category_id = None
                    if order.style_name and StyleImage:
                        style_img = StyleImage.query.filter(
                            StyleImage.name == order.style_name, StyleImage.is_active == True
                        ).first()
                        if style_img:
                            style_category_id = style_img.category_id
                    effect_images.append({
                        "id": 0,
                        "url": image_url,
                        "path": filename,
                        "style_category_id": style_category_id,
                    })
        except Exception as e:
            logger.info(f"从文件系统读取效果图失败: {e}")

    # 获取产品馆产品，按订单所有商品的一级/二级分类过滤（同一订单号可能含多个商品）
    ProductCategory = models.get("ProductCategory")
    ProductSubcategory = models.get("ProductSubcategory")
    gallery_query = Product.query.filter_by(is_active=True).order_by(Product.sort_order.asc())
    order_category_ids = set()
    order_subcategory_ids = set()
    # 同一订单号可能有多条 Order 记录（多个商品），需收集所有商品的分类
    same_number_orders = Order.query.filter_by(order_number=order.order_number).all()
    order_product_names = list({o.product_name for o in same_number_orders if o.product_name})
    for pname in order_product_names:
        # 1. 根据 product_name 查找产品，获取其分类
        order_product = Product.query.filter(
            Product.name == pname, Product.is_active == True
        ).first()
        if not order_product:
            order_product = Product.query.filter(
                Product.name.like(f"%{pname}%"),
                Product.is_active == True,
            ).first()
        if not order_product and hasattr(Product, "code"):
            order_product = Product.query.filter(
                Product.code == pname, Product.is_active == True
            ).first()
        if order_product:
            if order_product.category_id:
                order_category_ids.add(order_product.category_id)
            if order_product.subcategory_id:
                order_subcategory_ids.add(order_product.subcategory_id)
        elif ProductCategory:
            # 2. 若未找到产品，尝试匹配一级分类名（如 "证件照" 可能是分类名）
            order_cat = ProductCategory.query.filter(
                ProductCategory.name == pname,
                ProductCategory.is_active == True,
            ).first()
            if not order_cat:
                order_cat = ProductCategory.query.filter(
                    ProductCategory.name.like(f"%{pname}%"),
                    ProductCategory.is_active == True,
                ).first()
            if order_cat:
                order_category_ids.add(order_cat.id)
    if order_category_ids or order_subcategory_ids:
        # 优先按二级分类过滤：有二级分类时只显示该二级分类下的产品（如证件照-标准证件照只显示1个产品）
        # 无二级分类时退回到一级分类
        if order_subcategory_ids:
            gallery_query = gallery_query.filter(
                Product.subcategory_id.in_(order_subcategory_ids)
            )
            logger.info(
                f"🔍 [确认选片] 按订单商品二级分类过滤: {order_product_names} -> "
                f"subcategory_ids={order_subcategory_ids}"
            )
        else:
            gallery_query = gallery_query.filter(
                Product.category_id.in_(order_category_ids)
            )
            logger.info(
                f"🔍 [确认选片] 按订单商品一级分类过滤: {order_product_names} -> "
                f"category_ids={order_category_ids}"
            )
    gallery_products = gallery_query.all()
    products_data = []
    for product in gallery_products:
        sizes = (
            ProductSize.query.filter_by(product_id=product.id, is_active=True)
            .order_by(ProductSize.sort_order.asc())
            .all()
        )
        products_data.append(
            {
                "id": product.id,
                "name": product.name,
                "image_url": product.image_url or "",
                "sizes": [
                    {"id": s.id, "name": s.size_name, "price": float(s.price)} for s in sizes
                ],
            }
        )

    # 按风格过滤产品：每张照片只能添加其风格绑定的产品（在订单分类过滤的基础上再过滤）
    # style_products_map: {style_category_id: [products]}，key 统一为字符串避免 JSON 序列化错误
    style_products_map = {}
    style_category_ids = {
        img.get("style_category_id")
        for img in effect_images
        if img.get("style_category_id") is not None
    }
    if ProductStyleCategory and style_category_ids:
        for sc_id in style_category_ids:
            bindings = ProductStyleCategory.query.filter_by(
                style_category_id=sc_id
            ).all()
            bound_product_ids = {b.product_id for b in bindings}
            # 只保留启用的、有绑定的产品，key 用字符串
            style_products_map[str(sc_id)] = [
                p for p in products_data
                if p["id"] in bound_product_ids
            ]
    # 无风格约束时（style_category_id 为 null）使用全部产品（key 用 "all" 便于前端）
    style_products_map["all"] = products_data

    # 获取产品的免费选片张数
    free_selection_count = 1  # 默认1张
    if Product and order.product_name:
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        if product and hasattr(product, "free_selection_count"):
            free_selection_count = product.free_selection_count or 1

    return render_template(
        "admin/photo_selection_confirm.html",
        order=order,
        effect_images=effect_images,
        products_data=products_data,
        style_products_map=style_products_map,
        free_selection_count=free_selection_count,
    )


@bp.route("/admin/photo-selection/<int:order_id>/review")
@login_required
@admin_required
def photo_selection_review(order_id):
    """产品详情页 - 确认选片和支付"""

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("photo_selection.photo_selection_list.photo_selection_list"))

    Order = models["Order"]
    AITask = models["AITask"]

    order = Order.query.get_or_404(order_id)

    # 获取应用实例
    app = get_app_instance()

    # 获取订单的所有已完成的效果图
    ai_tasks = (
        AITask.query.filter_by(order_id=order.id, status="completed")
        .filter(AITask.output_image_path.isnot(None))
        .all()
    )

    # 构建效果图列表
    effect_images = []
    for task in ai_tasks:
        if task.output_image_path:
            hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)

            image_path = os.path.join(hd_folder, task.output_image_path)
            if os.path.exists(image_path):
                encoded_filename = quote(task.output_image_path, safe="")
                image_url = f"/public/hd/{encoded_filename}"

                effect_images.append(
                    {
                        "id": task.id,
                        "url": image_url,
                        "path": task.output_image_path,
                        "created_at": task.completed_at or task.created_at,
                    }
                )

    # 如果AITask中没有效果图，尝试从文件系统读取
    if len(effect_images) == 0:
        try:
            hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)

            if os.path.exists(hd_folder):
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                effect_files = glob.glob(pattern)
                effect_files.sort(key=os.path.getmtime, reverse=True)

                for filepath in effect_files:
                    filename = os.path.basename(filepath)
                    encoded_filename = quote(filename, safe="")
                    image_url = f"/public/hd/{encoded_filename}"

                    effect_images.append(
                        {
                            "id": 0,
                            "url": image_url,
                            "path": filename,
                            "created_at": datetime.fromtimestamp(os.path.getmtime(filepath)),
                        }
                    )
        except Exception as e:
            logger.info(f"从文件系统读取效果图失败: {e}")

    # 获取产品的免费选片张数和额外照片价格
    free_selection_count = 1
    extra_photo_price = 10.0
    if order.product_name:
        Product = models["Product"]
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        if product:
            if hasattr(product, "free_selection_count"):
                free_selection_count = product.free_selection_count or 1
            if hasattr(product, "extra_photo_price"):
                extra_photo_price = product.extra_photo_price or 10.0

    return render_template(
        "admin/photo_selection_review.html",
        order=order,
        effect_images=effect_images,
        free_selection_count=free_selection_count,
        extra_photo_price=extra_photo_price,
    )


@bp.route("/admin/photo-selection/<int:order_id>/check-payment", methods=["GET"])
@login_required
def check_payment_status(order_id):
    """检查支付状态"""
    if current_user.role not in ["admin", "operator"]:
        return jsonify({"paid": False, "message": "权限不足"}), 403

    models = get_models()
    if not models:
        return jsonify({"paid": False, "message": "系统未初始化"}), 500

    SelectionOrder = models.get("SelectionOrder")
    if not SelectionOrder:
        return jsonify({"paid": False, "message": "选片订单功能未启用"}), 400

    try:
        order_numbers = request.args.get("orders", "").split(",")
        order_numbers = [o.strip() for o in order_numbers if o.strip()]

        if not order_numbers:
            return jsonify({"paid": False, "message": "订单号不能为空"}), 400

        # 检查所有选片订单是否都已支付
        orders = SelectionOrder.query.filter(
            SelectionOrder.order_number.in_(order_numbers)
        ).all()

        if len(orders) == 0:
            return jsonify({"paid": False, "message": "订单不存在"}), 404

        # 检查是否所有订单都已支付
        all_paid = all(order.status == "paid" for order in orders)

        return jsonify(
            {
                "paid": all_paid,
                "orders": [{"order_number": o.order_number, "status": o.status} for o in orders],
            }
        )

    except Exception as e:
        logger.info(f"检查支付状态失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"paid": False, "message": f"检查失败: {str(e)}"}), 500


@bp.route("/admin/photo-selection/<int:order_id>/skip-payment", methods=["POST"])
@login_required
@admin_required
def skip_payment(order_id):
    """跳过支付（测试模式）"""

    models = get_models()
    if not models:
        return jsonify({"success": False, "message": "系统未初始化"}), 500

    SelectionOrder = models.get("SelectionOrder")
    if not SelectionOrder:
        return jsonify({"success": False, "message": "选片订单功能未启用"}), 400

    try:
        data = request.get_json()
        order_numbers = data.get("order_numbers", [])

        if not order_numbers:
            return jsonify({"success": False, "message": "订单号不能为空"}), 400

        # 检查支付配置是否允许跳过
        from app.utils.config_loader import get_config_value

        db = models["db"]
        AIConfig = models.get("AIConfig")
        test_mode = get_config_value("payment_test_mode", "true", db=db, AIConfig=AIConfig)
        skip_payment_enabled = get_config_value(
            "payment_skip_payment", "true", db=db, AIConfig=AIConfig
        )

        if test_mode.lower() != "true" or skip_payment_enabled.lower() != "true":
            return jsonify({"success": False, "message": "当前不是测试模式，无法跳过支付"}), 400

        # 更新选片订单状态为已支付
        orders = SelectionOrder.query.filter(
            SelectionOrder.order_number.in_(order_numbers)
        ).all()

        if len(orders) == 0:
            return jsonify({"success": False, "message": "订单不存在"}), 404

        for order in orders:
            order.status = "paid"
            if hasattr(order, "payment_time"):
                order.payment_time = datetime.now()
            if hasattr(order, "transaction_id"):
                order.transaction_id = f"TEST_{int(datetime.now().timestamp())}"

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "支付已跳过（测试模式）",
                "orders": [o.order_number for o in orders],
            }
        )

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"跳过支付失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"跳过支付失败: {str(e)}"}), 500
