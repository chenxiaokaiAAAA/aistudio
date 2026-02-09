# -*- coding: utf-8 -*-
"""
配置加载工具 - 从数据库读取系统配置
"""

import logging

logger = logging.getLogger(__name__)
import sys


def get_config_value(config_key, default_value=None, db=None, AIConfig=None):
    """
    从数据库获取配置值

    Args:
        config_key: 配置键
        default_value: 默认值
        db: 数据库实例（可选）
        AIConfig: AIConfig模型类（可选）

    Returns:
        配置值（字符串），如果不存在则返回默认值
    """
    try:
        # 如果没有传入，尝试从test_server获取
        if not db or not AIConfig:
            if "test_server" in sys.modules:
                test_server_module = sys.modules["test_server"]
                if hasattr(test_server_module, "db"):
                    db = test_server_module.db
                if hasattr(test_server_module, "AIConfig"):
                    AIConfig = test_server_module.AIConfig

        if db and AIConfig:
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config and config.config_value:
                return config.config_value
    except Exception as e:
        logger.warning("读取配置 {config_key} 失败: {str(e)}")

    return default_value


def get_int_config(config_key, default_value=0, db=None, AIConfig=None):
    """
    从数据库获取整数配置值

    Args:
        config_key: 配置键
        default_value: 默认值
        db: 数据库实例（可选）
        AIConfig: AIConfig模型类（可选）

    Returns:
        整数配置值
    """
    value = get_config_value(config_key, str(default_value), db, AIConfig)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default_value


def get_concurrency_configs(db=None, AIConfig=None):
    """
    获取并发相关配置

    Returns:
        dict: 包含所有并发配置的字典
    """
    return {
        "comfyui_max_concurrency": get_int_config("comfyui_max_concurrency", 10, db, AIConfig),
        "api_max_concurrency": get_int_config("api_max_concurrency", 5, db, AIConfig),
        "task_queue_max_size": get_int_config("task_queue_max_size", 100, db, AIConfig),
        "task_queue_workers": get_int_config("task_queue_workers", 3, db, AIConfig),
    }


def get_brand_name(db=None, AIConfig=None):
    """
    获取品牌名称

    Returns:
        str: 品牌名称，默认为 'AI拍照机'
    """
    return get_config_value("brand_name", "AI拍照机", db, AIConfig)


def get_image_upload_config(db=None, AIConfig=None):
    """
    获取图片上传配置

    Returns:
        dict: 包含图片上传策略和环境的字典
    """
    return {
        "strategy": get_config_value("image_upload_strategy", "grsai", db, AIConfig),
        "environment": get_config_value("image_upload_environment", "local", db, AIConfig),
    }


def should_upload_to_grsai(image_url=None, db=None, AIConfig=None):
    """
    判断是否应该上传图片到GRSAI服务器

    Args:
        image_url: 图片URL（可选，用于判断是否已经是云端URL）
        db: 数据库实例（可选）
        AIConfig: AIConfig模型类（可选）

    Returns:
        bool: True表示应该上传到GRSAI，False表示直接使用现有URL
    """
    config = get_image_upload_config(db, AIConfig)

    # 如果配置为直接使用云端URL，且图片URL已经是云端URL（http://或https://开头），则不上传
    if config["strategy"] == "direct":
        if image_url and (image_url.startswith("http://") or image_url.startswith("https://")):
            # 检查是否是本地路径（如 /uploads/xxx）
            if not image_url.startswith("/uploads/") and not image_url.startswith("/media/"):
                return False

    # 如果配置为上传到GRSAI，或者图片是本地路径，则需要上传
    if config["strategy"] == "grsai":
        return True

    # 默认情况下，如果是本地路径，需要上传
    if image_url and (image_url.startswith("/uploads/") or image_url.startswith("/media/")):
        return True

    return False
