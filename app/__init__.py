# -*- coding: utf-8 -*-
"""
Flask应用初始化
"""

import logging

logger = logging.getLogger(__name__)
import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# 支持从.env文件加载环境变量
try:
    from dotenv import load_dotenv

    load_dotenv()  # 自动加载.env文件
except ImportError:
    # 如果没有安装python-dotenv，忽略
    pass

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)

    # 配置
    # SECRET_KEY必须从环境变量读取，生产环境不允许使用默认值
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        is_production = (
            os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENV") == "production"
        )
        if is_production:
            raise ValueError(
                "❌ 安全错误: 生产环境必须设置SECRET_KEY环境变量！\n"
                "请设置环境变量: export SECRET_KEY='your-secret-key-here'\n"
                "或创建.env文件: SECRET_KEY=your-secret-key-here"
            )
        else:
            # 开发环境可以使用默认值，但会警告
            import warnings

            warnings.warn(
                "⚠️ 警告: 使用默认SECRET_KEY，仅用于开发环境！\n"
                "生产环境必须设置SECRET_KEY环境变量。",
                UserWarning,
            )
            secret_key = "change-me-in-production"
    app.config["SECRET_KEY"] = secret_key
    database_url = os.environ.get("DATABASE_URL", "sqlite:///pet_painting.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Redis缓存配置（可选）
    app.config["REDIS_HOST"] = os.environ.get("REDIS_HOST", "localhost")
    app.config["REDIS_PORT"] = int(os.environ.get("REDIS_PORT", 6379))
    app.config["REDIS_DB"] = int(os.environ.get("REDIS_DB", 0))
    app.config["REDIS_PASSWORD"] = os.environ.get("REDIS_PASSWORD", None)

    # 根据数据库类型设置不同的连接选项
    if database_url.startswith("postgresql"):
        # PostgreSQL连接选项
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,  # 连接前检查连接是否有效
            "pool_recycle": 3600,  # 1小时后回收连接
        }
    else:
        # SQLite连接选项
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"timeout": 20, "check_same_thread": False, "isolation_level": None}
        }
    app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "uploads")
    app.config["FINAL_FOLDER"] = os.environ.get("FINAL_FOLDER", "final_works")
    app.config["HD_FOLDER"] = os.environ.get("HD_FOLDER", "hd_images")
    app.config["WATERMARK_FOLDER"] = os.environ.get("WATERMARK_FOLDER", "static/images/shuiyin")
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB

    # Proxy headers support
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # 响应压缩（gzip）
    try:
        from flask_compress import Compress

        compress = Compress()
        compress.init_app(app)
        logger.info("✅ 响应压缩（gzip）已启用")
    except ImportError:
        # 如果没有安装flask-compress，使用werkzeug的gzip压缩
        try:
            from werkzeug.middleware.gzip import GzipMiddleware

            app.wsgi_app = GzipMiddleware(app.wsgi_app, compresslevel=6, minimum_size=500)
            logger.info("✅ 响应压缩（werkzeug gzip）已启用")
        except Exception as e:
            logger.warning(f"⚠️  响应压缩未启用: {e}")

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    # 注册Blueprint
    try:
        from app.routes.miniprogram import miniprogram_bp
        from app.routes.payment import payment_bp

        app.register_blueprint(payment_bp)
        app.register_blueprint(miniprogram_bp)

        logger.info("✅ 路由Blueprint已注册：payment_bp, miniprogram_bp")
    except ImportError as e:
        logger.warning(f"路由Blueprint注册失败: {e}")
        # 不影响应用启动，继续执行

    return app
