# -*- coding: utf-8 -*-
"""
加盟商前端路由
包含登录、仪表盘、下单、订单管理等前端页面路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import time
import json
import os
import qrcode
import io
import base64
from sqlalchemy import func, desc, text

from app.routes.franchisee.common import get_models, get_wechat_notification

# 创建前端路由子蓝图
bp = Blueprint('franchisee_frontend', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def franchisee_login():
    """加盟商登录页面"""
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return render_template('franchisee/login.html')
    
    FranchiseeAccount = models['FranchiseeAccount']
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('franchisee/login.html')
        
        account = FranchiseeAccount.query.filter_by(username=username).first()
        
        if account and check_password_hash(account.password, password):
            if account.status != 'active':
                flash('账户已被禁用，请联系管理员', 'error')
                return render_template('franchisee/login.html')
            
            session['franchisee_id'] = account.id
            session['franchisee_username'] = account.username
            session['franchisee_company'] = account.company_name
            
            flash(f'欢迎回来，{account.company_name}', 'success')
            return redirect(url_for('franchisee.franchisee_frontend.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('franchisee/login.html')


@bp.route('/logout')
def franchisee_logout():
    """加盟商退出登录"""
    session.pop('franchisee_id', None)
    session.pop('franchisee_username', None)
    session.pop('franchisee_company', None)
    flash('已退出登录', 'info')
    return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))


@bp.route('/dashboard')
def dashboard():
    """加盟商管理面板"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Order = models['Order']
    FranchiseeRecharge = models['FranchiseeRecharge']
    db = models['db']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    from sqlalchemy import func, or_
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)
    
    # 基础查询：只查询该加盟商的订单
    base_query = Order.query.filter(Order.franchisee_id == franchisee_id)
    
    # 订单统计
    total_orders = base_query.filter(Order.status != 'unpaid').count()
    daily_orders = base_query.filter(
        func.date(Order.created_at) == today,
        Order.status != 'unpaid'
    ).count()
    yesterday_orders = base_query.filter(
        func.date(Order.created_at) == yesterday,
        Order.status != 'unpaid'
    ).count()
    week_orders = base_query.filter(
        func.date(Order.created_at) >= this_week_start,
        Order.status != 'unpaid'
    ).count()
    month_orders = base_query.filter(
        func.date(Order.created_at) >= this_month_start,
        Order.status != 'unpaid'
    ).count()
    
    # 业绩统计（基于完成时间）
    daily_revenue = base_query.filter(
        func.date(Order.completed_at) == today,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    yesterday_revenue = base_query.filter(
        func.date(Order.completed_at) == yesterday,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    week_revenue = base_query.filter(
        func.date(Order.completed_at) >= this_week_start,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    month_revenue = base_query.filter(
        func.date(Order.completed_at) >= this_month_start,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    total_revenue = base_query.filter(
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    # 订单状态统计
    pending_orders = base_query.filter(Order.status.in_(['pending', '已支付'])).count()
    processing_orders = base_query.filter(Order.status == 'processing').count()
    completed_orders = base_query.filter(Order.status == 'completed').count()
    error_orders = base_query.filter(
        or_(
            Order.status.in_(['failed', 'error']),
            Order.printer_error_message.isnot(None)
        )
    ).count()
    
    # 最近30天的订单和充值记录
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    recent_orders = base_query.filter(
        Order.created_at >= thirty_days_ago
    ).order_by(desc(Order.created_at)).limit(10).all()
    
    recent_recharges = FranchiseeRecharge.query.filter(
        FranchiseeRecharge.franchisee_id == franchisee_id,
        FranchiseeRecharge.created_at >= thirty_days_ago
    ).order_by(desc(FranchiseeRecharge.created_at)).limit(10).all()
    
    total_amount = sum(order.price for order in recent_orders if order.price)
    total_deduction = sum(order.franchisee_deduction for order in recent_orders if order.franchisee_deduction)
    
    return render_template('franchisee/dashboard.html',
                         account=account,
                         recent_orders=recent_orders,
                         recent_recharges=recent_recharges,
                         total_orders=total_orders,
                         daily_orders=daily_orders,
                         yesterday_orders=yesterday_orders,
                         week_orders=week_orders,
                         month_orders=month_orders,
                         total_amount=total_amount,
                         total_deduction=total_deduction,
                         daily_revenue=float(daily_revenue),
                         yesterday_revenue=float(yesterday_revenue),
                         week_revenue=float(week_revenue),
                         month_revenue=float(month_revenue),
                         total_revenue=float(total_revenue),
                         pending_orders=pending_orders,
                         processing_orders=processing_orders,
                         completed_orders=completed_orders,
                         error_orders=error_orders)


@bp.route('/qrcode')
def franchisee_qrcode():
    """加盟商 - 查看二维码"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    account = FranchiseeAccount.query.get(franchisee_id)
    
    if not account:
        flash('账户不存在', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    return render_template('franchisee/qrcode.html', account=account)


@bp.route('/api/qrcode-preview')
def franchisee_qrcode_preview():
    """加盟商 - 二维码预览API"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    FranchiseeAccount = models['FranchiseeAccount']
    
    try:
        account = FranchiseeAccount.query.get(franchisee_id)
        if not account:
            return jsonify({'success': False, 'message': '账户不存在'}), 404
        
        qr_content = f"https://photogooo/franchisee/scan/{account.qr_code}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qrcode': f"data:image/png;base64,{img_base64}",
            'content': qr_content,
            'company_name': account.company_name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成二维码失败: {str(e)}'}), 500


@bp.route('/orders')
def franchisee_orders():
    """加盟商订单列表 - 复用管理后台的逻辑，但只显示该加盟商的订单"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Order = models['Order']
    db = models['db']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    from sqlalchemy import func, or_
    from sqlalchemy.orm import joinedload
    
    # 获取筛选参数
    status = request.args.get('status', '')
    order_mode = request.args.get('order_mode', '')
    search = request.args.get('search', '').strip()  # 订单搜索
    page = request.args.get('page', 1, type=int)  # 分页参数
    per_page = 10  # 每页显示10条
    
    # 构建查询 - 只查询该加盟商的订单，过滤掉未支付订单（除非专门查unpaid状态）
    if status == 'unpaid':
        query = Order.query.filter(Order.franchisee_id == franchisee_id)
    else:
        query = Order.query.filter(
            Order.franchisee_id == franchisee_id,
            Order.status != 'unpaid'
        )
    
    if status and status != 'unpaid':
        query = query.filter(Order.status == status)
    elif status == 'unpaid':
        query = query.filter(Order.status == 'unpaid')
    
    # 按订单类型筛选
    if order_mode:
        query = query.filter(Order.order_mode == order_mode)
    
    # 订单搜索（按订单号、客户姓名、客户电话搜索）
    if search:
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
    
    # 统计数据 - 按订单号统计（不重复计算）
    today = datetime.now().date()
    total_orders = db.session.query(func.count(func.distinct(Order.order_number))).filter(
        Order.franchisee_id == franchisee_id,
        Order.status != 'unpaid'
    ).scalar() or 0
    
    # 计算每日订单数（今天创建的订单，按订单号去重）
    daily_orders = db.session.query(func.count(func.distinct(Order.order_number))).filter(
        Order.franchisee_id == franchisee_id,
        func.date(Order.created_at) == today,
        Order.status != 'unpaid'
    ).scalar() or 0
    
    # 计算每日业绩总额（今天完成的订单总金额，需要按订单号分组后求和）
    completed_order_numbers = db.session.query(Order.order_number).filter(
        Order.franchisee_id == franchisee_id,
        func.date(Order.completed_at) == today,
        Order.status == 'completed'
    ).distinct().all()
    
    daily_revenue = 0.0
    for order_number_tuple in completed_order_numbers:
        order_number = order_number_tuple[0]
        # 计算该订单号下所有订单的总金额
        order_total = db.session.query(func.sum(Order.price)).filter(
            Order.franchisee_id == franchisee_id,
            Order.order_number == order_number
        ).scalar() or 0.0
        daily_revenue += float(order_total)
    
    # 计算待选片订单数（状态为pending_selection的订单，按订单号去重）
    pending_selection_order_numbers = db.session.query(Order.order_number).filter(
        Order.franchisee_id == franchisee_id,
        Order.status == 'pending_selection',
        Order.status != 'unpaid'
    ).distinct().all()
    pending_selection_orders = len(pending_selection_order_numbers)
    
    # 计算待发货订单数（状态为completed或hd_ready但未发货的订单，按订单号去重）
    pending_shipment_order_numbers = db.session.query(Order.order_number).filter(
        Order.franchisee_id == franchisee_id,
        Order.status.in_(['completed', 'hd_ready']),
        ~Order.status.in_(['shipped', 'delivered'])
    ).distinct().all()
    pending_shipment_orders = len(pending_shipment_order_numbers)
    
    return render_template('franchisee/orders.html',
                         account=account,
                         orders=paginated_orders,
                         status=status,
                         order_mode=order_mode,
                         search=search,
                         total_orders=total_orders,
                         daily_orders=daily_orders,
                         daily_revenue=daily_revenue,
                         pending_selection_orders=pending_selection_orders,
                         pending_shipment_orders=pending_shipment_orders,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count)


@bp.route('/order/<int:order_id>')
def franchisee_order_detail(order_id):
    """加盟商订单详情页面"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Order = models['Order']
    OrderImage = models['OrderImage']
    db = models['db']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    # 获取订单
    order = Order.query.get_or_404(order_id)
    
    # 验证订单是否属于该加盟商
    if order.franchisee_id != franchisee_id:
        flash('无权访问此订单', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_orders'))
    
    # 获取所有使用相同订单号的订单记录（支持追加产品）
    order_number = order.order_number
    all_orders = Order.query.filter_by(
        order_number=order_number,
        franchisee_id=franchisee_id  # 确保只获取该加盟商的订单
    ).order_by(Order.created_at.asc()).all()
    
    # 获取订单图片
    from urllib.parse import quote
    try:
        result = db.session.execute(
            text("SELECT id, order_id, path, is_main FROM order_image WHERE order_id = :order_id"),
            {"order_id": order.id}
        )
        images_data = result.fetchall()
        
        images = []
        for row in images_data:
            img_id, order_id_val, path, is_main = row
            class ImageObj:
                def __init__(self, id, path, is_main, encoded_path=None):
                    self.id = id
                    self.path = path
                    self.encoded_path = encoded_path or quote(path, safe='')
                    self.is_main = bool(is_main) if is_main is not None else False
            images.append(ImageObj(img_id, path, is_main, quote(path, safe='')))
    except Exception as e:
        try:
            order_images = OrderImage.query.filter_by(order_id=order.id).all()
            images = []
            for img in order_images:
                class ImageObj:
                    def __init__(self, id, path, is_main, encoded_path=None):
                        self.id = id
                        self.path = path
                        self.encoded_path = encoded_path or quote(path, safe='')
                        self.is_main = bool(is_main) if is_main is not None else False
                images.append(ImageObj(img.id, img.path, getattr(img, 'is_main', False), quote(img.path, safe='')))
        except Exception as e2:
            print(f"查询订单图片失败: {e2}")
            images = []
    
    # 获取效果图（如果有）
    from urllib.parse import quote
    effect_images = []
    if order.final_image:
        encoded_final_filename = quote(order.final_image, safe='')
        effect_images.append({
            'path': order.final_image,
            'encoded_path': encoded_final_filename,
            'type': 'final',
            'label': '完成的油画作品'
        })
    if order.hd_image:
        encoded_hd_filename = quote(order.hd_image, safe='')
        effect_images.append({
            'path': order.hd_image,
            'encoded_path': encoded_hd_filename,
            'type': 'hd',
            'label': '高清放大图'
        })
    
    # 选片信息（如果有）
    selected_images = []
    
    return render_template('franchisee/order_detail.html',
                         account=account,
                         order=order,
                         all_orders=all_orders,
                         images=images,
                         effect_images=effect_images,
                         selected_images=selected_images)


@bp.route('/confirm-order/<int:order_id>', methods=['POST'])
def confirm_order(order_id):
    """加盟商确认订单"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    models = get_models()
    if not models:
        return jsonify({'success': False, 'message': '系统未初始化'}), 500
    
    Order = models['Order']
    db = models['db']
    
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        if order.franchisee_id != franchisee_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        if order.status != 'completed' or not order.need_confirmation:
            return jsonify({'success': False, 'message': '订单状态不正确，无需确认'}), 400
        
        if order.franchisee_confirmed:
            return jsonify({'success': False, 'message': '订单已确认'}), 400
        
        order.franchisee_confirmed = True
        order.franchisee_confirmed_at = datetime.now()
        
        if order.final_image and not order.final_image_clean:
            order.final_image_clean = order.final_image
        
        if order.hd_image and not order.hd_image_clean:
            order.hd_image_clean = order.hd_image
        
        order.status = 'manufacturing'
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '订单确认成功，已进入制作流程'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'确认失败: {str(e)}'}), 500


@bp.route('/recharge-records')
def franchisee_recharge_records():
    """加盟商充值记录"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    FranchiseeRecharge = models['FranchiseeRecharge']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    recharge_records = FranchiseeRecharge.query.filter_by(franchisee_id=franchisee_id)\
        .order_by(desc(FranchiseeRecharge.created_at)).all()
    
    return render_template('franchisee/recharge_records.html',
                         account=account,
                         recharge_records=recharge_records)


@bp.route('/users')
def franchisee_users():
    """加盟商用户管理 - 显示该加盟商的所有客户"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Order = models['Order']
    db = models['db']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    # 获取该加盟商的所有订单
    orders = Order.query.filter_by(franchisee_id=franchisee_id).all()
    
    # 统计每个客户的信息（去重）
    customers_dict = {}
    for order in orders:
        if not order.customer_name and not order.customer_phone:
            continue
        
        # 使用手机号作为唯一标识，如果没有手机号则使用姓名
        customer_key = order.customer_phone or order.customer_name
        
        if customer_key not in customers_dict:
            customers_dict[customer_key] = {
                'name': order.customer_name or '未知',
                'phone': order.customer_phone or '未填写',
                'order_count': 0,
                'total_amount': 0.0,
                'first_order_time': order.created_at,
                'last_order_time': order.created_at
            }
        
        customers_dict[customer_key]['order_count'] += 1
        customers_dict[customer_key]['total_amount'] += (order.price or 0.0)
        
        if order.created_at < customers_dict[customer_key]['first_order_time']:
            customers_dict[customer_key]['first_order_time'] = order.created_at
        
        if order.created_at > customers_dict[customer_key]['last_order_time']:
            customers_dict[customer_key]['last_order_time'] = order.created_at
    
    # 转换为列表并排序（按最后下单时间倒序）
    customers = list(customers_dict.values())
    customers.sort(key=lambda x: x['last_order_time'], reverse=True)
    
    # 分页处理
    page = request.args.get('page', 1, type=int)
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    paginated_customers = customers[start:end]
    
    total_pages = (len(customers) + per_page - 1) // per_page
    
    return render_template('franchisee/users.html',
                         account=account,
                         customers=paginated_customers,
                         total_customers=len(customers),
                         current_page=page,
                         total_pages=total_pages)


@bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """加盟商修改密码"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    db = models['db']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                flash('请填写所有字段', 'error')
                return render_template('franchisee/change_password.html', account=account)
            
            if not check_password_hash(account.password, current_password):
                flash('当前密码错误', 'error')
                return render_template('franchisee/change_password.html', account=account)
            
            if len(new_password) < 6:
                flash('新密码长度至少6位', 'error')
                return render_template('franchisee/change_password.html', account=account)
            
            if new_password != confirm_password:
                flash('两次输入的新密码不一致', 'error')
                return render_template('franchisee/change_password.html', account=account)
            
            if check_password_hash(account.password, new_password):
                flash('新密码不能与当前密码相同', 'error')
                return render_template('franchisee/change_password.html', account=account)
            
            account.password = generate_password_hash(new_password)
            account.updated_at = datetime.now()
            
            db.session.commit()
            
            flash('密码修改成功，请重新登录', 'success')
            return redirect(url_for('franchisee.franchisee_logout'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'密码修改失败: {str(e)}', 'error')
    
    return render_template('franchisee/change_password.html', account=account)


@bp.route('/scan/<qr_code>')
def scan_franchisee_qrcode(qr_code):
    """处理加盟商二维码扫描"""
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('index'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    
    try:
        franchisee = FranchiseeAccount.query.filter_by(qr_code=qr_code, status='active').first()
        
        if not franchisee:
            flash('加盟商账户不存在或已禁用', 'error')
            return redirect(url_for('index'))
        
        if franchisee.remaining_quota <= 0:
            flash('加盟商账户额度不足，请联系管理员', 'error')
            return redirect(url_for('index'))
        
        session['franchisee_qr_code'] = qr_code
        session['franchisee_id'] = franchisee.id
        session['franchisee_company'] = franchisee.company_name
        
        return redirect(url_for('franchisee.franchisee_order_page', qr_code=qr_code))
        
    except Exception as e:
        flash(f'处理二维码失败: {str(e)}', 'error')
        return redirect(url_for('index'))


@bp.route('/fran-order', methods=['GET', 'POST'])
def franchisee_order():
    """加盟商独立下单页面"""
    franchisee_id = session.get('franchisee_id')
    if not franchisee_id:
        flash('请先登录', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Product = models['Product']
    ProductSize = models['ProductSize']
    ProductSizePetOption = models['ProductSizePetOption']
    ProductStyleCategory = models['ProductStyleCategory']
    ProductCustomField = models['ProductCustomField']
    StyleCategory = models['StyleCategory']
    StyleImage = models['StyleImage']
    Order = models['Order']
    OrderImage = models['OrderImage']
    FranchiseeRecharge = models['FranchiseeRecharge']
    User = models['User']
    db = models['db']
    app = models['app']
    allowed_file = models['allowed_file']
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    default_name = account.contact_person or ''
    default_phone = account.contact_phone or ''
    default_address = account.address or ''
    
    products = Product.query.filter_by(is_active=True).order_by(Product.sort_order.asc()).all()
    product_sizes = {}
    product_style_categories = {}
    products_list = []
    
    for product in products:
        products_list.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'description': product.description,
            'image_url': product.image_url
        })
        
        sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).order_by(ProductSize.sort_order.asc()).all()
        product_sizes[product.id] = []
        for size in sizes:
            pet_options = ProductSizePetOption.query.filter_by(size_id=size.id).order_by(ProductSizePetOption.sort_order.asc()).all()
            size_data = {
                'id': size.id,
                'size_name': size.size_name,
                'price': size.price,
                'printer_product_id': size.printer_product_id,
                'pet_options': [
                    {
                        'id': opt.id,
                        'pet_count_name': opt.pet_count_name,
                        'price': opt.price
                    }
                    for opt in pet_options
                ]
            }
            if not pet_options:
                size_data['pet_options'] = [{
                    'id': 0,
                    'pet_count_name': '默认',
                    'price': size.price
                }]
            product_sizes[product.id].append(size_data)
        
        product_style_relations = ProductStyleCategory.query.filter_by(product_id=product.id).all()
        bound_category_ids = [rel.style_category_id for rel in product_style_relations]
        product_style_categories[product.id] = bound_category_ids
    
    product_custom_fields = {}
    for product in products:
        custom_fields = ProductCustomField.query.filter_by(product_id=product.id).order_by(ProductCustomField.sort_order.asc()).all()
        product_custom_fields[product.id] = [
            {
                'id': field.id,
                'field_name': field.field_name,
                'field_type': field.field_type,
                'field_options': field.field_options,
                'is_required': field.is_required
            }
            for field in custom_fields
        ]
    
    all_style_categories_list = StyleCategory.query.filter_by(is_active=True).order_by(StyleCategory.sort_order.asc()).all()
    all_style_categories = [
        {
            'id': cat.id,
            'name': cat.name,
            'code': cat.code,
            'description': cat.description,
            'icon': cat.icon,
            'cover_image': cat.cover_image
        }
        for cat in all_style_categories_list
    ]
    all_style_images = {}
    for category in all_style_categories_list:
        images = StyleImage.query.filter_by(category_id=category.id, is_active=True).order_by(StyleImage.sort_order.asc()).all()
        all_style_images[category.id] = [
            {
                'id': img.id,
                'name': img.name,
                'code': img.code,
                'description': img.description,
                'image_url': img.image_url
            }
            for img in images
        ]
    
    if request.method == 'POST':
        try:
            customer_name = request.form['customer_name']
            customer_phone = request.form['customer_phone']
            product_id = request.form.get('product_id')
            size_id = request.form.get('size_id')
            style_id = request.form.get('style_id_real')
            shipping_info = request.form.get('full_address', '').strip()
            customer_note = request.form.get('customer_note', '').strip()
            
            selected_product = Product.query.get(product_id)
            selected_size = ProductSize.query.get(size_id)
            
            selected_style_name = ''
            if style_id:
                style_image = StyleImage.query.get(style_id)
                if style_image:
                    selected_style_name = style_image.name
            
            if not selected_product or not selected_size:
                flash('请选择有效的产品和尺寸', 'error')
                return render_template('franchisee/fran_order_new.html', 
                                     account=account, 
                                     products=products, 
                                     products_list=products_list,
                                     product_sizes=product_sizes,
                                     product_style_categories=product_style_categories,
                                     product_custom_fields=product_custom_fields,
                                     all_style_categories=all_style_categories,
                                     all_style_images=all_style_images,
                                     default_name=default_name,
                                     default_phone=default_phone,
                                     default_address=default_address)
            
            price = selected_size.price
            pet_option_id = request.form.get('pet_option_id')
            pet_options = ProductSizePetOption.query.filter_by(size_id=selected_size.id).all()
            
            if len(pet_options) > 1:
                if not pet_option_id or pet_option_id.strip() == '':
                    flash('请选择宠物数量', 'error')
                    return render_template('franchisee/fran_order_new.html', 
                                         account=account, 
                                         products=products, 
                                         products_list=products_list,
                                         product_sizes=product_sizes,
                                         product_style_categories=product_style_categories,
                                         product_custom_fields=product_custom_fields,
                                         all_style_categories=all_style_categories,
                                         all_style_images=all_style_images,
                                         default_name=default_name,
                                         default_phone=default_phone,
                                         default_address=default_address)
            
            if pet_option_id:
                try:
                    pet_option = ProductSizePetOption.query.get(int(pet_option_id))
                    if pet_option and pet_option.size_id == selected_size.id:
                        price = pet_option.price
                    elif len(pet_options) > 1:
                        flash('选择的宠物数量选项无效', 'error')
                        return render_template('franchisee/fran_order_new.html', 
                                             account=account, 
                                             products=products, 
                                             products_list=products_list,
                                             product_sizes=product_sizes,
                                             product_style_categories=product_style_categories,
                                             product_custom_fields=product_custom_fields,
                                             all_style_categories=all_style_categories,
                                             all_style_images=all_style_images,
                                             default_name=default_name,
                                             default_phone=default_phone,
                                             default_address=default_address)
                except (ValueError, TypeError):
                    if len(pet_options) > 1:
                        flash('宠物数量选项ID格式错误', 'error')
                        return render_template('franchisee/fran_order_new.html', 
                                             account=account, 
                                             products=products, 
                                             products_list=products_list,
                                             product_sizes=product_sizes,
                                             product_style_categories=product_style_categories,
                                             product_custom_fields=product_custom_fields,
                                             all_style_categories=all_style_categories,
                                             all_style_images=all_style_images,
                                             default_name=default_name,
                                             default_phone=default_phone,
                                             default_address=default_address)
            
            if account.remaining_quota < price:
                flash(f'加盟商账户额度不足，当前剩余额度：{account.remaining_quota}元，订单金额：{price}元', 'error')
                return render_template('franchisee/fran_order_new.html', 
                                     account=account, 
                                     products=products, 
                                     products_list=products_list,
                                     product_sizes=product_sizes,
                                     product_style_categories=product_style_categories,
                                     product_custom_fields=product_custom_fields,
                                     all_style_categories=all_style_categories,
                                     all_style_images=all_style_images,
                                     default_name=default_name,
                                     default_phone=default_phone,
                                     default_address=default_address)
            
            if 'images' not in request.files:
                flash('请上传图片', 'error')
                return render_template('franchisee/fran_order_new.html', 
                                     account=account, 
                                     products=products, 
                                     products_list=products_list,
                                     product_sizes=product_sizes,
                                     product_style_categories=product_style_categories,
                                     product_custom_fields=product_custom_fields,
                                     all_style_categories=all_style_categories,
                                     all_style_images=all_style_images,
                                     default_name=default_name,
                                     default_phone=default_phone,
                                     default_address=default_address)
            
            files = request.files.getlist('images')
            if not files or files[0].filename == '':
                flash('请选择图片文件', 'error')
                return render_template('franchisee/fran_order_new.html', 
                                     account=account, 
                                     products=products, 
                                     products_list=products_list,
                                     product_sizes=product_sizes,
                                     product_style_categories=product_style_categories,
                                     product_custom_fields=product_custom_fields,
                                     all_style_categories=all_style_categories,
                                     all_style_images=all_style_images,
                                     default_name=default_name,
                                     default_phone=default_phone,
                                     default_address=default_address)
            
            saved_filenames = []
            for i, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    forbidden_keywords = ['ComfyUI_temp', '_temp_', 'ComfyUI', 'temp_temp']
                    if any(keyword in filename for keyword in forbidden_keywords):
                        print(f"⚠️ 检测到包含禁用关键字的文件名: {filename}, 跳过此文件")
                        flash(f'文件 {filename} 包含非法字符，请重新上传正确的图片', 'warning')
                        continue
                    
                    timestamp = int(time.time())
                    unique_filename = f"{timestamp}_{i}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    saved_filenames.append(unique_filename)
            
            if not saved_filenames:
                flash('图片上传失败', 'error')
                return render_template('franchisee/fran_order_new.html', 
                                     account=account, 
                                     products=products, 
                                     products_list=products_list,
                                     product_sizes=product_sizes,
                                     product_style_categories=product_style_categories,
                                     product_custom_fields=product_custom_fields,
                                     all_style_categories=all_style_categories,
                                     all_style_images=all_style_images,
                                     default_name=default_name,
                                     default_phone=default_phone,
                                     default_address=default_address)
            
            order_number = f"PET{int(time.time())}{franchisee_id:04d}"
            need_confirmation = request.form.get('need_confirmation') == '1'
            
            custom_fields_data = {}
            custom_fields = ProductCustomField.query.filter_by(product_id=product_id).all()
            for field in custom_fields:
                field_key = f"custom_field_{field.id}"
                field_value = request.form.get(field_key, '').strip()
                if field_value or field.is_required:
                    custom_fields_data[field.field_name] = field_value
            
            custom_fields_json = json.dumps(custom_fields_data, ensure_ascii=False) if custom_fields_data else None
            
            order = Order(
                order_number=order_number,
                customer_name=customer_name,
                customer_phone=customer_phone,
                size=selected_size.size_name,
                style_name=selected_style_name,
                product_name=f"{selected_product.name} - {selected_size.size_name}",
                price=price,
                status='pending',
                shipping_info=shipping_info,
                franchisee_id=franchisee_id,
                franchisee_deduction=price,
                original_image=saved_filenames[0] if saved_filenames else '',
                source_type='franchisee',
                product_type=selected_product.code,
                need_confirmation=need_confirmation,
                confirmation_deadline=datetime.now() + timedelta(days=3) if need_confirmation else None,
                customer_note=customer_note,
                custom_fields=custom_fields_json
            )
            
            db.session.add(order)
            db.session.flush()
            
            main_image_index = request.form.get('main_image_index', '')
            try:
                main_index = int(main_image_index) if main_image_index else 0
            except (ValueError, TypeError):
                main_index = 0
            
            for i, filename in enumerate(saved_filenames):
                order_image = OrderImage(
                    order_id=order.id,
                    path=filename,
                    is_main=(i == main_index)
                )
                db.session.add(order_image)
                print(f"保存订单图片 - 订单ID: {order.id}, 图片索引: {i}, 文件名: {filename}, 是否主图: {i == main_index}")
            
            print(f"总共保存了 {len(saved_filenames)} 张图片到订单 {order.id}")
            
            account.used_quota += price
            account.remaining_quota -= price
            
            admin_user = User.query.filter_by(username='admin').first()
            admin_user_id = admin_user.id if admin_user else 1
            
            recharge_record = FranchiseeRecharge(
                franchisee_id=franchisee_id,
                amount=-price,
                admin_user_id=admin_user_id,
                recharge_type='deduction',
                description=f'订单 {order_number} 扣除'
            )
            db.session.add(recharge_record)
            
            db.session.commit()
            
            wechat_notify, WECHAT_NOTIFICATION_AVAILABLE = get_wechat_notification()
            if WECHAT_NOTIFICATION_AVAILABLE and wechat_notify:
                try:
                    wechat_notify(
                        order_number=order_number,
                        customer_name=customer_name,
                        total_price=price,
                        source='加盟商'
                    )
                    print(f"✅ 加盟商订单微信通知已发送: {order_number}")
                except Exception as e:
                    print(f"❌ 加盟商订单微信通知失败: {e}")
            
            flash(f'订单创建成功！订单号：{order_number}', 'success')
            return redirect(url_for('franchisee.franchisee_frontend.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            flash(f'订单创建失败：{error_msg}', 'error')
            print(f"订单创建错误: {error_msg}")
            
            if 'is_main' in error_msg and 'no column' in error_msg.lower():
                flash('数据库字段缺失，请联系管理员运行数据库迁移脚本', 'error')
    
    return render_template('franchisee/fran_order_new.html', 
                         account=account, 
                         products=products,
                         products_list=products_list,
                         product_sizes=product_sizes,
                         product_style_categories=product_style_categories,
                         product_custom_fields=product_custom_fields,
                         all_style_categories=all_style_categories,
                         all_style_images=all_style_images,
                         default_name=default_name,
                         default_phone=default_phone,
                         default_address=default_address)


@bp.route('/order/<qr_code>', methods=['GET', 'POST'])
def franchisee_order_page(qr_code):
    """加盟商专用下单页面"""
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('index'))
    
    FranchiseeAccount = models['FranchiseeAccount']
    Order = models['Order']
    db = models['db']
    app = models['app']
    allowed_file = models['allowed_file']
    
    try:
        franchisee = FranchiseeAccount.query.filter_by(qr_code=qr_code, status='active').first()
        
        if not franchisee:
            flash('加盟商账户不存在或已禁用', 'error')
            return redirect(url_for('index'))
        
        if franchisee.remaining_quota <= 0:
            flash('加盟商账户额度不足，请联系管理员', 'error')
            return redirect(url_for('index'))
        
        session['franchisee_qr_code'] = qr_code
        session['franchisee_id'] = franchisee.id
        session['franchisee_company'] = franchisee.company_name
        
        if request.method == 'POST':
            try:
                customer_name = request.form['name']
                customer_phone = request.form['phone']
                product_type = request.form.get('product_type', 'standard')
                
                product_prices = {
                    'standard': 299,
                    'premium': 399,
                    'luxury': 599
                }
                
                price = product_prices.get(product_type, 299)
                
                if franchisee.remaining_quota < price:
                    flash(f'加盟商账户额度不足，当前剩余额度：{franchisee.remaining_quota}元，订单金额：{price}元', 'error')
                    return render_template('franchisee/order.html', franchisee=franchisee)
                
                if 'image' not in request.files:
                    flash('请上传图片', 'error')
                    return render_template('franchisee/order.html', franchisee=franchisee)
                
                file = request.files['image']
                if file.filename == '':
                    flash('请选择图片文件', 'error')
                    return render_template('franchisee/order.html', franchisee=franchisee)
                
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    order = Order(
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        original_image=filename,
                        price=price,
                        status='pending',
                        franchisee_id=franchisee.id,
                        franchisee_deduction=price,
                        order_source='franchisee',
                        product_type=product_type
                    )
                    
                    db.session.add(order)
                    
                    franchisee.used_quota += price
                    franchisee.remaining_quota -= price
                    
                    db.session.commit()
                    
                    wechat_notify, WECHAT_NOTIFICATION_AVAILABLE = get_wechat_notification()
                    if WECHAT_NOTIFICATION_AVAILABLE and wechat_notify:
                        try:
                            wechat_notify(
                                order_number=order.order_number if hasattr(order, 'order_number') else f"加盟商{order.id}",
                                customer_name=customer_name,
                                total_price=price,
                                source='加盟商'
                            )
                            print(f"✅ 加盟商订单（二维码）微信通知已发送: {order.id}")
                        except Exception as e:
                            print(f"❌ 加盟商订单微信通知失败: {e}")
                    
                    flash(f'订单创建成功！订单金额：{price}元，已从加盟商账户扣除', 'success')
                    return redirect(url_for('franchisee.franchisee_order_page', qr_code=qr_code))
                else:
                    flash('不支持的文件格式', 'error')
                    return render_template('franchisee/order.html', franchisee=franchisee)
                    
            except Exception as e:
                db.session.rollback()
                flash(f'订单创建失败：{str(e)}', 'error')
                return render_template('franchisee/order.html', franchisee=franchisee)
        
        return render_template('franchisee/order.html', franchisee=franchisee)
        
    except Exception as e:
        flash(f'页面加载失败：{str(e)}', 'error')
        return redirect(url_for('index'))
