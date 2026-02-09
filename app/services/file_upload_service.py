# -*- coding: utf-8 -*-
"""
文件上传服务模块
统一处理文件上传、验证、保存逻辑
"""

import logging

logger = logging.getLogger(__name__)
import os
import re
import uuid
from datetime import datetime

from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename

# 允许的文件扩展名
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gi", "webp", "bmp"}
ALLOWED_FILE_EXTENSIONS = {"png", "jpg", "jpeg", "gi", "webp", "bmp", "pd", "doc", "docx"}

# MIME类型到扩展名的映射
MIME_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gi": ".gi",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}


def allowed_file(filename, allowed_extensions=None):
    """
    检查文件扩展名是否允许

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合，默认为图片扩展名

    Returns:
        bool: 是否允许
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def secure_filename_with_fallback(filename):
    """
    安全文件名处理，如果secure_filename返回空则使用备用方案

    Args:
        filename: 原始文件名

    Returns:
        str: 安全的文件名
    """
    # 先使用secure_filename处理
    safe_name = secure_filename(filename)

    if not safe_name:
        # 如果secure_filename返回空，手动处理
        safe_name = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        # 移除所有非ASCII字符和特殊字符，只保留字母、数字、点、下划线、连字符
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "", safe_name)
        if not safe_name:
            safe_name = "uploaded_file"

    return safe_name


def generate_unique_filename(original_filename, prefix="", suffix=""):
    """
    生成唯一的文件名

    Args:
        original_filename: 原始文件名
        prefix: 文件名前缀（例如: 'mp_', 'admin_'）
        suffix: 文件名后缀

    Returns:
        str: 唯一的文件名
    """
    # 处理文件名
    filename = secure_filename_with_fallback(original_filename)

    # 确保有扩展名
    if "." not in filename:
        filename = filename + ".jpg"  # 默认使用jpg

    # 生成时间戳和UUID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    # 组合文件名
    name, ext = os.path.splitext(filename)
    if prefix:
        filename = f"{prefix}{timestamp}_{unique_id}_{name}{ext}"
    else:
        filename = f"{timestamp}_{unique_id}_{name}{ext}"

    if suffix:
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{suffix}{ext}"

    return filename


def compress_image(file_path, max_size_mb=5, max_dimension=1920, quality=85):
    """
    压缩图片文件（使用优化版本）

    Args:
        file_path: 图片文件路径
        max_size_mb: 最大文件大小（MB），超过此大小才压缩
        max_dimension: 最大尺寸（像素）
        quality: JPEG质量（1-100）

    Returns:
        tuple: (是否压缩成功, 原始大小, 压缩后大小)
    """
    try:
        # 使用优化版本的图片处理器
        from app.utils.performance_optimizer import ImageProcessor

        return ImageProcessor.compress_image_async(file_path, max_size_mb, max_dimension, quality)
    except ImportError:
        # 如果导入失败，使用原有逻辑
        logger.warning("无法导入性能优化模块，使用原有压缩逻辑")
        try:
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024

            if file_size <= max_size_bytes:
                return True, file_size, file_size

            with Image.open(file_path) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

                img.save(file_path, "JPEG", quality=quality, optimize=True)
                new_size = os.path.getsize(file_path)
                return True, file_size, new_size
        except Exception as e:
            logger.info(f"图片压缩失败: {e}")
            return (
                False,
                file_size if "file_size" in locals() else 0,
                file_size if "file_size" in locals() else 0,
            )


def upload_image(file, upload_folder=None, prefix="", max_size_mb=20, compress=None):
    """
    上传图片文件

    Args:
        file: Flask文件对象
        upload_folder: 上传文件夹路径，如果为None则使用app配置
        prefix: 文件名前缀
        max_size_mb: 最大文件大小（MB）
        compress: 是否自动压缩大文件（如果为None，从配置读取）

    Returns:
        tuple: (是否成功, 文件名或错误信息, 文件路径或None)
    """
    # 从配置读取是否自动压缩
    if compress is None:
        try:
            from app.utils.image_path_config import get_image_path_config

            config = get_image_path_config()
            compress_config = config.get_compress_config()
            compress = compress_config["auto_compress"]
        except Exception as e:
            logger.debug(f"读取压缩配置失败，使用默认值: {e}")
            compress = True
    try:
        # 检查文件是否存在
        if not file or file.filename == "":
            return False, "文件名为空", None

        # 检查文件扩展名
        if not allowed_file(file.filename):
            return False, "不支持的文件格式", None

        # 获取上传文件夹
        if upload_folder is None:
            app = current_app
            upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")

        # 确保上传目录存在
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # 生成唯一文件名
        filename = generate_unique_filename(file.filename, prefix=prefix)
        file_path = os.path.join(upload_folder, filename)

        # 检查文件大小（在保存前）
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"文件大小超过限制（最大{max_size_mb}MB）", None

        # 保存文件
        file.save(file_path)

        # 压缩大文件（使用配置的触发大小）
        if compress:
            try:
                from app.utils.image_path_config import get_image_path_config

                config = get_image_path_config()
                compress_config = config.get_compress_config()
                compress_trigger_mb = compress_config["max_size_mb"]
            except Exception:
                compress_trigger_mb = 5  # 默认5MB

            if file_size > compress_trigger_mb * 1024 * 1024:
                success, old_size, new_size = compress_image(file_path)
                if success:
                    logger.info(f"图片已压缩: {old_size} -> {new_size} bytes")

        return True, filename, file_path

    except Exception as e:
        logger.info(f"图片上传失败: {str(e)}")
        return False, f"上传失败: {str(e)}", None


def get_file_url(filename, base_url=None):
    """
    获取文件访问URL

    Args:
        filename: 文件名
        base_url: 基础URL，如果为None则使用app配置

    Returns:
        str: 文件访问URL
    """
    if base_url is None:
        try:
            from app.utils.admin_helpers import get_models

            models = get_models(["get_base_url"])
            if models and models.get("get_base_url"):
                base_url = models["get_base_url"]()
            else:
                base_url = "/media/original"
        except Exception:
            base_url = "/media/original"

    return f"{base_url}/{filename}"
