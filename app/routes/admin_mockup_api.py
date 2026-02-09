# -*- coding: utf-8 -*-
"""
样机套图管理 API 和页面路由
"""

import logging
import os
import uuid

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required
from app.services.mockup_service import generate_mockup, generate_mockup_from_path, scan_psd_templates

logger = logging.getLogger(__name__)

admin_mockup_bp = Blueprint("admin_mockup", __name__)


# ============================================================================
# 页面路由
# ============================================================================


@admin_mockup_bp.route("/admin/mockup-templates")
@login_required
@admin_required
def mockup_templates_page():
    """样机套图配置页面"""
    return render_template("admin/mockup_templates.html")


# ============================================================================
# API 路由
# ============================================================================


@admin_mockup_bp.route("/api/admin/mockup/templates", methods=["GET"])
@login_required
@admin_required
def list_templates():
    """获取样机模板列表"""
    models = get_models(["MockupTemplate", "MockupTemplateProduct", "Product", "db"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    MockupTemplate = models["MockupTemplate"]
    MockupTemplateProduct = models["MockupTemplateProduct"]
    Product = models["Product"]

    templates = (
        MockupTemplate.query.order_by(MockupTemplate.sort_order.asc(), MockupTemplate.id.asc()).all()
    )
    result = []
    for t in templates:
        bindings = MockupTemplateProduct.query.filter_by(template_id=t.id).all()
        product_ids = [b.product_id for b in bindings]
        products = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
        result.append({
            "id": t.id,
            "name": t.name,
            "psd_path": t.psd_path,
            "smart_layer_name": t.smart_layer_name or "photogo",
            "preview_image_url": t.preview_image_url,
            "is_active": t.is_active,
            "sort_order": t.sort_order,
            "product_ids": product_ids,
            "products": [{"id": p.id, "name": p.name} for p in products],
        })
    return jsonify({"code": 0, "data": result})


@admin_mockup_bp.route("/api/admin/mockup/templates", methods=["POST"])
@login_required
@admin_required
def create_template():
    """创建样机模板"""
    models = get_models(["MockupTemplate", "MockupTemplateProduct", "db"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    psd_path = data.get("psd_path", "").strip()
    smart_layer_name = (data.get("smart_layer_name") or "photogo").strip()
    product_ids = data.get("product_ids") or []

    if not name or not psd_path:
        return jsonify({"code": -1, "message": "模板名称和 PSD 路径不能为空"}), 400

    db = models["db"]
    MockupTemplate = models["MockupTemplate"]
    MockupTemplateProduct = models["MockupTemplateProduct"]

    t = MockupTemplate(
        name=name,
        psd_path=psd_path,
        smart_layer_name=smart_layer_name,
        is_active=data.get("is_active", True),
        sort_order=int(data.get("sort_order") or 0),
    )
    db.session.add(t)
    db.session.flush()

    for pid in product_ids:
        if pid:
            db.session.add(MockupTemplateProduct(template_id=t.id, product_id=int(pid)))
    db.session.commit()
    return jsonify({"code": 0, "data": {"id": t.id}, "message": "创建成功"})


@admin_mockup_bp.route("/api/admin/mockup/templates/<int:template_id>", methods=["PUT"])
@login_required
@admin_required
def update_template(template_id):
    """更新样机模板"""
    models = get_models(["MockupTemplate", "MockupTemplateProduct", "db"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    t = models["MockupTemplate"].query.get(template_id)
    if not t:
        return jsonify({"code": -1, "message": "模板不存在"}), 404

    data = request.get_json() or {}
    if "name" in data:
        t.name = (data["name"] or "").strip()
    if "psd_path" in data:
        t.psd_path = (data["psd_path"] or "").strip()
    if "smart_layer_name" in data:
        t.smart_layer_name = (data["smart_layer_name"] or "photogo").strip()
    if "preview_image_url" in data:
        t.preview_image_url = data["preview_image_url"] or None
    if "is_active" in data:
        t.is_active = bool(data["is_active"])
    if "sort_order" in data:
        t.sort_order = int(data["sort_order"] or 0)

    if "product_ids" in data:
        models["MockupTemplateProduct"].query.filter_by(template_id=template_id).delete()
        for pid in (data["product_ids"] or []):
            if pid:
                models["db"].session.add(
                    models["MockupTemplateProduct"](template_id=template_id, product_id=int(pid))
                )

    models["db"].session.commit()
    return jsonify({"code": 0, "message": "更新成功"})


@admin_mockup_bp.route("/api/admin/mockup/templates/<int:template_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_template(template_id):
    """删除样机模板"""
    models = get_models(["MockupTemplate", "db"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    t = models["MockupTemplate"].query.get(template_id)
    if not t:
        return jsonify({"code": -1, "message": "模板不存在"}), 404

    models["db"].session.delete(t)
    models["db"].session.commit()
    return jsonify({"code": 0, "message": "删除成功"})


@admin_mockup_bp.route("/api/admin/mockup/products", methods=["GET"])
@login_required
@admin_required
def list_products():
    """获取产品列表（用于样机模板绑定）"""
    models = get_models(["Product"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    products = (
        models["Product"]
        .query.filter_by(is_active=True)
        .order_by(models["Product"].sort_order.asc(), models["Product"].id.asc())
        .all()
    )
    result = [{"id": p.id, "name": p.name} for p in products]
    return jsonify({"code": 0, "data": result})


@admin_mockup_bp.route("/api/admin/mockup/scan-psd", methods=["GET"])
@login_required
@admin_required
def scan_psd():
    """扫描目录下的 PSD 文件"""
    directory = request.args.get("directory", "").strip()
    if not directory:
        # 默认扫描 data/mockup_templates
        directory = os.path.join(current_app.root_path, "data", "mockup_templates")
    if not os.path.isabs(directory):
        directory = os.path.join(current_app.root_path, directory)

    if not os.path.isdir(directory):
        return jsonify({"code": 0, "data": [], "message": "目录不存在"})

    templates = scan_psd_templates(directory)
    # 转为相对路径便于存储
    for t in templates:
        t["path"] = os.path.relpath(t["path"], current_app.root_path).replace("\\", "/")
    return jsonify({"code": 0, "data": templates})


@admin_mockup_bp.route("/api/admin/mockup/order/<int:order_id>/templates", methods=["GET"])
@login_required
def get_order_mockup_templates(order_id):
    """获取订单可用的样机模板（根据订单产品）"""
    models = get_models(
        ["Order", "MockupTemplate", "MockupTemplateProduct", "Product"]
    )
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    Order = models["Order"]
    MockupTemplate = models["MockupTemplate"]
    MockupTemplateProduct = models["MockupTemplateProduct"]
    Product = models["Product"]

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"code": -1, "message": "订单不存在"}), 404

    # 根据 order.product_name 查找 Product
    product = None
    if order.product_name:
        product = Product.query.filter_by(name=order.product_name, is_active=True).first()

    if not product:
        return jsonify({"code": 0, "data": []})

    bindings = MockupTemplateProduct.query.filter_by(product_id=product.id).all()
    template_ids = [b.template_id for b in bindings]
    if not template_ids:
        return jsonify({"code": 0, "data": []})

    templates = (
        MockupTemplate.query.filter(
            MockupTemplate.id.in_(template_ids), MockupTemplate.is_active == True
        )
        .order_by(MockupTemplate.sort_order.asc())
        .all()
    )
    result = [
        {
            "id": t.id,
            "name": t.name,
            "preview_image_url": t.preview_image_url,
            "smart_layer_name": t.smart_layer_name or "photogo",
        }
        for t in templates
    ]
    return jsonify({"code": 0, "data": result})


@admin_mockup_bp.route("/api/admin/mockup/generate", methods=["POST"])
@login_required
def generate_mockup_api():
    """生成样机套图"""
    models = get_models(["MockupTemplate"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    data = request.get_json() or {}
    template_id = data.get("template_id")
    image_url = data.get("image_url", "").strip()
    output_format = data.get("output_format", "jpg")

    if not template_id or not image_url:
        return jsonify({"code": -1, "message": "缺少 template_id 或 image_url"}), 400

    template = models["MockupTemplate"].query.get(template_id)
    if not template or not template.is_active:
        return jsonify({"code": -1, "message": "模板不存在或已禁用"}), 404

    success, result = generate_mockup(template, image_url, current_app, output_format)
    if not success:
        return jsonify({"code": -1, "message": result.get("error", "生成失败")}), 500

    return jsonify({
        "code": 0,
        "data": {
            "preview_url": result["preview_url"],
            "filename": result["filename"],
        },
    })


@admin_mockup_bp.route("/api/admin/mockup/generate-test", methods=["POST"])
@login_required
@admin_required
def generate_mockup_test():
    """测试样机套图：选择模板 + 上传图片"""
    models = get_models(["MockupTemplate"])
    if not models:
        return jsonify({"code": -1, "message": "系统未初始化"}), 500

    template_id = request.form.get("template_id")
    image_file = request.files.get("image")

    if not template_id:
        return jsonify({"code": -1, "message": "请选择样机模板"}), 400
    if not image_file or not image_file.filename:
        return jsonify({"code": -1, "message": "请上传测试图片"}), 400

    # 校验文件类型
    ext = (image_file.filename or "").lower().split(".")[-1]
    if ext not in ("jpg", "jpeg", "png"):
        return jsonify({"code": -1, "message": "仅支持 JPG、PNG 格式"}), 400

    template = models["MockupTemplate"].query.get(template_id)
    if not template:
        return jsonify({"code": -1, "message": "模板不存在"}), 404

    # 保存上传文件到临时目录
    upload_dir = os.path.join(current_app.root_path, "data", "mockup_output")
    os.makedirs(upload_dir, exist_ok=True)
    temp_filename = f"test_upload_{uuid.uuid4().hex[:12]}.{ext}"
    temp_path = os.path.join(upload_dir, temp_filename)

    try:
        image_file.save(temp_path)
        success, result = generate_mockup_from_path(
            template, temp_path, current_app, output_format="jpg"
        )
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    if not success:
        return jsonify({"code": -1, "message": result.get("error", "生成失败")}), 500

    return jsonify({
        "code": 0,
        "data": {
            "preview_url": result["preview_url"],
            "filename": result["filename"],
        },
    })
