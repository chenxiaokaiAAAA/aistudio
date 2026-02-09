# -*- coding: utf-8 -*-
"""
缓存服务模块
支持Redis缓存，提升系统性能
"""

import hashlib
import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Redis客户端（延迟导入）
_redis_client = None


def get_redis_client():
    """获取Redis客户端（单例模式）"""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    # 如果已经尝试连接失败，直接返回None（避免重复尝试）
    if _redis_client is False:
        return None

    try:
        import redis
        from flask import current_app

        # 从配置获取Redis连接信息
        redis_host = current_app.config.get("REDIS_HOST", "localhost")
        redis_port = current_app.config.get("REDIS_PORT", 6379)
        redis_db = current_app.config.get("REDIS_DB", 0)
        redis_password = current_app.config.get("REDIS_PASSWORD", None)

        # 创建Redis连接（缩短超时时间，避免阻塞）
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,  # 自动解码为字符串
            socket_connect_timeout=1,  # 缩短连接超时到1秒
            socket_timeout=1,  # 缩短操作超时到1秒
        )

        # 测试连接（快速失败）
        _redis_client.ping()
        logger.info(f"✅ Redis连接成功: {redis_host}:{redis_port}")

        return _redis_client

    except ImportError:
        logger.warning("⚠️  Redis未安装，缓存功能将不可用。请安装: pip install redis")
        _redis_client = False  # 标记为已尝试，避免重复尝试
        return None
    except Exception as e:
        # 只在第一次失败时记录警告，避免日志刷屏
        if _redis_client is None:
            logger.warning(f"⚠️  Redis连接失败: {e}，缓存功能将不可用（不影响主功能）")
        _redis_client = False  # 标记为已尝试，避免重复尝试
        return None


def is_cache_available():
    """检查缓存是否可用"""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.ping()
        return True
    except Exception:
        return False


def cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    # 将参数序列化为字符串
    key_parts = [prefix]

    # 添加位置参数
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # 复杂对象使用hash
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

    # 添加关键字参数（排序后保证一致性）
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = "_".join(f"{k}:{v}" for k, v in sorted_kwargs)
        key_parts.append(kwargs_str)

    # 生成最终键
    key = "_".join(key_parts)

    # 如果键太长，使用hash
    if len(key) > 200:
        key = f"{prefix}_{hashlib.md5(key.encode()).hexdigest()}"

    return f"cache:{key}"


def get_cache(key: str) -> Optional[Any]:
    """
    从缓存获取数据

    Args:
        key: 缓存键

    Returns:
        缓存的数据，如果不存在或出错返回None
    """
    if not is_cache_available():
        return None

    try:
        client = get_redis_client()
        value = client.get(key)

        if value is None:
            return None

        # 尝试解析JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON，直接返回字符串
            return value

    except Exception as e:
        # 只在debug模式下记录，避免日志刷屏
        logger.debug(f"获取缓存失败 {key}: {e}")
        return None


def set_cache(key: str, value: Any, timeout: int = 3600) -> bool:
    """
    设置缓存

    Args:
        key: 缓存键
        value: 要缓存的数据
        timeout: 过期时间（秒），默认1小时

    Returns:
        是否设置成功
    """
    if not is_cache_available():
        return False

    try:
        client = get_redis_client()

        # 序列化为JSON
        if isinstance(value, (str, int, float, bool, type(None))):
            # 简单类型直接存储
            serialized = json.dumps(value, ensure_ascii=False)
        else:
            # 复杂对象序列化为JSON
            serialized = json.dumps(value, ensure_ascii=False, default=str)

        # 设置缓存
        client.setex(key, timeout, serialized)
        return True

    except Exception as e:
        logger.warning(f"⚠️  设置缓存失败 {key}: {e}")
        return False


def delete_cache(key: str) -> bool:
    """
    删除缓存

    Args:
        key: 缓存键

    Returns:
        是否删除成功
    """
    if not is_cache_available():
        return False

    try:
        client = get_redis_client()
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"⚠️  删除缓存失败 {key}: {e}")
        return False


def delete_cache_pattern(pattern: str) -> int:
    """
    按模式删除缓存

    Args:
        pattern: 缓存键模式（支持通配符，如 cache:product:*）

    Returns:
        删除的缓存数量
    """
    if not is_cache_available():
        return 0

    try:
        client = get_redis_client()
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"⚠️  按模式删除缓存失败 {pattern}: {e}")
        return 0


def cached(timeout: int = 3600, key_prefix: str = None):
    """
    缓存装饰器

    Args:
        timeout: 缓存过期时间（秒），默认1小时
        key_prefix: 缓存键前缀，如果不指定则使用函数名

    Usage:
        @cached(timeout=1800, key_prefix='products')
        def get_products():
            return Product.query.all()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key_str = cache_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_value = get_cache(cache_key_str)
            if cached_value is not None:
                logger.debug(f"✅ 缓存命中: {cache_key_str}")
                return cached_value

            # 缓存未命中，执行函数
            logger.debug(f"❌ 缓存未命中: {cache_key_str}")
            result = func(*args, **kwargs)

            # 将结果存入缓存
            set_cache(cache_key_str, result, timeout)

            return result

        return wrapper

    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs):
    """
    使缓存失效

    Args:
        key_prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数

    Usage:
        invalidate_cache('products', category_id=1)
    """
    cache_key_str = cache_key(key_prefix, *args, **kwargs)
    delete_cache(cache_key_str)
    logger.debug(f"🗑️  缓存已失效: {cache_key_str}")


def invalidate_cache_pattern(pattern: str):
    """
    按模式使缓存失效

    Args:
        pattern: 缓存键模式

    Usage:
        invalidate_cache_pattern('cache:products:*')
    """
    count = delete_cache_pattern(pattern)
    logger.debug(f"🗑️  已删除 {count} 个缓存: {pattern}")


# 常用缓存键前缀
CACHE_PREFIXES = {
    "PRODUCTS": "products",
    "PRODUCT_CATEGORIES": "product_categories",
    "STYLES": "styles",
    "STYLE_CATEGORIES": "style_categories",
    "ORDERS": "orders",
    "DASHBOARD": "dashboard",
    "CONFIG": "config",
    "STATISTICS": "statistics",
}


def get_cache_stats() -> dict:
    """
    获取缓存统计信息

    Returns:
        缓存统计信息字典
    """
    if not is_cache_available():
        return {"available": False, "message": "Redis未安装或不可用"}

    try:
        client = get_redis_client()
        info = client.info()

        return {
            "available": True,
            "used_memory": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_keys": client.dbsize(),
            "keyspace": info.get("db0", {}),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}
