# -*- coding: utf-8 -*-
"""
数据库模型
从 test_server.py 迁移所有数据库模型类
"""
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import re
import unicodedata

# 注意：这里不能从app导入db，因为会造成循环导入
# 使用延迟导入的方式：在函数中获取db实例
# 但类定义时就需要db.Model，所以我们需要一个更直接的方法

# 创建一个全局变量来存储db实例（将在test_server.py中设置）
_db_instance = None

def _get_db():
    """延迟获取db实例"""
    global _db_instance
    if _db_instance is not None:
        return _db_instance
    # 尝试从test_server导入db（在db初始化后）
    try:
        import sys
        # 获取test_server模块
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                _db_instance = test_server_module.db
                return _db_instance
    except (ImportError, AttributeError):
        pass
    # 如果无法获取，返回None（这种情况不应该发生）
    return None

# 导出所有模型类（包括新增的AI相关模型）
__all__ = [
    'Product', 'ProductSize', 'ProductSizePetOption', 'ProductImage', 
    'ProductStyleCategory', 'ProductCustomField',
    'StyleCategory', 'StyleImage',
    'HomepageBanner', 'WorksGallery', 'HomepageConfig',
    'User', 'UserVisit',
    'Order', 'OrderImage',
    'PhotoSignup',
    'PromotionUser', 'Commission', 'Withdrawal', 'PromotionTrack',
    'Coupon', 'UserCoupon', 'ShareRecord',
    'FranchiseeAccount', 'FranchiseeRecharge', 'SelfieMachine',
    'AITask', 'AIConfig',  # 新增AI相关模型
    'APIProviderConfig', 'APITemplate',  # 新增云端API服务商相关模型
    'ShopProduct', 'ShopProductImage', 'ShopProductSize', 'ShopOrder',  # 新增商城相关模型
    'PrintSizeConfig',  # 新增打印配置模型
    '_sanitize_style_code', '_build_style_code', '_ensure_unique_style_code'
]

# 创建一个代理对象，在访问时动态获取db
class DBProxy:
    """db代理类，延迟获取db实例"""
    def __getattr__(self, name):
        db_instance = _get_db()
        if db_instance is None:
            raise AttributeError(f"db尚未初始化，无法访问属性 '{name}'。请确保在test_server.py中先初始化db")
        return getattr(db_instance, name)

# 创建db代理实例（将在test_server.py中替换为实际的db实例）
# 注意：在类定义时，db.Model会被访问，此时db还是DBProxy
# 但DBProxy会在访问时动态获取db实例，所以需要确保在导入模型类之前，db已经初始化
db = DBProxy()

# 提供一个函数来设置db实例（用于test_server.py）
def set_db(db_instance):
    """设置db实例（用于test_server.py）
    注意：这个函数需要在导入模型类之前调用，但类定义在导入时就会执行
    所以我们需要在导入前设置db，或者使用延迟绑定的方式
    """
    global _db_instance, db
    # 直接替换db为实际的db实例
    _db_instance = db_instance
    db = db_instance

# ============================================================================
# 产品相关模型
# ============================================================================

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # 产品代码，如 keychain
    name = db.Column(db.String(100), nullable=False)  # 产品名称，如 艺术钥匙扣
    description = db.Column(db.Text)  # 产品描述
    image_url = db.Column(db.String(500))  # 产品图片URL
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序
    free_selection_count = db.Column(db.Integer, default=1)  # 标准赠送的选片张数（默认1张）
    extra_photo_price = db.Column(db.Float, default=10.0)  # 每加一张照片的价格（默认10元）
    created_at = db.Column(db.DateTime, default=datetime.now)

class ProductSize(db.Model):
    __tablename__ = 'product_sizes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('sizes', lazy=True))
    size_name = db.Column(db.String(100), nullable=False)  # 尺寸名称，如 30x40cm 或 8寸 (22x27cm) 桌摆画框
    price = db.Column(db.Float, nullable=False)  # 基础价格（用于向后兼容）
    printer_product_id = db.Column(db.String(50))  # 冲印系统产品ID，如 33673
    effect_image_url = db.Column(db.String(500))  # 效果图URL（用于选片页面显示）
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.now)

class ProductSizePetOption(db.Model):
    __tablename__ = 'product_size_pet_options'
    
    id = db.Column(db.Integer, primary_key=True)
    size_id = db.Column(db.Integer, db.ForeignKey('product_sizes.id'), nullable=False)
    size = db.relationship('ProductSize', backref=db.backref('pet_options', lazy=True, cascade='all, delete-orphan'))
    pet_count_name = db.Column(db.String(50), nullable=False)  # 宠物数量名称，如 "单只"、"多只"
    price = db.Column(db.Float, nullable=False)  # 该选项对应的价格
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.now)

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('images', lazy=True))
    image_url = db.Column(db.String(500), nullable=False)  # 图片URL
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)

class ProductStyleCategory(db.Model):
    __tablename__ = 'product_style_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    style_category_id = db.Column(db.Integer, db.ForeignKey('style_category.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('style_categories', lazy=True, cascade='all, delete-orphan'))
    style_category = db.relationship('StyleCategory', backref=db.backref('products', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 确保同一产品不会重复绑定同一风格分类
    __table_args__ = (db.UniqueConstraint('product_id', 'style_category_id', name='_product_style_category_uc'),)

class ProductCustomField(db.Model):
    __tablename__ = 'product_custom_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('custom_fields', lazy=True, cascade='all, delete-orphan'))
    field_name = db.Column(db.String(50), nullable=False)  # 字段名称，如"宠物数量"、"颜色"
    field_type = db.Column(db.String(20), nullable=False)  # 字段类型：text/select/number
    field_options = db.Column(db.Text)  # 如果是select类型，存储选项（JSON格式或逗号分隔）
    is_required = db.Column(db.Boolean, default=False)  # 是否必填
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.now)

# ============================================================================
# 风格相关模型
# ============================================================================

class StyleCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 分类名称，如"拟人风格"
    code = db.Column(db.String(20), unique=True, nullable=False)  # 分类代码，如"anthropomorphic"
    description = db.Column(db.String(200))  # 分类描述
    icon = db.Column(db.String(10))  # 图标，如"👑"
    cover_image = db.Column(db.String(500))  # 封面图片URL
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # ⭐ AI工作流相关字段（新增）- 分类级别默认配置
    workflow_name = db.Column(db.String(200))  # 工作流名称（不含.json）
    workflow_file = db.Column(db.String(200))  # 工作流文件名（含.json）
    workflow_input_ids = db.Column(db.Text)  # 输入图片节点ID（JSON数组字符串，如["199"]）
    workflow_output_id = db.Column(db.String(50))  # 输出节点ID
    workflow_ref_id = db.Column(db.String(50))  # 参考图节点ID（可选）
    workflow_ref_image = db.Column(db.String(500))  # 参考图文件名（可选）
    workflow_user_prompt_id = db.Column(db.String(50))  # 用户预设提示词节点ID（可选）
    workflow_custom_prompt_id = db.Column(db.String(50))  # 自定义提示词节点ID（可选）
    workflow_custom_prompt_content = db.Column(db.Text)  # 自定义提示词内容（可选）
    is_ai_enabled = db.Column(db.Boolean, default=False)  # 是否启用AI工作流处理（分类级别）

class StyleImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('style_category.id'), nullable=False)
    category = db.relationship('StyleCategory', backref=db.backref('images', lazy=True))
    name = db.Column(db.String(100), nullable=False)  # 风格名称，如"威廉国王"
    code = db.Column(db.String(50), nullable=False)  # 风格代码，如"william"
    description = db.Column(db.String(200))  # 风格描述
    image_url = db.Column(db.String(500), nullable=False)  # 图片URL
    design_image_url = db.Column(db.String(500))  # 设计水印图片URL（用于选片页面预览）
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # ⭐ AI工作流相关字段（新增）- 图片级别配置（覆盖分类配置）
    workflow_name = db.Column(db.String(200))  # 工作流名称（不含.json），如果为空则使用分类配置
    workflow_file = db.Column(db.String(200))  # 工作流文件名（含.json）
    workflow_input_ids = db.Column(db.Text)  # 输入图片节点ID（JSON数组字符串）
    workflow_output_id = db.Column(db.String(50))  # 输出节点ID
    workflow_ref_id = db.Column(db.String(50))  # 参考图节点ID（可选）
    workflow_ref_image = db.Column(db.String(500))  # 参考图文件名（可选）
    workflow_user_prompt_id = db.Column(db.String(50))  # 用户预设提示词节点ID（可选）
    workflow_custom_prompt_id = db.Column(db.String(50))  # 自定义提示词节点ID（可选）
    workflow_custom_prompt_content = db.Column(db.Text)  # 自定义提示词内容（可选）
    is_ai_enabled = db.Column(db.Boolean)  # 是否启用AI工作流（如果为None，继承分类配置）

# ============================================================================
# 首页相关模型
# ============================================================================

class HomepageBanner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))  # 轮播图标题
    subtitle = db.Column(db.String(200))  # 副标题
    image_url = db.Column(db.String(500), nullable=False)  # 图片URL
    link = db.Column(db.String(200))  # 跳转链接
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)

class WorksGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)  # 图片URL
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class HomepageConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))  # 首页标题
    subtitle = db.Column(db.String(200))  # 首页副标题
    description = db.Column(db.Text)  # 首页描述
    enable_custom_order = db.Column(db.Boolean, default=True)  # 启用定制功能
    enable_style_library = db.Column(db.Boolean, default=True)  # 启用风格库
    enable_product_gallery = db.Column(db.Boolean, default=True)  # 启用产品馆
    enable_works_gallery = db.Column(db.Boolean, default=True)  # 启用作品展示
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# ============================================================================
# 用户相关模型
# ============================================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'operator', 'merchant'
    commission_rate = db.Column(db.Float, default=0.2)  # 分佣比例，默认为20%
    qr_code = db.Column(db.String(100), unique=True)  # 二维码标识
    contact_person = db.Column(db.String(100))  # 联系人
    contact_phone = db.Column(db.String(20))  # 联系电话
    wechat_id = db.Column(db.String(50))  # 微信号
    # 新增字段
    cooperation_date = db.Column(db.Date)  # 合作时间
    merchant_address = db.Column(db.Text)  # 商家地址
    account_name = db.Column(db.String(100))  # 银行账户户名
    account_number = db.Column(db.String(50))  # 银行卡号
    bank_name = db.Column(db.String(100))  # 开户行

class UserVisit(db.Model):
    """用户访问追踪表"""
    __tablename__ = 'user_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)  # 会话ID
    openid = db.Column(db.String(50))  # 微信OpenID
    user_id = db.Column(db.String(50))  # 用户ID
    visit_time = db.Column(db.DateTime, default=datetime.now)  # 访问时间
    source = db.Column(db.String(20), default='miniprogram')  # 来源
    promotion_code = db.Column(db.String(20))  # 推广码
    referrer_user_id = db.Column(db.String(50))  # 推广者用户ID
    scene = db.Column(db.String(100))  # 扫码场景参数
    user_info = db.Column(db.Text)  # 用户信息
    visit_type = db.Column(db.String(20), default='scan')  # 访问类型
    is_authorized = db.Column(db.Boolean, default=False)  # 是否已授权
    is_registered = db.Column(db.Boolean, default=False)  # 是否已注册
    has_ordered = db.Column(db.Boolean, default=False)  # 是否已下单
    ip_address = db.Column(db.String(50))  # IP地址
    user_agent = db.Column(db.Text)  # 用户代理
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# ============================================================================
# 订单相关模型
# ============================================================================

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    size = db.Column(db.String(20))  # 尺寸
    style_name = db.Column(db.String(100))  # 艺术风格名称
    product_name = db.Column(db.String(100))  # 产品名称
    original_image = db.Column(db.String(200))  # 原图路径（兼容旧字段，取第一张）
    final_image = db.Column(db.String(200))  # 成品图路径（有水印）
    final_image_clean = db.Column(db.String(200))  # 成品图路径（无水印）
    hd_image = db.Column(db.String(200))  # 高清放大图路径（有水印）
    hd_image_clean = db.Column(db.String(200))  # 高清放大图路径（无水印）
    status = db.Column(db.String(20), default='paid')  # 订单状态流程：paid(已支付) -> shooting(正在拍摄) -> retouching(美颜处理中) -> ai_processing(AI任务处理中) -> pending_selection(待选片) -> selection_completed(已选片) -> printing(打印中) -> pending_shipment(待发货) -> shipped(已发货)
    shipping_info = db.Column(db.String(500))  # 物流信息（兼容旧字段）
    customer_address = db.Column(db.Text)  # 客户收货地址
    logistics_info = db.Column(db.Text)  # 快递物流信息（JSON格式）
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    merchant = db.relationship('User', backref=db.backref('orders', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.now)
    shooting_completed_at = db.Column(db.DateTime)  # 拍摄完成时间（自拍机上传照片的时间）
    retouch_completed_at = db.Column(db.DateTime)  # 精修美颜完成时间（后台上传精修图的时间）
    completed_at = db.Column(db.DateTime)  # 制作完成时间（后台上传效果图的时间）
    commission = db.Column(db.Float, default=0.0)  # 佣金金额
    price = db.Column(db.Float, default=0.0)  # 订单价格
    payment_time = db.Column(db.DateTime)  # 支付时间
    transaction_id = db.Column(db.String(100))  # 微信支付交易号
    external_platform = db.Column(db.String(50))  # 外部渠道（如 淘宝/抖音/小红书/公众号）
    external_order_number = db.Column(db.String(100))  # 外部平台订单号
    source_type = db.Column(db.String(20), default='website')  # 数据来源类型：miniprogram/website/api
    
    # 冲印系统发送状态跟踪
    printer_send_status = db.Column(db.String(20), default='not_sent')  # not_sent, sending, sent_success, sent_failed
    printer_send_time = db.Column(db.DateTime)  # 发送时间
    printer_error_message = db.Column(db.Text)  # 发送失败的错误信息
    printer_response_data = db.Column(db.Text)
    
    # 推广码相关字段
    promotion_code = db.Column(db.String(20))  # 推广码
    referrer_user_id = db.Column(db.String(50))  # 推广者用户ID
    
    # 加盟商相关字段
    franchisee_id = db.Column(db.Integer, db.ForeignKey('franchisee_accounts.id'))  # 加盟商ID
    franchisee_deduction = db.Column(db.Float, default=0.0)  # 加盟商扣除金额
    product_type = db.Column(db.String(20))  # 产品类型：standard, premium, luxury
    
    # 确版相关字段
    need_confirmation = db.Column(db.Boolean, default=False)  # 是否需要确版
    franchisee_confirmed = db.Column(db.Boolean, default=False)  # 加盟商是否已确认
    franchisee_confirmed_at = db.Column(db.DateTime)  # 加盟商确认时间
    confirmation_deadline = db.Column(db.DateTime)  # 确版截止时间
    skipped_production = db.Column(db.Boolean, default=False)  # 是否跳过制作
    
    # 自定义字段值（JSON格式存储，如 {"宠物数量": "2", "颜色": "红色"}）
    custom_fields = db.Column(db.Text)  # JSON格式存储产品自定义字段的值
    
    # 备注字段
    customer_note = db.Column(db.Text)  # 客户备注
    
    # 用户openid字段（用于发送通知）
    openid = db.Column(db.String(100))  # 下单用户的微信openid
    
    # 门店和自拍机信息
    store_name = db.Column(db.String(100))  # 门店名称
    selfie_machine_id = db.Column(db.String(100))  # 自拍机序列号

class OrderImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    is_main = db.Column(db.Boolean, default=False, nullable=False)  # 是否为主图

# ============================================================================
# AI工作流相关模型
# ============================================================================

class AITask(db.Model):
    """AI工作流任务"""
    __tablename__ = 'ai_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    order = db.relationship('Order', backref=db.backref('ai_tasks', lazy=True))
    order_number = db.Column(db.String(50), nullable=False)  # 订单号（冗余字段，便于查询）
    
    # 工作流配置信息（保存任务创建时的配置）
    workflow_name = db.Column(db.String(200))  # 工作流名称
    workflow_file = db.Column(db.String(200))  # 工作流文件名
    style_category_id = db.Column(db.Integer, db.ForeignKey('style_category.id'))  # 风格分类ID
    style_image_id = db.Column(db.Integer, db.ForeignKey('style_image.id'))  # 风格图片ID
    
    # 输入图片信息
    input_image_path = db.Column(db.String(500))  # 输入图片路径（原图或美颜后的图）
    input_image_type = db.Column(db.String(20), default='original')  # original/retouched
    
    # ComfyUI任务信息
    comfyui_prompt_id = db.Column(db.String(100))  # ComfyUI返回的prompt_id
    comfyui_node_id = db.Column(db.String(50))  # 输出节点ID
    
    # 任务状态
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, cancelled
    # pending: 待处理
    # processing: 处理中
    # completed: 已完成
    # failed: 失败
    # cancelled: 已取消
    
    # 输出结果
    output_image_path = db.Column(db.String(500))  # 输出图片路径（效果图）
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.now)  # 任务创建时间
    started_at = db.Column(db.DateTime)  # 任务开始处理时间
    completed_at = db.Column(db.DateTime)  # 任务完成时间
    estimated_completion_time = db.Column(db.DateTime)  # 预计完成时间
    
    # 错误信息
    error_message = db.Column(db.Text)  # 错误信息
    error_code = db.Column(db.String(50))  # 错误代码
    retry_count = db.Column(db.Integer, default=0)  # 重试次数
    
    # 处理信息
    processing_log = db.Column(db.Text)  # 处理日志（JSON格式）
    comfyui_response = db.Column(db.Text)  # ComfyUI响应数据（JSON格式）
    
    # 备注
    notes = db.Column(db.Text)  # 备注信息

class AIConfig(db.Model):
    """AI工作流系统配置"""
    __tablename__ = 'ai_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)  # 配置键
    config_value = db.Column(db.Text)  # 配置值
    description = db.Column(db.String(200))  # 配置说明
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 常用配置键：
    # 'comfyui_base_url' - ComfyUI服务器地址，如 'http://sm003:8188'
    # 'comfyui_api_endpoint' - API端点，如 '/api/prompt'
    # 'comfyui_timeout' - 超时时间（秒）
    # 'prefer_retouched_image' - 是否优先使用美颜后的图片（true/false）
    # 'auto_retry_on_failure' - 失败后是否自动重试（true/false）
    # 'max_retry_count' - 最大重试次数

class MeituAPIConfig(db.Model):
    """美图API配置"""
    __tablename__ = 'meitu_api_config'
    
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(100), nullable=True, comment='应用ID (APPID)')
    api_key = db.Column(db.String(100), nullable=False, comment='API密钥 (APIKEY)')
    api_secret = db.Column(db.String(100), nullable=False, comment='API密钥 (SECRETID)')
    api_base_url = db.Column(db.String(200), default='https://api.yunxiu.meitu.com', comment='API基础URL')
    api_endpoint = db.Column(db.String(200), default='/openapi/realphotolocal_async', comment='API接口路径')
    repost_url = db.Column(db.String(500), nullable=True, comment='回调URL（可选）')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    enable_in_workflow = db.Column(db.Boolean, default=False, comment='是否在订单处理流程中启用美颜API（开启后，上传原图会先经过美图API处理，再调用AI工作流）')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 兼容旧字段（如果app_id字段不存在，从api_key获取）
    def _get_app_id(self):
        if hasattr(self, 'app_id') and self.app_id:
            return self.app_id
        return self.api_key if hasattr(self, 'api_key') else None
    
    @property
    def app_key(self):
        return self.api_key
    
    @property
    def secret_id(self):
        return self.api_secret
    
    def to_dict(self):
        return {
            'id': self.id,
            'api_key': self.api_key if hasattr(self, 'api_key') else (self.app_id if hasattr(self, 'app_id') else ''),
            'api_secret': self.api_secret if hasattr(self, 'api_secret') else (self.secret_id if hasattr(self, 'secret_id') else ''),
            'api_base_url': self.api_base_url,
            'api_endpoint': self.api_endpoint if hasattr(self, 'api_endpoint') else '/openapi/realphotolocal_async',
            'repost_url': self.repost_url if hasattr(self, 'repost_url') else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # 兼容旧字段
            'app_id': getattr(self, 'app_id', None) or '',
            'secret_id': self.api_secret if hasattr(self, 'api_secret') else ''
        }

class MeituAPIPreset(db.Model):
    """美图API预设配置（可关联到风格分类或单个风格图片）"""
    __tablename__ = 'meitu_api_preset'
    
    id = db.Column(db.Integer, primary_key=True)
    style_category_id = db.Column(db.Integer, db.ForeignKey('style_category.id'), nullable=True, comment='风格分类ID（映射到整个分类）')
    style_image_id = db.Column(db.Integer, db.ForeignKey('style_image.id'), nullable=True, comment='风格图片ID（映射到单个图片）')
    preset_id = db.Column(db.String(100), nullable=False, comment='预设ID')
    preset_name = db.Column(db.String(200), comment='预设名称')
    description = db.Column(db.Text, comment='描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    style_category = db.relationship('StyleCategory', backref=db.backref('meitu_presets', lazy=True))
    style_image = db.relationship('StyleImage', backref=db.backref('meitu_presets', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'style_category_id': self.style_category_id,
            'style_category_name': self.style_category.name if self.style_category else None,
            'style_image_id': self.style_image_id,
            'style_image_name': self.style_image.name if self.style_image else None,
            'mapping_type': 'category' if self.style_category_id else 'image',
            'preset_id': self.preset_id,
            'preset_name': self.preset_name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MeituAPICallLog(db.Model):
    """美图API调用记录"""
    __tablename__ = 'meitu_api_call_log'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, comment='订单ID')
    order_number = db.Column(db.String(50), comment='订单号')
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True, comment='产品ID')
    preset_id = db.Column(db.String(100), comment='使用的预设ID')
    request_url = db.Column(db.String(500), comment='请求URL')
    request_params = db.Column(db.Text, comment='请求参数（JSON）')
    response_status = db.Column(db.Integer, comment='响应状态码')
    response_data = db.Column(db.Text, comment='响应数据（JSON）')
    msg_id = db.Column(db.String(100), comment='美图API返回的msg_id（用于查询结果）')
    result_image_url = db.Column(db.String(500), comment='结果图片URL')
    result_image_path = db.Column(db.String(500), comment='结果图片本地路径')
    error_message = db.Column(db.Text, comment='错误信息')
    duration_ms = db.Column(db.Integer, comment='请求耗时（毫秒）')
    status = db.Column(db.String(20), default='pending', comment='状态：pending, success, failed')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order_number,
            'product_id': self.product_id,
            'preset_id': self.preset_id,
            'request_url': self.request_url,
            'request_params': self.request_params,
            'response_status': self.response_status,
            'response_data': self.response_data,
            'msg_id': getattr(self, 'msg_id', None),  # 美图API返回的msg_id
            'result_image_url': self.result_image_url,
            'result_image_path': self.result_image_path,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# 云端API服务商相关模型
# ============================================================================

class APIProviderConfig(db.Model):
    """API服务商配置表"""
    __tablename__ = 'api_provider_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='配置名称')
    api_type = db.Column(db.String(50), default='nano-banana', comment='API类型：nano-banana, gemini-native, veo-video等')
    host_overseas = db.Column(db.String(200), comment='海外Host')
    host_domestic = db.Column(db.String(200), comment='国内直连Host')
    api_key = db.Column(db.String(500), comment='API Key')
    draw_endpoint = db.Column(db.String(200), default='/v1/draw/nano-banana', comment='绘画接口')
    result_endpoint = db.Column(db.String(200), default='/v1/draw/result', comment='获取结果接口')
    file_upload_endpoint = db.Column(db.String(200), default='/v1/file/upload', comment='文件上传接口')
    model_name = db.Column(db.String(100), comment='模型名称')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认配置')
    enable_retry = db.Column(db.Boolean, default=True, comment='是否启用重试（参与自动重试机制）')
    is_sync_api = db.Column(db.Boolean, default=False, comment='是否同步API（True=同步API，False=异步API）')
    priority = db.Column(db.Integer, default=0, comment='优先级（数字越大优先级越高）')
    description = db.Column(db.Text, comment='配置描述')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'api_type': self.api_type,
            'host_overseas': self.host_overseas,
            'host_domestic': self.host_domestic,
            'api_key': self.api_key,
            'draw_endpoint': self.draw_endpoint,
            'result_endpoint': self.result_endpoint,
            'file_upload_endpoint': self.file_upload_endpoint,
            'model_name': self.model_name,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'enable_retry': self.enable_retry,
            'is_sync_api': self.is_sync_api if hasattr(self, 'is_sync_api') else False,
            'priority': self.priority,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class APITemplate(db.Model):
    """API调用模板配置（关联到风格分类或风格图片）"""
    __tablename__ = 'api_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    style_category_id = db.Column(db.Integer, db.ForeignKey('style_category.id'), nullable=True, comment='风格分类ID（分类级别配置）')
    style_image_id = db.Column(db.Integer, db.ForeignKey('style_image.id'), nullable=True, comment='风格图片ID（图片级别配置，优先级更高）')
    api_config_id = db.Column(db.Integer, db.ForeignKey('api_provider_configs.id'), nullable=True, comment='关联的API配置ID')
    model_name = db.Column(db.String(100), comment='模型名称（如果API配置中已有，可覆盖）')
    default_prompt = db.Column(db.Text, comment='默认提示词（单个提示词，向后兼容）')
    prompts_json = db.Column(db.Text, comment='批量提示词（JSON格式），例如：["提示词1", "提示词2"]。如果设置了此字段，将使用此字段创建多个任务')
    default_size = db.Column(db.String(20), default='1K', comment='默认尺寸：1K, 2K, 4K等')
    default_aspect_ratio = db.Column(db.String(20), default='auto', comment='默认比例：auto, 1:1, 16:9等')
    points_cost = db.Column(db.Integer, default=0, comment='每次生成消耗的积分')
    prompt_editable = db.Column(db.Boolean, default=True, comment='提示词是否可编辑')
    size_editable = db.Column(db.Boolean, default=True, comment='尺寸是否可编辑')
    aspect_ratio_editable = db.Column(db.Boolean, default=True, comment='比例是否可编辑')
    enhance_prompt = db.Column(db.Boolean, default=False, comment='是否优化提示词（VEO模型：中文自动转英文）')
    upload_config = db.Column(db.Text, comment='上传配置（JSON格式），例如：{"uploads": [{"name": "参考图", "key": "reference"}]}')
    request_body_template = db.Column(db.Text, comment='请求体模板（JSON格式，用于自定义请求参数）')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    style_category = db.relationship('StyleCategory', backref=db.backref('api_templates', lazy=True))
    style_image = db.relationship('StyleImage', backref=db.backref('api_templates', lazy=True))
    api_config = db.relationship('APIProviderConfig', backref=db.backref('api_templates', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'style_category_id': self.style_category_id,
            'style_image_id': self.style_image_id,
            'api_config_id': self.api_config_id,
            'api_config_name': self.api_config.name if self.api_config else None,
            'model_name': self.model_name,
            'default_prompt': self.default_prompt,
            'prompts_json': self.prompts_json,  # 批量提示词
            'default_size': self.default_size,
            'default_aspect_ratio': self.default_aspect_ratio,
            'points_cost': self.points_cost,
            'prompt_editable': self.prompt_editable,
            'size_editable': self.size_editable,
            'aspect_ratio_editable': self.aspect_ratio_editable,
            'enhance_prompt': self.enhance_prompt,
            'upload_config': self.upload_config,
            'request_body_template': self.request_body_template,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# 其他模型
# ============================================================================

class PhotoSignup(db.Model):
    """宠物摄影报名表"""
    __tablename__ = 'photo_signup'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    pet_breed = db.Column(db.String(50), nullable=False)
    pet_weight = db.Column(db.String(50), nullable=True)
    pet_age = db.Column(db.String(50), nullable=True)
    pet_character = db.Column(db.String(500))
    available_date = db.Column(db.String(50))
    additional_notes = db.Column(db.String(500))
    
    # 宠物图片字段
    pet_images = db.Column(db.Text)  # JSON字符串存储图片URL列表
    
    # 推广相关字段
    user_id = db.Column(db.String(100))
    referrer_user_id = db.Column(db.String(100))
    referrer_promotion_code = db.Column(db.String(50))
    source = db.Column(db.String(50), default='miniprogram_carousel')
    
    # 状态字段
    status = db.Column(db.String(20), default='pending')  # pending, contacted, contact_failed, scheduled, completed, cancelled
    notes = db.Column(db.String(1000))  # 内部备注
    
    # 联系状态标记
    contact_no_answer = db.Column(db.Boolean, default=False)  # 电话未打通
    contact_success = db.Column(db.Boolean, default=False)  # 电话已打通
    
    # 时间字段
    submit_time = db.Column(db.DateTime, default=datetime.utcnow)
    contact_time = db.Column(db.DateTime)
    schedule_time = db.Column(db.DateTime)
    store_visit_time = db.Column(db.String(50))  # 到店时间（字符串格式，如"2025-10-01 14:30"）
    complete_time = db.Column(db.DateTime)

# ============================================================================
# 推广相关模型
# ============================================================================

class PromotionUser(db.Model):
    """推广用户表 - 小程序用户"""
    __tablename__ = 'promotion_users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)  # 小程序用户ID
    promotion_code = db.Column(db.String(20), unique=True, nullable=False)  # 推广码
    open_id = db.Column(db.String(100))  # 微信OpenID
    nickname = db.Column(db.String(100))  # 用户昵称
    avatar_url = db.Column(db.String(200))  # 头像URL
    phone_number = db.Column(db.String(20))  # 手机号
    total_earnings = db.Column(db.Float, default=0.0)  # 总收益
    total_orders = db.Column(db.Integer, default=0)  # 推广订单数
    eligible_for_promotion = db.Column(db.Boolean, default=False)  # 是否有推广资格（是否下过单）
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Commission(db.Model):
    """分佣记录表"""
    __tablename__ = 'commissions'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), nullable=False)  # 订单ID
    referrer_user_id = db.Column(db.String(50), nullable=False)  # 推广者用户ID
    amount = db.Column(db.Float, nullable=False)  # 佣金金额
    rate = db.Column(db.Float, nullable=False)  # 佣金比例
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    create_time = db.Column(db.DateTime, default=datetime.now)
    complete_time = db.Column(db.DateTime)  # 完成时间

class Withdrawal(db.Model):
    """提现申请表"""
    __tablename__ = 'withdrawals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # 用户ID
    user_phone = db.Column(db.String(20), nullable=False)  # 用户手机号
    amount = db.Column(db.Float, nullable=False)  # 提现金额
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    apply_time = db.Column(db.DateTime, default=datetime.now)  # 申请时间
    approve_time = db.Column(db.DateTime)  # 审核时间
    complete_time = db.Column(db.DateTime)  # 完成时间
    admin_notes = db.Column(db.Text)  # 管理员备注
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class PromotionTrack(db.Model):
    """推广访问追踪表"""
    __tablename__ = 'promotion_tracks'
    
    id = db.Column(db.Integer, primary_key=True)
    promotion_code = db.Column(db.String(20), nullable=False)  # 推广码
    referrer_user_id = db.Column(db.String(50), nullable=False)  # 推广者用户ID
    visitor_user_id = db.Column(db.String(50))  # 访问者用户ID
    visit_time = db.Column(db.BigInteger, nullable=False)  # 访问时间戳
    create_time = db.Column(db.DateTime, default=datetime.now)

# ============================================================================
# 优惠券相关模型
# ============================================================================

class Coupon(db.Model):
    """优惠券表"""
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 优惠券名称
    code = db.Column(db.String(20), unique=True, nullable=False)  # 优惠券代码
    type = db.Column(db.String(20), nullable=False)  # 类型：discount(折扣), cash(现金), free(免费)
    value = db.Column(db.Float, nullable=False)  # 优惠金额或折扣比例
    min_amount = db.Column(db.Float, default=0.0)  # 最低消费金额
    max_discount = db.Column(db.Float)  # 最大折扣金额（折扣券使用）
    total_count = db.Column(db.Integer, nullable=False)  # 总发放数量
    used_count = db.Column(db.Integer, default=0)  # 已使用数量
    per_user_limit = db.Column(db.Integer, default=1)  # 每用户限领数量
    start_time = db.Column(db.DateTime, nullable=False)  # 开始时间
    end_time = db.Column(db.DateTime, nullable=False)  # 结束时间
    status = db.Column(db.String(20), default='active')  # 状态：active, inactive, expired
    description = db.Column(db.Text)  # 优惠券描述
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 新增字段：优惠券来源和类型扩展
    source_type = db.Column(db.String(20), default='system')  # 来源类型：system系统, groupon团购, share分享, store门店
    groupon_order_id = db.Column(db.String(100))  # 团购订单ID（团购核销券使用）
    verify_amount = db.Column(db.Float)  # 核销金额（团购券使用）
    is_random_code = db.Column(db.Boolean, default=False)  # 是否为随机码券
    qr_code_url = db.Column(db.String(500))  # 领取二维码URL
    share_reward_amount = db.Column(db.Float)  # 分享奖励金额
    share_reward_type = db.Column(db.String(20))  # 分享奖励类型：sharer分享者, shared被分享者

class UserCoupon(db.Model):
    """用户优惠券表"""
    __tablename__ = 'user_coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # 用户ID
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)  # 优惠券ID
    coupon_code = db.Column(db.String(20), nullable=False)  # 优惠券代码
    status = db.Column(db.String(20), default='unused')  # 状态：unused, used, expired
    order_id = db.Column(db.String(50))  # 使用的订单ID
    get_time = db.Column(db.DateTime, default=datetime.now)  # 领取时间
    use_time = db.Column(db.DateTime)  # 使用时间
    expire_time = db.Column(db.DateTime)  # 过期时间
    
    # 关联关系
    coupon = db.relationship('Coupon', backref='user_coupons')

class ShareRecord(db.Model):
    """分享记录表"""
    __tablename__ = 'share_records'
    
    id = db.Column(db.Integer, primary_key=True)
    sharer_user_id = db.Column(db.String(50), nullable=False)  # 分享者用户ID
    shared_user_id = db.Column(db.String(50))  # 被分享者用户ID
    share_type = db.Column(db.String(20), default='work')  # 分享类型：work作品分享
    work_id = db.Column(db.Integer)  # 作品ID
    order_id = db.Column(db.Integer)  # 下单订单ID
    sharer_coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'))  # 分享者获得的优惠券ID
    shared_coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'))  # 被分享者获得的优惠券ID
    status = db.Column(db.String(20), default='pending')  # 状态：pending待下单, completed已完成
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    sharer_coupon = db.relationship('Coupon', foreign_keys=[sharer_coupon_id], backref='sharer_records')
    shared_coupon = db.relationship('Coupon', foreign_keys=[shared_coupon_id], backref='shared_records')

# ============================================================================
# 加盟商相关模型
# ============================================================================

class FranchiseeAccount(db.Model):
    """加盟商账户表"""
    __tablename__ = 'franchisee_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # 加盟商用户名
    password = db.Column(db.String(100), nullable=False)  # 密码
    company_name = db.Column(db.String(100), nullable=False)  # 公司名称
    contact_person = db.Column(db.String(50), nullable=False)  # 联系人
    contact_phone = db.Column(db.String(20), nullable=False)  # 联系电话
    contact_email = db.Column(db.String(100))  # 联系邮箱
    address = db.Column(db.Text)  # 公司地址
    business_license = db.Column(db.String(200))  # 营业执照图片路径
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    total_quota = db.Column(db.Float, default=0.0)  # 总充值额度
    used_quota = db.Column(db.Float, default=0.0)  # 已使用额度
    remaining_quota = db.Column(db.Float, default=0.0)  # 剩余额度
    qr_code = db.Column(db.String(100), unique=True)  # 加盟商二维码标识
    watermark_path = db.Column(db.String(200))  # 加盟商专属水印图片路径
    printer_shop_id = db.Column(db.String(50))  # 厂家影楼编号（可选，如果为空则使用默认配置）
    printer_shop_name = db.Column(db.String(100))  # 厂家影楼名称（可选，如果为空则使用默认配置）
    
    # 门店和自拍机信息（保留字段，用于向后兼容，实际使用SelfieMachine表）
    store_name = db.Column(db.String(100))  # 门店名称
    machine_name = db.Column(db.String(100))  # 自拍机名称（已废弃，使用SelfieMachine表）
    machine_serial_number = db.Column(db.String(100))  # 自拍机序列号（已废弃，使用SelfieMachine表）
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    recharge_records = db.relationship('FranchiseeRecharge', backref='franchisee', lazy=True)
    orders = db.relationship('Order', backref='franchisee_account', lazy=True)

class FranchiseeRecharge(db.Model):
    """加盟商充值记录表"""
    __tablename__ = 'franchisee_recharges'
    
    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey('franchisee_accounts.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # 充值金额（加盟商看到的金额）
    bonus_amount = db.Column(db.Float, default=0.0)  # 赠送金额（内部记录，不显示给加盟商）
    total_amount = db.Column(db.Float, nullable=False)  # 实际充值总额（amount + bonus_amount）
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 操作管理员
    admin_user = db.relationship('User', backref='franchisee_recharges')
    recharge_type = db.Column(db.String(20), default='manual')  # manual, refund, adjustment
    description = db.Column(db.Text)  # 充值说明
    created_at = db.Column(db.DateTime, default=datetime.now)

class SelfieMachine(db.Model):
    """自拍机设备表"""
    __tablename__ = 'selfie_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey('franchisee_accounts.id'), nullable=False)  # 关联的加盟商账户
    machine_name = db.Column(db.String(100), nullable=False)  # 自拍机名称
    machine_serial_number = db.Column(db.String(100), unique=True, nullable=False)  # 自拍机序列号（唯一）
    location = db.Column(db.String(200))  # 设备位置（可选）
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance
    notes = db.Column(db.Text)  # 备注信息
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    franchisee = db.relationship('FranchiseeAccount', backref=db.backref('selfie_machines', lazy=True, cascade='all, delete-orphan'))

class StaffUser(db.Model):
    """店员用户表 - 加盟商的子用户，用于权限管理"""
    __tablename__ = 'staff_users'
    
    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey('franchisee_accounts.id'), nullable=False)  # 关联的加盟商账户
    franchisee = db.relationship('FranchiseeAccount', backref='staff_users')
    
    # 用户标识（二选一）
    phone = db.Column(db.String(20))  # 手机号（优先使用）
    openid = db.Column(db.String(100))  # 微信openid（备用）
    
    # 用户信息
    name = db.Column(db.String(50))  # 姓名
    role = db.Column(db.String(50), default='staff')  # 角色：staff店员, manager经理等
    
    # 权限配置（JSON格式存储）
    # 例如：{"view_today_orders": true, "view_store_images": true, "view_all_orders": false}
    permissions = db.Column(db.Text, default='{}')  # JSON格式的权限配置
    
    # 状态
    status = db.Column(db.String(20), default='active')  # active, inactive
    
    # 备注
    notes = db.Column(db.Text)  # 备注信息
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 唯一约束：同一加盟商下，手机号或openid不能重复
    __table_args__ = (
        db.Index('idx_franchisee_phone', 'franchisee_id', 'phone'),
        db.Index('idx_franchisee_openid', 'franchisee_id', 'openid'),
    )

# ============================================================================
# 商城相关模型（实物产品）
# ============================================================================

class ShopProduct(db.Model):
    """商城产品表（实物产品：相框、T恤、抱枕等）"""
    __tablename__ = 'shop_products'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # 产品代码，如 photo_frame
    name = db.Column(db.String(100), nullable=False)  # 产品名称，如 精美相框
    description = db.Column(db.Text)  # 产品描述
    category = db.Column(db.String(50))  # 产品分类：photo_frame, t_shirt, pillow等
    image_url = db.Column(db.String(500))  # 主图URL
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class ShopProductImage(db.Model):
    """商城产品图片表"""
    __tablename__ = 'shop_product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('shop_products.id'), nullable=False)
    product = db.relationship('ShopProduct', backref=db.backref('images', lazy=True, cascade='all, delete-orphan'))
    image_url = db.Column(db.String(500), nullable=False)  # 图片URL
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)

class ShopProductSize(db.Model):
    """商城产品规格表（尺寸、颜色等）"""
    __tablename__ = 'shop_product_sizes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('shop_products.id'), nullable=False)
    product = db.relationship('ShopProduct', backref=db.backref('sizes', lazy=True, cascade='all, delete-orphan'))
    size_name = db.Column(db.String(100), nullable=False)  # 规格名称，如 "A4尺寸"、"红色"、"大号"
    price = db.Column(db.Float, nullable=False)  # 价格
    stock = db.Column(db.Integer, default=0)  # 库存（0表示不限）
    effect_image_url = db.Column(db.String(500))  # 效果图URL（用于选片页面显示）
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.now)

class ShopOrder(db.Model):
    """商城订单表（实物产品订单）"""
    __tablename__ = 'shop_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)  # 商城订单号
    original_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # 关联的原始订单ID（AI写真订单）
    original_order = db.relationship('Order', backref=db.backref('shop_orders', lazy=True))
    original_order_number = db.Column(db.String(50))  # 原始订单号（冗余字段，便于查询）
    
    # 用户信息
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    openid = db.Column(db.String(100))  # 微信openid
    customer_address = db.Column(db.Text, nullable=False)  # 收货地址
    
    # 产品信息
    product_id = db.Column(db.Integer, db.ForeignKey('shop_products.id'), nullable=False)
    product = db.relationship('ShopProduct', backref=db.backref('orders', lazy=True))
    product_name = db.Column(db.String(100), nullable=False)  # 产品名称（冗余字段）
    size_id = db.Column(db.Integer, db.ForeignKey('shop_product_sizes.id'), nullable=False)
    size = db.relationship('ShopProductSize', backref=db.backref('orders', lazy=True))
    size_name = db.Column(db.String(100), nullable=False)  # 规格名称（冗余字段）
    
    # 使用的图片（从原始订单中选择）
    image_url = db.Column(db.String(500))  # 使用的图片URL（来自原始订单的效果图）
    
    # 订单信息
    quantity = db.Column(db.Integer, default=1, nullable=False)  # 数量
    price = db.Column(db.Float, nullable=False)  # 单价
    total_price = db.Column(db.Float, nullable=False)  # 总价
    status = db.Column(db.String(20), default='pending')  # pending, paid, processing, shipped, completed, cancelled
    # pending: 待支付
    # paid: 已支付
    # processing: 处理中
    # shipped: 已发货
    # completed: 已完成
    # cancelled: 已取消
    
    # 物流信息
    logistics_info = db.Column(db.Text)  # 快递物流信息（JSON格式）
    shipping_time = db.Column(db.DateTime)  # 发货时间
    
    # 支付信息
    payment_time = db.Column(db.DateTime)  # 支付时间
    transaction_id = db.Column(db.String(100))  # 微信支付交易号
    
    # 备注
    customer_note = db.Column(db.Text)  # 客户备注
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间


# ============================================================================
# 打印配置相关模型
# ============================================================================

class PrintSizeConfig(db.Model):
    """打印尺寸配置表（根据商城产品配置不同的打印参数）"""
    __tablename__ = 'print_size_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('shop_products.id'), nullable=True)  # 关联商城产品ID（null表示默认配置，用于纯照片打印）
    product = db.Column(db.String(100))  # 产品名称（冗余字段，便于显示）
    size_id = db.Column(db.Integer, db.ForeignKey('shop_product_sizes.id'), nullable=True)  # 关联产品规格ID（可选）
    size_name = db.Column(db.String(100))  # 规格名称（冗余字段）
    
    # 打印尺寸参数（单位：厘米）
    print_width_cm = db.Column(db.Float, nullable=False)  # 打印宽度（厘米）
    print_height_cm = db.Column(db.Float, nullable=False)  # 打印高度（厘米）
    
    # 裁切参数（单位：像素或百分比）
    crop_x = db.Column(db.Float, default=0.0)  # 裁切起始X坐标（像素或百分比）
    crop_y = db.Column(db.Float, default=0.0)  # 裁切起始Y坐标（像素或百分比）
    crop_width = db.Column(db.Float)  # 裁切宽度（像素或百分比，null表示不裁切）
    crop_height = db.Column(db.Float)  # 裁切高度（像素或百分比，null表示不裁切）
    crop_mode = db.Column(db.String(20), default='center')  # 裁切模式：center（居中）、top（顶部）、bottom（底部）、left（左侧）、right（右侧）、custom（自定义）
    
    # 打印模板参数
    template_name = db.Column(db.String(100))  # 打印模板名称（如：4x6证件照、A4相框等）
    dpi = db.Column(db.Integer, default=300)  # 打印分辨率（DPI）
    color_mode = db.Column(db.String(20), default='RGB')  # 颜色模式：RGB、CMYK
    
    # 产品ID映射（用于冲印系统）
    printer_product_id = db.Column(db.String(50))  # 冲印系统产品ID
    printer_product_name = db.Column(db.String(100))  # 冲印系统产品名称
    
    # 是否启用
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 备注
    notes = db.Column(db.Text)  # 配置说明
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# ============================================================================
# 风格代码处理辅助函数
# ============================================================================

def _sanitize_style_code(raw_code):
    """将任意风格代码清洗成只含数字/字母/短横线的形式"""
    if not raw_code:
        return ''
    normalized = unicodedata.normalize('NFKD', str(raw_code))
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii') or str(raw_code)
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r'[^a-z0-9-]+', '-', ascii_text)
    ascii_text = re.sub(r'-{2,}', '-', ascii_text).strip('-')
    return ascii_text

def _build_style_code(style_name, category_code):
    """根据分类代码和风格名称生成基础风格代码"""
    name_slug = _sanitize_style_code(style_name)
    category_slug = _sanitize_style_code(category_code)
    parts = [part for part in [category_slug, name_slug] if part]
    base_code = '-'.join(parts)
    return base_code or category_slug or 'style'

def _ensure_unique_style_code(base_code, image_id=None):
    """为风格图片生成唯一代码，必要时自动追加序号"""
    base_code = _sanitize_style_code(base_code) or 'style'
    candidate = base_code
    suffix = 2
    while True:
        query = StyleImage.query.filter_by(code=candidate)
        if image_id:
            query = query.filter(StyleImage.id != image_id)
        if not query.first():
            return candidate
        candidate = f"{base_code}-{suffix}"
        suffix += 1
