#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建代码模块化目录结构
为代码重构做准备
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"

# 需要创建的目录结构
DIRECTORY_STRUCTURE = {
    "app": [
        "routes",
        "services",
        "utils",
    ],
    "app/routes": [],
    "app/services": [],
    "app/utils": [],
}

# 需要创建的文件模板
FILE_TEMPLATES = {
    "app/__init__.py": '''# -*- coding: utf-8 -*-
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
    
    # 注册Blueprint（将在后续步骤中添加）
    # from app.routes import admin_bp, miniprogram_bp, order_bp, payment_bp
    # app.register_blueprint(admin_bp)
    # app.register_blueprint(miniprogram_bp)
    # app.register_blueprint(order_bp)
    # app.register_blueprint(payment_bp)
    
    return app
''',
    
    "app/routes/__init__.py": '''# -*- coding: utf-8 -*-
"""
路由模块
"""
''',
    
    "app/routes/admin.py": '''# -*- coding: utf-8 -*-
"""
管理后台路由
从 test_server.py 迁移管理后台相关路由
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# TODO: 从 test_server.py 迁移以下路由：
# - /admin/dashboard
# - /admin/order/<id>
# - /admin/styles
# - /admin/sizes
# - /admin/homepage
# - /admin/works-gallery
# - /admin/photo-signups
# - /admin/merchants
# - /admin/orders/export
''',
    
    "app/routes/miniprogram.py": '''# -*- coding: utf-8 -*-
"""
小程序API路由
从 test_server.py 迁移小程序相关API
"""
from flask import Blueprint

miniprogram_bp = Blueprint('miniprogram', __name__, url_prefix='/api/miniprogram')

# TODO: 从 test_server.py 迁移以下路由：
# - /api/miniprogram/products
# - /api/miniprogram/styles
# - /api/miniprogram/banners
# - /api/miniprogram/orders (POST)
# - /api/miniprogram/orders (GET)
# - /api/miniprogram/order/<order_number>
# - /api/miniprogram/order/qrcode
# - /api/miniprogram/order/check
# - /api/miniprogram/order/upload
# - /api/miniprogram/upload
# - /api/user/openid
''',
    
    "app/routes/order.py": '''# -*- coding: utf-8 -*-
"""
订单相关路由
从 test_server.py 迁移订单相关路由
"""
from flask import Blueprint

order_bp = Blueprint('order', __name__)

# TODO: 从 test_server.py 迁移以下路由：
# - /order
# - /order/<order_id>
# - /api/order/<order_id>/logistics
''',
    
    "app/routes/payment.py": '''# -*- coding: utf-8 -*-
"""
支付相关路由
从 test_server.py 迁移支付相关路由
"""
from flask import Blueprint

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# TODO: 从 test_server.py 迁移以下路由：
# - /api/payment/create
# - /api/payment/notify
''',
    
    "app/services/__init__.py": '''# -*- coding: utf-8 -*-
"""
业务逻辑服务
"""
''',
    
    "app/services/order_service.py": '''# -*- coding: utf-8 -*-
"""
订单业务逻辑服务
从 test_server.py 迁移订单相关业务逻辑
"""
# TODO: 从 test_server.py 迁移以下函数：
# - 订单创建逻辑
# - 订单状态更新逻辑
# - 订单查询逻辑
# - 订单关联加盟商逻辑
''',
    
    "app/services/payment_service.py": '''# -*- coding: utf-8 -*-
"""
支付业务逻辑服务
从 test_server.py 迁移支付相关业务逻辑
"""
# TODO: 从 test_server.py 迁移以下函数：
# - 微信支付签名生成
# - 支付订单创建
# - 支付回调处理
# - 支付状态验证
''',
    
    "app/utils/__init__.py": '''# -*- coding: utf-8 -*-
"""
工具函数
"""
''',
    
    "app/utils/helpers.py": '''# -*- coding: utf-8 -*-
"""
通用工具函数
从 test_server.py 迁移通用工具函数
"""
# TODO: 从 test_server.py 迁移以下函数：
# - _parse_shipping_info
# - _get_product_id_from_size
# - generate_nonce_str
# - 其他辅助函数
''',
    
    "app/utils/image_utils.py": '''# -*- coding: utf-8 -*-
"""
图片处理工具函数
从 test_server.py 迁移图片处理相关函数
"""
# TODO: 从 test_server.py 迁移以下函数：
# - 图片上传处理
# - 图片压缩
# - 水印添加
# - 图片格式转换
''',
    
    "app/models.py": '''# -*- coding: utf-8 -*-
"""
数据库模型
从 test_server.py 迁移所有数据库模型类
"""
from app import db

# TODO: 从 test_server.py 迁移以下模型类（25个）：
# - Product
# - ProductSize
# - ProductSizePetOption
# - ProductImage
# - ProductStyleCategory
# - ProductCustomField
# - StyleCategory
# - StyleImage
# - HomepageBanner
# - WorksGallery
# - HomepageConfig
# - User
# - UserVisit
# - Order
# - OrderImage
# - PhotoSignup
# - PromotionUser
# - Commission
# - Withdrawal
# - PromotionTrack
# - Coupon
# - UserCoupon
# - FranchiseeAccount
# - FranchiseeRecharge
# - SelfieMachine
''',
}

def create_directories():
    """创建目录结构"""
    print("📁 创建目录结构...")
    for base_dir, subdirs in DIRECTORY_STRUCTURE.items():
        dir_path = PROJECT_ROOT / base_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {base_dir}/")
        
        for subdir in subdirs:
            subdir_path = dir_path / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {base_dir}/{subdir}/")

def create_files():
    """创建文件模板"""
    print()
    print("📄 创建文件模板...")
    for file_path, content in FILE_TEMPLATES.items():
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print(f"  ⚠️  文件已存在，跳过: {file_path}")
        else:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ {file_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("创建代码模块化目录结构")
    print("=" * 60)
    print()
    
    create_directories()
    create_files()
    
    print()
    print("=" * 60)
    print("✅ 目录结构创建完成！")
    print("=" * 60)
    print()
    print("📋 下一步：")
    print("  1. 查看 app/ 目录结构")
    print("  2. 按照 代码拆分方案.md 逐步迁移代码")
    print("  3. 每迁移一个模块，测试确保功能正常")
    print()

if __name__ == "__main__":
    main()
