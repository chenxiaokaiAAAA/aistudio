# -*- coding: utf-8 -*-
"""
小程序订单相关路由
"""
from flask import Blueprint, request, jsonify, current_app
from app.services.order_service import (
    create_miniprogram_order,
    get_order_by_number,
    check_order_for_verification,
    upload_order_photos
)
from app.routes.miniprogram.common import get_models, get_helper_functions
import qrcode
import base64
from io import BytesIO
import threading

# 创建订单相关的子蓝图
bp = Blueprint('orders', __name__)


@bp.route('/orders', methods=['POST'])
def miniprogram_submit_order():
    """小程序提交订单"""
    try:
        data = request.get_json()
        print(f"收到小程序订单数据: {data}")
        
        # 调用服务层函数创建订单
        success, result, error_message = create_miniprogram_order(data)
        
        if success:
            response_data = {
                'status': 'success',
                'message': '订单提交成功',
                **result
            }
            print(f"✅ 订单创建成功，返回数据: {response_data}")
            return jsonify(response_data)
        else:
            print(f"❌ 订单创建失败: {error_message}")
            status_code = 400 if '缺少' in error_message or '不足' in error_message or '不存在' in error_message else 500
            return jsonify({
                'status': 'error',
                'message': error_message
            }), status_code
            
    except Exception as e:
        import sys
        import traceback
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                test_server_module.db.session.rollback()
        print(f"❌ 订单提交异常: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error', 
            'message': f'订单提交失败: {str(e)}'
        }), 500


@bp.route('/orders', methods=['GET'])
def miniprogram_get_orders():
    """小程序获取订单列表 - 支持openid、userId和phone查询（临时兼容）"""
    try:
        # 延迟导入，避免循环导入
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'Order'):
                Order = test_server_module.Order
                OrderImage = test_server_module.OrderImage
                PromotionUser = test_server_module.PromotionUser
            else:
                from app.models import Order, OrderImage, PromotionUser
        else:
            from app.models import Order, OrderImage, PromotionUser
        
        from server_config import get_base_url, get_media_url
        from app.utils.helpers import parse_shipping_info as _parse_shipping_info
        from datetime import datetime
        
        openid = request.args.get('openid')
        user_id = request.args.get('userId')
        phone = request.args.get('phone')
        
        orders = []
        
        # 优先使用openid查询
        if openid:
            invalid_openids = ['anonymous', 'undefined', 'null', '']
            if openid in invalid_openids:
                print(f"⚠️ openid无效: {openid}，开发模式：尝试查询所有小程序订单（最近10条）")
                orders = Order.query.filter(
                    Order.source_type == 'miniprogram'
                ).order_by(Order.created_at.desc()).limit(10).all()
            elif len(openid) < 10 or not openid.replace('_', '').replace('-', '').isalnum():
                print(f"⚠️ openid格式不正确: {openid}，开发模式：尝试查询所有小程序订单（最近10条）")
                orders = Order.query.filter(
                    Order.source_type == 'miniprogram'
                ).order_by(Order.created_at.desc()).limit(10).all()
            else:
                orders = Order.query.filter(
                    Order.openid == openid,
                    Order.source_type == 'miniprogram'
                ).order_by(Order.created_at.desc()).all()
                
                if len(orders) == 0 and openid == 'test_openid_dev_mode_fixed':
                    print(f"⚠️ 开发模式：通过openid查询不到订单，尝试查询所有小程序订单（最近10条）")
                    orders = Order.query.filter(
                        Order.source_type == 'miniprogram'
                    ).order_by(Order.created_at.desc()).limit(10).all()
        
        elif user_id:
            user = PromotionUser.query.filter_by(user_id=user_id).first()
            if user and user.open_id:
                orders = Order.query.filter(
                    Order.openid == user.open_id,
                    Order.source_type == 'miniprogram'
                ).order_by(Order.created_at.desc()).all()
            else:
                return jsonify({'status': 'error', 'message': '用户ID无效或未绑定openid'}), 400
        
        elif phone:
            if not phone.isdigit() or len(phone) != 11:
                return jsonify({'status': 'error', 'message': '手机号格式不正确'}), 400
            
            orders = Order.query.filter(
                Order.customer_phone == phone,
                Order.source_type == 'miniprogram'
            ).order_by(Order.created_at.desc()).all()
        
        else:
            return jsonify({'status': 'error', 'message': '缺少openid、userId或phone参数'}), 400
        
        # 按订单号分组，合并相同订单号的订单
        from collections import defaultdict
        from urllib.parse import quote
        
        orders_by_number = defaultdict(list)
        for order in orders:
            orders_by_number[order.order_number].append(order)
        
        order_list = []
        for order_number, order_group in orders_by_number.items():
            # 按创建时间排序
            order_group.sort(key=lambda x: x.created_at)
            
            # 使用第一个订单作为主订单（用于获取客户信息等）
            main_order = order_group[0]
            
            # 收集所有订单的图片
            all_image_urls = []
            for order in order_group:
                images = OrderImage.query.filter_by(order_id=order.id).all()
                for img in images:
                    img_url = f"{get_media_url()}/original/{img.path}"
                    if img_url not in all_image_urls:
                        all_image_urls.append(img_url)
            
            # 使用主订单的精修图和效果图（向后兼容）
            final_image_url = None
            final_image_no_watermark_url = None
            if main_order.final_image:
                final_image_url = f"{get_media_url()}/final/{main_order.final_image}"
                if main_order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                    final_image_no_watermark_url = f"{get_media_url()}/final/clean_{main_order.final_image}"
            
            hd_image_url = None
            hd_image_no_watermark_url = None
            if main_order.hd_image:
                encoded_filename = quote(main_order.hd_image, safe='')
                hd_image_url = f"{get_base_url()}/public/hd/{encoded_filename}"
                if main_order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                    clean_filename = f"clean_{main_order.hd_image}"
                    encoded_clean_filename = quote(clean_filename, safe='')
                    hd_image_no_watermark_url = f"{get_base_url()}/public/hd/{encoded_clean_filename}"
            
            # 构建商品列表
            items = []
            total_price = 0
            for order in order_group:
                item_images = OrderImage.query.filter_by(order_id=order.id).all()
                item_image_urls = [f"{get_media_url()}/original/{img.path}" for img in item_images]
                
                items.append({
                    'orderId_db': order.id,
                    'styleName': order.style_name or '威廉国王',
                    'productName': order.product_name or '艺术钥匙扣',
                    'productType': order.size,
                    'selectedSpec': order.size,
                    'quantity': 1,
                    'price': order.price,
                    'status': order.status,
                    'orderMode': order.order_mode,
                    'images': item_image_urls,
                    'createTime': order.created_at.isoformat()
                })
                total_price += order.price
            
            # 检查是否有图片
            has_images = len(all_image_urls) > 0
            
            # 确定订单状态（如果有多个商品，使用最优先的状态）
            status_priority = {
                'pending': 1,
                'processing': 2,
                'manufacturing': 3,
                'completed': 4,
                'paid': 5
            }
            main_status = main_order.status
            for order in order_group:
                if order.status in status_priority:
                    if main_status not in status_priority or status_priority[order.status] < status_priority.get(main_status, 999):
                        main_status = order.status
            
            # 根据订单状态、订单类型和是否上传图片来确定显示状态
            if main_status == 'paid':
                if main_order.order_mode == 'shooting':
                    status_text = '待拍摄' if not has_images else '正在拍摄'
                elif main_order.order_mode == 'making':
                    status_text = '待传图' if not has_images else '待制作'
                else:
                    status_text = '待拍摄' if not has_images else '正在拍摄'
            elif main_status == 'pending':
                status_text = '待制作'
            else:
                status_map = {
                    'unpaid': '待支付',
                    'pending': '待制作',
                    'completed': '已完成',
                    'shipped': '已发货',
                    'hd_ready': '高清放大',
                    'manufacturing': '制作中',
                    'processing': '处理中',
                    'selection_completed': '选片已完成',
                    'shooting': '正在拍摄',
                    'retouching': '美颜处理中',
                    'ai_processing': 'AI任务处理中',
                    'pending_selection': '待选片',
                    'selection_completed': '已选片',
                    'printing': '打印中',
                    'pending_shipment': '待发货',
                    'delivered': '已发货',
                    'cancelled': '已取消',
                    'refunded': '已退款'
                }
                status_text = status_map.get(main_status, main_status)
            
            order_list.append({
                'orderId': order_number,
                'orderId_db': main_order.id,  # 使用主订单的数据库ID
                'customerName': main_order.customer_name,
                'customerPhone': main_order.customer_phone,
                'styleName': main_order.style_name or '威廉国王',  # 向后兼容：使用第一个商品的风格
                'productName': main_order.product_name or '艺术钥匙扣',  # 向后兼容：使用第一个商品的产品名
                'productType': main_order.size,  # 向后兼容
                'quantity': len(order_group),  # 商品数量
                'totalPrice': total_price,  # 总金额
                'status': main_status,
                'statusText': status_text,
                'orderMode': main_order.order_mode,
                'createTime': main_order.created_at.isoformat(),
                'completeTime': main_order.completed_at.isoformat() if main_order.completed_at else None,
                'images': all_image_urls,  # 所有订单的图片合并
                'originalImages': all_image_urls,
                'finalImage': final_image_url,
                'finalImageNoWatermark': final_image_no_watermark_url,
                'hdImage': hd_image_url,
                'hdImageNoWatermark': hd_image_no_watermark_url,
                'shippingInfo': _parse_shipping_info(main_order.shipping_info),
                # 新增：商品列表和是否多个商品标记
                'items': items,  # 所有商品列表
                'isMultipleItems': len(order_group) > 1  # 是否多个商品
            })
        
        return jsonify({
            'status': 'success',
            'orders': order_list
        })
        
    except Exception as e:
        print(f"获取订单失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取订单失败: {str(e)}'}), 500


@bp.route('/order/<order_number>', methods=['GET'])
def miniprogram_get_order_by_number(order_number):
    """小程序通过订单号查询单个订单（用于订单详情页，不依赖openid）"""
    try:
        # 调用服务层函数
        success, order_data, error_message = get_order_by_number(order_number)
        
        if success:
            return jsonify({
                'status': 'success',
                'order': order_data
            })
        else:
            status_code = 404 if '不存在' in error_message else 500
            return jsonify({
                'status': 'error',
                'message': error_message
            }), status_code
            
    except Exception as e:
        print(f"通过订单号查询订单失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'查询订单失败: {str(e)}'}), 500


@bp.route('/order/check', methods=['GET'])
def android_check_order():
    """安卓APP检查订单状态（用于扫码核销）"""
    try:
        order_id = request.args.get('orderId') or request.args.get('order_id')
        machine_serial_number = request.args.get('machineSerialNumber') or request.args.get('machine_serial_number') or request.args.get('selfie_machine_id')
        
        if not order_id:
            return jsonify({
                'success': False,
                'message': '订单ID不能为空'
            }), 400
        
        # 调用服务层函数
        success, order_data, error_message = check_order_for_verification(order_id, machine_serial_number)
        
        if success:
            return jsonify({
                'success': True,
                'order': order_data
            })
        else:
            # 如果已经拍摄过，返回400但包含订单信息
            if '已经拍摄过' in error_message:
                return jsonify({
                    'success': False,
                    'message': error_message,
                    'order': order_data
                }), 400
            else:
                status_code = 404 if '不存在' in error_message else 500
                return jsonify({
                    'success': False,
                    'message': error_message
                }), status_code
            
    except Exception as e:
        print(f"检查订单状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'检查订单失败: {str(e)}'
        }), 500


@bp.route('/order/qrcode', methods=['GET'])
def generate_order_qrcode():
    """生成订单核销二维码"""
    try:
        order_id = request.args.get('orderId') or request.args.get('order_id')
        
        if not order_id:
            return jsonify({
                'success': False,
                'message': '订单ID不能为空'
            }), 400
        
        # 延迟导入
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'Order'):
                Order = test_server_module.Order
            else:
                from app.models import Order
        else:
            from app.models import Order
        
        # 查找订单
        order = Order.query.filter_by(order_number=order_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
        
        # 生成二维码内容：格式为 order:订单ID
        qr_content = f"order:{order_id}"
        
        # 生成二维码图片
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # 转换为base64以便返回
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        qr_image_url = f"data:image/png;base64,{img_base64}"
        
        return jsonify({
            'success': True,
            'orderId': order_id,
            'qrContent': qr_content,
            'qrImage': qr_image_url
        })
        
    except Exception as e:
        print(f"生成订单二维码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'生成二维码失败: {str(e)}'
        }), 500


@bp.route('/orders/<order_id>/generate-qrcode', methods=['POST'])
def generate_shooting_qrcode(order_id):
    """生成拍摄核销二维码（立即拍摄）"""
    try:
        data = request.get_json() or {}
        action = data.get('action', 'shooting')
        
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '系统未初始化'
            }), 500
        
        Order = models['Order']
        db = models['db']
        
        # 查找订单（支持订单号或ID）
        order = None
        if order_id.isdigit():
            order = Order.query.get(int(order_id))
        if not order:
            order = Order.query.filter_by(order_number=order_id).first()
        
        if not order:
            print(f"❌ 订单不存在: order_id={order_id}, 类型={type(order_id)}")
            # 尝试查找最近创建的订单（用于调试）
            recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
            print(f"最近5个订单: {[(o.id, o.order_number, o.status) for o in recent_orders]}")
            return jsonify({
                'success': False,
                'message': f'订单不存在: {order_id}'
            }), 404
        
        # 对于多个商品订单（同一订单号有多条记录），需要更新所有相关订单
        order_number = order.order_number
        all_orders = Order.query.filter_by(order_number=order_number).all()
        
        print(f"🔍 找到 {len(all_orders)} 条订单记录，订单号: {order_number}")
        
        # 更新所有相关订单的 order_mode
        for o in all_orders:
            o.order_mode = 'shooting'
            print(f"✅ 已更新订单 ID={o.id}, order_mode='shooting', order_number={o.order_number}")
        
        # 拍摄模式（常规线下订单）保持原订单号格式（MP开头），不需要修改
        db.session.commit()
        
        # 生成二维码内容：格式为 order:订单ID
        qr_content = f"order:{order.order_number}"
        
        # 生成二维码图片
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # 转换为base64以便返回
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        qr_image_url = f"data:image/png;base64,{img_base64}"
        
        return jsonify({
            'success': True,
            'status': 'success',
            'orderId': order.order_number,
            'qrContent': qr_content,
            'qrImage': qr_image_url,
            'message': '拍摄核销二维码生成成功'
        })
        
    except Exception as e:
        print(f"生成拍摄二维码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'生成二维码失败: {str(e)}'
        }), 500


@bp.route('/orders/<order_id>/update-order-mode', methods=['POST'])
def update_order_mode(order_id):
    """更新订单类型（立即拍摄/立即制作）"""
    try:
        data = request.get_json() or {}
        order_mode = data.get('orderMode')  # 'shooting' 或 'making'
        
        if order_mode not in ['shooting', 'making']:
            return jsonify({
                'success': False,
                'message': '订单类型无效，必须是 shooting 或 making'
            }), 400
        
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '系统未初始化'
            }), 500
        
        Order = models['Order']
        OrderImage = models['OrderImage']
        db = models['db']
        
        # 查找订单（支持订单号或ID）
        order = None
        if order_id.isdigit():
            order = Order.query.get(int(order_id))
        if not order:
            order = Order.query.filter_by(order_number=order_id).first()
        
        if not order:
            return jsonify({
                'success': False,
                'message': f'订单不存在: {order_id}'
            }), 404
        
        # 检查订单状态：只有在"已支付"状态才能切换
        if order.status not in ['paid', '已支付']:
            return jsonify({
                'success': False,
                'message': '只有已支付的订单才能切换类型'
            }), 400
        
        # 检查是否已上传图片：如果已上传图片，不能切换
        # 对于多个商品订单，需要检查所有相关订单是否已上传图片
        order_number = order.order_number
        all_orders = Order.query.filter_by(order_number=order_number).all()
        
        for o in all_orders:
            order_images = OrderImage.query.filter_by(order_id=o.id).all()
            if order_images:
                return jsonify({
                    'success': False,
                    'message': '订单已上传图片，无法切换类型'
                }), 400
        
        # 对于多个商品订单（同一订单号有多条记录），需要更新所有相关订单
        print(f"🔍 找到 {len(all_orders)} 条订单记录，订单号: {order_number}")
        
        old_mode = order.order_mode
        new_order_number = order_number
        
        # 如果切换为"立即制作"且订单号是MP开头，改为XSDD-开头
        if order_mode == 'making' and order_number.startswith('MP'):
            from datetime import datetime
            import random
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            new_order_number = f'XSDD-{timestamp}{random_suffix}'
            print(f"✅ 订单类型切换为'立即制作'，将更新订单号: {order_number} -> {new_order_number}")
        # 如果切换为"立即拍摄"且订单号是XSDD-开头，改回MP-开头
        elif order_mode == 'shooting' and order_number.startswith('XSDD-'):
            from datetime import datetime
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = uuid.uuid4().hex[:4].upper()
            new_order_number = f'MP{timestamp}{random_suffix}'
            print(f"✅ 订单类型切换为'立即拍摄'，将更新订单号: {order_number} -> {new_order_number}")
        
        # 更新所有相关订单的 order_mode 和订单号
        for o in all_orders:
            o.order_mode = order_mode
            if new_order_number != order_number:
                o.order_number = new_order_number
            print(f"✅ 已更新订单 ID={o.id}, order_mode='{order_mode}', order_number={o.order_number}")
        
        # 如果订单号变更，同时更新相关AI任务的order_number字段（冗余字段，用于查询方便）
        if new_order_number != order_number:
            try:
                AITask = models.get('AITask')
                if AITask:
                    # 获取所有相关订单的ID
                    order_ids = [o.id for o in all_orders]
                    # 更新这些订单关联的AI任务的order_number字段
                    updated_tasks = AITask.query.filter(AITask.order_id.in_(order_ids)).update({
                        AITask.order_number: new_order_number
                    }, synchronize_session=False)
                    if updated_tasks > 0:
                        print(f"✅ 已更新 {updated_tasks} 个AI任务的订单号: {order_number} -> {new_order_number}")
            except Exception as e:
                print(f"⚠️ 更新AI任务订单号失败（不影响主流程）: {str(e)}")
        
        db.session.commit()
        
        print(f"✅ 订单类型已更新: {order_number} -> {new_order_number}, {old_mode} -> {order_mode}")
        
        return jsonify({
            'success': True,
            'status': 'success',
            'orderId': order.order_number,
            'orderMode': order_mode,
            'message': '订单类型更新成功'
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"更新订单类型失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'更新订单类型失败: {str(e)}'
        }), 500


@bp.route('/orders/<order_id>/set-manual', methods=['POST'])
def set_order_as_manual(order_id):
    """标记订单为人工线上订单（立即制作）"""
    try:
        data = request.get_json() or {}
        action = data.get('action', 'making')
        is_manual_order = data.get('isManualOrder', True)
        
        models = get_models()
        if not models:
            return jsonify({
                'success': False,
                'message': '系统未初始化'
            }), 500
        
        Order = models['Order']
        db = models['db']
        
        # 查找订单（支持订单号或ID）
        order = None
        if order_id.isdigit():
            order = Order.query.get(int(order_id))
        if not order:
            order = Order.query.filter_by(order_number=order_id).first()
        
        if not order:
            print(f"❌ 订单不存在: order_id={order_id}, 类型={type(order_id)}")
            # 尝试查找最近创建的订单（用于调试）
            recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
            print(f"最近5个订单: {[(o.id, o.order_number, o.status) for o in recent_orders]}")
            return jsonify({
                'success': False,
                'message': f'订单不存在: {order_id}'
            }), 404
        
        # 对于多个商品订单（同一订单号有多条记录），需要更新所有相关订单
        order_number = order.order_number
        all_orders = Order.query.filter_by(order_number=order_number).all()
        
        print(f"🔍 找到 {len(all_orders)} 条订单记录，订单号: {order_number}")
        
        # 如果是线上订单（立即制作），订单号应该以 XSDD- 开头
        # 如果当前订单号是 MP 开头（常规线下订单），则改为 XSDD- 开头
        new_order_number = order_number
        if order_number and order_number.startswith('MP'):
            from datetime import datetime
            import uuid
            # 生成新的订单号：XSDD-YYYYMMDDHHMMSSXXXX（线上订单）
            new_order_number = f"XSDD-{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            old_order_number = order_number
            print(f"✅ 立即制作订单，将更新订单号: {old_order_number} -> {new_order_number}")
        elif order_number and order_number.startswith('XSDD-'):
            print(f"ℹ️ 订单号已经是XSDD-开头，无需更新: {order_number}")
        else:
            print(f"⚠️ 订单号格式异常: {order_number}")
        
        # 更新所有相关订单的 order_mode 和订单号
        for o in all_orders:
            o.order_mode = 'making'
            if new_order_number != order_number:
                o.order_number = new_order_number
            print(f"✅ 已更新订单 ID={o.id}, order_mode='making', order_number={o.order_number}")
        
        # 标记订单不走自动化流程（人工线上订单）
        # 可以通过设置一个标记或者修改订单状态来实现
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'status': 'success',
            'message': '订单已标记为人工线上订单',
            'orderId': order.order_number
        })
        
    except Exception as e:
        print(f"标记人工订单失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'标记失败: {str(e)}'
        }), 500


@bp.route('/order/upload', methods=['POST'])
def android_upload_photos():
    """安卓APP上传照片（用于证件照拍摄后回传）"""
    try:
        print("=" * 50)
        print("📸 收到安卓APP上传照片请求")
        print(f"请求方法: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Form数据: {dict(request.form)}")
        print(f"Files keys: {list(request.files.keys())}")
        print("=" * 50)
        
        # 延迟导入，避免循环导入
        import sys
        import os
        import uuid
        from werkzeug.utils import secure_filename
        from PIL import Image
        
        # 从test_server模块获取db和app实例
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            Order = test_server_module.Order
            OrderImage = test_server_module.OrderImage
            SelfieMachine = test_server_module.SelfieMachine
            db = test_server_module.db
            app = test_server_module.app
            print("✅ 从test_server模块获取db和app实例成功")
        else:
            # 如果test_server模块不存在，尝试从current_app获取
            from app.models import Order, OrderImage, SelfieMachine
            from app import db as app_db
            db = app_db
            app = current_app
            print("✅ 从current_app获取db和app实例成功")
        
        order_id = request.form.get('orderId') or request.form.get('order_id')
        machine_serial_number = request.form.get('machineSerialNumber') or request.form.get('machine_serial_number') or request.form.get('selfie_machine_id')
        
        print(f"订单ID: {order_id}")
        print(f"自拍机序列号: {machine_serial_number}")
        
        if not order_id:
            print("❌ 订单ID为空")
            return jsonify({
                'success': False,
                'message': '订单ID不能为空'
            }), 400
        
        # 查找订单
        order = Order.query.filter_by(order_number=order_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在'
            }), 404
        
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
                    
                    print(f"✅ 订单 {order_id} 已通过自拍机序列号 {machine_serial_number} 关联到加盟商: {franchisee.company_name} (门店: {franchisee.store_name}, 设备: {machine.machine_name})")
            except Exception as e:
                print(f"⚠️  通过自拍机序列号关联加盟商失败: {e}")
        
        # 检查是否有上传的文件（Android App使用'photos'作为字段名）
        print(f"检查上传文件，request.files.keys(): {list(request.files.keys())}")
        
        if 'photos' not in request.files:
            print("❌ request.files中没有'photos'字段")
            # 尝试查找所有包含'photo'的字段
            photo_keys = [key for key in request.files.keys() if 'photo' in key.lower()]
            if photo_keys:
                print(f"⚠️  找到类似的字段: {photo_keys}")
            return jsonify({
                'success': False,
                'message': f'没有上传文件。找到的字段: {list(request.files.keys())}'
            }), 400
        
        files = request.files.getlist('photos')
        print(f"获取到 {len(files)} 个文件")
        
        if not files or len(files) == 0:
            print("❌ 文件列表为空")
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        uploaded_files = []
        
        # 处理每个上传的文件
        for idx, file in enumerate(files):
            if file.filename == '':
                print(f"⚠️  文件 {idx} 的文件名为空，跳过")
                continue
            
            print(f"处理文件 {idx + 1}/{len(files)}: {file.filename}")
            
            # 生成安全的文件名
            filename = secure_filename(f"android_{uuid.uuid4().hex[:8]}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            print(f"保存文件到: {file_path}")
            
            # 确保上传目录存在
            upload_dir = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                print(f"✅ 创建上传目录: {upload_dir}")
            
            # 保存文件
            try:
                file.save(file_path)
                print(f"✅ 文件保存成功: {file_path}")
            except Exception as save_error:
                print(f"❌ 文件保存失败: {save_error}")
                raise
            
            # 检查文件大小并压缩（如果需要）
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:  # 5MB
                try:
                    with Image.open(file_path) as img:
                        img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                        img.save(file_path, 'JPEG', quality=85, optimize=True)
                        file_size = os.path.getsize(file_path)
                except Exception as compress_error:
                    print(f"图片压缩失败: {compress_error}")
            
            # 创建订单图片记录
            order_image = OrderImage(
                order_id=order.id,
                path=filename,
                is_main=(len(uploaded_files) == 0)  # 第一张图片设为主图
            )
            db.session.add(order_image)
            
            # 更新订单的original_image字段（如果这是第一张图片）
            if len(uploaded_files) == 0:
                order.original_image = filename
            
            uploaded_files.append({
                'filename': filename,
                'originalname': file.filename,
                'path': f'/uploads/{filename}',
                'size': file_size
            })
        
        # 更新订单状态：上传完所有图片后，根据订单类型更新状态
        from datetime import datetime
        
        # 记录拍摄完成时间（如果Order模型有该字段）
        try:
            if hasattr(order, 'shooting_completed_at') and not order.shooting_completed_at:
                order.shooting_completed_at = datetime.now()
        except Exception:
            pass  # 如果字段不存在，忽略
        
        # 根据订单类型和是否启用美图API来决定状态
        # 立即拍摄（shooting）：上传完图片后，如果启用美图API，立即更新为"美颜中"，否则更新为"AI任务处理中"
        if order.order_mode == 'shooting':
            # 检查是否启用美图API
            try:
                MeituAPIConfig = test_server_module.MeituAPIConfig if 'test_server' in sys.modules else None
                if MeituAPIConfig:
                    meitu_config = MeituAPIConfig.query.filter_by(is_active=True).first()
                    if meitu_config and meitu_config.enable_in_workflow:
                        # 启用美图API：上传完图片后立即更新为"美颜中"
                        if order.status in ['pending', 'unpaid', 'paid', 'shooting']:
                            order.status = 'retouching'  # 美颜处理中
                            print(f"✅ 订单 {order.order_number} 状态已更新为: retouching（美颜处理中）- 已接收全部图片，开始美图API处理")
                    else:
                        # 未启用美图API：直接更新为"AI任务处理中"
                        if order.status in ['pending', 'unpaid', 'paid', 'shooting']:
                            order.status = 'ai_processing'  # AI任务处理中
                            print(f"✅ 订单 {order.order_number} 状态已更新为: ai_processing（AI任务处理中）- 已接收全部图片，跳过美图API")
                else:
                    # 无法获取美图配置：默认更新为"AI任务处理中"
                    if order.status in ['pending', 'unpaid', 'paid', 'shooting']:
                        order.status = 'ai_processing'  # AI任务处理中
                        print(f"✅ 订单 {order.order_number} 状态已更新为: ai_processing（AI任务处理中）- 已接收全部图片")
            except Exception as e:
                print(f"⚠️ 检查美图API配置失败: {e}，默认更新为AI任务处理中")
                if order.status in ['pending', 'unpaid', 'paid', 'shooting']:
                    order.status = 'ai_processing'  # AI任务处理中
        else:
            # 立即制作或其他类型：上传完图片后更新为"正在拍摄"
            if order.status in ['pending', 'unpaid', 'paid']:
                order.status = 'shooting'  # 正在拍摄
                print(f"✅ 订单 {order.order_number} 状态已更新为: shooting（正在拍摄）")
        
        db.session.commit()
        
        # 异步处理图片：美图API + AI工作流
        # 根据订单类型判断是否进入自动化流程
        # 立即拍摄（shooting）：收到上传的原图就进入AI制作流程
        # 立即制作（making）：收到上传的图片也不进行任何处理
        if order.order_mode == 'shooting':
            # 立即拍摄：进入自动化流程
            try:
                from app.services.image_processing_service import process_order_images
                
                # 获取风格分类ID（从订单中获取）
                style_category_id = order.style_category_id if hasattr(order, 'style_category_id') else None
                style_image_id = order.style_image_id if hasattr(order, 'style_image_id') else None
                
                # 在后台线程中处理图片（需要应用上下文）
                # 使用函数开头已获取的app实例（从test_server模块）
                app_instance = app  # app已在函数开头从test_server获取
                def process_images_async():
                    try:
                        # 使用从test_server获取的应用实例创建应用上下文
                        with app_instance.app_context():
                            process_order_images(
                                order_id=order.id,
                                order_number=order.order_number,
                                style_category_id=style_category_id,
                                style_image_id=style_image_id
                            )
                    except Exception as e:
                        print(f"后台处理图片失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                processing_thread = threading.Thread(target=process_images_async)
                processing_thread.daemon = True
                processing_thread.start()
                print(f"✅ 立即拍摄订单，已启动后台图片处理流程（美图API + AI工作流）")
            except Exception as e:
                print(f"⚠️  启动图片处理流程失败: {str(e)}")
                # 不影响上传成功的返回
        elif order.order_mode == 'making':
            # 立即制作：不进行任何自动化处理，等待人工处理
            print(f"ℹ️ 立即制作订单，跳过自动化处理流程，等待人工处理")
        else:
            # 未设置订单类型：默认进入自动化流程（兼容旧订单）
            print(f"⚠️ 订单类型未设置，默认进入自动化流程")
            try:
                from app.services.image_processing_service import process_order_images
                
                style_category_id = order.style_category_id if hasattr(order, 'style_category_id') else None
                style_image_id = order.style_image_id if hasattr(order, 'style_image_id') else None
                
                def process_images_async():
                    try:
                        process_order_images(
                            order_id=order.id,
                            order_number=order.order_number,
                            style_category_id=style_category_id,
                            style_image_id=style_image_id
                        )
                    except Exception as e:
                        print(f"后台处理图片失败: {str(e)}")
                
                processing_thread = threading.Thread(target=process_images_async)
                processing_thread.daemon = True
                processing_thread.start()
                print(f"✅ 已启动后台图片处理流程（美图API + AI工作流）")
            except Exception as e:
                print(f"⚠️  启动图片处理流程失败: {str(e)}")
        
        # 获取媒体URL
        from server_config import get_media_url
        media_url = get_media_url()
        
        # 构建返回数据
        uploaded_files_info = []
        for file_info in uploaded_files:
            uploaded_files_info.append({
                'filename': file_info['filename'],
                'originalname': file_info['originalname'],
                'path': f'/uploads/{file_info["filename"]}',
                'url': f'{media_url}/original/{file_info["filename"]}',
                'size': file_info['size'],
                'uploadTime': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'message': '照片上传成功',
            'orderId': order.order_number,
            'uploadedFiles': uploaded_files_info,
            'status': order.status
        })
            
    except Exception as e:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                test_server_module.db.session.rollback()
        print(f"上传订单照片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'上传照片失败: {str(e)}'
        }), 500


@bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def miniprogram_update_order_status(order_id):
    """小程序更新订单状态"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        Commission = models.get('Commission')
        app = models.get('app')
        send_order_completion_notification_auto = helpers.get('send_order_completion_notification_auto')
        from datetime import datetime
        import os
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
        
        status = data.get('status')
        status_text = data.get('statusText')
        
        if not status:
            return jsonify({'status': 'error', 'message': '缺少状态参数'}), 400
        
        # 查找订单
        order = Order.query.get_or_404(order_id)
        if order.source_type != 'miniprogram':
            return jsonify({'status': 'error', 'message': '订单类型不匹配'}), 400
        
        # 更新订单状态
        order.status = status
        if status == 'delivered':
            order.completed_at = datetime.now()
            # 更新分佣状态为已结算
            if Commission:
                commission = Commission.query.filter_by(order_id=order.order_number).first()
                if commission:
                    commission.status = 'completed'
                    commission.complete_time = datetime.now()
        elif status == 'completed':
            # 状态为completed时，设置完成时间
            order.completed_at = datetime.now()
        
        db.session.commit()
        
        # 如果状态更新为'completed'（已完成），自动发送订单完成通知
        if status == 'completed' and send_order_completion_notification_auto:
            # 检查是否为加盟商订单且需要确版
            if hasattr(order, 'franchisee_id') and order.franchisee_id and hasattr(order, 'need_confirmation') and order.need_confirmation and not getattr(order, 'franchisee_confirmed', False):
                # 加盟商订单需要确版，不发送通知
                pass
            else:
                # 普通订单或已确认的加盟商订单，正常流程
                try:
                    send_order_completion_notification_auto(order)
                except Exception as e:
                    print(f"发送订单完成通知失败: {e}")
        
        # 如果状态更新为'hd_ready'（高清放大），自动发送到冲印系统
        if status == 'hd_ready' and app:
            try:
                from printer_config import PRINTER_SYSTEM_CONFIG, PRINTER_SYSTEM_AVAILABLE
                from printer_client import PrinterSystemClient
                
                if PRINTER_SYSTEM_AVAILABLE and PRINTER_SYSTEM_CONFIG.get('enabled', False):
                    # 检查是否有高清图片
                    if hasattr(order, 'hd_image') and order.hd_image:
                        hd_image_path = os.path.join(app.config.get('HD_FOLDER', 'hd_images'), order.hd_image)
                        if os.path.exists(hd_image_path):
                            # 发送到冲印系统（传入order对象用于状态跟踪）
                            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
                            result = printer_client.send_order_to_printer(order, hd_image_path, order_obj=order)
                            
                            # 提交数据库更改（包括发送状态）
                            db.session.commit()
                            
                            if result['success']:
                                print(f"订单 {order.order_number} 高清图片已成功发送到冲印系统")
                                # 发送成功后，更新状态为已发货
                                order.status = 'processing'
                                db.session.commit()
                            else:
                                print(f"订单 {order.order_number} 高清图片发送到冲印系统失败: {result['message']}")
                        else:
                            print(f"订单 {order.order_number} 高清图片不存在: {hd_image_path}")
                            if hasattr(order, 'printer_send_status'):
                                order.printer_send_status = 'sent_failed'
                                order.printer_error_message = f"高清图片文件不存在: {hd_image_path}"
                                db.session.commit()
                    else:
                        print(f"订单 {order.order_number} 没有高清图片，跳过冲印系统发送")
                        if hasattr(order, 'printer_send_status'):
                            order.printer_send_status = 'sent_failed'
                            order.printer_error_message = "订单没有高清图片"
                            db.session.commit()
            except ImportError:
                print("冲印系统模块未找到，跳过冲印系统发送")
            except Exception as e:
                print(f"发送订单到冲印系统时发生错误: {str(e)}")
                if hasattr(order, 'printer_send_status'):
                    order.printer_send_status = 'sent_failed'
                    order.printer_error_message = f"发送异常: {str(e)}"
                    db.session.commit()
        
        # 状态文本映射
        status_text_map = {
            'unpaid': '待上传图片',
            'pending': '待制作',
            'completed': '已完成',
            'shipped': '已发货',
            'hd_ready': '高清放大',
            'manufacturing': '制作中',
            'processing': '处理中'
        }
        
        mapped_status_text = status_text_map.get(status, status_text)
        
        print(f"订单 {order_id} 状态更新为: {status} ({mapped_status_text})")
        
        return jsonify({
            'status': 'success',
            'message': '订单状态更新成功',
            'orderId': order.order_number,
            'status': order.status,
            'statusText': mapped_status_text
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"更新订单状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'更新订单状态失败: {str(e)}'}), 500


@bp.route('/orders/<order_id>/images', methods=['PUT'])
def update_order_images(order_id):
    """更新订单图片 - 支持替换单张图片"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        OrderImage = models['OrderImage']
        app = models.get('app')
        get_media_url = helpers.get('get_media_url')
        import os
        import uuid
        from PIL import Image
        
        data = request.get_json()
        images = data.get('images', [])
        uploaded_images = data.get('uploadedImages', [])
        replace_index = data.get('replaceIndex', -1)  # 要替换的图片索引
        is_replace_mode = data.get('isReplaceMode', False)  # 是否为替换模式
        
        # 查找订单（支持通过order_number查找）
        order = Order.query.filter_by(order_number=order_id).first()
        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404
        
        # 验证订单是否为小程序订单
        if order.source_type != 'miniprogram':
            return jsonify({'status': 'error', 'message': '订单类型不匹配'}), 400
        
        # 🔒 安全检查：只有已支付的订单才能上传图片
        if not order.payment_time:
            return jsonify({
                'status': 'error', 
                'message': '订单未支付，无法上传图片。请先完成支付。',
                'code': 'UNPAID_ORDER'
            }), 403
        
        print(f"图片更新请求: 订单={order_id}, 替换模式={is_replace_mode}, 替换索引={replace_index}")
        
        # 如果是替换模式
        if is_replace_mode and replace_index >= 0:
            # 替换模式：只替换指定索引的图片
            existing_images = OrderImage.query.filter_by(order_id=order.id).order_by(OrderImage.id).all()
            
            if replace_index >= len(existing_images):
                return jsonify({'status': 'error', 'message': '图片索引超出范围'}), 400
            
            # 获取要替换的图片记录
            old_image = existing_images[replace_index]
            
            # 处理新的图片数据
            new_image_path = ''
            processed_images = []
            
            # 优先处理uploadedImages
            if uploaded_images:
                for img_data in uploaded_images:
                    if img_data.get('filename'):
                        new_image_path = img_data['filename']
                        processed_images.append(img_data['filename'])
                        break
                    elif img_data.get('url'):
                        new_image_path = img_data['url']
                        processed_images.append(img_data['url'])
                        break
            elif images:
                new_image_path = images[0]
                processed_images.append(images[0])
            
            if not new_image_path:
                return jsonify({'status': 'error', 'message': '没有提供新图片'}), 400
            
            # 更新图片路径
            old_image.path = new_image_path
            
            # 更新订单的original_image字段（取第一张）
            if replace_index == 0:
                order.original_image = new_image_path
            
            db.session.commit()
            
            print(f"✅ 图片替换成功: 索引{replace_index}, 新路径={new_image_path}")
            
            # 获取所有图片路径返回
            updated_images = OrderImage.query.filter_by(order_id=order.id).order_by(OrderImage.id).all()
            image_urls = [f"{get_media_url()}/original/{img.path}" for img in updated_images]
            
            return jsonify({
                'status': 'success',
                'message': '图片替换成功',
                'images': image_urls,
                'replacedIndex': replace_index,
                'newImageUrl': f"{get_media_url()}/original/{new_image_path}"
            })
        
        # 普通模式：全部替换
        # 删除旧的订单图片
        OrderImage.query.filter_by(order_id=order.id).delete()
        
        # 处理上传的图片
        processed_images = []
        
        # 优先处理uploadedImages（如果有的话）
        if uploaded_images:
            print(f"处理uploadedImages字段中的图片，数量: {len(uploaded_images)}")
            for img_data in uploaded_images:
                if img_data.get('filename'):
                    # 使用已上传的文件名
                    filename = img_data['filename']
                    print(f"保存已上传图片: {filename}")
                    
                    order_image = OrderImage(
                        order_id=order.id,
                        path=filename,
                        is_main=False
                    )
                    db.session.add(order_image)
                    processed_images.append(filename)
                elif img_data.get('url'):
                    # 处理图片URL
                    img_url = img_data['url']
                    print(f"处理图片URL: {img_url}")
                    
                    # 生成本地文件名
                    img_filename = f"mp_{uuid.uuid4().hex[:8]}.jpg"
                    if app:
                        img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
                    else:
                        img_path = os.path.join('uploads', img_filename)
                    
                    # 如果是临时路径，创建一个占位符图片
                    if img_url.startswith('http://tmp/') or img_url.startswith('tmp/'):
                        # 创建占位符图片
                        placeholder_img = Image.new('RGB', (300, 300), color='lightgray')
                        placeholder_img.save(img_path, 'JPEG')
                        print(f"创建占位符图片: {img_path}")
                        
                        # 保存本地路径
                        order_image = OrderImage(
                            order_id=order.id,
                            path=img_filename
                        )
                        db.session.add(order_image)
                        processed_images.append(img_filename)
                    elif img_url.startswith('http'):
                        # 网络图片，创建占位符
                        placeholder_img = Image.new('RGB', (300, 300), color='lightblue')
                        placeholder_img.save(img_path, 'JPEG')
                        print(f"创建网络图片占位符: {img_path}")
                        
                        order_image = OrderImage(
                            order_id=order.id,
                            path=img_filename
                        )
                        db.session.add(order_image)
                        processed_images.append(img_filename)
                    else:
                        # 本地图片
                        order_image = OrderImage(
                            order_id=order.id,
                            path=img_url
                        )
                        db.session.add(order_image)
                        processed_images.append(img_url)
                else:
                    print(f"图片数据格式不正确: {img_data}")
        
        # 处理images字段（兼容直接传入图片路径列表）
        elif images:
            print(f"处理images字段中的图片，数量: {len(images)}")
            for image_url in images:
                # 生成本地文件名
                img_filename = f"mp_{uuid.uuid4().hex[:8]}.jpg"
                if app:
                    img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
                else:
                    img_path = os.path.join('uploads', img_filename)
                
                # 如果是临时路径或者其他格式，创建占位符
                if image_url.startswith('http://tmp/') or image_url.startswith('tmp/'):
                    placeholder_img = Image.new('RGB', (300, 300), color='lightgreen')
                    placeholder_img.save(img_path, 'JPEG')
                    
                    order_image = OrderImage(
                        order_id=order.id,
                        path=img_filename
                    )
                    db.session.add(order_image)
                    processed_images.append(img_filename)
                elif image_url.startswith('http'):
                    placeholder_img = Image.new('RGB', (300, 300), color='lightcoral')
                    placeholder_img.save(img_path, 'JPEG')
                    
                    order_image = OrderImage(
                        order_id=order.id,
                        path=img_filename
                    )
                    db.session.add(order_image)
                    processed_images.append(img_filename)
                else:
                    # 本地图片路径
                    order_image = OrderImage(
                        order_id=order.id,
                        path=image_url
                    )
                    db.session.add(order_image)
                    processed_images.append(image_url)
        
        # 更新订单的original_image字段（兼容旧系统）
        if processed_images:
            order.original_image = processed_images[0]
        
        # 立即制作类型：当用户上传了图片，任务状态自动更新为待制作
        if processed_images and order.order_mode == 'making':
            if order.status in ['paid', '已支付']:
                order.status = 'pending'
                print(f"✅ 立即制作订单 {order.order_number} 已上传图片，状态已更新为待制作")
        
        # 更新订单状态，如果有上传图片且当前状态为未上传图片状态，则改为待制作
        # 注意：这里只处理已支付订单的状态更新（支付检查已在前面完成）
        if processed_images and order.status in ['unpaid']:
            # 再次确认订单已支付（双重检查）
            if order.payment_time:
                order.status = 'pending'
            else:
                # 如果订单未支付，不应该更新状态
                print(f"⚠️ 警告：订单 {order_id} 未支付，但尝试更新状态为pending")
                db.session.rollback()
                return jsonify({
                    'status': 'error', 
                    'message': '订单未支付，无法更新订单状态。请先完成支付。',
                    'code': 'UNPAID_ORDER'
                }), 403
        
        db.session.commit()
        
        # 构建返回的图片URL列表
        image_urls = []
        for img_path in processed_images:
            # 构建完整的图片URL
            image_url = f"{get_media_url()}/original/{img_path}"
            image_urls.append(image_url)
        
        # 根据订单类型判断是否进入自动化流程
        # 立即拍摄（shooting）：收到上传的原图就进入AI制作流程
        # 立即制作（making）：收到上传的图片也不进行任何处理
        if order.order_mode == 'shooting':
            # 立即拍摄：进入自动化流程
            try:
                from app.services.image_processing_service import process_order_images
                
                # 获取风格分类ID（从订单中获取）
                style_category_id = order.style_category_id if hasattr(order, 'style_category_id') else None
                style_image_id = order.style_image_id if hasattr(order, 'style_image_id') else None
                
                # 在后台线程中处理图片（需要应用上下文）
                # 使用从models获取的app实例
                app_instance = app if app else None
                if not app_instance:
                    # 如果models中没有app，尝试从test_server获取
                    import sys
                    if 'test_server' in sys.modules:
                        test_server_module = sys.modules['test_server']
                        if hasattr(test_server_module, 'app'):
                            app_instance = test_server_module.app
                
                if app_instance:
                    def process_images_async():
                        try:
                            # 使用应用实例创建应用上下文
                            with app_instance.app_context():
                                process_order_images(
                                    order_id=order.id,
                                    order_number=order.order_number,
                                    style_category_id=style_category_id,
                                    style_image_id=style_image_id
                                )
                        except Exception as e:
                            print(f"后台处理图片失败: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    
                    processing_thread = threading.Thread(target=process_images_async)
                    processing_thread.daemon = True
                    processing_thread.start()
                    print(f"✅ 立即拍摄订单，已启动后台图片处理流程（美图API + AI工作流）")
                else:
                    print(f"⚠️ 无法获取应用实例，跳过后台图片处理")
            except Exception as e:
                print(f"⚠️  启动图片处理流程失败: {str(e)}")
        elif order.order_mode == 'making':
            # 立即制作：不进行任何自动化处理，等待人工处理
            print(f"ℹ️ 立即制作订单，跳过自动化处理流程，等待人工处理")
        else:
            # 未设置订单类型：默认进入自动化流程（兼容旧订单）
            print(f"⚠️ 订单类型未设置，默认进入自动化流程")
            try:
                from app.services.image_processing_service import process_order_images
                
                style_category_id = order.style_category_id if hasattr(order, 'style_category_id') else None
                style_image_id = order.style_image_id if hasattr(order, 'style_image_id') else None
                
                # 在后台线程中处理图片（需要应用上下文）
                # 使用从models获取的app实例
                app_instance = app if app else None
                if not app_instance:
                    # 如果models中没有app，尝试从test_server获取
                    import sys
                    if 'test_server' in sys.modules:
                        test_server_module = sys.modules['test_server']
                        if hasattr(test_server_module, 'app'):
                            app_instance = test_server_module.app
                
                if app_instance:
                    def process_images_async():
                        try:
                            # 使用应用实例创建应用上下文
                            with app_instance.app_context():
                                process_order_images(
                                    order_id=order.id,
                                    order_number=order.order_number,
                                    style_category_id=style_category_id,
                                    style_image_id=style_image_id
                                )
                        except Exception as e:
                            print(f"后台处理图片失败: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    
                    processing_thread = threading.Thread(target=process_images_async)
                    processing_thread.daemon = True
                    processing_thread.start()
                    print(f"✅ 已启动后台图片处理流程（美图API + AI工作流）")
                else:
                    print(f"⚠️ 无法获取应用实例，跳过后台图片处理")
            except Exception as e:
                print(f"⚠️  启动图片处理流程失败: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': '订单图片更新成功',
            'images': image_urls,
            'imageCount': len(processed_images)
        })
        
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"更新订单图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'更新订单图片失败: {str(e)}'}), 500


@bp.route('/orders/<order_id>/images/delete', methods=['DELETE'])
def delete_order_image(order_id):
    """删除订单中的单张图片"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        Order = models['Order']
        OrderImage = models['OrderImage']
        get_media_url = helpers.get('get_media_url')
        
        data = request.get_json()
        image_url = data.get('imageUrl', '')
        image_index = data.get('imageIndex', -1)
        
        print(f"删除图片请求: 订单={order_id}, 索引={image_index}, URL={image_url}")
        
        # 查找订单
        order = Order.query.filter_by(order_number=order_id).first()
        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404
        
        # 验证订单是否为小程序订单
        if order.source_type != 'miniprogram':
            return jsonify({'status': 'error', 'message': '订单类型不匹配'}), 400
        
        # 获取订单的所有图片
        existing_images = OrderImage.query.filter_by(order_id=order.id).order_by(OrderImage.id).all()
        
        if not existing_images:
            return jsonify({'status': 'error', 'message': '订单中没有图片'}), 400
        
        deleted_image = None
        
        if image_index >= 0 and image_index < len(existing_images):
            # 通过索引删除
            deleted_image = existing_images[image_index]
            db.session.delete(deleted_image)
            
            # 更新订单的original_image字段（如果删除的是第一张图片）
            if image_index == 0:
                remaining_images = OrderImage.query.filter_by(order_id=order.id).order_by(OrderImage.id).all()
                if remaining_images:
                    order.original_image = remaining_images[0].path
                else:
                    order.original_image = ''
                    
                    # 如果删除最后一张图片，将状态改为unpaid
                    if len(remaining_images) == 0:
                        order.status = 'unpaid'
            
            db.session.commit()
            
            print(f"✅ 图片删除成功: 索引{image_index}, 图片ID={deleted_image.id}")
        
        elif image_url:
            # 通过URL删除（从URL中提取文件名）
            filename = image_url.split('/')[-1] if image_url else ''
            
            # 在现有图片中查找匹配的图片
            for img in existing_images:
                if img.path == filename or image_url.endswith(img.path):
                    deleted_image = img
                    db.session.delete(img)
                    
                    # 更新订单的original_image字段（如果删除的是第一张图片）
                    if img.id == existing_images[0].id:
                        remaining_images = OrderImage.query.filter_by(order_id=order.id).order_by(OrderImage.id).all()
                        if remaining_images:
                            order.original_image = remaining_images[0].path
                        else:
                            order.original_image = ''
                            
                            # 如果删除最后一张图片，将状态改为unpaid
                            if len(remaining_images) == 0:
                                order.status = 'unpaid'
                    
                    db.session.commit()
                    print(f"✅ 图片删除成功: 图片ID={img.id}, 路径={img.path}")
                    break
            
            if not deleted_image:
                return jsonify({'status': 'error', 'message': '图片未找到'}), 404
        
        else:
            return jsonify({'status': 'error', 'message': '缺少图片信息'}), 400
        
        # 返回更新后的图片列表
        remaining_images = OrderImage.query.filter_by(order_id=order.id).order_by(OrderImage.id).all()
        remaining_urls = [f"{get_media_url()}/original/{img.path}" for img in remaining_images]
        
        return jsonify({
            'success': True,
            'message': '图片删除成功',
            'remainingImages': remaining_urls,
            'deletedIndex': image_index if image_index >= 0 else None,
            'remainingCount': len(remaining_images)
        })
            
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        print(f"删除图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'删除图片失败: {str(e)}'}), 500
