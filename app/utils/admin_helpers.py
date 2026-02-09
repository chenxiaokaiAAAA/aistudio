# -*- coding: utf-8 -*-
"""
管理后台辅助函数模块
统一提供 get_models() 等公共函数，避免代码重复
"""

import logging

logger = logging.getLogger(__name__)
import sys

from flask import current_app


def get_models(model_names=None):
    """
    统一的数据库模型获取函数（延迟导入）

    Args:
        model_names: 需要获取的模型名称列表，如果为None则返回所有常用模型
                     例如: ['Order', 'Product', 'StyleCategory']

    Returns:
        dict: 包含数据库模型和db对象的字典，如果未初始化则返回None
    """
    try:
        if "test_server" not in sys.modules:
            return None

        test_server_module = sys.modules["test_server"]

        # 定义所有可用的模型
        all_models = {
            "db": test_server_module.db,
            "User": test_server_module.User,
            "Order": getattr(test_server_module, "Order", None),
            "OrderImage": getattr(test_server_module, "OrderImage", None),
            "FranchiseeAccount": getattr(test_server_module, "FranchiseeAccount", None),
            "FranchiseeRecharge": getattr(test_server_module, "FranchiseeRecharge", None),
            "StyleCategory": getattr(test_server_module, "StyleCategory", None),
            "StyleSubcategory": getattr(test_server_module, "StyleSubcategory", None),
            "StyleImage": getattr(test_server_module, "StyleImage", None),
            "Product": getattr(test_server_module, "Product", None),
            "ProductSize": getattr(test_server_module, "ProductSize", None),
            "ProductImage": getattr(test_server_module, "ProductImage", None),
            "ProductSizePetOption": getattr(test_server_module, "ProductSizePetOption", None),
            "ProductStyleCategory": getattr(test_server_module, "ProductStyleCategory", None),
            "ProductCustomField": getattr(test_server_module, "ProductCustomField", None),
            "ProductCategory": getattr(test_server_module, "ProductCategory", None),
            "ProductSubcategory": getattr(test_server_module, "ProductSubcategory", None),
            "HomepageBanner": getattr(test_server_module, "HomepageBanner", None),
            "WorksGallery": getattr(test_server_module, "WorksGallery", None),
            "HomepageConfig": getattr(test_server_module, "HomepageConfig", None),
            "HomepageCategoryNav": getattr(test_server_module, "HomepageCategoryNav", None),
            "HomepageProductSection": getattr(test_server_module, "HomepageProductSection", None),
            "AIConfig": getattr(test_server_module, "AIConfig", None),
            "APITemplate": getattr(test_server_module, "APITemplate", None),
            "APIProviderConfig": getattr(test_server_module, "APIProviderConfig", None),
            "AITask": getattr(test_server_module, "AITask", None),
            "ShopProduct": getattr(test_server_module, "ShopProduct", None),
            "ShopProductImage": getattr(test_server_module, "ShopProductImage", None),
            "ShopProductSize": getattr(test_server_module, "ShopProductSize", None),
            "ShopOrder": getattr(test_server_module, "ShopOrder", None),
            "SelectionOrder": getattr(test_server_module, "SelectionOrder", None),
            "PrintSizeConfig": getattr(test_server_module, "PrintSizeConfig", None),
            "SelfieMachine": getattr(test_server_module, "SelfieMachine", None),
            "StaffUser": getattr(test_server_module, "StaffUser", None),
            "PromotionUser": getattr(test_server_module, "PromotionUser", None),
            "PromotionTrack": getattr(test_server_module, "PromotionTrack", None),
            "Commission": getattr(test_server_module, "Commission", None),
            "Withdrawal": getattr(test_server_module, "Withdrawal", None),
            "UserVisit": getattr(test_server_module, "UserVisit", None),
            "Coupon": getattr(test_server_module, "Coupon", None),
            "UserCoupon": getattr(test_server_module, "UserCoupon", None),
            "ShareRecord": getattr(test_server_module, "ShareRecord", None),
            "GrouponPackage": getattr(test_server_module, "GrouponPackage", None),
            "MeituAPIConfig": getattr(test_server_module, "MeituAPIConfig", None),
            "MeituAPICallLog": getattr(test_server_module, "MeituAPICallLog", None),
            "MeituAPIPreset": getattr(test_server_module, "MeituAPIPreset", None),
            "MeituTask": getattr(test_server_module, "MeituTask", None),
            "PollingConfig": getattr(test_server_module, "PollingConfig", None),
            "MockupTemplate": getattr(test_server_module, "MockupTemplate", None),
            "MockupTemplateProduct": getattr(test_server_module, "MockupTemplateProduct", None),
            "OperationLog": getattr(test_server_module, "OperationLog", None),
        }

        # 添加配置和工具函数
        all_models["app"] = getattr(test_server_module, "app", current_app)
        all_models["get_base_url"] = getattr(test_server_module, "get_base_url", None)
        all_models["WECHAT_PAY_CONFIG"] = getattr(test_server_module, "WECHAT_PAY_CONFIG", None)
        all_models["get_user_openid_service"] = getattr(
            test_server_module, "get_user_openid_service", None
        )
        all_models["PRINTER_SYSTEM_AVAILABLE"] = getattr(
            test_server_module, "PRINTER_SYSTEM_AVAILABLE", False
        )
        all_models["PRINTER_SYSTEM_CONFIG"] = getattr(
            test_server_module, "PRINTER_SYSTEM_CONFIG", {}
        )
        all_models["PrinterSystemClient"] = getattr(test_server_module, "PrinterSystemClient", None)
        all_models["calculate_visit_frequency"] = getattr(
            test_server_module, "calculate_visit_frequency", None
        )

        # 如果指定了模型名称，只返回需要的模型
        if model_names:
            result = {}
            for name in model_names:
                if name in all_models:
                    result[name] = all_models.get(name)
                else:
                    logger.warning(f"模型 {name} 不在可用模型列表中")
            return result

        # 否则返回所有模型
        return all_models

    except Exception as e:
        logger.warning(f"获取数据库模型失败: {e}")
        return None


def get_style_code_helpers():
    """
    获取风格代码处理辅助函数

    Returns:
        dict: 包含风格代码处理函数的字典，如果导入失败则返回None
    """
    try:
        from app.models import _build_style_code, _ensure_unique_style_code, _sanitize_style_code

        return {
            "_sanitize_style_code": _sanitize_style_code,
            "_build_style_code": _build_style_code,
            "_ensure_unique_style_code": _ensure_unique_style_code,
        }
    except ImportError as e:
        logger.warning("导入风格代码辅助函数失败: {e}")
        return None
