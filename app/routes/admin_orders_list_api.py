# -*- coding: utf-8 -*-
"""
管理后台订单列表API路由模块
提供订单列表、筛选、导出功能
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, make_response
from flask_login import login_required, current_user
from datetime import datetime
import io
import csv
import json
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
admin_orders_list_bp = Blueprint('admin_orders_list', __name__)

@admin_orders_list_bp.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    """订单管理页面"""
    models = get_models(['Order', 'FranchiseeAccount', 'db'])
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    Order = models['Order']
    FranchiseeAccount = models['FranchiseeAccount']
    db = models['db']
    
    # 获取筛选参数
    franchisee_id = request.args.get('franchisee_id', '')
    status = request.args.get('status', '')
    order_mode = request.args.get('order_mode', '')
    search = request.args.get('search', '').strip()  # 订单搜索
    page = request.args.get('page', 1, type=int)  # 分页参数
    per_page = 10  # 每页显示10条
    
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
    
    # 按订单类型筛选
    if order_mode:
        query = query.filter(Order.order_mode == order_mode)
    
    # 订单搜索（按订单号、客户姓名、客户电话搜索）
    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Order.order_number.like(f'%{search}%'),
                Order.customer_name.like(f'%{search}%'),
                Order.customer_phone.like(f'%{search}%')
            )
        )
    
    # 使用joinedload预加载franchisee_account关系，避免N+1查询
    all_orders = query.options(joinedload(Order.franchisee_account)).order_by(Order.created_at.desc()).all()
    
    # 按订单号分组，每个订单号只显示一条记录（使用第一个订单作为主订单）
    orders_by_number = {}
    for order in all_orders:
        if order.order_number not in orders_by_number:
            orders_by_number[order.order_number] = {
                'main_order': order,  # 主订单（用于显示基本信息）
                'items': [],  # 所有商品列表
                'total_price': 0.0,  # 总金额
                'item_count': 0  # 商品数量
            }
        
        # 添加商品信息
        orders_by_number[order.order_number]['items'].append({
            'id': order.id,
            'product_name': order.product_name,
            'price': order.price,
            'status': order.status
        })
        orders_by_number[order.order_number]['total_price'] += float(order.price or 0)
        orders_by_number[order.order_number]['item_count'] += 1
    
    # 转换为列表，每个订单号一条记录
    orders = []
    for order_number, order_data in orders_by_number.items():
        main_order = order_data['main_order']
        item_count = order_data['item_count']
        total_price = order_data['total_price']
        
        # 创建一个类似Order对象的对象，包含合并后的信息
        # 为了兼容模板，我们创建一个简单的对象
        class MergedOrder:
            def __init__(self, main_order, item_count, total_price, items):
                # 复制主订单的所有属性
                for attr in dir(main_order):
                    if not attr.startswith('_') and not callable(getattr(main_order, attr)):
                        try:
                            setattr(self, attr, getattr(main_order, attr))
                        except:
                            pass
                # 覆盖价格
                self.price = total_price
                self.item_count = item_count
                self.items = items
                # 如果多个商品，修改产品名称显示
                if item_count > 1:
                    # 显示第一个商品名称 + "等X件"
                    first_product = items[0]['product_name'] if items else main_order.product_name
                    self.product_name = f"{first_product} 等{item_count}件"
                else:
                    self.product_name = main_order.product_name
        
        merged_order = MergedOrder(main_order, item_count, total_price, order_data['items'])
        orders.append(merged_order)
    
    # 按创建时间排序（最新的在前）
    orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # 分页处理
    total_count = len(orders)
    total_pages = (total_count + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_orders = orders[start_idx:end_idx]
    
    # 获取所有加盟商（门店）列表
    franchisees = FranchiseeAccount.query.filter_by(status='active').order_by(FranchiseeAccount.company_name).all()
    
    # 统计数据 - 按订单号统计（不重复计算）
    # 获取所有不重复的订单号数量
    today = datetime.now().date()
    total_orders = db.session.query(func.count(func.distinct(Order.order_number))).filter(
        Order.status != 'unpaid'
    ).scalar() or 0
    
    # 计算每日订单数（今天创建的订单，按订单号去重）
    daily_orders = db.session.query(func.count(func.distinct(Order.order_number))).filter(
        func.date(Order.created_at) == today,
        Order.status != 'unpaid'
    ).scalar() or 0
    
    # 计算每日业绩总额（今天完成的订单总金额，需要按订单号分组后求和）
    # 先获取今天完成的所有订单号
    completed_order_numbers = db.session.query(Order.order_number).filter(
        func.date(Order.completed_at) == today,
        Order.status == 'completed'
    ).distinct().all()
    
    daily_revenue = 0.0
    for order_number_tuple in completed_order_numbers:
        order_number = order_number_tuple[0]
        # 计算该订单号下所有订单的总金额
        order_total = db.session.query(func.sum(Order.price)).filter(
            Order.order_number == order_number
        ).scalar() or 0.0
        daily_revenue += float(order_total)
    
    # 计算待发货订单数（状态为completed或hd_ready但未发货的订单，按订单号去重）
    pending_shipment_order_numbers = db.session.query(Order.order_number).filter(
        Order.status.in_(['completed', 'hd_ready']),
        ~Order.status.in_(['shipped', 'delivered'])
    ).distinct().all()
    pending_shipment_orders = len(pending_shipment_order_numbers)
    
    return render_template('admin/orders.html',
                         orders=paginated_orders,
                         franchisees=franchisees,
                         franchisee_id=franchisee_id,
                         status=status,
                         order_mode=order_mode,
                         search=search,
                         total_orders=total_orders,
                         daily_orders=daily_orders,
                         daily_revenue=daily_revenue,
                         pending_shipment_orders=pending_shipment_orders,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count)

@admin_orders_list_bp.route('/admin/orders/export', methods=['GET'])
@login_required
@admin_required
def export_orders():
    """导出所有订单数据为CSV格式"""
    try:
        models = get_models(['Order', 'FranchiseeAccount', 'db'])
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

@admin_orders_list_bp.route('/admin/orders/export/json', methods=['GET'])
@login_required
@admin_required
def export_orders_json():
    """导出所有订单数据为JSON格式"""
    try:
        models = get_models(['Order', 'FranchiseeAccount', 'db'])
        if not models:
            return jsonify({'success': False, 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        FranchiseeAccount = models['FranchiseeAccount']
        
        # 获取所有订单数据（排除未支付订单）
        orders = Order.query.filter(Order.status != 'unpaid').order_by(Order.created_at.desc()).all()
        
        # 转换为字典列表
        orders_data = []
        for order in orders:
            # 获取商家信息
            merchant_name = ''
            if hasattr(order, 'merchant') and order.merchant:
                merchant_name = order.merchant.username
            elif order.franchisee_id:
                franchisee_account = FranchiseeAccount.query.get(order.franchisee_id)
                if franchisee_account:
                    merchant_name = f"加盟商:{franchisee_account.company_name}"
            
            # 解析物流信息
            logistics_info = None
            if order.logistics_info:
                try:
                    logistics_info = json.loads(order.logistics_info)
                except:
                    logistics_info = order.logistics_info
            
            order_dict = {
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'customer_address': order.customer_address,
                'product_name': order.product_name,
                'size': order.size,
                'style_name': order.style_name,
                'status': order.status,
                'price': float(order.price) if order.price else 0,
                'commission': float(order.commission) if order.commission else 0,
                'payment_time': order.payment_time.isoformat() if order.payment_time else None,
                'transaction_id': order.transaction_id,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'completed_at': order.completed_at.isoformat() if order.completed_at else None,
                'merchant_name': merchant_name,
                'source_type': order.source_type,
                'external_platform': order.external_platform,
                'external_order_number': order.external_order_number,
                'logistics_info': logistics_info,
                'original_image': order.original_image,
                'final_image': order.final_image,
                'hd_image': order.hd_image,
                'printer_send_status': order.printer_send_status,
                'franchisee_id': order.franchisee_id,
                'customer_note': order.customer_note
            }
            orders_data.append(order_dict)
        
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
