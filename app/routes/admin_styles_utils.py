# -*- coding: utf-8 -*-
"""
风格管理工具函数模块
提供公共辅助函数
"""

import logging

logger = logging.getLogger(__name__)
from flask import current_app
from flask_login import current_user


def _is_from_playground(request):
    """检测请求是否来自Playground"""
    referer = request.headers.get("Referer", "")
    return (
        "/playground" in referer
        or request.form.get("from_playground") == "true"
        or request.get_json(silent=True)
        and request.get_json(silent=True).get("from_playground") is True
    )


def _get_test_order_info(request):
    """获取测试订单信息（根据来源返回不同的订单号和用户名）"""
    is_playground = _is_from_playground(request)
    import random
    import time

    if is_playground:
        order_number = f"PLAY_{int(time.time() * 1000)}{random.randint(1000, 9999)}"
        customer_name = (
            current_user.username
            if current_user and current_user.is_authenticated
            else "PLAYGROUND"
        )
        source_type = "playground_test"
    else:
        order_number = f"TEST_{int(time.time() * 1000)}{random.randint(1000, 9999)}"
        customer_name = "测试用户"
        source_type = "admin_test"

    return order_number, customer_name, source_type
