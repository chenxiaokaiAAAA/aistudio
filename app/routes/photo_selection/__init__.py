# -*- coding: utf-8 -*-
"""
选片页面路由模块
整合所有选片相关的子模块
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint

# 创建主蓝图
photo_selection_bp = Blueprint("photo_selection", __name__)

# 导入并注册所有子模块
try:
    from . import list

    photo_selection_bp.register_blueprint(list.bp)
    logger.info("✅ 已注册 photo_selection_list 蓝图")
except ImportError as e:
    logger.warning(f"无法导入list模块: {e}")

try:
    from . import detail

    photo_selection_bp.register_blueprint(detail.bp)
    logger.info("✅ 已注册 photo_selection_detail 蓝图")
except ImportError as e:
    logger.warning(f"无法导入detail模块: {e}")

try:
    from . import submit

    photo_selection_bp.register_blueprint(submit.bp)
    logger.info("✅ 已注册 photo_selection_submit 蓝图")
except ImportError as e:
    logger.warning(f"无法导入submit模块: {e}")

try:
    from . import confirm

    photo_selection_bp.register_blueprint(confirm.bp)
    logger.info("✅ 已注册 photo_selection_confirm 蓝图")
except ImportError as e:
    logger.warning(f"无法导入confirm模块: {e}")

try:
    from . import print_module

    photo_selection_bp.register_blueprint(print_module.bp)
    logger.info("✅ 已注册 photo_selection_print 蓝图")
except ImportError as e:
    logger.warning(f"无法导入print_module模块: {e}")

try:
    from . import qrcode

    photo_selection_bp.register_blueprint(qrcode.bp)
    logger.info("✅ 已注册 photo_selection_qrcode 蓝图")
except ImportError as e:
    logger.warning(f"无法导入qrcode模块: {e}")

try:
    from . import search

    photo_selection_bp.register_blueprint(search.bp)
    logger.info("✅ 已注册 photo_selection_search 蓝图")
except ImportError as e:
    logger.warning(f"无法导入search模块: {e}")

# 导出主蓝图（供test_server.py使用）
__all__ = ["photo_selection_bp"]
