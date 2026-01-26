from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, session, send_file, make_response, flash
import csv
import io
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import shutil
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import zipfile
from PIL import Image
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
# Proxy headers (X-Forwarded-*) support when behind nginx/elb
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Environment-driven configuration for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pet_painting.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['FINAL_FOLDER'] = os.environ.get('FINAL_FOLDER', 'final_works')
# Upload size limit (e.g., 20MB). Match reverse proxy setting like nginx client_max_body_size
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH_MB', '20')) * 1024 * 1024

# Secure cookies in production
is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
if is_production:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True

# 图片过期天数配置（可调整）
IMAGE_EXPIRE_DAYS = 30  # 30天过期

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FINAL_FOLDER'], exist_ok=True)


def cleanup_expired_images():
    """清理过期的图片文件"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        current_time = datetime.now()
        deleted_count = 0
        
        # 遍历上传文件夹中的所有文件
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            
            # 只处理文件，跳过文件夹
            if not os.path.isfile(file_path):
                continue
                
            try:
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                # 计算文件修改时间到现在的天数
                days_old = (current_time - file_mtime).days
                
                # 如果超过过期天数，删除文件
                if days_old > IMAGE_EXPIRE_DAYS:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"已删除过期文件: {filename} (修改于 {days_old} 天前)")
                    
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {e}")
                continue
                
        print(f"图片清理完成，共删除 {deleted_count} 个过期文件")
        return deleted_count
        
    except Exception as e:
        print(f"清理过期图片时出错: {e}")
        return 0

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.remember_cookie_duration = 60 * 60 * 24 * 14  # 14天（秒）

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'merchant'
    commission_rate = db.Column(db.Float, default=0.1)  # 分佣比例，默认为10%
    qr_code = db.Column(db.String(100), unique=True)  # 二维码标识
    contact_person = db.Column(db.String(100))  # 联系人
    contact_phone = db.Column(db.String(20))  # 联系电话
    wechat_id = db.Column(db.String(50))  # 微信号
    # 抖音相关字段
    douyin_openid = db.Column(db.String(100), unique=True)  # 抖音OpenID
    douyin_unionid = db.Column(db.String(100))  # 抖音UnionID
    douyin_nickname = db.Column(db.String(100))  # 抖音昵称
    douyin_avatar = db.Column(db.String(200))  # 抖音头像URL
    douyin_phone = db.Column(db.String(20))  # 抖音手机号
    import_source = db.Column(db.String(20), default='manual')  # 导入来源：manual/douyin

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    size = db.Column(db.String(20))  # 尺寸
    original_image = db.Column(db.String(200), nullable=False)  # 原图路径（兼容旧字段，取第一张）
    final_image = db.Column(db.String(200))  # 成品图路径
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, shipped
    shipping_info = db.Column(db.String(500))  # 物流信息
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    merchant = db.relationship('User', backref=db.backref('orders', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)
    commission = db.Column(db.Float, default=0.0)  # 佣金金额
    price = db.Column(db.Float, default=0.0)  # 订单价格
    external_platform = db.Column(db.String(50))  # 外部渠道（如 淘宝/抖音/小红书/公众号）
    external_order_number = db.Column(db.String(100))  # 外部平台订单号

class OrderImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

# 商品尺寸配置
class SizeOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # 如 small/medium
    name = db.Column(db.String(50), nullable=False)  # 显示名，如 小型 (30x40cm)
    price = db.Column(db.Float, nullable=False, default=50.0)

# 尺寸显示名过滤器：根据 code 显示配置名称，若无配置则回退到默认文案
@app.template_filter('size_name')
def size_name_filter(code):
    try:
        opt = SizeOption.query.filter_by(code=code).first()
        if opt:
            return opt.name
    except Exception:
        pass
    default_map = {
        'small': '小型 (30x40cm)',
        'medium': '中型 (40x50cm)',
        'large': '大型 (50x70cm)',
        'xlarge': '超大型 (70x100cm)'
    }
    return default_map.get(code, code or '')

# 生成商家二维码
def generate_qr_code(merchant_id):
    qr_id = str(uuid.uuid4())[:8]
    url = f"{request.host_url}order?merchant={qr_id}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # 转换为base64以便存储和显示
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_id, img_base64

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    return render_template('index.html')

# 统一入口，根据角色跳转到相应控制台
@app.route('/dashboard')
@login_required
def dashboard_redirect():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    if current_user.role == 'merchant':
        return redirect(url_for('merchant_dashboard'))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # 记住登录，维持会话
            login_user(user, remember=True)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('merchant_dashboard'))
        # 兼容旧数据：若存的是明文密码，首次登录时自动迁移为哈希
        if user and user.password == password:
            user.password = generate_password_hash(password)
            db.session.commit()
            login_user(user, remember=True)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('merchant_dashboard'))
        flash('用户名或密码错误', 'error')
        return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/order', methods=['GET', 'POST'])
def create_order():
    merchant_id = request.args.get('merchant')
    merchant = None
    
    if merchant_id:
        merchant = User.query.filter_by(qr_code=merchant_id).first()
    
    # 读取尺寸配置供模板渲染（暂时隐藏前端使用，但仍可用于价格默认值）
    size_options = SizeOption.query.order_by(SizeOption.price.asc()).all()

    if request.method == 'POST':
        customer_name = request.form['name']
        customer_phone = request.form['phone']
        # 尺寸可暂时不用，通过渠道/外部订单号下单
        size = request.form.get('size') or ''
        external_platform = request.form.get('external_platform')
        external_order_number = request.form.get('external_order_number')
        images = request.files.getlist('images') or ([] if 'image' not in request.files else [request.files['image']])
        
        if images:
            saved_filenames = []
            
            for img in images:
                if not img or img.filename == '':
                    continue
                filename = secure_filename(f"{uuid.uuid4()}_{img.filename}")
                # 直接保存到uploads根目录
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img.save(image_path)
                # 保存文件名（不包含路径）
                saved_filenames.append(filename)
            
            # 生成订单号（使用 UUID hex 防止 TypeError）
            order_number = f"PET{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            
            # 创建订单
            # 计算价格（按尺寸配置，找不到则使用默认50）
            if size:
                opt = SizeOption.query.filter_by(code=size).first()
                price = opt.price if opt else 50.0
            else:
                price = 50.0  # 未选择尺寸时使用默认价格

            new_order = Order(
                order_number=order_number,
                customer_name=customer_name,
                customer_phone=customer_phone,
                size=size,
                price=price,
                external_platform=external_platform,
                external_order_number=external_order_number,
                original_image=saved_filenames[0] if saved_filenames else '',
                merchant=merchant
            )
            
            db.session.add(new_order)
            db.session.commit()

            # 保存多图到关联表
            for fname in saved_filenames:
                db.session.add(OrderImage(order_id=new_order.id, path=fname))
            db.session.commit()
            
            return render_template('order_success.html', order_number=order_number)
    
    return render_template('order.html', merchant=merchant, size_options=size_options)

# 订单状态查询（用户无需登录）：通过订单号 + 手机号后4位验证
@app.route('/order/status', methods=['GET', 'POST'])
def order_status():
    order = None
    images = []
    orders = []
    # 支持 GET 直接查看指定订单
    if request.method == 'GET' and request.args.get('order_number') and request.args.get('phone_last4'):
        on = request.args.get('order_number')
        last4 = (request.args.get('phone_last4') or '').strip()
        q = Order.query.filter_by(order_number=on).first()
        if q and q.customer_phone.endswith(last4):
            order = q
            images = OrderImage.query.filter_by(order_id=order.id).all()
    if request.method == 'POST':
        order_number = request.form.get('order_number')
        phone_last4 = (request.form.get('phone_last4') or '').strip()
        name = (request.form.get('name') or '').strip()
        if order_number:
            q = Order.query.filter_by(order_number=order_number).first()
            if q and q.customer_phone.endswith(phone_last4):
                order = q
                images = OrderImage.query.filter_by(order_id=order.id).all()
        else:
            # 按姓名 + 手机号后4位匹配，返回最近的订单，并列出所有匹配
            if phone_last4 and name:
                like_pattern = f"%{phone_last4}"
                orders = (Order.query
                          .filter(Order.customer_name == name)
                          .filter(Order.customer_phone.like(like_pattern))
                          .order_by(Order.created_at.desc())
                          .all())
                if orders:
                    order = orders[0]
                    images = OrderImage.query.filter_by(order_id=order.id).all()
    return render_template('order_status.html', order=order, images=images, orders=orders)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        # 如果是商家，跳转到商家控制台
        if current_user.is_authenticated and current_user.role == 'merchant':
            return redirect(url_for('merchant_dashboard'))
        return redirect(url_for('login'))
    
    orders = Order.query.all()
    merchants = User.query.filter_by(role='merchant').all()
    return render_template('admin/dashboard.html', orders=orders, merchants=merchants)

# 管理端：尺寸配置列表与新增
@app.route('/admin/sizes', methods=['GET', 'POST'])
@login_required
def admin_sizes():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        price = float(request.form['price'])
        # 简单防重
        if not SizeOption.query.filter_by(code=code).first():
            db.session.add(SizeOption(code=code, name=name, price=price))
            db.session.commit()
        return redirect(url_for('admin_sizes'))
    sizes = SizeOption.query.order_by(SizeOption.price.asc()).all()
    return render_template('admin/sizes.html', sizes=sizes)

@app.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def admin_order_detail(order_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    order = Order.query.get_or_404(order_id)
    images = OrderImage.query.filter_by(order_id=order.id).all()
    size_options = SizeOption.query.order_by(SizeOption.price.asc()).all()
    
    if request.method == 'POST':
        if 'final_image' in request.files:
            final_image = request.files['final_image']
            if final_image:
                filename = secure_filename(f"final_{uuid.uuid4()}_{final_image.filename}")
                image_path = os.path.join(app.config['FINAL_FOLDER'], filename)
                final_image.save(image_path)
                order.final_image = filename
        
        # 更新尺寸和价格
        new_size = request.form['size']
        size_option = SizeOption.query.filter_by(code=new_size).first()
        if size_option:
            order.size = new_size
            order.price = size_option.price
        
        order.status = request.form['status']
        order.shipping_info = request.form['shipping_info']
        
        # 如果订单高清放大或已发货，计算佣金（按订单价格与商家分佣比例）
        if order.status in ['hd_ready', 'shipped'] and order.completed_at is None:
            order.completed_at = datetime.utcnow()
            if order.merchant:
                base_price = order.price or 0.0
                order.commission = base_price * (order.merchant.commission_rate or 0.0)
        
        db.session.commit()
        return redirect(url_for('admin_order_detail', order_id=order_id))
    
    return render_template('admin/order_details.html', order=order, images=images, size_options=size_options)

# 删除订单（管理员）
@app.route('/admin/order/<int:order_id>/delete', methods=['POST'])
@login_required
def admin_order_delete(order_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('订单已删除', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/merchant/dashboard')
@login_required
def merchant_dashboard():
    if current_user.role != 'merchant':
        # 如果是管理员，跳回管理员控制台
        if current_user.is_authenticated and current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(merchant_id=current_user.id).all()
    # 只计算高清放大和已发货状态的佣金
    total_commission = sum(order.commission for order in orders if order.status in ['hd_ready', 'shipped'])
    
    # 详细佣金统计
    completed_orders = Order.query.filter_by(merchant_id=current_user.id, status='completed').all()
    completed_commission = sum(order.commission for order in completed_orders if order.status in ['hd_ready', 'shipped'])
    
    pending_orders = Order.query.filter_by(merchant_id=current_user.id, status='pending').all()
    processing_orders = Order.query.filter_by(merchant_id=current_user.id, status='processing').all()
    shipped_orders = Order.query.filter_by(merchant_id=current_user.id, status='shipped').all()
    
    # 按来源统计
    website_orders = Order.query.filter_by(merchant_id=current_user.id, source_type='website').all()
    miniprogram_orders = Order.query.filter_by(merchant_id=current_user.id, source_type='miniprogram').all()
    
    website_commission = sum(order.commission for order in website_orders if order.status in ['hd_ready', 'shipped'])
    miniprogram_commission = sum(order.commission for order in miniprogram_orders if order.status in ['hd_ready', 'shipped'])
    
    # 当月佣金统计
    from datetime import datetime, date
    current_month_start = date.today().replace(day=1)
    current_month_orders = Order.query.filter(
        Order.merchant_id == current_user.id,
        Order.created_at >= current_month_start
    ).all()
    current_month_commission = sum(order.commission for order in current_month_orders if order.status in ['hd_ready', 'shipped'])
    
    # 生成或获取商家二维码
    if not current_user.qr_code:
        qr_id, qr_image = generate_qr_code(current_user.id)
        current_user.qr_code = qr_id
        db.session.commit()
    else:
        url = f"{request.host_url}order?merchant={current_user.qr_code}"
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
                          shipped_orders=len(shipped_orders),
                          website_orders=len(website_orders),
                          miniprogram_orders=len(miniprogram_orders),
                          website_commission=website_commission,
                          miniprogram_commission=miniprogram_commission,
                          qr_image=qr_image)

# 商家端：直接获取自己的二维码图片
@app.route('/merchant/qrcode.png')
@login_required
def merchant_self_qrcode_image():
    if current_user.role != 'merchant':
        return redirect(url_for('login'))
    merchant = current_user
    if not merchant.qr_code:
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()
    url = f"{request.host_url}order?merchant={merchant.qr_code}"
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

# 商家端：下载自己的二维码
@app.route('/merchant/qrcode/download')
@login_required
def merchant_self_qrcode_download():
    if current_user.role != 'merchant':
        return redirect(url_for('login'))
    merchant = current_user
    if not merchant.qr_code:
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()
    url = f"{request.host_url}order?merchant={merchant.qr_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    filename = f"merchant_{merchant.id}_qrcode.png"
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=filename)

# 商家查看单个订单详情
@app.route('/merchant/order/<int:order_id>')
@login_required
def merchant_order_detail(order_id):
    if current_user.role != 'merchant':
        return redirect(url_for('login'))
    order = Order.query.get_or_404(order_id)
    images = OrderImage.query.filter_by(order_id=order.id).all()
    # 仅允许查看自己的订单
    if order.merchant_id != current_user.id:
        return redirect(url_for('merchant_dashboard'))
    return render_template('merchant/order.html', order=order, images=images)

@app.route('/download/original/<filename>')
@login_required
def download_original(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/download/final/<filename>')
@login_required
def download_final(filename):
    return send_from_directory(app.config['FINAL_FOLDER'], filename, as_attachment=True)

# 批量下载订单所有原图
@app.route('/download/original/batch/<int:order_id>')
@login_required
def download_original_batch(order_id):
    order = Order.query.get_or_404(order_id)
    # 收集所有相关图片文件名（封面 + 多图）
    filenames = []
    if order.original_image:
        filenames.append(order.original_image)
    for oi in OrderImage.query.filter_by(order_id=order.id).all():
        if oi.path:
            filenames.append(oi.path)
    # 去重保序
    seen = set()
    unique_files = []
    for f in filenames:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    # 打包ZIP到内存
    mem_file = BytesIO()
    with zipfile.ZipFile(mem_file, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in unique_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            if os.path.exists(file_path):
                # 直接使用文件名
                zf.write(file_path, arcname=fname)
    mem_file.seek(0)
    download_name = f"order_{order.order_number}_originals.zip"
    return send_file(mem_file, mimetype='application/zip', as_attachment=True, download_name=download_name)

# 页面内显示图片（非下载）
@app.route('/media/original/<filename>')
@login_required
def media_original(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

@app.route('/media/final/<filename>')
@login_required
def media_final(filename):
    return send_from_directory(app.config['FINAL_FOLDER'], filename, as_attachment=False)

@app.route('/admin/add_merchant', methods=['GET', 'POST'])
@login_required
def add_merchant():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        commission_rate = float(request.form['commission_rate'])
        contact_person = request.form.get('contact_person', '')
        contact_phone = request.form.get('contact_phone', '')
        wechat_id = request.form.get('wechat_id', '')
        
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
            wechat_id=wechat_id
        )
        
        db.session.add(new_merchant)
        db.session.commit()
        flash('商家已添加成功', 'success')
        return redirect(url_for('merchants_list'))
    
    return render_template('admin/add_merchant.html')

# 新增：商家列表页面
@app.route('/admin/merchants')
@login_required
def merchants_list():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
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

# 新增：商家详情页面
@app.route('/admin/merchant/<int:merchant_id>')
@login_required
def merchant_details(merchant_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    merchant = User.query.get_or_404(merchant_id)
    if merchant.role != 'merchant':
        return redirect(url_for('merchants_list'))
    orders = Order.query.filter_by(merchant_id=merchant.id).order_by(Order.created_at.desc()).all()
    total_commission = sum(order.commission for order in orders)
    return render_template('admin/merchant_details.html', merchant=merchant, orders=orders, total_commission=total_commission)

# 编辑商家
@app.route('/admin/merchant/<int:merchant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_merchant(merchant_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
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
            from datetime import datetime
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
        return redirect(url_for('merchant_details', merchant_id=merchant.id))
    return render_template('admin/merchant_edit.html', merchant=merchant)

# 删除商家
@app.route('/admin/merchant/<int:merchant_id>/delete', methods=['POST'])
@login_required
def delete_merchant(merchant_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    merchant = User.query.get_or_404(merchant_id)
    # 如果该商家名下有订单，不直接删除用户本身，可选择保留订单并置空 merchant_id
    for order in Order.query.filter_by(merchant_id=merchant.id).all():
        order.merchant_id = None
    db.session.delete(merchant)
    db.session.commit()
    flash('商家已删除', 'success')
    return redirect(url_for('merchants_list'))

# 新增：按需生成并返回商家二维码图片
@app.route('/admin/merchant/<int:merchant_id>/qrcode.png')
@login_required
def merchant_qrcode_image(merchant_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    merchant = User.query.get_or_404(merchant_id)
    if not merchant.qr_code:
        # 若还没有二维码标识，则生成并保存
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()

    url = f"{request.host_url}order?merchant={merchant.qr_code}"
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

# 新增：下载商家二维码
@app.route('/admin/merchant/<int:merchant_id>/qrcode/download')
@login_required
def merchant_qrcode_download(merchant_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    merchant = User.query.get_or_404(merchant_id)
    if not merchant.qr_code:
        qr_id, _ = generate_qr_code(merchant.id)
        merchant.qr_code = qr_id
        db.session.commit()

    url = f"{request.host_url}order?merchant={merchant.qr_code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    filename = f"merchant_{merchant.id}_qrcode.png"
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=filename)

# 初始化数据库（仅在应用启动时创建表结构）
with app.app_context():
    db.create_all()
    # 兼容旧数据库：如果缺少 price 字段，则在线迁移添加
    try:
        columns = db.session.execute("PRAGMA table_info('order')").fetchall()
        column_names = [c[1] for c in columns]
        if 'price' not in column_names:
            db.session.execute("ALTER TABLE 'order' ADD COLUMN price FLOAT DEFAULT 0")
            db.session.commit()
        if 'external_platform' not in column_names:
            db.session.execute("ALTER TABLE 'order' ADD COLUMN external_platform VARCHAR(50)")
            db.session.commit()
        if 'external_order_number' not in column_names:
            db.session.execute("ALTER TABLE 'order' ADD COLUMN external_order_number VARCHAR(100)")
            db.session.commit()
    except Exception:
        db.session.rollback()

# 添加清理过期图片的路由（管理员专用）
@app.route('/admin/cleanup')
@login_required
def admin_cleanup():
    if current_user.role != 'admin':
        flash('权限不足', 'error')
        return redirect(url_for('merchant_dashboard'))
    
    deleted_count = cleanup_expired_images()
    flash(f'清理完成，共删除 {deleted_count} 个过期文件夹', 'success')
    return redirect(url_for('admin_dashboard'))

# 抖音导入相关路由
@app.route('/admin/douyin_import')
@login_required
def douyin_import():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/douyin_import.html')

@app.route('/admin/douyin/auth')
@login_required
def douyin_auth():
    """抖音授权登录"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    # 这里需要配置抖音开放平台的参数
    # client_id = "your_douyin_app_id"
    # redirect_uri = "http://your-domain.com/admin/douyin/callback"
    # scope = "user_info,phone"
    # 
    # auth_url = f"https://open.douyin.com/platform/oauth/connect/?client_key={client_id}&response_type=code&scope={scope}&redirect_uri={redirect_uri}"
    # return redirect(auth_url)
    
    flash('抖音授权功能需要配置抖音开放平台参数', 'info')
    return redirect(url_for('douyin_import'))

@app.route('/admin/douyin/callback')
@login_required
def douyin_callback():
    """抖音授权回调"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    code = request.args.get('code')
    if not code:
        flash('授权失败，未获取到授权码', 'error')
        return redirect(url_for('douyin_import'))
    
    # 这里需要实现获取access_token和用户信息的逻辑
    # 1. 使用code获取access_token
    # 2. 使用access_token获取用户信息
    # 3. 创建或更新用户记录
    
    flash('抖音授权回调功能需要实现API调用逻辑', 'info')
    return redirect(url_for('douyin_import'))

@app.route('/admin/douyin_import', methods=['POST'])
@login_required
def douyin_import_batch():
    """批量导入用户"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    if 'csv_file' not in request.files:
        flash('请选择CSV文件', 'error')
        return redirect(url_for('douyin_import'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('请选择CSV文件', 'error')
        return redirect(url_for('douyin_import'))
    
    if not file.filename.endswith('.csv'):
        flash('请上传CSV格式的文件', 'error')
        return redirect(url_for('douyin_import'))
    
    try:
        # 读取CSV文件
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        default_commission = float(request.form.get('default_commission', 10))
        imported_count = 0
        error_count = 0
        
        for row_num, row in enumerate(csv_input, 1):
            if len(row) < 2:  # 至少需要用户名和手机号
                error_count += 1
                continue
                
            username = row[0].strip()
            phone = row[1].strip() if len(row) > 1 else ''
            contact_person = row[2].strip() if len(row) > 2 else ''
            wechat_id = row[3].strip() if len(row) > 3 else ''
            commission_rate = float(row[4]) if len(row) > 4 and row[4].strip() else default_commission
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                error_count += 1
                continue
            
            # 生成二维码
            qr_id, _ = generate_qr_code(None)
            
            # 创建新用户
            new_user = User(
                username=username,
                password=generate_password_hash('123456'),  # 默认密码
                role='merchant',
                commission_rate=commission_rate,
                qr_code=qr_id,
                contact_person=contact_person,
                contact_phone=phone,
                wechat_id=wechat_id,
                import_source='batch'
            )
            
            db.session.add(new_user)
            imported_count += 1
        
        db.session.commit()
        flash(f'批量导入完成！成功导入 {imported_count} 个用户，失败 {error_count} 个', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'导入过程中出现错误: {str(e)}', 'error')
    
    return redirect(url_for('douyin_import'))

# ==================== 小程序API接口 ====================

# 小程序API路由组
@app.route('/api/miniprogram', methods=['GET'])
def miniprogram_api_info():
    """小程序API信息"""
    return jsonify({
        'status': 'success',
        'message': '小程序API服务正常',
        'version': '1.0.0',
        'endpoints': {
            'submit_order': '/api/miniprogram/orders',
            'get_orders': '/api/miniprogram/orders',
            'upload_work': '/api/miniprogram/orders/<order_id>/upload',
            'get_works': '/api/miniprogram/works'
        }
    })

@app.route('/api/miniprogram/orders', methods=['POST'])
def miniprogram_submit_order():
    """小程序提交订单"""
    try:
        data = request.get_json()
        print(f"收到小程序订单数据: {data}")  # 调试日志
        
        # 验证必要字段
        required_fields = ['orderId', 'customerName', 'customerPhone', 'styleName', 'productName', 'quantity', 'totalPrice']
        for field in required_fields:
            if field not in data:
                print(f"缺少必要字段: {field}")
                return jsonify({'status': 'error', 'message': f'缺少必要字段: {field}'}), 400
        
        # 生成订单号（如果未提供）
        order_number = data.get('orderId') or f"MP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        
        # 创建订单记录
        new_order = Order(
            order_number=order_number,
            customer_name=data['customerName'],
            customer_phone=data['customerPhone'],
            size=data.get('productType', ''),
            price=float(data['totalPrice']),
            status='pending',
            external_platform='miniprogram',
            external_order_number=order_number,
            original_image=data.get('uploadedImages', [{}])[0].get('url', '') if data.get('uploadedImages') else '',
            shipping_info=json.dumps({
                'receiver': data.get('receiver', ''),
                'address': data.get('address', ''),
                'remark': data.get('remark', '')
            })
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        print(f"订单创建成功，ID: {new_order.id}, 订单号: {order_number}")
        
        # 保存订单图片
        if data.get('uploadedImages'):
            for img_data in data['uploadedImages']:
                if img_data.get('url'):
                    db.session.add(OrderImage(
                        order_id=new_order.id,
                        path=img_data['url']
                    ))
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '订单提交成功',
            'orderId': order_number,
            'orderId_db': new_order.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"订单提交失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'订单提交失败: {str(e)}'}), 500

@app.route('/api/miniprogram/orders', methods=['GET'])
def miniprogram_get_orders():
    """小程序获取订单列表"""
    try:
        phone = request.args.get('phone')
        print(f"查询订单，手机号: {phone}")
        
        if not phone:
            return jsonify({'status': 'error', 'message': '缺少手机号参数'}), 400
        
        # 根据手机号查询订单
        orders = Order.query.filter(
            Order.customer_phone.like(f'%{phone}%'),
            Order.external_platform == 'miniprogram'
        ).order_by(Order.created_at.desc()).all()
        
        print(f"找到 {len(orders)} 个订单")
        
        order_list = []
        for order in orders:
            # 获取订单图片
            images = OrderImage.query.filter_by(order_id=order.id).all()
            
            order_list.append({
                'orderId': order.order_number,
                'orderId_db': order.id,
                'customerName': order.customer_name,
                'customerPhone': order.customer_phone,
                'styleName': order.external_platform,  # 可以扩展字段存储风格信息
                'productName': order.size,
                'quantity': 1,  # 默认数量
                'totalPrice': float(order.price or 0),
                'status': order.status,
                'statusText': {
                    'pending': '待制作',
                    'processing': '制作中', 
                    'completed': '已完成',
                    'shipped': '已发货'
                }.get(order.status, '未知'),
                'createTime': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'completeTime': order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else None,
                'images': [{'url': f'/media/original/{img.path}'} for img in images],
                'finalImage': f'/media/final/{order.final_image}' if order.final_image else None
            })
        
        return jsonify({
            'status': 'success',
            'orders': order_list
        })
        
    except Exception as e:
        print(f"获取订单失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取订单失败: {str(e)}'}), 500

@app.route('/api/miniprogram/works', methods=['GET'])
def miniprogram_get_works():
    """小程序获取用户作品"""
    try:
        phone = request.args.get('phone')
        print(f"查询作品，手机号: {phone}")
        
        if not phone:
            return jsonify({'status': 'error', 'message': '缺少手机号参数'}), 400
        
        # 查询已完成的订单
        orders = Order.query.filter(
            Order.customer_phone.like(f'%{phone}%'),
            Order.external_platform == 'miniprogram',
            Order.status == 'completed',
            Order.final_image.isnot(None)
        ).order_by(Order.completed_at.desc()).all()
        
        print(f"找到 {len(orders)} 个作品")
        
        works = []
        for order in orders:
            works.append({
                'id': order.id,
                'orderId': order.order_number,
                'styleName': order.external_platform,  # 可以扩展字段
                'productName': order.size,
                'finalImage': f'/media/final/{order.final_image}',
                'completeTime': order.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'createTime': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'status': 'success',
            'works': works
        })
        
    except Exception as e:
        print(f"获取作品失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取作品失败: {str(e)}'}), 500

# 跨域支持
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    with app.app_context():
        # 启动时执行一次清理
        cleanup_expired_images()
    app.run(host='0.0.0.0', port=6000, debug=False)
