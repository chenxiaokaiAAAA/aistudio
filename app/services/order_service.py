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
        # 检查是否为追加产品到现有订单
        add_to_existing_order = order_data.get('addToExistingOrder', False)
        existing_order_number = order_data.get('existingOrderNumber', '')
        
        # 如果追加产品，验证原订单是否存在且状态正确
        if add_to_existing_order and existing_order_number:
            existing_order = Order.query.filter_by(order_number=existing_order_number).first()
            if not existing_order:
                return False, None, f'原订单不存在: {existing_order_number}'
            
            # 检查订单状态：必须是已支付且未拍摄（状态为paid）
            # 如果状态是shooting或更后面的状态，说明已经拍摄了，不能追加
            if existing_order.status not in ['paid', '已支付']:
                return False, None, '订单已拍摄或已上传图片，无法追加产品。请重新下单'
            
            # 检查是否已上传图片：如果已上传图片，不能追加产品
            existing_images = OrderImage.query.filter_by(order_id=existing_order.id).all()
            if existing_images:
                return False, None, '订单已上传图片，无法追加产品。请重新下单'
            
            # 保存原订单的订单类型，用于后续处理
            original_order_mode = existing_order.order_mode
        
        # 检查是否为多个商品订单
        is_multiple_items = order_data.get('isMultipleItems', False)
        items = order_data.get('items', [])
        
        print(f"🔍 订单创建模式检查:")
        print(f"   add_to_existing_order: {add_to_existing_order}")
        print(f"   existing_order_number: {existing_order_number}")
        print(f"   is_multiple_items: {is_multiple_items}")
        print(f"   items数量: {len(items) if items else 0}")
        
        # 如果是追加产品模式，即使只有一个商品，也使用多个商品模式处理（确保使用原订单号）
        if add_to_existing_order and existing_order_number:
            print(f"✅ 进入追加产品模式")
            # 追加产品模式：使用多个商品模式处理
            order_data['orderId'] = existing_order_number
            # 如果没有 items，创建一个
            if not items or len(items) == 0:
                items = [{
                    'productName': order_data.get('productName', ''),
                    'styleName': order_data.get('styleName', ''),
                    'selectedSpec': order_data.get('selectedSpec', ''),
                    'price': float(order_data.get('totalPrice', 0)),
                    'productType': order_data.get('selectedSpec', '')
                }]
                order_data['items'] = items
            # 追加产品模式，直接使用多个商品模式
            return create_multiple_items_order(order_data, items, models, db, app)
        elif is_multiple_items and items and len(items) > 0:
            print(f"✅ 进入多个商品模式（正常下单）")
            # 多个商品模式：为每个商品创建订单，使用相同的订单号
            return create_multiple_items_order(order_data, items, models, db, app)
        else:
            print(f"✅ 进入单个商品模式（正常下单）")
        
        # 单个商品模式（原有逻辑）
        # 验证必要字段
        required_fields = ['customerName', 'customerPhone', 'styleName', 'productName', 'quantity', 'totalPrice']
        for field in required_fields:
            if field not in order_data:
                return False, None, f'缺少必要字段: {field}'
        
        # 打印调试信息
        print(f"🔍 create_miniprogram_order 单个商品模式订单号生成检查:")
        print(f"   add_to_existing_order: {add_to_existing_order}")
        print(f"   existing_order_number: {existing_order_number}")
        print(f"   order_data.get('orderId'): {order_data.get('orderId', 'None')}")
        
        # 生成订单号（默认MP开头，常规线下订单）
        # 如果用户选择"立即制作"，会在后续流程中改为XSDD-开头
        # 如果是追加产品，使用原订单号
        # 注意：正常下单时，无论前端传入什么订单号（包括PET开头的临时订单号），都应该生成新的订单号
        if add_to_existing_order and existing_order_number:
            order_number = existing_order_number
            print(f"✅ 追加产品模式：使用原订单号 {order_number}")
        else:
            # 正常下单模式：始终生成新的订单号，忽略前端传入的临时订单号
            # 前端可能传入PET开头的临时订单号或"待生成"，这些都应该被忽略
            order_number = f"MP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            print(f"✅ 新建订单模式：生成新订单号 {order_number}（忽略前端传入的临时订单号）")
        
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
                # 通过门店二维码下单：只关联门店，不扣除额度（因为用户已经支付了）
                franchisee_id = franchisee.id
                franchisee_deduction = 0.0  # 不扣除额度，因为用户已支付
                
                store_name = franchisee.store_name
                selfie_machine_name = franchisee.machine_name
                selfie_machine_id = franchisee.machine_serial_number
                
                print(f"✅ 通过门店二维码下单，关联门店: {franchisee.company_name} (ID: {franchisee_id})")
            else:
                print(f"⚠️ 门店二维码无效或门店已禁用: {franchisee_qr_code}")
                # 不返回错误，允许订单继续创建（向后兼容）
        
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

def create_multiple_items_order(order_data, items, models, db, app):
    """
    创建包含多个商品的订单（每个商品使用相同的订单号，但创建独立的Order记录）
    
    Args:
        order_data: 订单基础数据
        items: 商品列表
        models: 数据库模型字典
        db: 数据库实例
        app: Flask应用实例
    
    Returns:
        tuple: (success: bool, result: dict, error_message: str)
    """
    Order = models['Order']
    OrderImage = models['OrderImage']
    FranchiseeAccount = models['FranchiseeAccount']
    PromotionUser = models['PromotionUser']
    Commission = models['Commission']
    
    # 检查是否为追加产品模式
    add_to_existing_order = order_data.get('addToExistingOrder', False)
    existing_order_number = order_data.get('existingOrderNumber', '')
    existing_order = None
    
    print(f"🔍 追加产品模式检查: add_to_existing_order={add_to_existing_order}, existing_order_number={existing_order_number}")
    
    if add_to_existing_order and existing_order_number:
        existing_order = Order.query.filter_by(order_number=existing_order_number).first()
        if not existing_order:
            print(f"❌ 原订单不存在: {existing_order_number}")
            return False, None, f'原订单不存在: {existing_order_number}'
        
        print(f"✅ 找到原订单: ID={existing_order.id}, 订单号={existing_order.order_number}, 状态={existing_order.status}, 订单类型={existing_order.order_mode}")
        
        # 检查订单状态：必须是已支付且未拍摄（状态为paid）
        # 如果状态是shooting或更后面的状态，说明已经拍摄了，不能追加
        if existing_order.status not in ['paid', '已支付']:
            print(f"❌ 订单状态不正确，无法追加: {existing_order.status}")
            return False, None, '订单已拍摄或已上传图片，无法追加产品。请重新下单'
        
        # 检查是否已上传图片：如果已上传图片，不能追加产品
        existing_images = OrderImage.query.filter_by(order_id=existing_order.id).all()
        if existing_images:
            print(f"❌ 订单已上传图片，无法追加: 图片数量={len(existing_images)}")
            return False, None, '订单已上传图片，无法追加产品。请重新下单'
        
        print(f"✅ 原订单验证通过，可以追加产品")
    
    from app.utils.helpers import (
        validate_promotion_code, check_user_has_placed_order,
        check_user_eligible_for_commission, generate_stable_promotion_code,
        parse_shipping_info as _parse_shipping_info
    )
    
    try:
        # 打印调试信息
        print(f"🔍 create_multiple_items_order 订单号生成检查:")
        print(f"   add_to_existing_order: {add_to_existing_order}")
        print(f"   existing_order_number: {existing_order_number}")
        print(f"   order_data.get('orderId'): {order_data.get('orderId', 'None')}")
        
        # 生成订单号（默认MP开头，常规线下订单）
        # 如果用户选择"立即制作"，会在后续流程中改为XSDD-开头
        # 如果是追加产品模式，使用原订单号
        # 注意：正常下单时，无论前端传入什么订单号（包括PET开头的临时订单号），都应该生成新的订单号
        if add_to_existing_order and existing_order_number:
            order_number = existing_order_number
            print(f"✅ 追加产品模式：使用原订单号 {order_number}")
        else:
            # 正常下单模式：始终生成新的订单号，忽略前端传入的临时订单号
            # 前端可能传入PET开头的临时订单号或"待生成"，这些都应该被忽略
            order_number = f"MP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            print(f"✅ 新建订单模式：生成新订单号 {order_number}（忽略前端传入的临时订单号）")
        
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
                # 通过门店二维码下单：只关联门店，不扣除额度（因为用户已经支付了）
                franchisee_id = franchisee.id
                # 多个商品时，扣除金额为0（因为用户已支付）
                franchisee_deduction = 0.0
                
                store_name = franchisee.store_name
                selfie_machine_name = franchisee.machine_name
                selfie_machine_id = franchisee.machine_serial_number
                
                print(f"✅ 通过门店二维码下单（多个商品），关联门店: {franchisee.company_name} (ID: {franchisee_id})")
            else:
                print(f"⚠️ 门店二维码无效或门店已禁用: {franchisee_qr_code}")
                # 不返回错误，允许订单继续创建（向后兼容）
        
        # 为每个商品创建订单记录
        created_orders = []
        total_price = 0.0
        
        # 如果是追加产品模式，检查是否已有相同订单号的记录
        if add_to_existing_order and existing_order_number:
            # 检查是否已有相同订单号的订单记录
            existing_orders_count = Order.query.filter_by(order_number=order_number).count()
            print(f"🔍 追加产品模式：当前订单号 {order_number} 已有 {existing_orders_count} 条记录")
        
        for idx, item in enumerate(items):
            item_price = float(item.get('price', 0))
            total_price += item_price
            
            # 创建订单记录（每个商品一个订单，但使用相同的订单号）
            # 注意：order_number 字段已移除 unique=True，允许同一订单号有多条记录
            new_order = Order(
                order_number=order_number,
                customer_name=order_data.get('customerName', ''),
                customer_phone=order_data.get('customerPhone', ''),
                size=item.get('selectedSpec', ''),
                style_name=item.get('styleName', ''),  # 每个商品的工作流风格
                product_name=item.get('productName', ''),
                price=item_price,
                status='paid',  # 小程序下单默认为已支付
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
                franchisee_deduction=0.0,  # 通过门店二维码下单，不扣除额度（用户已支付）
                store_name=store_name,
                selfie_machine_id=selfie_machine_id,
                openid=order_data.get('openid', ''),
                # 保存商品信息用于工作流关联
                product_type=item.get('productType', ''),
                # 订单类型：从order_data中获取，如果没有则设为None（等支付成功后再选择）
                # 追加产品时继承原订单类型
                order_mode=existing_order.order_mode if (add_to_existing_order and existing_order) else order_data.get('orderMode', None)
            )
            
            db.session.add(new_order)
            db.session.flush()  # 获取订单ID
            
            created_orders.append(new_order)
        
        db.session.commit()
        
        # 如果是追加产品，打印详细信息
        if add_to_existing_order and existing_order:
            print(f"✅ 追加产品成功！")
            print(f"   原订单号: {order_number}")
            print(f"   新创建的订单数量: {len(created_orders)}")
            print(f"   新订单ID列表: {[o.id for o in created_orders]}")
            print(f"   所有订单共享订单号: {order_number}")
        
        # 更新用户推广资格（只处理一次）
        if created_orders and created_orders[0].openid:
            try:
                promotion_user = PromotionUser.query.filter_by(open_id=created_orders[0].openid).first()
                if promotion_user:
                    has_order = check_user_has_placed_order(promotion_user.user_id)
                    
                    if not promotion_user.eligible_for_promotion and has_order:
                        promotion_user.eligible_for_promotion = True
                        
                        if promotion_user.promotion_code and promotion_user.promotion_code.startswith('TEMP_'):
                            promotion_code = generate_stable_promotion_code(created_orders[0].openid)
                            
                            original_code = promotion_code
                            counter = 1
                            while PromotionUser.query.filter_by(promotion_code=promotion_code).first():
                                promotion_code = original_code + str(counter)
                                counter += 1
                            
                            promotion_user.promotion_code = promotion_code
                    
                    db.session.commit()
            except Exception as e:
                print(f"更新用户推广资格失败: {e}")
        
        # 处理推广码分佣（基于总价）
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
        
        # 保存订单图片（所有订单共享相同的图片）
        if order_data.get('uploadedImages'):
            for img_data in order_data['uploadedImages']:
                for order in created_orders:
                    if img_data.get('filename'):
                        db.session.add(OrderImage(
                            order_id=order.id,
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
                                    order_id=order.id,
                                    path=img_filename,
                                    is_main=False
                                ))
                            elif img_url.startswith('http'):
                                from PIL import Image
                                placeholder_img = Image.new('RGB', (300, 300), color='lightblue')
                                placeholder_img.save(img_path, 'JPEG')
                                
                                db.session.add(OrderImage(
                                    order_id=order.id,
                                    path=img_filename,
                                    is_main=False
                                ))
                            else:
                                db.session.add(OrderImage(
                                    order_id=order.id,
                                    path=img_url,
                                    is_main=False
                                ))
        
        db.session.commit()
        
        # 如果是追加产品，且原订单是"立即拍摄"类型，确保所有新订单都设置为"立即拍摄"类型
        if add_to_existing_order and existing_order and existing_order.order_mode == 'shooting':
            # 确保所有新追加的订单都设置为"立即拍摄"类型（如果之前没有设置）
            for new_order in created_orders:
                if new_order.order_mode != 'shooting':
                    new_order.order_mode = 'shooting'
            db.session.commit()
            print(f"✅ 追加产品完成，已更新所有新订单的订单类型为'立即拍摄'，订单号: {order_number}")
            print(f"   原订单类型: {existing_order.order_mode}, 新订单数量: {len(created_orders)}")
        
        # 处理分享奖励（在订单创建成功后）
        try:
            shared_user_id = order_data.get('userId') or order_data.get('user_id')
            share_record_id = order_data.get('share_record_id')
            work_id = order_data.get('work_id')
            
            if shared_user_id and (share_record_id or work_id) and created_orders:
                from app.routes.miniprogram.share_reward import process_share_reward_impl
                
                reward_data = {
                    'shared_user_id': shared_user_id,
                    'order_id': created_orders[0].id,
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
            'orderId_db': created_orders[0].id if created_orders else None,
            'orderCount': len(created_orders)  # 返回创建的订单数量
        }, None
        
    except Exception as e:
        if db:
            db.session.rollback()
        print(f"创建多个商品订单失败: {str(e)}")
        import traceback
        traceback.print_exc()
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
    Product = models.get('Product')
    ProductSize = models.get('ProductSize')
    
    config = get_server_config()
    get_base_url = config['get_base_url']
    get_media_url = config['get_media_url']
    
    from app.utils.helpers import parse_shipping_info as _parse_shipping_info
    from urllib.parse import quote
    
    try:
        # 获取所有使用相同订单号的订单记录（支持追加产品）
        orders = Order.query.filter_by(order_number=order_number).order_by(Order.created_at.asc()).all()
        
        if not orders or len(orders) == 0:
            return False, None, '订单不存在'
        
        # 使用第一个订单作为主订单（用于获取客户信息、收货信息等）
        main_order = orders[0]
        
        # 收集所有订单的图片（合并所有订单的图片）
        all_image_urls = []
        all_final_images = []
        all_hd_images = []
        for order in orders:
            images = OrderImage.query.filter_by(order_id=order.id).all()
            for img in images:
                img_url = f"{get_media_url()}/original/{img.path}"
                if img_url not in all_image_urls:
                    all_image_urls.append(img_url)
            
            # 收集精修图
            if order.final_image:
                final_img_url = f"{get_media_url()}/final/{order.final_image}"
                if final_img_url not in all_final_images:
                    all_final_images.append(final_img_url)
            
            # 收集效果图
            if order.hd_image:
                encoded_filename = quote(order.hd_image, safe='')
                hd_img_url = f"{get_base_url()}/public/hd/{encoded_filename}"
                if hd_img_url not in all_hd_images:
                    all_hd_images.append(hd_img_url)
        
        # 构建商品列表
        items = []
        total_price = 0
        for order in orders:
            # 构建每个商品的精修图和效果图URL
            item_final_image_url = None
            item_final_image_no_watermark_url = None
            if order.final_image:
                item_final_image_url = f"{get_media_url()}/final/{order.final_image}"
                if order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                    item_final_image_no_watermark_url = f"{get_media_url()}/final/clean_{order.final_image}"
            
            item_hd_image_url = None
            item_hd_image_no_watermark_url = None
            if order.hd_image:
                encoded_filename = quote(order.hd_image, safe='')
                item_hd_image_url = f"{get_base_url()}/public/hd/{encoded_filename}"
                if order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                    clean_filename = f"clean_{order.hd_image}"
                    encoded_clean_filename = quote(clean_filename, safe='')
                    item_hd_image_no_watermark_url = f"{get_base_url()}/public/hd/{encoded_clean_filename}"
            
            # 获取该订单的图片
            item_images = OrderImage.query.filter_by(order_id=order.id).all()
            item_image_urls = [f"{get_media_url()}/original/{img.path}" for img in item_images]
            
            # 获取尺寸效果图（通过产品名称和尺寸名称查找ProductSize）
            size_effect_image_url = None
            if order.product_name and order.size:
                try:
                    Product = models.get('Product')
                    ProductSize = models.get('ProductSize')
                    if Product and ProductSize:
                        # 通过产品名称查找产品
                        product = Product.query.filter_by(name=order.product_name, is_active=True).first()
                        if product:
                            # 通过尺寸名称查找尺寸
                            size = ProductSize.query.filter_by(
                                product_id=product.id,
                                size_name=order.size,
                                is_active=True
                            ).first()
                            if size and size.effect_image_url:
                                # 构建完整的图片URL
                                if size.effect_image_url.startswith('/'):
                                    size_effect_image_url = f"{get_base_url()}{size.effect_image_url}"
                                elif size.effect_image_url.startswith('http'):
                                    size_effect_image_url = size.effect_image_url
                                else:
                                    size_effect_image_url = f"{get_base_url()}/static/images/products/{size.effect_image_url}"
                except Exception as e:
                    print(f"获取尺寸效果图失败: {str(e)}")
            
            items.append({
                'orderId_db': order.id,
                'styleName': order.style_name or '威廉国王',
                'productName': order.product_name or '艺术钥匙扣',
                'productType': order.size,
                'selectedSpec': order.size,  # 规格
                'sizeEffectImage': size_effect_image_url,  # 尺寸效果图
                'quantity': 1,
                'price': order.price,
                'totalPrice': order.price,
                'status': order.status,
                'orderMode': order.order_mode,
                'images': item_image_urls,
                'originalImages': item_image_urls,
                'finalImage': item_final_image_url,
                'finalImageNoWatermark': item_final_image_no_watermark_url,
                'hdImage': item_hd_image_url,
                'hdImageNoWatermark': item_hd_image_no_watermark_url,
                'createTime': order.created_at.isoformat(),
                'completeTime': order.completed_at.isoformat() if order.completed_at else None
            })
            total_price += order.price
        
        # 使用主订单的第一个精修图和效果图（用于向后兼容）
        main_final_image_url = None
        main_final_image_no_watermark_url = None
        if main_order.final_image:
            main_final_image_url = f"{get_media_url()}/final/{main_order.final_image}"
            if main_order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                main_final_image_no_watermark_url = f"{get_media_url()}/final/clean_{main_order.final_image}"
        
        main_hd_image_url = None
        main_hd_image_no_watermark_url = None
        if main_order.hd_image:
            encoded_filename = quote(main_order.hd_image, safe='')
            main_hd_image_url = f"{get_base_url()}/public/hd/{encoded_filename}"
            if main_order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                clean_filename = f"clean_{main_order.hd_image}"
                encoded_clean_filename = quote(clean_filename, safe='')
                main_hd_image_no_watermark_url = f"{get_base_url()}/public/hd/{encoded_clean_filename}"
        
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
        
        # 确定订单状态（如果有多个商品，使用最优先的状态）
        # 优先级：pending > processing > manufacturing > completed > paid > 其他
        status_priority = {
            'pending': 1,
            'processing': 2,
            'manufacturing': 3,
            'completed': 4,
            'paid': 5
        }
        main_status = main_order.status
        for order in orders:
            if order.status in status_priority:
                if main_status not in status_priority or status_priority[order.status] < status_priority.get(main_status, 999):
                    main_status = order.status
        
        order_data = {
            'orderId': main_order.order_number,
            'orderId_db': main_order.id,
            'customerName': main_order.customer_name,
            'customerPhone': main_order.customer_phone,
            'styleName': main_order.style_name or '威廉国王',  # 向后兼容：使用第一个商品的风格
            'productName': main_order.product_name or '艺术钥匙扣',  # 向后兼容：使用第一个商品的产品名
            'productType': main_order.size,  # 向后兼容
            'selectedSpec': main_order.size,  # 向后兼容
            'quantity': len(orders),  # 商品数量
            'totalPrice': total_price,  # 总金额
            'status': main_status,
            'statusText': status_map.get(main_status, main_status),
            'orderMode': main_order.order_mode,  # 订单类型
            'createTime': main_order.created_at.isoformat(),
            'completeTime': main_order.completed_at.isoformat() if main_order.completed_at else None,
            'images': all_image_urls,  # 所有订单的图片合并
            'originalImages': all_image_urls,
            'finalImage': main_final_image_url,  # 向后兼容：使用第一个商品的精修图
            'finalImageNoWatermark': main_final_image_no_watermark_url,
            'hdImage': main_hd_image_url,  # 向后兼容：使用第一个商品的效果图
            'hdImageNoWatermark': main_hd_image_no_watermark_url,
            'shippingInfo': _parse_shipping_info(main_order.shipping_info),
            # 新增：商品列表
            'items': items,  # 所有商品列表
            'isMultipleItems': len(orders) > 1  # 是否多个商品
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
