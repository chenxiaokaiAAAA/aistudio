# -*- coding: utf-8 -*-
"""
管理后台产品配置API路由模块（主文件）
整合所有产品管理相关的子模块
"""

import logging

logger = logging.getLogger(__name__)
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

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
admin_products_bp = Blueprint("admin_products", __name__)


@admin_products_bp.route("/admin/products", methods=["GET"])
@login_required
@admin_required
def admin_products():
    """产品管理页面（三栏布局）"""
    models = get_models(["Product", "ProductCategory", "ProductSubcategory", "StyleCategory"])
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    Product = models["Product"]
    ProductCategory = models.get("ProductCategory")
    ProductSubcategory = models.get("ProductSubcategory")
    StyleCategory = models["StyleCategory"]

    # 获取产品列表
    try:
        products = (
            Product.query.filter_by(is_active=True)
            .order_by(Product.sort_order.asc(), Product.id.asc())
            .all()
        )
    except Exception as e:
        logger.info(f"获取产品列表失败: {e}")
        products = []

    # 获取分类数据
    product_categories = []
    product_subcategories = []
    if ProductCategory:
        product_categories = (
            ProductCategory.query.filter_by(is_active=True)
            .order_by(ProductCategory.sort_order.asc())
            .all()
        )
    if ProductSubcategory:
        product_subcategories = (
            ProductSubcategory.query.filter_by(is_active=True)
            .order_by(ProductSubcategory.sort_order.asc())
            .all()
        )

    # 按一级分类组织二级分类（转换为字典格式以便JSON序列化）
    subcategories_by_category = {}
    for subcat in product_subcategories:
        if subcat.category_id not in subcategories_by_category:
            subcategories_by_category[subcat.category_id] = []
        subcategories_by_category[subcat.category_id].append(
            {
                "id": subcat.id,
                "category_id": subcat.category_id,
                "name": subcat.name,
                "code": subcat.code,
                "icon": subcat.icon or "",
                "image_url": subcat.image_url or "",
                "sort_order": subcat.sort_order or 0,
                "is_active": subcat.is_active,
            }
        )

    # 获取风格分类
    style_categories = (
        StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order.asc()).all()
    )

    # 获取产品与风格分类的绑定关系（优化N+1查询）
    ProductStyleCategory = models.get("ProductStyleCategory")
    product_style_bindings = {}
    if ProductStyleCategory and products:
        # 批量查询所有产品的风格分类绑定（避免N+1查询）
        product_ids = [product.id for product in products]
        all_bindings = ProductStyleCategory.query.filter(
            ProductStyleCategory.product_id.in_(product_ids)
        ).all()

        # 构建映射：product_id -> [style_category_id, ...]
        for binding in all_bindings:
            if binding.product_id not in product_style_bindings:
                product_style_bindings[binding.product_id] = []
            product_style_bindings[binding.product_id].append(int(binding.style_category_id))

        # 确保所有产品都有绑定列表（即使为空）
        for product in products:
            if product.id not in product_style_bindings:
                product_style_bindings[product.id] = []
            logger.debug(
                f"📋 产品 {product.name} (ID: {product.id}) 绑定的风格分类: {product_style_bindings[product.id]} (总数: {len(product_style_bindings[product.id])})"
            )

    return render_template(
        "admin/products.html",
        products=products,
        product_categories=product_categories,
        subcategories_by_category=subcategories_by_category,
        style_categories=style_categories,
        product_style_bindings=product_style_bindings,
    )


@admin_products_bp.route("/api/admin/products/<int:product_id>", methods=["GET"])
@login_required
@admin_required
def admin_get_product_detail(product_id):
    """获取产品详情（API）"""
    try:
        models = get_models(
            ["Product", "ProductSize", "ProductImage", "ProductStyleCategory", "ProductCustomField"]
        )
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Product = models["Product"]
        ProductSize = models["ProductSize"]
        ProductImage = models["ProductImage"]
        ProductStyleCategory = models["ProductStyleCategory"]
        ProductCustomField = models["ProductCustomField"]

        product = Product.query.get_or_404(product_id)

        # 获取产品尺寸
        sizes = (
            ProductSize.query.filter_by(product_id=product_id, is_active=True)
            .order_by(ProductSize.sort_order.asc())
            .all()
        )

        # 获取产品图片
        images = (
            ProductImage.query.filter_by(product_id=product_id)
            .order_by(ProductImage.sort_order.asc())
            .all()
        )

        # 获取风格分类绑定
        style_bindings = ProductStyleCategory.query.filter_by(product_id=product_id).all()

        # 获取自定义字段
        custom_fields = (
            ProductCustomField.query.filter_by(product_id=product_id)
            .order_by(ProductCustomField.sort_order.asc())
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
                    "image_url": product.image_url,
                    "is_active": product.is_active,
                    "sort_order": product.sort_order,
                    "free_selection_count": getattr(product, "free_selection_count", 1),
                    "extra_photo_price": getattr(product, "extra_photo_price", 10.0),
                    "category_id": getattr(product, "category_id", None),
                    "subcategory_id": getattr(product, "subcategory_id", None),
                    "sizes": [
                        {
                            "id": size.id,
                            "size_name": size.size_name,
                            "price": float(size.price),
                            "printer_product_id": size.printer_product_id,
                            "effect_image_url": size.effect_image_url,
                            "sort_order": size.sort_order,
                        }
                        for size in sizes
                    ],
                    "images": [
                        {"id": img.id, "image_url": img.image_url, "sort_order": img.sort_order}
                        for img in images
                    ],
                    "style_category_ids": [binding.style_category_id for binding in style_bindings],
                    "custom_fields": [
                        {
                            "id": field.id,
                            "field_name": field.field_name,
                            "field_type": field.field_type,
                            "field_options": field.field_options,
                            "is_required": field.is_required,
                            "sort_order": field.sort_order,
                        }
                        for field in custom_fields
                    ],
                },
            }
        )
    except Exception as e:
        logger.info(f"获取产品详情失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取产品详情失败: {str(e)}"}), 500


@admin_products_bp.route("/admin/sizes", methods=["GET", "POST"])
@login_required
@admin_required
def admin_sizes():
    """产品配置管理页面（已废弃，重定向到新页面）"""
    # POST请求需要处理，GET请求才重定向
    if request.method == "GET":
        return redirect(url_for("admin_products.admin_products"))

    # POST请求继续处理（保留原有逻辑）

    # 以下代码已废弃，保留作为备份
    logger.info(f"🔵 admin_sizes函数被调用 - 方法: {request.method}")
    logger.info(f"🔵 请求URL: {request.url}")
    logger.info(f"🔵 请求路径: {request.path}")

    if current_user.role not in ["admin", "operator"]:
        logger.warning("用户权限不足")
        return redirect(url_for("auth.login"))

    models = get_models(
        [
            "Product",
            "ProductSize",
            "ProductImage",
            "ProductSizePetOption",
            "ProductStyleCategory",
            "ProductCustomField",
            "StyleCategory",
            "Order",
            "db",
        ]
    )
    if not models:
        logger.warning("系统未初始化")
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    db = models["db"]
    Product = models["Product"]
    ProductSize = models["ProductSize"]
    ProductImage = models["ProductImage"]
    ProductSizePetOption = models["ProductSizePetOption"]
    ProductStyleCategory = models["ProductStyleCategory"]
    ProductCustomField = models["ProductCustomField"]
    StyleCategory = models["StyleCategory"]
    Order = models["Order"]
    # 使用 current_app 替代 models['app']，更可靠
    app = models.get("app", current_app)

    if request.method == "POST":
        logger.info(f"📥 POST请求到达 - Content-Type: {request.content_type}")
        logger.info(f"📥 POST请求 - Content-Length: {request.content_length}")
        action = request.form.get("action")
        logger.info(f"📥 POST请求 - action: {action}")
        logger.info(f"📋 所有表单字段键: {list(request.form.keys())}")
        logger.info(f"📋 表单数据数量: {len(request.form)}")
        logger.info(f"📁 所有文件字段键: {list(request.files.keys())}")
        for key in request.files.keys():
            file = request.files[key]
            logger.info(
                f"📁 文件字段 '{key}': filename={file.filename if file else 'None'}, 类型={type(file)}"
            )

        if action == "add_product_with_sizes":
            # 一次性添加产品和多个尺寸
            code = request.form.get("code")
            name = request.form.get("name")
            description = request.form.get("description")

            # 处理多图上传
            image_urls = []
            uploaded_files = request.files.getlist("product_images[]")

            static_products_dir = os.path.join(app.root_path, "static", "images", "products")
            os.makedirs(static_products_dir, exist_ok=True)

            for i, file in enumerate(uploaded_files):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_urls.append(f"/static/images/products/{unique_filename}")

            # 保持向后兼容，如果没有多图上传，使用单图上传
            if not image_urls and "product_image" in request.files:
                file = request.files["product_image"]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_urls.append(f"/static/images/products/{unique_filename}")

            image_url = image_urls[0] if image_urls else ""

            # 获取尺寸数据
            size_names = request.form.getlist("size_name[]")
            size_printer_ids = request.form.getlist("size_printer_id[]")
            size_prices = request.form.getlist("size_price[]")
            sort_order = request.form.get("sort_order", 0)
            try:
                sort_order = int(sort_order)
            except (ValueError, TypeError):
                sort_order = 0

            if code and name and size_names:
                existing = Product.query.filter_by(code=code).first()
                if existing:
                    flash("产品代码已存在", "error")
                else:
                    # 获取选片赠送张数
                    try:
                        free_selection_count = int(request.form.get("free_selection_count", 1))
                        if free_selection_count < 0:
                            free_selection_count = 1
                    except (ValueError, TypeError):
                        free_selection_count = 1

                    # 获取每加一张照片的价格
                    try:
                        extra_photo_price = float(request.form.get("extra_photo_price", 10.0))
                        if extra_photo_price < 0:
                            extra_photo_price = 10.0
                    except (ValueError, TypeError):
                        extra_photo_price = 10.0

                    # 获取分类信息
                    category_id = request.form.get("category_id")
                    subcategory_id = request.form.get("subcategory_id")
                    try:
                        category_id = int(category_id) if category_id else None
                    except (ValueError, TypeError):
                        category_id = None
                    try:
                        subcategory_id = int(subcategory_id) if subcategory_id else None
                    except (ValueError, TypeError):
                        subcategory_id = None

                    # 创建产品
                    product = Product(
                        code=code,
                        name=name,
                        description=description,
                        image_url=image_url,
                        sort_order=sort_order,
                        free_selection_count=free_selection_count,
                        extra_photo_price=extra_photo_price,
                        category_id=category_id,
                        subcategory_id=subcategory_id,
                    )
                    db.session.add(product)
                    db.session.flush()

                    # 添加多图
                    for i, img_url in enumerate(image_urls):
                        product_image = ProductImage(
                            product_id=product.id, image_url=img_url, sort_order=i
                        )
                        db.session.add(product_image)

                    # 添加尺寸规格（宠物数量选项已注释 - 设备主要用于人像拍照，不需要宠物相关选项）
                    size_effect_images = request.files.getlist("size_effect_image[]")
                    for i, size_name in enumerate(size_names):
                        if size_name:
                            try:
                                printer_product_id = (
                                    size_printer_ids[i] if i < len(size_printer_ids) else None
                                )
                                # 获取价格，如果没有则默认为0
                                try:
                                    size_price = (
                                        float(size_prices[i])
                                        if i < len(size_prices) and size_prices[i]
                                        else 0.0
                                    )
                                except (ValueError, TypeError):
                                    size_price = 0.0

                                # 处理效果图上传
                                effect_image_url = ""
                                if i < len(size_effect_images):
                                    effect_file = size_effect_images[i]
                                    if effect_file and effect_file.filename:
                                        filename = secure_filename(effect_file.filename)
                                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                                        static_products_dir = os.path.join(
                                            current_app.root_path, "static", "images", "products"
                                        )
                                        os.makedirs(static_products_dir, exist_ok=True)
                                        file_path = os.path.join(
                                            static_products_dir, unique_filename
                                        )
                                        effect_file.save(file_path)
                                        effect_image_url = (
                                            f"/static/images/products/{unique_filename}"
                                        )

                                product_size = ProductSize(
                                    product_id=product.id,
                                    size_name=size_name,
                                    price=size_price,
                                    printer_product_id=printer_product_id,
                                    effect_image_url=effect_image_url,
                                    sort_order=i,
                                )
                                db.session.add(product_size)
                                db.session.flush()

                                # 宠物数量选项处理已注释 - 设备主要用于人像拍照，不需要宠物相关选项
                                # 获取该尺寸的宠物数量选项
                                # option_names = []
                                # option_prices = []
                                #
                                # for key in request.form:
                                #     if key.startswith('pet_option_name_') and key.endswith('[]'):
                                #         size_id_str = key.replace('pet_option_name_', '').replace('[]', '')
                                #         expected_size_id = f'size_{i}'
                                #         if size_id_str == expected_size_id:
                                #             option_names = request.form.getlist(key)
                                #             price_key = f'pet_option_price_{size_id_str}[]'
                                #             if price_key in request.form:
                                #                 option_prices = request.form.getlist(price_key)
                                #             break
                                #
                                # if not option_names:
                                #     all_option_names = request.form.getlist('pet_option_name[]')
                                #     all_option_prices = request.form.getlist('pet_option_price[]')
                                #     if len(all_option_names) > i:
                                #         option_names = [all_option_names[i]] if i < len(all_option_names) else []
                                #         option_prices = [all_option_prices[i]] if i < len(all_option_prices) else []
                                #
                                # # 添加该尺寸的宠物数量选项
                                # for j, option_name in enumerate(option_names):
                                #     if option_name and j < len(option_prices) and option_prices[j]:
                                #         try:
                                #             option_price = float(option_prices[j])
                                #             pet_option = ProductSizePetOption(
                                #                 size_id=product_size.id,
                                #                 pet_count_name=option_name,
                                #                 price=option_price,
                                #                 sort_order=j
                                #             )
                                #             db.session.add(pet_option)
                                #         except ValueError:
                                #             flash(f'尺寸 {size_name} 的选项价格格式错误', 'error')
                                #             db.session.rollback()
                                #             return redirect(url_for('admin_products.admin_products'))

                            except Exception as e:
                                flash(f"尺寸 {size_name} 添加失败: {str(e)}", "error")
                                db.session.rollback()
                                return redirect(url_for("admin_products.admin_products"))

                    # 处理风格分类绑定
                    bound_style_category_ids = request.form.getlist("style_category_ids[]")
                    bound_style_category_ids = [int(id) for id in bound_style_category_ids if id]

                    for category_id in bound_style_category_ids:
                        binding = ProductStyleCategory(
                            product_id=product.id, style_category_id=category_id
                        )
                        db.session.add(binding)

                    # 处理自定义字段
                    custom_field_names = request.form.getlist("custom_field_name[]")
                    custom_field_types = request.form.getlist("custom_field_type[]")
                    custom_field_options = request.form.getlist("custom_field_options[]")
                    custom_field_required = request.form.getlist("custom_field_required[]")

                    for i, field_name in enumerate(custom_field_names):
                        if field_name.strip():
                            field_type = (
                                custom_field_types[i] if i < len(custom_field_types) else "text"
                            )
                            field_options = (
                                custom_field_options[i] if i < len(custom_field_options) else None
                            )
                            is_required = (
                                custom_field_required[i] == "1"
                                if i < len(custom_field_required)
                                else False
                            )

                            custom_field = ProductCustomField(
                                product_id=product.id,
                                field_name=field_name.strip(),
                                field_type=field_type,
                                field_options=field_options.strip() if field_options else None,
                                is_required=is_required,
                                sort_order=i,
                            )
                            db.session.add(custom_field)

                    db.session.commit()

                    # 自动同步到冲印系统配置
                    try:
                        from product_config_sync import auto_sync_product_config

                        auto_sync_product_config()
                        flash("产品和尺寸添加成功，已自动同步到冲印系统", "success")
                    except Exception as sync_error:
                        logger.info(f"自动同步失败: {sync_error}")
                        flash("产品和尺寸添加成功，但同步到冲印系统失败", "warning")
            else:
                flash("请填写产品代码、名称和至少一个尺寸", "error")

        elif action == "delete_size":
            # 删除尺寸
            size_id = int(request.form.get("size_id"))
            try:
                product_size = ProductSize.query.get_or_404(size_id)

                orders_count = Order.query.filter_by(size=product_size.size_name).count()

                if orders_count > 0:
                    product_size.is_active = False
                    db.session.commit()
                    flash(f"该尺寸已有 {orders_count} 个订单，无法删除。已自动下架", "warning")
                else:
                    db.session.delete(product_size)
                    db.session.commit()
                    flash("尺寸删除成功", "success")

                try:
                    from product_config_sync import auto_sync_product_config

                    auto_sync_product_config()
                    if orders_count == 0:
                        flash("已自动同步到冲印系统", "success")
                except Exception as sync_error:
                    logger.info(f"自动同步失败: {sync_error}")
            except Exception as e:
                db.session.rollback()
                flash(f"操作失败: {str(e)}", "error")

        elif action == "edit_product":
            # 编辑产品
            product_id = int(request.form.get("product_id"))
            logger.info(f"📝 开始编辑产品 - 产品ID: {product_id}")
            try:
                product = Product.query.get_or_404(product_id)

                # 更新产品基本信息
                product.code = request.form.get("code")
                product.name = request.form.get("name")
                product.description = request.form.get("description", "")
                try:
                    product.sort_order = int(request.form.get("sort_order", 0))
                except (ValueError, TypeError):
                    product.sort_order = 0

                # 更新选片赠送张数
                try:
                    free_selection_count = int(request.form.get("free_selection_count", 1))
                    if free_selection_count < 0:
                        free_selection_count = 1
                    product.free_selection_count = free_selection_count
                except (ValueError, TypeError):
                    product.free_selection_count = 1

                # 更新每加一张照片的价格
                try:
                    extra_photo_price = float(request.form.get("extra_photo_price", 10.0))
                    if extra_photo_price < 0:
                        extra_photo_price = 10.0
                    product.extra_photo_price = extra_photo_price
                except (ValueError, TypeError):
                    product.extra_photo_price = 10.0

                # 处理上架/下架状态
                is_active = request.form.get("is_active")
                if is_active is not None:
                    product.is_active = is_active in ["1", "true", "True", "on"]

                # 处理产品分类
                category_id = request.form.get("category_id")
                if category_id:
                    try:
                        product.category_id = int(category_id) if category_id else None
                    except (ValueError, TypeError):
                        product.category_id = None
                else:
                    product.category_id = None

                subcategory_id = request.form.get("subcategory_id")
                if subcategory_id:
                    try:
                        product.subcategory_id = int(subcategory_id) if subcategory_id else None
                    except (ValueError, TypeError):
                        product.subcategory_id = None
                else:
                    product.subcategory_id = None

                # 处理封面图上传
                logger.info(f"🔍 检查封面图上传 - request.files keys: {list(request.files.keys())}")
                if "product_image" in request.files:
                    file = request.files["product_image"]
                    logger.info(
                        f"🔍 封面图文件对象: {file}, filename: {file.filename if file else 'None'}"
                    )
                    if file and file.filename and file.filename.strip():
                        logger.info(f"📷 处理封面图上传: {file.filename}")
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        static_products_dir = os.path.join(
                            app.root_path, "static", "images", "products"
                        )
                        os.makedirs(static_products_dir, exist_ok=True)
                        file_path = os.path.join(static_products_dir, unique_filename)
                        file.save(file_path)
                        product.image_url = f"/static/images/products/{unique_filename}"
                        logger.info(f"✅ 封面图已更新: {product.image_url}")
                    else:
                        logger.warning(
                            "封面图文件为空或文件名为空: file={file}, filename={file.filename if file else 'None'}"
                        )
                else:
                    logger.warning("request.files中没有product_image字段")

                # 处理多图上传
                uploaded_files = request.files.getlist("product_images[]")
                if uploaded_files and any(f.filename for f in uploaded_files):
                    static_products_dir = os.path.join(
                        app.root_path, "static", "images", "products"
                    )
                    os.makedirs(static_products_dir, exist_ok=True)

                    for file in uploaded_files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{uuid.uuid4().hex}_{filename}"
                            file_path = os.path.join(static_products_dir, unique_filename)
                            file.save(file_path)
                            image_url = f"/static/images/products/{unique_filename}"

                            # 获取当前最大排序
                            max_sort = (
                                db.session.query(db.func.max(ProductImage.sort_order))
                                .filter_by(product_id=product_id)
                                .scalar()
                                or 0
                            )

                            product_image = ProductImage(
                                product_id=product_id, image_url=image_url, sort_order=max_sort + 1
                            )
                            db.session.add(product_image)

                    # 如果没有主图，设置第一张为主图
                    if not product.image_url and uploaded_files[0].filename:
                        first_image = (
                            ProductImage.query.filter_by(product_id=product_id)
                            .order_by(ProductImage.sort_order.asc())
                            .first()
                        )
                        if first_image:
                            product.image_url = first_image.image_url

                # 处理风格分类绑定
                bound_style_category_ids = request.form.getlist("style_category_ids[]")
                logger.info(f"🎨 风格分类绑定数据 - 原始数据: {bound_style_category_ids}")
                bound_style_category_ids = [int(id) for id in bound_style_category_ids if id]
                logger.info(f"🎨 风格分类绑定数据 - 处理后的ID列表: {bound_style_category_ids}")

                # 先查询现有的绑定
                existing_bindings = ProductStyleCategory.query.filter_by(
                    product_id=product_id
                ).all()
                existing_category_ids = {binding.style_category_id for binding in existing_bindings}
                logger.info(f"🔍 现有绑定 - 风格分类ID列表: {list(existing_category_ids)}")

                # 计算需要删除和添加的绑定
                new_category_ids = set(bound_style_category_ids)
                to_delete = existing_category_ids - new_category_ids
                to_add = new_category_ids - existing_category_ids

                logger.info("📊 绑定变更分析:")
                logger.info(f"  - 需要删除的绑定: {list(to_delete)}")
                logger.info(f"  - 需要添加的绑定: {list(to_add)}")

                # 删除不需要的绑定
                if to_delete:
                    deleted_count = ProductStyleCategory.query.filter(
                        ProductStyleCategory.product_id == product_id,
                        ProductStyleCategory.style_category_id.in_(to_delete),
                    ).delete(synchronize_session=False)
                    logger.info(f"🗑️ 删除了 {deleted_count} 个不需要的绑定")
                else:
                    logger.info("ℹ️ 没有需要删除的绑定")

                # 添加新的绑定
                new_bindings_count = 0
                for category_id in to_add:
                    # 检查是否已存在（避免重复）
                    existing = ProductStyleCategory.query.filter_by(
                        product_id=product_id, style_category_id=category_id
                    ).first()
                    if not existing:
                        binding = ProductStyleCategory(
                            product_id=product_id, style_category_id=category_id
                        )
                        db.session.add(binding)
                        new_bindings_count += 1
                        logger.info(
                            f"✅ 添加风格分类绑定 - 产品ID: {product_id}, 风格分类ID: {category_id}"
                        )
                    else:
                        logger.warning(
                            "绑定已存在，跳过 - 产品ID: {product_id}, 风格分类ID: {category_id}"
                        )

                logger.info(f"📊 风格分类绑定处理完成 - 新增绑定数量: {new_bindings_count}")
                logger.info(f"📊 添加绑定后session状态 - 新对象数量: {len(db.session.new)}")

                # 处理自定义字段
                existing_field_ids = request.form.getlist("existing_custom_field_id[]")
                custom_field_names = request.form.getlist("custom_field_name[]")
                custom_field_types = request.form.getlist("custom_field_type[]")
                custom_field_options = request.form.getlist("custom_field_options[]")
                custom_field_required = request.form.getlist("custom_field_required[]")

                logger.info(f"📋 处理自定义字段 - 字段数量: {len(custom_field_names)}")
                logger.info(f"  - custom_field_names: {custom_field_names}")
                logger.info(f"  - custom_field_types: {custom_field_types}")
                logger.info(f"  - custom_field_options: {custom_field_options}")

                # 删除所有旧的自定义字段（使用 synchronize_session=False 避免影响新对象）
                deleted_count = ProductCustomField.query.filter_by(product_id=product_id).delete(
                    synchronize_session=False
                )
                logger.info(f"🗑️ 删除了 {deleted_count} 个旧的自定义字段")

                # 添加新的自定义字段
                import json

                added_count = 0
                for i, field_name in enumerate(custom_field_names):
                    if field_name.strip():
                        field_type = (
                            custom_field_types[i] if i < len(custom_field_types) else "text"
                        )
                        field_options_raw = (
                            custom_field_options[i] if i < len(custom_field_options) else None
                        )
                        is_required = (
                            custom_field_required[i] == "1"
                            if i < len(custom_field_required)
                            else False
                        )

                        logger.info(
                            f"📝 处理字段 {i}: 名称={field_name}, 类型={field_type}, 选项原始值={field_options_raw}"
                        )

                        # 处理选项（如果是下拉选择类型，可能是JSON格式）
                        field_options = None
                        if field_type == "select" and field_options_raw:
                            try:
                                # 尝试解析为JSON
                                logger.info(
                                    f"  🔍 尝试解析JSON: {field_options_raw[:100]}..."
                                )  # 只显示前100个字符
                                options_data = json.loads(field_options_raw)
                                logger.info(
                                    f"  ✅ JSON解析成功，类型: {type(options_data)}, 长度: {len(options_data) if isinstance(options_data, list) else 'N/A'}"
                                )

                                if isinstance(options_data, list):
                                    logger.info(f"  📋 处理 {len(options_data)} 个选项")
                                    # 处理每个选项的图片上传
                                    for option_index, option in enumerate(options_data):
                                        logger.info(f"    - 选项 {option_index}: {option}")
                                        if option.get("_hasNewImage"):
                                            # 查找对应的图片文件
                                            image_key = f"option_image_{i}_{option_index}"
                                            logger.info(f"    🔍 查找图片文件: {image_key}")
                                            logger.info(
                                                f"    📁 request.files keys: {list(request.files.keys())}"
                                            )

                                            if image_key in request.files:
                                                image_file = request.files[image_key]
                                                logger.info(
                                                    f"    ✅ 找到图片文件: {image_file.filename if image_file else 'None'}"
                                                )
                                                if image_file and image_file.filename:
                                                    # 保存图片
                                                    filename = secure_filename(image_file.filename)
                                                    unique_filename = (
                                                        f"{uuid.uuid4().hex}_{filename}"
                                                    )
                                                    static_products_dir = os.path.join(
                                                        app.root_path,
                                                        "static",
                                                        "images",
                                                        "products",
                                                    )
                                                    os.makedirs(static_products_dir, exist_ok=True)
                                                    file_path = os.path.join(
                                                        static_products_dir, unique_filename
                                                    )
                                                    image_file.save(file_path)
                                                    option["image_url"] = (
                                                        f"/static/images/products/{unique_filename}"
                                                    )
                                                    logger.info(
                                                        f"    📷 选项图片已上传: {option.get('name', '未知')} -> {option['image_url']}"
                                                    )
                                            else:
                                                logger.info(f"    ⚠️ 图片文件不存在: {image_key}")

                                        # 清理临时字段
                                        option.pop("_hasNewImage", None)
                                        option.pop("_imageFile", None)

                                    # 保存为JSON格式
                                    field_options = json.dumps(options_data, ensure_ascii=False)
                                    logger.info(
                                        f"  ✅ 最终选项JSON: {field_options[:200]}..."
                                    )  # 只显示前200个字符
                                else:
                                    # 如果不是列表，保持原样（向后兼容）
                                    logger.info("  ⚠️ JSON不是列表格式，保持原样")
                                    field_options = field_options_raw.strip()
                            except (json.JSONDecodeError, ValueError) as e:
                                # 如果不是JSON，按逗号分隔处理（向后兼容）
                                logger.info(f"  ⚠️ JSON解析失败: {str(e)}，按逗号分隔处理")
                                field_options = field_options_raw.strip()
                        else:
                            # 非下拉选择类型，直接使用原始值
                            field_options = field_options_raw.strip() if field_options_raw else None
                            logger.info("  ℹ️ 非下拉选择类型，直接使用原始值")

                        custom_field = ProductCustomField(
                            product_id=product_id,
                            field_name=field_name.strip(),
                            field_type=field_type,
                            field_options=field_options,
                            is_required=is_required,
                            sort_order=i,
                        )
                        db.session.add(custom_field)
                        added_count += 1
                        logger.info(
                            f"  ✅ 自定义字段已添加到session: {field_name} (类型: {field_type}, 选项: {field_options[:50] if field_options else 'None'}...)"
                        )

                logger.info(f"📊 自定义字段处理完成: 共添加 {added_count} 个字段")
                logger.info(
                    f"📊 当前session状态: 新对象={len(db.session.new)}, 修改对象={len(db.session.dirty)}, 删除对象={len(db.session.deleted)}"
                )

                # 处理赠送工作流配置（只支持风格图片类型）
                try:
                    import sys

                    if "test_server" in sys.modules:
                        test_server_module = sys.modules["test_server"]
                        ProductBonusWorkflow = (
                            test_server_module.ProductBonusWorkflow
                            if hasattr(test_server_module, "ProductBonusWorkflow")
                            else None
                        )

                        if ProductBonusWorkflow:
                            # 调试：输出所有表单字段
                            logger.info(f"📋 所有表单字段键: {list(request.form.keys())}")

                            existing_bonus_workflow_ids = request.form.getlist(
                                "existing_bonus_workflow_id[]"
                            )
                            bonus_workflow_types = request.form.getlist("bonus_workflow_type[]")
                            bonus_workflow_style_image_ids = request.form.getlist(
                                "bonus_workflow_style_image_id[]"
                            )
                            bonus_workflow_names = request.form.getlist("bonus_workflow_name[]")
                            bonus_workflow_sort_orders = request.form.getlist(
                                "bonus_workflow_sort_order[]"
                            )

                            logger.info(f"📝 处理赠送工作流配置 - 产品ID: {product_id}")
                            logger.info(
                                f"  - existing_bonus_workflow_ids: {existing_bonus_workflow_ids}"
                            )
                            logger.info(f"  - bonus_workflow_types: {bonus_workflow_types}")
                            logger.info(
                                f"  - bonus_workflow_style_image_ids: {bonus_workflow_style_image_ids}"
                            )
                            logger.info(f"  - bonus_workflow_names: {bonus_workflow_names}")
                            logger.info(
                                f"  - bonus_workflow_sort_orders: {bonus_workflow_sort_orders}"
                            )
                            logger.info(f"  - 工作流类型数量: {len(bonus_workflow_types)}")
                            logger.info(
                                f"  - 风格图片ID数量: {len(bonus_workflow_style_image_ids)}"
                            )
                            logger.info(f"  - 工作流名称数量: {len(bonus_workflow_names)}")

                            # 删除所有旧的赠送工作流配置
                            deleted_count = ProductBonusWorkflow.query.filter_by(
                                product_id=product_id
                            ).delete()
                            logger.info(f"  - 删除了 {deleted_count} 个旧的赠送工作流配置")

                            # 添加新的赠送工作流配置（只处理风格图片类型）
                            added_count = 0
                            for i, workflow_type in enumerate(bonus_workflow_types):
                                logger.info(f"  - 处理工作流 {i + 1}: 类型={workflow_type}")
                                if workflow_type == "style_image" and i < len(
                                    bonus_workflow_style_image_ids
                                ):
                                    try:
                                        style_image_id = (
                                            int(bonus_workflow_style_image_ids[i])
                                            if bonus_workflow_style_image_ids[i]
                                            else None
                                        )
                                    except (ValueError, TypeError):
                                        style_image_id = None

                                    if style_image_id:
                                        workflow_name = (
                                            bonus_workflow_names[i]
                                            if i < len(bonus_workflow_names)
                                            else None
                                        )
                                        try:
                                            sort_order = (
                                                int(bonus_workflow_sort_orders[i])
                                                if i < len(bonus_workflow_sort_orders)
                                                and bonus_workflow_sort_orders[i]
                                                else i
                                            )
                                        except (ValueError, TypeError):
                                            sort_order = i

                                        bonus_workflow = ProductBonusWorkflow(
                                            product_id=product_id,
                                            workflow_type="style_image",
                                            style_image_id=style_image_id,
                                            workflow_name=workflow_name,
                                            is_active=True,
                                            sort_order=sort_order,
                                        )
                                        db.session.add(bonus_workflow)
                                        added_count += 1
                                        logger.info(
                                            f"  - ✅ 添加赠送工作流: 风格图片ID={style_image_id}, 名称={workflow_name}, 排序={sort_order}"
                                        )
                                    else:
                                        logger.info(f"  - ⚠️ 跳过工作流 {i + 1}: style_image_id无效")
                                else:
                                    logger.info(
                                        f"  - ⚠️ 跳过工作流 {i + 1}: 类型不是style_image或索引超出范围"
                                    )

                            logger.info(f"✅ 共添加了 {added_count} 个赠送工作流配置")

                            # 在提交前验证
                            logger.info(
                                f"🔍 提交前验证: session中有 {len(db.session.new)} 个新对象待提交"
                            )

                            # 验证保存结果（提交前）
                            saved_count_before = ProductBonusWorkflow.query.filter_by(
                                product_id=product_id, is_active=True
                            ).count()
                            logger.info(
                                f"🔍 提交前: 数据库中该产品现在有 {saved_count_before} 个赠送工作流配置"
                            )

                            # 注意：这里不立即commit，等所有数据都准备好后一起commit
                        else:
                            logger.warning("ProductBonusWorkflow模型未找到，跳过赠送工作流处理")
                except Exception as e:
                    logger.error("处理赠送工作流配置失败: {str(e)}")
                    import traceback

                    traceback.print_exc()
                    # 不影响主流程，继续执行

                # 处理尺寸更新
                existing_size_ids = request.form.getlist("existing_size_id[]")
                size_names = request.form.getlist("size_name[]")
                size_printer_ids = request.form.getlist("size_printer_id[]")
                size_prices = request.form.getlist("size_price[]")
                size_effect_image_urls = request.form.getlist(
                    "size_effect_image_url[]"
                )  # 现有的效果图URL
                size_effect_images = request.files.getlist("size_effect_image[]")  # 新上传的效果图

                # 确保所有数组长度一致（以size_names为准）
                max_len = len(size_names)
                logger.info(f"📝 处理尺寸数据: 共 {max_len} 个尺寸")
                logger.info(f"   - existing_size_ids (原始): {existing_size_ids}")
                logger.info(f"   - size_names: {size_names}")
                logger.info(f"   - size_prices: {size_prices}")
                logger.info(f"   - size_effect_image_urls: {size_effect_image_urls}")
                logger.info(f"   - size_effect_images 数量: {len(size_effect_images)}")

                # 处理重复的existing_size_id：只取前max_len个，并去重
                # 如果existing_size_ids长度大于max_len，说明有重复，只取前max_len个
                if len(existing_size_ids) > max_len:
                    logger.warning(
                        "existing_size_ids长度({len(existing_size_ids)})大于size_names长度({max_len})，可能存在重复字段"
                    )
                    # 只取前max_len个，并去重（保留第一个出现的）
                    seen_ids = set()
                    deduplicated_ids = []
                    for sid in existing_size_ids[:max_len]:
                        if sid and sid.isdigit() and int(sid) not in seen_ids:
                            deduplicated_ids.append(sid)
                            seen_ids.add(int(sid))
                        elif not sid or not sid.isdigit():
                            deduplicated_ids.append("")
                    existing_size_ids = deduplicated_ids
                    logger.info(f"   - existing_size_ids (去重后): {existing_size_ids}")

                # 获取所有有效的existing_size_id（用于删除不存在的尺寸）
                valid_size_ids = []
                for size_id_str in existing_size_ids:
                    if size_id_str and size_id_str.isdigit():
                        size_id = int(size_id_str)
                        if size_id not in valid_size_ids:
                            valid_size_ids.append(size_id)

                # 删除不在列表中的尺寸
                if valid_size_ids:
                    ProductSize.query.filter(
                        ProductSize.product_id == product_id, ~ProductSize.id.in_(valid_size_ids)
                    ).delete(synchronize_session=False)
                    logger.info(f"🗑️ 删除不在列表中的尺寸，保留的ID: {valid_size_ids}")

                # 按索引遍历所有尺寸，确保每个尺寸都正确处理
                for i in range(max_len):
                    try:
                        size_id_str = existing_size_ids[i] if i < len(existing_size_ids) else ""
                        size_name = size_names[i] if i < len(size_names) else ""
                        size_printer_id = size_printer_ids[i] if i < len(size_printer_ids) else ""
                        size_price = size_prices[i] if i < len(size_prices) else "0"

                        if not size_name:
                            logger.warning("跳过第 {i+1} 个尺寸: 名称为空")
                            continue

                        try:
                            price = float(size_price) if size_price else 0.0
                        except (ValueError, TypeError):
                            price = 0.0

                        # 处理效果图：优先使用新上传的，否则使用现有的URL
                        effect_image_url = ""

                        # 先获取现有的URL（如果有）
                        existing_url = ""
                        if i < len(size_effect_image_urls):
                            existing_url = size_effect_image_urls[i] or ""

                        # 检查是否有新上传的效果图
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
                                    current_app.root_path, "static", "images", "products"
                                )
                                os.makedirs(static_products_dir, exist_ok=True)
                                file_path = os.path.join(static_products_dir, unique_filename)
                                effect_file.save(file_path)
                                effect_image_url = f"/static/images/products/{unique_filename}"
                                has_new_image = True
                                logger.info(f"✅ 第 {i + 1} 个尺寸上传新效果图: {effect_image_url}")

                        # 如果没有新上传的，使用现有的URL
                        if not has_new_image and existing_url:
                            effect_image_url = existing_url
                            logger.info(f"📷 第 {i + 1} 个尺寸使用现有效果图: {effect_image_url}")
                        elif not has_new_image and not existing_url:
                            logger.warning("第 {i+1} 个尺寸没有效果图")

                        # 判断是更新还是创建
                        if size_id_str and size_id_str.isdigit():
                            # 更新现有尺寸
                            size_id = int(size_id_str)
                            size = ProductSize.query.get(size_id)
                            if size:
                                size.size_name = size_name
                                size.printer_product_id = (
                                    size_printer_id if size_printer_id else None
                                )
                                size.price = price
                                size.effect_image_url = effect_image_url
                                size.sort_order = i
                                logger.info(
                                    f"✅ 更新尺寸 ID={size_id}: {size_name}, 价格={price}, 效果图={effect_image_url}"
                                )
                            else:
                                logger.warning("尺寸 ID={size_id} 不存在，将创建新尺寸")
                                # 如果ID不存在，创建新尺寸
                                new_size = ProductSize(
                                    product_id=product_id,
                                    size_name=size_name,
                                    price=price,
                                    printer_product_id=size_printer_id if size_printer_id else None,
                                    effect_image_url=effect_image_url,
                                    sort_order=i,
                                )
                                db.session.add(new_size)
                                logger.info(
                                    f"✅ 添加新尺寸: {size_name}, 价格={price}, 效果图={effect_image_url}"
                                )
                        else:
                            # 添加新尺寸
                            new_size = ProductSize(
                                product_id=product_id,
                                size_name=size_name,
                                price=price,
                                printer_product_id=size_printer_id if size_printer_id else None,
                                effect_image_url=effect_image_url,
                                sort_order=i,
                            )
                            db.session.add(new_size)
                            logger.info(
                                f"✅ 添加新尺寸: {size_name}, 价格={price}, 效果图={effect_image_url}"
                            )
                    except (ValueError, TypeError) as e:
                        logger.error("处理第 {i+1} 个尺寸时出错: {e}")
                        import traceback

                        traceback.print_exc()
                        pass

                # 提交所有更改（包括赠送工作流）
                logger.info("💾 准备提交数据库更改...")
                logger.info(f"  - 新对象数量: {len(db.session.new)}")
                logger.info(f"  - 修改对象数量: {len(db.session.dirty)}")
                logger.info(f"  - 删除对象数量: {len(db.session.deleted)}")

                db.session.commit()
                logger.info("✅ 数据库提交成功")

                # 使产品列表缓存失效
                try:
                    from app.services.cache_service import (
                        CACHE_PREFIXES,
                        cache_key,
                        delete_cache,
                        invalidate_cache_pattern,
                    )

                    invalidate_cache_pattern(f"cache:{CACHE_PREFIXES['PRODUCTS']}:*")
                    logger.info("产品列表缓存已失效")

                    # 使该产品的风格缓存失效（小程序 /styles?productId=xxx 会缓存）
                    for pid in (str(product_id), product.code or ""):
                        if pid:
                            key = cache_key(
                                CACHE_PREFIXES["STYLE_CATEGORIES"], product_id=pid
                            )
                            delete_cache(key)
                    logger.info("该产品风格缓存已失效")
                except Exception as e:
                    logger.warning(f"失效产品列表缓存失败: {e}")

                # 验证风格分类绑定保存结果（提交后）
                saved_bindings = ProductStyleCategory.query.filter_by(product_id=product_id).all()
                saved_category_ids = [binding.style_category_id for binding in saved_bindings]
                logger.info(f"🔍 提交后验证 - 数据库中该产品的风格分类绑定: {saved_category_ids}")
                logger.info(f"🔍 提交后验证 - 期望的绑定: {bound_style_category_ids}")
                if set(saved_category_ids) == set(bound_style_category_ids):
                    logger.info("✅ 风格分类绑定保存成功！")
                else:
                    logger.error(
                        "风格分类绑定保存失败！期望: {bound_style_category_ids}, 实际: {saved_category_ids}"
                    )

                # 验证保存结果（提交后）
                try:
                    import sys

                    if "test_server" in sys.modules:
                        test_server_module = sys.modules["test_server"]
                        ProductBonusWorkflow = (
                            test_server_module.ProductBonusWorkflow
                            if hasattr(test_server_module, "ProductBonusWorkflow")
                            else None
                        )
                        if ProductBonusWorkflow:
                            saved_count_after = ProductBonusWorkflow.query.filter_by(
                                product_id=product_id, is_active=True
                            ).count()
                            logger.info(
                                f"🔍 提交后验证: 数据库中该产品现在有 {saved_count_after} 个赠送工作流配置"
                            )
                except Exception as e:
                    logger.warning("验证保存结果失败: {str(e)}")

                # 自动同步到冲印系统配置
                try:
                    from product_config_sync import auto_sync_product_config

                    auto_sync_product_config()
                    flash("产品更新成功，已自动同步到冲印系统", "success")
                except Exception as sync_error:
                    logger.info(f"自动同步失败: {sync_error}")
                    flash("产品更新成功，但同步到冲印系统失败", "warning")

            except Exception as e:
                db.session.rollback()
                flash(f"更新失败: {str(e)}", "error")
                import traceback

                traceback.print_exc()

        elif action == "delete_product_image":
            # 删除产品图片
            image_id = int(request.form.get("image_id"))
            try:
                product_image = ProductImage.query.get_or_404(image_id)
                product_id = product_image.product_id
                deleted_image_url = product_image.image_url

                if product_image.image_url:
                    image_path = product_image.image_url.lstrip("/")
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            logger.info(f"删除图片文件失败: {str(e)}")

                db.session.delete(product_image)

                product = Product.query.get(product_id)
                if product and product.image_url == deleted_image_url:
                    other_image = ProductImage.query.filter_by(product_id=product_id).first()
                    if other_image:
                        product.image_url = other_image.image_url
                    else:
                        product.image_url = None

                db.session.commit()
                flash("图片删除成功", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"删除失败: {str(e)}", "error")

        elif action == "toggle_product_status":
            # 切换产品上架/下架状态
            product_id = int(request.form.get("product_id"))
            try:
                product = Product.query.get_or_404(product_id)
                product.is_active = not product.is_active
                db.session.commit()
                status_text = "上架" if product.is_active else "下架"
                flash(f"产品已{status_text}", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"操作失败: {str(e)}", "error")

        elif action == "delete_product":
            # 删除产品
            product_id = int(request.form.get("product_id"))
            try:
                product = Product.query.get_or_404(product_id)

                ProductSize.query.filter_by(product_id=product_id).delete()
                ProductImage.query.filter_by(product_id=product_id).delete()

                db.session.delete(product)
                db.session.commit()

                try:
                    from product_config_sync import auto_sync_product_config

                    auto_sync_product_config()
                    flash("产品删除成功，已自动同步到冲印系统", "success")
                except Exception as sync_error:
                    logger.info(f"自动同步失败: {sync_error}")
                    flash("产品删除成功，但同步到冲印系统失败", "warning")
            except Exception as e:
                db.session.rollback()
                flash("删除失败", "error")

        return redirect(url_for("admin_products.admin_products"))

    # GET请求：获取所有产品和尺寸
    try:
        products = Product.query.order_by(Product.sort_order.asc(), Product.id.asc()).all()

        # 为每个产品加载赠送工作流数据（确保backref能正常工作）
        try:
            import sys

            if "test_server" in sys.modules:
                test_server_module = sys.modules["test_server"]
                ProductBonusWorkflow = (
                    test_server_module.ProductBonusWorkflow
                    if hasattr(test_server_module, "ProductBonusWorkflow")
                    else None
                )

                if ProductBonusWorkflow:
                    # 批量加载所有产品的赠送工作流（避免N+1查询问题）
                    all_bonus_workflows = (
                        ProductBonusWorkflow.query.filter_by(is_active=True)
                        .order_by(
                            ProductBonusWorkflow.product_id.asc(),
                            ProductBonusWorkflow.sort_order.asc(),
                        )
                        .all()
                    )

                    # 按产品ID分组
                    bonus_workflows_by_product = {}
                    for bw in all_bonus_workflows:
                        if bw.product_id not in bonus_workflows_by_product:
                            bonus_workflows_by_product[bw.product_id] = []
                        bonus_workflows_by_product[bw.product_id].append(bw)

                    # 为每个产品设置bonus_workflows属性
                    for product in products:
                        product.bonus_workflows = bonus_workflows_by_product.get(product.id, [])
                        logger.info(
                            f"产品 {product.name} (ID: {product.id}) 的赠送工作流数量: {len(product.bonus_workflows)}"
                        )
                        if len(product.bonus_workflows) > 0:
                            for bw in product.bonus_workflows:
                                logger.info(
                                    f"  - 工作流: {bw.workflow_name or '未命名'} (风格图片ID: {bw.style_image_id})"
                                )
        except Exception as e:
            logger.info(f"加载赠送工作流数据失败: {str(e)}")
            import traceback

            traceback.print_exc()
    except Exception as e:
        # 如果字段不存在，使用原始SQL查询
        logger.info(f"ORM查询失败（可能缺少free_selection_count字段），使用原始SQL: {e}")
        from sqlalchemy import text

        try:
            result = db.session.execute(
                text(
                    "SELECT id, code, name, description, image_url, is_active, sort_order, created_at FROM products ORDER BY sort_order ASC, id ASC"
                )
            )
            products_data = result.fetchall()

            # 转换为Product对象（简化版）
            class ProductObj:
                def __init__(
                    self, id, code, name, description, image_url, is_active, sort_order, created_at
                ):
                    self.id = id
                    self.code = code
                    self.name = name
                    self.description = description
                    self.image_url = image_url
                    self.is_active = bool(is_active)
                    self.sort_order = sort_order
                    self.created_at = created_at
                    self.free_selection_count = 1  # 默认值

            products = [ProductObj(*row) for row in products_data]
        except Exception as e2:
            logger.info(f"原始SQL查询也失败: {e2}")
            products = []
    product_sizes = (
        ProductSize.query.join(Product)
        .order_by(ProductSize.product_id.asc(), ProductSize.sort_order.asc())
        .all()
    )
    product_images = (
        ProductImage.query.join(Product)
        .order_by(ProductImage.product_id.asc(), ProductImage.sort_order.asc())
        .all()
    )

    # 宠物数量选项加载已注释 - 设备主要用于人像拍照，不需要宠物相关选项
    # 为每个尺寸加载宠物数量选项
    # for size in product_sizes:
    #     pet_options = ProductSizePetOption.query.filter_by(size_id=size.id).order_by(ProductSizePetOption.sort_order.asc()).all()
    #     size.pet_options = pet_options
    # 为每个尺寸设置空的宠物选项列表（避免模板报错）
    for size in product_sizes:
        size.pet_options = []

    # 获取所有风格分类
    style_categories = (
        StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order.asc()).all()
    )

    # 优化N+1查询：批量查询所有产品的风格分类绑定
    product_style_bindings = {}
    product_ids = [product.id for product in products]
    if product_ids:
        all_bindings = ProductStyleCategory.query.filter(
            ProductStyleCategory.product_id.in_(product_ids)
        ).all()
        for binding in all_bindings:
            if binding.product_id not in product_style_bindings:
                product_style_bindings[binding.product_id] = []
            product_style_bindings[binding.product_id].append(int(binding.style_category_id))

    # 确保所有产品都有绑定列表（即使为空）
    for product in products:
        if product.id not in product_style_bindings:
            product_style_bindings[product.id] = []
        logger.info(
            f"📋 产品 {product.name} (ID: {product.id}) 绑定的风格分类: {product_style_bindings[product.id]} (总数: {len(product_style_bindings[product.id])})"
        )

    # 获取产品分类数据
    product_categories = []
    product_subcategories = []
    ProductCategory = models.get("ProductCategory")
    ProductSubcategory = models.get("ProductSubcategory")
    if ProductCategory:
        product_categories = (
            ProductCategory.query.filter_by(is_active=True)
            .order_by(ProductCategory.sort_order.asc())
            .all()
        )
    if ProductSubcategory:
        product_subcategories = (
            ProductSubcategory.query.filter_by(is_active=True)
            .order_by(ProductSubcategory.sort_order.asc())
            .all()
        )

    # 按一级分类组织二级分类（转换为字典格式以便JSON序列化）
    subcategories_by_category = {}
    for subcat in product_subcategories:
        if subcat.category_id not in subcategories_by_category:
            subcategories_by_category[subcat.category_id] = []
        # 将对象转换为字典
        subcategories_by_category[subcat.category_id].append(
            {
                "id": subcat.id,
                "category_id": subcat.category_id,
                "name": subcat.name,
                "code": subcat.code,
                "icon": subcat.icon or "",
                "image_url": subcat.image_url or "",
                "sort_order": subcat.sort_order or 0,
                "is_active": subcat.is_active,
            }
        )

    # 获取API模板列表和风格图片列表（用于赠送工作流配置）
    api_templates = []
    style_images = []
    try:
        import sys

        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            if hasattr(test_server_module, "APITemplate"):
                APITemplate = test_server_module.APITemplate
                api_templates = APITemplate.query.filter_by(is_active=True).all()

            # 直接从models获取StyleImage
            StyleImage = models.get("StyleImage")
            if StyleImage:
                style_images = (
                    StyleImage.query.filter_by(is_active=True)
                    .order_by(StyleImage.sort_order.asc())
                    .all()
                )
                logger.info(f"✅ 获取到 {len(style_images)} 个风格图片")
                # 调试：输出前几个风格图片的信息
                if len(style_images) > 0:
                    for img in style_images[:3]:
                        logger.info(
                            f"  - 风格图片: {img.name} (ID: {img.id}, 分类ID: {img.category_id})"
                        )
            else:
                logger.warning("StyleImage模型未找到，尝试从test_server直接获取")
                # 如果models中没有，尝试从test_server直接获取
                if hasattr(test_server_module, "StyleImage"):
                    StyleImage = test_server_module.StyleImage
                    style_images = (
                        StyleImage.query.filter_by(is_active=True)
                        .order_by(StyleImage.sort_order.asc())
                        .all()
                    )
                    logger.info(f"✅ 从test_server获取到 {len(style_images)} 个风格图片")
                else:
                    logger.error("无法获取StyleImage模型")
    except Exception as e:
        logger.info(f"获取API模板或风格图片列表失败: {str(e)}")
        import traceback

        traceback.print_exc()

    # 检查是否请求新的产品管理页面
    if request.args.get("view") == "products":
        return render_template(
            "admin/products.html",
            products=products,
            product_categories=product_categories,
            subcategories_by_category=subcategories_by_category,
            style_categories=style_categories,
        )

    return render_template(
        "admin/sizes.html",
        products=products,
        product_sizes=product_sizes,
        product_images=product_images,
        style_categories=style_categories,
        product_style_bindings=product_style_bindings,
        product_categories=product_categories,
        product_subcategories=product_subcategories,
        subcategories_by_category=subcategories_by_category,
        api_templates=api_templates,
        style_images=style_images,
    )
