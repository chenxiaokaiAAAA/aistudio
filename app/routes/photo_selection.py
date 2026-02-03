# -*- coding: utf-8 -*-
"""
选片页面路由模块
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sys
import os
import json
import uuid
import time
import qrcode
import base64
from io import BytesIO
from sqlalchemy import and_, or_

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
photo_selection_bp = Blueprint('photo_selection', __name__)

# 临时token存储（实际生产环境建议使用Redis）
_selection_tokens = {}
# 短token到完整token的映射
_short_token_map = {}


@photo_selection_bp.route('/admin/photo-selection')
def photo_selection_list():
    """选片页面 - 订单列表"""
    models = get_models(['Order', 'AITask'])
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    Order = models['Order']
    AITask = models['AITask']
    
    # 检查用户权限：如果是加盟商，只能查看自己的订单
    from flask import session
    from flask_login import current_user
    
    session_franchisee_id = session.get('franchisee_id')
    
    # 获取筛选参数
    franchisee_id = request.args.get('franchisee_id', type=int)
    
    # 如果session中有加盟商ID，说明是加盟商登录
    if session_franchisee_id:
        # 加盟商只能查看自己的订单，忽略URL参数中的franchisee_id
        franchisee_id = session_franchisee_id
    else:
        # 管理员需要登录且是admin或operator角色
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'operator']:
            flash('权限不足', 'error')
            return redirect(url_for('auth.login'))
    
    # 构建查询
    query = Order.query.filter(Order.status != 'unpaid')
    
    # 如果指定了加盟商ID，则只显示该加盟商的订单
    if franchisee_id:
        query = query.filter(Order.franchisee_id == franchisee_id)
    
    # 获取订单列表
    orders = query.order_by(Order.created_at.desc()).all()
    
    # 获取应用实例以访问配置
    from flask import current_app
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app_instance = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app_instance = current_app
    
    # 为每个订单检查任务状态
    orders_data = []
    for order in orders:
        # 获取该订单的所有AI任务
        ai_tasks = AITask.query.filter_by(order_id=order.id).all()
        
        # 检查是否所有任务都已完成
        # 如果有任务，则检查是否全部完成；如果没有任务，检查订单状态和效果图
        if len(ai_tasks) > 0:
            all_completed = all(task.status == 'completed' for task in ai_tasks)
        else:
            # 如果没有AI任务记录，但有效果图（手动上传），也认为可以选片
            # 检查订单是否有效果图文件
            has_effect_image = bool(order.hd_image)
            all_completed = has_effect_image and order.status in ['completed', 'hd_ready']
        
        # 获取效果图数量 - 首先从AITask统计，如果数量为0则从文件系统读取
        effect_images_count = 0
        
        # 1. 从AITask统计已完成且有效果图的任务
        if len(ai_tasks) > 0:
            completed_tasks_with_images = [task for task in ai_tasks 
                                          if task.status == 'completed' 
                                          and task.output_image_path]
            effect_images_count = len(completed_tasks_with_images)
            print(f"订单 {order.order_number}: 从AITask找到 {effect_images_count} 个已完成且有效果图的任务")
        
        # 2. 如果AITask中没有效果图，尝试从文件系统读取（与订单详情页面逻辑一致）
        if effect_images_count == 0:
            try:
                hd_folder = app_instance.config.get('HD_FOLDER', os.path.join(app_instance.root_path, 'hd_images'))
                if not os.path.isabs(hd_folder):
                    hd_folder = os.path.join(app_instance.root_path, hd_folder)
                
                if os.path.exists(hd_folder):
                    # 查找该订单的所有效果图文件
                    import glob
                    pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                    effect_files = glob.glob(pattern)
                    effect_images_count = len(effect_files)
                    if effect_images_count > 0:
                        print(f"订单 {order.order_number}: 从文件系统找到 {effect_images_count} 张效果图")
            except Exception as e:
                print(f"订单 {order.order_number}: 从文件系统读取效果图失败: {e}")
        
        # 3. 如果仍然为0，但订单有hd_image字段，计数为1（兼容旧数据）
        if effect_images_count == 0 and order.hd_image:
            effect_images_count = 1
            print(f"订单 {order.order_number}: 使用hd_image字段，效果图数量: 1")
        
        # 状态映射
        status_map = {
            'unpaid': '未支付',
            'paid': '已支付',
            'shooting': '正在拍摄',
            'retouching': '美颜处理中',
            'ai_processing': 'AI任务处理中',
            'pending_selection': '待选片',
            'selection_completed': '已选片',
            'printing': '打印中',
            'pending_shipment': '待发货',
            'shipped': '已发货',
            'pending': '待制作',
            'processing': '处理中',
            'manufacturing': '制作中',
            'completed': '已完成',
            'delivered': '已送达',
            'cancelled': '已取消',
            'refunded': '已退款',
            'hd_ready': '高清放大'
        }
        
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer_name or '',
            'customer_phone': order.customer_phone or '',
            'status': order.status,
            'status_text': status_map.get(order.status, order.status or '未知'),
            'product_name': order.product_name or '',
            'franchisee_id': getattr(order, 'franchisee_id', None),
            'all_tasks_completed': all_completed,
            'effect_images_count': effect_images_count,
            'created_at': order.created_at,
            'franchisee_id': getattr(order, 'franchisee_id', None)
        })
    
    # 获取加盟商信息（如果指定了加盟商ID）
    franchisee_info = None
    if franchisee_id:
        FranchiseeAccount = models.get('FranchiseeAccount')
        if FranchiseeAccount:
            franchisee = FranchiseeAccount.query.get(franchisee_id)
            if franchisee:
                franchisee_info = {
                    'id': franchisee.id,
                    'company_name': franchisee.company_name
                }
    
    return render_template('admin/photo_selection_list.html', 
                         orders=orders_data, 
                         franchisee_id=franchisee_id,
                         franchisee_info=franchisee_info)


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>')
def photo_selection_detail(order_id):
    """选片页面 - 选片详情"""
    models = get_models(['Order', 'AITask', 'Product', 'ProductSize', 'ShopProduct', 'ShopProductSize', 'StyleCategory', 'StyleImage', 'PrintSizeConfig'])
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('photo_selection.photo_selection_list'))
    
    Order = models['Order']
    AITask = models['AITask']
    Product = models['Product']
    ProductSize = models['ProductSize']
    ShopProduct = models['ShopProduct']
    ShopProductSize = models['ShopProductSize']
    
    order = Order.query.get_or_404(order_id)
    
    # 检查用户权限：如果是加盟商，只能查看自己的订单
    from flask import session
    from flask_login import current_user
    
    session_franchisee_id = session.get('franchisee_id')
    
    # 如果session中有加盟商ID，检查订单是否属于该加盟商
    if session_franchisee_id:
        if getattr(order, 'franchisee_id', None) != session_franchisee_id:
            flash('无权访问此订单', 'error')
            return redirect(url_for('photo_selection.photo_selection_list', franchisee_id=session_franchisee_id))
    else:
        # 管理员需要登录且是admin或operator角色
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'operator']:
            flash('权限不足', 'error')
            return redirect(url_for('auth.login'))
    
    # 获取应用实例
    from flask import current_app
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    # 获取订单的所有已完成的效果图（从AITask中获取）
    ai_tasks = AITask.query.filter_by(
        order_id=order.id,
        status='completed'
    ).filter(AITask.output_image_path.isnot(None)).order_by(AITask.completed_at.desc()).all()
    
    # 构建效果图列表
    effect_images = []
    for task in ai_tasks:
        if task.output_image_path:
            # 处理output_image_path：可能是相对路径、绝对路径或云端URL
            output_path = task.output_image_path
            
            # 如果是云端URL，直接使用
            if output_path.startswith('http://') or output_path.startswith('https://'):
                image_url = output_path
                filename = output_path.split('/')[-1]  # 提取文件名
                
                effect_images.append({
                    'id': task.id,
                    'url': image_url,
                    'path': filename,
                    'created_at': task.completed_at or task.created_at
                })
            else:
                # 如果是相对路径（如 final_works/xxx.png），提取文件名
                if '/' in output_path or '\\' in output_path:
                    # 提取文件名（处理Windows和Unix路径）
                    filename = os.path.basename(output_path.replace('\\', '/'))
                else:
                    filename = output_path
                
                # 先获取文件夹路径（在使用之前定义）
                hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
                final_folder = app.config.get('FINAL_FOLDER', os.path.join(app.root_path, 'final_works'))
                
                if not os.path.isabs(hd_folder):
                    hd_folder = os.path.join(app.root_path, hd_folder)
                if not os.path.isabs(final_folder):
                    final_folder = os.path.join(app.root_path, final_folder)
                
                # 构建图片URL（使用缩略图进行预览）
                from urllib.parse import quote
                from app.utils.image_thumbnail import get_thumbnail_path
                
                # 检查缩略图是否存在
                thumbnail_filename = get_thumbnail_path(filename)
                # 提取缩略图文件名（去掉路径）
                if '/' in thumbnail_filename or '\\' in thumbnail_filename:
                    thumbnail_filename = os.path.basename(thumbnail_filename.replace('\\', '/'))
                
                # 检查缩略图文件是否存在
                thumbnail_exists = False
                if os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                    thumbnail_exists = True
                elif os.path.exists(os.path.join(final_folder, thumbnail_filename)):
                    thumbnail_exists = True
                
                # 如果缩略图存在，使用缩略图；否则使用原图
                if thumbnail_exists:
                    encoded_filename = quote(thumbnail_filename, safe='')
                    image_url = f"/public/hd/{encoded_filename}"
                    print(f"✅ 使用缩略图: {thumbnail_filename}")
                else:
                    encoded_filename = quote(filename, safe='')
                    image_url = f"/public/hd/{encoded_filename}"
                    print(f"⚠️ 缩略图不存在，使用原图: {filename}")
                
                # 检查文件是否存在（优先检查HD_FOLDER，然后检查FINAL_FOLDER）
                file_exists = False
                if os.path.exists(os.path.join(hd_folder, filename)):
                    file_exists = True
                elif os.path.exists(os.path.join(final_folder, filename)):
                    file_exists = True
                
                if file_exists:
                    effect_images.append({
                        'id': task.id,
                        'url': image_url,
                        'path': filename,
                        'created_at': task.completed_at or task.created_at
                    })
                else:
                    # 即使文件不存在，也添加（可能是云端文件，通过URL访问）
                    print(f"⚠️ 选片详情 - 效果图文件不存在: {filename} (在HD_FOLDER和FINAL_FOLDER中均未找到)，但仍添加到列表（可能是云端文件）")
                    effect_images.append({
                        'id': task.id,
                        'url': image_url,
                        'path': filename,
                        'created_at': task.completed_at or task.created_at
                    })
    
    # 如果AITask中没有效果图，尝试从文件系统读取（与订单详情页面逻辑一致）
    if len(effect_images) == 0:
        try:
            hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)
            
            if os.path.exists(hd_folder):
                # 查找该订单的所有效果图文件
                import glob
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                effect_files = glob.glob(pattern)
                effect_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
                
                for filepath in effect_files:
                    filename = os.path.basename(filepath)
                    
                    # 构建图片URL（使用缩略图进行预览）
                    from urllib.parse import quote
                    from app.utils.image_thumbnail import get_thumbnail_path
                    
                    # 检查缩略图是否存在
                    thumbnail_filename = get_thumbnail_path(filename)
                    # 提取缩略图文件名（去掉路径）
                    if '/' in thumbnail_filename or '\\' in thumbnail_filename:
                        thumbnail_filename = os.path.basename(thumbnail_filename.replace('\\', '/'))
                    
                    # 检查缩略图文件是否存在
                    thumbnail_exists = False
                    if os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                        thumbnail_exists = True
                    
                    # 如果缩略图存在，使用缩略图；否则使用原图
                    if thumbnail_exists:
                        encoded_filename = quote(thumbnail_filename, safe='')
                        image_url = f"/public/hd/{encoded_filename}"
                        print(f"✅ 文件系统读取 - 使用缩略图: {thumbnail_filename}")
                    else:
                        encoded_filename = quote(filename, safe='')
                        image_url = f"/public/hd/{encoded_filename}"
                        print(f"⚠️ 文件系统读取 - 缩略图不存在，使用原图: {filename}")
                    
                    effect_images.append({
                        'id': 0,  # 文件系统读取的没有ID
                        'url': image_url,
                        'path': filename,
                        'created_at': datetime.fromtimestamp(os.path.getmtime(filepath))
                    })
                
                print(f"选片详情 - 订单 {order.order_number}: 从文件系统读取到 {len(effect_images)} 张效果图")
        except Exception as e:
            print(f"选片详情 - 从文件系统读取效果图失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 获取产品的免费选片张数和额外照片价格
    free_selection_count = 1  # 默认1张
    extra_photo_price = 10.0  # 默认10元/张
    if order.product_name:
        # 尝试从产品名称匹配产品
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        if product:
            if hasattr(product, 'free_selection_count'):
                free_selection_count = product.free_selection_count or 1
            if hasattr(product, 'extra_photo_price'):
                extra_photo_price = product.extra_photo_price or 10.0
    
    # 根据订单的product_name和size查找对应的套餐产品
    # 订单的product_name对应Product表，size对应ProductSize表
    package_product = None
    package_size = None
    package_effect_image_url = None
    
    print(f"🔍 查找套餐产品: order.product_name='{order.product_name}', order.size='{order.size}'")
    
    if order.product_name and order.size:
        # 首先从Product表查找匹配的产品（订单的product_name对应Product.name）
        package_product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        
        if package_product:
            print(f"✅ 找到产品: id={package_product.id}, name={package_product.name}")
            
            # 获取该产品的所有规格用于调试
            all_sizes_debug = ProductSize.query.filter_by(
                product_id=package_product.id,
                is_active=True
            ).all()
            print(f"📋 该产品共有 {len(all_sizes_debug)} 个规格:")
            for s in all_sizes_debug:
                print(f"   - id={s.id}, size_name='{s.size_name}', effect_image_url='{s.effect_image_url or '(无)'}'")
            
            # 根据订单的size查找匹配的ProductSize（订单的size对应ProductSize.size_name）
            # 首先尝试完全匹配（去除空格）
            order_size_trimmed = order.size.strip()
            package_size = ProductSize.query.filter_by(
                product_id=package_product.id,
                size_name=order_size_trimmed,
                is_active=True
            ).first()
            
            if package_size:
                print(f"✅ 完全匹配找到规格: id={package_size.id}, size_name='{package_size.size_name}'")
            else:
                print(f"⚠️ 完全匹配未找到，尝试智能匹配...")
                # 智能匹配：提取基础尺寸（如从"证件照-2寸-蓝底"提取"证件照-2寸"）
                # 订单size可能包含额外信息（如"证件照-2寸-蓝底"），需要提取基础部分
                order_size_parts = order_size_trimmed.split('-')
                base_size_candidates = []
                # 生成可能的匹配模式：证件照-2寸, 证件照-2寸-蓝底, 证件照-2寸-蓝底-xxx
                for i in range(1, len(order_size_parts) + 1):
                    base_size_candidates.append('-'.join(order_size_parts[:i]))
                
                print(f"   尝试匹配模式: {base_size_candidates}")
                
                # 先尝试精确匹配（去除空格）
                for candidate in base_size_candidates:
                    for size in all_sizes_debug:
                        size_name_trimmed = size.size_name.strip()
                        if size_name_trimmed == candidate:
                            package_size = size
                            print(f"✅ 智能匹配找到规格: id={size.id}, size_name='{size.size_name}' (匹配模式: '{candidate}')")
                            break
                    if package_size:
                        break
                
                # 如果还是没找到，尝试包含匹配
                if not package_size:
                    for size in all_sizes_debug:
                        size_name_trimmed = size.size_name.strip()
                        # 检查订单size是否包含规格名称，或规格名称是否包含订单size的基础部分
                        if (size_name_trimmed in order_size_trimmed) or (order_size_parts[0] in size_name_trimmed and len(order_size_parts) > 1 and order_size_parts[1] in size_name_trimmed):
                            package_size = size
                            print(f"✅ 包含匹配找到规格: id={size.id}, size_name='{size.size_name}'")
                            break
            
            # 如果找到了规格，获取效果图
            if package_size:
                if package_size.effect_image_url:
                    package_effect_image_url = package_size.effect_image_url
                    print(f"✅ 找到套餐产品效果图: 产品={package_product.name}, 规格={package_size.size_name}, 效果图={package_effect_image_url}")
                else:
                    print(f"⚠️ 找到规格但无效果图: 产品={package_product.name}, 规格={package_size.size_name}, effect_image_url为空")
            else:
                print(f"❌ 未找到匹配的规格")
        else:
            print(f"❌ 未找到产品: product_name='{order.product_name}'")
            # 列出所有产品用于调试
            all_products = Product.query.filter_by(is_active=True).all()
            print(f"📋 当前所有激活的产品: {[p.name for p in all_products]}")
    else:
        print(f"⚠️ 订单缺少必要信息: product_name={order.product_name}, size={order.size}")
    
    # 获取设计图片（水印）- 从订单的风格主题获取
    design_image_url = None
    print(f"🔍 查找设计图片: order.style_name='{order.style_name}'")
    
    if order.style_name:
        # 查找对应的风格主题
        StyleImage = models.get('StyleImage')
        if StyleImage:
            # 订单的style_name格式可能是"证件照/衬衫"，需要匹配StyleImage.name
            # 先尝试完全匹配
            style_image = StyleImage.query.filter_by(name=order.style_name, is_active=True).first()
            
            if not style_image:
                # 如果完全匹配失败，尝试只匹配风格名称部分（如"衬衫"）
                style_name_parts = order.style_name.split('/')
                if len(style_name_parts) > 1:
                    style_name_only = style_name_parts[-1].strip()  # 取最后一部分，如"衬衫"
                    print(f"   尝试匹配风格名称: '{style_name_only}'")
                    style_image = StyleImage.query.filter_by(name=style_name_only, is_active=True).first()
                    if not style_image:
                        # 尝试模糊匹配（包含）
                        all_styles = StyleImage.query.filter_by(is_active=True).all()
                        for s in all_styles:
                            if style_name_only in s.name or s.name in style_name_only:
                                style_image = s
                                print(f"   模糊匹配找到: '{s.name}'")
                                break
            
            if style_image:
                print(f"✅ 找到风格主题: id={style_image.id}, name={style_image.name}")
                # 使用design_image_url字段（如果已配置）
                if hasattr(style_image, 'design_image_url'):
                    print(f"   - design_image_url字段存在: '{style_image.design_image_url or '(空)'}'")
                    if style_image.design_image_url:
                        design_image_url = style_image.design_image_url
                        print(f"✅ 找到设计图片: {design_image_url}")
                    else:
                        print(f"⚠️ design_image_url字段为空")
                else:
                    print(f"⚠️ design_image_url字段不存在")
            else:
                print(f"❌ 未找到风格主题: style_name='{order.style_name}'")
                # 列出所有风格主题用于调试
                all_styles = StyleImage.query.filter_by(is_active=True).all()
                print(f"📋 当前所有激活的风格主题: {[s.name for s in all_styles]}")
        else:
            print(f"❌ StyleImage模型未找到，models.keys()={list(models.keys()) if models else 'None'}")
    else:
        print(f"⚠️ 订单无style_name")
    
    # 不再显示推荐产品列表，只传递套餐产品信息
    return render_template('admin/photo_selection_detail.html',
                         order=order,
                         effect_images=effect_images,
                         free_selection_count=free_selection_count,
                         extra_photo_price=extra_photo_price,
                         package_product=package_product,
                         package_size=package_size,
                         package_effect_image_url=package_effect_image_url,
                         design_image_url=design_image_url)


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>/submit', methods=['POST'])
def photo_selection_submit(order_id):
    """提交选片结果"""
    models = get_models(['Order', 'AITask', 'Product', 'ProductSize', 'ShopProduct', 'ShopProductSize', 'db'])
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    AITask = models['AITask']
    Product = models['Product']
    ShopProduct = models['ShopProduct']
    ShopProductSize = models['ShopProductSize']
    ShopOrder = models.get('ShopOrder')
    db = models['db']
    
    try:
        data = request.get_json()
        selected_image_ids = data.get('selected_image_ids', [])  # 选中的效果图ID列表（AITask的ID）
        image_product_mappings = data.get('image_product_mappings', {})  # 每张照片的产品关联信息 {imageId: [{product_id, size_id, quantity}, ...]}
        # 兼容旧版本（如果没有image_product_mappings，使用旧的selected_product_id和selected_size_id）
        selected_product_id = data.get('selected_product_id')
        selected_size_id = data.get('selected_size_id')
        
        if not selected_image_ids:
            return jsonify({'success': False, 'message': '请至少选择一张照片'}), 400
        
        # 产品关联是可选的（增项），不再强制要求
        # 如果有产品关联信息，会为关联的照片创建商城订单
        # 如果没有产品关联，只完成选片，不创建商城订单
        
        # 获取订单
        order = Order.query.get_or_404(order_id)
        
        # 检查用户权限：如果是加盟商，只能操作自己的订单
        from flask import session
        from flask_login import current_user
        
        session_franchisee_id = session.get('franchisee_id')
        
        # 如果session中有加盟商ID，检查订单是否属于该加盟商
        if session_franchisee_id:
            if getattr(order, 'franchisee_id', None) != session_franchisee_id:
                return jsonify({'success': False, 'message': '无权操作此订单'}), 403
        else:
            # 管理员需要登录且是admin或operator角色
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'message': '未登录'}), 401
            if current_user.role not in ['admin', 'operator']:
                return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取产品的免费选片张数和额外照片价格
        free_selection_count = 1  # 默认1张
        extra_photo_price = 10.0  # 默认10元/张
        if order.product_name:
            product = Product.query.filter_by(name=order.product_name, is_active=True).first()
            if product:
                if hasattr(product, 'free_selection_count'):
                    free_selection_count = product.free_selection_count or 1
                if hasattr(product, 'extra_photo_price'):
                    extra_photo_price = product.extra_photo_price or 10.0
        
        # 计算超出费用
        extra_count = max(0, len(selected_image_ids) - free_selection_count)
        extra_fee = extra_count * extra_photo_price
        
        # 获取选中的效果图路径（取第一张作为主图）
        # 分离AITask ID和文件系统图片（ID为0）
        task_ids = [img_id for img_id in selected_image_ids if img_id != 0]
        file_system_images = [img_id for img_id in selected_image_ids if img_id == 0]
        
        main_image_path = None
        
        # 1. 从AITask获取效果图
        if task_ids:
            selected_tasks = AITask.query.filter(
                AITask.id.in_(task_ids),
                AITask.order_id == order_id
            ).all()
            
            if selected_tasks:
                main_image_path = selected_tasks[0].output_image_path
        
        # 2. 如果包含文件系统的图片（ID为0），从文件系统查找
        if file_system_images or (not task_ids and selected_image_ids):
            # 获取应用实例
            from flask import current_app
            import sys
            if 'test_server' in sys.modules:
                test_server_module = sys.modules['test_server']
                app_instance = test_server_module.app if hasattr(test_server_module, 'app') else current_app
            else:
                app_instance = current_app
            
            try:
                hd_folder = app_instance.config.get('HD_FOLDER', os.path.join(app_instance.root_path, 'hd_images'))
                if not os.path.isabs(hd_folder):
                    hd_folder = os.path.join(app_instance.root_path, hd_folder)
                
                if os.path.exists(hd_folder):
                    # 查找该订单的所有效果图文件
                    import glob
                    pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                    effect_files = glob.glob(pattern)
                    effect_files.sort(key=os.path.getmtime, reverse=True)
                    
                    if effect_files and not main_image_path:
                        # 使用第一张文件作为主图
                        main_image_path = os.path.basename(effect_files[0])
            except Exception as e:
                print(f"从文件系统获取效果图失败: {e}")
        
        if not main_image_path:
            return jsonify({'success': False, 'message': '选中的效果图不存在'}), 400
        
        # 创建商城订单（如果ShopOrder模型存在）
        if ShopOrder:
            import time
            created_orders = []
            
            # 新版本：为每张关联了产品的照片创建订单（支持每张照片关联多个产品）
            if image_product_mappings:
                for mapping_key, mapping in image_product_mappings.items():
                    try:
                        image_id = int(mapping_key)
                    except (ValueError, TypeError):
                        continue
                    
                    # 支持新格式：mapping是产品列表（数组）
                    if isinstance(mapping, list):
                        # 新格式：一个图片关联多个产品
                        for product_mapping in mapping:
                            product_id = product_mapping.get('product_id')
                            size_id = product_mapping.get('size_id')
                            quantity = product_mapping.get('quantity', 1)
                            
                            if not product_id or size_id is None:
                                continue
                            
                            shop_product = ShopProduct.query.get(product_id)
                            shop_size = ShopProductSize.query.get(size_id) if size_id > 0 else None
                            
                            if not shop_product or not shop_size:
                                continue
                            
                            # 获取该图片的路径
                            image_path = None
                            if image_id != 0:
                                task = AITask.query.filter_by(id=image_id, order_id=order_id).first()
                                if task and task.output_image_path:
                                    image_path = task.output_image_path
                                    print(f"选片提交 - 从AITask获取图片路径: {image_path} (task_id={image_id})")
                            
                            # 如果没找到，使用main_image_path作为后备
                            if not image_path:
                                image_path = main_image_path
                                print(f"选片提交 - 使用main_image_path: {image_path}")
                            
                            # 如果还是没有，跳过这个订单
                            if not image_path:
                                print(f"选片提交 - 警告: 无法获取图片路径，跳过订单创建 (image_id={image_id})")
                                continue
                            
                            # 创建一个订单，quantity设置为用户选择的数量
                            # 生成商城订单号
                            shop_order_number = f"SHOP{int(time.time() * 1000) + len(created_orders)}"
                            
                            # 计算价格
                            size_price = float(shop_size.price)
                            total_price = size_price * quantity
                            
                            # 创建商城订单
                            shop_order = ShopOrder(
                                order_number=shop_order_number,
                                original_order_id=order.id,
                                original_order_number=order.order_number,
                                customer_name=order.customer_name or '',
                                customer_phone=order.customer_phone or '',
                                openid=order.openid,
                                customer_address=order.customer_address or '',
                                product_id=shop_product.id,
                                product_name=shop_product.name,
                                size_id=shop_size.id,
                                size_name=shop_size.size_name,
                                image_url=image_path,
                                quantity=quantity,  # 使用用户选择的数量
                                price=size_price,
                                total_price=total_price,  # 总价 = 单价 × 数量
                                status='pending',  # 待支付
                                customer_note=f"选片订单，照片ID: {image_id}, 产品: {shop_product.name}"
                            )
                            
                            db.session.add(shop_order)
                            created_orders.append(shop_order_number)
                            print(f"选片提交 - 创建商城订单: {shop_order_number}, 产品: {shop_product.name}, 数量: {quantity}, 总价: {total_price}")
                    
                    # 支持旧格式：mapping是单个对象
                    elif isinstance(mapping, dict):
                        if 'imageId' in mapping:
                            # 新格式：mapping中包含imageId字段
                            image_id = mapping.get('imageId')
                            product_id = mapping.get('productId')
                            size_id = mapping.get('sizeId')
                        else:
                            # 旧格式：mapping_key就是image_id
                            product_id = mapping.get('productId') or mapping.get('product_id')
                            size_id = mapping.get('sizeId') or mapping.get('size_id')
                        
                        if not product_id or size_id is None:
                            continue
                        
                        shop_product = ShopProduct.query.get(product_id)
                        shop_size = ShopProductSize.query.get(size_id) if size_id > 0 else None
                        
                        if not shop_product or not shop_size:
                            continue
                        
                        # 获取该图片的路径
                        image_path = None
                        if image_id != 0:
                            task = AITask.query.filter_by(id=image_id, order_id=order_id).first()
                            if task and task.output_image_path:
                                image_path = task.output_image_path
                                print(f"选片提交 - 从AITask获取图片路径: {image_path} (task_id={image_id})")
                        
                        # 如果没找到，使用main_image_path作为后备
                        if not image_path:
                            image_path = main_image_path
                            print(f"选片提交 - 使用main_image_path: {image_path}")
                        
                        # 如果还是没有，跳过这个订单
                        if not image_path:
                            print(f"选片提交 - 警告: 无法获取图片路径，跳过订单创建 (image_id={image_id})")
                            continue
                        
                        # 生成商城订单号
                        shop_order_number = f"SHOP{int(time.time() * 1000) + len(created_orders)}"
                        
                        # 计算价格
                        size_price = float(shop_size.price)
                        
                        # 创建商城订单
                        shop_order = ShopOrder(
                            order_number=shop_order_number,
                            original_order_id=order.id,
                            original_order_number=order.order_number,
                            customer_name=order.customer_name or '',
                            customer_phone=order.customer_phone or '',
                            openid=order.openid,
                            customer_address=order.customer_address or '',
                            product_id=shop_product.id,
                            product_name=shop_product.name,
                            size_id=shop_size.id,
                            size_name=shop_size.size_name,
                            image_url=image_path,
                            quantity=1,
                            price=size_price,
                            total_price=size_price,
                            status='pending',  # 待支付
                            customer_note=f"选片订单，照片ID: {image_id}, 产品: {shop_product.name}"
                        )
                        
                        db.session.add(shop_order)
                        created_orders.append(shop_order_number)
            # 旧版本兼容：使用统一的产品和规格
            elif selected_product_id and selected_size_id:
                shop_product = ShopProduct.query.get(selected_product_id)
                shop_size = ShopProductSize.query.get(selected_size_id)
                
                if not shop_product or not shop_size:
                    return jsonify({'success': False, 'message': '产品或规格不存在'}), 400
                
                # 获取图片路径（使用第一张选中的图片）
                image_path = main_image_path
                if not image_path:
                    return jsonify({'success': False, 'message': '无法获取效果图路径'}), 400
                
                # 计算总价（产品价格 + 超出费用）
                total_price = float(shop_size.price) + extra_fee
                
                # 生成商城订单号
                shop_order_number = f"SHOP{int(time.time() * 1000)}"
                
                # 创建商城订单
                shop_order = ShopOrder(
                    order_number=shop_order_number,
                    original_order_id=order.id,
                    original_order_number=order.order_number,
                    customer_name=order.customer_name or '',
                    customer_phone=order.customer_phone or '',
                    openid=order.openid,
                    customer_address=order.customer_address or '',
                    product_id=shop_product.id,
                    product_name=shop_product.name,
                    size_id=shop_size.id,
                    size_name=shop_size.size_name,
                    image_url=image_path,  # 使用上面获取的image_path
                    quantity=1,
                    price=float(shop_size.price),
                    total_price=total_price,
                    status='pending',
                    customer_note=f"选片订单，选中{len(selected_image_ids)}张照片，免费{free_selection_count}张，超出{extra_count}张"
                )
                
                db.session.add(shop_order)
                created_orders.append(shop_order_number)
            
            db.session.commit()
            
            # 更新原订单的选片状态（添加备注）
            if hasattr(order, 'customer_note'):
                current_note = order.customer_note or ''
                selection_note = f"已选片：{len(selected_image_ids)}张，创建商城订单：{', '.join(created_orders)}"
                if current_note:
                    order.customer_note = f"{current_note}\n{selection_note}"
                else:
                    order.customer_note = selection_note
            
            # 更新订单状态为"选片已完成"
            # 如果订单状态是pending_selection、ai_processing或其他处理中状态，更新为selection_completed
            if order.status in ['pending_selection', 'ai_processing', 'completed', 'hd_ready', 'processing', 'manufacturing']:
                order.status = 'selection_completed'  # 选片已完成
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'选片成功，已创建{len(created_orders)}个商城订单',
                'selected_count': len(selected_image_ids),
                'free_count': free_selection_count,
                'extra_count': extra_count,
                'extra_fee': extra_fee,
                'created_orders': created_orders,
                'total_price': sum([float(ShopProductSize.query.get(so.size_id).price) * so.quantity 
                                   for so in ShopOrder.query.filter(ShopOrder.order_number.in_(created_orders)).all() 
                                   if so.size_id])
            })
        else:
            # 如果ShopOrder模型不存在，只返回选片信息
            # 更新原订单的选片状态
            if hasattr(order, 'customer_note'):
                current_note = order.customer_note or ''
                selection_note = f"已选片：{len(selected_image_ids)}张"
                if current_note:
                    order.customer_note = f"{current_note}\n{selection_note}"
                else:
                    order.customer_note = selection_note
            
            # 更新订单状态为"选片已完成"
            if order.status in ['completed', 'hd_ready', 'processing', 'manufacturing']:
                order.status = 'selection_completed'  # 选片已完成
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '选片成功',
                'selected_count': len(selected_image_ids),
                'free_count': free_selection_count,
                'extra_count': extra_count,
                'extra_fee': extra_fee,
                'note': '商城订单功能未启用'
            })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"提交选片结果失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>/confirm')
@login_required
def photo_selection_confirm(order_id):
    """确认选片页面 - 选择产品和数量"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('photo_selection.photo_selection_list'))
    
    Order = models['Order']
    AITask = models['AITask']
    ShopProduct = models['ShopProduct']
    ShopProductSize = models['ShopProductSize']
    
    order = Order.query.get_or_404(order_id)
    
    # 获取选中的图片ID（从URL参数）
    selected_image_ids_str = request.args.get('images', '')
    if not selected_image_ids_str:
        flash('请先选择照片', 'error')
        return redirect(url_for('photo_selection.photo_selection_detail', order_id=order_id))
    
    selected_image_ids = [int(id) for id in selected_image_ids_str.split(',') if id.isdigit()]
    if not selected_image_ids:
        flash('请先选择照片', 'error')
        return redirect(url_for('photo_selection.photo_selection_detail', order_id=order_id))
    
    # 获取应用实例
    from flask import current_app
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    # 获取选中的效果图
    effect_images = []
    task_ids = [img_id for img_id in selected_image_ids if img_id != 0]
    file_system_images = [img_id for img_id in selected_image_ids if img_id == 0]
    
    # 从AITask获取效果图
    if task_ids:
        selected_tasks = AITask.query.filter(
            AITask.id.in_(task_ids),
            AITask.order_id == order_id
        ).all()
        
        for task in selected_tasks:
            if task.output_image_path:
                print(f"🔍 [确认选片] 处理任务 {task.id}, output_image_path: {task.output_image_path}")
                
                hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
                final_folder = app.config.get('FINAL_FOLDER', os.path.join(app.root_path, 'final_works'))
                if not os.path.isabs(hd_folder):
                    hd_folder = os.path.join(app.root_path, hd_folder)
                if not os.path.isabs(final_folder):
                    final_folder = os.path.join(app.root_path, final_folder)
                
                # 检查是否是缩略图路径
                from app.utils.image_thumbnail import get_original_path, get_thumbnail_path
                original_path = get_original_path(task.output_image_path)
                thumbnail_path = get_thumbnail_path(original_path)
                
                # 尝试多个路径：原图、缩略图
                image_path = None
                image_filename = None
                
                # 1. 检查原图是否存在
                original_file = os.path.basename(original_path)
                if os.path.exists(os.path.join(hd_folder, original_file)):
                    image_path = os.path.join(hd_folder, original_file)
                    image_filename = original_file
                elif os.path.exists(os.path.join(final_folder, original_file)):
                    image_path = os.path.join(final_folder, original_file)
                    image_filename = original_file
                # 2. 检查缩略图是否存在
                elif task.output_image_path.endswith('_thumb.jpg'):
                    thumb_file = os.path.basename(task.output_image_path)
                    if os.path.exists(os.path.join(hd_folder, thumb_file)):
                        image_path = os.path.join(hd_folder, thumb_file)
                        image_filename = thumb_file
                    elif os.path.exists(os.path.join(final_folder, thumb_file)):
                        image_path = os.path.join(final_folder, thumb_file)
                        image_filename = thumb_file
                # 3. 直接使用output_image_path
                else:
                    direct_file = os.path.basename(task.output_image_path)
                    if os.path.exists(os.path.join(hd_folder, direct_file)):
                        image_path = os.path.join(hd_folder, direct_file)
                        image_filename = direct_file
                    elif os.path.exists(os.path.join(final_folder, direct_file)):
                        image_path = os.path.join(final_folder, direct_file)
                        image_filename = direct_file
                
                if image_path and image_filename:
                    from urllib.parse import quote
                    # 优先使用缩略图URL（如果存在）
                    thumbnail_filename = get_thumbnail_path(image_filename)
                    if thumbnail_filename and os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                        encoded_filename = quote(thumbnail_filename, safe='')
                        image_url = f"/public/hd/{encoded_filename}"
                        print(f"✅ [确认选片] 使用缩略图: {thumbnail_filename}")
                    else:
                        encoded_filename = quote(image_filename, safe='')
                        image_url = f"/public/hd/{encoded_filename}"
                        print(f"✅ [确认选片] 使用原图: {image_filename}")
                    
                    effect_images.append({
                        'id': task.id,
                        'url': image_url,
                        'path': image_filename
                    })
                    print(f"✅ [确认选片] 添加效果图: task_id={task.id}, url={image_url}")
                else:
                    print(f"⚠️ [确认选片] 图片文件不存在: {task.output_image_path} (在HD_FOLDER和FINAL_FOLDER中均未找到)")
                    # 即使文件不存在，也添加（可能是云端文件，通过URL访问）
                    from urllib.parse import quote
                    encoded_filename = quote(os.path.basename(task.output_image_path), safe='')
                    image_url = f"/public/hd/{encoded_filename}"
                    effect_images.append({
                        'id': task.id,
                        'url': image_url,
                        'path': os.path.basename(task.output_image_path)
                    })
                    print(f"⚠️ [确认选片] 添加效果图（文件不存在，可能是云端）: task_id={task.id}, url={image_url}")
    
    # 从文件系统获取效果图
    if file_system_images or (not task_ids and selected_image_ids):
        try:
            hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)
            
            if os.path.exists(hd_folder):
                import glob
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                effect_files = glob.glob(pattern)
                effect_files.sort(key=os.path.getmtime, reverse=True)
                
                for filepath in effect_files[:len(selected_image_ids)]:
                    filename = os.path.basename(filepath)
                    from urllib.parse import quote
                    encoded_filename = quote(filename, safe='')
                    image_url = f"/public/hd/{encoded_filename}"
                    
                    effect_images.append({
                        'id': 0,
                        'url': image_url,
                        'path': filename
                    })
        except Exception as e:
            print(f"从文件系统读取效果图失败: {e}")
    
    # 获取所有启用的商城产品（用于产品选择）
    shop_products = ShopProduct.query.filter_by(is_active=True).order_by(ShopProduct.sort_order.asc()).all()
    products_data = []
    for product in shop_products:
        sizes = ShopProductSize.query.filter_by(product_id=product.id, is_active=True).order_by(ShopProductSize.sort_order.asc()).all()
        products_data.append({
            'id': product.id,
            'name': product.name,
            'image_url': product.image_url or '',
            'sizes': [{'id': s.id, 'name': s.size_name, 'price': float(s.price)} for s in sizes]
        })
    
    # 获取产品的免费选片张数
    free_selection_count = 1  # 默认1张
    Product = models.get('Product')
    if Product and order.product_name:
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        if product and hasattr(product, 'free_selection_count'):
            free_selection_count = product.free_selection_count or 1
    
    return render_template('admin/photo_selection_confirm.html',
                         order=order,
                         effect_images=effect_images,
                         shop_products=products_data,
                         free_selection_count=free_selection_count)


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>/review')
@login_required
@admin_required
def photo_selection_review(order_id):
    """产品详情页 - 确认选片和支付"""
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('photo_selection.photo_selection_list'))
    
    Order = models['Order']
    AITask = models['AITask']
    
    order = Order.query.get_or_404(order_id)
    
    # 获取应用实例
    from flask import current_app
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    # 获取订单的所有已完成的效果图
    ai_tasks = AITask.query.filter_by(
        order_id=order.id,
        status='completed'
    ).filter(AITask.output_image_path.isnot(None)).all()
    
    # 构建效果图列表
    effect_images = []
    for task in ai_tasks:
        if task.output_image_path:
            hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)
            
            image_path = os.path.join(hd_folder, task.output_image_path)
            if os.path.exists(image_path):
                from urllib.parse import quote
                encoded_filename = quote(task.output_image_path, safe='')
                image_url = f"/public/hd/{encoded_filename}"
                
                effect_images.append({
                    'id': task.id,
                    'url': image_url,
                    'path': task.output_image_path,
                    'created_at': task.completed_at or task.created_at
                })
    
    # 如果AITask中没有效果图，尝试从文件系统读取
    if len(effect_images) == 0:
        try:
            hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app.root_path, hd_folder)
            
            if os.path.exists(hd_folder):
                import glob
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                effect_files = glob.glob(pattern)
                effect_files.sort(key=os.path.getmtime, reverse=True)
                
                for filepath in effect_files:
                    filename = os.path.basename(filepath)
                    from urllib.parse import quote
                    encoded_filename = quote(filename, safe='')
                    image_url = f"/public/hd/{encoded_filename}"
                    
                    effect_images.append({
                        'id': 0,
                        'url': image_url,
                        'path': filename,
                        'created_at': datetime.fromtimestamp(os.path.getmtime(filepath))
                    })
        except Exception as e:
            print(f"从文件系统读取效果图失败: {e}")
    
    # 获取产品的免费选片张数和额外照片价格
    free_selection_count = 1
    extra_photo_price = 10.0
    if order.product_name:
        Product = models['Product']
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
        if product:
            if hasattr(product, 'free_selection_count'):
                free_selection_count = product.free_selection_count or 1
            if hasattr(product, 'extra_photo_price'):
                extra_photo_price = product.extra_photo_price or 10.0
    
    return render_template('admin/photo_selection_review.html',
                         order=order,
                         effect_images=effect_images,
                         free_selection_count=free_selection_count,
                         extra_photo_price=extra_photo_price)


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>/check-payment', methods=['GET'])
@login_required
def check_payment_status(order_id):
    """检查支付状态"""
    if current_user.role not in ['admin', 'operator']:
        return jsonify({'paid': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'paid': False, 'message': '系统未初始化'}), 500
    
    ShopOrder = models.get('ShopOrder')
    if not ShopOrder:
        return jsonify({'paid': False, 'message': '商城订单功能未启用'}), 400
    
    try:
        order_numbers = request.args.get('orders', '').split(',')
        order_numbers = [o.strip() for o in order_numbers if o.strip()]
        
        if not order_numbers:
            return jsonify({'paid': False, 'message': '订单号不能为空'}), 400
        
        # 检查所有订单是否都已支付
        orders = ShopOrder.query.filter(ShopOrder.order_number.in_(order_numbers)).all()
        
        if len(orders) == 0:
            return jsonify({'paid': False, 'message': '订单不存在'}), 404
        
        # 检查是否所有订单都已支付
        all_paid = all(order.status == 'paid' for order in orders)
        
        return jsonify({
            'paid': all_paid,
            'orders': [{'order_number': o.order_number, 'status': o.status} for o in orders]
        })
        
    except Exception as e:
        print(f"检查支付状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'paid': False, 'message': f'检查失败: {str(e)}'}), 500


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>/skip-payment', methods=['POST'])
@login_required
@admin_required
def skip_payment(order_id):
    """跳过支付（测试模式）"""
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    ShopOrder = models.get('ShopOrder')
    if not ShopOrder:
        return jsonify({'success': False, 'message': '商城订单功能未启用'}), 400
    
    try:
        data = request.get_json()
        order_numbers = data.get('order_numbers', [])
        
        if not order_numbers:
            return jsonify({'success': False, 'message': '订单号不能为空'}), 400
        
        # 检查支付配置是否允许跳过
        from app.utils.config_loader import get_config_value
        test_mode = get_config_value('payment_test_mode', 'true', db=models['db'], AIConfig=models.get('AIConfig'))
        skip_payment_enabled = get_config_value('payment_skip_payment', 'true', db=models['db'], AIConfig=models.get('AIConfig'))
        
        if test_mode.lower() != 'true' or skip_payment_enabled.lower() != 'true':
            return jsonify({'success': False, 'message': '当前不是测试模式，无法跳过支付'}), 400
        
        # 更新订单状态为已支付
        orders = ShopOrder.query.filter(ShopOrder.order_number.in_(order_numbers)).all()
        
        if len(orders) == 0:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        from datetime import datetime
        for order in orders:
            order.status = 'paid'
            if hasattr(order, 'payment_time'):
                order.payment_time = datetime.now()
            if hasattr(order, 'transaction_id'):
                order.transaction_id = f"TEST_{int(datetime.now().timestamp())}"
        
        models['db'].session.commit()
        
        return jsonify({
            'success': True,
            'message': '支付已跳过（测试模式）',
            'orders': [o.order_number for o in orders]
        })
        
    except Exception as e:
        if 'db' in locals():
            models['db'].session.rollback()
        print(f"跳过支付失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'跳过支付失败: {str(e)}'}), 500


@photo_selection_bp.route('/admin/photo-selection/<int:order_id>/start-print', methods=['POST'])
@login_required
def start_print(order_id):
    """开始打印照片"""
    if current_user.role not in ['admin', 'operator']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    ShopOrder = models.get('ShopOrder')
    AITask = models['AITask']
    db = models['db']
    
    try:
        data = request.get_json()
        order_numbers = data.get('order_numbers', [])
        
        if not order_numbers:
            return jsonify({'success': False, 'message': '订单号不能为空'}), 400
        
        # 获取原订单
        order = Order.query.get_or_404(order_id)
        
        # 获取商城订单
        shop_orders = []
        if ShopOrder:
            shop_orders = ShopOrder.query.filter(ShopOrder.order_number.in_(order_numbers)).all()
        
        # 检查是否启用冲印系统
        try:
            from printer_config import PRINTER_SYSTEM_CONFIG
            from printer_client import PrinterSystemClient
            
            if not PRINTER_SYSTEM_CONFIG.get('enabled', False):
                return jsonify({'success': False, 'message': '冲印系统未启用'}), 400
            
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        except ImportError:
            return jsonify({'success': False, 'message': '冲印系统模块未找到'}), 500
        
        # 获取应用实例
        from flask import current_app
        import sys
        import os
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
        else:
            app = current_app
        
        # 获取高清图片文件夹
        hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(app.root_path, hd_folder)
        
        success_count = 0
        failed_count = 0
        errors = []
        
        # 根据订单获取对应的打印机配置（支持多门店）
        from app.utils.printer_config_helper import get_printer_config_for_order
        printer_config = get_printer_config_for_order(order, models)
        local_printer_path = printer_config.get('local_printer_path') or None
        local_printer_proxy_url = printer_config.get('local_printer_proxy_url') or None
        local_printer_proxy_api_key = printer_config.get('local_printer_proxy_api_key') or None
        
        print(f"订单 {order.order_number} 的打印机配置:")
        print(f"  自拍机ID: {printer_config.get('machine_id')}")
        print(f"  门店名称: {printer_config.get('store_name')}")
        print(f"  本地打印机路径: {local_printer_path}")
        print(f"  打印代理服务地址: {local_printer_proxy_url}")
        
        # 为每个商城订单发送打印任务
        for shop_order in shop_orders:
            try:
                # 获取产品信息，判断是电子照片还是实物产品
                ShopProduct = models.get('ShopProduct')
                is_digital_photo = False
                
                if ShopProduct and shop_order.product_id:
                    try:
                        product = ShopProduct.query.get(shop_order.product_id)
                        if product:
                            # 如果产品分类是 digital_photo 或电子照片相关，使用本地打印
                            category = (product.category or '').lower()
                            if category in ['digital_photo', 'photo', '电子照片', '照片']:
                                is_digital_photo = True
                    except:
                        pass
                
                # 获取图片路径（打印时使用原图，不是缩略图）
                image_path = shop_order.image_url
                if not image_path:
                    # 如果没有图片URL，尝试从AITask获取
                    if shop_order.original_order_id:
                        tasks = AITask.query.filter_by(order_id=shop_order.original_order_id, status='completed').all()
                        if tasks and tasks[0].output_image_path:
                            image_path = tasks[0].output_image_path
                
                if not image_path:
                    errors.append(f"订单 {shop_order.order_number} 没有图片路径")
                    failed_count += 1
                    continue
                
                # 如果image_path是缩略图路径，转换为原图路径
                if image_path.endswith('_thumb.jpg'):
                    from app.utils.image_thumbnail import get_original_path
                    base_name = image_path.replace('_thumb.jpg', '')
                    # 尝试常见的图片扩展名
                    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                        test_path = base_name + ext
                        test_full_path = os.path.join(hd_folder, test_path)
                        if os.path.exists(test_full_path):
                            image_path = test_path
                            print(f"✅ 打印时使用原图: {image_path} (从缩略图 {shop_order.image_url} 转换)")
                            break
                
                # 构建完整路径
                full_image_path = os.path.join(hd_folder, image_path)
                if not os.path.exists(full_image_path):
                    # 尝试其他路径
                    possible_paths = [
                        full_image_path,
                        os.path.join('hd_images', image_path),
                        os.path.join('uploads', image_path),
                        os.path.join('final_works', image_path),
                        image_path,  # 直接使用原始路径
                    ]
                    found = False
                    for path in possible_paths:
                        if os.path.exists(path):
                            full_image_path = path
                            found = True
                            break
                    
                    if not found:
                        errors.append(f"订单 {shop_order.order_number} 的图片文件不存在: {image_path}")
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
                            printer_client_proxy = LocalPrinterClient(local_printer_proxy_url, local_printer_proxy_api_key)
                            
                            # 构建图片URL（需要可公网访问）
                            from urllib.parse import quote
                            try:
                                from printer_config import PRINTER_SYSTEM_CONFIG
                                file_access_base_url = PRINTER_SYSTEM_CONFIG.get('file_access_base_url', 'http://photogooo')
                            except:
                                # 从配置表获取
                                try:
                                    AIConfig = models.get('AIConfig')
                                    if AIConfig:
                                        file_url_config = AIConfig.query.filter_by(config_key='printer_file_access_base_url').first()
                                        file_access_base_url = file_url_config.config_value if file_url_config else 'http://photogooo'
                                    else:
                                        file_access_base_url = 'http://photogooo'
                                except:
                                    file_access_base_url = 'http://photogooo'
                            
                            # 打印时使用原图，确保image_path不是缩略图
                            original_image_path = image_path
                            if image_path.endswith('_thumb.jpg'):
                                base_name = image_path.replace('_thumb.jpg', '')
                                # 尝试常见的图片扩展名
                                for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                                    test_path = base_name + ext
                                    test_full_path = os.path.join(hd_folder, test_path)
                                    if os.path.exists(test_full_path):
                                        original_image_path = test_path
                                        print(f"✅ 打印代理使用原图: {original_image_path} (从缩略图 {image_path} 转换)")
                                        break
                            
                            encoded_filename = quote(original_image_path, safe='')
                            image_url = f"{file_access_base_url}/public/hd/original/{encoded_filename}"
                            
                            result = printer_client_proxy.print_image(
                                image_url=image_url,
                                copies=shop_order.quantity or 1
                            )
                        elif local_printer_path:
                            # 直接使用本地打印机（本地部署）
                            from local_printer import LocalPrinter
                            local_printer = LocalPrinter(local_printer_path)
                            result = local_printer.print_image(full_image_path, copies=shop_order.quantity or 1)
                        else:
                            # 没有配置本地打印机
                            result = {
                                'success': False,
                                'message': '未配置本地打印机或打印代理服务'
                            }
                        
                        if result.get('success'):
                            success_count += 1
                            if hasattr(shop_order, 'status'):
                                shop_order.status = 'printing'  # 打印中
                            
                            # 更新原订单状态为"打印中"（如果当前状态是selection_completed）
                            if order.status == 'selection_completed':
                                order.status = 'printing'  # 打印中
                        else:
                            failed_count += 1
                            error_msg = result.get('message', '本地打印失败')
                            errors.append(f"订单 {shop_order.order_number} 本地打印失败: {error_msg}")
                    except ImportError:
                        # 如果本地打印模块不可用，回退到远程API
                        errors.append(f"订单 {shop_order.order_number} 本地打印模块未找到，使用远程API")
                        is_digital_photo = False
                    except Exception as e:
                        failed_count += 1
                        error_msg = f'本地打印失败: {str(e)}'
                        errors.append(f"订单 {shop_order.order_number} {error_msg}")
                        print(f"本地打印失败: {e}")
                        import traceback
                        traceback.print_exc()
                
                if not is_digital_photo or not local_printer_path:
                    # 实物产品：发送到远程冲印系统
                    result = printer_client.send_order_to_printer(shop_order, full_image_path, order_obj=shop_order)
                    
                    if result.get('success'):
                        success_count += 1
                        # 更新商城订单状态
                        if hasattr(shop_order, 'status'):
                            shop_order.status = 'printing'  # 打印中
                        
                        # 更新原订单状态为"打印中"（如果当前状态是selection_completed）
                        if order.status == 'selection_completed':
                            order.status = 'printing'  # 打印中
                        if hasattr(shop_order, 'status'):
                            shop_order.status = 'printing'  # 打印中
                    else:
                        failed_count += 1
                        error_msg = result.get('message', '未知错误')
                        errors.append(f"订单 {shop_order.order_number} 打印失败: {error_msg}")
            
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                errors.append(f"订单 {shop_order.order_number} 处理失败: {error_msg}")
                print(f"处理订单 {shop_order.order_number} 时发生错误: {e}")
                import traceback
                traceback.print_exc()
        
        db.session.commit()
        
        if success_count > 0:
            message = f'成功启动 {success_count} 个打印任务'
            if failed_count > 0:
                message += f'，{failed_count} 个失败'
            return jsonify({
                'success': True,
                'message': message,
                'success_count': success_count,
                'failed_count': failed_count,
                'errors': errors
            })
        else:
            return jsonify({
                'success': False,
                'message': '所有打印任务都失败了',
                'errors': errors
            }), 400
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"启动打印失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'启动打印失败: {str(e)}'}), 500


@photo_selection_bp.route('/admin/photo-selection/generate-qrcode', methods=['POST'])
def generate_selection_qrcode():
    """生成选片登录二维码"""
    try:
        from flask import session
        from flask_login import current_user
        
        # 检查用户权限：加盟商或管理员
        session_franchisee_id = session.get('franchisee_id')
        
        if not session_franchisee_id and (not current_user.is_authenticated or current_user.role not in ['admin', 'operator']):
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 获取加盟商ID（如果是加盟商登录，使用session中的ID；如果是管理员，从请求参数获取）
        data = request.get_json() or {}
        franchisee_id = session_franchisee_id or data.get('franchisee_id')
        
        if not franchisee_id:
            return jsonify({'success': False, 'message': '缺少加盟商ID'}), 400
        
        # 生成临时token（有效期5分钟）
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=5)
        
        _selection_tokens[token] = {
            'franchisee_id': franchisee_id,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'used': False
        }
        
        # 清理过期的token
        current_time = datetime.now()
        expired_tokens = [k for k, v in _selection_tokens.items() if v['expires_at'] < current_time]
        for expired_token in expired_tokens:
            del _selection_tokens[expired_token]
        
        # 使用微信小程序码API生成小程序码（推荐方式）
        # 获取微信access_token
        from app.routes.qrcode_api import get_access_token
        access_token = get_access_token()
        
        if access_token:
            try:
                # 使用微信小程序码API
                import requests
                url = f'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}'
                
                # 构建参数：scene参数使用短格式（微信限制32字符）
                # 使用短格式：st=token的前16个字符（去掉连字符）
                # 例如：st=44199906ed1849f0 (16字符) 或 st=44199906ed1849f0 (16字符)
                short_token = token.replace('-', '')[:16]  # 去掉连字符，取前16个字符
                scene = f'st={short_token}'  # st=selection_token的缩写
                
                # 验证长度
                if len(scene) > 32:
                    # 如果还是太长，进一步缩短
                    short_token = token.replace('-', '')[:12]
                    scene = f'st={short_token}'
                
                print(f"调用微信小程序码API生成二维码，scene: {scene} (长度: {len(scene)}字符)")
                print(f"完整token: {token} (将映射到短token: {short_token})")
                
                # 存储短token到完整token的映射（用于验证时查找）
                _short_token_map[short_token] = token
                
                # 尝试不同的环境版本和页面路径
                # 先尝试体验版（trial），如果失败再尝试正式版（release）
                # 如果指定页面失败，可以尝试使用首页（index）
                attempts = [
                    {'page': 'pages/orders/orders', 'env_version': 'trial'},  # 体验版
                    {'page': 'pages/index/index', 'env_version': 'trial'},   # 体验版首页
                    {'page': 'pages/orders/orders', 'env_version': 'release'},  # 正式版
                    {'page': 'pages/index/index', 'env_version': 'release'},   # 正式版首页
                ]
                
                response = None
                last_error = None
                success = False
                
                for attempt in attempts:
                    params = {
                        'scene': scene,
                        'page': attempt['page'],
                        'env_version': attempt['env_version'],
                        'width': 300,
                        'auto_color': False,
                        'line_color': {"r": 0, "g": 0, "b": 0}
                    }
                    
                    print(f"尝试生成小程序码: page={attempt['page']}, env_version={attempt['env_version']}, scene={params['scene']}")
                    try:
                        response = requests.post(url, json=params, timeout=(10, 30))
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            
                            if 'application/json' in content_type:
                                # 如果返回JSON，说明有错误
                                error_data = response.json()
                                print(f"⚠️ 尝试失败: {error_data.get('errmsg', '未知错误')}")
                                last_error = error_data.get('errmsg', '未知错误')
                                continue  # 尝试下一个配置
                            else:
                                # 成功生成图片
                                print(f"✅ 使用配置成功生成: page={attempt['page']}, env_version={attempt['env_version']}")
                                success = True
                                break  # 成功，退出循环
                    except Exception as e:
                        print(f"⚠️ 请求异常: {str(e)}")
                        last_error = str(e)
                        continue
                
                if not success:
                    # 所有尝试都失败，抛出异常
                    raise Exception(f'生成小程序码失败: {last_error or "所有配置尝试均失败"}')
                
                # 如果成功，response已经在循环中设置
                # 转换为base64
                img_base64 = base64.b64encode(response.content).decode('utf-8')
                print("✅ 使用微信小程序码API生成成功")
                    
            except Exception as e:
                print(f"⚠️ 使用微信小程序码API失败，回退到普通二维码: {e}")
                # 回退到普通二维码
                # 构建小程序页面路径（用于普通二维码）
                qrcode_content = f"pages/orders/orders?selection_token={token}"
                
                # 生成二维码图片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qrcode_content)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                
                # 转换为base64
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        else:
            # 如果没有access_token，使用普通二维码
            print("⚠️ 无法获取access_token，使用普通二维码")
            qrcode_content = f"pages/orders/orders?selection_token={token}"
            
            # 生成二维码图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qrcode_content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # 转换为base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'token': token,
            'qrcode': f"data:image/png;base64,{img_base64}",
            'expires_at': expires_at.isoformat(),
            'qrcode_content': qrcode_content
        })
        
    except Exception as e:
        print(f"生成选片二维码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'生成二维码失败: {str(e)}'}), 500


@photo_selection_bp.route('/api/photo-selection/verify-token', methods=['POST'])
def verify_selection_token():
    """验证选片登录token"""
    try:
        data = request.get_json()
        token = data.get('token')
        openid = data.get('openid')  # 小程序用户的openid
        
        if not token:
            return jsonify({'success': False, 'message': '缺少token'}), 400
        
        # 严格检查openid，不允许匿名用户
        if not openid or openid == 'anonymous' or len(openid) < 10:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        # 检查token是否存在且未过期
        # 支持短token格式（从scene参数中解析的短token）
        full_token = token
        # 如果是短token，查找对应的完整token
        if token in _short_token_map:
            full_token = _short_token_map[token]
            print(f"✅ 短token映射: {token} -> {full_token}")
        
        if full_token not in _selection_tokens:
            return jsonify({'success': False, 'message': 'token不存在或已过期'}), 400
        
        token_info = _selection_tokens[full_token]
        
        # 检查是否已使用
        if token_info.get('used'):
            return jsonify({'success': False, 'message': 'token已使用'}), 400
        
        # 检查是否过期
        if token_info['expires_at'] < datetime.now():
            del _selection_tokens[full_token]
            # 同时删除短token映射
            if token in _short_token_map:
                del _short_token_map[token]
            return jsonify({'success': False, 'message': 'token已过期'}), 400
        
        # 获取加盟商ID
        franchisee_id = token_info['franchisee_id']
        
        # 获取该加盟商的所有订单（通过openid匹配）
        models = get_models(['Order'])
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        
        # 查询该用户的订单（通过openid匹配，且属于该加盟商）
        orders = Order.query.filter(
            Order.openid == openid,
            Order.franchisee_id == franchisee_id,
            Order.status != 'unpaid'
        ).order_by(Order.created_at.desc()).all()
        
        # 标记token为已使用
        token_info['used'] = True
        token_info['used_at'] = datetime.now()
        token_info['used_by_openid'] = openid
        
        # 同时删除短token映射（一次性使用）
        if token in _short_token_map:
            del _short_token_map[token]
        
        # 构建订单列表数据
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name or '',
                'customer_phone': order.customer_phone or '',
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None
            })
        
        return jsonify({
            'success': True,
            'franchisee_id': franchisee_id,
            'orders': orders_data,
            'message': '验证成功'
        })
        
    except Exception as e:
        print(f"验证选片token失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500


@photo_selection_bp.route('/api/photo-selection/search-orders', methods=['POST'])
def search_orders_for_selection():
    """通过手机号或订单号查询订单（用于选片）"""
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        order_number = data.get('order_number', '').strip()
        franchisee_id = data.get('franchisee_id')
        
        if not phone and not order_number:
            return jsonify({'success': False, 'message': '请提供手机号或订单号'}), 400
        
        if not franchisee_id:
            return jsonify({'success': False, 'message': '缺少加盟商ID'}), 400
        
        models = get_models(['Order'])
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        
        # 构建查询条件
        query = Order.query.filter(
            Order.franchisee_id == franchisee_id,
            Order.status != 'unpaid'
        )
        
        # 根据手机号或订单号查询
        if phone:
            # 验证手机号格式
            if not phone.isdigit() or len(phone) != 11:
                return jsonify({'success': False, 'message': '手机号格式不正确（应为11位数字）'}), 400
            query = query.filter(Order.customer_phone == phone)
        
        if order_number:
            query = query.filter(Order.order_number.like(f'%{order_number}%'))
        
        # 查询订单
        orders = query.order_by(Order.created_at.desc()).limit(50).all()  # 最多返回50条
        
        if not orders:
            return jsonify({
                'success': False,
                'message': '未找到符合条件的订单'
            }), 404
        
        # 构建订单列表数据
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name or '',
                'customer_phone': order.customer_phone or '',
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None
            })
        
        return jsonify({
            'success': True,
            'franchisee_id': franchisee_id,
            'orders': orders_data,
            'count': len(orders_data),
            'message': f'找到 {len(orders_data)} 个订单'
        })
        
    except Exception as e:
        print(f"查询订单失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500
