# -*- coding: utf-8 -*-
"""
小程序目录相关路由（风格、产品、轮播图）
"""
from flask import Blueprint, request, jsonify
from app.routes.miniprogram.common import get_models, get_helper_functions
import json

# 创建目录相关的子蓝图
bp = Blueprint('catalog', __name__)


@bp.route('/styles', methods=['GET'])
def miniprogram_get_styles():
    """获取所有风格分类和图片，支持按产品过滤"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Product = models['Product']
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        ProductStyleCategory = models['ProductStyleCategory']
        get_base_url = helpers['get_base_url']
        db = models['db']
        
        # 获取产品ID参数（可选）
        product_id = request.args.get('productId') or request.args.get('product_id')
        
        # 如果指定了产品ID，只返回该产品绑定的风格分类
        if product_id:
            # 通过产品code查找产品
            product = Product.query.filter_by(code=product_id, is_active=True).first()
            if product:
                # 获取产品绑定的风格分类ID
                bindings = ProductStyleCategory.query.filter_by(product_id=product.id).all()
                bound_category_ids = [binding.style_category_id for binding in bindings]
                
                if bound_category_ids:
                    # 只查询绑定的风格分类
                    categories = StyleCategory.query.filter(
                        StyleCategory.id.in_(bound_category_ids),
                        StyleCategory.is_active == True
                    ).order_by(StyleCategory.sort_order).all()
                    print(f"产品 {product.name} 绑定的风格分类数量: {len(categories)}")
                else:
                    # 产品没有绑定任何风格分类，返回空列表
                    categories = []
                    print(f"产品 {product.name} 没有绑定任何风格分类")
            else:
                # 产品不存在，返回所有风格分类（兼容旧逻辑）
                categories = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
                print(f"产品ID {product_id} 不存在，返回所有风格分类")
        else:
            # 没有指定产品ID，返回所有风格分类
            categories = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
        
        result = []
        for category in categories:
            images = StyleImage.query.filter_by(category_id=category.id, is_active=True).order_by(StyleImage.sort_order).all()
            
            # 确保封面图URL是完整的URL
            cover_image = category.cover_image
            if cover_image and not cover_image.startswith('http'):
                cover_image = f"{get_base_url()}{cover_image}"
            
            category_data = {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'icon': category.icon,
                'cover_image': cover_image,
                'images': []
            }
            
            for image in images:
                # 确保图片URL是完整的URL
                image_url = image.image_url
                if image_url and not image_url.startswith('http'):
                    image_url = f"{get_base_url()}{image_url}"
                
                image_data = {
                    'id': image.id,
                    'name': image.name,
                    'code': image.code,
                    'description': image.description,
                    'image_url': image_url
                }
                category_data['images'].append(image_data)
            
            result.append(category_data)
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200, {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
    except Exception as e:
        print(f"获取风格数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取风格数据失败'
        }), 500


@bp.route('/styles/refresh', methods=['GET'])
def miniprogram_refresh_styles():
    """强制刷新风格数据，清除缓存"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        get_base_url = helpers['get_base_url']
        from datetime import datetime
        
        # 强制重新查询数据库
        categories = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
        
        result = []
        for category in categories:
            images = StyleImage.query.filter_by(category_id=category.id, is_active=True).order_by(StyleImage.sort_order).all()
            
            # 确保封面图URL是完整的URL
            cover_image = category.cover_image
            if cover_image and not cover_image.startswith('http'):
                cover_image = f"{get_base_url()}{cover_image}"
            
            category_data = {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'icon': category.icon,
                'cover_image': cover_image,
                'images': [],
                'last_updated': datetime.now().isoformat()  # 添加时间戳
            }
            
            for image in images:
                # 确保图片URL是完整的URL
                image_url = image.image_url
                if image_url and not image_url.startswith('http'):
                    image_url = f"{get_base_url()}{image_url}"
                
                image_data = {
                    'id': image.id,
                    'name': image.name,
                    'code': image.code,
                    'description': image.description,
                    'image_url': image_url
                }
                category_data['images'].append(image_data)
            
            result.append(category_data)
        
        return jsonify({
            'status': 'success',
            'data': result,
            'refresh_time': datetime.now().isoformat()
        }), 200, {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
    except Exception as e:
        print(f"刷新风格数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '刷新风格数据失败'
        }), 500


@bp.route('/products', methods=['GET'])
def miniprogram_get_products():
    """获取所有产品配置"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Product = models['Product']
        ProductSize = models['ProductSize']
        ProductImage = models['ProductImage']
        ProductStyleCategory = models['ProductStyleCategory']
        ProductCustomField = models['ProductCustomField']
        ProductSizePetOption = models['ProductSizePetOption']
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        get_base_url = helpers['get_base_url']
        
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order.asc(), Product.id.asc()).all()
        
        result = []
        for product in products:
            sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).order_by(ProductSize.sort_order.asc()).all()
            
            print(f"产品: {product.name}, 尺寸数量: {len(sizes)}")
            
            # 处理图片URL
            image_url = product.image_url
            if image_url and not image_url.startswith('http'):
                # 如果是相对路径，转换为完整URL
                image_url = f'{get_base_url()}{image_url}'
            elif not image_url:
                # 如果没有图片，使用临时图片
                image_url = f'https://picsum.photos/300/400?random={product.id}'
            
            # 获取产品的多张图片
            product_images = ProductImage.query.filter_by(product_id=product.id, is_active=True).order_by(ProductImage.sort_order.asc()).all()
            images = []
            
            # 如果有ProductImage记录，使用多图
            if product_images:
                for img in product_images:
                    img_url = img.image_url
                    if img_url and not img_url.startswith('http'):
                        img_url = f'{get_base_url()}{img_url}'
                    images.append(img_url)
            else:
                # 如果没有多图记录，使用主图片
                images = [image_url] if image_url else [f'https://picsum.photos/300/400?random={product.id}']
            
            print(f"图片URL: {image_url}, 多图数量: {len(images)}")
            
            # 获取产品绑定的风格分类
            product_style_bindings = ProductStyleCategory.query.filter_by(product_id=product.id).all()
            bound_style_category_ids = [binding.style_category_id for binding in product_style_bindings]
            # 获取风格分类的code列表
            bound_style_category_codes = []
            if bound_style_category_ids:
                style_categories = StyleCategory.query.filter(StyleCategory.id.in_(bound_style_category_ids)).all()
                bound_style_category_codes = [cat.code for cat in style_categories]
            
            # 获取产品绑定的所有风格图片code（从风格分类下的所有图片）
            bound_style_codes = []
            if bound_style_category_ids:
                style_images = StyleImage.query.filter(
                    StyleImage.category_id.in_(bound_style_category_ids),
                    StyleImage.is_active == True
                ).all()
                bound_style_codes = [img.code for img in style_images]
            
            print(f"产品 {product.name} 绑定的风格分类ID: {bound_style_category_ids}")
            print(f"产品 {product.name} 绑定的风格分类code: {bound_style_category_codes}")
            print(f"产品 {product.name} 绑定的风格图片code: {bound_style_codes}")
            
            # 获取产品的自定义字段（用于颜色选项等）
            custom_fields = ProductCustomField.query.filter_by(product_id=product.id).all()
            custom_fields_data = []
            color_options = []  # 颜色选项列表
            
            for field in custom_fields:
                field_data = {
                    'field_name': field.field_name,
                    'field_type': field.field_type,
                    'field_options': field.field_options,
                    'is_required': field.is_required
                }
                custom_fields_data.append(field_data)
                
                # 如果是颜色/背景色字段，解析选项
                # 支持多种字段名称：背景色、颜色、背景颜色、background_color、color等
                # 也支持字段名称包含"色"或"color"的字段
                field_name_lower = field.field_name.lower() if field.field_name else ''
                is_color_field = (
                    field.field_name in ['背景色', '颜色', '背景颜色', 'background_color', 'color', '背景', '底色'] or
                    '色' in field.field_name or 
                    'color' in field_name_lower or
                    'background' in field_name_lower
                )
                
                if is_color_field and field.field_type == 'select':
                    if field.field_options:
                        try:
                            # 尝试解析为JSON数组
                            color_options = json.loads(field.field_options)
                        except:
                            # 如果不是JSON，按逗号分隔
                            color_options = [opt.strip() for opt in field.field_options.split(',') if opt.strip()]
            
            product_data = {
                'id': product.code,  # 使用code作为id
                'code': product.code,
                'name': product.name,
                'description': product.description,
                'image': image_url,  # 保持向后兼容的主图片
                'images': images,   # 新增多图数组
                'sizes': [],
                'sort_order': product.sort_order or 0,  # 添加排序字段
                # 添加产品-风格绑定信息
                'allowed_styles': bound_style_codes,  # 绑定的风格图片code列表
                'style_category_codes': bound_style_category_codes,  # 绑定的风格分类code列表
                'style_category_ids': bound_style_category_ids,  # 绑定的风格分类ID列表（备用）
                # 添加自定义字段数据
                'custom_fields': custom_fields_data,  # 所有自定义字段
                'color_options': color_options  # 颜色选项（便捷字段）
            }
            
            for size in sizes:
                print(f"  尺寸: {size.size_name}, 价格: {size.price}")
                
                # 获取尺寸的多宠配置
                pet_options = ProductSizePetOption.query.filter_by(size_id=size.id).order_by(ProductSizePetOption.sort_order.asc()).all()
                allow_multiple_pets = len(pet_options) > 1  # 如果有多个宠物选项，说明支持多宠
                
                print(f"    尺寸 {size.size_name} 的宠物选项数量: {len(pet_options)}, 支持多宠: {allow_multiple_pets}")
                
                size_data = {
                    'id': size.id,
                    'name': size.size_name,
                    'price': float(size.price),
                    # 添加多宠配置
                    'allow_multiple_pets': allow_multiple_pets,
                    'pet_options': [
                        {
                            'id': opt.id,
                            'name': opt.pet_count_name,
                            'price': float(opt.price)
                        }
                        for opt in pet_options
                    ] if pet_options else []
                }
                product_data['sizes'].append(size_data)
            
            result.append(product_data)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取产品数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取产品数据失败'
        }), 500


@bp.route('/banners', methods=['GET'])
def miniprogram_get_banners():
    """获取首页轮播图（小程序前端使用）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        HomepageBanner = models['HomepageBanner']
        get_base_url = helpers['get_base_url']
        
        banners = HomepageBanner.query.filter_by(is_active=True).order_by(HomepageBanner.sort_order).all()
        
        result = []
        for banner in banners:
            # 确保图片URL是完整的URL
            image_url = banner.image_url
            if image_url and not image_url.startswith('http'):
                image_url = f"{get_base_url()}{image_url}"
            
            # 尝试获取新字段，如果不存在则使用默认值
            try:
                promotion_params = None
                if hasattr(banner, 'promotion_params') and banner.promotion_params:
                    try:
                        promotion_params = json.loads(banner.promotion_params)
                    except (json.JSONDecodeError, TypeError):
                        promotion_params = None
                
                banner_type = getattr(banner, 'type', 'link')
            except AttributeError:
                promotion_params = None
                banner_type = 'link'
            
            result.append({
                'id': banner.id,
                'title': banner.title,
                'subtitle': banner.subtitle,
                'image_url': image_url,
                'link': banner.link,
                'type': banner_type,
                'promotion_params': promotion_params,
                'sort_order': banner.sort_order
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200, {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
    except Exception as e:
        print(f"获取轮播图失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取轮播图失败'
        }), 500
