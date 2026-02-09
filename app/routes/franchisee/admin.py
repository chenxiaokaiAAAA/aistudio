# -*- coding: utf-8 -*-
"""
加盟商管理 - 管理员后台管理路由
包含所有 /admin/ 开头的路由
"""

import logging

logger = logging.getLogger(__name__)
import hashlib
import os
import time
import uuid
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import desc, func
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app.routes.franchisee.common import get_models, get_wechat_notification

# 创建管理员后台管理子蓝图
bp = Blueprint("franchisee_admin", __name__)


def require_admin():
    """检查管理员权限的装饰器函数"""
    if current_user.role != "admin":
        flash("权限不足", "error")
        return redirect(url_for("admin_dashboard"))
    return None


@bp.route("/admin/accounts")
@login_required
def admin_franchisee_list():
    """管理员 - 加盟商账户列表"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin_dashboard"))

    FranchiseeAccount = models["FranchiseeAccount"]
    db = models["db"]

    # 获取筛选参数
    status = request.args.get("status", "")
    search = request.args.get("search", "")

    # 构建查询
    query = FranchiseeAccount.query

    if status:
        query = query.filter(FranchiseeAccount.status == status)

    if search:
        query = query.filter(
            (FranchiseeAccount.company_name.contains(search))
            | (FranchiseeAccount.contact_person.contains(search))
            | (FranchiseeAccount.contact_phone.contains(search))
        )

    accounts = query.order_by(desc(FranchiseeAccount.created_at)).all()

    return render_template(
        "admin/franchisee_list.html", accounts=accounts, status=status, search=search
    )


@bp.route("/admin/accounts/export")
@login_required
def export_franchisee_monthly_report():
    """导出加盟商月度报表"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin_dashboard"))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    FranchiseeRecharge = models["FranchiseeRecharge"]
    Order = models["Order"]

    import csv
    from io import StringIO

    try:
        # 获取月份参数（默认为当前月份）
        year_month = request.args.get("month", datetime.now().strftime("%Y-%m"))

        # 解析年月
        try:
            year, month = map(int, year_month.split("-"))
        except Exception:
            year = datetime.now().year
            month = datetime.now().month

        # 计算月份的开始和结束时间
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # 获取所有加盟商
        accounts = FranchiseeAccount.query.all()
        account_ids = [account.id for account in accounts]

        # 优化N+1查询：批量查询所有加盟商的统计数据
        recharge_stats_map = {}
        bonus_stats_map = {}
        consumption_stats_map = {}

        if account_ids:
            # 批量查询所有加盟商的充值金额
            recharge_stats = (
                db.session.query(
                    FranchiseeRecharge.franchisee_id,
                    func.sum(FranchiseeRecharge.amount).label("total_amount"),
                )
                .filter(
                    FranchiseeRecharge.franchisee_id.in_(account_ids),
                    FranchiseeRecharge.created_at >= start_date,
                    FranchiseeRecharge.created_at < end_date,
                )
                .group_by(FranchiseeRecharge.franchisee_id)
                .all()
            )
            recharge_stats_map = {row[0]: float(row[1] or 0) for row in recharge_stats}

            # 批量查询所有加盟商的赠送金额
            bonus_stats = (
                db.session.query(
                    FranchiseeRecharge.franchisee_id,
                    func.sum(FranchiseeRecharge.bonus_amount).label("total_bonus"),
                )
                .filter(
                    FranchiseeRecharge.franchisee_id.in_(account_ids),
                    FranchiseeRecharge.created_at >= start_date,
                    FranchiseeRecharge.created_at < end_date,
                )
                .group_by(FranchiseeRecharge.franchisee_id)
                .all()
            )
            bonus_stats_map = {row[0]: float(row[1] or 0) for row in bonus_stats}

            # 批量查询所有加盟商的消费金额
            consumption_stats = (
                db.session.query(
                    Order.franchisee_id,
                    func.sum(Order.franchisee_deduction).label("total_consumption"),
                )
                .filter(
                    Order.franchisee_id.in_(account_ids),
                    Order.created_at >= start_date,
                    Order.created_at < end_date,
                    Order.franchisee_deduction.isnot(None),
                )
                .group_by(Order.franchisee_id)
                .all()
            )
            consumption_stats_map = {row[0]: float(row[1] or 0) for row in consumption_stats}

        # 创建CSV内容
        output = StringIO()
        writer = csv.writer(output)

        # 写入CSV头部
        headers = [
            "公司名称",
            "用户名",
            "联系人",
            "联系电话",
            "当月充值金额",
            "当月赠送金额",
            "当月消费金额",
            "当前余额",
            "总额度",
            "已使用额度",
            "剩余额度",
            "状态",
        ]
        writer.writerow(headers)

        # 统计每个加盟商的数据（从批量查询的映射中获取）
        for account in accounts:
            # 从批量查询的映射中获取统计数据（避免N+1查询）
            recharge_amount = recharge_stats_map.get(account.id, 0)
            bonus_amount = bonus_stats_map.get(account.id, 0)
            consumption_amount = consumption_stats_map.get(account.id, 0)

            # 当前余额（剩余额度）
            current_balance = account.remaining_quota

            # 写入一行数据
            writer.writerow(
                [
                    account.company_name,
                    account.username,
                    account.contact_person,
                    account.contact_phone,
                    f"{recharge_amount:.2f}",
                    f"{bonus_amount:.2f}",
                    f"{consumption_amount:.2f}",
                    f"{current_balance:.2f}",
                    f"{account.total_quota:.2f}",
                    f"{account.used_quota:.2f}",
                    f"{account.remaining_quota:.2f}",
                    account.status,
                ]
            )

        # 创建响应
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8-sig"  # Excel兼容
        response.headers["Content-Disposition"] = (
            f"attachment; filename=franchisee_report_{year_month}.csv"
        )

        return response

    except Exception as e:
        db.session.rollback()
        flash(f"导出失败: {str(e)}", "error")
        return redirect(url_for("franchisee.franchisee_admin.admin_franchisee_list"))


@bp.route("/admin/accounts/add", methods=["GET", "POST"])
@login_required
def admin_add_franchisee():
    """管理员 - 添加加盟商账户"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin_dashboard"))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    FranchiseeRecharge = models["FranchiseeRecharge"]

    if request.method == "POST":
        try:
            # 获取表单数据
            username = request.form.get("username")
            password = request.form.get("password")
            company_name = request.form.get("company_name")
            contact_person = request.form.get("contact_person")
            contact_phone = request.form.get("contact_phone")
            contact_email = request.form.get("contact_email")
            address = request.form.get("address")
            initial_quota = float(request.form.get("initial_quota", 0))

            # 验证必填字段
            if not all([username, password, company_name, contact_person, contact_phone]):
                flash("请填写所有必填字段", "error")
                return render_template("admin/franchisee_add.html")

            # 检查用户名是否已存在
            if FranchiseeAccount.query.filter_by(username=username).first():
                flash("用户名已存在", "error")
                return render_template("admin/franchisee_add.html")

            # 生成二维码标识
            qr_code = f"FRANCH_{hashlib.md5(f'{username}{time.time()}'.encode()).hexdigest()[:12].upper()}"

            # 获取门店和自拍机信息
            store_name = request.form.get("store_name", "").strip() or None
            machine_name = request.form.get("machine_name", "").strip() or None
            machine_serial_number = request.form.get("machine_serial_number", "").strip() or None

            # 创建加盟商账户
            franchisee = FranchiseeAccount(
                username=username,
                password=generate_password_hash(password),
                company_name=company_name,
                contact_person=contact_person,
                contact_phone=contact_phone,
                contact_email=contact_email,
                address=address,
                total_quota=initial_quota,
                remaining_quota=initial_quota,
                qr_code=qr_code,
                store_name=store_name,
                machine_name=machine_name,
                machine_serial_number=machine_serial_number,
            )

            db.session.add(franchisee)
            db.session.flush()  # 获取ID

            # 如果有初始额度，创建充值记录
            if initial_quota > 0:
                recharge = FranchiseeRecharge(
                    franchisee_id=franchisee.id,
                    amount=initial_quota,
                    admin_user_id=current_user.id,
                    recharge_type="manual",
                    description=f"账户创建时初始充值 {initial_quota} 元",
                )
                db.session.add(recharge)

            db.session.commit()
            flash("加盟商账户创建成功", "success")
            return redirect(url_for("franchisee.franchisee_admin.admin_franchisee_list"))

        except Exception as e:
            db.session.rollback()
            flash(f"创建失败: {str(e)}", "error")
            return render_template("admin/franchisee_add.html")

    return render_template("admin/franchisee_add.html")


@bp.route("/admin/accounts/<int:account_id>/recharge", methods=["GET", "POST"])
@login_required
def admin_recharge_franchisee(account_id):
    """管理员 - 为加盟商充值"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin_dashboard"))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    FranchiseeRecharge = models["FranchiseeRecharge"]

    account = FranchiseeAccount.query.get_or_404(account_id)

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount"))
            bonus_amount = float(request.form.get("bonus_amount", 0))
            description = request.form.get("description", "")
            recharge_type = request.form.get("recharge_type", "manual")

            if amount <= 0:
                flash("充值金额必须大于0", "error")
                return render_template("admin/franchisee_recharge.html", account=account)

            # 计算实际充值总额
            total_amount = amount + bonus_amount

            # 更新账户额度（使用实际总额）
            account.total_quota += total_amount
            account.remaining_quota += total_amount

            # 构建充值说明
            if bonus_amount > 0:
                desc_text = (
                    f"管理员充值 {amount} 元，赠送 {bonus_amount} 元，实际到账 {total_amount} 元"
                )
            else:
                desc_text = description or f"管理员充值 {amount} 元"

            # 创建充值记录
            recharge = FranchiseeRecharge(
                franchisee_id=account.id,
                amount=amount,  # 充值金额（加盟商看到的）
                bonus_amount=bonus_amount,  # 赠送金额
                total_amount=total_amount,  # 实际充值总额
                admin_user_id=current_user.id,
                recharge_type=recharge_type,
                description=desc_text,
            )

            db.session.add(recharge)
            db.session.commit()

            # 提示消息（区分是否有赠送）
            if bonus_amount > 0:
                flash(
                    f"成功充值！充值 {amount} 元，赠送 {bonus_amount} 元，合计到账 {total_amount} 元",
                    "success",
                )
            else:
                flash(f"成功为 {account.company_name} 充值 {amount} 元", "success")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        except Exception as e:
            db.session.rollback()
            flash(f"充值失败: {str(e)}", "error")

    return render_template("admin/franchisee_recharge.html", account=account)


@bp.route("/admin/accounts/<int:account_id>")
@login_required
def admin_franchisee_detail(account_id):
    """管理员 - 加盟商账户详情"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin_dashboard"))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    FranchiseeRecharge = models["FranchiseeRecharge"]
    Order = models["Order"]
    SelfieMachine = models["SelfieMachine"]

    account = FranchiseeAccount.query.get_or_404(account_id)

    # 获取充值记录
    recharge_records = (
        FranchiseeRecharge.query.filter_by(franchisee_id=account_id)
        .order_by(desc(FranchiseeRecharge.created_at))
        .all()
    )

    # 获取订单记录
    orders = Order.query.filter_by(franchisee_id=account_id).order_by(desc(Order.created_at)).all()

    # 获取自拍机设备列表
    machines = (
        SelfieMachine.query.filter_by(franchisee_id=account_id)
        .order_by(desc(SelfieMachine.created_at))
        .all()
    )

    # 获取店员用户列表
    StaffUser = models.get("StaffUser")
    staff_users = []
    if StaffUser:
        staff_users = (
            StaffUser.query.filter_by(franchisee_id=account_id)
            .order_by(desc(StaffUser.created_at))
            .all()
        )

    # 获取退款申请列表 - 检查字段是否存在
    try:
        inspector = db.inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("orders")]

        if "refund_request_status" in columns:
            refund_requests = (
                Order.query.filter_by(franchisee_id=account_id)
                .filter(Order.refund_request_status.isnot(None))
                .order_by(desc(Order.refund_request_time))
                .all()
            )
        else:
            refund_requests = []
    except Exception as e:
        logger.info(f"获取退款申请列表失败: {e}")
        refund_requests = []

    # 统计数据
    total_orders = len(orders)
    total_order_amount = sum(order.price for order in orders if order.price)
    total_deduction = sum(
        order.franchisee_deduction for order in orders if order.franchisee_deduction
    )

    return render_template(
        "admin/franchisee_detail.html",
        account=account,
        recharge_records=recharge_records,
        orders=orders,
        machines=machines,
        staff_users=staff_users,
        refund_requests=refund_requests,
        total_orders=total_orders,
        total_order_amount=total_order_amount,
        total_deduction=total_deduction,
    )


@bp.route("/admin/accounts/<int:account_id>/qrcode-preview")
@login_required
def admin_qrcode_preview(account_id):
    """加盟商二维码预览"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        return jsonify({"success": False, "message": "系统未初始化"}), 500

    FranchiseeAccount = models["FranchiseeAccount"]

    try:
        account = FranchiseeAccount.query.get_or_404(account_id)

        # 生成二维码内容
        qr_content = f"https://photogooo/franchisee/scan/{account.qr_code}"

        # 创建二维码
        import base64
        import io

        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # 生成二维码图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

        return jsonify(
            {
                "success": True,
                "qrcode": f"data:image/png;base64,{img_base64}",
                "content": qr_content,
                "company_name": account.company_name,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"生成二维码失败: {str(e)}"}), 500


@bp.route("/admin/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_franchisee(account_id):
    """管理员 - 编辑加盟商账户"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("admin_dashboard"))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]

    account = FranchiseeAccount.query.get_or_404(account_id)

    if request.method == "POST":
        try:
            account.company_name = request.form.get("company_name")
            account.contact_person = request.form.get("contact_person")
            account.contact_phone = request.form.get("contact_phone")
            # 联系邮箱字段已取消
            # account.contact_email = request.form.get('contact_email')
            account.address = request.form.get("address")
            account.status = request.form.get("status")

            # 门店和自拍机信息已删除（底部已有）
            # account.store_name = request.form.get('store_name', '').strip() or None
            # account.machine_name = request.form.get('machine_name', '').strip() or None
            # account.machine_serial_number = request.form.get('machine_serial_number', '').strip() or None

            # 如果修改了密码
            new_password = request.form.get("new_password")
            if new_password:
                account.password = generate_password_hash(new_password)

            # 处理水印上传
            if "watermark" in request.files:
                watermark_file = request.files["watermark"]
                if watermark_file and watermark_file.filename:
                    # 确保上传目录存在
                    upload_dir = "final_works"
                    os.makedirs(upload_dir, exist_ok=True)

                    # 保存水印文件
                    filename = f"franchisee_{account_id}_{uuid.uuid4()}_{secure_filename(watermark_file.filename)}"
                    file_path = os.path.join(upload_dir, filename)
                    watermark_file.save(file_path)

                    # 保存到数据库
                    account.watermark_path = filename
                    logger.info(f"✅ 已保存加盟商水印: {file_path}")

            db.session.commit()
            flash("账户信息更新成功", "success")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        except Exception as e:
            db.session.rollback()
            flash(f"更新失败: {str(e)}", "error")

    return render_template("admin/franchisee_edit.html", account=account)


@bp.route("/admin/accounts/<int:account_id>/delete", methods=["POST"])
@login_required
def admin_delete_franchisee(account_id):
    """管理员 - 删除加盟商账户"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("franchisee.franchisee_admin.admin_franchisee_list"))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    FranchiseeRecharge = models["FranchiseeRecharge"]
    Order = models["Order"]

    account = FranchiseeAccount.query.get_or_404(account_id)

    try:
        # 检查是否有关联的订单
        order_count = Order.query.filter_by(franchisee_id=account_id).count()

        # 检查是否有关联的充值记录
        recharge_count = FranchiseeRecharge.query.filter_by(franchisee_id=account_id).count()

        if order_count > 0:
            flash(f"无法删除：该加盟商账户关联了 {order_count} 个订单，请先处理相关订单", "error")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        if recharge_count > 0:
            # 如果有充值记录，删除充值记录
            FranchiseeRecharge.query.filter_by(franchisee_id=account_id).delete()

        # 删除账户
        db.session.delete(account)
        db.session.commit()

        flash(f'加盟商账户 "{account.company_name}" 已成功删除', "success")
        logger.info(
            f"✅ 管理员 {current_user.username} 删除了加盟商账户: {account.company_name} (ID: {account_id})"
        )

    except Exception as e:
        db.session.rollback()
        flash(f"删除失败: {str(e)}", "error")
        logger.error("删除加盟商账户失败: {e}")
        import traceback

        traceback.print_exc()
        return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))

    return redirect(url_for("franchisee_admin.admin_franchisee_list"))


@bp.route("/admin/accounts/<int:account_id>/machines/add", methods=["POST"])
@login_required
def admin_add_machine(account_id):
    """管理员 - 添加自拍机设备"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    SelfieMachine = models["SelfieMachine"]

    account = FranchiseeAccount.query.get_or_404(account_id)

    try:
        machine_name = request.form.get("machine_name", "").strip()
        machine_serial_number = request.form.get("machine_serial_number", "").strip()
        location = request.form.get("location", "").strip() or None
        notes = request.form.get("notes", "").strip() or None

        if not machine_name or not machine_serial_number:
            flash("设备名称和序列号不能为空", "error")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        # 检查序列号是否已存在
        existing_machine = SelfieMachine.query.filter_by(
            machine_serial_number=machine_serial_number
        ).first()
        if existing_machine:
            flash(f"序列号 {machine_serial_number} 已被使用", "error")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        # 创建设备
        machine = SelfieMachine(
            franchisee_id=account_id,
            machine_name=machine_name,
            machine_serial_number=machine_serial_number,
            location=location,
            notes=notes,
            status="active",
        )

        db.session.add(machine)
        db.session.commit()

        flash(f'设备 "{machine_name}" 添加成功', "success")
        logger.info(
            f"✅ 管理员 {current_user.username} 为加盟商 {account.company_name} 添加了设备: {machine_name} (序列号: {machine_serial_number})"
        )

    except Exception as e:
        db.session.rollback()
        flash(f"添加设备失败: {str(e)}", "error")
        logger.error("添加设备失败: {e}")
        import traceback

        traceback.print_exc()

    return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))


@bp.route("/admin/accounts/<int:account_id>/machines/<int:machine_id>/edit", methods=["POST"])
@login_required
def admin_edit_machine(account_id, machine_id):
    """管理员 - 编辑自拍机设备"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    SelfieMachine = models["SelfieMachine"]

    account = FranchiseeAccount.query.get_or_404(account_id)
    machine = SelfieMachine.query.filter_by(id=machine_id, franchisee_id=account_id).first_or_404()

    try:
        machine_name = request.form.get("machine_name", "").strip()
        machine_serial_number = request.form.get("machine_serial_number", "").strip()
        location = request.form.get("location", "").strip() or None
        notes = request.form.get("notes", "").strip() or None
        status = request.form.get("status", "active")

        if not machine_name or not machine_serial_number:
            flash("设备名称和序列号不能为空", "error")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        # 检查序列号是否被其他设备使用
        if machine_serial_number != machine.machine_serial_number:
            existing_machine = SelfieMachine.query.filter_by(
                machine_serial_number=machine_serial_number
            ).first()
            if existing_machine:
                flash(f"序列号 {machine_serial_number} 已被其他设备使用", "error")
                return redirect(
                    url_for(
                        "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                    )
                )

        # 更新设备信息
        machine.machine_name = machine_name
        machine.machine_serial_number = machine_serial_number
        machine.location = location
        machine.notes = notes
        machine.status = status

        db.session.commit()

        flash(f'设备 "{machine_name}" 更新成功', "success")
        logger.info(
            f"✅ 管理员 {current_user.username} 更新了设备: {machine_name} (序列号: {machine_serial_number})"
        )

    except Exception as e:
        db.session.rollback()
        flash(f"更新设备失败: {str(e)}", "error")
        logger.error("更新设备失败: {e}")
        import traceback

        traceback.print_exc()

    return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))


@bp.route("/admin/accounts/<int:account_id>/machines/<int:machine_id>/delete", methods=["POST"])
@login_required
def admin_delete_machine(account_id, machine_id):
    """管理员 - 删除自拍机设备"""
    if require_admin():
        return require_admin()

    models = get_models()
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]
    SelfieMachine = models["SelfieMachine"]
    Order = models["Order"]

    account = FranchiseeAccount.query.get_or_404(account_id)
    machine = SelfieMachine.query.filter_by(id=machine_id, franchisee_id=account_id).first_or_404()

    try:
        # 检查是否有关联的订单
        order_count = Order.query.filter_by(selfie_machine_id=machine.machine_serial_number).count()

        if order_count > 0:
            flash(f"无法删除：该设备关联了 {order_count} 个订单，请先处理相关订单", "error")
            return redirect(
                url_for(
                    "franchisee.franchisee_admin.admin_franchisee_detail", account_id=account_id
                )
            )

        machine_name = machine.machine_name
        db.session.delete(machine)
        db.session.commit()

        flash(f'设备 "{machine_name}" 已成功删除', "success")
        logger.info(
            f"✅ 管理员 {current_user.username} 删除了设备: {machine_name} (序列号: {machine.machine_serial_number})"
        )

    except Exception as e:
        db.session.rollback()
        flash(f"删除设备失败: {str(e)}", "error")
        logger.error("删除设备失败: {e}")
        import traceback

        traceback.print_exc()

    return redirect(url_for("franchisee_admin.admin_franchisee_detail", account_id=account_id))


@bp.route("/admin/accounts/<int:account_id>/watermark", methods=["POST"])
@login_required
def admin_upload_watermark(account_id):
    """管理员 - 上传加盟商专属水印"""
    if current_user.role != "admin":
        return jsonify({"success": False, "message": "权限不足"}), 403

    models = get_models()
    if not models:
        return jsonify({"success": False, "message": "系统未初始化"}), 500

    db = models["db"]
    FranchiseeAccount = models["FranchiseeAccount"]

    account = FranchiseeAccount.query.get_or_404(account_id)

    if "watermark" not in request.files:
        return jsonify({"success": False, "message": "请选择文件"}), 400

    watermark_file = request.files["watermark"]
    if not watermark_file or not watermark_file.filename:
        return jsonify({"success": False, "message": "请选择文件"}), 400

    try:
        # 确保上传目录存在
        upload_dir = "final_works"
        os.makedirs(upload_dir, exist_ok=True)

        # 删除旧的水印文件（如果存在）
        if account.watermark_path:
            old_path = os.path.join(upload_dir, account.watermark_path)
            if os.path.exists(old_path):
                os.remove(old_path)
                logger.info(f"🗑️ 已删除旧水印: {old_path}")

        # 保存新的水印文件
        filename = (
            f"franchisee_{account_id}_{uuid.uuid4()}_{secure_filename(watermark_file.filename)}"
        )
        file_path = os.path.join(upload_dir, filename)
        watermark_file.save(file_path)

        # 保存到数据库
        account.watermark_path = filename
        db.session.commit()

        logger.info(f"✅ 已保存加盟商水印: {file_path}")
        flash("水印上传成功", "success")
        return jsonify({"success": True, "message": "水印上传成功", "filename": filename})

    except Exception as e:
        db.session.rollback()
        logger.error("水印上传失败: {str(e)}")
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500
