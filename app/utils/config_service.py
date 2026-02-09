# -*- coding: utf-8 -*-
"""
统一配置管理服务
优先级: 数据库配置 > 环境变量 > 文件配置 > 默认值
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)


class ConfigService:
    """统一配置管理服务"""

    def __init__(self, db=None, AIConfig=None):
        """
        初始化配置服务

        Args:
            db: 数据库实例（可选）
            AIConfig: AIConfig模型类（可选）
        """
        self.db = db
        self.AIConfig = AIConfig
        self._cache = {}

    def get_config(self, key, default_value=None, use_cache=True):
        """
        获取配置值（按优先级）

        优先级:
        1. 数据库配置 (AIConfig表)
        2. 环境变量
        3. 文件配置 (server_config.py)
        4. 默认值

        Args:
            key: 配置键
            default_value: 默认值
            use_cache: 是否使用缓存

        Returns:
            配置值
        """
        # 检查缓存
        if use_cache and key in self._cache:
            return self._cache[key]

        value = None

        # 1. 优先从数据库读取
        if self.db and self.AIConfig:
            try:
                config = self.AIConfig.query.filter_by(config_key=key).first()
                if config and config.config_value:
                    value = config.config_value
                    logger.debug(f"从数据库读取配置: {key} = {value}")
            except Exception as e:
                logger.warning(f"从数据库读取配置失败: {key}, 错误: {e}")

        # 2. 如果数据库没有，从环境变量读取
        if value is None:
            env_key = key.upper().replace(".", "_")
            value = os.environ.get(env_key)
            if value:
                logger.debug(f"从环境变量读取配置: {key} = {value}")

        # 3. 如果环境变量也没有，从文件配置读取
        if value is None:
            try:
                from server_config import get_config as get_server_config

                server_config = get_server_config()
                if key in server_config:
                    value = server_config[key]
                    logger.debug(f"从文件配置读取: {key} = {value}")
            except Exception as e:
                logger.debug(f"从文件配置读取失败: {key}, 错误: {e}")

        # 4. 使用默认值
        if value is None:
            value = default_value
            if value is not None:
                logger.debug(f"使用默认值: {key} = {value}")

        # 缓存结果
        if use_cache:
            self._cache[key] = value

        return value

    def set_config(self, key, value, description=None):
        """
        设置配置值（保存到数据库）

        Args:
            key: 配置键
            value: 配置值
            description: 配置说明
        """
        if not self.db or not self.AIConfig:
            logger.warning("数据库或AIConfig模型不可用，无法保存配置")
            return False

        try:
            config = self.AIConfig.query.filter_by(config_key=key).first()
            if config:
                config.config_value = str(value)
                if description:
                    config.description = description
            else:
                config = self.AIConfig(
                    config_key=key, config_value=str(value), description=description or ""
                )
                self.db.session.add(config)

            self.db.session.commit()

            # 清除缓存
            if key in self._cache:
                del self._cache[key]

            logger.info(f"配置已保存: {key} = {value}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {key}, 错误: {e}")
            self.db.session.rollback()
            return False

    def clear_cache(self):
        """清除配置缓存"""
        self._cache.clear()
        logger.debug("配置缓存已清除")


# 全局配置服务实例（延迟初始化）
_config_service = None


def get_config_service(db=None, AIConfig=None):
    """
    获取全局配置服务实例

    Args:
        db: 数据库实例（可选）
        AIConfig: AIConfig模型类（可选）

    Returns:
        ConfigService实例
    """
    global _config_service

    if _config_service is None:
        # 如果没有传入，尝试从test_server获取
        if not db or not AIConfig:
            if "test_server" in sys.modules:
                test_server_module = sys.modules["test_server"]
                if hasattr(test_server_module, "db"):
                    db = test_server_module.db
                if hasattr(test_server_module, "AIConfig"):
                    AIConfig = test_server_module.AIConfig

        _config_service = ConfigService(db=db, AIConfig=AIConfig)

    return _config_service


def get_config(key, default_value=None, db=None, AIConfig=None):
    """
    便捷函数：获取配置值

    Args:
        key: 配置键
        default_value: 默认值
        db: 数据库实例（可选）
        AIConfig: AIConfig模型类（可选）

    Returns:
        配置值
    """
    config_service = get_config_service(db=db, AIConfig=AIConfig)
    return config_service.get_config(key, default_value=default_value)
