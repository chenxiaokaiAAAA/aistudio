# -*- coding: utf-8 -*-
"""
加盟商路由公共函数模块
提供数据库模型和工具函数的延迟导入
"""
import sys


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'FranchiseeAccount': test_server_module.FranchiseeAccount,
        'FranchiseeRecharge': test_server_module.FranchiseeRecharge,
        'Order': test_server_module.Order,
        'User': test_server_module.User,
        'OrderImage': test_server_module.OrderImage,
        'Product': test_server_module.Product,
        'ProductSize': test_server_module.ProductSize,
        'ProductSizePetOption': test_server_module.ProductSizePetOption,
        'StyleCategory': test_server_module.StyleCategory,
        'StyleImage': test_server_module.StyleImage,
        'ProductStyleCategory': test_server_module.ProductStyleCategory,
        'ProductCustomField': test_server_module.ProductCustomField,
        'SelfieMachine': test_server_module.SelfieMachine,
        'StaffUser': test_server_module.StaffUser if hasattr(test_server_module, 'StaffUser') else None,
        'app': test_server_module.app if hasattr(test_server_module, 'app') else None,
        'allowed_file': test_server_module.allowed_file if hasattr(test_server_module, 'allowed_file') else None
    }


def get_wechat_notification():
    """获取微信通知模块（延迟导入）"""
    try:
        from wechat_notification import send_order_notification as wechat_notify
        return wechat_notify, True
    except ImportError:
        return None, False
