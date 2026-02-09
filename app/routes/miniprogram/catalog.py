# -*- coding: utf-8 -*-
"""
小程序目录相关路由（风格、产品、轮播图）
"""

import logging

logger = logging.getLogger(__name__)
import json

from flask import Blueprint, jsonify, request

from app.routes.miniprogram.common import get_helper_functions, get_models
from app.services.cache_service import CACHE_PREFIXES, cache_key, cached

# 创建目录相关的子蓝图
bp = Blueprint("catalog", __name__)


@bp.route("/styles", methods=["GET"])
def miniprogram_get_styles():
    """获取所有风格分类和图片，支持按产品过滤"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Product = models["Product"]
        StyleCategory = models["StyleCategory"]
        StyleSubcategory = models.get("StyleSubcategory")
        StyleImage = models["StyleImage"]
        ProductStyleCategory = models["ProductStyleCategory"]
        get_base_url = helpers["get_base_url"]
        db = models["db"]

        # 获取产品ID参数（可选）
        product_id = request.args.get("productId") or request.args.get("product_id")
        # refresh=1 时跳过缓存，确保与后台数据同步
        skip_cache = request.args.get("refresh") in ("1", "true", "yes")

        # 生成缓存键（包含产品ID参数）
        from app.services.cache_service import cache_key, get_cache, set_cache

        cache_key_str = cache_key(CACHE_PREFIXES["STYLE_CATEGORIES"], product_id=product_id)

        # 尝试从缓存获取（refresh 时跳过）
        cached_data = None if skip_cache else get_cache(cache_key_str)
        if cached_data is not None:
            logger.debug(f"缓存命中: 风格分类 (product_id={product_id})")
            return jsonify(cached_data)

        logger.debug(f"缓存未命中: 风格分类 (product_id={product_id})")

        # 如果指定了产品ID，只返回该产品绑定的风格分类
        if product_id:
            logger.info(f"🔍 请求风格分类，产品ID参数: {product_id}")
            # 通过产品code查找产品
            product = Product.query.filter_by(code=product_id, is_active=True).first()
            if not product:
                # 如果通过code找不到，尝试通过ID查找（兼容旧逻辑）
                try:
                    product_id_int = int(product_id)
                    product = Product.query.filter_by(id=product_id_int, is_active=True).first()
                    logger.warning(
                        "通过code未找到产品，尝试通过ID查找: {product_id_int}, 结果: {'找到' if product else '未找到'}"
                    )
                except (ValueError, TypeError):
                    pass

            if product:
                logger.info(f"✅ 找到产品: {product.name} (ID: {product.id}, Code: {product.code})")
                # 优化N+1查询：批量查询产品绑定的风格分类ID
                bindings = ProductStyleCategory.query.filter_by(product_id=product.id).all()
                bound_category_ids = [binding.style_category_id for binding in bindings]
                logger.info(f"📋 产品绑定的风格分类ID列表: {bound_category_ids}")

                if bound_category_ids:
                    # 只查询绑定的风格分类（已优化，使用IN查询）
                    categories = (
                        StyleCategory.query.filter(
                            StyleCategory.id.in_(bound_category_ids),
                            StyleCategory.is_active == True,
                        )
                        .order_by(StyleCategory.sort_order)
                        .all()
                    )
                    logger.info(f"✅ 产品 {product.name} 绑定的风格分类数量: {len(categories)}")
                    for cat in categories:
                        logger.info(f"   - {cat.name} (ID: {cat.id}, Code: {cat.code})")
                else:
                    # 产品没有绑定任何风格分类，返回空列表
                    categories = []
                    logger.warning(f"产品 {product.name} 没有绑定任何风格分类，返回空列表")
            else:
                # 产品不存在，返回空列表（不再返回所有分类，避免显示错误的分类）
                categories = []
                logger.error(f"产品ID {product_id} 不存在，返回空列表")
        else:
            # 没有指定产品ID，返回所有风格分类
            categories = (
                StyleCategory.query.filter_by(is_active=True)
                .order_by(StyleCategory.sort_order)
                .all()
            )

        # 优化N+1查询：批量查询所有风格图片、二级分类、风格分类绑定的产品
        category_ids = [cat.id for cat in categories]
        images_map = {}
        subcategories_map = {}
        bound_products_map = {}  # style_category_id -> [product_code, ...]

        if category_ids:
            # 批量查询所有风格分类绑定的产品（用于风格库直接进入时跳转产品详情）
            all_bindings = ProductStyleCategory.query.filter(
                ProductStyleCategory.style_category_id.in_(category_ids)
            ).all()
            product_ids = list({b.product_id for b in all_bindings})
            products_map = {}
            if product_ids:
                products = Product.query.filter(
                    Product.id.in_(product_ids), Product.is_active == True
                ).all()
                products_map = {p.id: p.code for p in products}
            for b in all_bindings:
                code = products_map.get(b.product_id)
                if code:
                    if b.style_category_id not in bound_products_map:
                        bound_products_map[b.style_category_id] = []
                    bound_products_map[b.style_category_id].append(code)

        if category_ids:
            # 批量查询所有风格图片
            all_images = (
                StyleImage.query.filter(
                    StyleImage.category_id.in_(category_ids), StyleImage.is_active == True
                )
                .order_by(StyleImage.sort_order)
                .all()
            )
            for img in all_images:
                if img.category_id not in images_map:
                    images_map[img.category_id] = []
                images_map[img.category_id].append(img)

            # 批量查询所有二级分类（is_active==True 或 NULL 均视为启用，兼容历史数据）
            if StyleSubcategory:
                all_subcategories = (
                    StyleSubcategory.query.filter(
                        StyleSubcategory.category_id.in_(category_ids),
                        (StyleSubcategory.is_active == True) | (StyleSubcategory.is_active.is_(None)),
                    )
                    .order_by(StyleSubcategory.sort_order)
                    .all()
                )
                for subcat in all_subcategories:
                    if subcat.category_id not in subcategories_map:
                        subcategories_map[subcat.category_id] = []
                    subcategories_map[subcat.category_id].append(subcat)

        result = []
        current_base_url = get_base_url()
        for category in categories:
            # 从批量查询的映射中获取二级分类（避免N+1查询）
            subcategories = subcategories_map.get(category.id, [])
            subcategories_data = []
            for subcategory in subcategories:
                subcategory_data = {
                    "id": subcategory.id,
                    "name": subcategory.name,
                    "code": subcategory.code,
                    "icon": subcategory.icon or "",
                    "cover_image": subcategory.cover_image or "",
                }
                # 处理二级分类封面图URL
                if subcategory_data["cover_image"]:
                    if not subcategory_data["cover_image"].startswith("http"):
                        subcategory_data["cover_image"] = (
                            f"{current_base_url}{subcategory_data['cover_image']}"
                        )
                    elif "192.168.2.54" in subcategory_data["cover_image"]:
                        subcategory_data["cover_image"] = subcategory_data["cover_image"].replace(
                            "http://192.168.2.54:8000", current_base_url
                        )
                    elif "photogooo" in subcategory_data["cover_image"]:
                        subcategory_data["cover_image"] = subcategory_data["cover_image"].replace(
                            "https://photogooo", current_base_url
                        )
                        subcategory_data["cover_image"] = subcategory_data["cover_image"].replace(
                            "http://photogooo", current_base_url
                        )
                subcategories_data.append(subcategory_data)

            # 从批量查询的映射中获取图片（避免N+1查询）
            images = images_map.get(category.id, [])

            # 确保封面图URL是完整的URL，并替换旧IP地址和旧域名
            cover_image = category.cover_image
            if cover_image:
                if not cover_image.startswith("http"):
                    # 相对路径，补全为完整URL
                    cover_image = f"{current_base_url}{cover_image}"
                elif "192.168.2.54" in cover_image:
                    # 如果URL包含旧的IP地址，替换为当前配置的IP
                    cover_image = cover_image.replace("http://192.168.2.54:8000", current_base_url)
                elif "photogooo" in cover_image:
                    # 如果URL包含旧的域名，替换为当前配置的地址
                    cover_image = cover_image.replace("https://photogooo", current_base_url)
                    cover_image = cover_image.replace("http://photogooo", current_base_url)

            # 该风格分类绑定的产品 code 列表（用于风格库直接进入时跳转产品详情页）
            bound_product_codes = bound_products_map.get(category.id, [])

            category_data = {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "description": category.description,
                "icon": category.icon,
                "cover_image": cover_image,
                "subcategories": subcategories_data,
                "images": [],
                "bound_product_codes": bound_product_codes,
            }

            subcat_name_map = {sub.id: sub.name for sub in subcategories}
            for image in images:
                # 确保图片URL是完整的URL，并替换旧IP地址和旧域名
                image_url = image.image_url
                if image_url:
                    if not image_url.startswith("http"):
                        # 相对路径，补全为完整URL
                        image_url = f"{current_base_url}{image_url}"
                    elif "192.168.2.54" in image_url:
                        # 如果URL包含旧的IP地址，替换为当前配置的IP
                        image_url = image_url.replace("http://192.168.2.54:8000", current_base_url)
                    elif "photogooo" in image_url:
                        # 如果URL包含旧的域名，替换为当前配置的地址
                        image_url = image_url.replace("https://photogooo", current_base_url)
                        image_url = image_url.replace("http://photogooo", current_base_url)

                subcat_id = image.subcategory_id if hasattr(image, "subcategory_id") else None
                image_data = {
                    "id": image.id,
                    "name": image.name,
                    "code": image.code,
                    "description": image.description,
                    "image_url": image_url,
                    "subcategory_id": subcat_id,
                    "subcategory_name": subcat_name_map.get(subcat_id, "") if subcat_id else "",
                }
                category_data["images"].append(image_data)

            result.append(category_data)

        response_data = {"status": "success", "data": result}

        # 存入缓存（1小时）
        set_cache(cache_key_str, response_data, timeout=3600)

        return jsonify(response_data)

    except Exception as e:
        logger.info(f"获取风格数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "获取风格数据失败"}), 500


@bp.route("/styles/refresh", methods=["GET"])
def miniprogram_refresh_styles():
    """强制刷新风格数据，清除缓存。支持 productId 参数清除指定产品的风格缓存"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        # 清除风格缓存（支持按 productId 清除指定产品，或清除全部）
        product_id = request.args.get("productId") or request.args.get("product_id")
        try:
            from app.services.cache_service import (
                CACHE_PREFIXES,
                cache_key,
                delete_cache,
                delete_cache_pattern,
            )

            if product_id:
                key = cache_key(CACHE_PREFIXES["STYLE_CATEGORIES"], product_id=product_id)
                delete_cache(key)
                logger.info(f"已清除产品 productId={product_id} 的风格缓存")
                # 若 productId 为数字，也清除 code 形式（产品可能用 code 请求）
                Product = models.get("Product")
                if Product:
                    try:
                        pid_int = int(product_id)
                        product = Product.query.get(pid_int)
                        if product and product.code:
                            key2 = cache_key(
                                CACHE_PREFIXES["STYLE_CATEGORIES"], product_id=product.code
                            )
                            delete_cache(key2)
                    except (ValueError, TypeError):
                        pass
            else:
                delete_cache_pattern("cache:style_categories*")
                logger.info("已清除所有风格缓存")
        except Exception as e:
            logger.warning(f"清除风格缓存失败: {e}")

        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        get_base_url = helpers["get_base_url"]
        from datetime import datetime

        # 强制重新查询数据库
        categories = (
            StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
        )

        # 优化N+1查询：批量查询所有风格图片
        category_ids = [cat.id for cat in categories]
        images_map = {}
        if category_ids:
            all_images = (
                StyleImage.query.filter(
                    StyleImage.category_id.in_(category_ids), StyleImage.is_active == True
                )
                .order_by(StyleImage.sort_order)
                .all()
            )
            for img in all_images:
                if img.category_id not in images_map:
                    images_map[img.category_id] = []
                images_map[img.category_id].append(img)

        result = []
        current_base_url = get_base_url()
        for category in categories:
            # 从批量查询的映射中获取图片（避免N+1查询）
            images = images_map.get(category.id, [])

            # 确保封面图URL是完整的URL，并替换旧IP地址和旧域名
            cover_image = category.cover_image
            if cover_image:
                if not cover_image.startswith("http"):
                    # 相对路径，补全为完整URL
                    cover_image = f"{current_base_url}{cover_image}"
                elif "192.168.2.54" in cover_image:
                    # 如果URL包含旧的IP地址，替换为当前配置的IP
                    cover_image = cover_image.replace("http://192.168.2.54:8000", current_base_url)
                elif "photogooo" in cover_image:
                    # 如果URL包含旧的域名，替换为当前配置的地址
                    cover_image = cover_image.replace("https://photogooo", current_base_url)
                    cover_image = cover_image.replace("http://photogooo", current_base_url)

            category_data = {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "description": category.description,
                "icon": category.icon,
                "cover_image": cover_image,
                "images": [],
                "last_updated": datetime.now().isoformat(),  # 添加时间戳
            }

            for image in images:
                # 确保图片URL是完整的URL，并替换旧IP地址和旧域名
                image_url = image.image_url
                if image_url:
                    if not image_url.startswith("http"):
                        # 相对路径，补全为完整URL
                        image_url = f"{current_base_url}{image_url}"
                    elif "192.168.2.54" in image_url:
                        # 如果URL包含旧的IP地址，替换为当前配置的IP
                        image_url = image_url.replace("http://192.168.2.54:8000", current_base_url)
                    elif "photogooo" in image_url:
                        # 如果URL包含旧的域名，替换为当前配置的地址
                        image_url = image_url.replace("https://photogooo", current_base_url)
                        image_url = image_url.replace("http://photogooo", current_base_url)

                image_data = {
                    "id": image.id,
                    "name": image.name,
                    "code": image.code,
                    "description": image.description,
                    "image_url": image_url,
                }
                category_data["images"].append(image_data)

            result.append(category_data)

        return (
            jsonify(
                {"status": "success", "data": result, "refresh_time": datetime.now().isoformat()}
            ),
            200,
            {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except Exception as e:
        logger.info(f"刷新风格数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "刷新风格数据失败"}), 500


@bp.route("/product-categories", methods=["GET"])
def miniprogram_get_product_categories():
    """获取产品分类（一级和二级分类）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        ProductCategory = models.get("ProductCategory")
        ProductSubcategory = models.get("ProductSubcategory")
        get_base_url = helpers["get_base_url"]

        if not ProductCategory or not ProductSubcategory:
            return jsonify({"status": "success", "data": []})

        # 获取所有一级分类
        categories = (
            ProductCategory.query.filter(ProductCategory.is_active == True)
            .order_by(ProductCategory.sort_order.asc())
            .all()
        )

        result = []
        for category in categories:
            # 获取该分类下的二级分类（is_active==True 或 NULL 均视为启用，兼容历史数据）
            subcategories = (
                ProductSubcategory.query.filter(
                    ProductSubcategory.category_id == category.id,
                    (ProductSubcategory.is_active == True) | (ProductSubcategory.is_active.is_(None)),
                )
                .order_by(ProductSubcategory.sort_order.asc())
                .all()
            )

            # 处理分类图片URL
            image_url = category.image_url
            if image_url:
                # 如果是相对路径，转换为完整URL
                if not image_url.startswith("http"):
                    image_url = f"{get_base_url()}{image_url}"
                # 对URL进行编码，确保特殊字符（包括空格）正确处理
                from urllib.parse import quote, urlparse, urlunparse

                parsed = urlparse(image_url)
                # 对路径部分进行编码，确保空格等特殊字符被正确编码
                # 使用quote的默认safe参数，只保留/不编码
                path_parts = parsed.path.split("/")
                encoded_parts = [quote(part, safe="") for part in path_parts]
                encoded_path = "/".join(encoded_parts)
                image_url = urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        encoded_path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment,
                    )
                )
            else:
                # 如果没有图片，设置为空字符串
                image_url = ""

            category_data = {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "icon": category.icon,
                "image_url": image_url,
                "sort_order": category.sort_order,
                "style_redirect_page": category.style_redirect_page or "",
                "subcategories": [],
            }

            # 添加二级分类
            for subcategory in subcategories:
                sub_image_url = subcategory.image_url
                if sub_image_url and not sub_image_url.startswith("http"):
                    sub_image_url = f"{get_base_url()}{sub_image_url}"

                category_data["subcategories"].append(
                    {
                        "id": subcategory.id,
                        "name": subcategory.name,
                        "code": subcategory.code,
                        "icon": subcategory.icon,
                        "image_url": sub_image_url,
                        "sort_order": subcategory.sort_order,
                    }
                )

            result.append(category_data)

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        logger.info(f"获取产品分类失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "获取产品分类失败"}), 500


@bp.route("/products", methods=["GET"])
def miniprogram_get_products():
    """获取所有产品配置"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        Product = models["Product"]
        ProductSize = models["ProductSize"]
        ProductImage = models["ProductImage"]
        ProductStyleCategory = models["ProductStyleCategory"]
        ProductCustomField = models["ProductCustomField"]
        ProductSizePetOption = models["ProductSizePetOption"]
        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]
        ProductCategory = models.get("ProductCategory")
        ProductSubcategory = models.get("ProductSubcategory")
        get_base_url = helpers["get_base_url"]

        # 获取分类参数（可选）
        category_id = request.args.get("categoryId") or request.args.get("category_id")
        subcategory_id = request.args.get("subcategoryId") or request.args.get("subcategory_id")
        # refresh=1 时跳过缓存，确保与后台数据同步
        skip_cache = request.args.get("refresh") in ("1", "true", "yes")

        # 生成缓存键（包含参数）
        from app.services.cache_service import cache_key, get_cache, set_cache

        cache_key_str = cache_key(
            CACHE_PREFIXES["PRODUCTS"], category_id=category_id, subcategory_id=subcategory_id
        )

        # 尝试从缓存获取（refresh 时跳过）
        cached_data = None if skip_cache else get_cache(cache_key_str)
        if cached_data is not None:
            logger.debug(
                f"缓存命中: 产品列表 (category_id={category_id}, subcategory_id={subcategory_id})"
            )
            return jsonify(cached_data)

        logger.debug(
            f"缓存未命中: 产品列表 (category_id={category_id}, subcategory_id={subcategory_id})"
        )

        # 查询产品
        query = Product.query.filter_by(is_active=True)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if subcategory_id:
            query = query.filter_by(subcategory_id=subcategory_id)

        products = query.order_by(Product.sort_order.asc(), Product.id.asc()).all()

        # 优化N+1查询：批量加载所有产品的关联数据
        product_ids = [product.id for product in products]

        # 批量查询所有产品的尺寸
        sizes_map = {}
        if product_ids:
            all_sizes = (
                ProductSize.query.filter(
                    ProductSize.product_id.in_(product_ids), ProductSize.is_active == True
                )
                .order_by(ProductSize.sort_order.asc())
                .all()
            )
            for size in all_sizes:
                if size.product_id not in sizes_map:
                    sizes_map[size.product_id] = []
                sizes_map[size.product_id].append(size)

        # 批量查询所有产品的图片
        images_map = {}
        if product_ids:
            all_images = (
                ProductImage.query.filter(
                    ProductImage.product_id.in_(product_ids), ProductImage.is_active == True
                )
                .order_by(ProductImage.sort_order.asc())
                .all()
            )
            for img in all_images:
                if img.product_id not in images_map:
                    images_map[img.product_id] = []
                images_map[img.product_id].append(img)

        # 批量查询所有产品的风格分类绑定
        style_bindings_map = {}
        if product_ids:
            all_bindings = ProductStyleCategory.query.filter(
                ProductStyleCategory.product_id.in_(product_ids)
            ).all()
            for binding in all_bindings:
                if binding.product_id not in style_bindings_map:
                    style_bindings_map[binding.product_id] = []
                style_bindings_map[binding.product_id].append(binding)

        # 优化：批量查询所有需要的风格分类和风格图片（避免在循环中重复查询）
        all_style_category_ids = set()
        for bindings in style_bindings_map.values():
            for binding in bindings:
                all_style_category_ids.add(binding.style_category_id)

        # 批量查询所有风格分类
        style_categories_map = {}
        if all_style_category_ids:
            all_style_categories = StyleCategory.query.filter(
                StyleCategory.id.in_(list(all_style_category_ids))
            ).all()
            for cat in all_style_categories:
                style_categories_map[cat.id] = cat

        # 批量查询所有风格图片
        style_images_map = {}
        if all_style_category_ids:
            all_style_images = StyleImage.query.filter(
                StyleImage.category_id.in_(list(all_style_category_ids)),
                StyleImage.is_active == True,
            ).all()
            for img in all_style_images:
                if img.category_id not in style_images_map:
                    style_images_map[img.category_id] = []
                style_images_map[img.category_id].append(img)

        # 批量查询所有产品的自定义字段
        custom_fields_map = {}
        if product_ids:
            all_custom_fields = ProductCustomField.query.filter(
                ProductCustomField.product_id.in_(product_ids)
            ).all()
            for field in all_custom_fields:
                if field.product_id not in custom_fields_map:
                    custom_fields_map[field.product_id] = []
                custom_fields_map[field.product_id].append(field)

        # 优化N+1查询：批量查询所有尺寸的宠物选项
        size_ids = [size.id for sizes in sizes_map.values() for size in sizes]
        pet_options_map = {}
        if size_ids:
            all_pet_options = (
                ProductSizePetOption.query.filter(ProductSizePetOption.size_id.in_(size_ids))
                .order_by(ProductSizePetOption.sort_order.asc())
                .all()
            )
            for opt in all_pet_options:
                if opt.size_id not in pet_options_map:
                    pet_options_map[opt.size_id] = []
                pet_options_map[opt.size_id].append(opt)

        # 优化N+1查询：批量查询所有产品的分类信息
        category_ids = set()
        subcategory_ids = set()
        for product in products:
            if hasattr(product, "category_id") and product.category_id:
                category_ids.add(product.category_id)
            if hasattr(product, "subcategory_id") and product.subcategory_id:
                subcategory_ids.add(product.subcategory_id)

        categories_map = {}
        if category_ids and ProductCategory:
            all_categories = ProductCategory.query.filter(
                ProductCategory.id.in_(list(category_ids))
            ).all()
            for cat in all_categories:
                categories_map[cat.id] = cat

        subcategories_map = {}
        if subcategory_ids and ProductSubcategory:
            all_subcategories = ProductSubcategory.query.filter(
                ProductSubcategory.id.in_(list(subcategory_ids))
            ).all()
            for subcat in all_subcategories:
                subcategories_map[subcat.id] = subcat

        result = []
        for product in products:
            # 从批量查询的映射中获取尺寸（避免N+1查询）
            sizes = sizes_map.get(product.id, [])

            logger.info(f"产品: {product.name}, 尺寸数量: {len(sizes)}")

            # 处理图片URL
            image_url = product.image_url
            if image_url and not image_url.startswith("http"):
                # 如果是相对路径，转换为完整URL
                image_url = f"{get_base_url()}{image_url}"
            elif not image_url:
                # 如果没有图片，使用临时图片
                image_url = f"https://picsum.photos/300/400?random={product.id}"

            # 从批量查询的映射中获取产品的多张图片（避免N+1查询）
            product_images = images_map.get(product.id, [])
            images = []

            # 如果有ProductImage记录，使用多图
            if product_images:
                for img in product_images:
                    img_url = img.image_url
                    if img_url and not img_url.startswith("http"):
                        img_url = f"{get_base_url()}{img_url}"
                    images.append(img_url)
            else:
                # 如果没有多图记录，使用主图片
                images = (
                    [image_url]
                    if image_url
                    else [f"https://picsum.photos/300/400?random={product.id}"]
                )

            logger.info(f"图片URL: {image_url}, 多图数量: {len(images)}")

            # 从批量查询的映射中获取产品绑定的风格分类（避免N+1查询）
            product_style_bindings = style_bindings_map.get(product.id, [])
            bound_style_category_ids = [
                binding.style_category_id for binding in product_style_bindings
            ]

            # 从批量查询的映射中获取风格分类的code列表（避免在循环中查询）
            bound_style_category_codes = []
            for cat_id in bound_style_category_ids:
                cat = style_categories_map.get(cat_id)
                if cat:
                    bound_style_category_codes.append(cat.code)

            # 从批量查询的映射中获取产品绑定的所有风格图片code（避免在循环中查询）
            bound_style_codes = []
            for cat_id in bound_style_category_ids:
                style_images = style_images_map.get(cat_id, [])
                bound_style_codes.extend([img.code for img in style_images])

            logger.info(f"产品 {product.name} 绑定的风格分类ID: {bound_style_category_ids}")
            logger.info(f"产品 {product.name} 绑定的风格分类code: {bound_style_category_codes}")
            logger.info(f"产品 {product.name} 绑定的风格图片code: {bound_style_codes}")

            # 从批量查询的映射中获取产品的自定义字段（避免N+1查询）
            custom_fields = custom_fields_map.get(product.id, [])
            custom_fields_data = []
            color_options = []  # 颜色选项列表

            for field in custom_fields:
                field_data = {
                    "field_name": field.field_name,
                    "field_type": field.field_type,
                    "field_options": field.field_options,
                    "is_required": field.is_required,
                }
                custom_fields_data.append(field_data)

                # 如果是颜色/背景色字段，解析选项
                # 支持多种字段名称：背景色、颜色、背景颜色、background_color、color等
                # 也支持字段名称包含"色"或"color"的字段
                field_name_lower = field.field_name.lower() if field.field_name else ""
                is_color_field = (
                    field.field_name
                    in ["背景色", "颜色", "背景颜色", "background_color", "color", "背景", "底色"]
                    or "色" in field.field_name
                    or "color" in field_name_lower
                    or "background" in field_name_lower
                )

                if is_color_field and field.field_type == "select":
                    if field.field_options:
                        try:
                            # 尝试解析为JSON数组（新格式：支持选项图片）
                            options_data = json.loads(field.field_options)
                            if isinstance(options_data, list):
                                # 新格式：每个选项是对象，包含name和image_url
                                color_options = []
                                for opt in options_data:
                                    if isinstance(opt, dict):
                                        color_options.append(
                                            {
                                                "name": opt.get("name", ""),
                                                "image_url": opt.get("image_url", ""),
                                            }
                                        )
                                    else:
                                        # 兼容：如果是字符串，转换为对象
                                        color_options.append({"name": str(opt), "image_url": ""})
                            else:
                                # 如果不是列表，按逗号分隔（旧格式）
                                color_options = [
                                    {"name": opt.strip(), "image_url": ""}
                                    for opt in field.field_options.split(",")
                                    if opt.strip()
                                ]
                        except Exception:
                            # 如果不是JSON，按逗号分隔（旧格式）
                            color_options = [
                                {"name": opt.strip(), "image_url": ""}
                                for opt in field.field_options.split(",")
                                if opt.strip()
                            ]

            # 从批量查询的映射中获取产品分类信息（避免N+1查询）
            category_info = None
            subcategory_info = None
            if hasattr(product, "category_id") and product.category_id:
                category = categories_map.get(product.category_id)
                if category:
                    category_info = {
                        "id": category.id,
                        "name": category.name,
                        "code": category.code,
                        "icon": category.icon,
                    }
            if hasattr(product, "subcategory_id") and product.subcategory_id:
                subcategory = subcategories_map.get(product.subcategory_id)
                if subcategory:
                    subcategory_info = {
                        "id": subcategory.id,
                        "name": subcategory.name,
                        "code": subcategory.code,
                        "icon": subcategory.icon,
                    }

            product_data = {
                "id": product.id,  # 数字ID（迁移后保持与数据库一致）
                "code": product.code,
                "name": product.name,
                "description": product.description,
                "image": image_url,  # 保持向后兼容的主图片
                "images": images,  # 新增多图数组
                "sizes": [],
                "sort_order": product.sort_order or 0,  # 添加排序字段
                # 添加产品分类信息
                "category": category_info,
                "subcategory": subcategory_info,
                "category_id": product.category_id if hasattr(product, "category_id") else None,
                "subcategory_id": (
                    product.subcategory_id if hasattr(product, "subcategory_id") else None
                ),
                # 添加产品-风格绑定信息
                "allowed_styles": bound_style_codes,  # 绑定的风格图片code列表
                "style_category_codes": bound_style_category_codes,  # 绑定的风格分类code列表
                "style_category_ids": bound_style_category_ids,  # 绑定的风格分类ID列表（备用）
                # 添加自定义字段数据
                "custom_fields": custom_fields_data,  # 所有自定义字段
                "color_options": color_options,  # 颜色选项（便捷字段）
            }

            for size in sizes:
                logger.info(f"  尺寸: {size.size_name}, 价格: {size.price}")

                # 从批量查询的映射中获取尺寸的多宠配置（避免N+1查询）
                pet_options = pet_options_map.get(size.id, [])
                allow_multiple_pets = len(pet_options) > 1  # 如果有多个宠物选项，说明支持多宠

                logger.info(
                    f"    尺寸 {size.size_name} 的宠物选项数量: {len(pet_options)}, 支持多宠: {allow_multiple_pets}"
                )

                # 处理效果图URL
                effect_image_url = size.effect_image_url
                if effect_image_url and not effect_image_url.startswith("http"):
                    effect_image_url = f"{get_base_url()}{effect_image_url}"

                size_data = {
                    "id": size.id,
                    "size_name": size.size_name,  # 添加size_name字段以兼容前端
                    "name": size.size_name,
                    "price": float(size.price),
                    "effect_image_url": (
                        effect_image_url if effect_image_url else None
                    ),  # 添加效果图URL
                    # 添加多宠配置
                    "allow_multiple_pets": allow_multiple_pets,
                    "pet_options": (
                        [
                            {"id": opt.id, "name": opt.pet_count_name, "price": float(opt.price)}
                            for opt in pet_options
                        ]
                        if pet_options
                        else []
                    ),
                }
                product_data["sizes"].append(size_data)

            result.append(product_data)

        response_data = {"status": "success", "data": result}

        # 存入缓存（30分钟）
        set_cache(cache_key_str, response_data, timeout=1800)

        return jsonify(response_data)

    except Exception as e:
        logger.info(f"获取产品数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "获取产品数据失败"}), 500


@bp.route("/banners", methods=["GET"])
def miniprogram_get_banners():
    """获取首页轮播图（小程序前端使用，支持缓存）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        # 生成缓存键
        from app.services.cache_service import cache_key, get_cache, set_cache

        cache_key_str = cache_key("homepage_banners")

        # 尝试从缓存获取
        cached_data = get_cache(cache_key_str)
        if cached_data is not None:
            logger.debug("缓存命中: 首页轮播图")
            return jsonify(cached_data)

        logger.debug("缓存未命中: 首页轮播图")

        HomepageBanner = models["HomepageBanner"]
        get_base_url = helpers["get_base_url"]

        banners = (
            HomepageBanner.query.filter_by(is_active=True).order_by(HomepageBanner.sort_order).all()
        )

        result = []
        for banner in banners:
            # 确保图片URL是完整的URL
            image_url = banner.image_url
            if image_url and not image_url.startswith("http"):
                image_url = f"{get_base_url()}{image_url}"

            # 尝试获取新字段，如果不存在则使用默认值
            try:
                promotion_params = None
                if hasattr(banner, "promotion_params") and banner.promotion_params:
                    try:
                        promotion_params = json.loads(banner.promotion_params)
                    except (json.JSONDecodeError, TypeError):
                        promotion_params = None

                banner_type = getattr(banner, "type", "link")
            except AttributeError:
                promotion_params = None
                banner_type = "link"

            result.append(
                {
                    "id": banner.id,
                    "title": banner.title,
                    "subtitle": banner.subtitle,
                    "image_url": image_url,
                    "link": banner.link,
                    "type": banner_type,
                    "promotion_params": promotion_params,
                    "sort_order": banner.sort_order,
                }
            )

        response_data = {"status": "success", "data": result}

        # 存入缓存（1小时）
        set_cache(cache_key_str, response_data, timeout=3600)

        return jsonify(response_data)

    except Exception as e:
        logger.info(f"获取轮播图失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "获取轮播图失败"}), 500


@bp.route("/homepage-config", methods=["GET"])
def miniprogram_get_homepage_config():
    """获取首页完整配置（分类导航、产品推荐模块，支持缓存）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({"status": "error", "message": "系统未初始化"}), 500

        # 生成缓存键
        from app.services.cache_service import cache_key, get_cache, set_cache

        cache_key_str = cache_key("homepage_config")

        # 尝试从缓存获取
        cached_data = get_cache(cache_key_str)
        if cached_data is not None:
            logger.debug("缓存命中: 首页配置")
            return jsonify(cached_data)

        logger.debug("缓存未命中: 首页配置")

        HomepageCategoryNav = models.get("HomepageCategoryNav")
        HomepageProductSection = models.get("HomepageProductSection")
        Product = models.get("Product")
        ProductImage = models.get("ProductImage")
        get_base_url = helpers["get_base_url"]

        result = {
            "category_navs": [],
            "product_sections": [],
            "featured_section": {"show": False},
            "time_journey_section": {"show": False},
            "ip_collab_section": {"show": False},
            "works_section": {"show": False},
            "activity_banner": {"show": False},
        }

        # 获取分类导航
        if HomepageCategoryNav:
            navs = (
                HomepageCategoryNav.query.filter_by(is_active=True)
                .order_by(HomepageCategoryNav.sort_order)
                .all()
            )
            for nav in navs:
                image_url = nav.image_url or ""
                # 统一旧路径为标准路径：/images/category_nav/、/images/category-nav/ -> /media/category_nav/
                if image_url:
                    for old_prefix in ("/images/category_nav/", "/images/category-nav/", "/static/images/category_nav/"):
                        if image_url.startswith(old_prefix):
                            filename = image_url[len(old_prefix):].lstrip("/")
                            image_url = f"/media/category_nav/{filename}"
                            break
                # 相对路径转换为完整URL
                if image_url and not image_url.startswith("http"):
                    image_url = f"{get_base_url()}{image_url}"

                result["category_navs"].append(
                    {
                        "id": nav.id,
                        "name": nav.name,
                        "icon": nav.icon,
                        "image_url": image_url,
                        "link_type": nav.link_type,
                        "link_value": nav.link_value,
                        "category_id": nav.category_id,
                    }
                )

        # 获取产品推荐模块（包括所有类型的模块）
        # 注意：固定模块（featured_section, time_journey, ip_collab, works）每个类型只取一个
        if HomepageProductSection and Product:
            # 先获取所有激活的模块
            all_sections = (
                HomepageProductSection.query.filter_by(is_active=True)
                .order_by(HomepageProductSection.sort_order)
                .all()
            )

            # 固定模块类型，每个类型只取第一个
            fixed_module_types = ["featured_section", "time_journey", "ip_collab", "works"]
            fixed_sections = {}
            sections = []

            for section in all_sections:
                if section.section_type in fixed_module_types:
                    # 固定模块，每个类型只保留一个
                    if section.section_type not in fixed_sections:
                        fixed_sections[section.section_type] = section
                        sections.append(section)
                else:
                    # 其他类型模块，全部保留
                    sections.append(section)

            for section in sections:
                # 解析配置数据
                section_config = {}
                if section.config:
                    try:
                        section_config = json.loads(section.config)
                    except Exception:
                        pass

                # 根据模块类型处理数据
                if section.section_type in ["featured", "hot", "seasonal", "custom"]:
                    # 标准产品推荐模块
                    # 解析产品ID列表
                    product_ids = []
                    if section.product_ids:
                        try:
                            product_ids = json.loads(section.product_ids)
                        except Exception:
                            try:
                                product_ids = [
                                    int(x) for x in section.product_ids.split(",") if x.strip()
                                ]
                            except Exception:
                                product_ids = []

                    # 获取产品数据
                    products = []
                    if product_ids:
                        products_query = Product.query.filter(
                            Product.id.in_(product_ids), Product.is_active == True
                        )
                        products_list = products_query.all()
                        products_dict = {p.id: p for p in products_list}
                        products = [
                            products_dict[pid] for pid in product_ids if pid in products_dict
                        ]
                    elif section.category_id:
                        products = (
                            Product.query.filter_by(category_id=section.category_id, is_active=True)
                            .order_by(Product.sort_order)
                            .limit(section.limit)
                            .all()
                        )
                    else:
                        products = (
                            Product.query.filter_by(is_active=True)
                            .order_by(Product.sort_order)
                            .limit(section.limit)
                            .all()
                        )

                    # 优化N+1查询：批量查询所有产品的图片
                    product_ids_for_images = [p.id for p in products]
                    product_images_map = {}
                    if product_ids_for_images and ProductImage:
                        all_product_images = (
                            ProductImage.query.filter(
                                ProductImage.product_id.in_(product_ids_for_images)
                            )
                            .order_by(ProductImage.sort_order.asc())
                            .all()
                        )
                        for img in all_product_images:
                            if img.product_id not in product_images_map:
                                product_images_map[img.product_id] = []
                            product_images_map[img.product_id].append(img)

                    # 处理产品数据
                    products_data = []
                    for product in products:
                        product_image_url = None
                        if ProductImage:
                            # 从批量查询的映射中获取产品图片（避免N+1查询）
                            product_images = product_images_map.get(product.id, [])
                            if product_images:
                                product_image = product_images[0]  # 取第一张图片
                                product_image_url = product_image.image_url
                                if product_image_url and not product_image_url.startswith("http"):
                                    product_image_url = f"{get_base_url()}{product_image_url}"

                        if not product_image_url and hasattr(product, "images") and product.images:
                            try:
                                images = (
                                    json.loads(product.images)
                                    if isinstance(product.images, str)
                                    else product.images
                                )
                                if images and len(images) > 0:
                                    product_image_url = images[0]
                                    if product_image_url and not product_image_url.startswith(
                                        "http"
                                    ):
                                        product_image_url = f"{get_base_url()}{product_image_url}"
                            except Exception:
                                pass

                        products_data.append(
                            {
                                "id": product.id,
                                "name": product.name,
                                "code": product.code,
                                "image_url": product_image_url,
                                "price": (
                                    float(product.price)
                                    if hasattr(product, "price") and product.price
                                    else 0
                                ),
                            }
                        )

                    result["product_sections"].append(
                        {
                            "id": section.id,
                            "section_type": section.section_type,
                            "title": section.title,
                            "subtitle": section.subtitle,
                            "show_more_button": section.show_more_button,
                            "more_link": section.more_link,
                            "layout_type": section.layout_type,
                            "products": products_data,
                        }
                    )
                elif section.section_type == "featured_section":
                    # 当季主推模块（特殊格式）
                    items = section_config.get("items", [])
                    processed_items = []
                    for item in items:
                        if item.get("image_url") and not item["image_url"].startswith("http"):
                            item["image_url"] = f"{get_base_url()}{item['image_url']}"
                        # 确保包含跳转链接字段
                        if "link_type" not in item:
                            item["link_type"] = item.get("type", "none")
                        if "link_value" not in item:
                            item["link_value"] = item.get("link", item.get("value", ""))
                        processed_items.append(item)

                    result["featured_section"] = {
                        "show": True,
                        "title": "当季主推",  # 固定标题，由前端决定
                        "show_subscribe": section_config.get("show_subscribe", True),
                        "items": processed_items,
                    }
                elif section.section_type == "time_journey":
                    # 时光旅程模块
                    categories = section_config.get("categories", [])
                    processed_categories = []
                    for cat in categories:
                        if cat.get("main_image") and not cat["main_image"].startswith("http"):
                            cat["main_image"] = f"{get_base_url()}{cat['main_image']}"
                        # 确保包含跳转链接字段
                        if "link_type" not in cat:
                            cat["link_type"] = cat.get("type", "none")
                        if "link_value" not in cat:
                            cat["link_value"] = cat.get("link", cat.get("value", ""))
                        processed_categories.append(cat)

                    result["time_journey_section"] = {
                        "show": True,
                        "title": "时光旅程",  # 固定标题，由前端决定
                        "categories": processed_categories,
                    }
                elif section.section_type == "ip_collab":
                    # IP联名模块
                    tabs = section_config.get("tabs", [])
                    processed_tabs = []
                    Product = models.get("Product")
                    ProductImage = models.get("ProductImage")
                    ProductCategory = models.get("ProductCategory")
                    ProductSubcategory = models.get("ProductSubcategory")
                    StyleCategory = models.get("StyleCategory")
                    StyleImage = models.get("StyleImage")

                    for tab in tabs:
                        if tab.get("logo") and not tab["logo"].startswith("http"):
                            tab["logo"] = f"{get_base_url()}{tab['logo']}"
                        # 分类目录：按 category_id 或 style_category_id 拉取该分类下全部图片
                        if tab.get("category_id") and not tab.get("product_id") and not tab.get("style_image_id"):
                            # 产品分类目录：获取该分类下所有产品的图片
                            images = []
                            if Product and ProductImage:
                                cat_id = tab["category_id"]
                                subcat_id = tab.get("subcategory_id")
                                q = Product.query.filter_by(is_active=True, category_id=cat_id)
                                if subcat_id:
                                    q = q.filter_by(subcategory_id=subcat_id)
                                products = q.order_by(Product.sort_order).all()
                                for p in products:
                                    pi = (
                                        ProductImage.query.filter_by(
                                            product_id=p.id, is_active=True
                                        )
                                        .order_by(ProductImage.sort_order)
                                        .first()
                                    )
                                    url = pi.image_url if pi else (p.image_url or "")
                                    if url and not url.startswith("http"):
                                        url = f"{get_base_url()}{url}"
                                    if url:
                                        images.append(url)
                                if not images and products:
                                    for p in products:
                                        if p.image_url:
                                            url = p.image_url
                                            if not url.startswith("http"):
                                                url = f"{get_base_url()}{url}"
                                            images.append(url)
                            tab["images"] = images
                        elif tab.get("style_category_id") and not tab.get("style_image_id"):
                            # 风格分类目录：获取该分类下所有风格图片
                            images = []
                            if StyleImage:
                                sc_id = tab["style_category_id"]
                                subcat_id = tab.get("style_subcategory_id")
                                q = StyleImage.query.filter_by(
                                    category_id=sc_id, is_active=True
                                )
                                if subcat_id:
                                    q = q.filter_by(subcategory_id=subcat_id)
                                style_imgs = q.order_by(StyleImage.sort_order).all()
                                for si in style_imgs:
                                    url = si.image_url or ""
                                    if url and not url.startswith("http"):
                                        url = f"{get_base_url()}{url}"
                                    if url:
                                        images.append(url)
                                tab["images"] = images
                        elif tab.get("images"):
                            if isinstance(tab["images"], list):
                                processed_images = []
                                for img in tab["images"]:
                                    if isinstance(img, str):
                                        if not img.startswith("http"):
                                            img = f"{get_base_url()}{img}"
                                        processed_images.append(img)
                                    elif isinstance(img, dict) and img.get("url"):
                                        img_url = img["url"]
                                        if not img_url.startswith("http"):
                                            img_url = f"{get_base_url()}{img_url}"
                                        processed_images.append(img_url)
                                tab["images"] = processed_images
                            else:
                                img = tab["images"]
                                if isinstance(img, str):
                                    if not img.startswith("http"):
                                        img = f"{get_base_url()}{img}"
                                    tab["images"] = [img]
                                else:
                                    tab["images"] = []
                        else:
                            if tab.get("image_url"):
                                img_url = tab["image_url"]
                                if not img_url.startswith("http"):
                                    img_url = f"{get_base_url()}{img_url}"
                                tab["images"] = [img_url]
                            else:
                                tab["images"] = []
                        if "link_type" not in tab:
                            tab["link_type"] = tab.get("type", "none")
                        if "link_value" not in tab:
                            tab["link_value"] = tab.get("link", tab.get("value", ""))
                        processed_tabs.append(tab)

                    result["ip_collab_section"] = {
                        "show": True,
                        "title": "IP联名",  # 固定标题，由前端决定
                        "active_tab": section_config.get("active_tab"),
                        "tabs": processed_tabs,
                    }
                elif section.section_type == "works":
                    # 用户故事/作品展示模块
                    tabs = section_config.get("tabs", [])
                    processed_tabs = []
                    for tab in tabs:
                        if tab.get("main_image") and not tab["main_image"].startswith("http"):
                            tab["main_image"] = f"{get_base_url()}{tab['main_image']}"
                        if tab.get("images"):
                            for img in tab["images"]:
                                if isinstance(img, dict):
                                    if img.get("url") and not img["url"].startswith("http"):
                                        img["url"] = f"{get_base_url()}{img['url']}"
                                    # 为图片对象添加跳转链接字段
                                    if "link_type" not in img:
                                        img["link_type"] = img.get("type", "none")
                                    if "link_value" not in img:
                                        img["link_value"] = img.get("link", img.get("value", ""))
                                elif isinstance(img, str) and not img.startswith("http"):
                                    img = f"{get_base_url()}{img}"
                        # 确保tab包含跳转链接字段
                        if "link_type" not in tab:
                            tab["link_type"] = tab.get("type", "none")
                        if "link_value" not in tab:
                            tab["link_value"] = tab.get("link", tab.get("value", ""))
                        processed_tabs.append(tab)

                    result["works_section"] = {
                        "show": True,
                        "title": "作品展示",  # 固定标题，由前端决定
                        "active_tab": section_config.get("active_tab"),
                        "tabs": processed_tabs,
                    }

        # 获取活动横幅
        HomepageActivityBanner = models.get("HomepageActivityBanner")
        if HomepageActivityBanner:
            banner = (
                HomepageActivityBanner.query.filter_by(is_active=True)
                .order_by(HomepageActivityBanner.sort_order)
                .first()
            )
            if banner:
                result["activity_banner"] = {"show": True, "text": banner.text}

        response_data = {"status": "success", "data": result}

        # 存入缓存（1小时）
        set_cache(cache_key_str, response_data, timeout=3600)

        return jsonify(response_data)

    except Exception as e:
        logger.info(f"获取首页配置失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "获取首页配置失败"}), 500
