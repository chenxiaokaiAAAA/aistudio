# -*- coding: utf-8 -*-
"""
小程序数字分身相关路由
"""
from flask import Blueprint, request, jsonify
from app.routes.miniprogram.common import get_models, get_helper_functions
from datetime import datetime

# 创建数字分身相关的子蓝图
bp = Blueprint('digital_avatar', __name__)


@bp.route('/digital-avatar/list', methods=['GET'])
def get_digital_avatar_list():
    """获取用户的数字分身列表（美图API处理后的AI写真照片）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        OrderImage = models['OrderImage']
        get_base_url = helpers['get_base_url']
        
        # 获取查询参数
        userId = request.args.get('userId')
        phone = request.args.get('phone')
        
        if not phone:
            return jsonify({'status': 'error', 'message': '缺少手机号参数'}), 400
        
        # 查询AI写真订单（product_name包含"AI写真"或"写真"）
        # 并且订单状态为已完成或制作中
        orders = Order.query.filter(
            Order.customer_phone.like(f'%{phone}%'),
            Order.external_platform == 'miniprogram',
            Order.product_name.like('%AI写真%')
        ).order_by(Order.created_at.desc()).all()
        
        avatar_list = []
        base_url = get_base_url()
        
        for order in orders:
            # 查找订单中所有图片
            all_images = OrderImage.query.filter_by(order_id=order.id).all()
            retouched_images = []
            
            # 查找美图API处理后的图片
            # 方法1: 检查是否有image_type字段且为'retouched'
            for img in all_images:
                if hasattr(img, 'image_type') and img.image_type == 'retouched':
                    retouched_images.append(img)
                    continue
                
                # 方法2: 检查路径中是否包含meitu_results（美图API结果目录）
                if 'meitu_results' in img.path:
                    retouched_images.append(img)
                    continue
                
                # 方法3: 检查路径中是否包含retouched关键字
                if 'retouched' in img.path.lower():
                    retouched_images.append(img)
                    continue
            
            # 如果找到了美图API处理后的图片
            if retouched_images:
                for img in retouched_images:
                    # 构建完整的图片URL
                    if img.path.startswith('/'):
                        image_url = f"{base_url}{img.path}"
                    elif img.path.startswith('http'):
                        image_url = img.path
                    elif 'meitu_results' in img.path:
                        # 美图API结果图片在uploads/meitu_results目录下
                        image_url = f"{base_url}/media/original/{img.path}"
                    else:
                        image_url = f"{base_url}/media/original/{img.path}"
                    
                    avatar_list.append({
                        'id': img.id,
                        'order_id': order.id,
                        'order_name': order.product_name or 'AI写真',
                        'order_number': order.order_number,
                        'image_url': image_url,
                        'create_time': order.created_at.strftime('%Y-%m-%d') if order.created_at else ''
                    })
        
        return jsonify({
            'status': 'success',
            'data': avatar_list
        })
        
    except Exception as e:
        print(f"获取数字分身列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取数字分身列表失败: {str(e)}'}), 500
