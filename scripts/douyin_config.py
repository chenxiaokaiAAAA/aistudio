#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音开放平台配置文件
"""

# 抖音开放平台配置
DOUYIN_OPEN_CONFIG = {
    # 这些信息需要从抖音开放平台获取
    'app_id': 'your_app_id',                    # 应用ID
    'app_secret': 'your_app_secret',            # 应用密钥
    'shop_id': 'your_shop_id',                  # 店铺ID
    'base_url': 'https://open.douyin.com',      # API基础URL
    'webhook_secret': 'your_webhook_secret',    # Webhook签名密钥
    
    # API版本和权限
    'api_version': 'v1',
    'scopes': [
        'shop.order.read',      # 读取订单权限
        'shop.order.write',     # 写入订单权限
        'shop.product.read',    # 读取商品权限
    ],
    
    # 请求配置
    'timeout': 30,
    'retry_times': 3,
    'retry_delay': 1,
}

# 抖音小店API端点
DOUYIN_API_ENDPOINTS = {
    'access_token': '/oauth/access_token/',           # 获取访问令牌
    'refresh_token': '/oauth/refresh_token/',        # 刷新访问令牌
    'order_list': '/api/shop/order/list/',           # 订单列表
    'order_detail': '/api/shop/order/detail/',       # 订单详情
    'product_list': '/api/shop/product/list/',       # 商品列表
    'shop_info': '/api/shop/info/',                 # 店铺信息
    'webhook_register': '/api/webhook/register/',    # 注册Webhook
}

# 订单状态映射
DOUYIN_ORDER_STATUS_MAP = {
    'UNPAID': 'pending',        # 未付款
    'PAID': 'processing',       # 已付款
    'SHIPPED': 'shipped',       # 已发货
    'COMPLETED': 'completed',   # 已完成
    'CANCELLED': 'cancelled',   # 已取消
    'REFUNDING': 'cancelled',   # 退款中
    'REFUNDED': 'cancelled',    # 已退款
}

# Webhook事件类型
DOUYIN_WEBHOOK_EVENTS = {
    'order.created': '订单创建',
    'order.paid': '订单支付',
    'order.shipped': '订单发货',
    'order.completed': '订单完成',
    'order.cancelled': '订单取消',
    'order.refunded': '订单退款',
}

# 错误码映射
DOUYIN_ERROR_CODES = {
    40001: '参数错误',
    40002: '签名错误',
    40003: '权限不足',
    40004: '请求频率超限',
    40005: '应用未授权',
    40006: '店铺不存在',
    40007: '订单不存在',
    40008: '商品不存在',
    50001: '服务器内部错误',
    50002: '服务暂时不可用',
}

def get_config():
    """获取配置"""
    return DOUYIN_OPEN_CONFIG

def get_api_endpoint(endpoint_name):
    """获取API端点"""
    return DOUYIN_API_ENDPOINTS.get(endpoint_name, '')

def map_order_status(douyin_status):
    """映射订单状态"""
    return DOUYIN_ORDER_STATUS_MAP.get(douyin_status, 'pending')

def get_error_message(error_code):
    """获取错误信息"""
    return DOUYIN_ERROR_CODES.get(error_code, '未知错误')

if __name__ == "__main__":
    print("抖音开放平台配置文件已准备就绪")
    print("配置项:")
    for key, value in DOUYIN_OPEN_CONFIG.items():
        if 'secret' in key.lower() or 'key' in key.lower():
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")




