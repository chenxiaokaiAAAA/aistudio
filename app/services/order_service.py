# -*- coding: utf-8 -*-
"""
订单业务逻辑服务
从 test_server.py 迁移订单相关业务逻辑
"""
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# 延迟获取数据库模型和db实例
def get_db_models():
    """延迟获取数据库模型（避免循环导入）"""
    try:
        from app.models import (
            Order, OrderImage, FranchiseeAccount, SelfieMachine,
            PromotionUser, Commission
        )
        return {
            'Order': Order,
            'OrderImage': OrderImage,
            'FranchiseeAccount': FranchiseeAccount,
            'SelfieMachine': SelfieMachine,
            'PromotionUser': PromotionUser,
            'Commission': Commission
        }
    except ImportError:
        return None

def get_db():
    """延迟获取db实例"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                return test_server_module.db
    except (ImportError, AttributeError):
        pass
    return None

def get_app():
    """延迟获取Flask app实例"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'app'):
                return test_server_module.app
    except (ImportError, AttributeError):
        pass
    return None

def get_server_config():
    """获取服务器配置函数"""
    try:
        from server_config import get_base_url, get_media_url
        return {
            'get_base_url': get_base_url,
            'get_media_url': get_media_url
        }
    except ImportError:
        def get_base_url():
            return 'http://192.168.2.54:8000'
        def get_media_url():
            return 'http://192.168.2.54:8000/media'
        return {
            'get_base_url': get_base_url,
            'get_media_url': get_media_url
        }

def create_miniprogram_order(order_data):
    """
    创建小程序订单
    
    Args:
        order_data: 订单数据字典，包含：
            - orderId: 订单号（可选，不提供则自动生成）
            - customerName: 客户姓名
            - customerPhone: 客户电话
            - styleName: 风格名称
            - productName: 产品名称
            - quantity: 数量
            - totalPrice: 总价
            - selectedSpec: 选择的规格
            - openid: 用户openid
            - referrerUserId: 推广者用户ID（可选）
            - referrerPromotionCode: 推广码（可选）
            - franchiseeQrCode: 加盟商二维码（可选）
            - uploadedImages: 上传的图片列表（可选）
            - receiver, phone, fullAddress, remark: 收货信息（可选）
    
    Returns:
        tuple: (success: bool, result: dict, error_message: str)
    """
    models = get_db_models()
    db = get_db()
    app = get_app()
    
    if not models or not db:
        return False, None, "数据库模型或db实例未初始化"
    
    Order = models['Order']
    OrderImage = models['OrderImage']
    FranchiseeAccount = models['FranchiseeAccount']
    PromotionUser = models['PromotionUser']
    Commission = models['Commission']
    
    # 导入工具函数
    from app.utils.helpers import (
        validate_promotion_code, check_user_has_placed_order,
        check_user_eligible_for_commission, generate_stable_promotion_code,
        parse_shipping_info as _parse_shipping_info
    )
    
    try:
        # 验证必要字段
        required_fields = ['customerName', 'customerPhone', 'styleName', 'productName', 'quantity', 'totalPrice']
        for field in required_fields:
            if field not in order_data:
                return False, None, f'缺少必要字段: {field}'
        
        # 生成订单号（如果未提供）
        order_number = order_data.get('orderId') or f"MP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        
        # 处理推广信息
        referrer_user_id = order_data.get('referrerUserId')
        referrer_promotion_code = order_data.get('referrerPromotionCode')
        
        if not referrer_user_id or not referrer_promotion_code:
            referrer_user_id = None
            referrer_promotion_code = None
        
        # 处理加盟商额度扣除
        franchisee_id = None
        franchisee_deduction = 0.0
        franchisee_qr_code = order_data.get('franchiseeQrCode', '')
        franchisee = None
        
        # 门店和自拍机信息
        store_name = None
        selfie_machine_name = None
        selfie_machine_id = None
        
        if franchisee_qr_code:
            franchisee = FranchiseeAccount.query.filter_by(qr_code=franchisee_qr_code, status='active').first()
            if franchisee:
                order_amount = float(order_data['totalPrice'])
                
                if franchisee.remaining_quota >= order_amount:
                    franchisee.used_quota += order_amount
                    franchisee.remaining_quota -= order_amount
                    franchisee_id = franchisee.id
                    franchisee_deduction = order_amount
                    
                    store_name = franchisee.store_name
                    selfie_machine_name = franchisee.machine_name
                    selfie_machine_id = franchisee.machine_serial_number
                else:
                    return False, None, f'加盟商额度不足，当前剩余额度: {franchisee.remaining_quota} 元'
            else:
                return False, None, '加盟商账户不存在或已禁用'
        
        # 创建订单记录
        new_order = Order(
            order_number=order_number,
            customer_name=order_data['customerName'],
            customer_phone=order_data['customerPhone'],
            size=order_data.get('selectedSpec', ''),
            style_name=order_data.get('styleName', ''),
            product_name=order_data.get('productName', ''),
            price=float(order_data['totalPrice']),
            status='paid',  # 小程序下单默认为已支付（因为已经扣费）
            external_platform=selfie_machine_name or 'miniprogram',
            external_order_number=selfie_machine_id or order_number,
            source_type='miniprogram',
            original_image='',
            shipping_info=json.dumps({
                'receiver': order_data.get('receiver', ''),
                'phone': order_data.get('phone', ''),
                'fullAddress': order_data.get('fullAddress', ''),
                'remark': order_data.get('remark', '')
            }),
            promotion_code=referrer_promotion_code or '',
            referrer_user_id=referrer_user_id or '',
            franchisee_id=franchisee_id,
            franchisee_deduction=franchisee_deduction,
            store_name=store_name,
            selfie_machine_id=selfie_machine_id,
            openid=order_data.get('openid', '')
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # 更新用户推广资格
        if new_order.openid:
            try:
                promotion_user = PromotionUser.query.filter_by(open_id=new_order.openid).first()
                if promotion_user:
                    has_order = check_user_has_placed_order(promotion_user.user_id)
                    
                    if not promotion_user.eligible_for_promotion and has_order:
                        promotion_user.eligible_for_promotion = True
                        
                        if promotion_user.promotion_code and promotion_user.promotion_code.startswith('TEMP_'):
                            promotion_code = generate_stable_promotion_code(new_order.openid)
                            
                            original_code = promotion_code
                            counter = 1
                            while PromotionUser.query.filter_by(promotion_code=promotion_code).first():
                                promotion_code = original_code + str(counter)
                                counter += 1
                            
                            promotion_user.promotion_code = promotion_code
                    
                    db.session.commit()
            except Exception as e:
                print(f"更新用户推广资格失败: {e}")
        
        # 处理推广码分佣
        if referrer_user_id and referrer_promotion_code:
            try:
                order_price = float(order_data['totalPrice'])
                
                if validate_promotion_code(referrer_promotion_code) == referrer_user_id:
                    referrer_eligible = check_user_eligible_for_commission(referrer_user_id)
                    
                    if referrer_eligible:
                        commission_rate = 0.2
                        commission_amount = order_price * commission_rate
                        
                        commission = Commission(
                            order_id=order_number,
                            referrer_user_id=referrer_user_id,
                            amount=commission_amount,
                            rate=commission_rate,
                            status='pending'
                        )
                        
                        db.session.add(commission)
                        
                        promotion_user = PromotionUser.query.filter_by(user_id=referrer_user_id).first()
                        if promotion_user:
                            promotion_user.total_orders += 1
                        
                        db.session.commit()
            except Exception as e:
                print(f"处理推广分佣失败: {e}")
                db.session.rollback()
                db.session.commit()
        
        # 保存订单图片
        if order_data.get('uploadedImages'):
            for img_data in order_data['uploadedImages']:
                if img_data.get('filename'):
                    db.session.add(OrderImage(
                        order_id=new_order.id,
                        path=img_data['filename'],
                        is_main=False
                    ))
                elif img_data.get('url'):
                    img_url = img_data['url']
                    img_filename = f"mp_{uuid.uuid4().hex[:8]}.jpg"
                    
                    if app:
                        img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
                        
                        if img_url.startswith('http://tmp/') or img_url.startswith('tmp/'):
                            from PIL import Image
                            placeholder_img = Image.new('RGB', (300, 300), color='lightgray')
                            placeholder_img.save(img_path, 'JPEG')
                            
                            db.session.add(OrderImage(
                                order_id=new_order.id,
                                path=img_filename,
                                is_main=False
                            ))
                        elif img_url.startswith('http'):
                            from PIL import Image
                            placeholder_img = Image.new('RGB', (300, 300), color='lightblue')
                            placeholder_img.save(img_path, 'JPEG')
                            
                            db.session.add(OrderImage(
                                order_id=new_order.id,
                                path=img_filename,
                                is_main=False
                            ))
                        else:
                            db.session.add(OrderImage(
                                order_id=new_order.id,
                                path=img_url,
                                is_main=False
                            ))
        
        db.session.commit()
        
        # 处理分享奖励（在订单创建成功后）
        try:
            shared_user_id = order_data.get('userId') or order_data.get('user_id')
            share_record_id = order_data.get('share_record_id')
            work_id = order_data.get('work_id')
            
            if shared_user_id and (share_record_id or work_id):
                # 直接调用内部函数
                from app.routes.miniprogram.share_reward import process_share_reward_impl
                
                reward_data = {
                    'shared_user_id': shared_user_id,
                    'order_id': new_order.id,
                    'share_record_id': share_record_id,
                    'work_id': work_id
                }
                
                result = process_share_reward_impl(reward_data)
                if result.get('status') == 'success':
                    print(f"✅ 分享奖励已发放: {result.get('message')}")
        except Exception as e:
            print(f"⚠️ 分享奖励处理异常: {e}")
        
        return True, {
            'orderId': order_number,
            'orderId_db': new_order.id
        }, None
        
    except Exception as e:
        if db:
            db.session.rollback()
        print(f"创建订单失败: {str(e)}")
        return False, None, f'订单提交失败: {str(e)}'

def get_order_by_number(order_number):
    """
    通过订单号获取订单详情
    
    Args:
        order_number: 订单号
    
    Returns:
        tuple: (success: bool, order_data: dict, error_message: str)
    """
    models = get_db_models()
    if not models:
        return False, None, "数据库模型未初始化"
    
    Order = models['Order']
    OrderImage = models['OrderImage']
    
    config = get_server_config()
    get_base_url = config['get_base_url']
    get_media_url = config['get_media_url']
    
    from app.utils.helpers import parse_shipping_info as _parse_shipping_info
    from urllib.parse import quote
    
    try:
        order = Order.query.filter_by(order_number=order_number).first()
        
        if not order:
            return False, None, '订单不存在'
        
        # 获取订单图片
        images = OrderImage.query.filter_by(order_id=order.id).all()
        image_urls = [f"{get_media_url()}/original/{img.path}" for img in images]
        
        # 构建精修图URL
        final_image_url = None
        final_image_no_watermark_url = None
        if order.final_image:
            final_image_url = f"{get_media_url()}/final/{order.final_image}"
            if order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                final_image_no_watermark_url = f"{get_media_url()}/final/clean_{order.final_image}"
        
        # 构建效果图URL
        hd_image_url = None
        hd_image_no_watermark_url = None
        if order.hd_image:
            encoded_filename = quote(order.hd_image, safe='')
            hd_image_url = f"{get_base_url()}/public/hd/{encoded_filename}"
            if order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                clean_filename = f"clean_{order.hd_image}"
                encoded_clean_filename = quote(clean_filename, safe='')
                hd_image_no_watermark_url = f"{get_base_url()}/public/hd/{encoded_clean_filename}"
        
        # 状态映射
        status_map = {
            'unpaid': '待上传图片',
            'pending': '待制作',
            'completed': '已完成',
            'shipped': '已发货',
            'hd_ready': '高清放大',
            'manufacturing': '制作中',
            'processing': '处理中',
            'paid': '已支付',
            'selection_completed': '选片已完成'
        }
        
        order_data = {
            'orderId': order.order_number,
            'orderId_db': order.id,
            'customerName': order.customer_name,
            'customerPhone': order.customer_phone,
            'styleName': order.style_name or '威廉国王',
            'productName': order.product_name or '艺术钥匙扣',
            'productType': order.size,
            'quantity': 1,
            'totalPrice': order.price,
            'status': order.status,
            'statusText': status_map.get(order.status, order.status),
            'createTime': order.created_at.isoformat(),
            'completeTime': order.completed_at.isoformat() if order.completed_at else None,
            'images': image_urls,
            'originalImages': image_urls,
            'finalImage': final_image_url,
            'finalImageNoWatermark': final_image_no_watermark_url,
            'hdImage': hd_image_url,
            'hdImageNoWatermark': hd_image_no_watermark_url,
            'shippingInfo': _parse_shipping_info(order.shipping_info)
        }
        
        return True, order_data, None
        
    except Exception as e:
        print(f"查询订单失败: {str(e)}")
        return False, None, f'查询订单失败: {str(e)}'

def check_order_for_verification(order_id, machine_serial_number=None):
    """
    检查订单是否可以核销（用于安卓APP扫码核销）
    
    Args:
        order_id: 订单号
        machine_serial_number: 自拍机序列号（可选）
    
    Returns:
        tuple: (success: bool, order_data: dict, error_message: str)
    """
    models = get_db_models()
    db = get_db()
    if not models or not db:
        return False, None, "数据库模型或db实例未初始化"
    
    Order = models['Order']
    OrderImage = models['OrderImage']
    SelfieMachine = models['SelfieMachine']
    
    config = get_server_config()
    get_media_url = config['get_media_url']
    
    try:
        order = Order.query.filter_by(order_number=order_id).first()
        
        if not order:
            return False, None, '订单不存在'
        
        # 如果订单还没有关联加盟商，且提供了自拍机序列号，尝试通过序列号关联加盟商
        if not order.franchisee_id and machine_serial_number:
            try:
                machine = SelfieMachine.query.filter_by(
                    machine_serial_number=machine_serial_number,
                    status='active'
                ).first()
                
                if machine and machine.franchisee:
                    franchisee = machine.franchisee
                    order.franchisee_id = franchisee.id
                    order.store_name = franchisee.store_name or order.store_name
                    order.selfie_machine_id = machine_serial_number
                    order.external_platform = machine.machine_name or order.external_platform or 'miniprogram'
                    order.external_order_number = machine_serial_number
                    
                    db.session.commit()
            except Exception as e:
                print(f"通过自拍机序列号关联加盟商失败: {e}")
        
        # 检查订单是否已支付
        is_paid = False
        if order.payment_time or order.transaction_id:
            is_paid = True
        elif order.status in ['paid', 'pending', 'manufacturing', 'completed', 'shipped', 'delivered']:
            is_paid = True
        
        # 检查订单是否已经拍摄过
        images = OrderImage.query.filter_by(order_id=order.id).all()
        image_urls = [f"{get_media_url()}/original/{img.path}" for img in images]
        has_photos = len(images) > 0
        
        if has_photos:
            return False, {
                'order_id': order.order_number,
                'order_number': order.order_number,
                'status': order.status,
                'is_paid': is_paid,
                'has_photos': True,
                'photos': image_urls
            }, '该订单已经拍摄过，不能重复拍摄'
        
        return True, {
            'order_id': order.order_number,
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'product_name': order.product_name or '证件照',
            'product_type': order.product_type or 'idphoto',
            'status': order.status,
            'is_paid': is_paid,
            'has_photos': has_photos,
            'amount': float(order.price) if order.price else 0.0,
            'photos': image_urls,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'payment_time': order.payment_time.isoformat() if order.payment_time else None
        }, None
        
    except Exception as e:
        print(f"检查订单状态失败: {str(e)}")
        return False, None, f'检查订单失败: {str(e)}'

def upload_order_photos(order_id, photos_data, machine_serial_number=None):
    """
    上传订单照片（用于安卓APP拍摄后回传）
    
    Args:
        order_id: 订单号
        photos_data: 照片数据列表（包含文件对象）
        machine_serial_number: 自拍机序列号（可选）
    
    Returns:
        tuple: (success: bool, result: dict, error_message: str)
    """
    models = get_db_models()
    db = get_db()
    app = get_app()
    
    if not models or not db or not app:
        return False, None, "数据库模型、db实例或app实例未初始化"
    
    Order = models['Order']
    OrderImage = models['OrderImage']
    SelfieMachine = models['SelfieMachine']
    
    try:
        order = Order.query.filter_by(order_number=order_id).first()
        
        if not order:
            return False, None, '订单不存在'
        
        # 如果订单还没有关联加盟商，且提供了自拍机序列号，尝试通过序列号关联加盟商
        if not order.franchisee_id and machine_serial_number:
            try:
                machine = SelfieMachine.query.filter_by(
                    machine_serial_number=machine_serial_number,
                    status='active'
                ).first()
                
                if machine and machine.franchisee:
                    franchisee = machine.franchisee
                    order.franchisee_id = franchisee.id
                    order.store_name = franchisee.store_name or order.store_name
                    order.selfie_machine_id = machine_serial_number
                    order.external_platform = machine.machine_name or order.external_platform or 'miniprogram'
                    order.external_order_number = machine_serial_number
            except Exception as e:
                print(f"通过自拍机序列号关联加盟商失败: {e}")
        
        # 保存上传的照片
        uploaded_files = []
        for photo_data in photos_data:
            if 'file' in photo_data and photo_data['file']:
                file = photo_data['file']
                if file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    file.save(file_path)
                    
                    # 创建订单图片记录
                    order_image = OrderImage(
                        order_id=order.id,
                        path=unique_filename,
                        image_type='original',
                        is_main=False
                    )
                    db.session.add(order_image)
                    uploaded_files.append(unique_filename)
        
        # 更新订单状态：如果订单状态是unpaid或paid，更新为processing（处理中）
        if order.status in ['unpaid', 'paid']:
            order.status = 'processing'
        
        db.session.commit()
        
        return True, {
            'orderId': order.order_number,
            'uploadedFiles': uploaded_files,
            'status': order.status
        }, None
        
    except Exception as e:
        if db:
            db.session.rollback()
        print(f"上传订单照片失败: {str(e)}")
        return False, None, f'上传照片失败: {str(e)}'

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
