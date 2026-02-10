# -*- coding: utf-8 -*-
"""
小程序团购核销相关路由
"""

import logging

logger = logging.getLogger(__name__)
import base64
import random
import string
import sys
from datetime import datetime, timedelta
from io import BytesIO

import qrcode
from flask import Blueprint, jsonify, request

from app.routes.miniprogram.common import get_helper_functions, get_models

bp = Blueprint("groupon", __name__)


def generate_random_code(length=8):
    """生成随机码"""
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def generate_qr_code(data):
    """生成二维码图片（base64编码）"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def check_staff_permission(openid, user_id, phone=None):
    """检查用户是否有团购核销权限（从StaffUser表中检查）"""
    try:
        models = get_models()
        if not models:
            return False

        StaffUser = models.get("StaffUser")
        if not StaffUser:
            return False

        import json

        # 优先通过手机号匹配
        if phone:
            staff_user = StaffUser.query.filter_by(phone=phone, status="active").first()
            if staff_user:
                try:
                    permissions = (
                        json.loads(staff_user.permissions) if staff_user.permissions else {}
                    )
                    # 检查是否有团购核销或退款申请权限
                    if permissions.get("groupon_verify") or permissions.get("refund_request"):
                        return True
                except Exception:
                    pass

        # 通过openid匹配
        if openid:
            staff_user = StaffUser.query.filter_by(openid=openid, status="active").first()
            if staff_user:
                try:
                    permissions = (
                        json.loads(staff_user.permissions) if staff_user.permissions else {}
                    )
                    # 检查是否有团购核销或退款申请权限
                    if permissions.get("groupon_verify") or permissions.get("refund_request"):
                        return True
                except Exception:
                    pass

        # 通过user_id匹配（如果user_id是手机号）
        if user_id and len(user_id) == 11 and user_id.isdigit():
            staff_user = StaffUser.query.filter_by(phone=user_id, status="active").first()
            if staff_user:
                try:
                    permissions = (
                        json.loads(staff_user.permissions) if staff_user.permissions else {}
                    )
                    # 检查是否有团购核销或退款申请权限
                    if permissions.get("groupon_verify") or permissions.get("refund_request"):
                        return True
                except Exception:
                    pass

        # 兼容旧方式：从系统配置中读取店员openid列表（保留向后兼容）
        try:
            AIConfig = models.get("AIConfig")
            if AIConfig:
                staff_config = AIConfig.query.filter_by(config_key="staff_openids").first()
                if staff_config and staff_config.config_value:
                    staff_openids = json.loads(staff_config.config_value)
                    if isinstance(staff_openids, list):
                        if openid in staff_openids or user_id in staff_openids:
                            return True
        except Exception:
            pass

        return False
    except Exception as e:
        logger.info(f"检查店员权限失败: {e}")
        import traceback

        traceback.print_exc()
        return False


@bp.route("/groupon/verify", methods=["POST"])
def miniprogram_verify_groupon():
    """小程序团购订单核销"""
    try:
        data = request.get_json()
        openid = data.get("openid")
        user_id = data.get("user_id")
        phone = data.get("phone", "")  # 获取手机号参数

        logger.info(f"小程序团购核销 - openid: {openid}, user_id: {user_id}, phone: {phone}")

        # 检查权限（传入手机号）
        if not check_staff_permission(openid, user_id, phone):
            logger.info(f"权限检查失败 - openid: {openid}, user_id: {user_id}, phone: {phone}")
            return jsonify({"status": "error", "message": "权限不足，只有店员可以操作"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        Coupon = models["Coupon"]
        UserCoupon = models["UserCoupon"]
        db = models["db"]

        # 验证必填字段
        required_fields = ["groupon_order_id", "customer_phone"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400

        groupon_order_id = data["groupon_order_id"]
        customer_phone = data["customer_phone"]
        customer_name = data.get("customer_name", "")
        expire_days = int(data.get("expire_days", 30))

        # 获取核销金额（优先使用套餐配置，否则使用手动输入的金额）
        verify_amount = None
        platform = data.get("platform", "")
        package_id = data.get("package_id")

        package = None
        if package_id:
            # 从套餐配置获取金额
            GrouponPackage = models.get("GrouponPackage")
            if GrouponPackage:
                # 确保package_id是整数
                try:
                    package_id_int = int(package_id) if package_id else None
                    if package_id_int:
                        package = GrouponPackage.query.get(package_id_int)
                        if package:
                            verify_amount = float(package.package_amount)
                            platform = package.platform
                        else:
                            return jsonify({"status": "error", "message": "套餐不存在"}), 400
                    else:
                        return jsonify({"status": "error", "message": "套餐ID无效"}), 400
                except (ValueError, TypeError) as e:
                    logger.info(f"套餐ID转换失败: {e}, package_id={package_id}")
                    return jsonify({"status": "error", "message": f"套餐ID格式错误: {str(e)}"}), 400
            else:
                return jsonify({"status": "error", "message": "套餐配置模型未初始化"}), 500
        elif "verify_amount" in data:
            # 兼容旧方式：手动输入金额
            verify_amount = float(data["verify_amount"])
        else:
            return jsonify({"status": "error", "message": "请选择套餐或输入核销金额"}), 400

        if verify_amount <= 0:
            return jsonify({"status": "error", "message": "核销金额必须大于0"}), 400

        # 检查是否已存在该团购订单的优惠券
        existing_coupon = Coupon.query.filter_by(
            groupon_order_id=groupon_order_id, source_type="groupon"
        ).first()

        if existing_coupon:
            return jsonify({"status": "error", "message": "该团购订单已核销，优惠券已生成"}), 400

        # 生成随机码
        random_code = generate_random_code(8)
        while Coupon.query.filter_by(code=random_code).first():
            random_code = generate_random_code(8)

        # 获取店员信息（小程序核销时）
        StaffUser = models.get("StaffUser")
        staff_user = None
        staff_user_id = None
        franchisee_id = None
        creator_name = ""
        creator_type = "staf"

        if StaffUser and phone:
            staff_user = StaffUser.query.filter_by(phone=phone, status="active").first()
            if staff_user:
                staff_user_id = staff_user.id
                franchisee_id = staff_user.franchisee_id
                creator_name = f"{staff_user.name}（店员）"

        # 创建优惠券
        now = datetime.now()
        coupon = Coupon(
            name=f"团购核销券-{verify_amount}元",
            code=random_code,
            type="free",
            value=verify_amount,
            min_amount=0.0,
            total_count=1,
            used_count=0,
            per_user_limit=1,
            start_time=now,
            end_time=now + timedelta(days=expire_days),
            status="active",
            description=f"团购订单{groupon_order_id}核销券，金额{verify_amount}元",
            source_type="groupon",
            groupon_order_id=groupon_order_id,
            verify_amount=verify_amount,
            is_random_code=True,
        )

        # 保存创建人信息
        if hasattr(coupon, "franchisee_id"):
            coupon.franchisee_id = franchisee_id
        if hasattr(coupon, "staff_user_id"):
            coupon.staff_user_id = staff_user_id
        if hasattr(coupon, "creator_type"):
            coupon.creator_type = creator_type
        if hasattr(coupon, "creator_name"):
            coupon.creator_name = creator_name

        # 保存平台和套餐信息
        if hasattr(coupon, "groupon_platform"):
            coupon.groupon_platform = platform
        if hasattr(coupon, "groupon_package_id") and package:
            try:
                coupon.groupon_package_id = int(package.id)
            except (ValueError, TypeError) as e:
                logger.info(f"保存套餐ID失败: {e}, package.id={package.id}")
                # 如果转换失败，至少保存平台信息
                pass

        # 如果Coupon模型有customer_phone字段，保存客户手机号
        if hasattr(coupon, "customer_phone"):
            coupon.customer_phone = customer_phone
        if hasattr(coupon, "customer_name"):
            coupon.customer_name = customer_name

        db.session.add(coupon)
        db.session.flush()

        # 生成领取二维码
        qr_data = f"coupon_code:{random_code}"
        qr_code_url = generate_qr_code(qr_data)
        coupon.qr_code_url = qr_code_url

        # 如果用户已注册且手机号匹配，自动保存优惠券到账户
        User = models.get("User")
        auto_saved = False
        if User and customer_phone:
            user = User.query.filter_by(phone=customer_phone).first()
            if user:
                # 检查是否已领取
                existing_user_coupon = UserCoupon.query.filter_by(
                    user_id=user.user_id, coupon_id=coupon.id
                ).first()
                if not existing_user_coupon:
                    user_coupon = UserCoupon(
                        user_id=user.user_id,
                        coupon_id=coupon.id,
                        coupon_code=random_code,
                        expire_time=coupon.end_time,
                        status="active",
                    )
                    db.session.add(user_coupon)
                    auto_saved = True

        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": "团购核销成功，优惠券已生成",
                "data": {
                    "coupon_id": coupon.id,
                    "coupon_code": random_code,
                    "coupon_name": coupon.name,
                    "verify_amount": verify_amount,
                    "qr_code_url": qr_code_url,
                    "expire_time": coupon.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "auto_saved": auto_saved,
                },
            }
        )

    except Exception as e:
        logger.info(f"小程序团购核销失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"团购核销失败: {str(e)}"}), 500


@bp.route("/groupon/check-staff", methods=["GET"])
def check_staff():
    """检查用户是否有团购核销权限"""
    try:
        openid = request.args.get("openid", "")
        user_id = request.args.get("user_id", "")
        phone = request.args.get("phone", "")  # 获取手机号参数

        is_staff = check_staff_permission(openid, user_id, phone)

        return jsonify({"status": "success", "data": {"is_staff": is_staff}})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"检查权限失败: {str(e)}"}), 500


@bp.route("/groupon/packages", methods=["GET"])
def get_groupon_packages():
    """获取团购套餐列表（小程序用）"""
    try:
        platform = request.args.get("platform", "").strip()

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        # 尝试获取GrouponPackage模型
        GrouponPackage = models.get("GrouponPackage")
        if not GrouponPackage:
            # 如果模型字典中没有，尝试直接从test_server获取
            try:
                import sys

                test_server = sys.modules.get("test_server")
                if test_server and hasattr(test_server, "GrouponPackage"):
                    GrouponPackage = test_server.GrouponPackage
                else:
                    return jsonify({"status": "error", "message": "团购套餐模型未初始化"}), 500
            except Exception:
                return jsonify({"status": "error", "message": "团购套餐模型未初始化"}), 500

        # 平台值映射（小程序使用英文，数据库可能使用中文）
        platform_map = {
            "meituan": "美团",
            "douyin": "抖音",
            "dianping": "大众点评",
            "other": "其他",
        }

        # 查询套餐（如果指定了平台，则过滤）
        query = GrouponPackage.query.filter_by(status="active")
        if platform:
            # 先尝试直接匹配，如果失败则尝试映射
            mapped_platform = platform_map.get(platform, platform)
            # 尝试两种格式
            from sqlalchemy import or_

            query = query.filter(
                or_(GrouponPackage.platform == platform, GrouponPackage.platform == mapped_platform)
            )
            logger.info(f"查询套餐 - 平台: {platform}, 映射后: {mapped_platform}")

        packages = query.order_by(GrouponPackage.sort_order.asc(), GrouponPackage.id.asc()).all()

        logger.info(f"查询到 {len(packages)} 个套餐")

        result = []
        for pkg in packages:
            result.append(
                {
                    "id": pkg.id,
                    "platform": pkg.platform,
                    "package_name": pkg.package_name,
                    "package_amount": float(pkg.package_amount),
                    "description": pkg.description or "",
                }
            )

        logger.info(f"返回套餐数据: {result}")

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取套餐列表失败: {str(e)}"}), 500
