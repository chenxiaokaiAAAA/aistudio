# 测试服务器 - test_server.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, session, send_file, make_response, flash
import csv
import io
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import shutil
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import zipfile
from PIL import Image, ImageDraw, ImageFont
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import zipfile
from io import BytesIO
import time
import requests
import hashlib
import random
import string
import xml.etree.ElementTree as ET
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import re
import unicodedata
import logging

# 支持从.env文件加载环境变量（必须在其他导入之前）
try:
    from dotenv import load_dotenv
    import os
    # 确保从项目根目录加载.env文件
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)  # 明确指定.env文件路径，覆盖现有环境变量
        db_url = os.environ.get('DATABASE_URL', '')
        if db_url and 'postgresql://' in db_url:
            print(f"✅ 已加载 .env 文件，数据库: PostgreSQL")
        elif db_url:
            print(f"✅ 已加载 .env 文件，数据库: {db_url[:30]}...")
        else:
            print("✅ 已加载 .env 文件（但未设置DATABASE_URL）")
    else:
        print(f"⚠️  .env 文件不存在: {env_path}")
except ImportError:
    # 如果没有安装python-dotenv，忽略
    print("⚠️  未安装 python-dotenv，无法自动加载 .env 文件")
    print("   建议运行: pip install python-dotenv")
except Exception as e:
    import traceback
    print(f"⚠️  加载 .env 文件时出错: {str(e)}")
    print(traceback.format_exc())

# 导入冲印系统相关模块
try:
    from printer_config import PRINTER_SYSTEM_CONFIG, SIZE_MAPPING
    from printer_client import PrinterSystemClient
    PRINTER_SYSTEM_AVAILABLE = True
except ImportError:
    PRINTER_SYSTEM_AVAILABLE = False
    print("警告: 冲印系统模块未找到，自动传片功能将不可用")

# 导入同步配置模块
try:
    from sync_config_routes import sync_bp
    SYNC_CONFIG_AVAILABLE = True
except ImportError:
    SYNC_CONFIG_AVAILABLE = False
    print("警告: 同步配置模块未找到，自动同步功能将不可用")

# 导入订单通知模块
try:
    from order_notification import notify_new_order, notify_paid_order
    ORDER_NOTIFICATION_AVAILABLE = True
except ImportError:
    ORDER_NOTIFICATION_AVAILABLE = False
    print("警告: 订单通知模块未找到，提醒功能将不可用")

# 导入微信通知模块
try:
    from wechat_notification import send_order_notification as wechat_notify
    WECHAT_NOTIFICATION_AVAILABLE = True
except ImportError:
    WECHAT_NOTIFICATION_AVAILABLE = False
    print("警告: 微信通知模块未找到，微信提醒功能将不可用")

# 导入服务器配置
try:
    from server_config import get_base_url as _server_config_get_base_url, \
                             get_media_url as _server_config_get_media_url, \
                             get_static_url as _server_config_get_static_url, \
                             get_notify_url as _server_config_get_notify_url, \
                             get_api_base_url as _server_config_get_api_base_url
    SERVER_CONFIG_AVAILABLE = True
except ImportError:
    SERVER_CONFIG_AVAILABLE = False
    # 如果配置不可用，使用默认值
    def _server_config_get_base_url():
        return 'http://192.168.2.54:8000'
    def _server_config_get_media_url():
        return 'http://192.168.2.54:8000/media'
    def _server_config_get_static_url():
        return 'http://192.168.2.54:8000/static'
    def _server_config_get_notify_url():
        return 'http://192.168.2.54:8000/api/payment/notify'
    def _server_config_get_api_base_url():
        return 'http://192.168.2.54:8000/api'
    print("警告: 服务器配置模块未找到，使用默认本地地址")

# 定义全局函数（将在数据库初始化后重新定义以优先使用数据库配置）
def get_base_url():
    """获取服务器基础URL（优先从数据库读取，否则使用server_config）"""
    try:
        # 动态获取AIConfig，避免在导入时未定义
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'MODELS_AVAILABLE') and test_server_module.MODELS_AVAILABLE:
                if hasattr(test_server_module, 'AIConfig'):
                    AIConfig = test_server_module.AIConfig
                    if hasattr(AIConfig, 'query'):
                        config = AIConfig.query.filter_by(config_key='server_base_url').first()
                        if config and config.config_value:
                            return config.config_value
    except:
        pass
    return _server_config_get_base_url()

def get_media_url():
    """获取媒体文件URL（优先从数据库读取，否则使用server_config）"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'MODELS_AVAILABLE') and test_server_module.MODELS_AVAILABLE:
                if hasattr(test_server_module, 'AIConfig'):
                    AIConfig = test_server_module.AIConfig
                    if hasattr(AIConfig, 'query'):
                        config = AIConfig.query.filter_by(config_key='server_media_url').first()
                        if config and config.config_value:
                            return config.config_value
    except:
        pass
    return _server_config_get_media_url()

def get_static_url():
    """获取静态文件URL（优先从数据库读取，否则使用server_config）"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'MODELS_AVAILABLE') and test_server_module.MODELS_AVAILABLE:
                if hasattr(test_server_module, 'AIConfig'):
                    AIConfig = test_server_module.AIConfig
                    if hasattr(AIConfig, 'query'):
                        config = AIConfig.query.filter_by(config_key='server_static_url').first()
                        if config and config.config_value:
                            return config.config_value
    except:
        pass
    return _server_config_get_static_url()

def get_notify_url():
    """获取支付通知URL（优先从数据库读取，否则使用server_config）"""
    # 通知URL通常不需要从数据库读取，使用server_config即可
    return _server_config_get_notify_url()

def get_api_base_url():
    """获取API基础URL（优先从数据库读取，否则使用server_config）"""
    try:
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'MODELS_AVAILABLE') and test_server_module.MODELS_AVAILABLE:
                if hasattr(test_server_module, 'AIConfig'):
                    AIConfig = test_server_module.AIConfig
                    if hasattr(AIConfig, 'query'):
                        config = AIConfig.query.filter_by(config_key='server_api_url').first()
                        if config and config.config_value:
                            return config.config_value
    except:
        pass
    return _server_config_get_api_base_url()

# ⭐ 数据库模型将在db初始化后导入（见第587行之后）

# ⭐ 导入工具函数（从app.utils模块）
from app.utils.helpers import (
    generate_sign, verify_sign, dict_to_xml, xml_to_dict, generate_nonce_str,
    parse_shipping_info as _parse_shipping_info,
    get_product_id_from_size as _get_product_id_from_size,
    generate_promotion_code, generate_stable_promotion_code, generate_stable_user_id,
    validate_promotion_code,
    generate_coupon_code, validate_coupon_code, create_coupon,
    get_user_coupons, can_user_get_coupon, user_get_coupon,
    can_use_coupon, calculate_discount_amount, use_coupon,
    check_user_has_placed_order, check_user_eligible_for_commission,
    allowed_file,
    generate_production_info, generate_smart_filename, generate_smart_image_name,
    generate_qr_code
)
from app.utils.image_utils import add_watermark_to_image

# ⭐ 导入服务层函数（从app.services模块）
from app.services.order_service import (
    create_miniprogram_order,
    get_order_by_number,
    check_order_for_verification,
    upload_order_photos
)
from app.services.payment_service import (
    create_payment_order,
    handle_payment_notify,
    get_user_openid as get_user_openid_service
)

# 微信支付配置（默认值，建议在管理后台「小程序配置」中配置，以数据库为准）
WECHAT_PAY_CONFIG = {
    'appid': 'wxf5b325a2a0b55d9d',  # 小程序AppID（与 aistudio-小程序v2/project.config.json 保持一致）
    'mch_id': '1728339549',       # 商户号
    'api_key': 'Rebf8QfhS383srRkbO5PQoHeUm7qUIGT',  # 32位API密钥
    'notify_url': get_notify_url(),
    'app_secret': ''  # 小程序AppSecret，必须在管理后台「小程序配置」中填写，否则登录/手机号解密会失败
}

# ⭐ 微信支付辅助函数已迁移到 app.utils.helpers

app = Flask(__name__)
# Proxy headers (X-Forwarded-*) support when behind nginx/elb
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# 配置日志系统（在配置之前初始化）
try:
    from app.utils.logger_config import setup_logging
    setup_logging(app)
    logger = logging.getLogger(__name__)
    logger.info("✅ 日志系统已初始化")
except Exception as e:
    import warnings
    warnings.warn(f"日志系统初始化失败: {e}，使用基础日志配置", UserWarning)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

# Environment-driven configuration for production
# SECRET_KEY必须从环境变量读取，生产环境不允许使用默认值
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENV') == 'production'
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
            UserWarning
        )
        secret_key = 'change-me-in-production'
app.config['SECRET_KEY'] = secret_key
database_url = os.environ.get('DATABASE_URL', 'sqlite:///pet_painting.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 根据数据库类型设置不同的连接选项
if database_url.startswith('postgresql'):
    # PostgreSQL连接选项
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # 连接前检查连接是否有效
        'pool_recycle': 3600,  # 1小时后回收连接
        'pool_size': 10,  # 连接池大小
        'max_overflow': 20  # 最大溢出连接数
    }
else:
    # SQLite连接选项（优化SQLite数据库连接配置，解决卡顿问题）
    # SQLite不支持连接池参数，只使用connect_args
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'timeout': 20,
            'check_same_thread': False,
            'isolation_level': None  # 自动提交模式，减少锁竞争
        }
    }
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['FINAL_FOLDER'] = os.environ.get('FINAL_FOLDER', 'final_works')
app.config['HD_FOLDER'] = os.environ.get('HD_FOLDER', 'hd_images')  # 高清图片文件夹
app.config['WATERMARK_FOLDER'] = os.environ.get('WATERMARK_FOLDER', 'static/images/shuiyin')  # 水印图片文件夹
# Upload size limit (e.g., 20MB). Match reverse proxy setting like nginx client_max_body_size
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH_MB', '100')) * 1024 * 1024

# Secure cookies in production
is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENV') == 'production'
use_https = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
# 只在真正使用HTTPS时才启用Secure Cookie
# HTTP环境下禁用Secure Cookie（否则Cookie无法设置，导致登录失败）
if is_production and use_https:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
else:
    # HTTP环境下禁用Secure Cookie
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FINAL_FOLDER'], exist_ok=True)
os.makedirs(app.config['HD_FOLDER'], exist_ok=True)
os.makedirs(app.config['WATERMARK_FOLDER'], exist_ok=True)

# 添加模板上下文处理器，让所有模板都能访问服务器配置和品牌名称
@app.context_processor
def inject_server_config():
    """注入服务器配置和品牌名称到所有模板"""
    import json
    from flask_login import current_user
    
    def get_user_page_permissions(user):
        """获取用户的页面权限列表"""
        if not user:
            return []
        if user.role == 'admin':
            return None  # None表示拥有所有权限
        if user.role == 'operator':
            page_permissions = getattr(user, 'page_permissions', None)
            if page_permissions:
                try:
                    return json.loads(page_permissions)
                except:
                    return []
            return []
        return []
    
    def has_page_permission(permission_id):
        """检查当前用户是否有指定权限"""
        if not current_user or not current_user.is_authenticated:
            return False
        if current_user.role == 'admin':
            return True
        if current_user.role == 'operator':
            permissions = get_user_page_permissions(current_user)
            if permissions is None:  # admin
                return True
            return permission_id in permissions
        return False
    
    try:
        from server_config import get_base_url, get_media_url, get_static_url, get_api_base_url
        from app.utils.config_loader import get_brand_name
        return {
            'server_base_url': get_base_url(),
            'server_media_url': get_media_url(),
            'server_static_url': get_static_url(),
            'server_api_url': get_api_base_url(),
            'brand_name': get_brand_name(),
            'get_user_page_permissions': get_user_page_permissions,
            'has_page_permission': has_page_permission
        }
    except ImportError:
        # 如果配置不可用，使用默认值
        from app.utils.config_loader import get_brand_name
        return {
            'server_base_url': 'http://192.168.2.54:8000',
            'server_media_url': 'http://192.168.2.54:8000/media',
            'server_static_url': 'http://192.168.2.54:8000/static',
            'server_api_url': 'http://192.168.2.54:8000/api',
            'brand_name': get_brand_name(),
            'get_user_page_permissions': get_user_page_permissions,
            'has_page_permission': has_page_permission
        }

# ⭐ 图片处理函数已迁移到 app.utils.image_utils

# ⭐ 文件名生成函数已迁移到 app.utils.helpers

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'  # 使用蓝图名称前缀

# ⭐ 导入数据库模型（在db初始化后）
# 注意：需要先设置models模块的db引用，然后再导入模型类
try:
    # 注意：导入models模块时会立即执行类定义，此时db.Model会被访问
    # 所以我们需要在导入前设置db，但导入时就会执行类定义
    # 解决方案：使用延迟绑定的DBProxy，在访问时动态获取db
    # 关键：确保test_server模块已经在sys.modules中，这样_get_db()就能找到db
    import sys
    # 如果当前模块是__main__，也注册为test_server，这样_get_db()能找到db
    if __name__ == '__main__':
        sys.modules['test_server'] = sys.modules[__name__]
    
    # 先导入models模块（会执行类定义，但DBProxy会在访问时通过_get_db()获取db）
    import app.models as models_module
    # 立即设置db实例（替换DBProxy为实际的db，这样后续访问就直接使用db）
    models_module.set_db(db)
    # 现在导入所有模型类（此时db已经可用）
    from app.models import (
        ProductCategory, ProductSubcategory,  # 产品分类模型
        Product, ProductSize, ProductSizePetOption, ProductImage, ProductStyleCategory, ProductCustomField, ProductBonusWorkflow,
        StyleCategory, StyleSubcategory, StyleImage,
        HomepageBanner, WorksGallery, HomepageConfig, HomepageCategoryNav, HomepageProductSection, HomepageActivityBanner,
        User, UserVisit, OperationLog,
        Order, OrderImage,
        PromotionUser, Commission, Withdrawal, PromotionTrack,
        Coupon, UserCoupon, ShareRecord, GrouponPackage,
        FranchiseeAccount, FranchiseeRecharge, SelfieMachine, StaffUser,
        AITask, AIConfig,  # 新增AI相关模型
        MeituAPIConfig, MeituAPIPreset, MeituAPICallLog,  # 美图API相关模型
        APIProviderConfig, APITemplate,  # 新增云端API服务商相关模型
        PollingConfig,  # 新增轮询配置模型
        ShopProduct, ShopProductImage, ShopProductSize, ShopOrder,  # 新增商城相关模型
        SelectionOrder,  # 选片订单（关联产品馆）
        PrintSizeConfig,  # 新增打印配置模型
        MockupTemplate, MockupTemplateProduct,  # 样机套图模型
        _sanitize_style_code, _build_style_code, _ensure_unique_style_code
    )
    MODELS_AVAILABLE = True
    print("✅ 数据库模型模块已加载")
except ImportError as e:
    MODELS_AVAILABLE = False
    print(f"⚠️  数据库模型模块未找到: {e}")
    import traceback
    traceback.print_exc()
    # 如果导入失败，将在后面定义模型类（向后兼容）
    # 注意：不要在这里定义模型，因为可能导致重复定义错误
except AttributeError as e:
    MODELS_AVAILABLE = False
    print(f"⚠️  数据库模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    # 注意：不要在这里定义模型，因为可能导致重复定义错误
login_manager.remember_cookie_duration = 60 * 60 * 24 * 14  # 14天（秒）

# 创建线程池用于异步处理
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async_worker")

# 异步任务队列
async_queue = queue.Queue()

def async_worker():
    """异步工作线程"""
    while True:
        try:
            task = async_queue.get(timeout=1)
            if task is None:
                break
            func, args, kwargs = task
            func(*args, **kwargs)
            async_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"异步任务执行失败: {e}")

# 启动异步工作线程
async_thread = threading.Thread(target=async_worker, daemon=True)
async_thread.start()

def submit_async_task(func, *args, **kwargs):
    """提交异步任务"""
    async_queue.put((func, args, kwargs))

# 注册蓝图
if SYNC_CONFIG_AVAILABLE:
    app.register_blueprint(sync_bp, url_prefix='')

# 蓝图注册将在模型定义后执行

# 产品配置模型（支持多尺寸规格）
# ⭐ 数据库模型已迁移到 app/models.py

if not MODELS_AVAILABLE:
    # 向后兼容：如果导入失败，在这里定义模型类
    # 但要注意：如果部分模型已经导入，这里定义会导致重复定义错误
    # 所以暂时注释掉，如果确实需要，可以在这里定义缺失的模型
    print("⚠️  警告：数据库模型导入失败，但为了避免重复定义错误，不在这里定义模型")
    print("⚠️  请检查 app/models.py 文件是否正确，并确保所有模型都已定义")
    pass
    # class Product(db.Model):
    #     __tablename__ = 'products'
    #     id = db.Column(db.Integer, primary_key=True)
    #     code = db.Column(db.String(50), unique=True, nullable=False)
    #     name = db.Column(db.String(100), nullable=False)
    #     description = db.Column(db.Text)
    #     image_url = db.Column(db.String(500))
    #     is_active = db.Column(db.Boolean, default=True)
    #     sort_order = db.Column(db.Integer, default=0)
    #     created_at = db.Column(db.DateTime, default=datetime.now)
    # ... 其他模型类定义（仅在导入失败时使用）

# 尺寸显示名过滤器：根据 code 显示配置名称，若无配置则回退到默认文案
@app.template_filter('size_name')
def size_name_filter(code):
    if not code:
        return '未选择'
    
    try:
        # 1. 直接通过产品名称查找（小程序发送的完整产品名称）
        size = ProductSize.query.filter_by(size_name=code).first()
        if size:
            return f"{size.size_name} (¥{size.price})"
    except Exception as e:
        print(f"尺寸查找异常: {e}")
        pass
    
    try:
        # 查找对应的尺寸配置 - 通过printer_product_id查找
        size = ProductSize.query.filter_by(printer_product_id=code).first()
        if size:
            return f"{size.size_name} (¥{size.price})"
    except Exception:
        pass
    
    # 如果没找到，尝试通过ID查找
    try:
        if code and code.isdigit():
            size = ProductSize.query.filter_by(id=int(code)).first()
            if size:
                return f"{size.size_name} (¥{size.price})"
    except Exception:
        pass
    
    # 特殊处理：如果code是数字字符串（如"1", "2"等），通过SIZE_MAPPING查找
    if code and code.isdigit():
        try:
            from printer_config import SIZE_MAPPING
            if code in SIZE_MAPPING:
                mapping = SIZE_MAPPING[code]
                printer_product_id = mapping['product_id']
                # 通过printer_product_id查找对应的尺寸
                size = ProductSize.query.filter_by(printer_product_id=printer_product_id).first()
                if size:
                    return f"{size.size_name} (¥{size.price})"
        except Exception:
            pass
    
    # 特殊处理：尝试通过上下文查找对应的产品尺寸
    try:
        # 尝试从请求上下文中获取订单信息
        from flask import request
        if hasattr(request, 'view_args') and 'order_id' in request.view_args:
            order_id = request.view_args['order_id']
            order = Order.query.get(order_id)
            if order and order.product_name:
                # 根据订单的产品名称查找对应的产品
                product = Product.query.filter_by(name=order.product_name).first()
                if product:
                    # 查找该产品的第一个尺寸
                    size = ProductSize.query.filter_by(product_id=product.id).first()
                    if size:
                        return f"{size.size_name} (¥{size.price})"
    except Exception:
        pass
    
    # 特殊处理：如果code是"1"或其他数字，尝试查找产品库中的尺寸
    if code and code.isdigit():
        try:
            # 查找第一个可用的产品尺寸
            size = ProductSize.query.filter_by(is_active=True).first()
            if size:
                return f"{size.size_name} (¥{size.price})"
        except Exception:
            pass
    
    # 处理新的尺寸格式（如 "30x40"）
    if code and 'x' in str(code) and not code.endswith('cm'):
        return f"{code}cm"
    
    # 兼容旧格式 - 但优先尝试从产品库中查找
    old_format_map = {
        'small': '小型 (30x40cm)',
        'medium': '中型 (40x50cm)', 
        'large': '大型 (50x70cm)',
        'xlarge': '超大型 (70x100cm)',
        'keychain': '钥匙扣',
        'phonecase': '手机壳',
        'pillow': '抱枕',
        'painting': '挂画'
    }
    
    # 如果是旧格式代码，尝试查找产品库中的实际尺寸
    if code in old_format_map:
        try:
            # 查找产品库中的实际尺寸
            size = ProductSize.query.filter_by(is_active=True).first()
            if size:
                return f"{size.size_name} (¥{size.price})"
        except Exception:
            pass
        
        # 如果没找到产品尺寸，返回旧格式的显示
        return old_format_map[code]
    
    return code or ''

# JSON解析过滤器
@app.template_filter('from_json')
def from_json_filter(json_string):
    """将JSON字符串解析为Python对象"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return {}

# 产品ID过滤器
@app.template_filter('product_id')
def product_id_filter(size):
    """根据尺寸信息获取产品ID"""
    return _get_product_id_from_size(size)

# ⭐ 数据库模型已迁移到 app/models.py

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册加盟商管理蓝图（在模型定义后）
def register_franchisee_blueprints():
    """注册加盟商相关蓝图"""
    try:
        from app.routes.franchisee import franchisee_bp
        app.register_blueprint(franchisee_bp)
        print("✅ 加盟商管理模块已加载")
    except ImportError as e:
        print(f"⚠️  加盟商管理模块加载失败: {e}")
    
    try:
        from franchisee_qrcode_generator import qrcode_bp
        app.register_blueprint(qrcode_bp)
        print("✅ 加盟商二维码生成模块已加载")
    except ImportError as e:
        print(f"⚠️  加盟商二维码生成模块加载失败: {e}")

# 文件上传辅助函数
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 立即注册蓝图（在模型定义后）
register_franchisee_blueprints()

# ⭐ 注册路由Blueprint（从app.routes模块）
try:
    from app.routes.payment import payment_bp
    from app.routes.miniprogram import miniprogram_bp
    from app.routes.miniprogram.refund import bp as miniprogram_refund_bp
    from app.routes.order import order_bp
    from app.routes.ai import ai_bp
    from app.routes.meitu import meitu_bp
    
    # 注册基础路由蓝图（必须优先注册）
    from app.routes.base import base_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.admin_orders import admin_orders_bp
    from app.routes.merchant import merchant_bp
    from app.routes.media import media_bp
    app.register_blueprint(base_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_orders_bp)
    app.register_blueprint(merchant_bp)
    app.register_blueprint(media_bp)
    
    # 注册选片页面蓝图
    try:
        from app.routes.photo_selection import photo_selection_bp
        app.register_blueprint(photo_selection_bp)
        print("✅ 选片页面蓝图已注册")
    except Exception as e:
        print(f"⚠️  选片页面蓝图注册失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 注册个人中心蓝图
    try:
        from app.routes.admin_profile import admin_profile_bp
        app.register_blueprint(admin_profile_bp)
        print("✅ 个人中心蓝图已注册")
    except Exception as e:
        print(f"⚠️  个人中心蓝图注册失败: {e}")
    
    # 注册仪表盘API蓝图
    try:
        from app.routes.admin_dashboard_api import admin_dashboard_api_bp
        app.register_blueprint(admin_dashboard_api_bp)
        print("✅ 仪表盘API蓝图已注册")
    except Exception as e:
        print(f"⚠️  仪表盘API蓝图注册失败: {e}")
    
    # 注册过期图片清理蓝图
    try:
        from app.routes.admin_image_cleanup import admin_image_cleanup_bp
        app.register_blueprint(admin_image_cleanup_bp)
        print("✅ 过期图片清理蓝图已注册")
    except Exception as e:
        print(f"⚠️  过期图片清理蓝图注册失败: {e}")
    
    # 注册其他业务蓝图
    app.register_blueprint(payment_bp)
    
    # 尝试注册用户API蓝图（如果导入失败，不影响其他功能）
    try:
        from app.routes.user_api import user_api_bp
        app.register_blueprint(user_api_bp)
        print("✅ 用户API蓝图已注册")
        # 验证路由是否注册成功
        with app.app_context():
            rules = [str(rule) for rule in app.url_map.iter_rules()]
            visit_routes = [r for r in rules if '/api/user/visit' in r]
            if visit_routes:
                print(f"✅ 访问记录路由已注册: {visit_routes}")
            else:
                print("⚠️  警告: /api/user/visit 路由未找到!")
    except Exception as e:
        print(f"⚠️  用户API蓝图注册失败: {e}")
        import traceback
        traceback.print_exc()
        print("   提示: 如果缺少Crypto模块，请运行: pip install pycryptodome")
    
    # 注册推广API蓝图
    try:
        from app.routes.promotion_api import promotion_api_bp
        app.register_blueprint(promotion_api_bp)
        print("✅ 推广API蓝图已注册")
    except Exception as e:
        print(f"⚠️  推广API蓝图注册失败: {e}")
    
    # 注册优惠券API蓝图
    try:
        from app.routes.coupon_api import coupon_api_bp
        app.register_blueprint(coupon_api_bp)
        print("✅ 优惠券API蓝图已注册")
    except Exception as e:
        print(f"⚠️  优惠券API蓝图注册失败: {e}")
    
    # 注册管理员优惠券API蓝图
    try:
        from app.routes.admin_coupon_api import admin_coupon_api_bp
        app.register_blueprint(admin_coupon_api_bp)
        print("✅ 管理员优惠券API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理员优惠券API蓝图注册失败: {e}")
    
    # 注册团购核销API蓝图
    try:
        from app.routes.admin_groupon_api import admin_groupon_api_bp
        app.register_blueprint(admin_groupon_api_bp)
        
        # 注册团购套餐配置API蓝图
        try:
            from app.routes.admin_groupon_package_api import admin_groupon_package_api_bp
            app.register_blueprint(admin_groupon_package_api_bp)
        except Exception as e:
            print(f"⚠️ 注册团购套餐配置API蓝图失败: {e}")
        
        # 注册团购核销记录页面蓝图
        try:
            from app.routes.admin_groupon_verify import bp as admin_groupon_verify_bp
            app.register_blueprint(admin_groupon_verify_bp)
            print("✅ 团购核销记录页面蓝图已注册")
        except Exception as e:
            print(f"⚠️ 注册团购核销记录页面蓝图失败: {e}")
        
        print("✅ 团购核销API蓝图已注册")
    except Exception as e:
        print(f"⚠️  团购核销API蓝图注册失败: {e}")
    
    # 注册支付管理蓝图
    try:
        from app.routes.admin_payment_management import bp as admin_payment_management_bp
        app.register_blueprint(admin_payment_management_bp)
        print("✅ 支付管理蓝图已注册")
    except Exception as e:
        print(f"⚠️  支付管理蓝图注册失败: {e}")
    
    # 注册退款审核API蓝图
    try:
        from app.routes.admin_refund_api import bp as admin_refund_api_bp
        app.register_blueprint(admin_refund_api_bp)
        print("✅ 退款审核API蓝图已注册")
    except Exception as e:
        print(f"⚠️  退款审核API蓝图注册失败: {e}")
    
    # 注册第三方团购核销API蓝图
    try:
        from app.routes.admin_third_party_groupon_api import admin_third_party_groupon_api_bp
        app.register_blueprint(admin_third_party_groupon_api_bp)
        print("✅ 第三方团购核销API蓝图已注册")
    except Exception as e:
        print(f"⚠️  第三方团购核销API蓝图注册失败: {e}")
    
    # 注册管理后台风格管理API蓝图
    try:
        from app.routes.admin_styles_api import admin_styles_api_bp
        app.register_blueprint(admin_styles_api_bp)
        print("✅ 管理后台风格管理API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台风格管理API蓝图注册失败: {e}")
    
    # 注册产品分类管理API蓝图
    try:
        from app.routes.admin_product_categories_api import admin_product_categories_api_bp
        app.register_blueprint(admin_product_categories_api_bp)
        print("✅ 产品分类管理API蓝图已注册")
    except Exception as e:
        print(f"⚠️  产品分类管理API蓝图注册失败: {e}")
    
    # 注册轮询配置API蓝图
    try:
        from app.routes.admin_polling_config_api import admin_polling_config_api_bp
        app.register_blueprint(admin_polling_config_api_bp)
        print("✅ 轮询配置API蓝图已注册")
    except Exception as e:
        print(f"⚠️  轮询配置API蓝图注册失败: {e}")
    
    # 注册Playground API蓝图
    try:
        from app.routes.playground_api import playground_api_bp
        app.register_blueprint(playground_api_bp)
        print("✅ Playground API蓝图已注册")
    except Exception as e:
        print(f"⚠️  Playground API蓝图注册失败: {e}")
    
    # 注册管理后台首页配置API蓝图
    try:
        from app.routes.admin_homepage_api import admin_homepage_api_bp
        app.register_blueprint(admin_homepage_api_bp)
        print("✅ 管理后台首页配置API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台首页配置API蓝图注册失败: {e}")
    
    # 注册管理后台小程序配置API蓝图
    try:
        from app.routes.admin_miniprogram_config_api import admin_miniprogram_config_api_bp
        app.register_blueprint(admin_miniprogram_config_api_bp)
        print("✅ 管理后台小程序配置API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台小程序配置API蓝图注册失败: {e}")
    
    # 注册管理后台推广管理API蓝图
    try:
        from app.routes.admin_promotion_api import admin_promotion_api_bp
        app.register_blueprint(admin_promotion_api_bp)
        print("✅ 管理后台推广管理API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台推广管理API蓝图注册失败: {e}")
    
    # 注册调试API蓝图（开发环境使用）
    try:
        from app.routes.debug_api import debug_api_bp
        app.register_blueprint(debug_api_bp)
        print("✅ 调试API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台推广管理API蓝图注册失败: {e}")
    
    # 注册管理后台用户管理API蓝图
    try:
        from app.routes.admin_users_api import admin_users_api_bp
        app.register_blueprint(admin_users_api_bp)
        print("✅ 管理后台用户管理API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台用户管理API蓝图注册失败: {e}")
    
    # 注册管理后台消息通知API蓝图
    try:
        from app.routes.admin_notification_api import admin_notification_api_bp
        app.register_blueprint(admin_notification_api_bp)
        print("✅ 管理后台消息通知API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台消息通知API蓝图注册失败: {e}")
    
    # 注册物流回调API蓝图
    try:
        from app.routes.logistics_api import logistics_api_bp
        app.register_blueprint(logistics_api_bp)
        print("✅ 物流回调API蓝图已注册")
    except Exception as e:
        print(f"⚠️  物流回调API蓝图注册失败: {e}")
    
    # 注册管理后台工具API蓝图
    try:
        from app.routes.admin_tools_api import admin_tools_api_bp
        app.register_blueprint(admin_tools_api_bp)
        print("✅ 管理后台工具API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台工具API蓝图注册失败: {e}")
    
    # 注册二维码生成API蓝图
    try:
        from app.routes.qrcode_api import qrcode_api_bp
        app.register_blueprint(qrcode_api_bp)
        print("✅ 二维码生成API蓝图已注册")
    except Exception as e:
        print(f"⚠️  二维码生成API蓝图注册失败: {e}")
    
    # 注册管理后台产品配置API蓝图
    try:
        from app.routes.admin_products_api import admin_products_bp
        app.register_blueprint(admin_products_bp)
        print("✅ 管理后台产品配置API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台产品配置API蓝图注册失败: {e}")
    
    # 注册管理后台商城管理API蓝图
    try:
        from app.routes.admin_shop_api import admin_shop_bp
        app.register_blueprint(admin_shop_bp)
        print("✅ 管理后台商城管理API蓝图已注册")
    except Exception as e:
        print(f"⚠️  管理后台商城管理API蓝图注册失败: {e}")

    # 注册样机套图管理API蓝图
    try:
        from app.routes.admin_mockup_api import admin_mockup_bp
        app.register_blueprint(admin_mockup_bp)
        print("✅ 样机套图管理API蓝图已注册")
    except Exception as e:
        print(f"⚠️  样机套图管理API蓝图注册失败: {e}")
    
    # 注册店员权限管理蓝图
    try:
        from app.routes.staff_permission import bp as staff_permission_bp
        app.register_blueprint(staff_permission_bp)
        print("✅ 店员权限管理蓝图已注册")
    except Exception as e:
        print(f"⚠️  店员权限管理蓝图注册失败: {e}")
    
    app.register_blueprint(miniprogram_bp)
    
    # 注册小程序退款申请API蓝图
    try:
        app.register_blueprint(miniprogram_refund_bp)
        print("✅ 小程序退款申请API蓝图已注册")
    except Exception as e:
        print(f"⚠️  小程序退款申请API蓝图注册失败: {e}")
    app.register_blueprint(order_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(meitu_bp)
    
    # 注册API服务商配置管理蓝图
    try:
        from app.routes.ai_provider import ai_provider_bp
        app.register_blueprint(ai_provider_bp)
        print("✅ API服务商配置管理模块已加载")
    except ImportError as e:
        print(f"⚠️  API服务商配置管理模块加载失败: {e}")
    
    print("✅ 路由Blueprint已注册：payment_bp, user_bp, miniprogram_bp, order_bp, ai_bp, meitu_bp, ai_provider_bp")

    # 注册 Swagger/OpenAPI 交互式文档（用 print 确保在 Gunicorn 日志中可见）
    try:
        from app.routes.swagger_api import init_swagger
        if init_swagger(app):
            print("✅ Swagger/OpenAPI 文档已启用: /docs, /apidocs")
        else:
            print("⚠️ Swagger/OpenAPI 文档未启用（请在 venv 中执行: pip install flasgger 后重启）")
    except Exception as e:
        print(f"⚠️  Swagger/OpenAPI 文档注册失败: {e}")
except ImportError as e:
    print(f"⚠️  路由Blueprint注册失败: {e}")
    import traceback
    traceback.print_exc()

# ==================== 已迁移模块说明 ====================
# 以下路由和功能已迁移到对应的蓝图模块：
# - 基础路由 → app.routes.base 和 app.routes.auth
# - 管理后台路由 → app.routes.admin
# - 订单路由 → app.routes.order 和 app.routes.admin_orders
# - 支付路由 → app.routes.payment (已迁移，以下路由已注释)
# - 商户路由 → app.routes.merchant
# - 媒体文件路由 → app.routes.media
# - 物流回调API → app.routes.logistics_api
# - 工具函数 → app.utils.helpers
# =====================================================

# ⚠️ 以下支付路由已迁移到 app.routes.payment，已注释
# ⚠️ 以下支付路由已迁移到 app.routes.payment，已注释
# ==================== 管理API接口 ====================
# 以下路由已迁移到对应的蓝图模块：
# - 用户openid路由 → app.routes.user_api
# - 小程序API → app.routes.miniprogram
# - 批量下载原图路由 → app.routes.media
# - 物流回调API → app.routes.logistics_api
# - 风格管理API → app.routes.admin_styles_api
# =====================================================

# 风格管理API和小程序API已迁移到对应的蓝图模块

# ⭐ 以下调试路由已迁移到 app.routes.debug_api，已删除：
# - debug_payment() → /api/debug/payment
# - test_coupons() → /api/coupons/test
# - debug_coupons() → /api/coupons/debug

def get_order_images(order_id):
    """获取订单图片列表"""
    order_images = OrderImage.query.filter_by(order_id=order_id).all()
    return [img.path for img in order_images]

# ==================== 已迁移模块说明 ====================
# - 首页管理API → app.routes.admin_homepage_api
# - 调试API → app.routes.debug_api
# =====================================================

# ⭐ 以下路由已迁移到 app.routes.debug_api，已删除：
# - get_example_images() → /api/example-images

# 清空测试数据路由（仅用于开发）
# 管理后台工具API已迁移到 app.routes.admin_tools_api

# 配置日志系统（确保每个请求都有日志输出）
import logging
import sys

# 配置日志，同时输出到文件和标准输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # 输出到标准输出，Gunicorn 会捕获
    ]
)
logger = logging.getLogger(__name__)

# 请求日志中间件（类似本地 Flask 的输出）
@app.before_request
def log_request():
    """记录每个请求"""
    logger.info(f"📥 请求: {request.method} {request.url}")

@app.after_request
def after_request(response):
    """跨域支持和响应日志"""
    # 记录响应
    logger.info(f"📤 响应: {response.status_code} {request.method} {request.url}")
    
    # 跨域支持（使用set而不是add，避免重复）
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers['Access-Control-Allow-Origin'] = '*'
    if 'Access-Control-Allow-Headers' not in response.headers:
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    if 'Access-Control-Allow-Methods' not in response.headers:
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

def migrate_database():
    """数据库迁移 - 添加新字段（仅在需要时执行）"""
    try:
        from sqlalchemy import text, inspect
        
        # 检测数据库类型
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        is_postgresql = database_url.startswith('postgresql')
        
        # 检查是否已经迁移过（通过检查source_type字段是否存在）
        if is_postgresql:
            # PostgreSQL: 使用 information_schema
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND table_schema = 'public'
            """))
            order_columns = [row[0] for row in result.fetchall()]
        else:
            # SQLite: 使用 PRAGMA
            result = db.session.execute(text("PRAGMA table_info(\"order\")"))
            order_columns = [row[1] for row in result.fetchall()]
        
        if 'source_type' in order_columns:
            # 已经迁移过，跳过
            pass
        else:
            print("开始数据库迁移...")
        
        # 检查并修复order_image表的is_main字段
        if is_postgresql:
            # PostgreSQL: 获取所有表名
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
        else:
            # SQLite: 获取所有表名
            tables = [t[0] for t in db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()]
        
        table_name = 'order_images' if is_postgresql else 'order_image'
        if table_name in tables:
            if is_postgresql:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                """))
                columns = [row[0] for row in result.fetchall()]
            else:
                result = db.session.execute(text("PRAGMA table_info(order_image)"))
                columns = [row[1] for row in result.fetchall()]
            
            if 'is_main' not in columns:
                print(f"添加 is_main 字段到 {table_name} 表...")
                if is_postgresql:
                    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN is_main BOOLEAN DEFAULT FALSE NOT NULL"))
                else:
                    db.session.execute(text("ALTER TABLE order_image ADD COLUMN is_main BOOLEAN DEFAULT 0 NOT NULL"))
                
                # 对于已有数据，将第一条图片设为主图
                db.session.execute(text(f"""
                    UPDATE {table_name} 
                    SET is_main = {('TRUE', '1')[is_postgresql]} 
                    WHERE id IN (
                        SELECT MIN(id) 
                        FROM {table_name} 
                        GROUP BY order_id
                    )
                """))
                db.session.commit()
                print("is_main字段添加成功！")
        
        if 'source_type' not in order_columns:
            print("开始数据库迁移...")
        
        # 检查并添加 style_category 表的 cover_image 字段
        # 先查找实际的表名（可能是 style_category、stylecategory 或 style_categories）
        style_table_name = None
        possible_names = ['style_category', 'stylecategory', 'style_categories']
        for name in possible_names:
            if name in tables:
                style_table_name = name
                break
        
        # 如果没找到，尝试模糊匹配
        if not style_table_name:
            for table in tables:
                if 'style' in table.lower() and 'category' in table.lower() and 'subcategory' not in table.lower():
                    style_table_name = table
                    break
        
        if style_table_name:
            if is_postgresql:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{style_table_name}' AND table_schema = 'public'
                """))
                columns = [row[0] for row in result.fetchall()]
            else:
                result = db.session.execute(text(f"PRAGMA table_info({style_table_name})"))
                columns = [row[1] for row in result.fetchall()]
            
            if 'cover_image' not in columns:
                print(f"添加 cover_image 字段到 {style_table_name} 表...")
                try:
                    db.session.execute(text(f"ALTER TABLE {style_table_name} ADD COLUMN cover_image VARCHAR(255)"))
                    db.session.commit()
                    print("✅ cover_image 字段添加成功")
                except Exception as e:
                    if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                        print("⚠️ cover_image 字段已存在，跳过添加")
                        db.session.rollback()
                    else:
                        print(f"❌ 添加 cover_image 字段失败: {str(e)}")
                        db.session.rollback()
                        # 不抛出异常，继续执行其他迁移
            else:
                print("ℹ️ cover_image 字段已存在，跳过添加")
        else:
            print(f"⚠️ 未找到 style_category 表，跳过 cover_image 字段添加（可能表名不同）")
        
        # 检查并添加 user 表的缺失字段
        # 先查找实际的表名（可能是 user 或 users）
        user_table_name = None
        possible_names = ['user', 'users']
        for name in possible_names:
            if name in tables:
                user_table_name = name
                break
        
        # 如果没找到，尝试模糊匹配
        if not user_table_name:
            for table in tables:
                if table.lower() == 'user' or table.lower() == 'users':
                    user_table_name = table
                    break
        
        if user_table_name:
            if is_postgresql:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{user_table_name}' AND table_schema = 'public'
                """))
                user_columns = [row[0] for row in result.fetchall()]
            else:
                result = db.session.execute(text(f"PRAGMA table_info({user_table_name})"))
                user_columns = [row[1] for row in result.fetchall()]
        else:
            print(f"⚠️ 未找到 user 表，跳过用户表字段添加（可能表名不同）")
            user_columns = []  # 设置为空列表，跳过后续字段添加
        
        missing_user_fields = [
            ('commission_rate', 'DECIMAL(5,2) DEFAULT 0.00'),
            ('qr_code', 'VARCHAR(255)'),
            ('contact_person', 'VARCHAR(100)'),
            ('contact_phone', 'VARCHAR(20)'),
            ('wechat_id', 'VARCHAR(100)')
        ]
        
        if user_table_name and user_columns:
            for field_name, field_type in missing_user_fields:
                if field_name not in user_columns:
                    print(f"添加 {field_name} 字段到 {user_table_name} 表...")
                    try:
                        # PostgreSQL 需要调整数据类型
                        if is_postgresql:
                            pg_type = field_type.replace('DECIMAL(5,2)', 'NUMERIC(5,2)').replace('VARCHAR', 'VARCHAR')
                            db.session.execute(text(f"ALTER TABLE {user_table_name} ADD COLUMN {field_name} {pg_type}"))
                        else:
                            db.session.execute(text(f"ALTER TABLE {user_table_name} ADD COLUMN {field_name} {field_type}"))
                        db.session.commit()
                        print(f"✅ {field_name} 字段添加成功")
                    except Exception as e:
                        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                            print(f"⚠️ {field_name} 字段已存在，跳过添加")
                            db.session.rollback()
                        else:
                            print(f"❌ 添加 {field_name} 字段失败: {str(e)}")
                            db.session.rollback()
                            # 不抛出异常，继续执行其他字段
        
        # 添加 order 表的缺失字段
        missing_order_fields = [
            ('style_name', 'VARCHAR(100)'),
            ('product_name', 'VARCHAR(100)'),
            ('original_image', 'TEXT'),
            ('final_image', 'TEXT'),
            ('shipping_info', 'TEXT'),
            ('merchant_id', 'INTEGER'),
            ('completed_at', 'DATETIME'),
            ('commission', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('price', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('external_platform', 'VARCHAR(50)'),
            ('external_order_number', 'VARCHAR(100)'),
            ('source_type', 'VARCHAR(20) DEFAULT "website"')
        ]
        
        order_table_name = 'orders' if is_postgresql else '"order"'
        for field_name, field_type in missing_order_fields:
            if field_name not in order_columns:
                print(f"添加 {field_name} 字段到 {order_table_name} 表...")
                # PostgreSQL 需要调整数据类型和默认值
                if is_postgresql:
                    pg_type = field_type.replace('DECIMAL(10,2)', 'NUMERIC(10,2)').replace('VARCHAR', 'VARCHAR')
                    pg_type = pg_type.replace('DATETIME', 'TIMESTAMP').replace('"website"', "'website'")
                    db.session.execute(text(f"ALTER TABLE {order_table_name} ADD COLUMN {field_name} {pg_type}"))
                else:
                    db.session.execute(text(f"ALTER TABLE {order_table_name} ADD COLUMN {field_name} {field_type}"))
                db.session.commit()
                print(f"{field_name} 字段添加成功")
        
        # 为现有记录设置正确的source_type
        if order_table_name and 'source_type' in order_columns:
            print("更新现有订单的source_type...")
            try:
                # 小程序来源的订单（external_platform = 'miniprogram'）
                db.session.execute(text(f"UPDATE {order_table_name} SET source_type = 'miniprogram' WHERE external_platform = 'miniprogram'"))
                # 网页来源的订单（external_platform 为空或非miniprogram）
                db.session.execute(text(f"UPDATE {order_table_name} SET source_type = 'website' WHERE external_platform IS NULL OR external_platform != 'miniprogram'"))
                db.session.commit()
                print("✅ source_type 更新完成")
            except Exception as e:
                print(f"⚠️ 更新 source_type 失败: {str(e)}")
                db.session.rollback()
        
        # 为现有记录设置默认封面图（仅在封面图为空时设置）
        if MODELS_AVAILABLE:
            try:
                categories = StyleCategory.query.all()
                for category in categories:
                    if not category.cover_image:
                        if category.code == 'anthropomorphic':
                            category.cover_image = '/static/images/8-威廉国王.jpg'
                        elif category.code == 'oil_painting':
                            category.cover_image = '/static/images/油画风格-梵高.jpg'
                        elif category.code == 'transfer':
                            category.cover_image = '/static/images/转绘风格-卡通.png'
                        else:
                            category.cover_image = '/static/images/8-威廉国王.jpg'  # 默认图片
                
                db.session.commit()
            except NameError:
                print("⚠️ StyleCategory 未定义，跳过封面图设置")
            except Exception as e:
                print(f"⚠️ 设置封面图失败: {e}")
                try:
                    db.session.rollback()
                except:
                    pass
        
        # 检查并添加 meitu_api_config 表的字段
        # 先查找实际的表名（可能是 meitu_api_config 或 meitu_api_configs）
        meitu_table_name = None
        possible_names = ['meitu_api_config', 'meitu_api_configs']
        for name in possible_names:
            if name in tables:
                meitu_table_name = name
                break
        
        # 如果没找到，尝试模糊匹配
        if not meitu_table_name:
            for table in tables:
                if 'meitu' in table.lower() and 'api' in table.lower() and 'config' in table.lower():
                    meitu_table_name = table
                    break
        
        if meitu_table_name:
            if is_postgresql:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{meitu_table_name}' AND table_schema = 'public'
                """))
                meitu_columns = [row[0] for row in result.fetchall()]
            else:
                result = db.session.execute(text(f"PRAGMA table_info({meitu_table_name})"))
                meitu_columns = [row[1] for row in result.fetchall()]
            
            # 添加 app_id 字段（如果不存在）
            if 'app_id' not in meitu_columns:
                print(f"添加 app_id 字段到 {meitu_table_name} 表...")
                db.session.execute(text(f"ALTER TABLE {meitu_table_name} ADD COLUMN app_id VARCHAR(100)"))
                db.session.commit()
                print("✅ app_id 字段添加成功")
            
            # 添加 api_endpoint 字段（如果不存在）
            if 'api_endpoint' not in meitu_columns:
                print(f"添加 api_endpoint 字段到 {meitu_table_name} 表...")
                default_value = "'/openapi/realphotolocal_async'" if is_postgresql else "'/openapi/realphotolocal_async'"
                db.session.execute(text(f"ALTER TABLE {meitu_table_name} ADD COLUMN api_endpoint VARCHAR(200) DEFAULT {default_value}"))
                db.session.commit()
                print("✅ api_endpoint 字段添加成功")
            
            # 添加 repost_url 字段（如果不存在）
            if 'repost_url' not in meitu_columns:
                print(f"添加 repost_url 字段到 {meitu_table_name} 表...")
                db.session.execute(text(f"ALTER TABLE {meitu_table_name} ADD COLUMN repost_url VARCHAR(500)"))
                db.session.commit()
                print("✅ repost_url 字段添加成功")
            
            # 添加 enable_in_workflow 字段（如果不存在）
            if 'enable_in_workflow' not in meitu_columns:
                print(f"添加 enable_in_workflow 字段到 {meitu_table_name} 表...")
                default_bool = 'FALSE' if is_postgresql else '0'
                db.session.execute(text(f"ALTER TABLE {meitu_table_name} ADD COLUMN enable_in_workflow BOOLEAN DEFAULT {default_bool} NOT NULL"))
                db.session.commit()
                print("✅ enable_in_workflow 字段添加成功")
            
            # 自动修复错误的API Base URL（将 openapi.meitu.com 更新为 api.yunxiu.meitu.com）
            if 'api_base_url' in meitu_columns:
                try:
                    print("检查并修复美图API配置中的错误URL...")
                    result = db.session.execute(text(f"""
                        SELECT COUNT(*) FROM {meitu_table_name} 
                        WHERE api_base_url = 'https://openapi.meitu.com' 
                           OR api_base_url LIKE '%openapi.meitu.com%'
                    """))
                    count = result.fetchone()[0]
                    if count > 0:
                        print(f"发现 {count} 条记录包含错误的API URL，正在修复...")
                        db.session.execute(text(f"""
                            UPDATE {meitu_table_name} 
                            SET api_base_url = 'https://api.yunxiu.meitu.com'
                            WHERE api_base_url = 'https://openapi.meitu.com' 
                               OR api_base_url LIKE '%openapi.meitu.com%'
                        """))
                        db.session.commit()
                        print("✅ 已自动修复美图API配置中的错误URL")
                    else:
                        print("✅ 美图API配置URL检查通过（无需修复）")
                except Exception as e:
                    print(f"⚠️ 检查美图API配置URL失败: {str(e)}")
                    db.session.rollback()
            
            # 确保 api_endpoint 有默认值（如果为空）
            if 'api_endpoint' in meitu_columns:
                try:
                    db.session.execute(text(f"""
                        UPDATE {meitu_table_name} 
                        SET api_endpoint = '/openapi/realphotolocal_async'
                        WHERE api_endpoint IS NULL OR api_endpoint = ''
                    """))
                    db.session.commit()
                except Exception as e:
                    print(f"⚠️ 更新 api_endpoint 默认值失败: {str(e)}")
                    db.session.rollback()
        else:
            print(f"⚠️ 未找到 meitu_api_config 表，跳过美图API配置字段添加（可能表名不同）")
        
        # 添加 msg_id 字段到 meitu_api_call_log 表（如果不存在）
        # 注意：这个迁移应该在 meitu_api_config 块外部，因为它是独立的表
        # 先查找实际的表名（可能是 meitu_api_call_log 或 meitu_api_call_logs）
        call_log_table_name = None
        possible_names = ['meitu_api_call_log', 'meitu_api_call_logs']
        for name in possible_names:
            if name in tables:
                call_log_table_name = name
                break
        
        # 如果没找到，尝试模糊匹配
        if not call_log_table_name:
            for table in tables:
                if 'meitu' in table.lower() and 'api' in table.lower() and 'call' in table.lower() and 'log' in table.lower():
                    call_log_table_name = table
                    break
        
        if call_log_table_name:
            if is_postgresql:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{call_log_table_name}' AND table_schema = 'public'
                """))
                call_log_columns = [row[0] for row in result.fetchall()]
            else:
                result = db.session.execute(text(f"PRAGMA table_info({call_log_table_name})"))
                call_log_columns = [row[1] for row in result.fetchall()]
            
            if 'msg_id' not in call_log_columns:
                print(f"添加 msg_id 字段到 {call_log_table_name} 表...")
                try:
                    db.session.execute(text(f"ALTER TABLE {call_log_table_name} ADD COLUMN msg_id VARCHAR(100)"))
                    db.session.commit()
                    print("✅ msg_id 字段添加成功")
                    
                    # 从现有的 response_data 中提取 msg_id 并更新到新字段
                    print("从现有记录中提取 msg_id...")
                    all_logs = db.session.execute(text(f"SELECT id, response_data FROM {call_log_table_name} WHERE response_data IS NOT NULL")).fetchall()
                    updated_count = 0
                    for log_id, response_data in all_logs:
                        if response_data:
                            try:
                                import json
                                data = json.loads(response_data) if isinstance(response_data, str) else response_data
                                if isinstance(data, dict):
                                    msg_id = data.get('msg_id')
                                    if msg_id:
                                        db.session.execute(text(f"UPDATE {call_log_table_name} SET msg_id = :msg_id WHERE id = :id"), {
                                            'msg_id': msg_id,
                                            'id': log_id
                                        })
                                        updated_count += 1
                            except:
                                pass
                    db.session.commit()
                    if updated_count > 0:
                        print(f"✅ 已从 {updated_count} 条现有记录中提取并更新 msg_id")
                except Exception as e:
                    if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                        print("⚠️ msg_id 字段已存在，跳过添加")
                        db.session.rollback()
                    else:
                        print(f"❌ 添加 msg_id 字段失败: {str(e)}")
                        db.session.rollback()
            else:
                print("✅ meitu_api_call_log 表的 msg_id 字段已存在")
        else:
            print(f"⚠️ 未找到 meitu_api_call_log 表，跳过 msg_id 字段添加（可能表名不同）")
        
        # 检查并添加 api_provider_configs 表的 is_sync_api 字段
        if 'api_provider_configs' in tables:
            if is_postgresql:
                result = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'api_provider_configs' AND table_schema = 'public'
                """))
                api_config_columns = [row[0] for row in result.fetchall()]
            else:
                result = db.session.execute(text("PRAGMA table_info(api_provider_configs)"))
                api_config_columns = [row[1] for row in result.fetchall()]
            
            if 'is_sync_api' not in api_config_columns:
                print("添加 is_sync_api 字段到 api_provider_configs 表...")
                default_bool = 'FALSE' if is_postgresql else '0'
                db.session.execute(text(f"ALTER TABLE api_provider_configs ADD COLUMN is_sync_api BOOLEAN DEFAULT {default_bool} NOT NULL"))
                db.session.commit()
                
                # 根据 api_type 自动设置 is_sync_api 的值
                sync_value = 'TRUE' if is_postgresql else '1'
                db.session.execute(text(f"UPDATE api_provider_configs SET is_sync_api = {sync_value} WHERE api_type = 'gemini-native'"))
                db.session.commit()
                print("is_sync_api 字段添加成功，并已根据 api_type 自动设置值")
        
        # 检查并修复 franchisee_accounts 表的 password 字段长度
        if 'franchisee_accounts' in tables:
            if is_postgresql:
                result = db.session.execute(text("""
                    SELECT column_name, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = 'franchisee_accounts' 
                    AND table_schema = 'public'
                    AND column_name = 'password'
                """))
                password_col = result.fetchone()
                if password_col and password_col[1] and password_col[1] < 255:
                    print(f"修复 franchisee_accounts.password 字段长度 ({password_col[1]} -> 255)...")
                    try:
                        db.session.execute(text("ALTER TABLE franchisee_accounts ALTER COLUMN password TYPE VARCHAR(255)"))
                        db.session.commit()
                        print("✅ password 字段长度已修复")
                    except Exception as e:
                        print(f"⚠️ 修复 password 字段长度失败: {str(e)}")
                        db.session.rollback()
            else:
                # SQLite不支持直接修改列类型，需要重建表
                # 这里只记录警告
                print("⚠️ SQLite不支持修改列类型，如需修复password字段长度，请手动处理")
        
        print("数据库迁移完成")
        
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        db.session.rollback()

def init_concurrency_configs():
    """初始化并发和队列配置（如果不存在，使用默认值）"""
    try:
        from app.utils.config_loader import get_int_config
        from app.models import AIConfig
        from datetime import datetime
        
        default_configs = [
            ('comfyui_max_concurrency', '10', 'ComfyUI最大并发数'),
            ('api_max_concurrency', '5', 'API最大并发数'),
            ('task_queue_max_size', '100', '任务队列最大大小'),
            ('task_queue_workers', '3', '任务队列工作线程数')
        ]
        
        for config_key, default_value, description in default_configs:
            existing = AIConfig.query.filter_by(config_key=config_key).first()
            if not existing:
                new_config = AIConfig(
                    config_key=config_key,
                    config_value=default_value,
                    description=description
                )
                db.session.add(new_config)
                print(f"✅ 初始化配置: {config_key} = {default_value}")
        
        db.session.commit()
        print("✅ 并发配置初始化完成")
    except Exception as e:
        print(f"⚠️ 初始化并发配置失败: {str(e)}")
        import traceback
        traceback.print_exc()


def init_default_data():
    """初始化默认数据 - 只在数据库为空时创建"""
    # 检查模型是否可用
    if not MODELS_AVAILABLE:
        print("⚠️ 数据库模型未加载，跳过默认数据创建")
        return
    
    try:
        # 检查是否已有数据，如果有则不创建
        existing_categories = StyleCategory.query.count()
        if existing_categories > 0:
            print(f"数据库中已有 {existing_categories} 个风格分类，跳过默认数据创建")
            return
    except NameError as e:
        print(f"⚠️ StyleCategory 未定义，跳过默认数据创建: {e}")
        return
    except Exception as e:
        print(f"⚠️ 检查数据库时出错，跳过默认数据创建: {e}")
        return
    
    print("数据库为空，开始创建默认数据...")
    
    # 创建默认风格分类
    categories = [
        {
            'name': '拟人风格',
            'code': 'anthropomorphic',
            'description': '伯爵公主、皇家大臣、铠甲战士等拟人化风格',
            'icon': '👑',
            'cover_image': '/static/images/8-威廉国王.jpg',  # 使用实际存在的图片
            'sort_order': 1
        },
        {
            'name': '油画风格',
            'code': 'oil_painting',
            'description': '经典油画艺术风格，厚重笔触，丰富色彩',
            'icon': '🎨',
            'cover_image': '/static/images/油画风格-梵高.jpg',  # 使用实际存在的图片
            'sort_order': 2
        },
        {
            'name': '转绘风格',
            'code': 'transfer',
            'description': '现代转绘艺术风格，清新简约',
            'icon': '✨',
            'cover_image': '/static/images/转绘风格-卡通.png',  # 使用实际存在的图片
            'sort_order': 3
        }
    ]
    
    try:
        for cat_data in categories:
            category = StyleCategory(**cat_data)
            db.session.add(category)
            print(f"创建风格分类: {cat_data['name']}")
        
        db.session.commit()
        print("✅ 默认风格分类创建完成")
    except Exception as e:
        print(f"⚠️ 创建风格分类失败: {e}")
        db.session.rollback()
        return
    
    # 创建默认风格图片
    images = [
        {
            'category_code': 'anthropomorphic',
            'name': '威廉国王',
            'code': 'william',
            'description': '威严庄重的宠物，如国王般尊贵威严',
            'image_url': '/static/images/8-威廉国王.jpg',
            'sort_order': 1
        },
        {
            'category_code': 'anthropomorphic',
            'name': '伯爵公主',
            'code': 'princess',
            'description': '富贵优雅的宠物，如公主般高贵典雅',
            'image_url': '/static/images/1-伯爵公主.jpg',
            'sort_order': 2
        },
        {
            'category_code': 'oil_painting',
            'name': '梵高风格',
            'code': 'vangogh',
            'description': '印象派大师梵高的经典绘画风格',
            'image_url': '/static/images/油画风格-梵高.jpg',
            'sort_order': 1
        },
        {
            'category_code': 'oil_painting',
            'name': '睡莲风格',
            'code': 'waterlily',
            'description': '莫奈式的印象派睡莲绘画风格',
            'image_url': '/static/images/油画风格-睡莲.jpg',
            'sort_order': 2
        },
        {
            'category_code': 'oil_painting',
            'name': '厚涂风格',
            'code': 'impasto',
            'description': '厚重笔触的厚涂绘画风格',
            'image_url': '/static/images/油画风格-厚涂.png',
            'sort_order': 3
        },
        {
            'category_code': 'transfer',
            'name': '卡通风格',
            'code': 'cartoon',
            'description': '可爱萌趣的卡通转绘风格',
            'image_url': '/static/images/转绘风格-卡通.png',
            'sort_order': 1
        }
    ]
    
    try:
        for img_data in images:
            # 查找对应的分类
            category = StyleCategory.query.filter_by(code=img_data['category_code']).first()
            if category:
                existing = StyleImage.query.filter_by(code=img_data['code']).first()
                if not existing:
                    image = StyleImage(
                        category_id=category.id,
                        name=img_data['name'],
                        code=img_data['code'],
                        description=img_data['description'],
                        image_url=img_data['image_url'],
                        sort_order=img_data['sort_order']
                    )
                    db.session.add(image)
                    print(f"创建风格图片: {img_data['name']} (分类: {category.name})")
        
        db.session.commit()
        print("✅ 默认风格图片创建完成")
    except Exception as e:
        print(f"⚠️ 创建风格图片失败: {e}")
        db.session.rollback()
        return
    
    # 创建默认首页配置
    try:
        config = HomepageConfig.query.first()
        if not config:
            config = HomepageConfig(
                title='AI拍照机',
                subtitle='专属定制',
                description='为您打造专属艺术品',
                enable_custom_order=True,
                enable_style_library=True,
                enable_product_gallery=True,
                enable_works_gallery=True
            )
            db.session.add(config)
            print("创建默认首页配置")
        
        # 创建默认轮播图 (竖版长比例)
        banners = [
            {
                'title': '拟人风格',
                'subtitle': '皇家宠物',
                'image_url': '/static/images/8-威廉国王.jpg',
                'link': '/pages/style/style',
                'sort_order': 1,
                'is_active': True
            },
            {
                'title': '油画风格',
                'subtitle': '艺术大师',
                'image_url': '/static/images/油画风格-梵高.jpg',
                'link': '/pages/style/style',
                'sort_order': 2,
                'is_active': True
            },
            {
                'title': '转绘风格',
                'subtitle': '可爱萌趣',
                'image_url': '/static/images/转绘风格-卡通.png',
                'link': '/pages/style/style',
                'sort_order': 3,
                'is_active': True
            },
            {
                'title': '样片展示',
                'subtitle': '精美作品',
                'image_url': '/static/images/样片展示.jpg',
                'link': '/works-gallery',
                'sort_order': 4,
                'is_active': True
            }
        ]
        
        for banner_data in banners:
            existing = HomepageBanner.query.filter_by(title=banner_data['title']).first()
            if not existing:
                banner = HomepageBanner(**banner_data)
                db.session.add(banner)
                print(f"创建轮播图: {banner_data['title']}")
        
        db.session.commit()
        print("✅ 默认首页配置和轮播图创建完成")
    except Exception as e:
        print(f"⚠️ 创建首页配置或轮播图失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
    
    print("✅ 默认数据初始化完成")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 数据库迁移
        migrate_database()
        
        # 初始化默认数据
        init_default_data()
        
        # 创建默认管理员账号
        if MODELS_AVAILABLE:
            try:
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        password=generate_password_hash('admin123'),
                        role='admin'
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("创建默认管理员账号: admin/admin123")
                else:
                    print("✅ 管理员账号已存在")
            except NameError as e:
                print(f"⚠️ User 模型未定义，跳过创建管理员账号: {e}")
            except Exception as e:
                print(f"⚠️ 创建管理员账号失败: {e}")
        else:
            print("⚠️ 数据库模型未加载，跳过创建管理员账号")
        
        # 初始化并发和队列配置（如果不存在，使用默认值）
        try:
            from app.utils.config_loader import get_int_config
            from app.models import AIConfig
            from datetime import datetime
            
            default_configs = [
                ('comfyui_max_concurrency', '10', 'ComfyUI最大并发数'),
                ('api_max_concurrency', '5', 'API最大并发数'),
                ('task_queue_max_size', '100', '任务队列最大大小'),
                ('task_queue_workers', '3', '任务队列工作线程数')
            ]
            
            for config_key, default_value, description in default_configs:
                existing = AIConfig.query.filter_by(config_key=config_key).first()
                if not existing:
                    new_config = AIConfig(
                        config_key=config_key,
                        config_value=default_value,
                        description=description
                    )
                    db.session.add(new_config)
                    print(f"✅ 初始化配置: {config_key} = {default_value}")
            
            db.session.commit()
        except Exception as e:
            print(f"⚠️ 初始化并发配置失败: {str(e)}")
        
        # 启动任务队列服务（用于管理10台设备、40-50个排队任务）
        try:
            from app.services.task_queue_service import start_task_queue
            start_task_queue()
            print("✅ 任务队列服务已启动")
        except Exception as e:
            print(f"⚠️ 启动任务队列服务失败: {str(e)}")
            print("⚠️ 系统将使用直接调用模式（兼容模式）")
        
        # 启动AI任务状态自动轮询服务（定期检查处理中的任务并更新状态）
        try:
            from app.services.ai_task_polling_service import init_ai_task_polling_service
            init_ai_task_polling_service()
            print("✅ AI任务状态自动轮询服务已启动")
        except Exception as e:
            print(f"⚠️ 启动AI任务状态轮询服务失败: {str(e)}")
    
# ⭐ 管理后台工具API已迁移到 app.routes.admin_tools_api

# ⭐ 预约拍照功能已完全删除


# ==================== 用户访问追踪API接口 ====================

# 用户访问追踪API（新版本 - 支持完整访问追踪）
# 用户相关路由已迁移到 app.routes.user_api

def get_referrer_user_id(invitee_user_id):
    """获取推荐人ID"""
    try:
        # 查找最新的推广访问记录
        track = PromotionTrack.query.filter_by(visitor_user_id=invitee_user_id).order_by(PromotionTrack.create_time.desc()).first()
        
        if track:
            print(f"找到推荐人: {track.referrer_user_id} (通过推广码: {track.promotion_code})")
            return track.referrer_user_id, track.promotion_code
        return None, None
    except Exception as e:
        print(f"获取推荐人ID失败: {e}")
        return None, None

# 更新用户信息接口
# 用户相关路由已迁移到 app.routes.user_api（续）

        # ⭐ 提现功能已删除，不再计算提现金额

# ⭐ 用户提现记录功能已删除

# 用户相关路由已迁移到 app.routes.user_api（续）

def send_subscribe_message(openid, template_id, data, page=None, check_subscription=True):
    """发送订阅消息"""
    try:
        # 暂时跳过订阅状态检查，等数据库表结构更新后再启用
        # if check_subscription:
        #     user = PromotionUser.query.filter_by(open_id=openid).first()
        #     if user and not user.is_subscribed:
        #         print(f"用户 {user.user_id} 未订阅消息，跳过发送")
        #         return False
        # 获取access_token
        access_token_url = 'https://api.weixin.qq.com/cgi-bin/token'
        token_params = {
            'grant_type': 'client_credential',
            'appid': WECHAT_PAY_CONFIG['appid'],
            'secret': WECHAT_PAY_CONFIG['app_secret']
        }
        
        token_response = requests.get(access_token_url, params=token_params, timeout=30)
        
        if token_response.status_code == 200:
            token_result = token_response.json()
            if 'access_token' in token_result:
                access_token = token_result['access_token']
                
                # 发送订阅消息
                send_url = f'https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}'
                
                message_data = {
                    'touser': openid,
                    'template_id': template_id,
                    'data': data
                }
                
                if page:
                    message_data['page'] = page
                
                send_response = requests.post(send_url, json=message_data, timeout=30)
                
                if send_response.status_code == 200:
                    result = send_response.json()
                    if result.get('errcode') == 0:
                        print(f"订阅消息发送成功: {openid}")
                        return True
                    else:
                        print(f"订阅消息发送失败: {result}")
                        return False
                else:
                    print(f"订阅消息请求失败: {send_response.status_code}")
                    return False
            else:
                print(f"获取access_token失败: {token_result}")
                return False
        else:
            print(f"获取access_token请求失败: {token_response.status_code}")
            return False
            
    except Exception as e:
        print(f"发送订阅消息异常: {str(e)}")
        return False

# 提现审核通过通知
# ⭐ 提现通知功能已完全删除

# 订单完成通知
# 消息通知API已迁移到 app.routes.admin_notification_api

# 自动发送订单完成通知
def send_order_completion_notification_auto(order):
    """自动发送订单完成通知"""
    try:
        # 优先使用订单中保存的用户openid
        openid = getattr(order, 'openid', None)
        
        # 如果没有openid，尝试通过其他方式获取（兼容旧订单）
        if not openid:
            # 可以通过订单的customer_phone查找对应的推广用户
            promotion_user = PromotionUser.query.filter_by(phone_number=order.customer_phone).first()
            if promotion_user:
                openid = promotion_user.open_id
        
        if not openid:
            print(f"订单 {order.order_number} 无法获取用户openid，跳过通知发送")
            return False
        
        # 发送订阅消息 - 制作完成通知模板
        template_data = {
            'character_string13': {'value': order.order_number},  # 订单编号
            'thing1': {'value': order.size or '定制产品'},  # 作品名称
            'time17': {'value': order.completed_at.strftime('%Y年%m月%d日 %H:%M')}  # 制作完成时间
        }
        
        success = send_subscribe_message(
            openid=openid,
            template_id='BOy7pDiq-pM1qiJHJfP9jUjAbi9o0bZG5-mEKZbnYT8',  # 制作完成通知模板ID
            data=template_data,
            page=f'/pages/order-detail/order-detail?orderId={order.order_number}'  # 跳转到订单详情页
        )
        
        if success:
            print(f"自动发送订单完成通知成功: {order.order_number}")
            return True
        else:
            print(f"自动发送订单完成通知失败: {order.order_number}")
            return False
            
    except Exception as e:
        print(f"自动发送订单完成通知异常: {str(e)}")
        return False

# 自动发送推广收益通知
def send_commission_notification_auto(commission):
    """自动发送推广收益通知"""
    try:
        # 获取用户信息
        promotion_user = PromotionUser.query.filter_by(user_id=commission.referrer_user_id).first()
        if not promotion_user or not promotion_user.open_id:
            print(f"分佣记录 {commission.id} 无法获取用户信息，跳过通知发送")
            return False
        
        # 获取订单信息
        order = Order.query.filter_by(order_number=commission.order_id).first()
        if not order:
            print(f"分佣记录 {commission.id} 无法获取订单信息，跳过通知发送")
            return False
        
        # 发送订阅消息 - 收益提成提醒模板
        template_data = {
            'thing1': {'value': f'¥{order.price}'},  # 下单金额
            'thing2': {'value': f'¥{commission.amount}'},  # 提成金额
            'thing3': {'value': '已结算' if commission.status == 'completed' else '待结算'}  # 金额状态
        }
        
        success = send_subscribe_message(
            openid=promotion_user.open_id,
            template_id='bcY_uUJMP1IGFIuUyiFeBSFIPbCb4areeTXs78HUe9Y',  # 收益提成提醒模板ID
            data=template_data,
            page='/pages/promotion/promotion'
        )
        
        if success:
            print(f"自动发送推广收益通知成功: 用户{commission.referrer_user_id}, 分佣{commission.amount}元")
            return True
        else:
            print(f"自动发送推广收益通知失败: 用户{commission.referrer_user_id}")
            return False
            
    except Exception as e:
        print(f"自动发送推广收益通知异常: {str(e)}")
        return False

# 推广相关路由已迁移到 app.routes.promotion_api

# ⚠️ 以下优惠券路由已迁移到 app.routes.coupon_api 和 app.routes.admin_coupon_api，已注释
# ==================== 已迁移模块说明 ====================
# - 管理员优惠券API → app.routes.admin_coupon_api
# - 二维码生成API → app.routes.qrcode_api
# - 推广管理页面和API → app.routes.admin_promotion_api
# - 用户管理路由 → app.routes.admin_users_api
# - 消息通知API → app.routes.admin_notification_api
# - 用户消息相关路由 → app.routes.user_api
# =====================================================

# ⭐ 以下函数已迁移到 app.routes.admin_coupon_api，已删除：
# - create_coupon_admin()
# - update_coupon_admin()
# - delete_coupon_admin()
# - admin_coupons_management()

        # ⭐ 提现功能已删除，不再删除提现记录

# ⭐ 抖音同步功能已删除

# 导入订单状态自动更新服务（可选功能）
try:
    import sys
    import os
    # 添加 scripts 目录到 Python 路径
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    from auto_status_update_service import init_auto_update_service
    # init_auto_update_service()  # 暂时禁用自动更新服务
    print("⚠️ 订单状态自动更新服务已禁用")
except ImportError as e:
    print(f"⚠️ 订单状态自动更新服务未找到: {str(e)}")
except Exception as e:
    print(f"⚠️ 订单状态自动更新服务加载失败: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 数据库迁移
        migrate_database()
        
        # 初始化默认数据
        init_default_data()
        
        # 创建默认管理员账号
        if MODELS_AVAILABLE:
            try:
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        password=generate_password_hash('admin123'),
                        role='admin'
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("创建默认管理员账号: admin/admin123")
                else:
                    print("✅ 管理员账号已存在")
            except NameError as e:
                print(f"⚠️ User 模型未定义，跳过创建管理员账号: {e}")
            except Exception as e:
                print(f"⚠️ 创建管理员账号失败: {e}")
        else:
            print("⚠️ 数据库模型未加载，跳过创建管理员账号")
    
    # 注册加盟商蓝图（已在上面调用过）
    # register_franchisee_blueprints()
    
    # ============== 自动数据表初始化API ================
    # ⭐ 预约拍照功能已完全删除
    
    app.run(host='0.0.0.0', port=8000, debug=True)
