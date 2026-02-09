# -*- coding: utf-8 -*-
"""
分页工具模块
提供统一的分页功能
"""

from math import ceil

from flask import request


def get_pagination_params(max_per_page=100):
    """
    从请求参数获取分页参数

    Args:
        max_per_page: 每页最大记录数（防止请求过多数据）

    Returns:
        tuple: (page, per_page)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # 限制每页最大记录数
    if per_page > max_per_page:
        per_page = max_per_page

    # 确保页码至少为1
    if page < 1:
        page = 1

    return page, per_page


def paginate_query(query, page=None, per_page=None, max_per_page=100):
    """
    对查询进行分页

    Args:
        query: SQLAlchemy查询对象
        page: 页码（如果为None，从请求参数获取）
        per_page: 每页记录数（如果为None，从请求参数获取）
        max_per_page: 每页最大记录数

    Returns:
        pagination对象
    """
    if page is None or per_page is None:
        page, per_page = get_pagination_params(max_per_page)

    return query.paginate(page=page, per_page=per_page, error_out=False)


def format_pagination_response(pagination, data_key="data"):
    """
    格式化分页响应

    Args:
        pagination: SQLAlchemy分页对象
        data_key: 数据字段名

    Returns:
        dict: 格式化的响应数据
    """
    return {
        data_key: [item for item in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_prev": pagination.has_prev,
            "has_next": pagination.has_next,
            "prev_page": pagination.prev_num if pagination.has_prev else None,
            "next_page": pagination.next_num if pagination.has_next else None,
        },
    }
