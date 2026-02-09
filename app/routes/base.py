# -*- coding: utf-8 -*-
"""
基础路由（首页、作品展示等）
"""

import logging

logger = logging.getLogger(__name__)
import sys

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

# 创建蓝图
base_bp = Blueprint("base", __name__)


@base_bp.route("/")
def index():
    """首页 - 重定向到管理后台登录页面"""
    # 暂时隐藏首页，直接跳转到登录页面
    # 如果需要恢复首页，可以取消下面的注释，并注释掉重定向
    return redirect(url_for("auth.login"))

    # 原首页代码（已隐藏，需要时可恢复）
    # try:
    #     if 'test_server' not in sys.modules:
    #         return render_template('index.html', style_data={}, product_data=[])
    #
    #     test_server_module = sys.modules['test_server']
    #     StyleCategory = test_server_module.StyleCategory
    #     StyleImage = test_server_module.StyleImage
    #     Product = test_server_module.Product
    #     ProductSize = test_server_module.ProductSize
    #     ProductImage = test_server_module.ProductImage
    #
    #     # 获取所有启用的风格分类
    #     categories = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
    #
    #     # 获取所有启用的风格图片
    #     images = StyleImage.query.filter_by(is_active=True).order_by(StyleImage.sort_order).all()
    #
    #     # 按分类组织图片数据
    #     style_data = {}
    #     for category in categories:
    #         style_data[category.code] = {
    #             'id': category.id,
    #             'name': category.name,
    #             'code': category.code,
    #             'description': category.description,
    #             'icon': category.icon,
    #             'cover_image': category.cover_image,
    #             'images': []
    #         }
    #
    #     # 将图片分配到对应分类
    #     for image in images:
    #         category_code = image.category.code
    #         if category_code in style_data:
    #             style_data[category_code]['images'].append({
    #                 'id': image.id,
    #                 'name': image.name,
    #                 'code': image.code,
    #                 'description': image.description,
    #                 'image_url': image.image_url
    #             })
    #
    #     # 获取产品配置数据
    #     products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    #     product_data = []
    #     for product in products:
    #         # 获取该产品的所有尺寸
    #         sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).order_by(ProductSize.sort_order).all()
    #         # 获取该产品的所有图片
    #         product_images = ProductImage.query.filter_by(product_id=product.id, is_active=True).order_by(ProductImage.sort_order).all()
    #         product_info = {
    #             'id': product.id,
    #             'code': product.code,
    #             'name': product.name,
    #             'description': product.description,
    #             'image_url': product.image_url,
    #             'sizes': [{'name': size.size_name, 'price': size.price} for size in sizes],
    #             'images': [{'url': img.image_url, 'sort_order': img.sort_order} for img in product_images]
    #         }
    #         product_data.append(product_info)
    #
    #     return render_template('index.html', style_data=style_data, product_data=product_data)
    #
    # except Exception as e:
    #     logger.info(f"加载首页数据失败: {str(e)}")
    #     # 如果出错，返回空的数据
    #     return render_template('index.html', style_data={}, product_data=[])


# ⭐ 作品展示功能已删除
# @base_bp.route('/works-gallery')
# def works_gallery():


@base_bp.route("/test-select-style")
def test_select_style():
    """测试下拉菜单样式页面"""
    from flask import send_file

    return send_file("test_select_style.html")


@base_bp.route("/playground")
@login_required
def playground():
    """Playground页面 - AI工作流测试平台"""
    try:
        # 检查权限
        if current_user.role not in ["admin", "operator"]:
            from flask import flash

            flash("权限不足", "error")
            return redirect(url_for("auth.login"))

        # 检查页面权限（操作员需要检查）
        if current_user.role == "operator":
            from flask import flash

            from app.utils.permission_utils import has_page_permission

            if not has_page_permission(current_user, "/playground"):
                flash("您没有权限访问Playground页面", "error")
                return redirect(url_for("admin_profile.admin_profile"))

        # 获取品牌名称
        from app.utils.config_loader import get_brand_name

        brand_name = get_brand_name()
        return render_template("playground.html", brand_name=brand_name, current_user=current_user)
    except Exception as e:
        logger.info(f"加载Playground页面失败: {str(e)}")
        import traceback

        traceback.print_exc()
        # 如果出错，返回基本页面
        return render_template("playground.html", brand_name="AI Studio", current_user=current_user)


@base_bp.route("/playground/tasks")
def playground_tasks():
    """Playground任务日志页面"""
    try:
        from flask_login import current_user

        from app.utils.config_loader import get_brand_name

        brand_name = get_brand_name()
        return render_template(
            "playground_tasks.html", brand_name=brand_name, current_user=current_user
        )
    except Exception as e:
        logger.info(f"加载Playground任务日志页面失败: {str(e)}")
        import traceback

        traceback.print_exc()
        from flask_login import current_user

        return render_template(
            "playground_tasks.html", brand_name="AI Studio", current_user=current_user
        )
