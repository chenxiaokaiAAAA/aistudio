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
        StyleSubcategory = models.get('StyleSubcategory')
        StyleImage = models['StyleImage']
        ProductStyleCategory = models['ProductStyleCategory']
        get_base_url = helpers['get_base_url']
        db = models['db']
        
        # 获取产品ID参数（可选）
        product_id = request.args.get('productId') or request.args.get('product_id')
        
        # 如果指定了产品ID，只返回该产品绑定的风格分类
        if product_id:
            print(f"🔍 请求风格分类，产品ID参数: {product_id}")
            # 通过产品code查找产品
            product = Product.query.filter_by(code=product_id, is_active=True).first()
            if not product:
                # 如果通过code找不到，尝试通过ID查找（兼容旧逻辑）
                try:
                    product_id_int = int(product_id)
                    product = Product.query.filter_by(id=product_id_int, is_active=True).first()
                    print(f"⚠️ 通过code未找到产品，尝试通过ID查找: {product_id_int}, 结果: {'找到' if product else '未找到'}")
                except (ValueError, TypeError):
                    pass
            
            if product:
                print(f"✅ 找到产品: {product.name} (ID: {product.id}, Code: {product.code})")
                # 获取产品绑定的风格分类ID
                bindings = ProductStyleCategory.query.filter_by(product_id=product.id).all()
                bound_category_ids = [binding.style_category_id for binding in bindings]
                print(f"📋 产品绑定的风格分类ID列表: {bound_category_ids}")
                
                if bound_category_ids:
                    # 只查询绑定的风格分类
                    categories = StyleCategory.query.filter(
                        StyleCategory.id.in_(bound_category_ids),
                        StyleCategory.is_active == True
                    ).order_by(StyleCategory.sort_order).all()
                    print(f"✅ 产品 {product.name} 绑定的风格分类数量: {len(categories)}")
                    for cat in categories:
                        print(f"   - {cat.name} (ID: {cat.id}, Code: {cat.code})")
                else:
                    # 产品没有绑定任何风格分类，返回空列表
                    categories = []
                    print(f"⚠️ 产品 {product.name} 没有绑定任何风格分类，返回空列表")
            else:
                # 产品不存在，返回空列表（不再返回所有分类，避免显示错误的分类）
                categories = []
                print(f"❌ 产品ID {product_id} 不存在，返回空列表")
        else:
            # 没有指定产品ID，返回所有风格分类
            categories = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order).all()
        
        result = []
        current_base_url = get_base_url()
        for category in categories:
            # 获取该分类下的所有二级分类
            subcategories_data = []
            if StyleSubcategory:
                subcategories = StyleSubcategory.query.filter_by(
                    category_id=category.id,
                    is_active=True
                ).order_by(StyleSubcategory.sort_order).all()
                
                for subcategory in subcategories:
                    subcategory_data = {
                        'id': subcategory.id,
                        'name': subcategory.name,
                        'code': subcategory.code,
                        'icon': subcategory.icon or '',
                        'cover_image': subcategory.cover_image or ''
                    }
                    # 处理二级分类封面图URL
                    if subcategory_data['cover_image']:
                        if not subcategory_data['cover_image'].startswith('http'):
                            subcategory_data['cover_image'] = f"{current_base_url}{subcategory_data['cover_image']}"
                        elif '192.168.2.54' in subcategory_data['cover_image']:
                            subcategory_data['cover_image'] = subcategory_data['cover_image'].replace('http://192.168.2.54:8000', current_base_url)
                    subcategories_data.append(subcategory_data)
            
            # 获取该分类下的所有风格图片（不按二级分类过滤，因为可能有些图片没有关联二级分类）
            images = StyleImage.query.filter_by(category_id=category.id, is_active=True).order_by(StyleImage.sort_order).all()
            
            # 确保封面图URL是完整的URL，并替换旧IP地址
            cover_image = category.cover_image
            if cover_image:
                if not cover_image.startswith('http'):
                    # 相对路径，补全为完整URL
                    cover_image = f"{current_base_url}{cover_image}"
                elif '192.168.2.54' in cover_image:
                    # 如果URL包含旧的IP地址，替换为当前配置的IP
                    cover_image = cover_image.replace('http://192.168.2.54:8000', current_base_url)
            
            category_data = {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'icon': category.icon,
                'cover_image': cover_image,
                'subcategories': subcategories_data,
                'images': []
            }
            
            for image in images:
                # 确保图片URL是完整的URL，并替换旧IP地址
                image_url = image.image_url
                if image_url:
                    if not image_url.startswith('http'):
                        # 相对路径，补全为完整URL
                        image_url = f"{current_base_url}{image_url}"
                    elif '192.168.2.54' in image_url:
                        # 如果URL包含旧的IP地址，替换为当前配置的IP
                        image_url = image_url.replace('http://192.168.2.54:8000', current_base_url)
                
                image_data = {
                    'id': image.id,
                    'name': image.name,
                    'code': image.code,
                    'description': image.description,
                    'image_url': image_url,
                    'subcategory_id': image.subcategory_id if hasattr(image, 'subcategory_id') else None
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
        current_base_url = get_base_url()
        for category in categories:
            images = StyleImage.query.filter_by(category_id=category.id, is_active=True).order_by(StyleImage.sort_order).all()
            
            # 确保封面图URL是完整的URL，并替换旧IP地址
            cover_image = category.cover_image
            if cover_image:
                if not cover_image.startswith('http'):
                    # 相对路径，补全为完整URL
                    cover_image = f"{current_base_url}{cover_image}"
                elif '192.168.2.54' in cover_image:
                    # 如果URL包含旧的IP地址，替换为当前配置的IP
                    cover_image = cover_image.replace('http://192.168.2.54:8000', current_base_url)
            
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
                # 确保图片URL是完整的URL，并替换旧IP地址
                image_url = image.image_url
                if image_url:
                    if not image_url.startswith('http'):
                        # 相对路径，补全为完整URL
                        image_url = f"{current_base_url}{image_url}"
                    elif '192.168.2.54' in image_url:
                        # 如果URL包含旧的IP地址，替换为当前配置的IP
                        image_url = image_url.replace('http://192.168.2.54:8000', current_base_url)
                
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


@bp.route('/product-categories', methods=['GET'])
def miniprogram_get_product_categories():
    """获取产品分类（一级和二级分类）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        ProductCategory = models.get('ProductCategory')
        ProductSubcategory = models.get('ProductSubcategory')
        get_base_url = helpers['get_base_url']
        
        if not ProductCategory or not ProductSubcategory:
            return jsonify({
                'status': 'success',
                'data': []
            })
        
        # 获取所有一级分类
        categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.sort_order.asc()).all()
        
        result = []
        for category in categories:
            # 获取该分类下的二级分类
            subcategories = ProductSubcategory.query.filter_by(
                category_id=category.id,
                is_active=True
            ).order_by(ProductSubcategory.sort_order.asc()).all()
            
            # 处理分类图片URL
            image_url = category.image_url
            if image_url:
                # 如果是相对路径，转换为完整URL
                if not image_url.startswith('http'):
                    image_url = f'{get_base_url()}{image_url}'
                # 对URL进行编码，确保特殊字符（包括空格）正确处理
                from urllib.parse import quote, urlparse, urlunparse
                parsed = urlparse(image_url)
                # 对路径部分进行编码，确保空格等特殊字符被正确编码
                # 使用quote的默认safe参数，只保留/不编码
                path_parts = parsed.path.split('/')
                encoded_parts = [quote(part, safe='') for part in path_parts]
                encoded_path = '/'.join(encoded_parts)
                image_url = urlunparse((parsed.scheme, parsed.netloc, encoded_path, parsed.params, parsed.query, parsed.fragment))
            else:
                # 如果没有图片，设置为空字符串
                image_url = ''
            
            category_data = {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'icon': category.icon,
                'image_url': image_url,
                'sort_order': category.sort_order,
                'style_redirect_page': category.style_redirect_page or '',
                'subcategories': []
            }
            
            # 添加二级分类
            for subcategory in subcategories:
                sub_image_url = subcategory.image_url
                if sub_image_url and not sub_image_url.startswith('http'):
                    sub_image_url = f'{get_base_url()}{sub_image_url}'
                
                category_data['subcategories'].append({
                    'id': subcategory.id,
                    'name': subcategory.name,
                    'code': subcategory.code,
                    'icon': subcategory.icon,
                    'image_url': sub_image_url,
                    'sort_order': subcategory.sort_order
                })
            
            result.append(category_data)
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        print(f"获取产品分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取产品分类失败'
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
        ProductCategory = models.get('ProductCategory')
        ProductSubcategory = models.get('ProductSubcategory')
        get_base_url = helpers['get_base_url']
        
        # 获取分类参数（可选）
        category_id = request.args.get('categoryId') or request.args.get('category_id')
        subcategory_id = request.args.get('subcategoryId') or request.args.get('subcategory_id')
        
        # 查询产品
        query = Product.query.filter_by(is_active=True)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if subcategory_id:
            query = query.filter_by(subcategory_id=subcategory_id)
        
        products = query.order_by(Product.sort_order.asc(), Product.id.asc()).all()
        
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
                            # 尝试解析为JSON数组（新格式：支持选项图片）
                            options_data = json.loads(field.field_options)
                            if isinstance(options_data, list):
                                # 新格式：每个选项是对象，包含name和image_url
                                color_options = []
                                for opt in options_data:
                                    if isinstance(opt, dict):
                                        color_options.append({
                                            'name': opt.get('name', ''),
                                            'image_url': opt.get('image_url', '')
                                        })
                                    else:
                                        # 兼容：如果是字符串，转换为对象
                                        color_options.append({
                                            'name': str(opt),
                                            'image_url': ''
                                        })
                            else:
                                # 如果不是列表，按逗号分隔（旧格式）
                                color_options = [{'name': opt.strip(), 'image_url': ''} for opt in field.field_options.split(',') if opt.strip()]
                        except:
                            # 如果不是JSON，按逗号分隔（旧格式）
                            color_options = [{'name': opt.strip(), 'image_url': ''} for opt in field.field_options.split(',') if opt.strip()]
            
            # 获取产品分类信息
            category_info = None
            subcategory_info = None
            if ProductCategory and hasattr(product, 'category_id') and product.category_id:
                category = ProductCategory.query.get(product.category_id)
                if category:
                    category_info = {
                        'id': category.id,
                        'name': category.name,
                        'code': category.code,
                        'icon': category.icon
                    }
            if ProductSubcategory and hasattr(product, 'subcategory_id') and product.subcategory_id:
                subcategory = ProductSubcategory.query.get(product.subcategory_id)
                if subcategory:
                    subcategory_info = {
                        'id': subcategory.id,
                        'name': subcategory.name,
                        'code': subcategory.code,
                        'icon': subcategory.icon
                    }
            
            product_data = {
                'id': product.code,  # 使用code作为id
                'code': product.code,
                'name': product.name,
                'description': product.description,
                'image': image_url,  # 保持向后兼容的主图片
                'images': images,   # 新增多图数组
                'sizes': [],
                'sort_order': product.sort_order or 0,  # 添加排序字段
                # 添加产品分类信息
                'category': category_info,
                'subcategory': subcategory_info,
                'category_id': product.category_id if hasattr(product, 'category_id') else None,
                'subcategory_id': product.subcategory_id if hasattr(product, 'subcategory_id') else None,
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
                
                # 处理效果图URL
                effect_image_url = size.effect_image_url
                if effect_image_url and not effect_image_url.startswith('http'):
                    effect_image_url = f'{get_base_url()}{effect_image_url}'
                
                size_data = {
                    'id': size.id,
                    'size_name': size.size_name,  # 添加size_name字段以兼容前端
                    'name': size.size_name,
                    'price': float(size.price),
                    'effect_image_url': effect_image_url if effect_image_url else None,  # 添加效果图URL
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

@bp.route('/homepage-config', methods=['GET'])
def miniprogram_get_homepage_config():
    """获取首页完整配置（分类导航、产品推荐模块）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        HomepageCategoryNav = models.get('HomepageCategoryNav')
        HomepageProductSection = models.get('HomepageProductSection')
        Product = models.get('Product')
        ProductImage = models.get('ProductImage')
        get_base_url = helpers['get_base_url']
        
        result = {
            'category_navs': [],
            'product_sections': [],
            'featured_section': {'show': False},
            'time_journey_section': {'show': False},
            'ip_collab_section': {'show': False},
            'works_section': {'show': False},
            'activity_banner': {'show': False}
        }
        
        # 获取分类导航
        if HomepageCategoryNav:
            navs = HomepageCategoryNav.query.filter_by(is_active=True).order_by(HomepageCategoryNav.sort_order).all()
            for nav in navs:
                image_url = nav.image_url
                # 如果是小程序本地图片路径（/images/开头），保持原样，不转换为服务器URL
                # 其他相对路径才转换为完整URL
                if image_url and not image_url.startswith('http') and not image_url.startswith('/images/'):
                    image_url = f"{get_base_url()}{image_url}"
                
                result['category_navs'].append({
                    'id': nav.id,
                    'name': nav.name,
                    'icon': nav.icon,
                    'image_url': image_url,
                    'link_type': nav.link_type,
                    'link_value': nav.link_value,
                    'category_id': nav.category_id
                })
        
        # 获取产品推荐模块（包括所有类型的模块）
        # 注意：固定模块（featured_section, time_journey, ip_collab, works）每个类型只取一个
        if HomepageProductSection and Product:
            # 先获取所有激活的模块
            all_sections = HomepageProductSection.query.filter_by(is_active=True).order_by(HomepageProductSection.sort_order).all()
            
            # 固定模块类型，每个类型只取第一个
            fixed_module_types = ['featured_section', 'time_journey', 'ip_collab', 'works']
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
                    except:
                        pass
                
                # 根据模块类型处理数据
                if section.section_type in ['featured', 'hot', 'seasonal', 'custom']:
                    # 标准产品推荐模块
                    # 解析产品ID列表
                    product_ids = []
                    if section.product_ids:
                        try:
                            product_ids = json.loads(section.product_ids)
                        except:
                            try:
                                product_ids = [int(x) for x in section.product_ids.split(',') if x.strip()]
                            except:
                                product_ids = []
                    
                    # 获取产品数据
                    products = []
                    if product_ids:
                        products_query = Product.query.filter(
                            Product.id.in_(product_ids),
                            Product.is_active == True
                        )
                        products_list = products_query.all()
                        products_dict = {p.id: p for p in products_list}
                        products = [products_dict[pid] for pid in product_ids if pid in products_dict]
                    elif section.category_id:
                        products = Product.query.filter_by(
                            category_id=section.category_id,
                            is_active=True
                        ).order_by(Product.sort_order).limit(section.limit).all()
                    else:
                        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).limit(section.limit).all()
                    
                    # 处理产品数据
                    products_data = []
                    for product in products:
                        product_image_url = None
                        if ProductImage:
                            product_image = ProductImage.query.filter_by(product_id=product.id).first()
                            if product_image:
                                product_image_url = product_image.image_url
                                if product_image_url and not product_image_url.startswith('http'):
                                    product_image_url = f"{get_base_url()}{product_image_url}"
                        
                        if not product_image_url and hasattr(product, 'images') and product.images:
                            try:
                                images = json.loads(product.images) if isinstance(product.images, str) else product.images
                                if images and len(images) > 0:
                                    product_image_url = images[0]
                                    if product_image_url and not product_image_url.startswith('http'):
                                        product_image_url = f"{get_base_url()}{product_image_url}"
                            except:
                                pass
                        
                        products_data.append({
                            'id': product.id,
                            'name': product.name,
                            'code': product.code,
                            'image_url': product_image_url,
                            'price': float(product.price) if hasattr(product, 'price') and product.price else 0
                        })
                    
                    result['product_sections'].append({
                        'id': section.id,
                        'section_type': section.section_type,
                        'title': section.title,
                        'subtitle': section.subtitle,
                        'show_more_button': section.show_more_button,
                        'more_link': section.more_link,
                        'layout_type': section.layout_type,
                        'products': products_data
                    })
                elif section.section_type == 'featured_section':
                    # 当季主推模块（特殊格式）
                    items = section_config.get('items', [])
                    processed_items = []
                    for item in items:
                        if item.get('image_url') and not item['image_url'].startswith('http'):
                            item['image_url'] = f"{get_base_url()}{item['image_url']}"
                        # 确保包含跳转链接字段
                        if 'link_type' not in item:
                            item['link_type'] = item.get('type', 'none')
                        if 'link_value' not in item:
                            item['link_value'] = item.get('link', item.get('value', ''))
                        processed_items.append(item)
                    
                    result['featured_section'] = {
                        'show': True,
                        'title': '当季主推',  # 固定标题，由前端决定
                        'show_subscribe': section_config.get('show_subscribe', True),
                        'items': processed_items
                    }
                elif section.section_type == 'time_journey':
                    # 时光旅程模块
                    categories = section_config.get('categories', [])
                    processed_categories = []
                    for cat in categories:
                        if cat.get('main_image') and not cat['main_image'].startswith('http'):
                            cat['main_image'] = f"{get_base_url()}{cat['main_image']}"
                        # 确保包含跳转链接字段
                        if 'link_type' not in cat:
                            cat['link_type'] = cat.get('type', 'none')
                        if 'link_value' not in cat:
                            cat['link_value'] = cat.get('link', cat.get('value', ''))
                        processed_categories.append(cat)
                    
                    result['time_journey_section'] = {
                        'show': True,
                        'title': '时光旅程',  # 固定标题，由前端决定
                        'categories': processed_categories
                    }
                elif section.section_type == 'ip_collab':
                    # IP联名模块
                    tabs = section_config.get('tabs', [])
                    processed_tabs = []
                    for tab in tabs:
                        if tab.get('logo') and not tab['logo'].startswith('http'):
                            tab['logo'] = f"{get_base_url()}{tab['logo']}"
                        # 确保images是字符串数组
                        if tab.get('images'):
                            if isinstance(tab['images'], list):
                                # 处理数组中的每个元素
                                processed_images = []
                                for img in tab['images']:
                                    if isinstance(img, str):
                                        # 字符串，直接处理URL
                                        if not img.startswith('http'):
                                            img = f"{get_base_url()}{img}"
                                        processed_images.append(img)
                                    elif isinstance(img, dict) and img.get('url'):
                                        # 对象，提取url字段
                                        img_url = img['url']
                                        if not img_url.startswith('http'):
                                            img_url = f"{get_base_url()}{img_url}"
                                        processed_images.append(img_url)
                                tab['images'] = processed_images
                            else:
                                # 如果不是数组，转换为数组
                                img = tab['images']
                                if isinstance(img, str):
                                    if not img.startswith('http'):
                                        img = f"{get_base_url()}{img}"
                                    tab['images'] = [img]
                                else:
                                    tab['images'] = []
                        else:
                            # 如果没有images，尝试从image_url获取
                            if tab.get('image_url'):
                                img_url = tab['image_url']
                                if not img_url.startswith('http'):
                                    img_url = f"{get_base_url()}{img_url}"
                                tab['images'] = [img_url]
                            else:
                                tab['images'] = []
                        # 确保包含跳转链接字段
                        if 'link_type' not in tab:
                            tab['link_type'] = tab.get('type', 'none')
                        if 'link_value' not in tab:
                            tab['link_value'] = tab.get('link', tab.get('value', ''))
                        processed_tabs.append(tab)
                    
                    result['ip_collab_section'] = {
                        'show': True,
                        'title': 'IP联名',  # 固定标题，由前端决定
                        'active_tab': section_config.get('active_tab'),
                        'tabs': processed_tabs
                    }
                elif section.section_type == 'works':
                    # 用户故事/作品展示模块
                    tabs = section_config.get('tabs', [])
                    processed_tabs = []
                    for tab in tabs:
                        if tab.get('main_image') and not tab['main_image'].startswith('http'):
                            tab['main_image'] = f"{get_base_url()}{tab['main_image']}"
                        if tab.get('images'):
                            for img in tab['images']:
                                if isinstance(img, dict):
                                    if img.get('url') and not img['url'].startswith('http'):
                                        img['url'] = f"{get_base_url()}{img['url']}"
                                    # 为图片对象添加跳转链接字段
                                    if 'link_type' not in img:
                                        img['link_type'] = img.get('type', 'none')
                                    if 'link_value' not in img:
                                        img['link_value'] = img.get('link', img.get('value', ''))
                                elif isinstance(img, str) and not img.startswith('http'):
                                    img = f"{get_base_url()}{img}"
                        # 确保tab包含跳转链接字段
                        if 'link_type' not in tab:
                            tab['link_type'] = tab.get('type', 'none')
                        if 'link_value' not in tab:
                            tab['link_value'] = tab.get('link', tab.get('value', ''))
                        processed_tabs.append(tab)
                    
                    result['works_section'] = {
                        'show': True,
                        'title': '作品展示',  # 固定标题，由前端决定
                        'active_tab': section_config.get('active_tab'),
                        'tabs': processed_tabs
                    }
        
        # 获取活动横幅
        HomepageActivityBanner = models.get('HomepageActivityBanner')
        if HomepageActivityBanner:
            banner = HomepageActivityBanner.query.filter_by(is_active=True).order_by(HomepageActivityBanner.sort_order).first()
            if banner:
                result['activity_banner'] = {
                    'show': True,
                    'text': banner.text
                }
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200, {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
    except Exception as e:
        print(f"获取首页配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取首页配置失败'
        }), 500