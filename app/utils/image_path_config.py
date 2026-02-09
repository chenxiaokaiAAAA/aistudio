# -*- coding: utf-8 -*-
"""
图片路径配置管理模块
统一管理所有图片存储路径，支持从数据库读取配置
支持未来切换到OSS存储
"""

import logging

logger = logging.getLogger(__name__)
import os
import sys

from app.utils.config_loader import get_config_value


class ImagePathConfig:
    """图片路径配置管理类"""

    # 配置键定义
    CONFIG_KEYS = {
        "upload_folder": "image_path_upload_folder",
        "final_folder": "image_path_final_folder",
        "hd_folder": "image_path_hd_folder",
        "watermark_folder": "image_path_watermark_folder",
        "static_folder": "image_path_static_folder",
        "storage_type": "image_storage_type",  # 'local' 或 'oss'
        "oss_bucket": "image_oss_bucket",
        "oss_endpoint": "image_oss_endpoint",
        "oss_access_key": "image_oss_access_key",
        "oss_secret_key": "image_oss_secret_key",
        "oss_domain": "image_oss_domain",  # OSS自定义域名
        # 图片压缩配置
        "compress_max_size_mb": "image_compress_max_size_mb",  # 超过此大小才压缩（MB）
        "compress_max_dimension": "image_compress_max_dimension",  # 压缩后最大尺寸（像素）
        "compress_quality": "image_compress_quality",  # JPEG压缩质量（1-100）
        "thumbnail_max_size": "image_thumbnail_max_size",  # 缩略图最大尺寸（像素）
        "thumbnail_quality": "image_thumbnail_quality",  # 缩略图质量（1-100）
        "auto_compress": "image_auto_compress",  # 是否自动压缩（true/false）
        "auto_thumbnail": "image_auto_thumbnail",  # 是否自动生成缩略图（true/false）
    }

    def __init__(self, app=None, db=None, AIConfig=None):
        """
        初始化图片路径配置

        Args:
            app: Flask应用实例
            db: 数据库实例（可选）
            AIConfig: AIConfig模型类（可选）
        """
        self.app = app
        self.db = db
        self.AIConfig = AIConfig
        self._cache = {}

    def _get_db_objects(self):
        """获取数据库对象"""
        if not self.db or not self.AIConfig:
            if "test_server" in sys.modules:
                test_server_module = sys.modules["test_server"]
                if hasattr(test_server_module, "db"):
                    self.db = test_server_module.db
                if hasattr(test_server_module, "AIConfig"):
                    self.AIConfig = test_server_module.AIConfig
        return self.db, self.AIConfig

    def get_config(self, key, default_value=None):
        """从数据库获取配置值"""
        config_key = self.CONFIG_KEYS.get(key, key)
        db, AIConfig = self._get_db_objects()
        return get_config_value(config_key, default_value, db, AIConfig)

    def get_upload_folder(self):
        """获取上传文件夹路径"""
        if "upload_folder" not in self._cache:
            # 优先从数据库读取，其次从app.config，最后使用默认值
            value = self.get_config("upload_folder")
            if not value and self.app:
                value = self.app.config.get("UPLOAD_FOLDER", "uploads")
            if not value:
                value = "uploads"
            self._cache["upload_folder"] = value
        return self._cache["upload_folder"]

    def get_final_folder(self):
        """获取完成效果图文件夹路径"""
        if "final_folder" not in self._cache:
            value = self.get_config("final_folder")
            if not value and self.app:
                value = self.app.config.get("FINAL_FOLDER", "final_works")
            if not value:
                value = "final_works"
            self._cache["final_folder"] = value
        return self._cache["final_folder"]

    def get_hd_folder(self):
        """获取高清图文件夹路径"""
        if "upload_folder" not in self._cache:
            value = self.get_config("hd_folder")
            if not value and self.app:
                value = self.app.config.get("HD_FOLDER", "hd_images")
            if not value:
                value = "hd_images"
            self._cache["hd_folder"] = value
        return self._cache["hd_folder"]

    def get_watermark_folder(self):
        """获取水印文件夹路径"""
        if "watermark_folder" not in self._cache:
            value = self.get_config("watermark_folder")
            if not value and self.app:
                value = self.app.config.get("WATERMARK_FOLDER", "static/images/shuiyin")
            if not value:
                value = "static/images/shuiyin"
            self._cache["watermark_folder"] = value
        return self._cache["watermark_folder"]

    def get_static_folder(self):
        """获取静态文件文件夹路径"""
        if "static_folder" not in self._cache:
            value = self.get_config("static_folder")
            if not value and self.app:
                value = self.app.config.get("STATIC_FOLDER", "static")
            if not value:
                value = "static"
            self._cache["static_folder"] = value
        return self._cache["static_folder"]

    def get_storage_type(self):
        """获取存储类型：'local' 或 'oss'"""
        return self.get_config("storage_type", "local")

    def get_oss_config(self):
        """获取OSS配置"""
        return {
            "bucket": self.get_config("oss_bucket", ""),
            "endpoint": self.get_config("oss_endpoint", ""),
            "access_key": self.get_config("oss_access_key", ""),
            "secret_key": self.get_config("oss_secret_key", ""),
            "domain": self.get_config("oss_domain", ""),
        }

    def get_image_path(self, folder_type, filename):
        """
        获取图片完整路径

        Args:
            folder_type: 文件夹类型 ('upload', 'final', 'hd', 'watermark', 'static')
            filename: 文件名

        Returns:
            完整路径
        """
        if folder_type == "upload":
            base_folder = self.get_upload_folder()
        elif folder_type == "final":
            base_folder = self.get_final_folder()
        elif folder_type == "hd":
            base_folder = self.get_hd_folder()
        elif folder_type == "watermark":
            base_folder = self.get_watermark_folder()
        elif folder_type == "static":
            base_folder = self.get_static_folder()
        else:
            base_folder = "uploads"

        return os.path.join(base_folder, filename)

    def get_image_url(self, folder_type, filename, base_url=None):
        """
        获取图片访问URL

        Args:
            folder_type: 文件夹类型
            filename: 文件名
            base_url: 基础URL（可选，从server_config获取）

        Returns:
            完整URL
        """
        storage_type = self.get_storage_type()

        if storage_type == "oss":
            # OSS存储
            oss_config = self.get_oss_config()
            if oss_config.get("domain"):
                return f"{oss_config['domain']}/{folder_type}/{filename}"
            elif oss_config.get("endpoint") and oss_config.get("bucket"):
                return f"https://{oss_config['bucket']}.{oss_config['endpoint']}/{folder_type}/{filename}"
        else:
            # 本地存储
            if not base_url:
                try:
                    from server_config import get_base_url

                    base_url = get_base_url()
                except Exception:
                    base_url = "http://localhost:8000"

            if folder_type == "upload":
                return f"{base_url}/media/original/{filename}"
            elif folder_type == "final":
                return f"{base_url}/media/final/{filename}"
            elif folder_type == "hd":
                return f"{base_url}/media/hd/{filename}"
            elif folder_type == "watermark":
                return f"{base_url}/static/images/shuiyin/{filename}"
            elif folder_type == "static":
                return f"{base_url}/static/{filename}"

        return f"{base_url}/media/{filename}"

    def clear_cache(self):
        """清除缓存"""
        self._cache = {}

    def get_compress_config(self):
        """获取图片压缩配置"""
        return {
            "max_size_mb": float(self.get_config("compress_max_size_mb", 5)),  # 默认5MB
            "max_dimension": int(self.get_config("compress_max_dimension", 1920)),  # 默认1920px
            "quality": int(self.get_config("compress_quality", 85)),  # 默认85
            "auto_compress": self.get_config("auto_compress", "true").lower() == "true",  # 默认启用
        }

    def get_thumbnail_config(self):
        """获取缩略图配置"""
        return {
            "max_size": int(self.get_config("thumbnail_max_size", 1920)),  # 默认1920px
            "quality": int(self.get_config("thumbnail_quality", 85)),  # 默认85
            "auto_thumbnail": self.get_config("auto_thumbnail", "true").lower()
            == "true",  # 默认启用
        }

    def get_all_paths(self):
        """获取所有路径配置"""
        return {
            "upload_folder": self.get_upload_folder(),
            "final_folder": self.get_final_folder(),
            "hd_folder": self.get_hd_folder(),
            "watermark_folder": self.get_watermark_folder(),
            "static_folder": self.get_static_folder(),
            "storage_type": self.get_storage_type(),
            "oss_config": self.get_oss_config() if self.get_storage_type() == "oss" else None,
            "compress_config": self.get_compress_config(),
            "thumbnail_config": self.get_thumbnail_config(),
        }


# 全局实例（延迟初始化）
_image_path_config = None


def get_image_path_config(app=None, db=None, AIConfig=None):
    """获取图片路径配置实例（单例模式）"""
    global _image_path_config
    if _image_path_config is None:
        _image_path_config = ImagePathConfig(app, db, AIConfig)
    elif app and not _image_path_config.app:
        _image_path_config.app = app
    return _image_path_config
