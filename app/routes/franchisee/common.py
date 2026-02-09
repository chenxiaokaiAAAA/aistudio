# -*- coding: utf-8 -*-
"""
加盟商路由公共函数模块
提供数据库模型和工具函数的延迟导入
"""

import logging

logger = logging.getLogger(__name__)

# 统一导入公共函数
from app.utils.admin_helpers import get_models


def get_wechat_notification():
    """获取微信通知模块（延迟导入）"""
    try:
        from wechat_notification import send_order_notification as wechat_notify

        return wechat_notify, True
    except ImportError:
        return None, False
