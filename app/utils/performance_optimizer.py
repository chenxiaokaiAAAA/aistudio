# -*- coding: utf-8 -*-
"""
性能优化工具模块
提供：图片处理优化、API响应优化、缓存等功能
"""

import functools
import hashlib
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple

from flask import Response, current_app, request
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图片处理优化类"""

    @staticmethod
    def compress_image_async(
        file_path: str, max_size_mb: float = 5, max_dimension: int = 1920, quality: int = 85
    ) -> Tuple[bool, int, int]:
        """
        异步压缩图片（优化版本）

        Args:
            file_path: 图片文件路径
            max_size_mb: 最大文件大小（MB）
            max_dimension: 最大尺寸（像素）
            quality: JPEG质量（1-100）

        Returns:
            tuple: (是否成功, 原始大小, 压缩后大小)
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                return False, 0, 0

            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024

            # 如果文件大小未超过限制，不压缩
            if file_size <= max_size_bytes:
                return True, file_size, file_size

            # 打开并压缩图片
            with Image.open(file_path) as img:
                # 转换为RGB模式（如果需要）
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # 调整尺寸
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

                # 保存压缩后的图片
                img.save(file_path, "JPEG", quality=quality, optimize=True)
                new_size = os.path.getsize(file_path)

                logger.info(
                    f"✅ 图片压缩成功: {file_path} ({file_size / 1024:.2f} KB -> {new_size / 1024:.2f} KB)"
                )
                return True, file_size, new_size

        except Exception as e:
            logger.error(f"图片压缩失败: {file_path}, 错误: {e}")
            return (
                False,
                file_size if "file_size" in locals() else 0,
                file_size if "file_size" in locals() else 0,
            )

    @staticmethod
    def generate_thumbnail_optimized(
        original_path: str,
        thumbnail_path: Optional[str] = None,
        max_size: int = 1920,
        quality: int = 85,
    ) -> Optional[str]:
        """
        优化版缩略图生成（带缓存检查）

        Args:
            original_path: 原图路径
            thumbnail_path: 缩略图保存路径（如果为None，自动生成）
            max_size: 最大边长（像素）
            quality: JPEG质量（1-100）

        Returns:
            str: 缩略图路径，如果失败返回None
        """
        try:
            if not os.path.exists(original_path):
                logger.warning(f"原图文件不存在: {original_path}")
                return None

            # 如果没有指定缩略图路径，自动生成
            if thumbnail_path is None:
                base, ext = os.path.splitext(original_path)
                thumbnail_path = f"{base}_thumb.jpg"

            # 检查缩略图是否已存在且比原图新
            if os.path.exists(thumbnail_path):
                thumbnail_mtime = os.path.getmtime(thumbnail_path)
                original_mtime = os.path.getmtime(original_path)
                if thumbnail_mtime >= original_mtime:
                    logger.debug(f"缩略图已存在且是最新的: {thumbnail_path}")
                    return thumbnail_path

            # 打开原图
            with Image.open(original_path) as img:
                # 转换为RGB（JPG不支持透明度）
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # 计算新尺寸（保持宽高比，长边不超过max_size）
                width, height = img.size
                if width > max_size or height > max_size:
                    if width > height:
                        new_width = max_size
                        new_height = int(height * max_size / width)
                    else:
                        new_height = max_size
                        new_width = int(width * max_size / height)

                    # 使用高质量重采样
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 确保缩略图目录存在
                thumbnail_dir = os.path.dirname(thumbnail_path)
                if thumbnail_dir and not os.path.exists(thumbnail_dir):
                    os.makedirs(thumbnail_dir, exist_ok=True)

                # 保存缩略图
                img.save(thumbnail_path, "JPEG", quality=quality, optimize=True)

                original_size = os.path.getsize(original_path)
                thumbnail_size = os.path.getsize(thumbnail_path)
                compression_ratio = (
                    (1 - thumbnail_size / original_size) * 100 if original_size > 0 else 0
                )

                logger.info(
                    f"✅ 缩略图生成成功: {thumbnail_path} (压缩率: {compression_ratio:.1f}%)"
                )
                return thumbnail_path

        except Exception as e:
            logger.error(f"生成缩略图失败: {original_path}, 错误: {e}")
            return None


class ResponseOptimizer:
    """API响应优化类"""

    @staticmethod
    def add_cache_headers(
        response: Response, max_age: int = 3600, public: bool = True, must_revalidate: bool = False
    ) -> Response:
        """
        添加缓存响应头

        Args:
            response: Flask响应对象
            max_age: 缓存时间（秒），默认1小时
            public: 是否允许公共缓存
            must_revalidate: 是否必须重新验证

        Returns:
            Response: 添加了缓存头的响应对象
        """
        cache_control = []
        if public:
            cache_control.append("public")
        cache_control.append(f"max-age={max_age}")
        if must_revalidate:
            cache_control.append("must-revalidate")

        response.headers["Cache-Control"] = ", ".join(cache_control)
        response.headers["Expires"] = (datetime.utcnow() + timedelta(seconds=max_age)).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )
        return response

    @staticmethod
    def add_etag_header(response: Response, content: Any) -> Response:
        """
        添加ETag响应头（用于缓存验证）

        Args:
            response: Flask响应对象
            content: 响应内容（用于生成ETag）

        Returns:
            Response: 添加了ETag头的响应对象
        """
        if isinstance(content, (str, bytes)):
            etag = hashlib.md5(
                content.encode() if isinstance(content, str) else content
            ).hexdigest()
        else:
            # 对于JSON等对象，转换为字符串后生成ETag
            import json

            etag = hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()

        response.headers["ETag"] = f'"{etag}"'
        return response

    @staticmethod
    def check_etag(request_obj: Any, etag: str) -> bool:
        """
        检查ETag是否匹配（用于304 Not Modified响应）

        Args:
            request_obj: Flask请求对象
            etag: 当前资源的ETag

        Returns:
            bool: 如果ETag匹配返回True
        """
        if_none_match = request_obj.headers.get("If-None-Match", "")
        return f'"{etag}"' in if_none_match or etag in if_none_match

    @staticmethod
    def optimize_json_response(
        data: Dict[str, Any], max_age: int = 300, add_etag: bool = True
    ) -> Response:
        """
        优化JSON响应（添加缓存头、ETag等）

        Args:
            data: JSON数据
            max_age: 缓存时间（秒），默认5分钟
            add_etag: 是否添加ETag

        Returns:
            Response: 优化后的响应对象
        """
        from flask import jsonify

        response = jsonify(data)

        # 添加缓存头
        ResponseOptimizer.add_cache_headers(response, max_age=max_age, public=False)

        # 添加ETag
        if add_etag:
            ResponseOptimizer.add_etag_header(response, data)

        return response


def cache_response(max_age: int = 300, key_func: Optional[Callable] = None):
    """
    响应缓存装饰器

    Args:
        max_age: 缓存时间（秒）
        key_func: 缓存键生成函数（可选）

    Usage:
        @cache_response(max_age=600)
        def my_view():
            return jsonify({'data': '...'})
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = f"perf:{key_func(*args, **kwargs)}"
            else:
                cache_key = f"perf:{func.__name__}:{request.path}:{request.query_string.decode()}"

            # 尝试从 Redis 缓存获取
            try:
                from app.services.cache_service import get_cache, set_cache

                cached = get_cache(cache_key)
                if cached is not None:
                    return Response(
                        cached.get("body"),
                        status=cached.get("status", 200),
                        mimetype=cached.get("mimetype", "application/json"),
                    )
            except Exception:
                pass

            # 执行函数
            response = func(*args, **kwargs)

            # 添加缓存头
            if isinstance(response, Response):
                ResponseOptimizer.add_cache_headers(response, max_age=max_age)
                # 缓存 JSON 响应到 Redis
                try:
                    from app.services.cache_service import set_cache

                    if response.content_type and "application/json" in response.content_type:
                        set_cache(
                            cache_key,
                            {
                                "body": response.get_data(as_text=True),
                                "status": response.status_code,
                                "mimetype": response.content_type,
                            },
                            timeout=max_age,
                        )
                except Exception:
                    pass

            return response

        return wrapper

    return decorator


def optimize_image_response(response: Response, file_path: str) -> Response:
    """
    优化图片响应（添加缓存头、压缩等）

    Args:
        response: Flask响应对象
        file_path: 图片文件路径

    Returns:
        Response: 优化后的响应对象
    """
    # 添加长期缓存（图片通常不会变化）
    ResponseOptimizer.add_cache_headers(response, max_age=86400 * 30, public=True)

    # 添加ETag（基于文件修改时间）
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        etag = hashlib.md5(f"{file_path}:{mtime}".encode()).hexdigest()
        response.headers["ETag"] = f'"{etag}"'

    # 设置内容类型
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gi": "image/gi",
        ".webp": "image/webp",
    }
    if ext in content_types:
        response.headers["Content-Type"] = content_types[ext]

    return response
