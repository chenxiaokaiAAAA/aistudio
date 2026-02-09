# -*- coding: utf-8 -*-
"""
美图API配置管理路由（已拆分到子模块）
此文件保留用于向后兼容，实际路由已拆分到 app.routes.meitu 包中
"""

import logging

logger = logging.getLogger(__name__)

# 从子模块导入主蓝图，保持向后兼容
try:
    from app.routes.meitu import meitu_bp

    logger.info("✅ 已从子模块导入 meitu_bp")
except ImportError as e:
    logger.warning(f"无法从子模块导入 meitu_bp: {e}")
    # 如果导入失败，创建一个空的蓝图（向后兼容）
    from flask import Blueprint

    meitu_bp = Blueprint("meitu", __name__, url_prefix="/admin/meitu")
    logger.warning("已创建空的 meitu_bp 蓝图（向后兼容）")

# 导出蓝图（供 test_server.py 等使用）
__all__ = ["meitu_bp"]
