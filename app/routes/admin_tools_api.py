# -*- coding: utf-8 -*-
"""
管理后台工具API路由模块
从 test_server.py 迁移工具类API路由
"""

import logging

logger = logging.getLogger(__name__)
import json
import os
import re
import sys
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models

# 创建蓝图
admin_tools_api_bp = Blueprint("admin_tools_api", __name__)


@admin_tools_api_bp.route("/api/admin/upload-image", methods=["POST"])
@login_required
def admin_upload_image():
    """管理员上传图片"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        # 直接使用 current_app，确保与媒体路由使用相同的应用实例
        from flask import current_app

        app = current_app

        if "image" not in request.files:
            return jsonify({"success": False, "message": "没有上传文件"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "message": "文件名为空"}), 400

        from werkzeug.utils import secure_filename

        filename = secure_filename(file.filename)
        if not filename:
            # 如果secure_filename返回空字符串，使用原始文件名（去除特殊字符）
            filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
            # 移除所有非字母数字、点、下划线的字符
            filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)
            if not filename:
                filename = "uploaded_image"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 确保文件名有扩展名
        if "." not in filename:
            # 根据MIME类型添加扩展名
            if file.content_type:
                ext_map = {
                    "image/png": ".png",
                    "image/jpeg": ".jpg",
                    "image/jpg": ".jpg",
                    "image/gi": ".gi",
                    "image/webp": ".webp",
                }
                ext = ext_map.get(file.content_type, ".png")
                filename = filename + ext

        filename = f"{timestamp}_{filename}"

        # 检查文件大小（限制为20MB）
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        max_size = 20 * 1024 * 1024  # 20MB
        if file_size > max_size:
            return (
                jsonify(
                    {
                        "success": False,
                        "status": "error",
                        "message": f"文件大小超过限制（最大20MB），当前文件大小: {file_size / 1024 / 1024:.2f}MB",
                    }
                ),
                400,
            )

        upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")

        # 确保路径是绝对路径，与媒体路由的处理方式保持一致
        if not os.path.isabs(upload_folder):
            upload_folder = os.path.join(app.root_path, upload_folder)

        # 分类导航图标使用统一子目录 uploads/category_nav/
        subfolder = request.form.get("subfolder", "").strip()
        if subfolder == "category_nav":
            upload_folder = os.path.join(upload_folder, "category_nav")

        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)

        # 打印调试信息
        logger.info("📤 上传文件信息:")
        logger.info(f"   - 配置的UPLOAD_FOLDER: {app.config.get('UPLOAD_FOLDER', 'uploads')}")
        logger.info(f"   - 绝对路径: {upload_folder}")
        logger.info(f"   - 文件名: {filename}")
        logger.info(f"   - 完整路径: {filepath}")

        try:
            file.save(filepath)
            # 验证文件是否真的保存成功
            if os.path.exists(filepath):
                actual_size = os.path.getsize(filepath)
                logger.info(f"✅ 图片上传成功: {filepath}, 大小: {actual_size} bytes")
            else:
                logger.error("文件保存后不存在: {filepath}")
                return (
                    jsonify({"success": False, "status": "error", "message": "文件保存失败"}),
                    500,
                )
        except Exception as save_error:
            logger.error("保存文件失败: {save_error}")
            return (
                jsonify(
                    {
                        "success": False,
                        "status": "error",
                        "message": f"保存文件失败: {str(save_error)}",
                    }
                ),
                500,
            )

        # 获取基础URL（使用相对路径，避免端口不匹配问题）
        if subfolder == "category_nav":
            image_url = f"/media/category_nav/{filename}"
        else:
            image_url = f"/media/original/{filename}"

        # 可选：如果需要绝对URL，可以从请求中获取
        # from flask import request
        # base_url = request.host_url.rstrip('/')  # 获取当前请求的基础URL
        # image_url = f'{base_url}/media/original/{filename}'

        return jsonify(
            {
                "status": "success",
                "success": True,  # 保持向后兼容
                "message": "图片上传成功",
                "filename": filename,
                "url": image_url,  # 保持向后兼容
                "image_url": image_url,  # 前端期望的字段名
            }
        )

    except Exception as e:
        logger.info(f"上传图片失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500


@admin_tools_api_bp.route("/api/admin/init-data", methods=["POST"])
@login_required
def admin_init_data():
    """初始化数据（管理后台）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]

        # 调用初始化函数
        from test_server import init_default_data

        init_default_data()

        return jsonify({"success": True, "message": "数据初始化成功"})

    except Exception as e:
        logger.info(f"初始化数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"初始化失败: {str(e)}"}), 500


@admin_tools_api_bp.route("/api/admin/clean-duplicates", methods=["POST"])
@login_required
def admin_clean_duplicates():
    """清理重复数据（管理后台）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        Order = models["Order"]

        # 查找重复订单（基于订单号）
        duplicates = (
            db.session.query(Order.order_number, db.func.count(Order.id).label("count"))
            .group_by(Order.order_number)
            .having(db.func.count(Order.id) > 1)
            .all()
        )

        # 优化N+1查询：批量查询所有重复订单号的订单
        order_numbers_list = [row[0] for row in duplicates]
        orders_by_number = {}
        if order_numbers_list:
            all_duplicate_orders = (
                Order.query.filter(Order.order_number.in_(order_numbers_list))
                .order_by(Order.created_at)
                .all()
            )
            for order in all_duplicate_orders:
                if order.order_number not in orders_by_number:
                    orders_by_number[order.order_number] = []
                orders_by_number[order.order_number].append(order)

        cleaned_count = 0
        for order_number, count in duplicates:
            # 从批量查询的映射中获取订单（避免N+1查询）
            orders = orders_by_number.get(order_number, [])
            for order in orders[1:]:  # 跳过第一个
                db.session.delete(order)
                cleaned_count += 1

        db.session.commit()

        return jsonify({"success": True, "message": f"清理完成，删除了 {cleaned_count} 条重复订单"})

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"清理重复数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"清理失败: {str(e)}"}), 500


@admin_tools_api_bp.route("/api/admin/update-cover-images", methods=["POST"])
@login_required
def admin_update_cover_images():
    """更新封面图片（管理后台）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        StyleCategory = models["StyleCategory"]
        StyleImage = models["StyleImage"]

        # 优化N+1查询：批量查询所有分类和图片
        categories = StyleCategory.query.all()

        # 批量查询所有风格图片（按分类分组）
        category_ids = [cat.id for cat in categories]
        images_by_category = {}
        if category_ids:
            all_images = (
                StyleImage.query.filter(
                    StyleImage.category_id.in_(category_ids), StyleImage.is_active is True
                )
                .order_by(StyleImage.sort_order)
                .all()
            )
            for img in all_images:
                if img.category_id not in images_by_category:
                    images_by_category[img.category_id] = []
                images_by_category[img.category_id].append(img)

        updated_count = 0
        for category in categories:
            # 从批量查询的映射中获取第一张图片（避免N+1查询）
            images = images_by_category.get(category.id, [])
            first_image = images[0] if images else None

            if first_image and first_image.image_url:
                category.cover_image = first_image.image_url
                updated_count += 1

        db.session.commit()

        return jsonify(
            {"success": True, "message": f"更新完成，更新了 {updated_count} 个分类的封面图片"}
        )

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"更新封面图片失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"}), 500


@admin_tools_api_bp.route("/admin/clear-test-data", methods=["POST"])
@login_required
def clear_test_data():
    """清理测试数据（管理后台）"""
    try:
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        db = models["db"]
        Order = models["Order"]

        # 删除测试订单（订单号包含TEST或test的，但不包括source_type='admin_test'的正式测试订单）
        # source_type='admin_test'的订单是正式创建的测试订单，应该保留在订单管理中
        test_orders = Order.query.filter(
            (Order.order_number.like("%TEST%") | Order.order_number.like("%test%")),
            Order.source_type != "admin_test",  # 不清理正式测试订单
        ).all()

        deleted_count = len(test_orders)
        for order in test_orders:
            db.session.delete(order)

        db.session.commit()

        return jsonify({"success": True, "message": f"清理完成，删除了 {deleted_count} 条测试订单"})

    except Exception as e:
        if "db" in locals():
            db.session.rollback()
        logger.info(f"清理测试数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"清理失败: {str(e)}"}), 500
