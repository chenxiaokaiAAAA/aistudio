# -*- coding: utf-8 -*-
"""
管理后台产品配置API路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
import sys
import os
import uuid
from werkzeug.utils import secure_filename

# 创建蓝图
admin_products_bp = Blueprint('admin_products', __name__)


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'Product': test_server_module.Product,
        'ProductSize': test_server_module.ProductSize,
        'ProductImage': test_server_module.ProductImage,
        'ProductSizePetOption': test_server_module.ProductSizePetOption,
        'ProductStyleCategory': test_server_module.ProductStyleCategory,
        'ProductCustomField': test_server_module.ProductCustomField,
        'StyleCategory': test_server_module.StyleCategory,
        'Order': test_server_module.Order,
        'app': test_server_module.app if hasattr(test_server_module, 'app') else current_app
    }


@admin_products_bp.route('/admin/sizes', methods=['GET', 'POST'])
@login_required
def admin_sizes():
    """产品配置管理页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    db = models['db']
    Product = models['Product']
    ProductSize = models['ProductSize']
    ProductImage = models['ProductImage']
    ProductSizePetOption = models['ProductSizePetOption']
    ProductStyleCategory = models['ProductStyleCategory']
    ProductCustomField = models['ProductCustomField']
    StyleCategory = models['StyleCategory']
    Order = models['Order']
    app = models['app']
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_product_with_sizes':
            # 一次性添加产品和多个尺寸
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            
            # 处理多图上传
            image_urls = []
            uploaded_files = request.files.getlist('product_images[]')
            
            static_products_dir = os.path.join(app.root_path, 'static', 'images', 'products')
            os.makedirs(static_products_dir, exist_ok=True)
            
            for i, file in enumerate(uploaded_files):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_urls.append(f"/static/images/products/{unique_filename}")
            
            # 保持向后兼容，如果没有多图上传，使用单图上传
            if not image_urls and 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(static_products_dir, unique_filename)
                    file.save(file_path)
                    image_urls.append(f"/static/images/products/{unique_filename}")
            
            image_url = image_urls[0] if image_urls else ''
            
            # 获取尺寸数据
            size_names = request.form.getlist('size_name[]')
            size_printer_ids = request.form.getlist('size_printer_id[]')
            size_prices = request.form.getlist('size_price[]')
            sort_order = request.form.get('sort_order', 0)
            try:
                sort_order = int(sort_order)
            except (ValueError, TypeError):
                sort_order = 0
            
            if code and name and size_names:
                existing = Product.query.filter_by(code=code).first()
                if existing:
                    flash('产品代码已存在', 'error')
                else:
                    # 获取选片赠送张数
                    try:
                        free_selection_count = int(request.form.get('free_selection_count', 1))
                        if free_selection_count < 0:
                            free_selection_count = 1
                    except (ValueError, TypeError):
                        free_selection_count = 1
                    
                    # 获取每加一张照片的价格
                    try:
                        extra_photo_price = float(request.form.get('extra_photo_price', 10.0))
                        if extra_photo_price < 0:
                            extra_photo_price = 10.0
                    except (ValueError, TypeError):
                        extra_photo_price = 10.0
                    
                    # 创建产品
                    product = Product(code=code, name=name, description=description, image_url=image_url, sort_order=sort_order, free_selection_count=free_selection_count, extra_photo_price=extra_photo_price)
                    db.session.add(product)
                    db.session.flush()
                    
                    # 添加多图
                    for i, img_url in enumerate(image_urls):
                        product_image = ProductImage(
                            product_id=product.id,
                            image_url=img_url,
                            sort_order=i
                        )
                        db.session.add(product_image)
                    
                    # 添加尺寸规格（宠物数量选项已注释 - 设备主要用于人像拍照，不需要宠物相关选项）
                    size_effect_images = request.files.getlist('size_effect_image[]')
                    for i, size_name in enumerate(size_names):
                        if size_name:
                            try:
                                printer_product_id = size_printer_ids[i] if i < len(size_printer_ids) else None
                                # 获取价格，如果没有则默认为0
                                try:
                                    size_price = float(size_prices[i]) if i < len(size_prices) and size_prices[i] else 0.0
                                except (ValueError, TypeError):
                                    size_price = 0.0
                                
                                # 处理效果图上传
                                effect_image_url = ''
                                if i < len(size_effect_images):
                                    effect_file = size_effect_images[i]
                                    if effect_file and effect_file.filename:
                                        filename = secure_filename(effect_file.filename)
                                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                                        static_products_dir = os.path.join(current_app.root_path, 'static', 'images', 'products')
                                        os.makedirs(static_products_dir, exist_ok=True)
                                        file_path = os.path.join(static_products_dir, unique_filename)
                                        effect_file.save(file_path)
                                        effect_image_url = f"/static/images/products/{unique_filename}"
                                
                                product_size = ProductSize(
                                    product_id=product.id,
                                    size_name=size_name,
                                    price=size_price,
                                    printer_product_id=printer_product_id,
                                    effect_image_url=effect_image_url,
                                    sort_order=i
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
                                #             return redirect(url_for('admin_products.admin_sizes'))
                                
                            except Exception as e:
                                flash(f'尺寸 {size_name} 添加失败: {str(e)}', 'error')
                                db.session.rollback()
                                return redirect(url_for('admin_products.admin_sizes'))
                    
                    # 处理风格分类绑定
                    bound_style_category_ids = request.form.getlist('style_category_ids[]')
                    bound_style_category_ids = [int(id) for id in bound_style_category_ids if id]
                    
                    for category_id in bound_style_category_ids:
                        binding = ProductStyleCategory(
                            product_id=product.id,
                            style_category_id=category_id
                        )
                        db.session.add(binding)
                    
                    # 处理自定义字段
                    custom_field_names = request.form.getlist('custom_field_name[]')
                    custom_field_types = request.form.getlist('custom_field_type[]')
                    custom_field_options = request.form.getlist('custom_field_options[]')
                    custom_field_required = request.form.getlist('custom_field_required[]')
                    
                    for i, field_name in enumerate(custom_field_names):
                        if field_name.strip():
                            field_type = custom_field_types[i] if i < len(custom_field_types) else 'text'
                            field_options = custom_field_options[i] if i < len(custom_field_options) else None
                            is_required = custom_field_required[i] == '1' if i < len(custom_field_required) else False
                            
                            custom_field = ProductCustomField(
                                product_id=product.id,
                                field_name=field_name.strip(),
                                field_type=field_type,
                                field_options=field_options.strip() if field_options else None,
                                is_required=is_required,
                                sort_order=i
                            )
                            db.session.add(custom_field)
                    
                    db.session.commit()
                    
                    # 自动同步到冲印系统配置
                    try:
                        from product_config_sync import auto_sync_product_config
                        auto_sync_product_config()
                        flash('产品和尺寸添加成功，已自动同步到冲印系统', 'success')
                    except Exception as sync_error:
                        print(f"自动同步失败: {sync_error}")
                        flash('产品和尺寸添加成功，但同步到冲印系统失败', 'warning')
            else:
                flash('请填写产品代码、名称和至少一个尺寸', 'error')
        
        elif action == 'delete_size':
            # 删除尺寸
            size_id = int(request.form.get('size_id'))
            try:
                product_size = ProductSize.query.get_or_404(size_id)
                
                orders_count = Order.query.filter_by(size=product_size.size_name).count()
                
                if orders_count > 0:
                    product_size.is_active = False
                    db.session.commit()
                    flash(f'该尺寸已有 {orders_count} 个订单，无法删除。已自动下架', 'warning')
                else:
                    db.session.delete(product_size)
                    db.session.commit()
                    flash('尺寸删除成功', 'success')
                
                try:
                    from product_config_sync import auto_sync_product_config
                    auto_sync_product_config()
                    if orders_count == 0:
                        flash('已自动同步到冲印系统', 'success')
                except Exception as sync_error:
                    print(f"自动同步失败: {sync_error}")
            except Exception as e:
                db.session.rollback()
                flash(f'操作失败: {str(e)}', 'error')
        
        elif action == 'edit_product':
            # 编辑产品
            product_id = int(request.form.get('product_id'))
            try:
                product = Product.query.get_or_404(product_id)
                
                # 更新产品基本信息
                product.code = request.form.get('code')
                product.name = request.form.get('name')
                product.description = request.form.get('description', '')
                try:
                    product.sort_order = int(request.form.get('sort_order', 0))
                except (ValueError, TypeError):
                    product.sort_order = 0
                
                # 更新选片赠送张数
                try:
                    free_selection_count = int(request.form.get('free_selection_count', 1))
                    if free_selection_count < 0:
                        free_selection_count = 1
                    product.free_selection_count = free_selection_count
                except (ValueError, TypeError):
                    product.free_selection_count = 1
                
                # 更新每加一张照片的价格
                try:
                    extra_photo_price = float(request.form.get('extra_photo_price', 10.0))
                    if extra_photo_price < 0:
                        extra_photo_price = 10.0
                    product.extra_photo_price = extra_photo_price
                except (ValueError, TypeError):
                    product.extra_photo_price = 10.0
                
                # 处理上架/下架状态
                is_active = request.form.get('is_active')
                if is_active is not None:
                    product.is_active = is_active in ['1', 'true', 'True', 'on']
                
                # 处理多图上传
                uploaded_files = request.files.getlist('product_images[]')
                if uploaded_files and any(f.filename for f in uploaded_files):
                    static_products_dir = os.path.join(app.root_path, 'static', 'images', 'products')
                    os.makedirs(static_products_dir, exist_ok=True)
                    
                    for file in uploaded_files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{uuid.uuid4().hex}_{filename}"
                            file_path = os.path.join(static_products_dir, unique_filename)
                            file.save(file_path)
                            image_url = f"/static/images/products/{unique_filename}"
                            
                            # 获取当前最大排序
                            max_sort = db.session.query(db.func.max(ProductImage.sort_order)).filter_by(product_id=product_id).scalar() or 0
                            
                            product_image = ProductImage(
                                product_id=product_id,
                                image_url=image_url,
                                sort_order=max_sort + 1
                            )
                            db.session.add(product_image)
                    
                    # 如果没有主图，设置第一张为主图
                    if not product.image_url and uploaded_files[0].filename:
                        first_image = ProductImage.query.filter_by(product_id=product_id).order_by(ProductImage.sort_order.asc()).first()
                        if first_image:
                            product.image_url = first_image.image_url
                
                # 处理风格分类绑定
                bound_style_category_ids = request.form.getlist('style_category_ids[]')
                bound_style_category_ids = [int(id) for id in bound_style_category_ids if id]
                
                # 删除旧的绑定
                ProductStyleCategory.query.filter_by(product_id=product_id).delete()
                
                # 添加新的绑定
                for category_id in bound_style_category_ids:
                    binding = ProductStyleCategory(
                        product_id=product_id,
                        style_category_id=category_id
                    )
                    db.session.add(binding)
                
                # 处理自定义字段
                existing_field_ids = request.form.getlist('existing_custom_field_id[]')
                custom_field_names = request.form.getlist('custom_field_name[]')
                custom_field_types = request.form.getlist('custom_field_type[]')
                custom_field_options = request.form.getlist('custom_field_options[]')
                custom_field_required = request.form.getlist('custom_field_required[]')
                
                # 删除所有旧的自定义字段
                ProductCustomField.query.filter_by(product_id=product_id).delete()
                
                # 添加新的自定义字段
                for i, field_name in enumerate(custom_field_names):
                    if field_name.strip():
                        field_type = custom_field_types[i] if i < len(custom_field_types) else 'text'
                        field_options = custom_field_options[i] if i < len(custom_field_options) else None
                        is_required = custom_field_required[i] == '1' if i < len(custom_field_required) else False
                        
                        custom_field = ProductCustomField(
                            product_id=product_id,
                            field_name=field_name.strip(),
                            field_type=field_type,
                            field_options=field_options.strip() if field_options else None,
                            is_required=is_required,
                            sort_order=i
                        )
                        db.session.add(custom_field)
                
                # 处理尺寸更新
                existing_size_ids = request.form.getlist('existing_size_id[]')
                size_names = request.form.getlist('size_name[]')
                size_printer_ids = request.form.getlist('size_printer_id[]')
                size_prices = request.form.getlist('size_price[]')
                size_effect_image_urls = request.form.getlist('size_effect_image_url[]')  # 现有的效果图URL
                size_effect_images = request.files.getlist('size_effect_image[]')  # 新上传的效果图
                
                # 导入必要的模块
                from werkzeug.utils import secure_filename
                import uuid
                
                # 确保所有数组长度一致（以size_names为准）
                max_len = len(size_names)
                print(f"📝 处理尺寸数据: 共 {max_len} 个尺寸")
                print(f"   - existing_size_ids (原始): {existing_size_ids}")
                print(f"   - size_names: {size_names}")
                print(f"   - size_prices: {size_prices}")
                print(f"   - size_effect_image_urls: {size_effect_image_urls}")
                print(f"   - size_effect_images 数量: {len(size_effect_images)}")
                
                # 处理重复的existing_size_id：只取前max_len个，并去重
                # 如果existing_size_ids长度大于max_len，说明有重复，只取前max_len个
                if len(existing_size_ids) > max_len:
                    print(f"⚠️ existing_size_ids长度({len(existing_size_ids)})大于size_names长度({max_len})，可能存在重复字段")
                    # 只取前max_len个，并去重（保留第一个出现的）
                    seen_ids = set()
                    deduplicated_ids = []
                    for sid in existing_size_ids[:max_len]:
                        if sid and sid.isdigit() and int(sid) not in seen_ids:
                            deduplicated_ids.append(sid)
                            seen_ids.add(int(sid))
                        elif not sid or not sid.isdigit():
                            deduplicated_ids.append('')
                    existing_size_ids = deduplicated_ids
                    print(f"   - existing_size_ids (去重后): {existing_size_ids}")
                
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
                        ProductSize.product_id == product_id,
                        ~ProductSize.id.in_(valid_size_ids)
                    ).delete(synchronize_session=False)
                    print(f"🗑️ 删除不在列表中的尺寸，保留的ID: {valid_size_ids}")
                
                # 按索引遍历所有尺寸，确保每个尺寸都正确处理
                for i in range(max_len):
                    try:
                        size_id_str = existing_size_ids[i] if i < len(existing_size_ids) else ''
                        size_name = size_names[i] if i < len(size_names) else ''
                        size_printer_id = size_printer_ids[i] if i < len(size_printer_ids) else ''
                        size_price = size_prices[i] if i < len(size_prices) else '0'
                        
                        if not size_name:
                            print(f"⚠️ 跳过第 {i+1} 个尺寸: 名称为空")
                            continue
                        
                        try:
                            price = float(size_price) if size_price else 0.0
                        except (ValueError, TypeError):
                            price = 0.0
                        
                        # 处理效果图：优先使用新上传的，否则使用现有的URL
                        effect_image_url = ''
                        
                        # 先获取现有的URL（如果有）
                        existing_url = ''
                        if i < len(size_effect_image_urls):
                            existing_url = size_effect_image_urls[i] or ''
                        
                        # 检查是否有新上传的效果图
                        has_new_image = False
                        if i < len(size_effect_images):
                            effect_file = size_effect_images[i]
                            # 检查文件是否真的被选择了（有文件名且不是空字符串）
                            if effect_file and hasattr(effect_file, 'filename') and effect_file.filename:
                                # 有新上传的效果图，使用新的
                                filename = secure_filename(effect_file.filename)
                                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                                static_products_dir = os.path.join(current_app.root_path, 'static', 'images', 'products')
                                os.makedirs(static_products_dir, exist_ok=True)
                                file_path = os.path.join(static_products_dir, unique_filename)
                                effect_file.save(file_path)
                                effect_image_url = f"/static/images/products/{unique_filename}"
                                has_new_image = True
                                print(f"✅ 第 {i+1} 个尺寸上传新效果图: {effect_image_url}")
                        
                        # 如果没有新上传的，使用现有的URL
                        if not has_new_image and existing_url:
                            effect_image_url = existing_url
                            print(f"📷 第 {i+1} 个尺寸使用现有效果图: {effect_image_url}")
                        elif not has_new_image and not existing_url:
                            print(f"⚠️ 第 {i+1} 个尺寸没有效果图")
                        
                        # 判断是更新还是创建
                        if size_id_str and size_id_str.isdigit():
                            # 更新现有尺寸
                            size_id = int(size_id_str)
                            size = ProductSize.query.get(size_id)
                            if size:
                                size.size_name = size_name
                                size.printer_product_id = size_printer_id if size_printer_id else None
                                size.price = price
                                size.effect_image_url = effect_image_url
                                size.sort_order = i
                                print(f"✅ 更新尺寸 ID={size_id}: {size_name}, 价格={price}, 效果图={effect_image_url}")
                            else:
                                print(f"⚠️ 尺寸 ID={size_id} 不存在，将创建新尺寸")
                                # 如果ID不存在，创建新尺寸
                                new_size = ProductSize(
                                    product_id=product_id,
                                    size_name=size_name,
                                    price=price,
                                    printer_product_id=size_printer_id if size_printer_id else None,
                                    effect_image_url=effect_image_url,
                                    sort_order=i
                                )
                                db.session.add(new_size)
                                print(f"✅ 添加新尺寸: {size_name}, 价格={price}, 效果图={effect_image_url}")
                        else:
                            # 添加新尺寸
                            new_size = ProductSize(
                                product_id=product_id,
                                size_name=size_name,
                                price=price,
                                printer_product_id=size_printer_id if size_printer_id else None,
                                effect_image_url=effect_image_url,
                                sort_order=i
                            )
                            db.session.add(new_size)
                            print(f"✅ 添加新尺寸: {size_name}, 价格={price}, 效果图={effect_image_url}")
                    except (ValueError, TypeError) as e:
                        print(f"❌ 处理第 {i+1} 个尺寸时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        pass
                
                db.session.commit()
                
                # 自动同步到冲印系统配置
                try:
                    from product_config_sync import auto_sync_product_config
                    auto_sync_product_config()
                    flash('产品更新成功，已自动同步到冲印系统', 'success')
                except Exception as sync_error:
                    print(f"自动同步失败: {sync_error}")
                    flash('产品更新成功，但同步到冲印系统失败', 'warning')
                    
            except Exception as e:
                db.session.rollback()
                flash(f'更新失败: {str(e)}', 'error')
                import traceback
                traceback.print_exc()
        
        elif action == 'delete_product_image':
            # 删除产品图片
            image_id = int(request.form.get('image_id'))
            try:
                product_image = ProductImage.query.get_or_404(image_id)
                product_id = product_image.product_id
                deleted_image_url = product_image.image_url
                
                if product_image.image_url:
                    image_path = product_image.image_url.lstrip('/')
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"删除图片文件失败: {str(e)}")
                
                db.session.delete(product_image)
                
                product = Product.query.get(product_id)
                if product and product.image_url == deleted_image_url:
                    other_image = ProductImage.query.filter_by(product_id=product_id).first()
                    if other_image:
                        product.image_url = other_image.image_url
                    else:
                        product.image_url = None
                
                db.session.commit()
                flash('图片删除成功', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'删除失败: {str(e)}', 'error')
        
        elif action == 'toggle_product_status':
            # 切换产品上架/下架状态
            product_id = int(request.form.get('product_id'))
            try:
                product = Product.query.get_or_404(product_id)
                product.is_active = not product.is_active
                db.session.commit()
                status_text = '上架' if product.is_active else '下架'
                flash(f'产品已{status_text}', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'操作失败: {str(e)}', 'error')
        
        elif action == 'delete_product':
            # 删除产品
            product_id = int(request.form.get('product_id'))
            try:
                product = Product.query.get_or_404(product_id)
                
                ProductSize.query.filter_by(product_id=product_id).delete()
                ProductImage.query.filter_by(product_id=product_id).delete()
                
                db.session.delete(product)
                db.session.commit()
                
                try:
                    from product_config_sync import auto_sync_product_config
                    auto_sync_product_config()
                    flash('产品删除成功，已自动同步到冲印系统', 'success')
                except Exception as sync_error:
                    print(f"自动同步失败: {sync_error}")
                    flash('产品删除成功，但同步到冲印系统失败', 'warning')
            except Exception as e:
                db.session.rollback()
                flash('删除失败', 'error')
        
        return redirect(url_for('admin_products.admin_sizes'))
    
    # GET请求：获取所有产品和尺寸
    try:
        products = Product.query.order_by(Product.sort_order.asc(), Product.id.asc()).all()
    except Exception as e:
        # 如果字段不存在，使用原始SQL查询
        print(f"ORM查询失败（可能缺少free_selection_count字段），使用原始SQL: {e}")
        from sqlalchemy import text
        try:
            result = db.session.execute(
                text("SELECT id, code, name, description, image_url, is_active, sort_order, created_at FROM products ORDER BY sort_order ASC, id ASC")
            )
            products_data = result.fetchall()
            # 转换为Product对象（简化版）
            class ProductObj:
                def __init__(self, id, code, name, description, image_url, is_active, sort_order, created_at):
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
            print(f"原始SQL查询也失败: {e2}")
            products = []
    product_sizes = ProductSize.query.join(Product).order_by(ProductSize.product_id.asc(), ProductSize.sort_order.asc()).all()
    product_images = ProductImage.query.join(Product).order_by(ProductImage.product_id.asc(), ProductImage.sort_order.asc()).all()
    
    # 宠物数量选项加载已注释 - 设备主要用于人像拍照，不需要宠物相关选项
    # 为每个尺寸加载宠物数量选项
    # for size in product_sizes:
    #     pet_options = ProductSizePetOption.query.filter_by(size_id=size.id).order_by(ProductSizePetOption.sort_order.asc()).all()
    #     size.pet_options = pet_options
    # 为每个尺寸设置空的宠物选项列表（避免模板报错）
    for size in product_sizes:
        size.pet_options = []
    
    # 获取所有风格分类
    style_categories = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order.asc()).all()
    
    # 获取产品与风格分类的绑定关系
    product_style_bindings = {}
    for product in products:
        bindings = ProductStyleCategory.query.filter_by(product_id=product.id).all()
        product_style_bindings[product.id] = [binding.style_category_id for binding in bindings]
    
    return render_template('admin/sizes.html', 
                         products=products, 
                         product_sizes=product_sizes, 
                         product_images=product_images,
                         style_categories=style_categories,
                         product_style_bindings=product_style_bindings)
