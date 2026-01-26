# -*- coding: utf-8 -*-
"""
小程序API路由模块
统一注册所有子模块的蓝图
"""
from flask import Blueprint, jsonify

# 创建主蓝图
miniprogram_bp = Blueprint('miniprogram', __name__, url_prefix='/api/miniprogram')

# 导入并注册所有子模块
from . import orders, media, catalog, works, promotion, shop, digital_avatar, share_reward, groupon, third_party_groupon

# 注册子蓝图到主蓝图
miniprogram_bp.register_blueprint(orders.bp)
miniprogram_bp.register_blueprint(media.bp)
miniprogram_bp.register_blueprint(catalog.bp)
miniprogram_bp.register_blueprint(works.bp)
miniprogram_bp.register_blueprint(promotion.bp)
miniprogram_bp.register_blueprint(shop.bp)
miniprogram_bp.register_blueprint(digital_avatar.bp)
miniprogram_bp.register_blueprint(share_reward.bp)
miniprogram_bp.register_blueprint(groupon.bp)
miniprogram_bp.register_blueprint(third_party_groupon.bp)

# 注册API信息路由（在主蓝图上）
@miniprogram_bp.route('', methods=['GET'])
def miniprogram_api_info():
    """小程序API信息"""
    return jsonify({
        'status': 'success',
        'message': '小程序API服务正常',
        'version': '1.0.0',
        'endpoints': {
            'get_styles': '/api/miniprogram/styles',
            'submit_order': '/api/miniprogram/orders',
            'get_orders': '/api/miniprogram/orders',
            'upload_work': '/api/miniprogram/orders/<order_id>/upload',
            'get_works': '/api/miniprogram/works',
            'get_promotion_code': '/api/miniprogram/promotion-code'
        }
    })
