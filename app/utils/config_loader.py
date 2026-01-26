# -*- coding: utf-8 -*-
"""
配置加载工具 - 从数据库读取系统配置
"""
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
            if 'test_server' in sys.modules:
                test_server_module = sys.modules['test_server']
                if hasattr(test_server_module, 'db'):
                    db = test_server_module.db
                if hasattr(test_server_module, 'AIConfig'):
                    AIConfig = test_server_module.AIConfig
        
        if db and AIConfig:
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config and config.config_value:
                return config.config_value
    except Exception as e:
        print(f"⚠️ 读取配置 {config_key} 失败: {str(e)}")
    
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
        'comfyui_max_concurrency': get_int_config('comfyui_max_concurrency', 10, db, AIConfig),
        'api_max_concurrency': get_int_config('api_max_concurrency', 5, db, AIConfig),
        'task_queue_max_size': get_int_config('task_queue_max_size', 100, db, AIConfig),
        'task_queue_workers': get_int_config('task_queue_workers', 3, db, AIConfig)
    }


def get_brand_name(db=None, AIConfig=None):
    """
    获取品牌名称
    
    Returns:
        str: 品牌名称，默认为 'AI拍照机'
    """
    return get_config_value('brand_name', 'AI拍照机', db, AIConfig)