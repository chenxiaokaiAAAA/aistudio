# -*- coding: utf-8 -*-
"""
选片页面 - 打印相关功能
"""

import logging

logger = logging.getLogger(__name__)
import os

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models

from .utils import get_app_instance

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_print", __name__)


@bp.route("/admin/photo-selection/<int:order_id>/start-print", methods=["POST"])
@login_required
def start_print(order_id):
    """开始打印照片"""
    if current_user.role not in ["admin", "operator"]:
        return jsonify({"success": False, "message": "权限不足"}), 403

    models = get_models()
    if not models:
        return jsonify({"success": False, "message": "系统未初始化"}), 500

    Order = models["Order"]
    SelectionOrder = models.get("SelectionOrder")
    AITask = models["AITask"]
    db = models["db"]

    try:
        data = request.get_json()
        order_numbers = data.get("order_numbers", [])

        if not order_numbers:
            return jsonify({"success": False, "message": "订单号不能为空"}), 400

        # 获取原订单
        order = Order.query.get_or_404(order_id)

        # 获取选片订单（产品馆）
        shop_orders = []
        if SelectionOrder:
            shop_orders = SelectionOrder.query.filter(
                SelectionOrder.order_number.in_(order_numbers)
            ).all()

        # 检查是否启用冲印系统
        try:
            from printer_client import PrinterSystemClient
            from printer_config import PRINTER_SYSTEM_CONFIG

            if not PRINTER_SYSTEM_CONFIG.get("enabled", False):
                return jsonify({"success": False, "message": "冲印系统未启用"}), 400

            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        except ImportError:
            return jsonify({"success": False, "message": "冲印系统模块未找到"}), 500

        # 获取应用实例
        app = get_app_instance()

        # 获取高清图片文件夹
        hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(app.root_path, hd_folder)

        success_count = 0
        failed_count = 0
        errors = []

        # 根据订单获取对应的打印机配置（支持多门店）
        from app.utils.printer_config_helper import get_printer_config_for_order

        printer_config = get_printer_config_for_order(order, models)
        local_printer_path = printer_config.get("local_printer_path") or None
        local_printer_proxy_url = printer_config.get("local_printer_proxy_url") or None
        local_printer_proxy_api_key = printer_config.get("local_printer_proxy_api_key") or None

        logger.info(f"订单 {order.order_number} 的打印机配置:")
        logger.info(f"  自拍机ID: {printer_config.get('machine_id')}")
        logger.info(f"  门店名称: {printer_config.get('store_name')}")
        logger.info(f"  本地打印机路径: {local_printer_path}")
        logger.info(f"  打印代理服务地址: {local_printer_proxy_url}")

        # 优化N+1查询：批量查询所有产品馆产品信息和AI任务
        Product = models.get("Product")
        products_map = {}
        if Product and shop_orders:
            product_ids = [so.product_id for so in shop_orders if so.product_id]
            if product_ids:
                all_products = Product.query.filter(Product.id.in_(product_ids)).all()
                for product in all_products:
                    products_map[product.id] = product

        # 批量查询所有订单的AI任务（避免N+1查询）
        ai_tasks_map = {}
        if AITask and shop_orders:
            original_order_ids = [
                so.original_order_id for so in shop_orders if so.original_order_id
            ]
            if original_order_ids:
                all_ai_tasks = AITask.query.filter(
                    AITask.order_id.in_(original_order_ids), AITask.status == "completed"
                ).all()
                for task in all_ai_tasks:
                    if task.order_id not in ai_tasks_map:
                        ai_tasks_map[task.order_id] = []
                    ai_tasks_map[task.order_id].append(task)

        # 为每个商城订单发送打印任务
        for shop_order in shop_orders:
            try:
                # 获取产品信息，判断是电子照片还是实物产品（从批量查询的映射中获取）
                is_digital_photo = False

                if shop_order.product_id and shop_order.product_id in products_map:
                    product = products_map[shop_order.product_id]
                    # 产品馆产品：根据分类或产品名称判断是否为电子照片（证件照等）
                    category_name = ""
                    if hasattr(product, "category") and product.category:
                        category_name = (getattr(product.category, "name", "") or "").lower()
                    if not category_name and hasattr(product, "subcategory") and product.subcategory:
                        category_name = (getattr(product.subcategory, "name", "") or "").lower()
                    product_name = (getattr(product, "name", "") or "").lower()
                    if category_name in ["digital_photo", "photo", "电子照片", "照片", "证件照"] or "证件照" in product_name:
                        is_digital_photo = True

                # 获取图片路径（打印时使用原图，不是缩略图）
                image_path = shop_order.image_url
                if not image_path:
                    # 如果没有图片URL，尝试从AITask获取（从批量查询的映射中获取）
                    if (
                        shop_order.original_order_id
                        and shop_order.original_order_id in ai_tasks_map
                    ):
                        tasks = ai_tasks_map[shop_order.original_order_id]
                        if tasks and tasks[0].output_image_path:
                            image_path = tasks[0].output_image_path

                if not image_path:
                    errors.append(f"订单 {shop_order.order_number} 没有图片路径")
                    failed_count += 1
                    continue

                # 如果image_path是缩略图路径，转换为原图路径
                if image_path.endswith("_thumb.jpg"):
                    from app.utils.image_thumbnail import get_original_path

                    base_name = image_path.replace("_thumb.jpg", "")
                    # 尝试常见的图片扩展名
                    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                        test_path = base_name + ext
                        test_full_path = os.path.join(hd_folder, test_path)
                        if os.path.exists(test_full_path):
                            image_path = test_path
                            logger.info(
                                f"✅ 打印时使用原图: {image_path} (从缩略图 {shop_order.image_url} 转换)"
                            )
                            break

                # 构建完整路径
                full_image_path = os.path.join(hd_folder, image_path)
                if not os.path.exists(full_image_path):
                    # 尝试其他路径
                    possible_paths = [
                        full_image_path,
                        os.path.join("hd_images", image_path),
                        os.path.join("uploads", image_path),
                        os.path.join("final_works", image_path),
                        image_path,  # 直接使用原始路径
                    ]
                    found = False
                    for path in possible_paths:
                        if os.path.exists(path):
                            full_image_path = path
                            found = True
                            break

                    if not found:
                        errors.append(
                            f"订单 {shop_order.order_number} 的图片文件不存在: {image_path}"
                        )
                        failed_count += 1
                        continue

                # 根据产品类型选择打印方式
                if is_digital_photo:
                    # 电子照片：使用本地打印机
                    try:
                        # 使用从订单获取的打印机配置（已支持多门店）
                        if local_printer_proxy_url:
                            # 使用打印代理服务（远程部署）
                            from local_printer_client import LocalPrinterClient

                            printer_client_proxy = LocalPrinterClient(
                                local_printer_proxy_url, local_printer_proxy_api_key
                            )

                            # 构建图片URL（需要可公网访问）
                            from urllib.parse import quote

                            try:
                                from printer_config import PRINTER_SYSTEM_CONFIG

                                file_access_base_url = PRINTER_SYSTEM_CONFIG.get(
                                    "file_access_base_url", "http://photogooo"
                                )
                            except Exception:
                                # 从配置表获取
                                try:
                                    AIConfig = models.get("AIConfig")
                                    if AIConfig:
                                        file_url_config = AIConfig.query.filter_by(
                                            config_key="printer_file_access_base_url"
                                        ).first()
                                        file_access_base_url = (
                                            file_url_config.config_value
                                            if file_url_config
                                            else "http://photogooo"
                                        )
                                    else:
                                        file_access_base_url = "http://photogooo"
                                except Exception:
                                    file_access_base_url = "http://photogooo"

                            # 打印时使用原图，确保image_path不是缩略图
                            original_image_path = image_path
                            if image_path.endswith("_thumb.jpg"):
                                base_name = image_path.replace("_thumb.jpg", "")
                                # 尝试常见的图片扩展名
                                for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                                    test_path = base_name + ext
                                    test_full_path = os.path.join(hd_folder, test_path)
                                    if os.path.exists(test_full_path):
                                        original_image_path = test_path
                                        logger.info(
                                            f"✅ 打印代理使用原图: {original_image_path} (从缩略图 {image_path} 转换)"
                                        )
                                        break

                            encoded_filename = quote(original_image_path, safe="")
                            image_url = (
                                f"{file_access_base_url}/public/hd/original/{encoded_filename}"
                            )

                            result = printer_client_proxy.print_image(
                                image_url=image_url, copies=shop_order.quantity or 1
                            )
                        elif local_printer_path:
                            # 直接使用本地打印机（本地部署）
                            from local_printer import LocalPrinter

                            local_printer = LocalPrinter(local_printer_path)
                            result = local_printer.print_image(
                                full_image_path, copies=shop_order.quantity or 1
                            )
                        else:
                            # 没有配置本地打印机
                            result = {"success": False, "message": "未配置本地打印机或打印代理服务"}

                        if result.get("success"):
                            success_count += 1
                            if hasattr(shop_order, "status"):
                                shop_order.status = "printing"  # 打印中

                            # 更新原订单状态为"打印中"（如果当前状态是selection_completed）
                            if order.status == "selection_completed":
                                order.status = "printing"  # 打印中
                        else:
                            failed_count += 1
                            error_msg = result.get("message", "本地打印失败")
                            errors.append(
                                f"订单 {shop_order.order_number} 本地打印失败: {error_msg}"
                            )
                    except ImportError:
                        # 如果本地打印模块不可用，回退到远程API
                        errors.append(
                            f"订单 {shop_order.order_number} 本地打印模块未找到，使用远程API"
                        )
                        is_digital_photo = False
                    except Exception as e:
                        failed_count += 1
                        error_msg = f"本地打印失败: {str(e)}"
                        errors.append(f"订单 {shop_order.order_number} {error_msg}")
                        logger.info(f"本地打印失败: {e}")
                        import traceback

                        traceback.print_exc()

                if not is_digital_photo or not local_printer_path:
                    # 实物产品：发送到远程冲印系统
                    result = printer_client.send_order_to_printer(
                        shop_order, full_image_path, order_obj=shop_order
                    )

                    if result.get("success"):
                        success_count += 1
                        # 更新商城订单状态
                        if hasattr(shop_order, "status"):
                            shop_order.status = "printing"  # 打印中

                        # 更新原订单状态为"打印中"（如果当前状态是selection_completed）
                        if order.status == "selection_completed":
                            order.status = "printing"  # 打印中
                        if hasattr(shop_order, "status"):
                            shop_order.status = "printing"  # 打印中
                    else:
                        failed_count += 1
                        error_msg = result.get("message", "未知错误")
                        errors.append(f"订单 {shop_order.order_number} 打印失败: {error_msg}")

            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                errors.append(f"订单 {shop_order.order_number} 处理失败: {error_msg}")
                logger.info(f"处理订单 {shop_order.order_number} 时发生错误: {e}")
                import traceback

                traceback.print_exc()

        db.session.commit()

        if success_count > 0:
            message = f"成功启动 {success_count} 个打印任务"
            if failed_count > 0:
                message += f"，{failed_count} 个失败"
            return jsonify(
                {
                    "success": True,
                    "message": message,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "errors": errors,
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "所有打印任务都失败了", "errors": errors}),
                400,
            )

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"启动打印失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"启动打印失败: {str(e)}"}), 500
