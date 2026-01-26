# -*- coding: utf-8 -*-
"""
Flask应用初始化
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pet_painting.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'timeout': 20,
            'check_same_thread': False,
            'isolation_level': None
        }
    }
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['FINAL_FOLDER'] = os.environ.get('FINAL_FOLDER', 'final_works')
    app.config['HD_FOLDER'] = os.environ.get('HD_FOLDER', 'hd_images')
    app.config['WATERMARK_FOLDER'] = os.environ.get('WATERMARK_FOLDER', 'static/images/shuiyin')
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB
    
    # Proxy headers support
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # 注册Blueprint
    try:
        from app.routes.payment import payment_bp, user_bp
        from app.routes.miniprogram import miniprogram_bp
        
        app.register_blueprint(payment_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(miniprogram_bp)
        
        print("✅ 路由Blueprint已注册：payment_bp, user_bp, miniprogram_bp")
    except ImportError as e:
        print(f"⚠️  路由Blueprint注册失败: {e}")
        # 不影响应用启动，继续执行
    
    return app
