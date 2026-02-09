# -*- coding: utf-8 -*-
"""
管理后台商城产品管理API路由
"""

import logging

logger = logging.getLogger(__name__)
import json
import os
import sys
import uuid
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_shop_bp = Blueprint("admin_shop", __name__)


@admin_shop_bp.route("/admin/shop/products", methods=["GET", "POST"])
@login_required
def admin_shop_products():
    """商城产品管理页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    db = models["db"]
    ShopProduct = models["ShopProduct"]
    ShopProductImage = models["ShopProductImage"]
    ShopProductSize = models["ShopProductSize"]
    app = models["app"]

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_product":
            # 添加商城产品
            code = request.form.get("code")
            name = request.form.get("name")
            description = request.form.get("description", "")
            category = request.form.get("category", "")
            sort_order = int(request.form.get("sort_order", 0))

            # 检查代码是否已存在
            if ShopProduct.query.filter_by(code=code).first():
                flash(f"产品代码 {code} 已存在", "error")
                return redirect(url_for("admin_shop.admin_shop_products"))

            # 处理主图上传
            image_url = ""
            if "product_image" in request.files:
                file = request.files["product_image"]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    static_products_dir = os.path.join(
                        app.root_path, "static", "images", "shop_products"
                    )
                    os.makedirs(static_products_dir, exist_ok=True)
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_url = f"/static/images/shop_products/{unique_filename}"

            # 创建产品
            new_product = ShopProduct(
                code=code,
                name=name,
                description=description,
                category=category,
                image_url=image_url,
                sort_order=sort_order,
                is_active=True,
            )
            db.session.add(new_product)
            db.session.flush()

            # 处理多图上传
            uploaded_files = request.files.getlist("product_images[]")
            for i, file in enumerate(uploaded_files):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    static_products_dir = os.path.join(
                        app.root_path, "static", "images", "shop_products"
                    )
                    os.makedirs(static_products_dir, exist_ok=True)
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_url_item = f"/static/images/shop_products/{unique_filename}"

                    db.session.add(
                        ShopProductImage(
                            product_id=new_product.id,
                            image_url=image_url_item,
                            sort_order=i,
                            is_active=True,
                        )
                    )

            # 处理规格数据
            size_names = request.form.getlist("size_name[]")
            size_prices = request.form.getlist("size_price[]")
            size_stocks = request.form.getlist("size_stock[]")
            size_effect_images = request.files.getlist("size_effect_image[]")

            for i, (size_name, size_price, size_stock) in enumerate(
                zip(size_names, size_prices, size_stocks)
            ):
                if size_name and size_price:
                    try:
                        price = float(size_price)
                        stock = int(size_stock) if size_stock else 0

                        # 处理效果图上传
                        effect_image_url = ""
                        if i < len(size_effect_images):
                            effect_file = size_effect_images[i]
                            if effect_file and effect_file.filename:
                                filename = secure_filename(effect_file.filename)
                                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                                static_products_dir = os.path.join(
                                    app.root_path, "static", "images", "shop_products"
                                )
                                os.makedirs(static_products_dir, exist_ok=True)
                                file_path = os.path.join(static_products_dir, unique_filename)
                                effect_file.save(file_path)
                                effect_image_url = f"/static/images/shop_products/{unique_filename}"

                        db.session.add(
                            ShopProductSize(
                                product_id=new_product.id,
                                size_name=size_name,
                                price=price,
                                stock=stock,
                                effect_image_url=effect_image_url,
                                sort_order=i,
                                is_active=True,
                            )
                        )
                    except ValueError:
                        pass

            db.session.commit()
            flash("商城产品添加成功", "success")
            return redirect(url_for("admin_shop.admin_shop_products"))

        elif action == "edit_product":
            # 编辑商城产品
            product_id = int(request.form.get("product_id"))
            product = ShopProduct.query.get_or_404(product_id)

            product.code = request.form.get("code")
            product.name = request.form.get("name")
            product.description = request.form.get("description", "")
            product.category = request.form.get("category", "")
            product.sort_order = int(request.form.get("sort_order", 0))

            # 处理主图上传
            if "product_image" in request.files:
                file = request.files["product_image"]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    static_products_dir = os.path.join(
                        app.root_path, "static", "images", "shop_products"
                    )
                    os.makedirs(static_products_dir, exist_ok=True)
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    product.image_url = f"/static/images/shop_products/{unique_filename}"

            # 处理多图上传
            uploaded_files = request.files.getlist("product_images[]")
            existing_image_count = ShopProductImage.query.filter_by(product_id=product_id).count()
            for i, file in enumerate(uploaded_files):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    static_products_dir = os.path.join(
                        app.root_path, "static", "images", "shop_products"
                    )
                    os.makedirs(static_products_dir, exist_ok=True)
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_url_item = f"/static/images/shop_products/{unique_filename}"

                    db.session.add(
                        ShopProductImage(
                            product_id=product_id,
                            image_url=image_url_item,
                            sort_order=existing_image_count + i,
                            is_active=True,
                        )
                    )

            # 更新规格数据
            size_ids = request.form.getlist("size_id[]")
            size_names = request.form.getlist("size_name[]")
            size_prices = request.form.getlist("size_price[]")
            size_stocks = request.form.getlist("size_stock[]")
            size_effect_image_urls = request.form.getlist(
                "size_effect_image_url[]"
            )  # 现有的效果图URL
            size_effect_images = request.files.getlist("size_effect_image[]")  # 新上传的效果图

            # 确保所有数组长度一致（以size_names为准，因为它是必填的）
            max_len = len(size_names)
            logger.info(f"📝 处理规格数据: 共 {max_len} 个规格")
            logger.info(f"   - size_ids: {size_ids}")
            logger.info(f"   - size_names: {size_names}")
            logger.info(f"   - size_prices: {size_prices}")
            logger.info(f"   - size_stocks: {size_stocks}")
            logger.info(f"   - size_effect_image_urls: {size_effect_image_urls}")
            logger.info(f"   - size_effect_images 数量: {len(size_effect_images)}")

            # 删除不存在的规格
            existing_size_ids = [int(sid) for sid in size_ids if sid]
            if existing_size_ids:
                ShopProductSize.query.filter(
                    ShopProductSize.product_id == product_id,
                    ~ShopProductSize.id.in_(existing_size_ids),
                ).delete(synchronize_session=False)

            # 更新或添加规格 - 使用索引遍历，确保每个规格都正确处理
            for i in range(max_len):
                size_id = size_ids[i] if i < len(size_ids) else ""
                size_name = size_names[i] if i < len(size_names) else ""
                size_price = size_prices[i] if i < len(size_prices) else ""
                size_stock = size_stocks[i] if i < len(size_stocks) else "0"

                if not size_name or not size_price:
                    logger.warning("跳过第 {i+1} 个规格: 名称或价格为空")
                    continue

                try:
                    price = float(size_price)
                    stock = int(size_stock) if size_stock else 0

                    # 处理效果图：优先使用新上传的，否则使用现有的URL
                    effect_image_url = ""

                    # 先获取现有的URL（如果有）
                    existing_url = ""
                    if i < len(size_effect_image_urls):
                        existing_url = size_effect_image_urls[i] or ""

                    # 检查是否有新上传的效果图（文件对象存在且有文件名）
                    has_new_image = False
                    if i < len(size_effect_images):
                        effect_file = size_effect_images[i]
                        # 检查文件是否真的被选择了（有文件名且不是空字符串）
                        if (
                            effect_file
                            and hasattr(effect_file, "filename")
                            and effect_file.filename
                        ):
                            # 有新上传的效果图，使用新的
                            filename = secure_filename(effect_file.filename)
                            unique_filename = f"{uuid.uuid4().hex}_{filename}"
                            static_products_dir = os.path.join(
                                app.root_path, "static", "images", "shop_products"
                            )
                            os.makedirs(static_products_dir, exist_ok=True)
                            file_path = os.path.join(static_products_dir, unique_filename)
                            effect_file.save(file_path)
                            effect_image_url = f"/static/images/shop_products/{unique_filename}"
                            has_new_image = True
                            logger.info(f"✅ 第 {i + 1} 个规格上传新效果图: {effect_image_url}")

                    # 如果没有新上传的，使用现有的URL
                    if not has_new_image and existing_url:
                        effect_image_url = existing_url
                        logger.info(f"📷 第 {i + 1} 个规格使用现有效果图: {effect_image_url}")
                    elif not has_new_image and not existing_url:
                        logger.warning("第 {i+1} 个规格没有效果图")

                    if size_id:
                        # 更新现有规格
                        size = ShopProductSize.query.get(int(size_id))
                        if size:
                            size.size_name = size_name
                            size.price = price
                            size.stock = stock
                            size.effect_image_url = effect_image_url
                            size.sort_order = i
                            logger.info(
                                f"✅ 更新规格 ID={size_id}: {size_name}, 价格={price}, 效果图={effect_image_url}"
                            )
                        else:
                            logger.warning("规格 ID={size_id} 不存在，将创建新规格")
                            # 如果ID不存在，创建新规格
                            db.session.add(
                                ShopProductSize(
                                    product_id=product_id,
                                    size_name=size_name,
                                    price=price,
                                    stock=stock,
                                    effect_image_url=effect_image_url,
                                    sort_order=i,
                                    is_active=True,
                                )
                            )
                    else:
                        # 添加新规格
                        db.session.add(
                            ShopProductSize(
                                product_id=product_id,
                                size_name=size_name,
                                price=price,
                                stock=stock,
                                effect_image_url=effect_image_url,
                                sort_order=i,
                                is_active=True,
                            )
                        )
                        logger.info(
                            f"✅ 添加新规格: {size_name}, 价格={price}, 效果图={effect_image_url}"
                        )
                except (ValueError, TypeError) as e:
                    logger.error("处理第 {i+1} 个规格时出错: {e}")
                    import traceback

                    traceback.print_exc()
                    pass

            db.session.commit()
            flash("商城产品更新成功", "success")
            return redirect(url_for("admin_shop.admin_shop_products"))

        elif action == "delete_product":
            # 删除商城产品
            product_id = int(request.form.get("product_id"))
            product = ShopProduct.query.get_or_404(product_id)

            # 删除关联的图片和规格
            ShopProductImage.query.filter_by(product_id=product_id).delete()
            ShopProductSize.query.filter_by(product_id=product_id).delete()

            db.session.delete(product)
            db.session.commit()
            flash("商城产品删除成功", "success")
            return redirect(url_for("admin_shop.admin_shop_products"))

        elif action == "toggle_active":
            # 切换启用状态
            product_id = int(request.form.get("product_id"))
            product = ShopProduct.query.get_or_404(product_id)
            product.is_active = not product.is_active
            db.session.commit()
            flash("状态更新成功", "success")
            return redirect(url_for("admin_shop.admin_shop_products"))

    # GET请求：显示产品列表
    products = ShopProduct.query.order_by(ShopProduct.sort_order.asc(), ShopProduct.id.desc()).all()

    # 优化N+1查询：批量加载关联数据
    product_ids = [product.id for product in products]

    # 批量查询所有产品的图片
    images_map = {}
    if product_ids:
        all_images = (
            ShopProductImage.query.filter(
                ShopProductImage.product_id.in_(product_ids), ShopProductImage.is_active
            )
            .order_by(ShopProductImage.sort_order.asc())
            .all()
        )
        for image in all_images:
            if image.product_id not in images_map:
                images_map[image.product_id] = []
            images_map[image.product_id].append(image)

    # 批量查询所有产品的尺寸
    sizes_map = {}
    if product_ids:
        all_sizes = (
            ShopProductSize.query.filter(
                ShopProductSize.product_id.in_(product_ids), ShopProductSize.is_active
            )
            .order_by(ShopProductSize.sort_order.asc())
            .all()
        )
        for size in all_sizes:
            if size.product_id not in sizes_map:
                sizes_map[size.product_id] = []
            sizes_map[size.product_id].append(size)

    # 为每个产品分配关联数据（避免N+1查询）
    for product in products:
        product.images_list = images_map.get(product.id, [])
        product.sizes_list = sizes_map.get(product.id, [])

    return render_template("admin/shop_products.html", products=products)


@admin_shop_bp.route("/admin/shop/products/<int:product_id>", methods=["GET"])
@login_required
def admin_shop_product_detail(product_id):
    """获取商城产品详情（API）"""
    if current_user.role not in ["admin", "operator"]:
        return jsonify({"status": "error", "message": "无权限"}), 403

    models = get_models()
    if not models:
        return jsonify({"status": "error", "message": "系统未初始化"}), 500

    ShopProduct = models["ShopProduct"]
    ShopProductImage = models["ShopProductImage"]
    ShopProductSize = models["ShopProductSize"]

    product = ShopProduct.query.get_or_404(product_id)

    # 获取关联数据
    images = (
        ShopProductImage.query.filter_by(product_id=product_id, is_active=True)
        .order_by(ShopProductImage.sort_order.asc())
        .all()
    )

    sizes = (
        ShopProductSize.query.filter_by(product_id=product_id, is_active=True)
        .order_by(ShopProductSize.sort_order.asc())
        .all()
    )

    return jsonify(
        {
            "status": "success",
            "data": {
                "id": product.id,
                "code": product.code,
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "image_url": product.image_url,
                "is_active": product.is_active,
                "sort_order": product.sort_order,
                "images": [
                    {"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order}
                    for img in images
                ],
                "sizes": [
                    {
                        "id": size.id,
                        "size_name": size.size_name,
                        "price": size.price,
                        "stock": size.stock,
                        "effect_image_url": size.effect_image_url,
                        "sort_order": size.sort_order,
                    }
                    for size in sizes
                ],
            },
        }
    )


@admin_shop_bp.route("/admin/shop/orders", methods=["GET"])
@login_required
def admin_shop_orders():
    """商城订单管理页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    ShopOrder = models["ShopOrder"]

    # 获取筛选参数
    status = request.args.get("status", "")
    search = request.args.get("search", "")

    query = ShopOrder.query

    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (ShopOrder.order_number.like(f"%{search}%"))
            | (ShopOrder.customer_name.like(f"%{search}%"))
            | (ShopOrder.customer_phone.like(f"%{search}%"))
        )

    # 尝试按created_at排序，如果字段不存在则按id排序
    try:
        orders = query.order_by(ShopOrder.created_at.desc()).all()
    except AttributeError:
        # 如果created_at字段不存在，按id排序
        orders = query.order_by(ShopOrder.id.desc()).all()

    return render_template("admin/shop_orders.html", orders=orders, status=status, search=search)


@admin_shop_bp.route("/admin/shop/orders/<int:order_id>", methods=["GET"])
@login_required
def admin_shop_order_detail(order_id):
    """商城订单详情页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    ShopOrder = models["ShopOrder"]
    Order = models.get("Order")
    AITask = models.get("AITask")

    # 获取商城订单
    shop_order = ShopOrder.query.get_or_404(order_id)

    # 获取关联的原始订单（如果存在）
    original_order = None
    if shop_order.original_order_id and Order:
        original_order = Order.query.get(shop_order.original_order_id)

    # 获取该原始订单的所有商城订单（按图片分组）
    selected_images = []
    if original_order:
        # 查询该原始订单的所有商城订单
        all_shop_orders = (
            ShopOrder.query.filter_by(original_order_id=original_order.id)
            .order_by(
                ShopOrder.created_at.asc()
                if hasattr(ShopOrder, "created_at")
                else ShopOrder.id.asc()
            )
            .all()
        )

        # 按图片路径分组
        images_dict = {}
        for so in all_shop_orders:
            image_path = so.image_url
            if image_path:
                if image_path in images_dict:
                    images_dict[image_path]["products"].append(
                        {
                            "order_number": so.order_number,
                            "product_id": so.product_id,
                            "product_name": so.product_name or "",
                            "size_id": so.size_id,
                            "size_name": so.size_name or "",
                            "quantity": so.quantity or 1,
                            "price": float(so.price or 0),
                            "total_price": float(so.price or 0) * (so.quantity or 1),
                            "status": so.status,
                        }
                    )
                else:
                    from urllib.parse import quote

                    encoded_filename = quote(image_path, safe="")
                    image_url = f"/public/hd/{encoded_filename}"

                    images_dict[image_path] = {
                        "image_url": image_url,
                        "image_path": so.image_url,
                        "products": [
                            {
                                "order_number": so.order_number,
                                "product_id": so.product_id,
                                "product_name": so.product_name or "",
                                "size_id": so.size_id,
                                "size_name": so.size_name or "",
                                "quantity": so.quantity or 1,
                                "price": float(so.price or 0),
                                "total_price": float(so.price or 0) * (so.quantity or 1),
                                "status": so.status,
                            }
                        ],
                    }

        selected_images = list(images_dict.values())

    return render_template(
        "admin/shop_order_detail.html",
        shop_order=shop_order,
        original_order=original_order,
        selected_images=selected_images,
    )
