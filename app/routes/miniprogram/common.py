import logging

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
小程序API公共函数模块
提供数据库模型和工具函数的延迟导入
"""


def get_models():
    """获取数据库模型和配置（延迟导入）"""
    import sys

    if "test_server" not in sys.modules:
        return None
    test_server_module = sys.modules["test_server"]
    models = {
        "db": test_server_module.db,
        "Order": test_server_module.Order,
        "OrderImage": test_server_module.OrderImage,
        "StyleCategory": test_server_module.StyleCategory,
        "StyleSubcategory": getattr(test_server_module, "StyleSubcategory", None),
        "StyleImage": test_server_module.StyleImage,
        "ProductCategory": getattr(test_server_module, "ProductCategory", None),
        "ProductSubcategory": getattr(test_server_module, "ProductSubcategory", None),
        "Product": test_server_module.Product,
        "ProductSize": test_server_module.ProductSize,
        "ProductImage": test_server_module.ProductImage,
        "ProductStyleCategory": test_server_module.ProductStyleCategory,
        "ProductCustomField": test_server_module.ProductCustomField,
        "ProductSizePetOption": test_server_module.ProductSizePetOption,
        "HomepageBanner": test_server_module.HomepageBanner,
        "HomepageCategoryNav": getattr(test_server_module, "HomepageCategoryNav", None),
        "HomepageProductSection": getattr(test_server_module, "HomepageProductSection", None),
        "HomepageActivityBanner": getattr(test_server_module, "HomepageActivityBanner", None),
        "PromotionUser": test_server_module.PromotionUser,
        "Commission": test_server_module.Commission,
        "app": test_server_module.app if hasattr(test_server_module, "app") else None,
    }

    # 添加商城相关模型（如果存在）
    try:
        if hasattr(test_server_module, "ShopProduct"):
            models["ShopProduct"] = test_server_module.ShopProduct
        if hasattr(test_server_module, "ShopProductImage"):
            models["ShopProductImage"] = test_server_module.ShopProductImage
        if hasattr(test_server_module, "ShopProductSize"):
            models["ShopProductSize"] = test_server_module.ShopProductSize
        if hasattr(test_server_module, "ShopOrder"):
            models["ShopOrder"] = test_server_module.ShopOrder
    except Exception as e:
        logger.info(f"警告: 加载商城模型时出错: {e}")
        import traceback

        traceback.print_exc()

    # 添加其他模型（如果存在）
    try:
        if hasattr(test_server_module, "AIConfig"):
            models["AIConfig"] = test_server_module.AIConfig
        if hasattr(test_server_module, "Coupon"):
            models["Coupon"] = test_server_module.Coupon
        if hasattr(test_server_module, "UserCoupon"):
            models["UserCoupon"] = test_server_module.UserCoupon
        if hasattr(test_server_module, "StaffUser"):
            models["StaffUser"] = test_server_module.StaffUser
        if hasattr(test_server_module, "GrouponPackage"):
            models["GrouponPackage"] = test_server_module.GrouponPackage
    except Exception as e:
        logger.info(f"警告: 加载其他模型时出错: {e}")

    return models


def get_helper_functions():
    """获取工具函数（延迟导入）"""
    import sys

    if "test_server" not in sys.modules:
        return None
    test_server_module = sys.modules["test_server"]
    return {
        "get_base_url": (
            test_server_module.get_base_url if hasattr(test_server_module, "get_base_url") else None
        ),
        "get_media_url": (
            test_server_module.get_media_url
            if hasattr(test_server_module, "get_media_url")
            else None
        ),
        "get_access_token": (
            test_server_module.get_access_token
            if hasattr(test_server_module, "get_access_token")
            else None
        ),
        "send_order_completion_notification_auto": (
            test_server_module.send_order_completion_notification_auto
            if hasattr(test_server_module, "send_order_completion_notification_auto")
            else None
        ),
    }
