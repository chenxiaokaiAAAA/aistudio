# -*- coding: utf-8 -*-
"""
选片页面 - 订单详情
"""

import logging

logger = logging.getLogger(__name__)
import glob
import os
from datetime import datetime
from urllib.parse import quote

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.utils.admin_helpers import get_models
from app.utils.image_thumbnail import get_thumbnail_path

from .utils import check_photo_selection_permission, get_app_instance

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("photo_selection_detail", __name__)


@bp.route("/admin/photo-selection/<int:order_id>")
def photo_selection_detail(order_id):
    """选片页面 - 选片详情"""
    models = get_models(
        [
            "Order",
            "AITask",
            "Product",
            "ProductSize",
            "ShopProduct",
            "ShopProductSize",
            "StyleCategory",
            "StyleImage",
            "PrintSizeConfig",
            "MockupTemplate",
            "MockupTemplateProduct",
        ]
    )
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("photo_selection.photo_selection_list.photo_selection_list"))

    Order = models["Order"]
    AITask = models["AITask"]
    Product = models["Product"]
    ProductSize = models["ProductSize"]

    order = Order.query.get_or_404(order_id)

    # 检查用户权限
    from flask import session

    session_franchisee_id = session.get("franchisee_id")
    has_permission, redirect_response = check_photo_selection_permission(
        order, session_franchisee_id, current_user
    )
    if not has_permission:
        return redirect_response

    # 获取应用实例
    app = get_app_instance()
    if app is None:
        flash("系统错误：无法获取应用实例", "error")
        return redirect(url_for("photo_selection.photo_selection_list.photo_selection_list"))

    # 获取订单的所有已完成的效果图（从AITask中获取）
    ai_tasks = (
        AITask.query.filter_by(order_id=order.id, status="completed")
        .filter(AITask.output_image_path.isnot(None))
        .order_by(AITask.completed_at.desc())
        .all()
    )

    # 构建效果图列表
    effect_images = []
    for task in ai_tasks:
        if task.output_image_path:
            # 处理output_image_path：可能是相对路径、绝对路径或云端URL
            output_path = task.output_image_path

            # 如果是云端URL，直接使用
            if output_path.startswith("http://") or output_path.startswith("https://"):
                image_url = output_path
                filename = output_path.split("/")[-1]  # 提取文件名

                effect_images.append(
                    {
                        "id": task.id,
                        "url": image_url,
                        "path": filename,
                        "created_at": task.completed_at or task.created_at,
                    }
                )
            else:
                # 如果是相对路径（如 final_works/xxx.png），提取文件名
                if "/" in output_path or "\\" in output_path:
                    # 提取文件名（处理Windows和Unix路径）
                    filename = os.path.basename(output_path.replace("\\", "/"))
                else:
                    filename = output_path

                # 先获取文件夹路径（在使用之前定义）
                hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
                final_folder = app.config.get(
                    "FINAL_FOLDER", os.path.join(app.root_path, "final_works")
                )

                if not os.path.isabs(hd_folder):
                    hd_folder = os.path.join(app.root_path, hd_folder)
                if not os.path.isabs(final_folder):
                    final_folder = os.path.join(app.root_path, final_folder)

                # 构建图片URL（使用缩略图进行预览）
                # 检查缩略图是否存在
                thumbnail_filename = get_thumbnail_path(filename)
                # 提取缩略图文件名（去掉路径）
                if "/" in thumbnail_filename or "\\" in thumbnail_filename:
                    thumbnail_filename = os.path.basename(thumbnail_filename.replace("\\", "/"))

                # 检查缩略图文件是否存在
                thumbnail_exists = False
                if os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                    thumbnail_exists = True
                elif os.path.exists(os.path.join(final_folder, thumbnail_filename)):
                    thumbnail_exists = True

                # 如果缩略图存在，使用缩略图；否则使用原图
                if thumbnail_exists:
                    encoded_filename = quote(thumbnail_filename, safe="")
                    image_url = f"/public/hd/{encoded_filename}"
                    logger.info(f"✅ 使用缩略图: {thumbnail_filename}")
                else:
                    encoded_filename = quote(filename, safe="")
                    image_url = f"/public/hd/{encoded_filename}"
                    logger.warning(f"缩略图不存在，使用原图: {filename}")

                # 检查文件是否存在（优先检查HD_FOLDER，然后检查FINAL_FOLDER）
                file_exists = False
                if os.path.exists(os.path.join(hd_folder, filename)):
                    file_exists = True
                elif os.path.exists(os.path.join(final_folder, filename)):
                    file_exists = True

                if file_exists:
                    effect_images.append(
                        {
                            "id": task.id,
                            "url": image_url,
                            "path": filename,
                            "created_at": task.completed_at or task.created_at,
                        }
                    )
                else:
                    # 即使文件不存在，也添加（可能是云端文件，通过URL访问）
                    logger.warning(
                        f"选片详情 - 效果图文件不存在: {filename} (在HD_FOLDER和FINAL_FOLDER中均未找到)，但仍添加到列表（可能是云端文件）"
                    )
                    effect_images.append(
                        {
                            "id": task.id,
                            "url": image_url,
                            "path": filename,
                            "created_at": task.completed_at or task.created_at,
                        }
                    )

    # 如果AITask中没有效果图，尝试从文件系统读取（与订单详情页面逻辑一致）
    if len(effect_images) == 0:
        try:
            hd_folder = app.config.get("HD_FOLDER", os.path.join(app.root_path, "hd_images"))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)

            if os.path.exists(hd_folder):
                # 查找该订单的所有效果图文件
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                effect_files = glob.glob(pattern)
                effect_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序

                for filepath in effect_files:
                    filename = os.path.basename(filepath)

                    # 构建图片URL（使用缩略图进行预览）
                    # 检查缩略图是否存在
                    thumbnail_filename = get_thumbnail_path(filename)
                    # 提取缩略图文件名（去掉路径）
                    if "/" in thumbnail_filename or "\\" in thumbnail_filename:
                        thumbnail_filename = os.path.basename(thumbnail_filename.replace("\\", "/"))

                    # 检查缩略图文件是否存在
                    thumbnail_exists = False
                    if os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                        thumbnail_exists = True

                    # 如果缩略图存在，使用缩略图；否则使用原图
                    if thumbnail_exists:
                        encoded_filename = quote(thumbnail_filename, safe="")
                        image_url = f"/public/hd/{encoded_filename}"
                        logger.info(f"✅ 文件系统读取 - 使用缩略图: {thumbnail_filename}")
                    else:
                        encoded_filename = quote(filename, safe="")
                        image_url = f"/public/hd/{encoded_filename}"
                        logger.warning(f"文件系统读取 - 缩略图不存在，使用原图: {filename}")

                    effect_images.append(
                        {
                            "id": 0,  # 文件系统读取的没有ID
                            "url": image_url,
                            "path": filename,
                            "created_at": datetime.fromtimestamp(os.path.getmtime(filepath)),
                        }
                    )

                logger.info(
                    f"选片详情 - 订单 {order.order_number}: 从文件系统读取到 {len(effect_images)} 张效果图"
                )
        except Exception as e:
            logger.info(f"选片详情 - 从文件系统读取效果图失败: {e}")
            import traceback

            traceback.print_exc()

    # 获取产品的免费选片张数和额外照片价格
    free_selection_count = 1  # 默认1张
    extra_photo_price = 10.0  # 默认10元/张
    if order.product_name:
        # 尝试从产品名称匹配产品
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        if product:
            if hasattr(product, "free_selection_count"):
                free_selection_count = product.free_selection_count or 1
            if hasattr(product, "extra_photo_price"):
                extra_photo_price = product.extra_photo_price or 10.0

    # 根据订单的product_name和size查找对应的套餐产品
    # 订单的product_name对应Product表，size对应ProductSize表
    package_product = None
    package_size = None
    package_effect_image_url = None

    logger.info(
        f"🔍 查找套餐产品: order.product_name='{order.product_name}', order.size='{order.size}'"
    )

    if order.product_name and order.size:
        # 首先从Product表查找匹配的产品（订单的product_name对应Product.name）
        package_product = Product.query.filter_by(name=order.product_name, is_active=True).first()

        if package_product:
            logger.info(f"✅ 找到产品: id={package_product.id}, name={package_product.name}")

            # 获取该产品的所有规格用于调试
            all_sizes_debug = ProductSize.query.filter_by(
                product_id=package_product.id, is_active=True
            ).all()
            logger.info(f"📋 该产品共有 {len(all_sizes_debug)} 个规格:")
            for s in all_sizes_debug:
                logger.info(
                    f"   - id={s.id}, size_name='{s.size_name}', effect_image_url='{s.effect_image_url or '(无)'}'"
                )

            # 根据订单的size查找匹配的ProductSize（订单的size对应ProductSize.size_name）
            # 首先尝试完全匹配（去除空格）
            order_size_trimmed = order.size.strip()
            package_size = ProductSize.query.filter_by(
                product_id=package_product.id, size_name=order_size_trimmed, is_active=True
            ).first()

            if package_size:
                logger.info(
                    f"✅ 完全匹配找到规格: id={package_size.id}, size_name='{package_size.size_name}'"
                )
            else:
                logger.warning("完全匹配未找到，尝试智能匹配...")
                # 智能匹配：提取基础尺寸（如从"证件照-2寸-蓝底"提取"证件照-2寸"）
                # 订单size可能包含额外信息（如"证件照-2寸-蓝底"），需要提取基础部分
                order_size_parts = order_size_trimmed.split("-")
                base_size_candidates = []
                # 生成可能的匹配模式：证件照-2寸, 证件照-2寸-蓝底, 证件照-2寸-蓝底-xxx
                for i in range(1, len(order_size_parts) + 1):
                    base_size_candidates.append("-".join(order_size_parts[:i]))

                logger.info(f"   尝试匹配模式: {base_size_candidates}")

                # 先尝试精确匹配（去除空格）
                for candidate in base_size_candidates:
                    for size in all_sizes_debug:
                        size_name_trimmed = size.size_name.strip()
                        if size_name_trimmed == candidate:
                            package_size = size
                            logger.info(
                                f"✅ 智能匹配找到规格: id={size.id}, size_name='{size.size_name}' (匹配模式: '{candidate}')"
                            )
                            break
                    if package_size:
                        break

                # 如果还是没找到，尝试包含匹配
                if not package_size:
                    for size in all_sizes_debug:
                        size_name_trimmed = size.size_name.strip()
                        # 检查订单size是否包含规格名称，或规格名称是否包含订单size的基础部分
                        if (size_name_trimmed in order_size_trimmed) or (
                            order_size_parts[0] in size_name_trimmed
                            and len(order_size_parts) > 1
                            and order_size_parts[1] in size_name_trimmed
                        ):
                            package_size = size
                            logger.info(
                                f"✅ 包含匹配找到规格: id={size.id}, size_name='{size.size_name}'"
                            )
                            break

            # 如果找到了规格，获取效果图
            if package_size:
                if package_size.effect_image_url:
                    package_effect_image_url = package_size.effect_image_url
                    logger.info(
                        f"✅ 找到套餐产品效果图: 产品={package_product.name}, 规格={package_size.size_name}, 效果图={package_effect_image_url}"
                    )
                else:
                    logger.warning(
                        f"找到规格但无效果图: 产品={package_product.name}, 规格={package_size.size_name}, effect_image_url为空"
                    )
            else:
                logger.error("未找到匹配的规格")
        else:
            logger.error(f"未找到产品: product_name='{order.product_name}'")
            # 列出所有产品用于调试
            all_products = Product.query.filter_by(is_active=True).all()
            logger.info(f"📋 当前所有激活的产品: {[p.name for p in all_products]}")
    else:
        logger.warning(f"订单缺少必要信息: product_name={order.product_name}, size={order.size}")

    # 获取设计图片（水印）- 从订单的风格主题获取
    design_image_url = None
    logger.info(f"🔍 查找设计图片: order.style_name='{order.style_name}'")

    if order.style_name:
        # 查找对应的风格主题
        StyleImage = models.get("StyleImage")
        if StyleImage:
            # 订单的style_name格式可能是"证件照/衬衫"，需要匹配StyleImage.name
            # 先尝试完全匹配
            style_image = StyleImage.query.filter_by(name=order.style_name, is_active=True).first()

            if not style_image:
                # 如果完全匹配失败，尝试只匹配风格名称部分（如"衬衫"）
                style_name_parts = order.style_name.split("/")
                if len(style_name_parts) > 1:
                    style_name_only = style_name_parts[-1].strip()  # 取最后一部分，如"衬衫"
                    logger.info(f"   尝试匹配风格名称: '{style_name_only}'")
                    style_image = StyleImage.query.filter_by(
                        name=style_name_only, is_active=True
                    ).first()
                    if not style_image:
                        # 尝试模糊匹配（包含）
                        all_styles = StyleImage.query.filter_by(is_active=True).all()
                        for s in all_styles:
                            if style_name_only in s.name or s.name in style_name_only:
                                style_image = s
                                logger.info(f"   模糊匹配找到: '{s.name}'")
                                break

            if style_image:
                logger.info(f"✅ 找到风格主题: id={style_image.id}, name={style_image.name}")
                # 使用design_image_url字段（如果已配置）
                if hasattr(style_image, "design_image_url"):
                    logger.info(
                        f"   - design_image_url字段存在: '{style_image.design_image_url or '(空)'}'"
                    )
                    if style_image.design_image_url:
                        design_image_url = style_image.design_image_url
                        logger.info(f"✅ 找到设计图片: {design_image_url}")
                    else:
                        logger.warning("design_image_url字段为空")
                else:
                    logger.warning("design_image_url字段不存在")
            else:
                logger.error(f"未找到风格主题: style_name='{order.style_name}'")
                # 列出所有风格主题用于调试
                all_styles = StyleImage.query.filter_by(is_active=True).all()
                logger.info(f"📋 当前所有激活的风格主题: {[s.name for s in all_styles]}")
        else:
            logger.error(
                f"StyleImage模型未找到，models.keys()={list(models.keys()) if models else 'None'}"
            )
    else:
        logger.warning("订单无style_name")

    # 样机套图：若套餐产品绑定了样机模板，则传递可用模板列表
    available_mockup_templates = []
    if package_product and models.get("MockupTemplate") and models.get("MockupTemplateProduct"):
        MockupTemplate = models["MockupTemplate"]
        MockupTemplateProduct = models["MockupTemplateProduct"]
        bindings = MockupTemplateProduct.query.filter_by(product_id=package_product.id).all()
        template_ids = [b.template_id for b in bindings]
        if template_ids:
            templates = (
                MockupTemplate.query.filter(
                    MockupTemplate.id.in_(template_ids), MockupTemplate.is_active == True
                )
                .order_by(MockupTemplate.sort_order.asc())
                .all()
            )
            available_mockup_templates = [
                {
                    "id": t.id,
                    "name": t.name,
                    "preview_image_url": t.preview_image_url,
                    "smart_layer_name": t.smart_layer_name or "photogo",
                }
                for t in templates
            ]

    return render_template(
        "admin/photo_selection_detail.html",
        order=order,
        effect_images=effect_images,
        free_selection_count=free_selection_count,
        extra_photo_price=extra_photo_price,
        package_product=package_product,
        package_size=package_size,
        package_effect_image_url=package_effect_image_url,
        design_image_url=design_image_url,
        available_mockup_templates=available_mockup_templates,
    )
