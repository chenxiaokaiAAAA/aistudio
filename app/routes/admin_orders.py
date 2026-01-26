# -*- coding: utf-8 -*-
"""
订单管理路由模块
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, make_response, current_app
from flask_login import login_required, current_user
from datetime import datetime
import sys
import os
import io
import csv
import json
from werkzeug.utils import secure_filename
from sqlalchemy import text

# 创建蓝图
admin_orders_bp = Blueprint('admin_orders', __name__)


@admin_orders_bp.route('/admin/orders')
@login_required
def admin_orders():
    """订单管理页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        from flask import flash
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    Order = models['Order']
    FranchiseeAccount = models['FranchiseeAccount']
    
    # 获取筛选参数
    franchisee_id = request.args.get('franchisee_id', '')
    status = request.args.get('status', '')
    
    # 构建查询 - 过滤掉未支付订单（除非专门查unpaid状态）
    if status == 'unpaid':
        query = Order.query
    else:
        query = Order.query.filter(Order.status != 'unpaid')
    
    # 按加盟商（门店）筛选
    if franchisee_id:
        query = query.filter(Order.franchisee_id == int(franchisee_id))
    
    if status and status != 'unpaid':
        query = query.filter(Order.status == status)
    elif status == 'unpaid':
        query = query.filter(Order.status == 'unpaid')
    
    # 使用joinedload预加载franchisee_account关系，避免N+1查询
    from sqlalchemy.orm import joinedload
    orders = query.options(joinedload(Order.franchisee_account)).order_by(Order.created_at.desc()).all()
    
    # 获取所有加盟商（门店）列表
    franchisees = FranchiseeAccount.query.filter_by(status='active').order_by(FranchiseeAccount.company_name).all()
    
    # 统计数据 - 排除未支付订单
    total_orders = Order.query.filter(Order.status != 'unpaid').count()
    
    # 计算每日订单数（今天创建的订单）
    from sqlalchemy import func
    from datetime import datetime
    today = datetime.now().date()
    daily_orders = Order.query.filter(
        func.date(Order.created_at) == today,
        Order.status != 'unpaid'
    ).count()
    
    # 计算每日业绩总额（今天完成的订单总金额）
    daily_revenue = Order.query.filter(
        func.date(Order.completed_at) == today,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    # 计算待发货订单数（状态为completed或hd_ready但未发货的订单）
    pending_shipment_orders = Order.query.filter(
        Order.status.in_(['completed', 'hd_ready']),
        ~Order.status.in_(['shipped', 'delivered'])
    ).count()
    
    return render_template('admin/orders.html',
                         orders=orders,
                         franchisees=franchisees,
                         franchisee_id=franchisee_id,
                         status=status,
                         total_orders=total_orders,
                         daily_orders=daily_orders,
                         daily_revenue=daily_revenue,
                         pending_shipment_orders=pending_shipment_orders)


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'Order': test_server_module.Order,
        'OrderImage': test_server_module.OrderImage,
        'Product': test_server_module.Product,
        'ProductSize': test_server_module.ProductSize,
        'FranchiseeAccount': test_server_module.FranchiseeAccount,
        'AITask': getattr(test_server_module, 'AITask', None),  # 添加AITask模型
        'ShopOrder': getattr(test_server_module, 'ShopOrder', None),  # 添加ShopOrder模型
        'PRINTER_SYSTEM_AVAILABLE': getattr(test_server_module, 'PRINTER_SYSTEM_AVAILABLE', False),
        'PRINTER_SYSTEM_CONFIG': getattr(test_server_module, 'PRINTER_SYSTEM_CONFIG', {}),
        'PrinterSystemClient': getattr(test_server_module, 'PrinterSystemClient', None),
    }


@admin_orders_bp.route('/admin/orders/export', methods=['GET'])
@login_required
def export_orders():
    """导出所有订单数据为CSV格式"""
    try:
        # 检查管理员权限（operator也可以导出）
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        FranchiseeAccount = models['FranchiseeAccount']
        
        # 获取所有订单数据（排除未支付订单）
        orders = Order.query.filter(Order.status != 'unpaid').order_by(Order.created_at.desc()).all()
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入CSV头部
        headers = [
            '订单ID', '订单号', '客户姓名', '客户手机', '客户地址',
            '产品名称', '尺寸', '艺术风格', '订单状态', '订单价格',
            '佣金金额', '支付时间', '交易号', '下单时间', '完成时间',
            '商家', '来源类型', '外部平台', '外部订单号',
            '物流信息', '快递公司', '快递单号', '物流状态',
            '原图路径', '成品图路径', '高清图路径',
            '冲印发送状态', '加盟商ID', '客户备注'
        ]
        writer.writerow(headers)
        
        # 来源类型中文映射
        source_type_map = {
            'miniprogram': '小程序',
            'website': '网站',
            'douyin': '抖音',
            'franchisee': '加盟商'
        }
        
        # 地址解析函数
        def parse_address(shipping_info_str):
            """解析地址信息"""
            try:
                shipping_info = json.loads(shipping_info_str) if shipping_info_str else {}
                receiver = shipping_info.get('receiver', '')
                full_address = shipping_info.get('fullAddress', '')
                
                if full_address:
                    return full_address
                
                # 拼接省市区
                province = shipping_info.get('province', '')
                city = shipping_info.get('city', '')
                district = shipping_info.get('district', '')
                address = shipping_info.get('address', '')
                
                address_parts = [receiver, province, city, district, address]
                address_parts = [p for p in address_parts if p]  # 过滤空值
                return ' '.join(address_parts) if address_parts else ''
            except:
                return shipping_info_str if shipping_info_str else ''
        
        # 写入订单数据
        for order in orders:
            # 解析物流信息
            logistics_info = None
            logistics_company = ''
            tracking_number = ''
            logistics_status = ''
            
            if order.logistics_info:
                try:
                    logistics_info = json.loads(order.logistics_info)
                    logistics_company = logistics_info.get('company', '')
                    tracking_number = logistics_info.get('tracking_number', '')
                    logistics_status = logistics_info.get('status', '')
                except:
                    pass
            
            # 获取商家信息
            merchant_name = ''
            if hasattr(order, 'merchant') and order.merchant:
                merchant_name = order.merchant.username
            elif order.franchisee_id:
                # 获取加盟商名称
                franchisee_account = FranchiseeAccount.query.get(order.franchisee_id)
                if franchisee_account:
                    merchant_name = f"加盟商:{franchisee_account.company_name}"
                else:
                    merchant_name = f"加盟商ID:{order.franchisee_id}"
            
            # 状态中文映射
            status_map = {
                'unpaid': '未支付',
                'pending': '待制作',
                'processing': '处理中',
                'manufacturing': '制作中',
                'completed': '已完成',
                'shipped': '已发货',
                'delivered': '已送达',
                'cancelled': '已取消',
                'refunded': '已退款',
                'hd_ready': '高清放大'
            }
            status_display = status_map.get(order.status, order.status or '未知')
            
            # 解析客户地址
            customer_address_display = order.customer_address or ''
            if not customer_address_display and order.shipping_info:
                # 如果customer_address为空，从shipping_info中解析
                customer_address_display = parse_address(order.shipping_info)
            
            # 来源类型映射
            source_type_display = source_type_map.get(order.source_type, order.source_type or '未知')
            
            # 写入一行数据
            row = [
                order.id,
                order.order_number,
                order.customer_name,
                order.customer_phone or '',
                customer_address_display,
                order.product_name or '',
                order.size or '',
                order.style_name or '',
                status_display,
                order.price or 0,
                order.commission or 0,
                order.payment_time.strftime('%Y-%m-%d %H:%M:%S') if order.payment_time else '',
                order.transaction_id or '',
                order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
                order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else '',
                merchant_name,
                source_type_display,
                order.external_platform or '',
                order.external_order_number or '',
                order.shipping_info or '',
                logistics_company,
                tracking_number,
                logistics_status,
                order.original_image or '',
                order.final_image or '',
                order.hd_image or '',
                order.printer_send_status or '',
                order.franchisee_id or '',
                order.customer_note or ''
            ]
            writer.writerow(row)
        
        # 准备响应
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        # 创建响应
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        print(f"导出订单数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/orders/export/json', methods=['GET'])
@login_required
def export_orders_json():
    """导出所有订单数据为JSON格式"""
    try:
        # 检查管理员权限（operator也可以导出）
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        FranchiseeAccount = models['FranchiseeAccount']
        
        # 获取所有订单数据（排除未支付订单）
        orders = Order.query.filter(Order.status != 'unpaid').order_by(Order.created_at.desc()).all()
        
        # 状态映射
        status_map = {
            'unpaid': '未支付',
            'pending': '待制作',
            'processing': '处理中',
            'manufacturing': '制作中',
            'completed': '已完成',
            'shipped': '已发货',
            'delivered': '已送达',
            'cancelled': '已取消',
            'refunded': '已退款',
            'hd_ready': '高清放大'
        }
        
        # 来源类型映射
        source_type_map = {
            'miniprogram': '小程序',
            'website': '网站',
            'douyin': '抖音',
            'franchisee': '加盟商'
        }
        
        # 地址解析函数
        def parse_address(shipping_info_str):
            """解析地址信息"""
            try:
                shipping_info = json.loads(shipping_info_str) if shipping_info_str else {}
                receiver = shipping_info.get('receiver', '')
                full_address = shipping_info.get('fullAddress', '')
                
                if full_address:
                    return full_address
                
                # 拼接省市区
                province = shipping_info.get('province', '')
                city = shipping_info.get('city', '')
                district = shipping_info.get('district', '')
                address = shipping_info.get('address', '')
                
                address_parts = [receiver, province, city, district, address]
                address_parts = [p for p in address_parts if p]  # 过滤空值
                return ' '.join(address_parts) if address_parts else ''
            except:
                return shipping_info_str if shipping_info_str else ''
        
        # 构建订单数据列表
        orders_data = []
        for order in orders:
            # 解析物流信息
            logistics_info = None
            logistics_company = ''
            tracking_number = ''
            logistics_status = ''
            
            if order.logistics_info:
                try:
                    logistics_info = json.loads(order.logistics_info)
                    logistics_company = logistics_info.get('company', '')
                    tracking_number = logistics_info.get('tracking_number', '')
                    logistics_status = logistics_info.get('status', '')
                except:
                    pass
            
            # 获取商家信息
            merchant_name = ''
            if hasattr(order, 'merchant') and order.merchant:
                merchant_name = order.merchant.username
            elif order.franchisee_id:
                franchisee_account = FranchiseeAccount.query.get(order.franchisee_id)
                if franchisee_account:
                    merchant_name = f"加盟商:{franchisee_account.company_name}"
                else:
                    merchant_name = f"加盟商ID:{order.franchisee_id}"
            
            # 解析客户地址
            customer_address_display = order.customer_address or ''
            if not customer_address_display and order.shipping_info:
                customer_address_display = parse_address(order.shipping_info)
            
            order_data = {
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone or '',
                'customer_address': customer_address_display,
                'product_name': order.product_name or '',
                'size': order.size or '',
                'style_name': order.style_name or '',
                'status': status_map.get(order.status, order.status or '未知'),
                'price': float(order.price) if order.price else 0.0,
                'commission': float(order.commission) if order.commission else 0.0,
                'payment_time': order.payment_time.isoformat() if order.payment_time else None,
                'transaction_id': order.transaction_id or '',
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'completed_at': order.completed_at.isoformat() if order.completed_at else None,
                'merchant': merchant_name,
                'source_type': source_type_map.get(order.source_type, order.source_type or '未知'),
                'external_platform': order.external_platform or '',
                'external_order_number': order.external_order_number or '',
                'shipping_info': order.shipping_info or '',
                'logistics_company': logistics_company,
                'tracking_number': tracking_number,
                'logistics_status': logistics_status,
                'original_image': order.original_image or '',
                'final_image': order.final_image or '',
                'hd_image': order.hd_image or '',
                'printer_send_status': order.printer_send_status or '',
                'franchisee_id': order.franchisee_id or '',
                'customer_note': order.customer_note or ''
            }
            orders_data.append(order_data)
        
        # 创建响应
        response = make_response(json.dumps(orders_data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    except Exception as e:
        print(f"导出订单数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def admin_order_detail(order_id):
    """订单详情页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    # 处理测试订单（order_id=0）
    if order_id == 0:
        flash('这是测试任务，没有对应的订单记录', 'info')
        from app.routes.ai import ai_bp
        return redirect(url_for('ai.ai_tasks'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    db = models['db']
    Order = models['Order']
    OrderImage = models['OrderImage']
    Product = models['Product']
    ProductSize = models['ProductSize']
    
    # 获取app实例（用于文件路径）
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app_instance = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app_instance = current_app
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # 使用原始SQL查询，避免SQLAlchemy模型字段问题
        result = db.session.execute(
            text("SELECT id, order_id, path, is_main FROM order_image WHERE order_id = :order_id"),
            {"order_id": order.id}
        )
        images_data = result.fetchall()
        print(f"订单详情 - 订单ID: {order_id}, 查询到图片数量: {len(images_data)}")
        
        # 转换为OrderImage对象（如果可能）或使用字典
        images = []
        for row in images_data:
            img_id, order_id_val, path, is_main = row
            print(f"  - 图片ID: {img_id}, 路径: {path}, 是否主图: {is_main}")
            # 创建简单的对象来存储图片信息
            class ImageObj:
                def __init__(self, id, path, is_main):
                    self.id = id
                    self.path = path
                    self.is_main = bool(is_main) if is_main is not None else False
            images.append(ImageObj(img_id, path, is_main))
    except Exception as e:
        # 如果查询失败，尝试使用SQLAlchemy查询（可能字段不存在）
        print(f"原始SQL查询失败，尝试SQLAlchemy查询: {e}")
        try:
            images = OrderImage.query.filter_by(order_id=order.id).all()
            print(f"SQLAlchemy查询成功 - 订单ID: {order_id}, 查询到图片数量: {len(images)}")
            for img in images:
                print(f"  - 图片ID: {img.id}, 路径: {img.path}, 是否主图: {getattr(img, 'is_main', False)}")
        except Exception as e2:
            # 如果查询失败（可能是数据库表结构问题），返回空列表并记录错误
            print(f"查询订单图片失败: {e2}")
            import traceback
            traceback.print_exc()
            images = []
    
    # 查询产品（如果free_selection_count字段不存在，会使用默认值1）
    try:
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    except Exception as e:
        # 如果字段不存在，使用原始SQL查询
        print(f"ORM查询失败（可能缺少free_selection_count字段），使用原始SQL: {e}")
        try:
            result = db.session.execute(
                text("SELECT id, code, name, description, image_url, is_active, sort_order, created_at FROM products WHERE is_active = 1 ORDER BY sort_order")
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
    sizes = ProductSize.query.filter_by(is_active=True).order_by(ProductSize.sort_order).all()
    
    # 将ProductSize对象转换为模板期望的格式
    size_options = []
    for size in sizes:
        size_options.append({
            'code': f"size_{size.id}",  # 使用ID作为code
            'name': size.size_name,
            'price': size.price
        })
    
    # 获取所有效果图（从AITask中获取，如果不存在则从文件系统读取）
    effect_images = []
    AITask = models.get('AITask')
    if AITask:
        try:
            ai_tasks = AITask.query.filter_by(
                order_id=order.id,
                status='completed'
            ).filter(AITask.output_image_path.isnot(None)).order_by(AITask.completed_at.desc()).all()
            
            for task in ai_tasks:
                if task.output_image_path:
                    # 处理output_image_path：可能是相对路径、绝对路径或云端URL
                    output_path = task.output_image_path
                    
                    # 如果是云端URL，直接使用
                    if output_path.startswith('http://') or output_path.startswith('https://'):
                        image_url = output_path
                        filename = output_path.split('/')[-1]  # 提取文件名
                    else:
                        # 如果是相对路径（如 final_works/xxx.png），提取文件名
                        if '/' in output_path or '\\' in output_path:
                            # 提取文件名（处理Windows和Unix路径）
                            filename = os.path.basename(output_path.replace('\\', '/'))
                        else:
                            filename = output_path
                        
                        # 构建图片URL（使用缩略图进行预览）
                        from urllib.parse import quote
                        from app.utils.image_thumbnail import get_thumbnail_path
                        
                        # 检查缩略图是否存在
                        thumbnail_filename = get_thumbnail_path(filename)
                        # 提取缩略图文件名
                        if '/' in thumbnail_filename or '\\' in thumbnail_filename:
                            thumbnail_filename = os.path.basename(thumbnail_filename.replace('\\', '/'))
                        
                        # 检查缩略图文件是否存在
                        hd_folder = app_instance.config.get('HD_FOLDER', 'hd_images')
                        final_folder = app_instance.config.get('FINAL_FOLDER', 'final_works')
                        if not os.path.isabs(hd_folder):
                            hd_folder = os.path.join(app_instance.root_path, hd_folder)
                        if not os.path.isabs(final_folder):
                            final_folder = os.path.join(app_instance.root_path, final_folder)
                        
                        thumbnail_exists = False
                        if os.path.exists(os.path.join(hd_folder, thumbnail_filename)):
                            thumbnail_exists = True
                        elif os.path.exists(os.path.join(final_folder, thumbnail_filename)):
                            thumbnail_exists = True
                        
                        # 如果缩略图存在，使用缩略图；否则使用原图
                        if thumbnail_exists:
                            encoded_filename = quote(thumbnail_filename, safe='')
                            image_url = f"/public/hd/{encoded_filename}"
                        else:
                            encoded_filename = quote(filename, safe='')
                            image_url = f"/public/hd/{encoded_filename}"
                    
                    effect_images.append({
                        'id': task.id,
                        'filename': filename,
                        'url': image_url,
                        'created_at': task.completed_at or task.created_at
                    })
            
            print(f"订单详情 - 订单ID: {order_id}, 从AITask查询到效果图数量: {len(effect_images)}")
            for img in effect_images:
                print(f"  效果图: {img['filename']}")
        except Exception as e:
            print(f"从AITask查询效果图失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 如果AITask中没有效果图，尝试从文件系统读取（备选方案）
    if len(effect_images) == 0:
        print(f"订单详情 - AITask中没有效果图，尝试从文件系统读取...")
        try:
            hd_folder = app_instance.config.get('HD_FOLDER', 'hd_images')
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(app_instance.root_path, hd_folder)
            
            print(f"效果图文件夹路径: {hd_folder}")
            print(f"文件夹是否存在: {os.path.exists(hd_folder)}")
            
            if os.path.exists(hd_folder):
                # 查找该订单的所有效果图文件
                import glob
                pattern = os.path.join(hd_folder, f"{order.order_number}_effect_*")
                print(f"搜索模式: {pattern}")
                effect_files = glob.glob(pattern)
                print(f"找到文件数量: {len(effect_files)}")
                for f in effect_files:
                    print(f"  文件: {f}")
                
                effect_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间排序
                
                for filepath in effect_files:
                    filename = os.path.basename(filepath)
                    from urllib.parse import quote
                    encoded_filename = quote(filename, safe='')
                    image_url = f"/public/hd/{encoded_filename}"
                    
                    effect_images.append({
                        'id': 0,  # 文件系统读取的没有ID
                        'filename': filename,
                        'url': image_url,
                        'created_at': datetime.fromtimestamp(os.path.getmtime(filepath))
                    })
                
                print(f"订单详情 - 订单ID: {order_id}, 从文件系统读取到效果图数量: {len(effect_images)}")
                for img in effect_images:
                    print(f"  效果图: {img['filename']}")
            else:
                print(f"⚠️ 效果图文件夹不存在: {hd_folder}")
        except Exception as e:
            print(f"❌ 从文件系统读取效果图失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"订单详情 - 从AITask获取到 {len(effect_images)} 张效果图，跳过文件系统读取")
    
    # 获取选片信息（从ShopOrder中获取）
    selected_images = []
    ShopOrder = models.get('ShopOrder')
    AITask = models.get('AITask')
    
    if ShopOrder:
        try:
            print(f"\n=== 开始查询选片信息 ===")
            print(f"订单ID: {order_id}, 订单号: {order.order_number}, 订单状态: {order.status}")
            
            # 尝试通过original_order_id查询
            try:
                shop_orders_by_id = ShopOrder.query.filter_by(original_order_id=order.id).all()
                print(f"通过original_order_id查询到 {len(shop_orders_by_id)} 条记录")
            except Exception as e:
                print(f"通过original_order_id查询失败: {e}")
                shop_orders_by_id = []
            
            # 尝试通过original_order_number查询
            try:
                shop_orders_by_number = ShopOrder.query.filter_by(original_order_number=order.order_number).all()
                print(f"通过original_order_number查询到 {len(shop_orders_by_number)} 条记录")
            except Exception as e:
                print(f"通过original_order_number查询失败: {e}")
                shop_orders_by_number = []
            
            # 合并结果并去重
            shop_orders_dict = {}
            for so in shop_orders_by_id:
                shop_orders_dict[so.id] = so
            for so in shop_orders_by_number:
                shop_orders_dict[so.id] = so
            
            shop_orders = list(shop_orders_dict.values())
            
            # 排序
            try:
                shop_orders.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') and x.created_at else x.id)
            except:
                shop_orders.sort(key=lambda x: x.id)
            
            print(f"合并后共 {len(shop_orders)} 条商城订单")
            
            # 按图片路径分组，每张图片关联多个产品
            images_dict = {}  # key: image_url, value: {image_url, image_path, products: []}
            
            for shop_order in shop_orders:
                print(f"\n  处理商城订单: {shop_order.order_number}")
                print(f"    original_order_id: {shop_order.original_order_id}")
                print(f"    original_order_number: {shop_order.original_order_number}")
                print(f"    image_url: {shop_order.image_url}")
                print(f"    产品: {shop_order.product_name}, 规格: {shop_order.size_name}, 数量: {shop_order.quantity}")
                
                # 获取图片路径
                image_path = shop_order.image_url
                
                # 如果image_url为空，尝试从AITask获取
                if not image_path and shop_order.original_order_id and AITask:
                    print(f"    image_url为空，尝试从AITask获取...")
                    # 这里需要知道具体是哪个AITask，暂时跳过
                    # 可以考虑在customer_note中存储task_id
                    pass
                
                if image_path:
                    # 如果该图片已存在，添加产品信息
                    if image_path in images_dict:
                        existing = images_dict[image_path]
                        # 添加产品信息到列表
                        existing['products'].append({
                            'order_number': shop_order.order_number,
                            'product_id': shop_order.product_id,
                            'product_name': shop_order.product_name or '',
                            'size_id': shop_order.size_id,
                            'size_name': shop_order.size_name or '',
                            'quantity': shop_order.quantity or 1,
                            'price': float(shop_order.price or 0),
                            'total_price': float(shop_order.price or 0) * (shop_order.quantity or 1),
                        })
                        print(f"    📝 添加产品到已有图片: {shop_order.product_name}-{shop_order.size_name}")
                    else:
                        # 构建图片URL - image_url存储的是AITask的output_image_path
                        # 与效果图使用相同的URL构建方式
                        from urllib.parse import quote
                        
                        # 直接使用image_path作为filename（与效果图逻辑一致）
                        encoded_filename = quote(image_path, safe='')
                        image_url = f"/public/hd/{encoded_filename}"
                        
                        images_dict[image_path] = {
                            'image_url': image_url,
                            'image_path': shop_order.image_url,
                            'products': [{
                                'order_number': shop_order.order_number,
                                'product_id': shop_order.product_id,
                                'product_name': shop_order.product_name or '',
                                'size_id': shop_order.size_id,
                                'size_name': shop_order.size_name or '',
                                'quantity': shop_order.quantity or 1,
                                'price': float(shop_order.price or 0),
                                'total_price': float(shop_order.price or 0) * (shop_order.quantity or 1),
                            }],
                            'created_at': shop_order.created_at if hasattr(shop_order, 'created_at') and shop_order.created_at else None
                        }
                        print(f"    ✅ 添加新图片: URL={image_url}, 产品: {shop_order.product_name}-{shop_order.size_name}")
                else:
                    print(f"    ⚠️ 跳过：image_url为空")
            
            # 将按图片分组的数据转换为列表
            selected_images = list(images_dict.values())
            
            print(f"\n最终选片数量: {len(selected_images)}")
            print(f"=== 选片信息查询完成 ===\n")
            
        except Exception as e:
            print(f"❌ 查询选片信息失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ ShopOrder模型不存在，无法查询选片信息")
    
    print(f"订单详情页面 - 订单ID: {order_id}")
    print(f"订单final_image字段: {order.final_image}")
    if order.final_image:
        final_path = os.path.join(current_app.config['FINAL_FOLDER'], order.final_image)
        print(f"效果图完整路径: {final_path}")
        print(f"效果图文件是否存在: {os.path.exists(final_path)}")
    
    if request.method == 'POST':
        print("=" * 50)
        print(f"收到订单更新请求，订单ID: {order_id}")
        print(f"请求方法: {request.method}")
        print(f"请求文件键: {list(request.files.keys())}")
        print(f"请求表单键: {list(request.form.keys())}")
        print(f"Content-Type: {request.content_type}")
        print(f"Content-Length: {request.content_length}")
        
        # 详细打印文件信息
        print("=" * 50)
        print("所有文件字段:")
        for key in request.files:
            files = request.files.getlist(key)
            print(f"  字段 '{key}': {len(files)} 个文件")
            for idx, file in enumerate(files):
                if file and file.filename:
                    print(f"    文件 {idx+1}: {file.filename}, 大小: {file.content_length or '未知'} bytes")
                else:
                    print(f"    文件 {idx+1}: 空文件或无效文件")
        
        # 特别检查hd_image[]字段
        if 'hd_image[]' in request.files:
            hd_files = request.files.getlist('hd_image[]')
            print(f"\n特别检查 - hd_image[]字段: 找到 {len(hd_files)} 个文件")
            for idx, f in enumerate(hd_files):
                if f and f.filename:
                    print(f"  hd_image[{idx}]: {f.filename}, 大小: {f.content_length or '未知'} bytes")
                else:
                    print(f"  hd_image[{idx}]: 空文件")
        
        print("=" * 50)
        
        try:
            # 处理精修图上传
            if 'final_image' in request.files:
                final_image_file = request.files['final_image']
                if final_image_file and final_image_file.filename:
                    print(f"处理精修图上传: {final_image_file.filename}")
                    try:
                        # 确保目录存在
                        final_folder = app_instance.config.get('FINAL_FOLDER', 'final_works')
                        if not os.path.isabs(final_folder):
                            final_folder = os.path.join(app_instance.root_path, final_folder)
                        os.makedirs(final_folder, exist_ok=True)
                        print(f"精修图目录: {final_folder}")
                        
                        # 生成文件名
                        filename = secure_filename(final_image_file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{order.order_number}_final_{timestamp}_{filename}"
                        filepath = os.path.join(final_folder, filename)
                        
                        # 保存文件
                        final_image_file.save(filepath)
                        print(f"精修图保存成功: {filepath}, 文件大小: {os.path.getsize(filepath)} bytes")
                        
                        # 更新订单
                        order.final_image = filename
                        # 如果精修图完成时间未设置，则设置当前时间
                        if not order.retouch_completed_at:
                            order.retouch_completed_at = datetime.now()
                        
                        # 更新订单状态为"美颜处理中"（如果当前状态是shooting）
                        if order.status in ['shooting', 'paid']:
                            order.status = 'retouching'  # 美颜处理中
                        
                        flash('精修图上传成功', 'success')
                    except Exception as e:
                        print(f"精修图上传失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        flash(f'精修图上传失败: {str(e)}', 'error')
            
            # 处理效果图上传（支持多图）
            hd_images_uploaded = []
            
            # 尝试多种方式获取文件
            hd_image_files = []
            if 'hd_image[]' in request.files:
                hd_image_files = request.files.getlist('hd_image[]')
                print(f"从 'hd_image[]' 字段获取到 {len(hd_image_files)} 个文件")
            elif 'hd_image' in request.files:
                # 兼容单图上传
                single_file = request.files['hd_image']
                if single_file and single_file.filename:
                    hd_image_files = [single_file]
                    print(f"从 'hd_image' 字段获取到 1 个文件")
            
            # 过滤掉空文件
            hd_image_files = [f for f in hd_image_files if f and f.filename]
            print(f"过滤后，有效文件数量: {len(hd_image_files)}")
            
            if hd_image_files:
                print(f"开始处理效果图上传，共 {len(hd_image_files)} 张")
                AITask = models.get('AITask')
                
                # 如果从models中获取不到，尝试直接从test_server模块获取
                if not AITask:
                    import sys
                    if 'test_server' in sys.modules:
                        test_server_module = sys.modules['test_server']
                        AITask = getattr(test_server_module, 'AITask', None)
                        if AITask:
                            print(f"✅ 从test_server模块直接获取AITask模型成功")
                
                try:
                    # 确保目录存在
                    hd_folder = app_instance.config.get('HD_FOLDER', 'hd_images')
                    if not os.path.isabs(hd_folder):
                        hd_folder = os.path.join(app_instance.root_path, hd_folder)
                    os.makedirs(hd_folder, exist_ok=True)
                    print(f"效果图目录: {hd_folder}")
                    
                    # 处理每张效果图
                    for idx, hd_image_file in enumerate(hd_image_files):
                        if not hd_image_file or not hd_image_file.filename:
                            continue
                        
                        print(f"处理第 {idx + 1} 张效果图: {hd_image_file.filename}")
                        
                        # 生成文件名
                        filename = secure_filename(hd_image_file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{order.order_number}_effect_{timestamp}_{idx+1:03d}_{filename}"
                        filepath = os.path.join(hd_folder, filename)
                        
                        # 保存文件
                        hd_image_file.save(filepath)
                        file_size = os.path.getsize(filepath)
                        print(f"效果图保存成功: {filepath}, 文件大小: {file_size} bytes")
                        
                        # 生成缩略图（长边1920px的JPG）
                        try:
                            from app.utils.image_thumbnail import generate_thumbnail
                            thumbnail_path = generate_thumbnail(filepath, max_size=1920, quality=85)
                            if thumbnail_path:
                                print(f"✅ 缩略图生成成功: {thumbnail_path}")
                        except Exception as thumb_error:
                            print(f"⚠️ 生成缩略图失败: {str(thumb_error)}")
                            import traceback
                            traceback.print_exc()
                        
                        # 创建AITask记录（用于选片功能）
                        if AITask:
                            try:
                                ai_task = AITask(
                                    order_id=order.id,
                                    order_number=order.order_number,
                                    status='completed',
                                    output_image_path=filename,  # 只保存文件名，相对路径
                                    completed_at=datetime.now()
                                )
                                db.session.add(ai_task)
                                # 立即刷新以获取ID
                                db.session.flush()
                                print(f"✅ 创建AITask记录: task_id={ai_task.id}, output_image_path={filename}, order_id={order.id}")
                            except Exception as e:
                                print(f"❌ 创建AITask记录失败: {str(e)}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"⚠️ AITask模型未找到，跳过创建AITask记录")
                        
                        hd_images_uploaded.append(filename)
                        
                        # 第一张效果图作为主图，更新订单的hd_image字段
                        if idx == 0:
                            order.hd_image = filename
                    
                    # 如果制作完成时间未设置，则设置当前时间
                    if not order.completed_at and hd_images_uploaded:
                        order.completed_at = datetime.now()
                    
                    # 更新订单状态：如果当前是ai_processing，改为pending_selection（待选片）
                    if order.status in ['ai_processing', 'retouching', 'shooting'] and hd_images_uploaded:
                        order.status = 'pending_selection'  # 待选片
                        print(f"✅ 订单 {order.order_number} 效果图已上传，状态已更新为: pending_selection")
                    
                    if hd_images_uploaded:
                        flash(f'效果图上传成功，共 {len(hd_images_uploaded)} 张', 'success')
                    
                except Exception as e:
                    print(f"效果图上传失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    flash(f'效果图上传失败: {str(e)}', 'error')
            
            # 处理订单状态更新
            if 'status' in request.form:
                new_status = request.form.get('status')
                if new_status:
                    order.status = new_status
                    print(f"订单状态更新为: {new_status}")
            
            # 处理产品名称和尺寸（如果提供）
            if 'product_name' in request.form:
                product_name = request.form.get('product_name')
                if product_name:
                    order.product_name = product_name
            
            if 'size' in request.form:
                size = request.form.get('size')
                if size:
                    order.size = size
            
            # 提交更改
            db.session.commit()
            print("=" * 50)
            print(f"✅ 订单更新成功，订单ID: {order_id}")
            print("=" * 50)
            flash('订单更新成功', 'success')
            
        except Exception as e:
            db.session.rollback()
            print("=" * 50)
            print(f"❌ 订单更新失败: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print("=" * 50)
            flash(f'订单更新失败: {str(e)}', 'error')
        
        return redirect(url_for('admin_orders.admin_order_detail', order_id=order_id))
    
    return render_template('admin/order_details.html', 
                         order=order, 
                         images=images,
                         effect_images=effect_images,  # 传递所有效果图
                         selected_images=selected_images,  # 传递选片信息
                         products=products,
                         size_options=size_options)


@admin_orders_bp.route('/admin/order/<int:order_id>/send-to-printer', methods=['POST'])
@login_required
def admin_send_to_printer(order_id):
    """管理员手动发送订单到冲印系统"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    PRINTER_SYSTEM_AVAILABLE = models['PRINTER_SYSTEM_AVAILABLE']
    PRINTER_SYSTEM_CONFIG = models['PRINTER_SYSTEM_CONFIG']
    PrinterSystemClient = models['PrinterSystemClient']
    db = models['db']
    
    order = Order.query.get_or_404(order_id)
    
    # 检查订单状态和高清图片
    if order.status != 'hd_ready':
        return jsonify({'success': False, 'message': '订单状态必须是"高清放大"才能发送'}), 400
    
    if not order.hd_image:
        return jsonify({'success': False, 'message': '订单没有高清图片'}), 400
    
    # 检查冲印系统配置
    if not PRINTER_SYSTEM_AVAILABLE or not PRINTER_SYSTEM_CONFIG.get('enabled', False):
        return jsonify({'success': False, 'message': '冲印系统未启用'}), 400
    
    try:
        # 检查高清图片文件
        hd_image_path = os.path.join(current_app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            return jsonify({'success': False, 'message': f'高清图片文件不存在: {hd_image_path}'}), 400
        
        # 发送到冲印系统
        if PrinterSystemClient:
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
            result = printer_client.send_order_to_printer(order, hd_image_path, order_obj=order)
            
            # 提交数据库更改
            db.session.commit()
            
            if result['success']:
                # 发送成功后，更新状态为"厂家制作中"
                order.status = 'manufacturing'  # 新增状态：厂家制作中
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': '订单已成功发送到厂家',
                    'new_status': 'manufacturing'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': f'发送失败: {result.get("message", "未知错误")}'
                })
        else:
            return jsonify({'success': False, 'message': '冲印系统客户端未初始化'}), 500
            
    except Exception as e:
        print(f"发送订单到冲印系统时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/order/<int:order_id>/delete', methods=['POST'])
@login_required
def admin_order_delete(order_id):
    """删除订单"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    db = models['db']
    
    order = Order.query.get_or_404(order_id)
    
    try:
        db.session.delete(order)
        db.session.commit()
        flash('订单删除成功', 'success')
        return jsonify({'success': True, 'message': '订单删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除订单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/order/<int:order_id>/send-data', methods=['GET'])
@login_required
def admin_view_send_data(order_id):
    """管理员查看订单发送数据包"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    db = models['db']
    PrinterSystemClient = models.get('PrinterSystemClient')
    PRINTER_SYSTEM_CONFIG = models.get('PRINTER_SYSTEM_CONFIG', {})
    
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # 检查高清图片
        if not order.hd_image:
            return jsonify({'success': False, 'message': '订单没有高清图片'}), 400
        
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            return jsonify({'success': False, 'message': f'高清图片文件不存在: {hd_image_path}'}), 400
        
        # 构建发送数据包（不实际发送）
        if not PrinterSystemClient:
            return jsonify({'success': False, 'message': '冲印系统客户端不可用'}), 500
        
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 获取图片信息
        image_info = printer_client._get_image_info(hd_image_path, order)
        
        # 构建订单数据
        order_data = printer_client._build_order_data(order, hd_image_path)
        
        # 订单基本信息
        order_info = {
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'product_name': order.product_name,
            'size': order.size,
            'status': order.status,
            'hd_image': order.hd_image
        }
        
        return jsonify({
            'success': True,
            'order_info': order_info,
            'image_info': image_info,
            'send_data': order_data
        })
        
    except Exception as e:
        print(f"获取发送数据包时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/order/<int:order_id>/check-image-size', methods=['GET'])
@login_required
def admin_check_image_size(order_id):
    """管理员检查订单图片尺寸"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    PrinterSystemClient = models.get('PrinterSystemClient')
    PRINTER_SYSTEM_CONFIG = models.get('PRINTER_SYSTEM_CONFIG', {})
    
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
    else:
        app = current_app
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # 检查高清图片
        if not order.hd_image:
            return jsonify({'success': False, 'message': '订单没有高清图片'}), 400
        
        hd_image_path = os.path.join(app.config['HD_FOLDER'], order.hd_image)
        if not os.path.exists(hd_image_path):
            return jsonify({'success': False, 'message': f'高清图片文件不存在: {hd_image_path}'}), 400
        
        # 验证图片尺寸
        if not PrinterSystemClient:
            return jsonify({'success': False, 'message': '冲印系统客户端不可用'}), 500
        
        printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        validation_result = printer_client._validate_image_size(hd_image_path, order)
        
        return jsonify({
            'success': True,
            'validation_result': validation_result
        })
        
    except Exception as e:
        print(f"检查图片尺寸时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'检查失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/order/<int:order_id>/manual-logistics', methods=['POST'])
@login_required
def admin_manual_logistics(order_id):
    """管理员或营运管理员手动录入快递单号"""
    if current_user.role not in ['admin', 'operator']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    db = models['db']
    
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 验证必要字段
        company = data.get('company')
        tracking_number = data.get('tracking_number')
        status = data.get('status', 'shipped')
        remark = data.get('remark', '')
        
        if not company or not tracking_number:
            return jsonify({'success': False, 'message': '快递公司和快递单号不能为空'}), 400
        
        # 查找订单
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        # 构建物流信息（JSON格式）
        logistics_data = {
            'company': company,
            'tracking_number': tracking_number,
            'status': status,
            'remark': remark,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'manual'  # 标记为手动录入
        }
        
        # 更新订单物流信息
        order.logistics_info = json.dumps(logistics_data, ensure_ascii=False)
        
        # 如果订单状态不是已发货相关状态，更新为已发货
        if order.status not in ['shipped', 'delivered']:
            order.status = 'shipped'  # 已发货
        
        # 添加发货时间字段（如果不存在则使用当前时间）
        if hasattr(order, 'shipped_at'):
            order.shipped_at = datetime.now()
        
        db.session.commit()
        
        print(f"✅ 订单 {order.order_number} 手动录入快递信息成功:")
        print(f"   快递公司: {company}")
        print(f"   快递单号: {tracking_number}")
        print(f"   状态: {status}")
        print(f"   备注: {remark}")
        
        return jsonify({
            'success': True,
            'message': '快递单号录入成功',
            'logistics_info': logistics_data
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"手动录入快递单号失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'录入失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/orders/batch-update-status', methods=['POST'])
@login_required
def batch_update_order_status():
    """批量更新订单状态（基于AI任务完成情况）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        AITask = models['AITask']
        db = models['db']
        
        # 查找所有状态为"AI任务处理中"的订单
        orders_to_check = Order.query.filter(
            Order.status.in_(['ai_processing', 'retouching', 'shooting', 'processing'])
        ).all()
        
        updated_count = 0
        skipped_count = 0
        updated_orders = []
        
        for order in orders_to_check:
            # 查询该订单的所有AI任务
            all_tasks = AITask.query.filter_by(order_id=order.id).all()
            
            if len(all_tasks) == 0:
                skipped_count += 1
                continue
            
            # 过滤掉失败和取消的任务，只统计有效任务
            valid_tasks = [t for t in all_tasks if t.status not in ['failed', 'cancelled']]
            completed_tasks = [t for t in valid_tasks if t.status == 'completed' and t.output_image_path]
            
            # 如果所有有效任务都已完成，更新订单状态为"待选片"
            if len(valid_tasks) > 0 and len(completed_tasks) == len(valid_tasks):
                old_status = order.status
                order.status = 'pending_selection'  # 待选片
                updated_count += 1
                updated_orders.append({
                    'order_number': order.order_number,
                    'old_status': old_status,
                    'new_status': 'pending_selection',
                    'tasks_count': len(valid_tasks)
                })
            else:
                skipped_count += 1
        
        if updated_count > 0:
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': f'批量更新完成，更新了 {updated_count} 个订单状态',
                'data': {
                    'updated_count': updated_count,
                    'skipped_count': skipped_count,
                    'updated_orders': updated_orders
                }
            })
        else:
            return jsonify({
                'status': 'info',
                'message': f'没有订单需要更新（跳过了 {skipped_count} 个订单）',
                'data': {
                    'updated_count': 0,
                    'skipped_count': skipped_count
                }
            })
    
    except Exception as e:
        print(f"批量更新订单状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'批量更新失败: {str(e)}'}), 500


@admin_orders_bp.route('/admin/orders/add', methods=['GET', 'POST'])
@login_required
def admin_add_order():
    """管理员手动新增订单"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    Order = models['Order']
    OrderImage = models['OrderImage']
    db = models['db']
    
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
        WECHAT_NOTIFICATION_AVAILABLE = getattr(test_server_module, 'WECHAT_NOTIFICATION_AVAILABLE', False)
        wechat_notify = getattr(test_server_module, 'wechat_notify', None)
    else:
        app = current_app
        WECHAT_NOTIFICATION_AVAILABLE = False
        wechat_notify = None
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            customer_name = request.form['customer_name']
            customer_phone = request.form['customer_phone']
            price = float(request.form['price'])
            status = request.form.get('status', 'pending')
            source_type = request.form.get('source_type', 'website')
            external_platform = request.form.get('external_platform', '')
            external_order_number = request.form.get('external_order_number', '')
            customer_address = request.form.get('customer_address', '')
            
            # 处理图片上传
            original_image = None
            if 'original_image' in request.files:
                file = request.files['original_image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    original_image = filename
            
            # 创建订单
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                price=price,
                status=status,
                source_type=source_type,
                external_platform=external_platform,
                external_order_number=external_order_number,
                customer_address=customer_address,
                original_image=original_image or 'manual_order.jpg'  # 默认图片
            )
            
            db.session.add(order)
            db.session.flush()  # 获取订单ID，但不提交事务
            
            # 如果有图片，创建OrderImage记录
            if original_image:
                order_image = OrderImage(
                    order_id=order.id,
                    path=original_image,
                    is_main=True  # 管理员手动创建的订单，第一张图片设为主图
                )
                db.session.add(order_image)
            
            db.session.commit()
            
            # ⭐ 发送微信通知
            if WECHAT_NOTIFICATION_AVAILABLE and wechat_notify:
                try:
                    wechat_notify(
                        order_number=order.order_number,
                        customer_name=customer_name,
                        total_price=price,
                        source='管理后台'
                    )
                except Exception as e:
                    print(f"微信通知失败: {e}")
            
            flash('订单创建成功！', 'success')
            # 重定向到订单详情页
            return redirect(url_for('admin_orders.admin_order_detail', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'订单创建失败：{str(e)}', 'error')
            import traceback
            traceback.print_exc()
    
    return render_template('admin/add_order.html')