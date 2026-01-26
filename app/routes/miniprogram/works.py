# -*- coding: utf-8 -*-
"""
小程序作品路由
"""
from flask import Blueprint, request, jsonify
from app.routes.miniprogram.common import get_models, get_helper_functions
from datetime import datetime

# 创建作品相关的子蓝图
bp = Blueprint('works', __name__)


@bp.route('/works', methods=['GET'])
def miniprogram_get_works():
    """小程序获取用户作品 - 支持openid和phone查询（临时兼容）"""
    try:
        models = get_models()
        helpers = get_helper_functions()
        if not models or not helpers:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        get_media_url = helpers.get('get_media_url')
        
        openid = request.args.get('openid')
        phone = request.args.get('phone')  # 临时支持手机号查询
        
        orders = []
        
        # 优先使用openid查询
        if openid:
            # 验证openid格式（基本格式检查）
            if len(openid) < 10 or not openid.replace('_', '').replace('-', '').isalnum():
                return jsonify({'status': 'error', 'message': 'openid格式不正确'}), 400
            
            # 只按openid查询，确保用户只能看到自己的作品
            orders = Order.query.filter(
                Order.openid == openid,
                Order.source_type == 'miniprogram',
                Order.final_image.isnot(None)
            ).order_by(Order.created_at.desc()).all()
            
            print(f"用户 {openid} 查询到 {len(orders)} 个作品")
            
            # 记录查询日志（用于安全审计）
            print(f"作品查询日志: openid={openid}, 结果数量={len(orders)}, 时间={datetime.now()}")
        
        # 临时支持手机号查询（兼容旧版本）
        elif phone:
            # 验证手机号格式
            if not phone.isdigit() or len(phone) != 11:
                return jsonify({'status': 'error', 'message': '手机号格式不正确'}), 400
            
            # 按手机号查询作品
            orders = Order.query.filter(
                Order.customer_phone == phone,
                Order.source_type == 'miniprogram',
                Order.final_image.isnot(None)
            ).order_by(Order.created_at.desc()).all()
            
            print(f"手机号 {phone} 查询到 {len(orders)} 个作品")
            
            # 记录查询日志（用于安全审计）
            print(f"作品查询日志: phone={phone}, 结果数量={len(orders)}, 时间={datetime.now()}")
        
        # 如果都没有提供，返回错误
        if not openid and not phone:
            return jsonify({'status': 'error', 'message': '缺少openid或phone参数，无法查询作品'}), 400
        
        print(f"查询到 {len(orders)} 个作品订单")
        for order in orders:
            print(f"订单 {order.order_number}: 状态={order.status}, 图片={order.final_image}")
        
        works = []
        for order in orders:
            # 根据订单状态决定显示水印还是无水印图片
            if order.status in ['manufacturing', 'completed', 'shipped', 'delivered']:
                # 已确认制作，显示无水印图片
                final_image_url = f'{get_media_url()}/final/clean_{order.final_image}'
            else:
                # 未确认制作，显示有水印图片
                final_image_url = f'{get_media_url()}/final/{order.final_image}'
            
            works.append({
                'id': order.id,
                'orderId': order.order_number,
                'styleName': order.external_platform,
                'productName': order.size,
                'finalImage': final_image_url,
                'status': order.status,  # 添加状态字段
                'completeTime': order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else None,
                'createTime': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'status': 'success',
            'works': works
        })
        
    except Exception as e:
        print(f"获取作品失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取作品失败: {str(e)}'}), 500
