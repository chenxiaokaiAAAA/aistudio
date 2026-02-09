# -*- coding: utf-8 -*-
"""
管理员团购核销API路由模块
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
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_groupon_api_bp = Blueprint("admin_groupon_api", __name__, url_prefix="/api/admin/groupon")


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


@admin_groupon_api_bp.route("/verify", methods=["POST"])
@login_required
def verify_groupon_order():
    """团购订单核销 - 生成随机码免拍券"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        Coupon = models["Coupon"]
        UserCoupon = models["UserCoupon"]
        db = models["db"]

        data = request.get_json()

        # 验证必填字段
        required_fields = ["groupon_order_id", "customer_phone"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400

        groupon_order_id = data["groupon_order_id"]
        customer_phone = data["customer_phone"]
        customer_name = data.get("customer_name", "")
        expire_days = int(data.get("expire_days", 30))  # 默认30天有效期

        # 获取核销金额（优先使用套餐配置，否则使用手动输入的金额）
        verify_amount = None
        platform = data.get("platform", "")
        package_id = data.get("package_id")

        if package_id:
            # 从套餐配置获取金额
            try:
                GrouponPackage = models.get("GrouponPackage")
                if GrouponPackage:
                    # 确保package_id是整数
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
                else:
                    # 如果GrouponPackage模型不存在，尝试使用手动输入的金额
                    if "verify_amount" in data:
                        verify_amount = float(data["verify_amount"])
                    else:
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": "套餐配置功能未启用，请手动输入核销金额",
                                }
                            ),
                            400,
                        )
            except (ValueError, TypeError) as e:
                return jsonify({"status": "error", "message": f"套餐ID格式错误: {str(e)}"}), 400
            except Exception as e:
                logger.info(f"获取套餐配置失败: {str(e)}")
                import traceback

                traceback.print_exc()
                # 如果获取套餐失败，尝试使用手动输入的金额
                if "verify_amount" in data:
                    verify_amount = float(data["verify_amount"])
                else:
                    return (
                        jsonify({"status": "error", "message": f"获取套餐配置失败: {str(e)}"}),
                        500,
                    )
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
        # 确保随机码唯一
        while Coupon.query.filter_by(code=random_code).first():
            random_code = generate_random_code(8)

        # 创建优惠券
        now = datetime.now()
        coupon = Coupon(
            name=f"团购核销券-{verify_amount}元",
            code=random_code,
            type="free",  # 免拍券类型
            value=verify_amount,
            min_amount=0.0,  # 无门槛
            total_count=1,  # 单个券
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

        # 保存平台和套餐信息
        if hasattr(coupon, "groupon_platform"):
            coupon.groupon_platform = platform
        if hasattr(coupon, "groupon_package_id") and package_id:
            try:
                coupon.groupon_package_id = int(package_id)
            except Exception:
                pass

        # 保存创建人信息（管理员创建）
        if hasattr(coupon, "creator_type"):
            coupon.creator_type = "admin"
        if hasattr(coupon, "creator_name"):
            coupon.creator_name = current_user.username if current_user else "管理员"

        db.session.add(coupon)
        db.session.flush()

        # 生成领取二维码（包含优惠券代码）
        # 二维码内容：小程序页面路径 + 优惠券代码
        qr_data = f"coupon_code:{random_code}"
        qr_code_url = generate_qr_code(qr_data)
        coupon.qr_code_url = qr_code_url

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
                },
            }
        )

    except Exception as e:
        logger.info(f"团购核销失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"团购核销失败: {str(e)}"}), 500


@admin_groupon_api_bp.route("/verify/list", methods=["GET"])
@login_required
def get_groupon_verify_list():
    """获取团购核销记录列表"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"status": "error", "message": "数据库模型未初始化"}), 500

        Coupon = models["Coupon"]

        # 优化：添加分页支持
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # 查询团购核销券（数据库层面分页）
        query = Coupon.query.filter_by(source_type="groupon")

        # 支持筛选参数
        platform = request.args.get("platform", "")
        if platform:
            query = query.filter_by(groupon_platform=platform)

        search = request.args.get("search", "").strip()
        if search:
            from sqlalchemy import or_

            query = query.filter(
                or_(
                    Coupon.groupon_order_id.like(f"%{search}%"),
                    Coupon.code.like(f"%{search}%"),
                    Coupon.name.like(f"%{search}%"),
                )
            )

        # 分页查询
        pagination = query.order_by(Coupon.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        coupons = pagination.items

        result = []
        for coupon in coupons:
            result.append(
                {
                    "id": coupon.id,
                    "groupon_order_id": coupon.groupon_order_id,
                    "coupon_code": coupon.code,
                    "coupon_name": coupon.name,
                    "verify_amount": float(coupon.verify_amount) if coupon.verify_amount else 0,
                    "status": coupon.status,
                    "used_count": coupon.used_count,
                    "create_time": (
                        coupon.create_time.strftime("%Y-%m-%d %H:%M:%S")
                        if coupon.create_time
                        else ""
                    ),
                    "expire_time": (
                        coupon.end_time.strftime("%Y-%m-%d %H:%M:%S") if coupon.end_time else ""
                    ),
                    "qr_code_url": coupon.qr_code_url,
                }
            )

        return jsonify(
            {
                "status": "success",
                "data": result,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }
        )

    except Exception as e:
        logger.info(f"获取团购核销记录失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取团购核销记录失败: {str(e)}"}), 500
