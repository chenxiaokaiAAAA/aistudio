# -*- coding: utf-8 -*-
"""
权限检查工具函数
"""

import logging

logger = logging.getLogger(__name__)
import json

from flask_login import current_user

# 页面路径与权限ID的映射
PAGE_PATH_TO_PERMISSION = {
    "/admin/dashboard": "dashboard",
    "/admin/orders": "orders",
    "/admin/order/": "orders",  # 订单详情页
    "/admin/shop/orders": "shop_orders",
    "/admin/photo-selection": "photo_selection",
    "/franchisee/admin/accounts": "franchisee",
    "/franchisee/admin": "franchisee",
    "/admin/franchisee": "franchisee",
    "/admin/sizes": "products",
    "/admin/shop/products": "shop_products",
    "/admin/styles": "styles",
    "/playground": "playground",
    "/admin/ai/tasks": "ai_tasks",
    "/admin/meitu/tasks": "meitu_tasks",
    "/admin/system-config": "system_config",
    "/admin/meitu/config": "meitu_config",
    "/admin/ai-provider/config": "ai_provider_config",
    "/admin/image-cleanup": "image_cleanup",
    "/admin/polling-config": "polling_config",
    "/admin/print-config": "print_config",
    "/admin/printer": "printer",
    "/admin/coupons": "coupons",
    "/admin/promotion": "promotion",
    "/admin/homepage": "homepage",
    "/admin/profile": "profile",
}


def get_user_page_permissions(user):
    """
    获取用户的页面权限列表
    返回: list of permission IDs, 如果是admin或没有配置则返回None（表示拥有所有权限）
    """
    if not user:
        return None

    # 管理员拥有所有权限
    if user.role == "admin":
        return None

    # 操作员需要检查权限配置
    if user.role == "operator":
        page_permissions = getattr(user, "page_permissions", None)
        if page_permissions:
            try:
                return json.loads(page_permissions)
            except Exception:
                return []
        return []

    # 其他角色默认无权限
    return []


def has_page_permission(user, path):
    """
    检查用户是否有权限访问指定路径
    返回: True/False
    """
    if not user:
        return False

    # 管理员拥有所有权限
    if user.role == "admin":
        return True

    # 操作员需要检查权限
    if user.role == "operator":
        permissions = get_user_page_permissions(user)
        if permissions is None:  # admin角色
            return True

        # 根据路径查找对应的权限ID
        permission_id = None
        for page_path, perm_id in PAGE_PATH_TO_PERMISSION.items():
            if path.startswith(page_path) or path == page_path:
                permission_id = perm_id
                break

        # 如果找不到对应的权限ID，默认允许访问（向后兼容）
        if permission_id is None:
            return True

        # 检查是否在权限列表中
        return permission_id in permissions

    # 其他角色默认无权限
    return False


def get_allowed_pages(user):
    """
    获取用户允许访问的所有页面路径
    返回: list of paths
    """
    if not user:
        return []

    # 管理员拥有所有权限
    if user.role == "admin":
        return list(PAGE_PATH_TO_PERMISSION.keys())

    # 操作员需要检查权限配置
    if user.role == "operator":
        permissions = get_user_page_permissions(user)
        if permissions is None:  # admin角色
            return list(PAGE_PATH_TO_PERMISSION.keys())

        # 根据权限ID查找对应的路径
        allowed_paths = []
        for path, perm_id in PAGE_PATH_TO_PERMISSION.items():
            if perm_id in permissions:
                allowed_paths.append(path)

        # 个人中心始终允许访问
        if "/admin/profile" not in allowed_paths:
            allowed_paths.append("/admin/profile")

        return allowed_paths

    # 其他角色只有个人中心
    return ["/admin/profile"]
