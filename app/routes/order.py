# -*- coding: utf-8 -*-
"""
订单相关路由
从 test_server.py 迁移订单相关路由
"""
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

order_bp = Blueprint('order', __name__)

# ============================================================================
# 订单创建和状态查询路由（网页版）
# ============================================================================

@order_bp.route('/order', methods=['GET', 'POST'])
def create_order():
    """创建订单页面和创建订单（网页版）"""
    # 从test_server模块获取必要的对象
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        User = test_server_module.User
        ProductSize = test_server_module.ProductSize
        Product = test_server_module.Product
        Order = test_server_module.Order
        OrderImage = test_server_module.OrderImage
        db = test_server_module.db
        app = test_server_module.app
    else:
        from app.models import User, ProductSize, Product, Order, OrderImage
        from app import db, current_app as app
    
    merchant_id = request.args.get('merchant')
    merchant = None
    franchisee = None  # 初始化franchisee变量
    
    if merchant_id:
        merchant = User.query.filter_by(qr_code=merchant_id).first()
    
    # 读取产品尺寸配置供模板渲染
    product_sizes = ProductSize.query.join(Product).order_by(ProductSize.price.asc()).all()

    if request.method == 'POST':
        try:
            customer_name = request.form['name']
            customer_phone = request.form['phone']
            # 尺寸可暂时不用，通过渠道/外部订单号下单
            size = request.form.get('size') or ''
            external_platform = request.form.get('external_platform')
            external_order_number = request.form.get('external_order_number')
            
            # 加盟商产品选择
            product_type = request.form.get('product')
            franchisee_deduction = 0.0
            
            # 收货地址信息
            full_address = request.form.get('fullAddress', '')
            
            # 构建地址信息
            shipping_info = json.dumps({
                'receiver': customer_name,
                'phone': customer_phone,
                'fullAddress': full_address,
                'remark': ''
            })
            
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
                price = 50.0  # 默认价格
                product_name = None
                
                # 处理加盟商产品选择
                if franchisee and product_type:
                    product_prices = {
                        'standard': 299.0,
                        'premium': 399.0,
                        'luxury': 599.0
                    }
                    product_names = {
                        'standard': '标准版',
                        'premium': '高级版',
                        'luxury': '豪华版'
                    }
                    
                    if product_type in product_prices:
                        price = product_prices[product_type]
                        product_name = product_names[product_type]
                        
                        # 检查加盟商额度
                        if franchisee.remaining_quota >= price:
                            franchisee.used_quota += price
                            franchisee.remaining_quota -= price
                            franchisee_deduction = price
                            print(f"加盟商额度扣除成功: {franchisee.company_name}, 扣除金额: {price}, 剩余额度: {franchisee.remaining_quota}")
                        else:
                            flash(f'加盟商额度不足，当前剩余额度: {franchisee.remaining_quota} 元', 'error')
                            return render_template('order.html', merchant=merchant, franchisee=franchisee, size_options=product_sizes)
                
                if size and not product_type:
                    # 首先尝试通过SIZE_MAPPING查找
                    try:
                        from printer_config import SIZE_MAPPING
                        if size in SIZE_MAPPING:
                            mapping = SIZE_MAPPING[size]
                            product_name = mapping['product_name']
                            # 通过尺寸名称查找对应的尺寸配置
                            size_config = ProductSize.query.filter_by(size_name=product_name).first()
                            if size_config:
                                price = size_config.price
                    except Exception:
                        pass
                    
                    # 如果没找到，尝试直接通过尺寸名称查找
                    if price == 50.0:
                        size_config = ProductSize.query.filter_by(size_name=size).first()
                        if size_config:
                            price = size_config.price
                            product_name = size_config.size_name

                new_order = Order(
                    order_number=order_number,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    size=size,
                    product_name=product_name,  # 设置产品名称
                    price=price,
                    external_platform=external_platform,
                    external_order_number=external_order_number,
                    source_type='website',  # 明确标识为网页来源
                    original_image=saved_filenames[0] if saved_filenames else '',
                    shipping_info=shipping_info,  # 保存收货地址
                    merchant=merchant,
                    franchisee_id=franchisee.id if franchisee else None,
                    franchisee_deduction=franchisee_deduction
                )
                
                db.session.add(new_order)
                db.session.flush()  # 先刷新获取ID，但不提交事务
                
                print(f"✅ 订单创建成功，ID: {new_order.id}, 订单号: {order_number}")

                # 保存多图到关联表，第一张设为主图
                for i, fname in enumerate(saved_filenames):
                    db.session.add(OrderImage(
                        order_id=new_order.id, 
                        path=fname,
                        is_main=(i == 0)  # 第一张图片设为主图
                    ))
                
                # 提交所有更改
                db.session.commit()
                print(f"✅ 订单数据已持久化到数据库，订单号: {order_number}")
                
                return render_template('order_success.html', order_number=order_number)
            else:
                flash('请上传图片', 'error')
                return render_template('order.html', merchant=merchant, size_options=product_sizes)
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ 订单创建失败: {str(e)}")
            flash(f'订单创建失败: {str(e)}', 'error')
            return render_template('order.html', merchant=merchant, franchisee=franchisee, size_options=product_sizes)
    
    return render_template('order.html', merchant=merchant, franchisee=franchisee, size_options=product_sizes)

@order_bp.route('/order/status', methods=['GET', 'POST'])
def order_status():
    """订单状态查询（用户无需登录）：通过订单号 + 手机号后4位验证"""
    # 从test_server模块获取必要的对象
    import sys
    if 'test_server' in sys.modules:
        test_server_module = sys.modules['test_server']
        Order = test_server_module.Order
        OrderImage = test_server_module.OrderImage
    else:
        from app.models import Order, OrderImage
    
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

# ============================================================================
# 订单API路由
# ============================================================================

@order_bp.route('/api/order/<int:order_id>/logistics', methods=['GET'])
def get_order_logistics(order_id):
    """获取订单物流信息"""
    try:
        # 从test_server模块获取必要的对象
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            Order = test_server_module.Order
        else:
            from app.models import Order
        
        order = Order.query.get_or_404(order_id)
        
        logistics_info = None
        if order.logistics_info:
            try:
                logistics_info = json.loads(order.logistics_info)
            except:
                logistics_info = None
        elif order.shipping_info and order.shipping_info.startswith('{'):
            # 兼容旧格式：shipping_info字段中的JSON数据
            try:
                logistics_info = json.loads(order.shipping_info)
            except:
                logistics_info = None
        
        return jsonify({
            'success': True,
            'order_number': order.order_number,
            'status': order.status,
            'logistics': logistics_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@order_bp.route('/api/order/complete-free', methods=['POST'])
def complete_free_order():
    """完成0元订单支付（使用优惠券）"""
    try:
        # 从test_server模块获取必要的对象
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            Order = test_server_module.Order
            UserCoupon = test_server_module.UserCoupon
            Coupon = test_server_module.Coupon
            db = test_server_module.db
        else:
            from app.models import Order, UserCoupon, Coupon
            from app import db
        
        data = request.get_json()
        order_id = data.get('orderId')
        coupon_code = data.get('couponCode')
        user_id = data.get('userId')
        
        if not all([order_id, coupon_code, user_id]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数：orderId、couponCode、userId'
            }), 400
        
        # 查找订单
        order = Order.query.filter_by(order_number=order_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
        
        # 检查订单状态
        if order.status != 'unpaid':
            return jsonify({
                'success': False,
                'message': f'订单状态不正确，当前状态：{order.status}'
            }), 400
        
        # 查找用户优惠券
        user_coupon = UserCoupon.query.filter_by(
            user_id=user_id,
            coupon_code=coupon_code,
            status='unused'
        ).first()
        
        if not user_coupon:
            return jsonify({
                'success': False,
                'message': '优惠券不存在或已使用'
            }), 400
        
        # 检查优惠券是否有效
        coupon = user_coupon.coupon
        now = datetime.now()
        
        if coupon.status != 'active':
            return jsonify({
                'success': False,
                'message': '优惠券已失效'
            }), 400
        
        # 检查优惠券是否在有效期内
        if now < coupon.start_time or now > coupon.end_time:
            return jsonify({
                'success': False,
                'message': '优惠券不在有效期内'
            }), 400
        
        # 检查用户优惠券是否过期
        if hasattr(user_coupon, 'expire_time') and user_coupon.expire_time and now > user_coupon.expire_time:
            return jsonify({
                'success': False,
                'message': '优惠券已过期'
            }), 400
        
        # 检查订单金额是否满足优惠券使用条件
        if float(order.price) < coupon.min_amount:
            return jsonify({
                'success': False,
                'message': f'订单金额需满{coupon.min_amount}元才能使用此优惠券'
            }), 400
        
        # 开始事务处理
        # 1. 更新订单状态：unpaid → paid
        order.status = 'paid'
        order.payment_time = datetime.now()
        import time
        order.transaction_id = f"FREE_{order_id}_{int(time.time())}"  # 生成免费订单交易号
        
        # 2. 标记优惠券已使用：unused → used
        user_coupon.status = 'used'
        user_coupon.order_id = order.id
        if hasattr(user_coupon, 'use_time'):
            user_coupon.use_time = datetime.now()
        elif hasattr(user_coupon, 'used_at'):
            user_coupon.used_at = datetime.now()
        
        # 3. 更新优惠券使用计数
        if hasattr(coupon, 'used_count'):
            coupon.used_count += 1
        
        # 提交事务
        db.session.commit()
        
        print(f"✅ 0元订单完成支付成功: 订单={order_id}, 优惠券={coupon_code}, 用户={user_id}")
        
        return jsonify({
            'success': True,
            'message': '订单支付完成',
            'data': {
                'orderId': order_id,
                'status': 'paid',
                'paymentTime': order.payment_time.isoformat(),
                'transactionId': order.transaction_id,
                'couponCode': coupon_code
            }
        })
        
    except Exception as e:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                test_server_module.db.session.rollback()
        print(f"完成0元订单支付失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'支付失败: {str(e)}'
        }), 500
