# -*- coding: utf-8 -*-
"""
通用工具函数
从 test_server.py 迁移通用工具函数
"""

import logging

logger = logging.getLogger(__name__)
import hashlib
import json
import random
import string
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


# 注意：这些函数需要访问数据库模型，所以需要延迟导入
def get_db_models():
    """延迟获取数据库模型（避免循环导入）"""
    try:
        from app.models import Coupon, Order, PromotionUser, UserCoupon

        return {
            "PromotionUser": PromotionUser,
            "Coupon": Coupon,
            "UserCoupon": UserCoupon,
            "Order": Order,
        }
    except ImportError:
        return None


def get_db():
    """延迟获取db实例"""
    try:
        import sys

        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            if hasattr(test_server_module, "db"):
                return test_server_module.db
    except (ImportError, AttributeError):
        pass
    return None


# ============================================================================
# 微信支付相关工具函数
# ============================================================================


def generate_sign(params, api_key):
    """生成微信支付签名"""
    # 过滤空值并排序
    filtered_params = {k: v for k, v in params.items() if v != "" and v is not None}
    sorted_params = sorted(filtered_params.items())

    # 拼接字符串
    string_sign_temp = "&".join([f"{k}={v}" for k, v in sorted_params])
    string_sign_temp += f"&key={api_key}"

    # MD5加密并转大写
    sign = hashlib.md5(string_sign_temp.encode("utf-8")).hexdigest().upper()
    return sign


def verify_sign(params, api_key, sign):
    """验证微信支付签名"""
    expected_sign = generate_sign(params, api_key)
    return expected_sign == sign


def dict_to_xml(data):
    """字典转XML格式"""
    xml = "<xml>"
    for key, value in data.items():
        xml += f"<{key}><![CDATA[{value}]]></{key}>"
    xml += "</xml>"
    return xml


def xml_to_dict(xml_str):
    """XML转字典格式"""
    try:
        root = ET.fromstring(xml_str)
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result
    except ET.ParseError:
        return {}


def generate_nonce_str():
    """生成随机字符串"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


# ============================================================================
# 数据解析工具函数
# ============================================================================


def parse_shipping_info(shipping_info):
    """解析收货信息，处理Unicode编码"""
    if not shipping_info:
        return {}

    try:
        # 直接使用json.loads解析，它会自动处理Unicode转义
        data = json.loads(shipping_info)
        return data
    except json.JSONDecodeError:
        # 如果解析失败，返回空字典
        return {}


def get_product_id_from_size(size):
    """根据尺寸信息获取产品ID"""
    if not size:
        return "未配置"

    # 导入尺寸映射
    try:
        from printer_config import SIZE_MAPPING

        # 直接匹配
        if size in SIZE_MAPPING:
            return SIZE_MAPPING[size]["product_id"]

        # 根据产品名称反向查找
        for key, value in SIZE_MAPPING.items():
            if value["product_name"] == size:
                return value["product_id"]

        # 根据部分匹配查找
        for key, value in SIZE_MAPPING.items():
            if size in value["product_name"] or value["product_name"] in size:
                return value["product_id"]

        return "未配置"
    except ImportError:
        return "未配置"


# ============================================================================
# 推广码相关工具函数
# ============================================================================


def generate_promotion_code(user_id):
    """生成推广码（兼容旧版本）"""
    hash_obj = hashlib.md5(user_id.encode())
    promotion_code = hash_obj.hexdigest()[:8].upper()
    return promotion_code


def generate_stable_promotion_code(openid):
    """基于OpenID生成稳定的推广码"""
    if not openid:
        return None

    hash_obj = hashlib.md5(openid.encode("utf-8"))
    hash_hex = hash_obj.hexdigest()

    # 生成PET开头的5位推广码
    promotion_code = "PET" + hash_hex[:5].upper()

    logger.info(f"基于OpenID生成推广码: {openid} -> {promotion_code}")
    return promotion_code


def generate_stable_user_id(openid):
    """基于OpenID生成稳定的用户ID"""
    if not openid:
        return None

    hash_obj = hashlib.md5(openid.encode("utf-8"))
    hash_hex = hash_obj.hexdigest()

    # 生成USER开头的10位用户ID
    user_id = "USER" + hash_hex[:10].upper()

    logger.info(f"基于OpenID生成用户ID: {openid} -> {user_id}")
    return user_id


def validate_promotion_code(promotion_code):
    """验证推广码有效性"""
    models = get_db_models()
    if not models:
        return None

    PromotionUser = models["PromotionUser"]
    user = PromotionUser.query.filter_by(promotion_code=promotion_code).first()
    return user.user_id if user else None


# ============================================================================
# 优惠券相关工具函数
# ============================================================================


def generate_coupon_code():
    """生成优惠券代码"""
    # 生成8位随机代码
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return code


def validate_coupon_code(code):
    """验证优惠券代码是否已存在"""
    models = get_db_models()
    if not models:
        return True

    Coupon = models["Coupon"]
    existing_coupon = Coupon.query.filter_by(code=code).first()
    return existing_coupon is None


def create_coupon(
    name,
    coupon_type,
    value,
    min_amount=0.0,
    max_discount=None,
    total_count=100,
    per_user_limit=1,
    start_time=None,
    end_time=None,
    description=None,
):
    """创建优惠券"""
    models = get_db_models()
    db = get_db()
    if not models or not db:
        raise RuntimeError("数据库模型或db实例未初始化")

    Coupon = models["Coupon"]

    # 生成唯一代码
    while True:
        code = generate_coupon_code()
        if validate_coupon_code(code):
            break

    # 设置默认时间
    if not start_time:
        start_time = datetime.now()
    if not end_time:
        end_time = start_time + timedelta(days=30)

    coupon = Coupon(
        name=name,
        code=code,
        type=coupon_type,
        value=value,
        min_amount=min_amount,
        max_discount=max_discount,
        total_count=total_count,
        per_user_limit=per_user_limit,
        start_time=start_time,
        end_time=end_time,
        description=description,
    )

    db.session.add(coupon)
    db.session.commit()
    return coupon


def get_user_coupons(user_id, status=None):
    """获取用户优惠券列表"""
    models = get_db_models()
    if not models:
        return []

    UserCoupon = models["UserCoupon"]
    Coupon = models["Coupon"]

    query = UserCoupon.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    coupons = query.join(Coupon).all()
    return coupons


def can_user_get_coupon(user_id, coupon_id):
    """检查用户是否可以领取优惠券"""
    models = get_db_models()
    if not models:
        return False, "数据库模型未初始化"

    Coupon = models["Coupon"]
    UserCoupon = models["UserCoupon"]

    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        return False, "优惠券不存在"

    # 检查优惠券状态
    if coupon.status != "active":
        return False, "优惠券已失效"

    # 检查时间
    now = datetime.now()
    if now < coupon.start_time or now > coupon.end_time:
        return False, "优惠券不在有效期内"

    # 检查库存
    if coupon.used_count >= coupon.total_count:
        return False, "优惠券已领完"

    # 检查用户领取限制
    user_coupon_count = UserCoupon.query.filter_by(user_id=user_id, coupon_id=coupon_id).count()

    if user_coupon_count >= coupon.per_user_limit:
        return False, f"已达到领取限制（最多{coupon.per_user_limit}张）"

    return True, "可以领取"


def user_get_coupon(user_id, coupon_id):
    """用户领取优惠券"""
    models = get_db_models()
    db = get_db()
    if not models or not db:
        return False, "数据库模型或db实例未初始化"

    Coupon = models["Coupon"]
    UserCoupon = models["UserCoupon"]

    can_get, message = can_user_get_coupon(user_id, coupon_id)
    if not can_get:
        return False, message

    coupon = Coupon.query.get(coupon_id)

    # 创建用户优惠券记录
    user_coupon = UserCoupon(
        user_id=user_id, coupon_id=coupon_id, coupon_code=coupon.code, expire_time=coupon.end_time
    )

    db.session.add(user_coupon)
    db.session.commit()

    return True, "领取成功"


def can_use_coupon(user_id, coupon_code, order_amount):
    """检查优惠券是否可以使用"""
    models = get_db_models()
    if not models:
        return False, "数据库模型未初始化"

    UserCoupon = models["UserCoupon"]

    user_coupon = UserCoupon.query.filter_by(
        user_id=user_id, coupon_code=coupon_code, status="unused"
    ).first()

    if not user_coupon:
        return False, "优惠券不存在或已使用"

    coupon = user_coupon.coupon

    # 检查时间
    now = datetime.now()
    if now > coupon.end_time or now > user_coupon.expire_time:
        return False, "优惠券已过期"

    # 检查最低消费
    if order_amount < coupon.min_amount:
        return False, f"订单金额需满{coupon.min_amount}元"

    return True, "可以使用"


def calculate_discount_amount(coupon_code, order_amount):
    """计算优惠金额"""
    models = get_db_models()
    if not models:
        return 0

    Coupon = models["Coupon"]

    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if not coupon:
        return 0

    if coupon.type == "cash":
        # 现金券直接减免
        discount_amount = coupon.value
    elif coupon.type == "discount":
        # 折扣券按比例计算
        discount_amount = order_amount * (coupon.value / 100)
        # 检查最大折扣限制
        if coupon.max_discount and discount_amount > coupon.max_discount:
            discount_amount = coupon.max_discount
    elif coupon.type == "free":
        # 免费券
        discount_amount = order_amount
    else:
        discount_amount = 0

    return min(discount_amount, order_amount)  # 不能超过订单金额


def use_coupon(user_id, coupon_code, order_id):
    """使用优惠券"""
    models = get_db_models()
    db = get_db()
    if not models or not db:
        return False, "数据库模型或db实例未初始化"

    UserCoupon = models["UserCoupon"]

    can_use, message = can_use_coupon(
        user_id, coupon_code, 0
    )  # 这里不检查金额，在订单中使用时再检查
    if not can_use:
        return False, message

    user_coupon = UserCoupon.query.filter_by(
        user_id=user_id, coupon_code=coupon_code, status="unused"
    ).first()

    # 更新用户优惠券状态
    user_coupon.status = "used"
    user_coupon.order_id = order_id
    user_coupon.use_time = datetime.now()

    # 更新优惠券使用计数
    coupon = user_coupon.coupon
    coupon.used_count += 1

    db.session.commit()
    return True, "使用成功"


# ============================================================================
# 用户检查工具函数
# ============================================================================


def check_user_has_placed_order(user_id):
    """检查用户是否下过单（排除unpaid状态）"""
    models = get_db_models()
    if not models:
        return False

    PromotionUser = models["PromotionUser"]
    Order = models["Order"]

    try:
        # 通过openid查找小程序订单
        if user_id.startswith("USER"):
            # 这是基于OpenID生成的稳定用户ID，需要查找对应的openid
            user = PromotionUser.query.filter_by(user_id=user_id).first()
            if user and user.open_id:
                # 通过openid查找订单
                orders = Order.query.filter(
                    Order.openid == user.open_id,
                    Order.status != "unpaid",  # 排除未支付订单
                    Order.source_type == "miniprogram",
                ).count()
                logger.info(f"用户 {user_id} (openid: {user.open_id}) 下过 {orders} 个有效订单")
                return orders > 0

        # 如果没有openid信息，尝试通过订单中的其他字段匹配
        # 这里可能需要根据实际情况调整匹配逻辑
        return False

    except Exception as e:
        logger.info(f"检查用户订单失败: {e}")
        return False


def check_user_eligible_for_commission(user_id):
    """检查用户是否有分佣资格"""
    # 用户下过单就有分佣资格
    return check_user_has_placed_order(user_id)


# ============================================================================
# 文件处理工具函数
# ============================================================================


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gi", "bmp", "webp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# 文件名生成工具函数
# ============================================================================


def generate_production_info(order):
    """生成制作信息文本"""
    from datetime import datetime

    # 获取服务器配置
    try:
        from server_config import get_base_url
    except ImportError:

        def get_base_url():
            return "http://192.168.2.54:8000"

    # 获取OrderImage模型
    models = get_db_models()
    OrderImage = None
    if models:
        try:
            from app.models import OrderImage
        except ImportError:
            pass

    info_lines = []
    info_lines.append("=" * 50)
    info_lines.append("AI拍照制作信息")
    info_lines.append("=" * 50)
    info_lines.append(f"订单号: {order.order_number}")
    info_lines.append(f"客户姓名: {order.customer_name}")
    info_lines.append(f"联系电话: {order.customer_phone}")
    info_lines.append(f"订单时间: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    info_lines.append("")

    # 制作规格信息
    info_lines.append("制作规格:")
    info_lines.append("-" * 20)
    if order.size:
        info_lines.append(f"尺寸: {order.size}")
    if order.style_name:
        info_lines.append(f"艺术风格: {order.style_name}")
    if order.product_name:
        info_lines.append(f"产品类型: {order.product_name}")
    info_lines.append("")

    # 收货信息
    if order.customer_address:
        info_lines.append("收货地址:")
        info_lines.append("-" * 20)
        info_lines.append(order.customer_address)
        info_lines.append("")

    # 客户备注
    if order.customer_note:
        info_lines.append("客户备注:")
        info_lines.append("-" * 20)
        info_lines.append(order.customer_note)
        info_lines.append("")

    # 订单状态
    status_map = {
        "pending": "待制作",
        "processing": "制作中",
        "completed": "已完成",
        "shipped": "已发货",
        "hd_ready": "高清放大",
    }
    info_lines.append("订单状态:")
    info_lines.append("-" * 20)
    info_lines.append(f"当前状态: {status_map.get(order.status, order.status)}")
    if order.completed_at:
        info_lines.append(f"完成时间: {order.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    info_lines.append("")

    # 图片信息
    info_lines.append("图片信息:")
    info_lines.append("-" * 20)
    if order.original_image:
        info_lines.append(f"封面图片: {order.original_image}")

    # 统计图片数量
    image_count = 1 if order.original_image else 0
    if OrderImage:
        try:
            for oi in OrderImage.query.filter_by(order_id=order.id).all():
                if oi.path:
                    image_count += 1
        except Exception:
            pass

    info_lines.append(f"图片总数: {image_count} 张")
    info_lines.append("")

    # 制作说明
    info_lines.append("制作说明:")
    info_lines.append("-" * 20)
    info_lines.append("1. 请按照指定尺寸和风格进行制作")
    info_lines.append("2. 确保图片质量和色彩还原度")
    info_lines.append("3. 制作完成后请及时上传效果图")
    info_lines.append("4. 如有疑问请联系客户确认")
    info_lines.append("")

    # 联系方式
    info_lines.append("联系方式:")
    info_lines.append("-" * 20)
    info_lines.append(f"系统: {get_base_url()}")
    info_lines.append("客服: 请通过系统联系")
    info_lines.append("")
    info_lines.append("=" * 50)
    info_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    info_lines.append("=" * 50)

    return "\n".join(info_lines)


def generate_smart_filename(order):
    """生成智能文件名"""
    import re

    parts = []

    # 订单号
    parts.append(order.order_number)

    # 客户姓名（简化）
    if order.customer_name:
        # 只取姓氏，避免文件名过长
        customer_name = (
            order.customer_name[:2] if len(order.customer_name) > 2 else order.customer_name
        )
        parts.append(customer_name)

    # 尺寸
    if order.size:
        # 清理尺寸字符串，移除特殊字符
        size_clean = order.size.replace("x", "x").replace("*", "x").replace("×", "x")
        parts.append(f"尺寸{size_clean}")

    # 艺术风格
    if order.style_name:
        # 简化风格名称
        style_clean = order.style_name.replace("风格", "").replace("艺术", "")
        if len(style_clean) > 6:
            style_clean = style_clean[:6]
        parts.append(style_clean)

    # 组合文件名
    filename = "_".join(parts)

    # 清理文件名中的特殊字符
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    return filename


def generate_smart_image_name(order, original_filename, index):
    """生成智能图片文件名"""
    import os

    # 获取文件扩展名
    file_ext = os.path.splitext(original_filename)[1]

    # 生成基础名称
    base_name = order.order_number

    # 如果有多个图片，添加序号
    return f"{base_name}_图片{index + 1}{file_ext}"


# ============================================================================
# 二维码生成工具函数
# ============================================================================


def generate_qr_code(merchant_id):
    """生成商家二维码"""
    try:
        import base64
        import uuid
        from io import BytesIO

        import qrcode

        # 获取服务器配置
        try:
            from server_config import get_base_url
        except ImportError:

            def get_base_url():
                return "http://192.168.2.54:8000"

        qr_id = str(uuid.uuid4())[:8]
        url = f"{get_base_url()}/order?merchant={qr_id}"

        # 生成二维码图片
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # 转换为base64以便存储和显示
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return qr_id, img_base64
    except Exception as e:
        logger.info(f"生成二维码失败: {e}")
        return None, None
