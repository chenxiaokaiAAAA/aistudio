# -*- coding: utf-8 -*-
"""
商户管理路由模块
包含商户端和管理端的商户管理功能
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, make_response, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import sys
import os
import qrcode
import base64
from io import BytesIO

# 创建蓝图
merchant_bp = Blueprint('merchant', __name__)


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'User': test_server_module.User,
        'Order': test_server_module.Order,
        'OrderImage': test_server_module.OrderImage,
        'get_base_url': test_server_module.get_base_url,
        'generate_qr_code': test_server_module.generate_qr_code,
    }


# ============================================================================
# 商户端路由
# ============================================================================

@merchant_bp.route('/merchant/dashboard')
@login_required
def merchant_dashboard():
    """商户控制台"""
    if current_user.role != 'merchant':
        # 如果是管理员，跳回管理员控制台
        if current_user.is_authenticated and current_user.role == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    Order = models['Order']
    db = models['db']
    generate_qr_code = models['generate_qr_code']
    
    orders = Order.query.filter_by(merchant_id=current_user.id).all()
    # 只计算高清放大和已发货状态的佣金
    total_commission = sum(order.commission for order in orders if order.status in ['hd_ready', 'delivered'])
    
    # 详细佣金统计
    completed_orders = Order.query.filter_by(merchant_id=current_user.id, status='completed').all()
    completed_commission = sum(order.commission for order in completed_orders if order.status in ['hd_ready', 'delivered'])
    
    pending_orders = Order.query.filter_by(merchant_id=current_user.id, status='pending').all()
    processing_orders = Order.query.filter_by(merchant_id=current_user.id, status='processing').all()
    delivered_orders = Order.query.filter_by(merchant_id=current_user.id, status='delivered').all()
    
    # 按来源统计
    website_orders = Order.query.filter_by(merchant_id=current_user.id, source_type='website').all()
    miniprogram_orders = Order.query.filter_by(merchant_id=current_user.id, source_type='miniprogram').all()
    
    website_commission = sum(order.commission for order in website_orders if order.status in ['hd_ready', 'delivered'])
    miniprogram_commission = sum(order.commission for order in miniprogram_orders if order.status in ['hd_ready', 'delivered'])
    
    # 当月佣金统计
    current_month_start = date.today().replace(day=1)
    current_month_orders = Order.query.filter(
        Order.merchant_id == current_user.id,
        Order.created_at >= current_month_start
    ).all()
    current_month_commission = sum(order.commission for order in current_month_orders if order.status in ['hd_ready', 'delivered'])
    
    # 生成或获取商家二维码
    if not current_user.qr_code:
        qr_id, qr_image = generate_qr_code(current_user.id)
        current_user.qr_code = qr_id
        db.session.commit()
    else:
        get_base_url = models['get_base_url']
        url = f"{get_base_url()}/order?merchant={current_user.qr_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return render_template('merchant/dashboard.html', 
                          orders=orders, 
                          total_commission=total_commission,
                          completed_commission=completed_commission,
                          current_month_commission=current_month_commission,
                          pending_orders=len(pending_orders),
                          processing_orders=len(processing_orders),
                          delivered_orders=len(delivered_orders),
                          website_orders=len(website_orders),
                          miniprogram_orders=len(miniprogram_orders),
                          website_commission=website_commission,
                          miniprogram_commission=miniprogram_commission,
                          qr_image=qr_image)


@merchant_bp.route('/merchant/order/<int:order_id>')
@login_required
def merchant_order_detail(order_id):
    """商户查看单个订单详情"""
    if current_user.role != 'merchant':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    Order = models['Order']
    OrderImage = models['OrderImage']
    
    order = Order.query.get_or_404(order_id)
    images = OrderImage.query.filter_by(order_id=order.id).all()
    # 仅允许查看自己的订单
    if order.merchant_id != current_user.id:
        return redirect(url_for('merchant.merchant_dashboard'))
    return render_template('merchant/order.html', order=order, images=images)


@merchant_bp.route('/merchant/qrcode.png')
@login_required
def merchant_self_qrcode_image():
    """商家端：直接获取自己的二维码图片"""
    if current_user.role != 'merchant':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        return redirect(url_for('auth.login'))
    
    db = models['db']
    generate_qr_code = models['generate_qr_code']
    get_base_url = models['get_base_url']
    
    merchant = current_user
    if not merchant.qr_code:
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()
    url = f"{get_base_url()}/order?merchant={merchant.qr_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers.set('Content-Type', 'image/png')
    return response


@merchant_bp.route('/merchant/qrcode/download')
@login_required
def merchant_self_qrcode_download():
    """商家端：下载自己的二维码"""
    if current_user.role != 'merchant':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        return redirect(url_for('auth.login'))
    
    db = models['db']
    generate_qr_code = models['generate_qr_code']
    get_base_url = models['get_base_url']
    
    merchant = current_user
    if not merchant.qr_code:
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()
    url = f"{get_base_url()}/order?merchant={merchant.qr_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    filename = f"merchant_{merchant.id}_qrcode.png"
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=filename)


# ============================================================================
# 管理端商户管理路由
# ============================================================================

@merchant_bp.route('/admin/merchants')
@login_required
def merchants_list():
    """商家列表页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    User = models['User']
    Order = models['Order']
    
    merchants = User.query.filter_by(role='merchant').all()
    # 预计算统计数据供模板展示
    merchant_stats = []
    for merchant in merchants:
        orders = Order.query.filter_by(merchant_id=merchant.id).all()
        total_commission = sum(order.commission for order in orders)
        order_count = len(orders)
        merchant_stats.append({
            'merchant': merchant,
            'total_commission': total_commission,
            'order_count': order_count,
        })
    return render_template('admin/merchants.html', merchant_stats=merchant_stats)


@merchant_bp.route('/admin/merchant/<int:merchant_id>')
@login_required
def merchant_details(merchant_id):
    """商家详情页面"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    User = models['User']
    Order = models['Order']
    
    merchant = User.query.get_or_404(merchant_id)
    if merchant.role != 'merchant':
        return redirect(url_for('merchant.merchants_list'))
    orders = Order.query.filter_by(merchant_id=merchant.id).order_by(Order.created_at.desc()).all()
    total_commission = sum(order.commission for order in orders)
    return render_template('admin/merchant_details.html', merchant=merchant, orders=orders, total_commission=total_commission)


@merchant_bp.route('/admin/merchant/<int:merchant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_merchant(merchant_id):
    """编辑商家"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    User = models['User']
    db = models['db']
    
    merchant = User.query.get_or_404(merchant_id)
    if request.method == 'POST':
        username = request.form['username'].strip()
        commission_rate = float(request.form['commission_rate'])
        
        # 更新基本信息
        merchant.username = username
        merchant.commission_rate = commission_rate
        
        # 更新联系方式
        merchant.contact_person = request.form.get('contact_person', '').strip() or None
        merchant.contact_phone = request.form.get('contact_phone', '').strip() or None
        merchant.wechat_id = request.form.get('wechat_id', '').strip() or None
        
        # 更新合作时间
        cooperation_date_str = request.form.get('cooperation_date', '').strip()
        if cooperation_date_str:
            try:
                merchant.cooperation_date = datetime.strptime(cooperation_date_str, '%Y-%m-%d').date()
            except ValueError:
                merchant.cooperation_date = None
        else:
            merchant.cooperation_date = None
        
        # 更新地址信息
        merchant.merchant_address = request.form.get('merchant_address', '').strip() or None
        
        # 更新银行信息
        merchant.account_name = request.form.get('account_name', '').strip() or None
        merchant.account_number = request.form.get('account_number', '').strip() or None
        merchant.bank_name = request.form.get('bank_name', '').strip() or None
        
        db.session.commit()
        flash('商家信息已更新', 'success')
        return redirect(url_for('merchant.merchant_details', merchant_id=merchant.id))
    return render_template('admin/merchant_edit.html', merchant=merchant)


@merchant_bp.route('/admin/merchant/<int:merchant_id>/delete', methods=['POST'])
@login_required
def delete_merchant(merchant_id):
    """删除商家"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    User = models['User']
    Order = models['Order']
    db = models['db']
    
    merchant = User.query.get_or_404(merchant_id)
    # 如果该商家名下有订单，不直接删除用户本身，可选择保留订单并置空 merchant_id
    for order in Order.query.filter_by(merchant_id=merchant.id).all():
        order.merchant_id = None
    db.session.delete(merchant)
    db.session.commit()
    flash('商家已删除', 'success')
    return redirect(url_for('merchant.merchants_list'))


@merchant_bp.route('/admin/merchant/<int:merchant_id>/qrcode.png')
@login_required
def merchant_qrcode_image(merchant_id):
    """按需生成并返回商家二维码图片"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        return redirect(url_for('auth.login'))
    
    User = models['User']
    db = models['db']
    generate_qr_code = models['generate_qr_code']
    get_base_url = models['get_base_url']
    
    merchant = User.query.get_or_404(merchant_id)
    if not merchant.qr_code:
        # 若还没有二维码标识，则生成并保存
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()

    url = f"{get_base_url()}/order?merchant={merchant.qr_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers.set('Content-Type', 'image/png')
    return response


@merchant_bp.route('/admin/merchant/<int:merchant_id>/qrcode/download')
@login_required
def merchant_qrcode_download(merchant_id):
    """下载商家二维码"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        return redirect(url_for('auth.login'))
    
    User = models['User']
    db = models['db']
    generate_qr_code = models['generate_qr_code']
    get_base_url = models['get_base_url']
    
    merchant = User.query.get_or_404(merchant_id)
    if not merchant.qr_code:
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()

    url = f"{get_base_url()}/order?merchant={merchant.qr_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    filename = f"merchant_{merchant.id}_qrcode.png"
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=filename)


@merchant_bp.route('/admin/add_merchant', methods=['GET', 'POST'])
@login_required
def add_merchant():
    """添加商家"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    User = models['User']
    db = models['db']
    generate_qr_code = models['generate_qr_code']
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        commission_rate = float(request.form['commission_rate'])
        contact_person = request.form.get('contact_person', '')
        contact_phone = request.form.get('contact_phone', '')
        wechat_id = request.form.get('wechat_id', '')
        # 新增字段
        cooperation_date = request.form.get('cooperation_date')
        merchant_address = request.form.get('merchant_address', '')
        account_name = request.form.get('account_name', '')
        account_number = request.form.get('account_number', '')
        bank_name = request.form.get('bank_name', '')
        
        # 生成二维码
        qr_id, _ = generate_qr_code(None)
        
        new_merchant = User(
            username=username,
            password=generate_password_hash(password),
            role='merchant',
            commission_rate=commission_rate,
            qr_code=qr_id,
            contact_person=contact_person,
            contact_phone=contact_phone,
            wechat_id=wechat_id,
            cooperation_date=datetime.strptime(cooperation_date, '%Y-%m-%d').date() if cooperation_date else None,
            merchant_address=merchant_address,
            account_name=account_name,
            account_number=account_number,
            bank_name=bank_name
        )
        
        db.session.add(new_merchant)
        db.session.commit()
        flash('商家已添加成功', 'success')
        return redirect(url_for('merchant.merchants_list'))
    
    return render_template('admin/add_merchant.html')
