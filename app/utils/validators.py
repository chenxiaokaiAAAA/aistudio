# -*- coding: utf-8 -*-
"""
输入验证工具模块
提供统一的输入验证和清理功能
"""

import logging

logger = logging.getLogger(__name__)
import re
from urllib.parse import quote, unquote

from app.utils.exceptions import ValidationError


def sanitize_string(value, max_length=None, allow_empty=False):
    """
    清理字符串输入

    Args:
        value: 输入值
        max_length: 最大长度
        allow_empty: 是否允许空字符串

    Returns:
        清理后的字符串

    Raises:
        ValidationError: 验证失败
    """
    if value is None:
        if allow_empty:
            return ""
        raise ValidationError("值不能为空")

    # 转换为字符串
    value = str(value).strip()

    # 检查是否为空
    if not value and not allow_empty:
        raise ValidationError("值不能为空")

    # 检查长度
    if max_length and len(value) > max_length:
        raise ValidationError(f"值长度不能超过{max_length}个字符")

    return value


def sanitize_phone(phone):
    """
    验证和清理手机号

    Args:
        phone: 手机号

    Returns:
        清理后的手机号（只保留数字）

    Raises:
        ValidationError: 手机号格式不正确
    """
    if not phone:
        raise ValidationError("手机号不能为空")

    # 移除所有非数字字符
    phone = re.sub(r"\D", "", str(phone))

    # 验证长度（中国手机号11位）
    if len(phone) != 11:
        raise ValidationError("手机号必须是11位数字")

    # 验证开头（1开头）
    if not phone.startswith("1"):
        raise ValidationError("手机号格式不正确")

    return phone


def sanitize_email(email):
    """
    验证和清理邮箱地址

    Args:
        email: 邮箱地址

    Returns:
        清理后的邮箱地址（小写）

    Raises:
        ValidationError: 邮箱格式不正确
    """
    if not email:
        raise ValidationError("邮箱不能为空")

    email = str(email).strip().lower()

    # 基本格式验证
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("邮箱格式不正确")

    return email


def sanitize_url(url):
    """
    验证和清理URL

    Args:
        url: URL字符串

    Returns:
        清理后的URL

    Raises:
        ValidationError: URL格式不正确
    """
    if not url:
        raise ValidationError("URL不能为空")

    url = str(url).strip()

    # 基本URL格式验证
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValidationError("URL必须以http://或https://开头")

    return url


def sanitize_order_number(order_number):
    """
    验证和清理订单号

    Args:
        order_number: 订单号

    Returns:
        清理后的订单号

    Raises:
        ValidationError: 订单号格式不正确
    """
    if not order_number:
        raise ValidationError("订单号不能为空")

    order_number = str(order_number).strip().upper()

    # 订单号只能包含字母、数字、连字符和下划线
    if not re.match(r"^[A-Z0-9_-]+$", order_number):
        raise ValidationError("订单号格式不正确，只能包含字母、数字、连字符和下划线")

    # 长度限制
    if len(order_number) > 50:
        raise ValidationError("订单号长度不能超过50个字符")

    return order_number


def sanitize_search_query(query):
    """
    清理搜索查询字符串，防止SQL注入

    Args:
        query: 搜索查询字符串

    Returns:
        清理后的查询字符串
    """
    if not query:
        return ""

    query = str(query).strip()

    # 移除SQL注入常见字符
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
    for char in dangerous_chars:
        query = query.replace(char, "")

    # 限制长度
    if len(query) > 100:
        query = query[:100]

    return query


def sanitize_filename(filename):
    """
    清理文件名，防止路径遍历攻击

    Args:
        filename: 文件名

    Returns:
        清理后的文件名

    Raises:
        ValidationError: 文件名不安全
    """
    if not filename:
        raise ValidationError("文件名不能为空")

    filename = str(filename).strip()

    # 移除路径分隔符
    filename = filename.replace("/", "").replace("\\", "")

    # 移除危险字符
    dangerous_chars = ["..", "<", ">", ":", '"', "|", "?", "*"]
    for char in dangerous_chars:
        filename = filename.replace(char, "")

    # 限制长度
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def validate_pagination(page, per_page, max_per_page=100):
    """
    验证分页参数

    Args:
        page: 页码
        per_page: 每页数量
        max_per_page: 每页最大数量

    Returns:
        (page, per_page) 元组

    Raises:
        ValidationError: 参数无效
    """
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 20
    except (ValueError, TypeError):
        raise ValidationError("分页参数必须是数字")

    if page < 1:
        raise ValidationError("页码必须大于0")

    if per_page < 1:
        raise ValidationError("每页数量必须大于0")

    if per_page > max_per_page:
        raise ValidationError(f"每页数量不能超过{max_per_page}")

    return page, per_page
