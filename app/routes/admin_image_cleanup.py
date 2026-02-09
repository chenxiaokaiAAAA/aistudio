# -*- coding: utf-8 -*-
"""
过期图片清理管理路由
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models

admin_image_cleanup_bp = Blueprint("admin_image_cleanup", __name__)


@admin_image_cleanup_bp.route("/admin/image-cleanup")
@login_required
def admin_image_cleanup():
    """过期图片清理配置页面"""
    if current_user.role not in ["admin", "operator"]:
        return redirect(url_for("auth.login"))

    return render_template("admin/image_cleanup.html")


@admin_image_cleanup_bp.route("/api/admin/image-cleanup/config", methods=["GET"])
@login_required
def get_cleanup_config():
    """获取清理配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models(["AIConfig", "db"])
        default_config = {
            "final_image_days": 3,
            "retouched_image_days": 30,
            "custom_cleanup_rules": [],
        }
        if models and models.get("AIConfig"):
            config_row = models["AIConfig"].query.filter_by(
                config_key="image_cleanup"
            ).first()
            if config_row and config_row.config_value:
                try:
                    import json

                    loaded = json.loads(config_row.config_value)
                    default_config.update(loaded)
                except (json.JSONDecodeError, TypeError):
                    pass

        return jsonify({"success": True, "config": default_config})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取配置失败: {str(e)}"}), 500


@admin_image_cleanup_bp.route("/api/admin/image-cleanup/config", methods=["POST"])
@login_required
def save_cleanup_config():
    """保存清理配置"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models(["AIConfig", "db"])
        if not models or not models.get("AIConfig") or not models.get("db"):
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        data = request.get_json()
        config = data.get("config", {})
        config_json = json.dumps(
            {
                "final_image_days": config.get("final_image_days", 3),
                "retouched_image_days": config.get("retouched_image_days", 30),
                "custom_cleanup_rules": config.get("custom_cleanup_rules", []),
            },
            ensure_ascii=False,
        )

        AIConfig = models["AIConfig"]
        db = models["db"]
        row = AIConfig.query.filter_by(config_key="image_cleanup").first()
        if row:
            row.config_value = config_json
        else:
            row = AIConfig(
                config_key="image_cleanup",
                config_value=config_json,
                description="图片清理规则配置",
            )
            db.session.add(row)
        db.session.commit()

        return jsonify({"success": True, "message": "配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "message": f"保存配置失败: {str(e)}"}), 500


@admin_image_cleanup_bp.route("/api/admin/image-cleanup/execute", methods=["POST"])
@login_required
def execute_cleanup():
    """执行清理任务"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"success": False, "message": "权限不足"}), 403

        models = get_models()
        if not models:
            return jsonify({"success": False, "message": "数据库未初始化"}), 500

        Order = models.get("Order")
        OrderImage = models.get("OrderImage")
        db = models.get("db")

        if not Order or not db:
            return jsonify({"success": False, "message": "数据库模型未找到"}), 500

        data = request.get_json()
        days = data.get("days", 0)

        if days <= 0:
            return jsonify({"success": False, "message": "天数必须大于0"}), 400

        # 计算指定天数前的日期
        cutoff_date = datetime.now() - timedelta(days=days)
        logger.info(
            f"[清理] 开始清理 {days} 天前的订单（截止日期: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}）"
        )

        # 查询符合条件的订单
        # 条件1：completed_at 存在且小于截止日期
        # 条件2：completed_at 为空，但 created_at 小于截止日期，且状态为已完成相关状态
        # 条件3：completed_at 为空，但 created_at 小于截止日期（放宽条件，只要订单存在就清理）
        from sqlalchemy import or_

        orders = Order.query.filter(
            or_(
                (Order.completed_at.isnot(None)) & (Order.completed_at < cutoff_date),
                (
                    (Order.completed_at.is_(None))
                    & (Order.created_at < cutoff_date)
                    & (
                        Order.status.in_(
                            [
                                "shipped",
                                "completed",
                                "hd_ready",
                                "selection_completed",
                                "printing",
                                "pending_shipment",
                            ]
                        )
                    )
                ),
                # 放宽条件：如果 created_at 小于截止日期，即使状态不是已完成，也尝试清理（可能是旧数据）
                (
                    (Order.created_at < cutoff_date)
                    & (
                        Order.status.notin_(
                            [
                                "unpaid",
                                "paid",
                                "shooting",
                                "retouching",
                                "ai_processing",
                                "pending_selection",
                            ]
                        )
                    )
                ),
            )
        ).all()

        logger.info(f"[清理] 找到 {len(orders)} 个符合条件的订单")
        for order in orders:
            logger.info(
                f"  - 订单: {order.order_number}, 状态: {order.status}, 创建时间: {order.created_at}, 完成时间: {order.completed_at}"
            )

        if not orders:
            return jsonify(
                {
                    "success": True,
                    "message": f"没有找到{days}天前已完成的订单",
                    "deleted_count": 0,
                    "orders_count": 0,
                }
            )

        # 获取文件夹路径（使用绝对路径）
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        final_folder = current_app.config.get("FINAL_FOLDER", "final_works")
        hd_folder = current_app.config.get("HD_FOLDER", "hd_images")

        # 获取项目根目录
        # Flask 的 root_path 取决于 Flask(__name__) 中 __name__ 的值
        # 如果 Flask(__name__) 在 test_server.py 中，__name__ 是 '__main__'，root_path 指向 test_server.py 所在目录
        # 如果 Flask(__name__) 在 app/__init__.py 中，__name__ 是 'app'，root_path 指向 app 目录
        # 为了兼容两种情况，先检查 root_path 是否包含 'app' 目录
        root_path_obj = Path(current_app.root_path).resolve()
        logger.info(f"[清理] Flask root_path: {root_path_obj}")

        # 如果 root_path 是 app 目录，则向上一级到项目根目录
        if root_path_obj.name == "app" and (root_path_obj / "routes").exists():
            project_root = root_path_obj.parent
        else:
            # 如果 root_path 已经是项目根目录（包含 uploads, final_works, hd_images 等目录）
            project_root = root_path_obj

        logger.info(f"[清理] 项目根目录: {project_root}")

        # 如果是相对路径，基于项目根目录构建绝对路径
        if not os.path.isabs(upload_folder):
            upload_path = (project_root / upload_folder).resolve()
        else:
            upload_path = Path(upload_folder).resolve()

        if not os.path.isabs(final_folder):
            final_path = (project_root / final_folder).resolve()
        else:
            final_path = Path(final_folder).resolve()

        if not os.path.isabs(hd_folder):
            hd_path = (project_root / hd_folder).resolve()
        else:
            hd_path = Path(hd_folder).resolve()

        logger.info("[清理] 文件夹路径:")
        logger.info(f"  - uploads: {upload_path}")
        logger.info(f"  - final_works: {final_path}")
        logger.info(f"  - hd_images: {hd_path}")

        # 优化N+1查询：批量查询所有订单的图片（在循环外执行一次）
        order_images_map = {}
        if OrderImage:
            order_ids_for_images = [o.id for o in orders]
            if order_ids_for_images:
                all_order_images = OrderImage.query.filter(
                    OrderImage.order_id.in_(order_ids_for_images)
                ).all()
                for img in all_order_images:
                    if img.order_id not in order_images_map:
                        order_images_map[img.order_id] = []
                    order_images_map[img.order_id].append(img)

        # 统计信息
        deleted_count = 0
        not_found_count = 0
        error_count = 0
        total_size = 0
        processed_orders = 0

        # 遍历订单，删除相关图片
        for order in orders:
            order_processed = False
            logger.info(f"\n[清理] 处理订单: {order.order_number}")

            # 1. 删除 uploads 目录中的原图
            if order.original_image:
                # 检查是否是URL（跳过URL格式的路径）
                if order.original_image.startswith(("http://", "https://")):
                    logger.info(f"  [原图] ⚠️ 跳过URL路径: {order.original_image}")
                else:
                    # 提取文件名（如果路径包含目录分隔符，只取文件名部分）
                    filename = os.path.basename(order.original_image)
                    image_path = upload_path / filename
                    logger.info(f"  [原图] 检查: {image_path} (原始路径: {order.original_image})")

                    # 尝试多种方式查找文件
                    found_files = []
                    if image_path.exists() and image_path.is_file():
                        found_files.append(image_path)
                    else:
                        # 模式1: 精确文件名匹配（去掉扩展名后匹配）
                        base_name = os.path.splitext(filename)[0]
                        found_files.extend(
                            [f for f in upload_path.glob(f"{base_name}*") if f.is_file()]
                        )
                        # 模式2: 如果文件名包含订单号，查找包含订单号的文件
                        if order.order_number in filename:
                            found_files.extend(
                                [
                                    f
                                    for f in upload_path.glob(f"*{order.order_number}*")
                                    if f.is_file()
                                ]
                            )
                        # 模式3: 查找文件名中包含原始文件名关键部分的所有文件
                        if len(base_name) > 8:
                            key_part = base_name[-8:]  # 取文件名后8位作为关键部分
                            found_files.extend(
                                [f for f in upload_path.glob(f"*{key_part}*") if f.is_file()]
                            )

                    # 去重
                    found_files = list(set(found_files))

                    if found_files:
                        logger.info(f"  [原图] 找到 {len(found_files)} 个相关文件，将全部删除")
                        for file_to_delete in found_files:
                            try:
                                file_size = file_to_delete.stat().st_size
                                total_size += file_size
                                file_to_delete.unlink()
                                deleted_count += 1
                                order_processed = True
                                logger.info(
                                    f"  [原图] ✅ 已删除: {file_to_delete.name} ({file_size / 1024:.2f} KB)"
                                )
                            except Exception as e:
                                error_count += 1
                                logger.info(f"  [原图] ❌ 删除失败 {file_to_delete.name}: {str(e)}")
                    else:
                        not_found_count += 1
                        logger.info(f"  [原图] ⚠️ 文件不存在: {image_path} (或未找到相关文件)")

            # 从批量查询的映射中获取图片（避免N+1查询）
            if OrderImage:
                order_images = order_images_map.get(order.id, [])
                logger.info(f"  [订单图片] 找到 {len(order_images)} 张图片")
                for order_image in order_images:
                    if order_image.path:
                        # 检查是否是URL（跳过URL格式的路径）
                        if order_image.path.startswith(("http://", "https://")):
                            logger.info(f"    [订单图片] ⚠️ 跳过URL路径: {order_image.path}")
                        else:
                            # 提取文件名（如果路径包含目录分隔符，只取文件名部分）
                            filename = os.path.basename(order_image.path)
                            image_path = upload_path / filename
                            logger.info(
                                f"    [订单图片] 检查: {image_path} (原始路径: {order_image.path})"
                            )

                            # 尝试多种方式查找文件
                            found_files = []
                            if image_path.exists() and image_path.is_file():
                                found_files.append(image_path)
                            else:
                                # 模式1: 精确文件名匹配（去掉扩展名后匹配）
                                base_name = os.path.splitext(filename)[0]
                                found_files.extend(
                                    [f for f in upload_path.glob(f"{base_name}*") if f.is_file()]
                                )
                                # 模式2: 如果文件名包含订单号，查找包含订单号的文件
                                if order.order_number in filename:
                                    found_files.extend(
                                        [
                                            f
                                            for f in upload_path.glob(f"*{order.order_number}*")
                                            if f.is_file()
                                        ]
                                    )
                                # 模式3: 查找文件名中包含原始文件名关键部分的所有文件
                                if len(base_name) > 8:
                                    key_part = base_name[-8:]  # 取文件名后8位作为关键部分
                                    found_files.extend(
                                        [
                                            f
                                            for f in upload_path.glob(f"*{key_part}*")
                                            if f.is_file()
                                        ]
                                    )

                            # 去重
                            found_files = list(set(found_files))

                            if found_files:
                                logger.info(
                                    f"    [订单图片] 找到 {len(found_files)} 个相关文件，将全部删除"
                                )
                                for file_to_delete in found_files:
                                    try:
                                        file_size = file_to_delete.stat().st_size
                                        total_size += file_size
                                        file_to_delete.unlink()
                                        deleted_count += 1
                                        order_processed = True
                                        logger.info(
                                            f"    [订单图片] ✅ 已删除: {file_to_delete.name} ({file_size / 1024:.2f} KB)"
                                        )
                                    except Exception as e:
                                        error_count += 1
                                        logger.info(
                                            f"    [订单图片] ❌ 删除失败 {file_to_delete.name}: {str(e)}"
                                        )
                            else:
                                not_found_count += 1
                                logger.info(
                                    f"    [订单图片] ⚠️ 文件不存在: {image_path} (或未找到相关文件)"
                                )

            # 2. 删除 final_works 目录中的效果图
            if order.final_image:
                # 检查是否是URL（跳过URL格式的路径）
                if order.final_image.startswith(("http://", "https://")):
                    logger.info(f"  [效果图] ⚠️ 跳过URL路径: {order.final_image}")
                else:
                    # 提取文件名（如果路径包含目录分隔符，只取文件名部分）
                    filename = os.path.basename(order.final_image)
                    image_path = final_path / filename
                    logger.info(f"  [效果图] 检查: {image_path} (原始路径: {order.final_image})")
                    # 如果直接路径不存在，尝试查找包含订单号的文件
                    if not image_path.exists():
                        # 尝试查找以订单号开头的文件（支持多种模式）
                        order_files = []
                        # 模式1: 订单号开头
                        order_files.extend(list(final_path.glob(f"{order.order_number}*")))
                        # 模式2: 包含订单号
                        if not order_files:
                            order_files.extend(
                                [
                                    f
                                    for f in final_path.glob("*")
                                    if f.is_file() and order.order_number in f.name
                                ]
                            )
                        # 模式3: 如果文件名包含订单号的一部分
                        if not order_files and len(order.order_number) > 8:
                            short_order = order.order_number[:8]
                            order_files.extend(
                                [
                                    f
                                    for f in final_path.glob("*")
                                    if f.is_file() and short_order in f.name
                                ]
                            )

                        if order_files:
                            logger.info(
                                f"  [效果图] 找到 {len(order_files)} 个相关文件，将全部删除"
                            )
                            for order_file in order_files:
                                if order_file.is_file():
                                    try:
                                        file_size = order_file.stat().st_size
                                        total_size += file_size
                                        order_file.unlink()
                                        deleted_count += 1
                                        order_processed = True
                                        logger.info(
                                            f"  [效果图] ✅ 已删除: {order_file.name} ({file_size / 1024:.2f} KB)"
                                        )
                                    except Exception as e:
                                        error_count += 1
                                        logger.info(
                                            f"  [效果图] ❌ 删除失败 {order_file.name}: {str(e)}"
                                        )
                    elif image_path.exists() and image_path.is_file():
                        try:
                            file_size = image_path.stat().st_size
                            total_size += file_size
                            image_path.unlink()
                            deleted_count += 1
                            order_processed = True
                            logger.info(
                                f"  [效果图] ✅ 已删除: {order.final_image} ({file_size / 1024:.2f} KB)"
                            )
                        except Exception as e:
                            error_count += 1
                            logger.info(f"  [效果图] ❌ 删除失败 {order.final_image}: {str(e)}")
                    else:
                        not_found_count += 1
                        logger.info(f"  [效果图] ⚠️ 文件不存在: {image_path}")

            # 删除无水印版本
            if order.final_image_clean:
                # 检查是否是URL
                if order.final_image_clean.startswith(("http://", "https://")):
                    logger.info(f"  [无水印效果图] ⚠️ 跳过URL路径: {order.final_image_clean}")
                else:
                    filename = os.path.basename(order.final_image_clean)
                    clean_image_path = final_path / filename
                    logger.info(
                        f"  [无水印效果图] 检查: {clean_image_path} (原始路径: {order.final_image_clean})"
                    )
                    if clean_image_path.exists() and clean_image_path.is_file():
                        try:
                            file_size = clean_image_path.stat().st_size
                            total_size += file_size
                            clean_image_path.unlink()
                            deleted_count += 1
                            order_processed = True
                            logger.info(
                                f"  [无水印效果图] ✅ 已删除: {order.final_image_clean} ({file_size / 1024:.2f} KB)"
                            )
                        except Exception as e:
                            error_count += 1
                            logger.info(
                                f"  [无水印效果图] ❌ 删除失败 {order.final_image_clean}: {str(e)}"
                            )
                    else:
                        not_found_count += 1
                        logger.info(f"  [无水印效果图] ⚠️ 文件不存在: {clean_image_path}")

            # 检查 clean_ 前缀的文件（兼容旧数据）
            if order.final_image and not order.final_image.startswith(("http://", "https://")):
                filename = os.path.basename(order.final_image)
                clean_filename = f"clean_{filename}"
                clean_image_path = final_path / clean_filename
                logger.info(f"  [clean_效果图] 检查: {clean_image_path}")
                if clean_image_path.exists() and clean_image_path.is_file():
                    # 如果数据库中没有记录，但文件存在，也删除
                    if not order.final_image_clean or order.final_image_clean != clean_filename:
                        try:
                            file_size = clean_image_path.stat().st_size
                            total_size += file_size
                            clean_image_path.unlink()
                            deleted_count += 1
                            order_processed = True
                        except Exception as e:
                            error_count += 1
                            logger.info(f"删除clean_效果图失败 {clean_filename}: {str(e)}")

            # 3. 删除 hd_images 目录中的高清图
            if order.hd_image:
                # 检查是否是URL
                if order.hd_image.startswith(("http://", "https://")):
                    logger.info(f"  [高清图] ⚠️ 跳过URL路径: {order.hd_image}")
                else:
                    filename = os.path.basename(order.hd_image)
                    image_path = hd_path / filename
                    logger.info(f"  [高清图] 检查: {image_path} (原始路径: {order.hd_image})")
                    # 如果直接路径不存在，尝试查找包含订单号的文件
                    if not image_path.exists():
                        # 尝试查找以订单号开头的文件（支持多种模式）
                        order_files = []
                        # 模式1: 订单号开头
                        order_files.extend(list(hd_path.glob(f"{order.order_number}*")))
                        # 模式2: 包含订单号
                        if not order_files:
                            order_files.extend(
                                [
                                    f
                                    for f in hd_path.glob("*")
                                    if f.is_file() and order.order_number in f.name
                                ]
                            )
                        # 模式3: 如果文件名包含订单号的一部分
                        if not order_files and len(order.order_number) > 8:
                            short_order = order.order_number[:8]
                            order_files.extend(
                                [
                                    f
                                    for f in hd_path.glob("*")
                                    if f.is_file() and short_order in f.name
                                ]
                            )

                        if order_files:
                            logger.info(
                                f"  [高清图] 找到 {len(order_files)} 个相关文件，将全部删除"
                            )
                            for order_file in order_files:
                                if order_file.is_file():
                                    try:
                                        file_size = order_file.stat().st_size
                                        total_size += file_size
                                        order_file.unlink()
                                        deleted_count += 1
                                        order_processed = True
                                        logger.info(
                                            f"  [高清图] ✅ 已删除: {order_file.name} ({file_size / 1024:.2f} KB)"
                                        )
                                    except Exception as e:
                                        error_count += 1
                                        logger.info(
                                            f"  [高清图] ❌ 删除失败 {order_file.name}: {str(e)}"
                                        )
                    elif image_path.exists() and image_path.is_file():
                        try:
                            file_size = image_path.stat().st_size
                            total_size += file_size
                            image_path.unlink()
                            deleted_count += 1
                            order_processed = True
                            logger.info(
                                f"  [高清图] ✅ 已删除: {order.hd_image} ({file_size / 1024:.2f} KB)"
                            )
                        except Exception as e:
                            error_count += 1
                            logger.info(f"  [高清图] ❌ 删除失败 {order.hd_image}: {str(e)}")
                    else:
                        not_found_count += 1
                        logger.info(f"  [高清图] ⚠️ 文件不存在: {image_path}")

            # 删除无水印高清图
            if order.hd_image_clean:
                # 检查是否是URL
                if order.hd_image_clean.startswith(("http://", "https://")):
                    logger.info(f"  [无水印高清图] ⚠️ 跳过URL路径: {order.hd_image_clean}")
                else:
                    filename = os.path.basename(order.hd_image_clean)
                    clean_image_path = hd_path / filename
                    logger.info(
                        f"  [无水印高清图] 检查: {clean_image_path} (原始路径: {order.hd_image_clean})"
                    )
                    if clean_image_path.exists() and clean_image_path.is_file():
                        try:
                            file_size = clean_image_path.stat().st_size
                            total_size += file_size
                            clean_image_path.unlink()
                            deleted_count += 1
                            order_processed = True
                            logger.info(
                                f"  [无水印高清图] ✅ 已删除: {order.hd_image_clean} ({file_size / 1024:.2f} KB)"
                            )
                        except Exception as e:
                            error_count += 1
                            logger.info(
                                f"  [无水印高清图] ❌ 删除失败 {order.hd_image_clean}: {str(e)}"
                            )
                    else:
                        not_found_count += 1
                        logger.info(f"  [无水印高清图] ⚠️ 文件不存在: {clean_image_path}")

            # 检查 clean_ 前缀的高清图（兼容旧数据）
            if order.hd_image and not order.hd_image.startswith(("http://", "https://")):
                filename = os.path.basename(order.hd_image)
                clean_filename = f"clean_{filename}"
                clean_image_path = hd_path / clean_filename
                logger.info(f"  [clean_高清图] 检查: {clean_image_path}")
                if clean_image_path.exists() and clean_image_path.is_file():
                    # 如果数据库中没有记录，但文件存在，也删除
                    if not order.hd_image_clean or order.hd_image_clean != clean_filename:
                        try:
                            file_size = clean_image_path.stat().st_size
                            total_size += file_size
                            clean_image_path.unlink()
                            deleted_count += 1
                            order_processed = True
                        except Exception as e:
                            error_count += 1
                            logger.info(f"删除clean_高清图失败 {clean_filename}: {str(e)}")

            if order_processed:
                processed_orders += 1
                logger.info(f"  [订单] ✅ 订单 {order.order_number} 已处理")
            else:
                logger.info(f"  [订单] ⚠️ 订单 {order.order_number} 没有找到可删除的文件")

        # 格式化消息
        size_mb = total_size / 1024 / 1024
        message = f"清理完成，已清理{days}天前的订单图片"
        if processed_orders > 0:
            message += f"（处理了{processed_orders}个订单，删除了{deleted_count}个文件"
            if size_mb > 0:
                message += f"，释放{size_mb:.2f}MB空间"
            message += "）"

        return jsonify(
            {
                "success": True,
                "message": message,
                "deleted_count": deleted_count,
                "orders_count": len(orders),
                "processed_orders": processed_orders,
                "not_found_count": not_found_count,
                "error_count": error_count,
                "total_size_mb": round(size_mb, 2),
            }
        )
    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        logger.info(f"执行清理失败: {error_detail}")
        return jsonify({"success": False, "message": f"执行清理失败: {str(e)}"}), 500
