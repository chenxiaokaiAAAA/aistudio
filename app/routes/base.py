# -*- coding: utf-8 -*-
"""
基础路由（首页、作品展示等）
"""
from flask import Blueprint, render_template, redirect, url_for
import sys

# 创建蓝图
base_bp = Blueprint('base', __name__)


@base_bp.route('/')
def index():
    """首页 - 重定向到管理后台登录页面"""
    # 暂时隐藏首页，直接跳转到登录页面
    # 如果需要恢复首页，可以取消下面的注释，并注释掉重定向
    return redirect(url_for('auth.login'))
    
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
    #     print(f"加载首页数据失败: {str(e)}")
    #     # 如果出错，返回空的数据
    #     return render_template('index.html', style_data={}, product_data=[])


# ⭐ 作品展示功能已删除
# @base_bp.route('/works-gallery')
# def works_gallery():


@base_bp.route('/test-select-style')
def test_select_style():
    """测试下拉菜单样式页面"""
    from flask import send_file
    return send_file('test_select_style.html')
