# -*- coding: utf-8 -*-
"""
小程序商城相关路由
"""
from flask import Blueprint, request, jsonify, current_app
from app.routes.miniprogram.common import get_models, get_helper_functions
import sys

# 创建商城相关的子蓝图
bp = Blueprint('shop', __name__)


@bp.route('/shop/products', methods=['GET'])
def miniprogram_get_shop_products():
    """获取商城产品列表"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        # 检查商城模型是否存在
        if 'ShopProduct' not in models:
            return jsonify({'status': 'error', 'message': '商城模型未初始化，请运行创建商城表.py脚本创建数据库表'}), 500
        
        ShopProduct = models['ShopProduct']
        ShopProductImage = models['ShopProductImage']
        ShopProductSize = models['ShopProductSize']
        get_base_url = helpers['get_base_url']
        
        # 获取启用的产品（兼容布尔值和整数）
        # SQLite可能将布尔值存储为整数，所以同时查询True和1
        from sqlalchemy import or_
        products = ShopProduct.query.filter(
            or_(ShopProduct.is_active == True, ShopProduct.is_active == 1)
        ).order_by(
            ShopProduct.sort_order.asc(), ShopProduct.id.asc()
        ).all()
        
        print(f"DEBUG: 查询到 {len(products)} 个启用的产品")
        if len(products) == 0:
            # 如果查询结果为空，查询所有产品看看
            all_products = ShopProduct.query.all()
            print(f"DEBUG: 数据库中共有 {len(all_products)} 个产品")
            for p in all_products:
                print(f"DEBUG: 产品ID={p.id}, 名称={p.name}, is_active={p.is_active} (类型: {type(p.is_active).__name__})")
        
        result = []
        for product in products:
            # 获取产品图片
            images = ShopProductImage.query.filter_by(
                product_id=product.id, is_active=True
            ).order_by(ShopProductImage.sort_order.asc()).all()
            
            # 获取产品规格
            sizes = ShopProductSize.query.filter_by(
                product_id=product.id, is_active=True
            ).order_by(ShopProductSize.sort_order.asc()).all()
            
            # 构建图片URL列表（转换为完整URL）
            image_urls = []
            base_url = get_base_url()
            if product.image_url:
                # 如果是相对路径，转换为完整URL
                if product.image_url.startswith('/'):
                    image_url = f"{base_url}{product.image_url}"
                elif not product.image_url.startswith('http'):
                    image_url = f"{base_url}/{product.image_url}"
                else:
                    image_url = product.image_url
                image_urls.append(image_url)
            for img in images:
                if img.image_url:
                    # 如果是相对路径，转换为完整URL
                    if img.image_url.startswith('/'):
                        img_url = f"{base_url}{img.image_url}"
                    elif not img.image_url.startswith('http'):
                        img_url = f"{base_url}/{img.image_url}"
                    else:
                        img_url = img.image_url
                    image_urls.append(img_url)
            
            # 构建规格列表
            sizes_list = []
            for size in sizes:
                sizes_list.append({
                    'id': size.id,
                    'size_name': size.size_name,
                    'price': float(size.price),
                    'stock': size.stock
                })
            
            # 处理主图URL（转换为完整URL）
            main_image = ''
            if product.image_url:
                if product.image_url.startswith('/'):
                    main_image = f"{base_url}{product.image_url}"
                elif not product.image_url.startswith('http'):
                    main_image = f"{base_url}/{product.image_url}"
                else:
                    main_image = product.image_url
            
            result.append({
                'id': product.id,
                'code': product.code,
                'name': product.name,
                'description': product.description or '',
                'category': product.category or '',
                'image': main_image,
                'images': image_urls,
                'sizes': sizes_list
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except KeyError as e:
        print(f"获取商城产品列表失败: 模型未找到 - {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'商城模型未初始化，请确保数据库表已创建'}), 500
    except Exception as e:
        print(f"获取商城产品列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取产品列表失败: {str(e)}'}), 500


@bp.route('/shop/products/<int:product_id>', methods=['GET'])
def miniprogram_get_shop_product_detail(product_id):
    """获取商城产品详情"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        # 检查商城模型是否存在
        if 'ShopProduct' not in models:
            return jsonify({'status': 'error', 'message': '商城模型未初始化，请运行创建商城表.py脚本创建数据库表'}), 500
        
        ShopProduct = models['ShopProduct']
        ShopProductImage = models['ShopProductImage']
        ShopProductSize = models['ShopProductSize']
        get_base_url = helpers['get_base_url']
        
        product = ShopProduct.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({'status': 'error', 'message': '产品不存在'}), 404
        
        # 获取产品图片
        images = ShopProductImage.query.filter_by(
            product_id=product.id, is_active=True
        ).order_by(ShopProductImage.sort_order.asc()).all()
        
        # 获取产品规格
        sizes = ShopProductSize.query.filter_by(
            product_id=product.id, is_active=True
        ).order_by(ShopProductSize.sort_order.asc()).all()
        
        # 构建图片URL列表（转换为完整URL）
        image_urls = []
        base_url = get_base_url()
        if product.image_url:
            # 如果是相对路径，转换为完整URL
            if product.image_url.startswith('/'):
                img_url = f"{base_url}{product.image_url}"
            elif not product.image_url.startswith('http'):
                img_url = f"{base_url}/{product.image_url}"
            else:
                img_url = product.image_url
            image_urls.append(img_url)
        for img in images:
            if img.image_url:
                # 如果是相对路径，转换为完整URL
                if img.image_url.startswith('/'):
                    img_url = f"{base_url}{img.image_url}"
                elif not img.image_url.startswith('http'):
                    img_url = f"{base_url}/{img.image_url}"
                else:
                    img_url = img.image_url
                image_urls.append(img_url)
        
        # 构建规格列表
        sizes_list = []
        for size in sizes:
            sizes_list.append({
                'id': size.id,
                'size_name': size.size_name,
                'price': float(size.price),
                'stock': size.stock
            })
        
        # 处理主图URL（转换为完整URL）
        main_image = ''
        if product.image_url:
            if product.image_url.startswith('/'):
                main_image = f"{base_url}{product.image_url}"
            elif not product.image_url.startswith('http'):
                main_image = f"{base_url}/{product.image_url}"
            else:
                main_image = product.image_url
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': product.id,
                'code': product.code,
                'name': product.name,
                'description': product.description or '',
                'category': product.category or '',
                'image': main_image,
                'images': image_urls,
                'sizes': sizes_list
            }
        })
        
    except Exception as e:
        print(f"获取商城产品详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取产品详情失败: {str(e)}'}), 500


@bp.route('/shop/orders', methods=['POST'])
def miniprogram_create_shop_order():
    """创建商城订单"""
    try:
        data = request.get_json()
        print(f"收到商城订单数据: {data}")
        
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        # 检查商城模型是否存在
        if 'ShopProduct' not in models:
            return jsonify({'status': 'error', 'message': '商城模型未初始化，请运行创建商城表.py脚本创建数据库表'}), 500
        
        db = models['db']
        ShopProduct = models['ShopProduct']
        ShopProductSize = models['ShopProductSize']
        ShopOrder = models['ShopOrder']
        Order = models['Order']
        
        # 验证必填字段
        required_fields = ['product_id', 'size_id', 'quantity', 'customer_name', 'customer_phone', 'customer_address']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'status': 'error', 'message': f'缺少必填字段: {field}'}), 400
        
        # 验证产品
        product = ShopProduct.query.filter_by(id=data['product_id'], is_active=True).first()
        if not product:
            return jsonify({'status': 'error', 'message': '产品不存在或已下架'}), 404
        
        # 验证规格
        size = ShopProductSize.query.filter_by(id=data['size_id'], product_id=data['product_id'], is_active=True).first()
        if not size:
            return jsonify({'status': 'error', 'message': '产品规格不存在'}), 404
        
        # 验证库存
        if size.stock > 0 and data['quantity'] > size.stock:
            return jsonify({'status': 'error', 'message': f'库存不足，当前库存: {size.stock}'}), 400
        
        # 验证原始订单（如果提供）
        original_order = None
        if data.get('original_order_id'):
            original_order = Order.query.get(data['original_order_id'])
            if not original_order:
                return jsonify({'status': 'error', 'message': '原始订单不存在'}), 404
        
        # 计算价格
        quantity = int(data['quantity'])
        price = float(size.price)
        total_price = price * quantity
        
        # 生成订单号
        import time
        order_number = f"SHOP{int(time.time() * 1000)}{random.randint(1000, 9999)}"
        
        # 创建订单
        new_order = ShopOrder(
            order_number=order_number,
            original_order_id=original_order.id if original_order else None,
            original_order_number=original_order.order_number if original_order else None,
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            openid=data.get('openid'),
            customer_address=data['customer_address'],
            product_id=product.id,
            product_name=product.name,
            size_id=size.id,
            size_name=size.size_name,
            image_url=data.get('image_url'),  # 使用的图片URL（来自原始订单）
            quantity=quantity,
            price=price,
            total_price=total_price,
            status='pending',
            customer_note=data.get('customer_note', '')
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # 更新库存（如果有限制）
        if size.stock > 0:
            size.stock -= quantity
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '订单创建成功',
            'data': {
                'order_id': new_order.id,
                'order_number': new_order.order_number,
                'total_price': float(new_order.total_price)
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                test_server_module.db.session.rollback()
        print(f"创建商城订单失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'创建订单失败: {str(e)}'}), 500


@bp.route('/shop/orders', methods=['GET'])
def miniprogram_get_shop_orders():
    """获取用户的商城订单列表"""
    try:
        openid = request.args.get('openid')
        if not openid:
            return jsonify({'status': 'error', 'message': '缺少openid参数'}), 400
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        # 检查商城模型是否存在
        if 'ShopOrder' not in models:
            return jsonify({'status': 'error', 'message': '商城模型未初始化，请运行创建商城表.py脚本创建数据库表'}), 500
        
        ShopOrder = models['ShopOrder']
        
        # 获取用户的订单
        orders = ShopOrder.query.filter_by(openid=openid).order_by(
            ShopOrder.created_at.desc()
        ).all()
        
        result = []
        for order in orders:
            result.append({
                'id': order.id,
                'order_number': order.order_number,
                'product_name': order.product_name,
                'size_name': order.size_name,
                'quantity': order.quantity,
                'total_price': float(order.total_price),
                'status': order.status,
                'status_text': _get_status_text(order.status),
                'image_url': order.image_url or '',
                'created_at': order.created_at.isoformat() if order.created_at else '',
                'original_order_number': order.original_order_number or ''
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取商城订单列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取订单列表失败: {str(e)}'}), 500


def _get_status_text(status):
    """获取订单状态文本"""
    status_map = {
        'pending': '待支付',
        'paid': '已支付',
        'processing': '处理中',
        'shipped': '已发货',
        'completed': '已完成',
        'cancelled': '已取消'
    }
    return status_map.get(status, status)


import random
