# -*- coding: utf-8 -*-
"""
日志配置模块
统一配置应用的日志系统
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(app=None, log_level=None):
    """
    配置应用日志系统

    Args:
        app: Flask应用实例（可选）
        log_level: 日志级别（可选，默认从环境变量读取）
    """
    # 确定日志级别
    if log_level is None:
        env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, env_level, logging.INFO)

    # 确定是否生产环境
    is_production = (
        os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENV") == "production"
    )

    # 创建日志格式
    if is_production:
        # 生产环境：结构化日志
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
    else:
        # 开发环境：详细日志
        log_format = "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(log_format, datefmt=date_format)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 控制台处理器（所有环境）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（生产环境）
    if is_production:
        log_dir = os.environ.get("LOG_DIR", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 应用日志
        app_log_file = os.path.join(log_dir, "app.log")
        app_handler = RotatingFileHandler(
            app_log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)

        # 错误日志
        error_log_file = os.path.join(log_dir, "error.log")
        error_handler = RotatingFileHandler(
            error_log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    # 配置Flask日志
    if app:
        app.logger.setLevel(log_level)
        # Flask日志也使用根日志记录器的处理器
        app.logger.handlers = root_logger.handlers

    # 设置第三方库日志级别
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


def get_logger(name):
    """
    获取日志记录器

    Args:
        name: 日志记录器名称（通常是模块名）

    Returns:
        logging.Logger实例
    """
    return logging.getLogger(name)
