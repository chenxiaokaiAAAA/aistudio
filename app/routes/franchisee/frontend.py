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
    
    account = FranchiseeAccount.query.get(franchisee_id)
    if not account or account.status != 'active':
        flash('账户不存在或已被禁用', 'error')
        return redirect(url_for('franchisee.franchisee_frontend.franchisee_login'))
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    recent_orders = Order.query.filter(
        Order.franchisee_id == franchisee_id,
        Order.created_at >= thirty_days_ago
    ).order_by(desc(Order.created_at)).all()
    
    recent_recharges = FranchiseeRecharge.query.filter(
        FranchiseeRecharge.franchisee_id == franchisee_id,
        FranchiseeRecharge.created_at >= thirty_days_ago
    ).order_by(desc(FranchiseeRecharge.created_at)).all()
    
    total_orders = len(recent_orders)
    total_amount = sum(order.price for order in recent_orders if order.price)
    total_deduction = sum(order.franchisee_deduction for order in recent_orders if order.franchisee_deduction)
    
    return render_template('franchisee/dashboard.html',
                         account=account,
                         recent_orders=recent_orders,
                         recent_recharges=recent_recharges,
                         total_orders=total_orders,
                         total_amount=total_amount,
                         total_deduction=total_deduction)


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
        
        qr_content = f"https://moeart.cc/franchisee/scan/{account.qr_code}"
        
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
    """加盟商订单列表"""
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
    
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Order.query.filter_by(franchisee_id=franchisee_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Order.created_at <= end_dt)
        except ValueError:
            pass
    
    orders = query.order_by(desc(Order.created_at)).all()
    
    order_images_dict = {}
    for order in orders:
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
                    def __init__(self, id, path, is_main):
                        self.id = id
                        self.path = path
                        self.is_main = bool(is_main) if is_main is not None else False
                images.append(ImageObj(img_id, path, is_main))
            order_images_dict[order.id] = images
        except Exception as e:
            try:
                images = OrderImage.query.filter_by(order_id=order.id).all()
                order_images_dict[order.id] = images
            except Exception as e2:
                print(f"查询订单 {order.id} 图片失败: {e2}")
                order_images_dict[order.id] = []
    
    return render_template('franchisee/orders.html',
                         account=account,
                         orders=orders,
                         order_images_dict=order_images_dict,
                         status=status,
                         start_date=start_date,
                         end_date=end_date)


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
