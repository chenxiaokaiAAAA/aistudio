# -*- coding: utf-8 -*-
"""
美图API配置管理路由模块
整合所有美图相关的子模块
"""

import logging

logger = logging.getLogger(__name__)
from flask import Blueprint

# 创建主蓝图
meitu_bp = Blueprint("meitu", __name__, url_prefix="/admin/meitu")

# 导入并注册所有子模块
try:
    from . import config

    meitu_bp.register_blueprint(config.bp)
    logger.info("✅ 已注册 meitu_config 蓝图")
except ImportError as e:
    logger.warning(f"无法导入config模块: {e}")

try:
    from . import presets

    meitu_bp.register_blueprint(presets.bp)
    logger.info("✅ 已注册 meitu_presets 蓝图")
except ImportError as e:
    logger.warning(f"无法导入presets模块: {e}")

try:
    from . import tasks

    meitu_bp.register_blueprint(tasks.bp)
    logger.info("✅ 已注册 meitu_tasks 蓝图")
except ImportError as e:
    logger.warning(f"无法导入tasks模块: {e}")

try:
    from . import test

    meitu_bp.register_blueprint(test.bp)
    logger.info("✅ 已注册 meitu_test 蓝图")
except ImportError as e:
    logger.warning(f"无法导入test模块: {e}")

# 导出主蓝图（供test_server.py使用）
__all__ = ["meitu_bp"]
