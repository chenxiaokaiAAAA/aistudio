# -*- coding: utf-8 -*-
"""
媒体文件路由模块
处理图片的访问和下载
"""

import logging

logger = logging.getLogger(__name__)
import os
import sys
import zipfile
from io import BytesIO
from urllib.parse import unquote

from flask import Blueprint, current_app, jsonify, send_file, send_from_directory
from flask_login import login_required

# 统一导入公共函数
from app.utils.admin_helpers import get_models
from app.utils.helpers import (
    generate_production_info,
    generate_smart_filename,
    generate_smart_image_name,
)

# 创建蓝图
media_bp = Blueprint("media", __name__)


# ============================================================================
# 下载路由（需要登录）
# ============================================================================


@media_bp.route("/download/original/<filename>")
@login_required
def download_original(filename):
    """下载原图"""
    try:
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(file_path):
            logger.info(f"原图文件不存在: {file_path}")
            return "文件不存在", 404
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True
        )
    except Exception as e:
        logger.info(f"下载原图失败: {e}")
        return f"下载失败: {str(e)}", 500


@media_bp.route("/download/final/<filename>")
@login_required
def download_final(filename):
    """下载有水印的效果图（预览用）"""
    try:
        file_path = os.path.join(current_app.config["FINAL_FOLDER"], filename)
        if not os.path.exists(file_path):
            logger.info(f"效果图文件不存在: {file_path}")
            return "文件不存在", 404
        return send_from_directory(current_app.config["FINAL_FOLDER"], filename, as_attachment=True)
    except Exception as e:
        logger.info(f"下载效果图失败: {e}")
        return f"下载失败: {str(e)}", 500


@media_bp.route("/download/final/clean/<filename>")
@login_required
def download_final_clean(filename):
    """下载无水印的高清效果图（确认制作后）"""
    try:
        models = get_models()
        if not models:
            return "系统未初始化", 500

        Order = models["Order"]

        # 查找对应的订单
        order = Order.query.filter_by(final_image=filename).first()
        if not order:
            return "订单不存在", 404

        # 检查订单状态，只有确认制作后才能下载无水印版本
        if order.status not in ["hd_ready", "completed", "shipped", "delivered", "manufacturing"]:
            return "订单尚未确认制作，无法下载无水印版本", 403

        # 查找原始无水印文件
        clean_filename = f"clean_{filename}"
        clean_file_path = os.path.join(current_app.config["FINAL_FOLDER"], clean_filename)

        # 检查无水印版本是否存在
        if not os.path.exists(clean_file_path):
            return "无水印版本文件不存在", 404

        return send_from_directory(
            current_app.config["FINAL_FOLDER"], clean_filename, as_attachment=True
        )
    except Exception as e:
        logger.info(f"下载无水印效果图失败: {e}")
        return f"下载失败: {str(e)}", 500


@media_bp.route("/download/hd/<filename>")
@login_required
def download_hd(filename):
    """下载高清图"""
    try:
        file_path = os.path.join(current_app.config["HD_FOLDER"], filename)
        if not os.path.exists(file_path):
            logger.info(f"高清图文件不存在: {file_path}")
            return "文件不存在", 404
        return send_from_directory(current_app.config["HD_FOLDER"], filename, as_attachment=True)
    except Exception as e:
        logger.info(f"下载高清图失败: {e}")
        return f"下载失败: {str(e)}", 500


@media_bp.route("/download/original/batch/<int:order_id>")
@login_required
def download_original_batch(order_id):
    """批量下载订单的所有原图（打包为ZIP，包含制作信息）"""
    try:
        models = get_models()
        if not models:
            return "系统未初始化", 500

        Order = models["Order"]
        OrderImage = models["OrderImage"]

        if not OrderImage:
            return "系统未初始化", 500

        # 获取订单
        order = Order.query.get_or_404(order_id)

        # 收集所有相关图片文件名（封面 + 多图）
        filenames = []
        if order.original_image:
            filenames.append(order.original_image)
        for oi in OrderImage.query.filter_by(order_id=order.id).all():
            if oi.path:
                filenames.append(oi.path)

        # 去重保序
        seen = set()
        unique_files = []
        for f in filenames:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        if not unique_files:
            return "订单没有图片", 404

        # 生成制作信息
        production_info = generate_production_info(order)

        # 生成智能文件名
        smart_filename = generate_smart_filename(order)

        # 打包ZIP到内存
        mem_file = BytesIO()
        with zipfile.ZipFile(mem_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 添加制作信息txt文件
            zf.writestr("制作信息.txt", production_info.encode("utf-8"))

            # 添加所有图片文件
            for fname in unique_files:
                file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
                if os.path.exists(file_path):
                    # 使用智能文件名
                    smart_image_name = generate_smart_image_name(
                        order, fname, unique_files.index(fname)
                    )
                    zf.write(file_path, arcname=smart_image_name)

        mem_file.seek(0)
        download_name = f"{smart_filename}.zip"
        return send_file(
            mem_file, mimetype="application/zip", as_attachment=True, download_name=download_name
        )
    except Exception as e:
        logger.info(f"批量下载原图失败: {e}")
        import traceback

        traceback.print_exc()
        return f"下载失败: {str(e)}", 500


# ============================================================================
# 媒体访问路由（页面内显示，非下载）
# ============================================================================


@media_bp.route("/media/hd/<filename>")
@login_required
def media_hd(filename):
    """访问效果图（需要登录）"""
    return send_from_directory(current_app.config["HD_FOLDER"], filename, as_attachment=False)


@media_bp.route("/public/hd/<filename>")
def public_media_hd(filename):
    """公开的高清图片访问，供厂家系统访问（无需登录）
    支持缩略图和原图访问（预览时使用缩略图）
    """
    try:
        # 先尝试从HD_FOLDER读取
        hd_folder = current_app.config.get("HD_FOLDER", "hd_images")
        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(current_app.root_path, hd_folder)

        hd_filepath = os.path.join(hd_folder, filename)

        if os.path.exists(hd_filepath):
            response = send_from_directory(hd_folder, filename, as_attachment=False)
            # 如果是缩略图，设置较短的缓存时间（1小时）
            if filename.endswith("_thumb.jpg"):
                response.cache_control.max_age = 3600  # 1小时
                response.cache_control.public = True
            else:
                # 原图设置较长的缓存时间（7天）
                response.cache_control.max_age = 604800  # 7天
                response.cache_control.public = True
            return response

        # 如果HD_FOLDER中不存在，尝试从FINAL_FOLDER读取
        final_folder = current_app.config.get("FINAL_FOLDER", "final_works")
        if not os.path.isabs(final_folder):
            final_folder = os.path.join(current_app.root_path, final_folder)

        final_filepath = os.path.join(final_folder, filename)

        if os.path.exists(final_filepath):
            response = send_from_directory(final_folder, filename, as_attachment=False)
            # 如果是缩略图，设置较短的缓存时间（1小时）
            if filename.endswith("_thumb.jpg"):
                response.cache_control.max_age = 3600  # 1小时
                response.cache_control.public = True
            else:
                # 原图设置较长的缓存时间（7天）
                response.cache_control.max_age = 604800  # 7天
                response.cache_control.public = True
            return response

        # 文件不存在
        logger.error("图片文件不存在: {filename}")
        logger.info(f"   尝试路径1: {hd_filepath}")
        logger.info(f"   尝试路径2: {final_filepath}")
        return jsonify({"error": "文件不存在", "filename": filename}), 404

    except Exception as e:
        logger.error("访问高清图片失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"访问文件失败: {str(e)}"}), 500


@media_bp.route("/public/hd/original/<filename>")
def public_media_hd_original(filename):
    """获取原图（用于打印或推送到小程序）
    如果请求的是缩略图文件名，自动转换为原图文件名
    """
    try:
        from app.utils.image_thumbnail import get_original_path

        # 如果请求的是缩略图，转换为原图文件名
        original_filename = filename
        if filename.endswith("_thumb.jpg"):
            # 提取原图文件名（去掉_thumb.jpg后缀，恢复原扩展名）
            base_name = filename.replace("_thumb.jpg", "")
            # 尝试常见的图片扩展名
            hd_folder = current_app.config.get("HD_FOLDER", "hd_images")
            final_folder = current_app.config.get("FINAL_FOLDER", "final_works")
            if not os.path.isabs(hd_folder):
                hd_folder = os.path.join(current_app.root_path, hd_folder)
            if not os.path.isabs(final_folder):
                final_folder = os.path.join(current_app.root_path, final_folder)

            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                test_filename = base_name + ext
                hd_filepath = os.path.join(hd_folder, test_filename)
                final_filepath = os.path.join(final_folder, test_filename)
                if os.path.exists(hd_filepath):
                    original_filename = test_filename
                    break
                elif os.path.exists(final_filepath):
                    original_filename = test_filename
                    break
        else:
            original_filename = filename

        # 优先从HD_FOLDER读取
        hd_folder = current_app.config.get("HD_FOLDER", "hd_images")
        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(current_app.root_path, hd_folder)

        hd_filepath = os.path.join(hd_folder, original_filename)

        if os.path.exists(hd_filepath):
            return send_from_directory(hd_folder, original_filename, as_attachment=False)

        # 如果HD_FOLDER中不存在，尝试从FINAL_FOLDER读取
        final_folder = current_app.config.get("FINAL_FOLDER", "final_works")
        if not os.path.isabs(final_folder):
            final_folder = os.path.join(current_app.root_path, final_folder)

        final_filepath = os.path.join(final_folder, original_filename)

        if os.path.exists(final_filepath):
            return send_from_directory(final_folder, original_filename, as_attachment=False)

        # 文件不存在
        logger.error("原图文件不存在: {original_filename}")
        return jsonify({"error": "文件不存在", "filename": original_filename}), 404

    except Exception as e:
        logger.info(f"访问原图失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"访问失败: {str(e)}"}), 500


@media_bp.route("/public/mockup/<filename>")
def public_mockup(filename):
    """样机套图生成结果访问（无需登录）"""
    try:
        output_dir = current_app.config.get("MOCKUP_OUTPUT_FOLDER")
        if not output_dir:
            output_dir = os.path.join(current_app.root_path, "data", "mockup_output")
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(current_app.root_path, output_dir)

        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "文件不存在", "filename": filename}), 404

        return send_from_directory(output_dir, filename, as_attachment=False)
    except Exception as e:
        logger.exception("访问样机图片失败: %s", e)
        return jsonify({"error": str(e)}), 500


@media_bp.route("/media/original/<path:filename>")
def media_original(filename):
    """访问原图（无需登录，供小程序等使用）。filename 支持 URL 编码（如 %20）。"""
    try:
        filename = unquote(filename, encoding="utf-8")
        upload_folder = current_app.config["UPLOAD_FOLDER"]

        # 确保路径是绝对路径，与上传接口的处理方式保持一致
        if not os.path.isabs(upload_folder):
            upload_folder = os.path.join(current_app.root_path, upload_folder)

        filepath = os.path.join(upload_folder, filename)

        # 打印调试信息
        logger.info("📥 访问文件请求:")
        logger.info(
            f"   - 配置的UPLOAD_FOLDER: {current_app.config.get('UPLOAD_FOLDER', 'uploads')}"
        )
        logger.info(f"   - 绝对路径: {upload_folder}")
        logger.info(f"   - 文件名: {filename}")
        logger.info(f"   - 完整路径: {filepath}")
        logger.info(f"   - 文件是否存在: {os.path.exists(filepath)}")

        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error("文件不存在: %s", filepath)
            # 列出目录内容以便调试
            if os.path.exists(upload_folder):
                files = os.listdir(upload_folder)
                logger.info(f"   - 目录中的文件: {files[:10]}")  # 只显示前10个
            else:
                logger.info(f"   - 目录不存在: {upload_folder}")
            return jsonify({"error": "文件不存在", "filename": filename, "path": filepath}), 404

        # 安全检查：确保文件在upload_folder目录内（防止路径遍历攻击）
        real_upload_folder = os.path.realpath(upload_folder)
        real_filepath = os.path.realpath(filepath)
        if not real_filepath.startswith(real_upload_folder):
            logger.error("路径遍历攻击尝试: %s", filepath)
            return jsonify({"error": "非法路径"}), 403

        file_size = os.path.getsize(filepath)
        logger.info(f"✅ 返回文件: {filepath}, 大小: {file_size} bytes")
        return send_from_directory(upload_folder, filename, as_attachment=False)
    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error("访问原图失败: %s", e)
        return jsonify({"error": f"访问文件失败: {str(e)}"}), 500


@media_bp.route("/media/category_nav/<path:filename>")
def media_category_nav(filename):
    """访问分类导航图标（统一存储路径：uploads/category_nav/）"""
    try:
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        if not os.path.isabs(upload_folder):
            upload_folder = os.path.join(current_app.root_path, upload_folder)
        category_nav_folder = os.path.join(upload_folder, "category_nav")
        filepath = os.path.join(category_nav_folder, filename)
        if os.path.exists(filepath):
            real_folder = os.path.realpath(category_nav_folder)
            real_filepath = os.path.realpath(filepath)
            if real_filepath.startswith(real_folder):
                return send_from_directory(category_nav_folder, filename, as_attachment=False)
        static_fallback = os.path.join(current_app.root_path, "static", "images", "category_nav", filename)
        if os.path.exists(static_fallback):
            return send_from_directory(
                os.path.join(current_app.root_path, "static", "images", "category_nav"), filename, as_attachment=False
            )
        return jsonify({"error": "文件不存在", "filename": filename}), 404
    except Exception as e:
        logger.exception("访问分类导航图标失败: %s", e)
        return jsonify({"error": str(e)}), 500


@media_bp.route("/media/final/<path:filename>")
def media_final(filename):
    """访问效果图（无需登录，供小程序等使用）。filename 支持 URL 编码（如 %20）。"""
    filename = unquote(filename, encoding="utf-8")
    logger.info(f"请求效果图: {filename}")
    final_path = os.path.join(current_app.config["FINAL_FOLDER"], filename)
    logger.info(f"效果图路径: {final_path}")
    logger.info(f"文件是否存在: {os.path.exists(final_path)}")
    if os.path.exists(final_path):
        logger.info(f"文件大小: {os.path.getsize(final_path)} bytes")
    return send_from_directory(current_app.config["FINAL_FOLDER"], filename, as_attachment=False)


@media_bp.route("/media/final/clean/<filename>")
def media_final_clean(filename):
    """访问无水印效果图（无需登录）"""
    try:
        # 查找原始无水印文件
        clean_filename = f"clean_{filename}"
        clean_file_path = os.path.join(current_app.config["FINAL_FOLDER"], clean_filename)

        # 检查无水印版本是否存在
        if not os.path.exists(clean_file_path):
            return jsonify({"error": "无水印版本文件不存在"}), 404

        return send_from_directory(
            current_app.config["FINAL_FOLDER"], clean_filename, as_attachment=False
        )
    except Exception as e:
        logger.info(f"访问无水印效果图失败: {e}")
        return jsonify({"error": "无水印图片不存在"}), 404


@media_bp.route("/media/hd/clean/<filename>")
def media_hd_clean(filename):
    """访问无水印高清图片（无需登录）"""
    try:
        # 查找原始无水印文件
        clean_filename = f"clean_{filename}"
        clean_file_path = os.path.join(current_app.config["HD_FOLDER"], clean_filename)

        # 检查无水印版本是否存在
        if not os.path.exists(clean_file_path):
            return jsonify({"error": "无水印版本文件不存在"}), 404

        return send_from_directory(
            current_app.config["HD_FOLDER"], clean_filename, as_attachment=False
        )
    except Exception as e:
        logger.info(f"访问无水印高清图片失败: {e}")
        return jsonify({"error": "无水印高清图片不存在"}), 404
