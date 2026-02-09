# -*- coding: utf-8 -*-
"""
选片模块工具函数
"""

import logging

logger = logging.getLogger(__name__)
import uuid
from datetime import datetime, timedelta

# 临时token存储（实际生产环境建议使用Redis）
# 注意：这些变量需要在模块级别共享，所以放在这里
_selection_tokens = {}
# 短token到完整token的映射
_short_token_map = {}

# 导出给其他模块使用
__all__ = ["_selection_tokens", "_short_token_map"]


def create_selection_token(franchisee_id, expires_minutes=5):
    """创建选片登录token"""
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=expires_minutes)

    _selection_tokens[token] = {
        "franchisee_id": franchisee_id,
        "created_at": datetime.now(),
        "expires_at": expires_at,
        "used": False,
    }

    # 清理过期的token
    cleanup_expired_tokens()

    return token, expires_at


def verify_selection_token(token):
    """验证选片登录token"""
    # 支持短token格式（从scene参数中解析的短token）
    full_token = token
    # 如果是短token，查找对应的完整token
    if token in _short_token_map:
        full_token = _short_token_map[token]
        logger.info(f"✅ 短token映射: {token} -> {full_token}")

    if full_token not in _selection_tokens:
        return None, "token不存在或已过期"

    token_info = _selection_tokens[full_token]

    # 检查是否已使用
    if token_info.get("used"):
        return None, "token已使用"

    # 检查是否过期
    if token_info["expires_at"] < datetime.now():
        del _selection_tokens[full_token]
        # 同时删除短token映射
        if token in _short_token_map:
            del _short_token_map[token]
        return None, "token已过期"

    return token_info, None


def mark_token_as_used(token, openid=None):
    """标记token为已使用"""
    full_token = token
    if token in _short_token_map:
        full_token = _short_token_map[token]

    if full_token in _selection_tokens:
        token_info = _selection_tokens[full_token]
        token_info["used"] = True
        token_info["used_at"] = datetime.now()
        if openid:
            token_info["used_by_openid"] = openid

        # 同时删除短token映射（一次性使用）
        if token in _short_token_map:
            del _short_token_map[token]


def create_short_token(full_token):
    """创建短token（用于微信小程序码scene参数）"""
    short_token = full_token.replace("-", "")[:16]  # 去掉连字符，取前16个字符
    _short_token_map[short_token] = full_token
    return short_token


def cleanup_expired_tokens():
    """清理过期的token"""
    current_time = datetime.now()
    expired_tokens = [k for k, v in _selection_tokens.items() if v["expires_at"] < current_time]
    for expired_token in expired_tokens:
        del _selection_tokens[expired_token]


def get_app_instance():
    """获取应用实例"""
    import sys

    from flask import current_app, has_app_context

    try:
        # 检查是否有应用上下文
        if not has_app_context():
            logger.warning("没有Flask应用上下文，无法获取应用实例")
            return None

        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            if hasattr(test_server_module, "app") and test_server_module.app is not None:
                return test_server_module.app

        # 尝试获取current_app
        try:
            app = current_app
            # 验证app是否有效（有config属性）
            if hasattr(app, "config"):
                return app
            else:
                logger.warning("current_app没有config属性")
                return None
        except RuntimeError as e:
            logger.warning(f"无法获取current_app: {e}")
            return None
    except Exception as e:
        logger.error(f"获取应用实例时出错: {e}", exc_info=True)
        return None


def check_photo_selection_permission(order, session_franchisee_id=None, current_user=None):
    """检查选片权限"""
    from flask import flash, redirect, session, url_for

    if session_franchisee_id is None:
        session_franchisee_id = session.get("franchisee_id")

    # 如果session中有加盟商ID，检查订单是否属于该加盟商
    if session_franchisee_id:
        if getattr(order, "franchisee_id", None) != session_franchisee_id:
            return False, redirect(
                url_for(
                    "photo_selection.photo_selection_list.photo_selection_list",
                    franchisee_id=session_franchisee_id,
                )
            )
    else:
        # 管理员需要登录且是admin或operator角色
        if not current_user or not current_user.is_authenticated:
            return False, redirect(url_for("auth.login"))
        if current_user.role not in ["admin", "operator"]:
            flash("权限不足", "error")
            return False, redirect(url_for("auth.login"))

    return True, None
