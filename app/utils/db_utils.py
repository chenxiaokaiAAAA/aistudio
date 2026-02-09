# -*- coding: utf-8 -*-
"""
数据库工具函数
提供统一的数据库模型获取接口
"""

import logging

logger = logging.getLogger(__name__)
import sys


def get_models():
    """获取数据库模型（延迟导入）"""
    if "test_server" not in sys.modules:
        return None
    test_server_module = sys.modules["test_server"]
    return {
        "db": test_server_module.db,
        "User": test_server_module.User,
        "Order": test_server_module.Order,
        "OrderImage": test_server_module.OrderImage,
        "FranchiseeAccount": test_server_module.FranchiseeAccount,
        "StyleCategory": test_server_module.StyleCategory,
        "StyleImage": test_server_module.StyleImage,
        "Product": test_server_module.Product,
        "ProductSize": test_server_module.ProductSize,
        "ProductImage": test_server_module.ProductImage,
        "ProductSizePetOption": test_server_module.ProductSizePetOption,
        "ProductStyleCategory": test_server_module.ProductStyleCategory,
        "ProductCustomField": test_server_module.ProductCustomField,
        "HomepageBanner": test_server_module.HomepageBanner,
        "WorksGallery": test_server_module.WorksGallery,
        "HomepageConfig": test_server_module.HomepageConfig,
        "AIConfig": test_server_module.AIConfig,
        "AITask": getattr(test_server_module, "AITask", None),
        "MeituAPICallLog": getattr(test_server_module, "MeituAPICallLog", None),
        "APITemplate": getattr(test_server_module, "APITemplate", None),
        "APIProviderConfig": getattr(test_server_module, "APIProviderConfig", None),
        "UserAccessLog": getattr(test_server_module, "UserAccessLog", None),
    }
