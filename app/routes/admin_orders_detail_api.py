# -*- coding: utf-8 -*-
"""
管理后台订单详情API路由模块
提供订单详情查看和状态更新功能
"""

import logging

logger = logging.getLogger(__name__)
import os
import sys
from datetime import datetime
from urllib.parse import quote

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
from sqlalchemy import func, text
from werkzeug.utils import secure_filename

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
admin_orders_detail_bp = Blueprint("admin_orders_detail", __name__)


@admin_orders_detail_bp.route("/admin/order/<int:order_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_order_detail(order_id):
    """订单详情页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))

    # 处理测试订单（order_id=0）
    if order_id == 0:
        flash("这是测试任务，没有对应的订单记录", "info")
        from app.routes.ai import ai_bp

        return redirect(url_for("ai.ai_tasks"))

    models = get_models(
        ["Order", "OrderImage", "Product", "ProductSize", "ShopOrder", "AITask", "db"]
    )
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin.admin_routes.admin_dashboard"))

    db = models["db"]
    Order = models["Order"]
    OrderImage = models["OrderImage"]
    Product = models["Product"]
    ProductSize = models["ProductSize"]

    # 获取app实例（用于文件路径）
    if "test_server" in sys.modules:
        test_server_module = sys.modules["test_server"]
        app_instance = test_server_module.app if hasattr(test_server_module, "app") else current_app
    else:
        app_instance = current_app

    order = Order.query.get_or_404(order_id)

    # 获取所有使用相同订单号的订单记录（支持追加产品）
    order_number = order.order_number
    all_orders = (
        Order.query.filter_by(order_number=order_number).order_by(Order.created_at.asc()).all()
    )

    # 优化N+1查询：批量查询所有订单的图片
    order_ids = [o.id for o in all_orders]
    images_map = {}
    try:
        # 使用原始SQL批量查询，避免SQLAlchemy模型字段问题
        if order_ids:
            placeholders = ",".join([f":order_id_{i}" for i in range(len(order_ids))])
            params = {f"order_id_{i}": oid for i, oid in enumerate(order_ids)}
            result = db.session.execute(
                text(
                    f"SELECT id, order_id, path, is_main FROM order_image WHERE order_id IN ({placeholders})"
                ),
                params,
            )
            images_data = result.fetchall()
            logger.info(f"订单详情 - 批量查询到图片数量: {len(images_data)}")

            # 转换为OrderImage对象并按order_id分组
            for row in images_data:
                img_id, order_id_val, path, is_main = row
                if order_id_val not in images_map:
                    images_map[order_id_val] = []

                class ImageObj:
                    def __init__(self, id, path, is_main):
                        self.id = id
                        self.path = path
                        self.is_main = bool(is_main) if is_main is not None else False

                images_map[order_id_val].append(ImageObj(img_id, path, is_main))
    except Exception as e:
        # 如果查询失败，尝试使用SQLAlchemy批量查询（可能字段不存在）
        logger.info(f"原始SQL批量查询失败，尝试SQLAlchemy批量查询: {e}")
        try:
            if order_ids:
                all_images = OrderImage.query.filter(OrderImage.order_id.in_(order_ids)).all()
                for img in all_images:
                    if img.order_id not in images_map:
                        images_map[img.order_id] = []
                    images_map[img.order_id].append(img)
            logger.info(f"SQLAlchemy查询成功 - 订单ID: {order_id}, 查询到图片数量: {len(all_images)}")
            for img in all_images:
                logger.info(
                    f"  - 图片ID: {img.id}, 路径: {img.path}, 是否主图: {getattr(img, 'is_main', False)}"
                )
        except Exception as e2:
            # 如果查询失败（可能是数据库表结构问题），返回空列表并记录错误
            logger.info(f"查询订单图片失败: {e2}")
            import traceback

            traceback.print_exc()

    # 获取当前订单的图片（从批量查询的映射中获取）
    images = images_map.get(order.id, [])
    logger.info(f"订单详情 - 订单ID: {order_id}, 查询到图片数量: {len(images)}")

    # 查询产品（如果free_selection_count字段不存在，会使用默认值1）
    try:
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    except Exception as e:
        # 如果字段不存在，使用原始SQL查询
        logger.info(f"ORM查询失败（可能缺少free_selection_count字段），使用原始SQL: {e}")
        try:
            result = db.session.execute(
                text(
                    "SELECT id, code, name, description, image_url, is_active, sort_order, created_at FROM products WHERE is_active = 1 ORDER BY sort_order"
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
    # 优化：产品尺寸通常数量不多，但为了保持一致性，仍然使用批量查询
    sizes = ProductSize.query.filter_by(is_active=True).order_by(ProductSize.sort_order).all()

    # 将ProductSize对象转换为模板期望的格式
    size_options = []
    for size in sizes:
        size_options.append(
            {
                "code": f"size_{size.id}",  # 使用ID作为code
                "name": size.size_name,
                "price": size.price,
            }
        )

    # 获取所有效果图（从AITask中获取，如果不存在则从文件系统读取）
    effect_images = []
    # 优化N+1查询：批量查询所有订单的AI任务
    AITask = models.get("AITask")
    ai_tasks_map = {}
    if AITask and order_ids:
        try:
            all_ai_tasks = (
                AITask.query.filter(AITask.order_id.in_(order_ids), AITask.status == "completed")
                .filter(AITask.output_image_path.isnot(None))
                .order_by(AITask.completed_at.desc())
                .all()
            )
            for task in all_ai_tasks:
                if task.order_id not in ai_tasks_map:
                    ai_tasks_map[task.order_id] = []
                ai_tasks_map[task.order_id].append(task)
        except Exception as e:
            logger.info(f"批量查询AI任务失败: {e}")

    # 获取当前订单的AI任务（从批量查询的映射中获取）
    ai_tasks = ai_tasks_map.get(order.id, [])
    if AITask and not ai_tasks:
        # 如果批量查询失败，回退到单个查询
        try:
            ai_tasks = (
                AITask.query.filter_by(order_id=order.id, status="completed")
                .filter(AITask.output_image_path.isnot(None))
                .order_by(AITask.completed_at.desc())
                .all()
            )

            for task in ai_tasks:
                if task.output_image_path:
                    # 处理output_image_path：可能是相对路径、绝对路径或云端URL
                    output_path = task.output_image_path

                    # 如果是云端URL，直接使用
                    if output_path.startswith("http://") or output_path.startswith("https://"):
                        image_url = output_path
                        filename = output_path.split("/")[-1]  # 提取文件名
                    else:
                        # 如果是相对路径（如 final_works/xxx.png），提取文件名
                        if "/" in output_path or "\\" in output_path:
                            # 提取文件名（处理Windows和Unix路径）
                            filename = os.path.basename(output_path.replace("\\", "/"))
                        else:
                            filename = output_path

                        # 构建图片URL（使用缩略图进行预览）
                        from app.utils.image_thumbnail import get_thumbnail_path

                        # 检查缩略图是否存在
                        thumbnail_filename = get_thumbnail_path(filename)
                        # 提取缩略图文件名
                        if "/" in thumbnail_filename or "\\" in thumbnail_filename:
                            thumbnail_filename = os.path.basename(
                                thumbnail_filename.replace("\\", "/")
                            )

                        # 检查缩略图文件是否存在
                        hd_folder = app_instance.config.get("HD_FOLDER", "hd_images")
                        final_folder = app_instance.config.get("FINAL_FOLDER", "final_works")
                        if not os.path.isabs(hd_folder):
                            hd_folder = os.path.join(app_instance.root_path, hd_folder)
                        if not os.path.isabs(final_folder):
                            final_folder = os.path.join(app_instance.root_path, final_folder)

                        thumbnail_exists = False
                        if os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                            thumbnail_exists = True
                        elif os.path.exists(os.path.join(final_folder, thumbnail_filename)):
                            thumbnail_exists = True

                        # 如果缩略图存在，使用缩略图；否则使用原图
                        if thumbnail_exists:
                            encoded_filename = quote(thumbnail_filename, safe="")
                            image_url = f"/public/hd/{encoded_filename}"
                        else:
                            encoded_filename = quote(filename, safe="")
                            image_url = f"/public/hd/{encoded_filename}"

                    effect_images.append(
                        {
                            "id": task.id,
                            "filename": filename,
                            "url": image_url,
                            "created_at": task.completed_at or task.created_at,
                        }
                    )

            logger.info(
                f"订单详情 - 订单ID: {order_id}, 从AITask查询到效果图数量: {len(effect_images)}"
            )
            for img in effect_images:
                logger.info(f"  效果图: {img['filename']}")
        except Exception as e:
            logger.info(f"从AITask查询效果图失败: {e}")
            import traceback

            traceback.print_exc()

    # 如果AITask中没有效果图，尝试从文件系统读取（备选方案）
    if len(effect_images) == 0:
        logger.info("订单详情 - AITask中没有效果图，尝试从文件系统读取...")
        try:
            hd_folder = app_instance.config.get("HD_FOLDER", "hd_images")
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app_instance.root_path, hd_folder)

            logger.info(f"效果图文件夹路径: {hd_folder}")
            logger.info(f"文件夹是否存在: {os.path.exists(hd_folder)}")

            if os.path.exists(hd_folder):
                # 查找该订单的所有效果图文件
                import glob

                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                logger.info(f"搜索模式: {pattern}")
                effect_files = glob.glob(pattern)
                logger.info(f"找到文件数量: {len(effect_files)}")
                for f in effect_files:
                    logger.info(f"  文件: {f}")

                effect_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序

                for filepath in effect_files:
                    filename = os.path.basename(filepath)
                    encoded_filename = quote(filename, safe="")
                    image_url = f"/public/hd/{encoded_filename}"

                    effect_images.append(
                        {
                            "id": 0,  # 文件系统读取的没有ID
                            "filename": filename,
                            "url": image_url,
                            "created_at": datetime.fromtimestamp(os.path.getmtime(filepath)),
                        }
                    )

                logger.info(
                    f"订单详情 - 订单ID: {order_id}, 从文件系统读取到效果图数量: {len(effect_images)}"
                )
                for img in effect_images:
                    logger.info(f"  效果图: {img['filename']}")
            else:
                logger.warning("效果图文件夹不存在: {hd_folder}")
        except Exception as e:
            logger.error("从文件系统读取效果图失败: {e}")
            import traceback

            traceback.print_exc()
    else:
        logger.info(f"订单详情 - 从AITask获取到 {len(effect_images)} 张效果图，跳过文件系统读取")

    # 获取选片信息（从ShopOrder中获取）
    selected_images = []
    ShopOrder = models.get("ShopOrder")
    AITask = models.get("AITask")

    if ShopOrder:
        try:
            logger.info("\n=== 开始查询选片信息 ===")
            logger.info(
                f"订单ID: {order_id}, 订单号: {order.order_number}, 订单状态: {order.status}"
            )

            # 尝试通过original_order_id查询
            try:
                # 优化N+1查询：批量查询所有订单的ShopOrder
                order_ids_for_shop = [o.id for o in all_orders]
                shop_orders_by_id_map = {}
                if order_ids_for_shop:
                    all_shop_orders_by_id = ShopOrder.query.filter(
                        ShopOrder.original_order_id.in_(order_ids_for_shop)
                    ).all()
                    for shop_order in all_shop_orders_by_id:
                        if shop_order.original_order_id not in shop_orders_by_id_map:
                            shop_orders_by_id_map[shop_order.original_order_id] = []
                        shop_orders_by_id_map[shop_order.original_order_id].append(shop_order)

                # 从批量查询的映射中获取ShopOrder（避免N+1查询）
                shop_orders_by_id = shop_orders_by_id_map.get(order.id, [])
                logger.info(f"通过original_order_id查询到 {len(shop_orders_by_id)} 条记录")
            except Exception as e:
                logger.info(f"通过original_order_id查询失败: {e}")
                shop_orders_by_id = []

            # 尝试通过original_order_number查询
            try:
                # 优化N+1查询：批量查询所有订单号的ShopOrder
                order_numbers_for_shop = [o.order_number for o in all_orders]
                shop_orders_by_number_map = {}
                if order_numbers_for_shop:
                    all_shop_orders_by_number = ShopOrder.query.filter(
                        ShopOrder.original_order_number.in_(order_numbers_for_shop)
                    ).all()
                    for shop_order in all_shop_orders_by_number:
                        if shop_order.original_order_number not in shop_orders_by_number_map:
                            shop_orders_by_number_map[shop_order.original_order_number] = []
                        shop_orders_by_number_map[shop_order.original_order_number].append(
                            shop_order
                        )

                # 从批量查询的映射中获取ShopOrder（避免N+1查询）
                shop_orders_by_number = shop_orders_by_number_map.get(order.order_number, [])
                logger.info(f"通过original_order_number查询到 {len(shop_orders_by_number)} 条记录")
            except Exception as e:
                logger.info(f"通过original_order_number查询失败: {e}")
                shop_orders_by_number = []

            # 合并结果并去重
            shop_orders_dict = {}
            for so in shop_orders_by_id:
                shop_orders_dict[so.id] = so
            for so in shop_orders_by_number:
                shop_orders_dict[so.id] = so

            shop_orders = list(shop_orders_dict.values())

            # 排序
            try:
                shop_orders.sort(
                    key=lambda x: (
                        x.created_at if hasattr(x, "created_at") and x.created_at else x.id
                    )
                )
            except Exception:
                shop_orders.sort(key=lambda x: x.id)

            logger.info(f"合并后共 {len(shop_orders)} 条商城订单")

            # 按图片路径分组，每张图片关联多个产品
            images_dict = {}  # key: image_url, value: {image_url, image_path, products: []}

            for shop_order in shop_orders:
                logger.info(f"\n  处理商城订单: {shop_order.order_number}")
                logger.info(f"    original_order_id: {shop_order.original_order_id}")
                logger.info(f"    original_order_number: {shop_order.original_order_number}")
                logger.info(f"    image_url: {shop_order.image_url}")
                logger.info(
                    f"    产品: {shop_order.product_name}, 规格: {shop_order.size_name}, 数量: {shop_order.quantity}"
                )

                # 获取图片路径
                image_path = shop_order.image_url

                # 如果image_url为空，尝试从AITask获取
                if not image_path and shop_order.original_order_id and AITask:
                    logger.info("    image_url为空，尝试从AITask获取...")
                    # 这里需要知道具体是哪个AITask，暂时跳过
                    # 可以考虑在customer_note中存储task_id
                    pass

                if image_path:
                    # 如果该图片已存在，添加产品信息
                    if image_path in images_dict:
                        existing = images_dict[image_path]
                        # 添加产品信息到列表
                        existing["products"].append(
                            {
                                "order_number": shop_order.order_number,
                                "product_id": shop_order.product_id,
                                "product_name": shop_order.product_name or "",
                                "size_id": shop_order.size_id,
                                "size_name": shop_order.size_name or "",
                                "quantity": shop_order.quantity or 1,
                                "price": float(shop_order.price or 0),
                                "total_price": float(shop_order.price or 0)
                                * (shop_order.quantity or 1),
                            }
                        )
                        logger.info(
                            f"    📝 添加产品到已有图片: {shop_order.product_name}-{shop_order.size_name}"
                        )
                    else:
                        # 构建图片URL - image_url存储的是AITask的output_image_path
                        # 与效果图使用相同的URL构建方式
                        # 直接使用image_path作为filename（与效果图逻辑一致）
                        encoded_filename = quote(image_path, safe="")
                        image_url = f"/public/hd/{encoded_filename}"

                        images_dict[image_path] = {
                            "image_url": image_url,
                            "image_path": shop_order.image_url,
                            "products": [
                                {
                                    "order_number": shop_order.order_number,
                                    "product_id": shop_order.product_id,
                                    "product_name": shop_order.product_name or "",
                                    "size_id": shop_order.size_id,
                                    "size_name": shop_order.size_name or "",
                                    "quantity": shop_order.quantity or 1,
                                    "price": float(shop_order.price or 0),
                                    "total_price": float(shop_order.price or 0)
                                    * (shop_order.quantity or 1),
                                }
                            ],
                            "created_at": (
                                shop_order.created_at
                                if hasattr(shop_order, "created_at") and shop_order.created_at
                                else None
                            ),
                        }
                        logger.info(
                            f"    ✅ 添加新图片: URL={image_url}, 产品: {shop_order.product_name}-{shop_order.size_name}"
                        )
                else:
                    logger.info("    ⚠️ 跳过：image_url为空")

            # 将按图片分组的数据转换为列表
            selected_images = list(images_dict.values())

            logger.info(f"\n最终选片数量: {len(selected_images)}")
            logger.info("=== 选片信息查询完成 ===\n")

        except Exception as e:
            logger.error("查询选片信息失败: {e}")
            import traceback

            traceback.print_exc()
    else:
        logger.warning("ShopOrder模型不存在，无法查询选片信息")

    logger.info(f"订单详情页面 - 订单ID: {order_id}")
    logger.info(f"订单final_image字段: {order.final_image}")
    if order.final_image:
        final_path = os.path.join(current_app.config["FINAL_FOLDER"], order.final_image)
        logger.info(f"效果图完整路径: {final_path}")
        logger.info(f"效果图文件是否存在: {os.path.exists(final_path)}")

    if request.method == "POST":
        logger.info("=" * 50)
        logger.info(f"收到订单更新请求，订单ID: {order_id}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求文件键: {list(request.files.keys())}")
        logger.info(f"请求表单键: {list(request.form.keys())}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Content-Length: {request.content_length}")

        # 详细打印文件信息
        logger.info("=" * 50)
        logger.info("所有文件字段:")
        for key in request.files:
            files = request.files.getlist(key)
            logger.info(f"  字段 '{key}': {len(files)} 个文件")
            for idx, file in enumerate(files):
                if file and file.filename:
                    logger.info(
                        f"    文件 {idx + 1}: {file.filename}, 大小: {file.content_length or '未知'} bytes"
                    )
                else:
                    logger.info(f"    文件 {idx + 1}: 空文件或无效文件")

        # 特别检查hd_image[]字段
        if "hd_image[]" in request.files:
            hd_files = request.files.getlist("hd_image[]")
            logger.info(f"\n特别检查 - hd_image[]字段: 找到 {len(hd_files)} 个文件")
            for idx, f in enumerate(hd_files):
                if f and f.filename:
                    logger.info(
                        f"  hd_image[{idx}]: {f.filename}, 大小: {f.content_length or '未知'} bytes"
                    )
                else:
                    logger.info(f"  hd_image[{idx}]: 空文件")

        logger.info("=" * 50)

        try:
            # 处理精修图上传
            if "final_image" in request.files:
                final_image_file = request.files["final_image"]
                if final_image_file and final_image_file.filename:
                    logger.info(f"处理精修图上传: {final_image_file.filename}")
                    try:
                        # 确保目录存在
                        final_folder = app_instance.config.get("FINAL_FOLDER", "final_works")
                        if not os.path.isabs(final_folder):
                            final_folder = os.path.join(app_instance.root_path, final_folder)
                        os.makedirs(final_folder, exist_ok=True)
                        logger.info(f"精修图目录: {final_folder}")

                        # 生成文件名
                        filename = secure_filename(final_image_file.filename)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{order.order_number}_final_{timestamp}_{filename}"
                        filepath = os.path.join(final_folder, filename)

                        # 保存文件
                        final_image_file.save(filepath)
                        logger.info(
                            f"精修图保存成功: {filepath}, 文件大小: {os.path.getsize(filepath)} bytes"
                        )

                        # 更新订单
                        order.final_image = filename
                        # 如果精修图完成时间未设置，则设置当前时间
                        if not order.retouch_completed_at:
                            order.retouch_completed_at = datetime.now()

                        # 更新订单状态为"美颜处理中"（如果当前状态是shooting）
                        if order.status in ["shooting", "paid"]:
                            order.status = "retouching"  # 美颜处理中

                        flash("精修图上传成功", "success")
                    except Exception as e:
                        logger.info(f"精修图上传失败: {str(e)}")
                        import traceback

                        traceback.print_exc()
                        flash(f"精修图上传失败: {str(e)}", "error")

            # 处理效果图上传（支持多图）
            hd_images_uploaded = []

            # 尝试多种方式获取文件
            hd_image_files = []
            if "hd_image[]" in request.files:
                hd_image_files = request.files.getlist("hd_image[]")
                logger.info(f"从 'hd_image[]' 字段获取到 {len(hd_image_files)} 个文件")
            elif "hd_image" in request.files:
                # 兼容单图上传
                single_file = request.files["hd_image"]
                if single_file and single_file.filename:
                    hd_image_files = [single_file]
                    logger.info("从 'hd_image' 字段获取到 1 个文件")

            # 过滤掉空文件
            hd_image_files = [f for f in hd_image_files if f and f.filename]
            logger.info(f"过滤后，有效文件数量: {len(hd_image_files)}")

            if hd_image_files:
                logger.info(f"开始处理效果图上传，共 {len(hd_image_files)} 张")
                AITask = models.get("AITask")

                # 如果从models中获取不到，尝试直接从test_server模块获取
                if not AITask:
                    if "test_server" in sys.modules:
                        test_server_module = sys.modules["test_server"]
                        AITask = getattr(test_server_module, "AITask", None)
                        if AITask:
                            logger.info("✅ 从test_server模块直接获取AITask模型成功")

                try:
                    # 确保目录存在
                    hd_folder = app_instance.config.get("HD_FOLDER", "hd_images")
                    if not os.path.isabs(hd_folder):
                        hd_folder = os.path.join(app_instance.root_path, hd_folder)
                    os.makedirs(hd_folder, exist_ok=True)
                    logger.info(f"效果图目录: {hd_folder}")

                    # 处理每张效果图
                    for idx, hd_image_file in enumerate(hd_image_files):
                        if not hd_image_file or not hd_image_file.filename:
                            continue

                        logger.info(f"处理第 {idx + 1} 张效果图: {hd_image_file.filename}")

                        # 生成文件名
                        filename = secure_filename(hd_image_file.filename)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{order.order_number}_effect_{timestamp}_{idx + 1:03d}_{filename}"
                        filepath = os.path.join(hd_folder, filename)

                        # 保存文件
                        hd_image_file.save(filepath)
                        file_size = os.path.getsize(filepath)
                        logger.info(f"效果图保存成功: {filepath}, 文件大小: {file_size} bytes")

                        # 生成缩略图（长边1920px的JPG）
                        try:
                            from app.utils.image_thumbnail import generate_thumbnail

                            thumbnail_path = generate_thumbnail(filepath, max_size=1920, quality=85)
                            if thumbnail_path:
                                logger.info(f"✅ 缩略图生成成功: {thumbnail_path}")
                        except Exception as thumb_error:
                            logger.warning("生成缩略图失败: {str(thumb_error)}")
                            import traceback

                            traceback.print_exc()

                        # 创建AITask记录（用于选片功能）
                        if AITask:
                            try:
                                ai_task = AITask(
                                    order_id=order.id,
                                    order_number=order.order_number,
                                    status="completed",
                                    output_image_path=filename,  # 只保存文件名，相对路径
                                    completed_at=datetime.now(),
                                )
                                db.session.add(ai_task)
                                # 立即刷新以获取ID
                                db.session.flush()
                                logger.info(
                                    f"✅ 创建AITask记录: task_id={ai_task.id}, output_image_path={filename}, order_id={order.id}"
                                )
                            except Exception as e:
                                logger.error("创建AITask记录失败: {str(e)}")
                                import traceback

                                traceback.print_exc()
                        else:
                            logger.warning("AITask模型未找到，跳过创建AITask记录")

                        hd_images_uploaded.append(filename)

                        # 第一张效果图作为主图，更新订单的hd_image字段
                        if idx == 0:
                            order.hd_image = filename

                    # 如果制作完成时间未设置，则设置当前时间
                    if not order.completed_at and hd_images_uploaded:
                        order.completed_at = datetime.now()

                    # 更新订单状态：如果当前是ai_processing，改为pending_selection（待选片）
                    if (
                        order.status in ["ai_processing", "retouching", "shooting"]
                        and hd_images_uploaded
                    ):
                        order.status = "pending_selection"  # 待选片
                        logger.info(
                            f"✅ 订单 {order.order_number} 效果图已上传，状态已更新为: pending_selection"
                        )

                    if hd_images_uploaded:
                        flash(f"效果图上传成功，共 {len(hd_images_uploaded)} 张", "success")

                except Exception as e:
                    logger.info(f"效果图上传失败: {str(e)}")
                    import traceback

                    traceback.print_exc()
                    flash(f"效果图上传失败: {str(e)}", "error")

            # 处理订单状态更新
            if "status" in request.form:
                new_status = request.form.get("status")
                if new_status:
                    order.status = new_status
                    logger.info(f"订单状态更新为: {new_status}")

            # 处理产品名称和尺寸（如果提供）
            if "product_name" in request.form:
                product_name = request.form.get("product_name")
                if product_name:
                    order.product_name = product_name

            if "size" in request.form:
                size = request.form.get("size")
                if size:
                    order.size = size

            # 提交更改
            db.session.commit()
            logger.info("=" * 50)
            logger.info(f"✅ 订单更新成功，订单ID: {order_id}")
            logger.info("=" * 50)
            flash("订单更新成功", "success")

        except Exception as e:
            db.session.rollback()
            logger.info("=" * 50)
            logger.error("订单更新失败: {str(e)}")
            logger.info(f"错误类型: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            logger.info("=" * 50)
            flash(f"订单更新失败: {str(e)}", "error")

        return redirect(
            url_for("admin_orders.admin_orders_detail.admin_order_detail", order_id=order_id)
        )

    return render_template(
        "admin/order_details.html",
        order=order,
        all_orders=all_orders,  # 传递所有使用相同订单号的订单记录
        images=images,
        effect_images=effect_images,  # 传递所有效果图
        selected_images=selected_images,  # 传递选片信息
        products=products,
        size_options=size_options,
    )


@admin_orders_detail_bp.route("/admin/orders/batch-update-status", methods=["POST"])
@login_required
@admin_required
def batch_update_order_status():
    """批量更新订单状态（基于AI任务完成情况）"""
    try:
        models = get_models(["Order", "AITask", "db"])
        if not models:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Order = models["Order"]
        AITask = models["AITask"]
        db = models["db"]

        # 查找所有状态为"AI任务处理中"的订单
        orders_to_check = Order.query.filter(
            Order.status.in_(["ai_processing", "retouching", "shooting", "processing"])
        ).all()

        # 批量查询所有订单的AI任务（优化N+1查询）
        order_ids = [order.id for order in orders_to_check]
        tasks_by_order = {}
        if AITask and order_ids:
            # 一次性查询所有相关订单的AI任务
            all_tasks = AITask.query.filter(AITask.order_id.in_(order_ids)).all()
            # 按订单ID分组
            for task in all_tasks:
                if task.order_id not in tasks_by_order:
                    tasks_by_order[task.order_id] = []
                tasks_by_order[task.order_id].append(task)

        updated_count = 0
        skipped_count = 0
        updated_orders = []

        for order in orders_to_check:
            # 从批量查询结果中获取该订单的所有AI任务（避免N+1查询）
            all_tasks = tasks_by_order.get(order.id, [])

            if len(all_tasks) == 0:
                skipped_count += 1
                continue

            # 过滤掉失败和取消的任务，只统计有效任务
            valid_tasks = [t for t in all_tasks if t.status not in ["failed", "cancelled"]]
            completed_tasks = [
                t for t in valid_tasks if t.status == "completed" and t.output_image_path
            ]

            # 如果所有有效任务都已完成，更新订单状态为"待选片"
            if len(valid_tasks) > 0 and len(completed_tasks) == len(valid_tasks):
                old_status = order.status
                order.status = "pending_selection"  # 待选片
                updated_count += 1
                updated_orders.append(
                    {
                        "order_number": order.order_number,
                        "old_status": old_status,
                        "new_status": "pending_selection",
                        "tasks_count": len(valid_tasks),
                    }
                )
            else:
                skipped_count += 1

        if updated_count > 0:
            db.session.commit()
            return jsonify(
                {
                    "status": "success",
                    "message": f"批量更新完成，更新了 {updated_count} 个订单状态",
                    "data": {
                        "updated_count": updated_count,
                        "skipped_count": skipped_count,
                        "updated_orders": updated_orders,
                    },
                }
            )
        else:
            return jsonify(
                {
                    "status": "info",
                    "message": f"没有订单需要更新（跳过了 {skipped_count} 个订单）",
                    "data": {"updated_count": 0, "skipped_count": skipped_count},
                }
            )

    except Exception as e:
        logger.info(f"批量更新订单状态失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"批量更新失败: {str(e)}"}), 500


@admin_orders_detail_bp.route("/admin/orders/add", methods=["GET", "POST"])
@login_required
def admin_add_order():
    """管理员手动新增订单"""
    if current_user.role != "admin":
        return redirect(url_for("auth.login"))

    models = get_models(["Order", "OrderImage", "db"])
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    Order = models["Order"]
    OrderImage = models["OrderImage"]
    db = models["db"]

    if "test_server" in sys.modules:
        test_server_module = sys.modules["test_server"]
        app = test_server_module.app if hasattr(test_server_module, "app") else current_app
        WECHAT_NOTIFICATION_AVAILABLE = getattr(
            test_server_module, "WECHAT_NOTIFICATION_AVAILABLE", False
        )
        wechat_notify = getattr(test_server_module, "wechat_notify", None)
    else:
        app = current_app
        WECHAT_NOTIFICATION_AVAILABLE = False
        wechat_notify = None

    if request.method == "POST":
        try:
            # 获取表单数据
            customer_name = request.form["customer_name"]
            customer_phone = request.form["customer_phone"]
            price = float(request.form["price"])
            status = request.form.get("status", "pending")
            source_type = request.form.get("source_type", "website")
            external_platform = request.form.get("external_platform", "")
            external_order_number = request.form.get("external_order_number", "")
            customer_address = request.form.get("customer_address", "")

            # 处理图片上传
            original_image = None
            if "original_image" in request.files:
                file = request.files["original_image"]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(filepath)
                    original_image = filename

            # 创建订单
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                price=price,
                status=status,
                source_type=source_type,
                external_platform=external_platform,
                external_order_number=external_order_number,
                customer_address=customer_address,
                original_image=original_image or "manual_order.jpg",  # 默认图片
            )

            db.session.add(order)
            db.session.flush()  # 获取订单ID，但不提交事务

            # 如果有图片，创建OrderImage记录
            if original_image:
                order_image = OrderImage(
                    order_id=order.id,
                    path=original_image,
                    is_main=True,  # 管理员手动创建的订单，第一张图片设为主图
                )
                db.session.add(order_image)

            db.session.commit()

            # ⭐ 发送微信通知
            if WECHAT_NOTIFICATION_AVAILABLE and wechat_notify:
                try:
                    wechat_notify(
                        order_number=order.order_number,
                        customer_name=customer_name,
                        total_price=price,
                        source="管理后台",
                    )
                except Exception as e:
                    logger.info(f"微信通知失败: {e}")

            flash("订单创建成功！", "success")
            # 重定向到订单详情页
            return redirect(
                url_for("admin_orders.admin_orders_detail.admin_order_detail", order_id=order.id)
            )

        except Exception as e:
            db.session.rollback()
            flash(f"订单创建失败：{str(e)}", "error")
            import traceback

            traceback.print_exc()

    return render_template("admin/add_order.html")


@admin_orders_detail_bp.route("/admin/orders/get-customer-info", methods=["GET"])
@login_required
@admin_required
def get_customer_info():
    """根据手机号获取客户信息（用于自动填充）"""
    try:
        phone = request.args.get("phone", "").strip()

        if not phone:
            return jsonify({"success": False, "message": "缺少手机号参数"}), 400

        models = get_models(["PromotionUser", "Order"])
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        PromotionUser = models.get("PromotionUser")
        Order = models.get("Order")

        customer_name = None

        # 1. 优先从PromotionUser表查找（小程序用户）
        if PromotionUser:
            promotion_user = PromotionUser.query.filter_by(phone_number=phone).first()
            if promotion_user:
                customer_name = promotion_user.nickname or promotion_user.user_id
                return jsonify(
                    {"success": True, "customer_name": customer_name, "source": "promotion_user"}
                )

        # 2. 从订单表中查找最近使用该手机号的订单
        if Order:
            recent_order = (
                Order.query.filter_by(customer_phone=phone)
                .order_by(Order.created_at.desc())
                .first()
            )
            if recent_order and recent_order.customer_name:
                customer_name = recent_order.customer_name
                return jsonify(
                    {"success": True, "customer_name": customer_name, "source": "recent_order"}
                )

        # 3. 如果都没找到，返回提示信息
        return jsonify(
            {"success": False, "message": "未找到该手机号的注册用户，请手动填写客户姓名"}
        )

    except Exception as e:
        logger.info(f"获取客户信息失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取客户信息失败: {str(e)}"}), 500


@admin_orders_detail_bp.route("/admin/order/<int:order_id>/delete-effect-image", methods=["POST"])
@login_required
@admin_required
def delete_effect_image(order_id):
    """删除订单效果图"""
    try:
        models = get_models(["Order", "AITask", "db"])
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        Order = models["Order"]
        AITask = models.get("AITask")
        db = models["db"]

        # 获取订单
        order = Order.query.get_or_404(order_id)

        # 获取请求数据
        data = request.get_json()
        task_id = data.get("task_id")
        filename = data.get("filename")

        if not filename:
            return jsonify({"success": False, "message": "缺少文件名参数"}), 400

        # 获取app实例
        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            app_instance = (
                test_server_module.app if hasattr(test_server_module, "app") else current_app
            )
        else:
            app_instance = current_app

        deleted_count = 0

        # 1. 如果提供了task_id且不为0，删除AITask记录
        if task_id and task_id != 0 and AITask:
            task = AITask.query.filter_by(id=task_id, order_id=order_id).first()
            if task:
                # 删除AITask记录
                db.session.delete(task)
                deleted_count += 1
                logger.info(f"删除AITask记录: task_id={task_id}, order_id={order_id}")

        # 2. 删除文件系统中的效果图文件
        hd_folder = app_instance.config.get("HD_FOLDER", "hd_images")
        final_folder = app_instance.config.get("FINAL_FOLDER", "final_works")

        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(app_instance.root_path, hd_folder)
        if not os.path.isabs(final_folder):
            final_folder = os.path.join(app_instance.root_path, final_folder)

        # 删除原图
        file_paths = [os.path.join(hd_folder, filename), os.path.join(final_folder, filename)]

        # 删除缩略图（如果存在）
        from app.utils.image_thumbnail import get_thumbnail_path

        thumbnail_filename = get_thumbnail_path(filename)
        if "/" in thumbnail_filename or "\\" in thumbnail_filename:
            thumbnail_filename = os.path.basename(thumbnail_filename.replace("\\", "/"))

        file_paths.extend(
            [
                os.path.join(hd_folder, thumbnail_filename),
                os.path.join(final_folder, thumbnail_filename),
            ]
        )

        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"删除文件: {file_path}")
                except Exception as e:
                    logger.info(f"删除文件失败: {file_path}, 错误: {e}")

        # 3. 如果删除的是订单的hd_image字段对应的图片，清空该字段
        if order.hd_image == filename:
            order.hd_image = None
            logger.info(f"清空订单hd_image字段: order_id={order_id}")

        # 提交更改
        db.session.commit()

        return jsonify(
            {"success": True, "message": f"效果图删除成功（删除了 {deleted_count} 个文件/记录）"}
        )

    except Exception as e:
        db.session.rollback()
        logger.info(f"删除效果图失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"删除失败: {str(e)}"}), 500
