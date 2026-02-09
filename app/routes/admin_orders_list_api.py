# -*- coding: utf-8 -*-
"""
管理后台订单列表API路由模块
提供订单列表、筛选、导出功能
"""

import logging

logger = logging.getLogger(__name__)
import csv
import io
import json
from datetime import datetime

from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_required

# 创建蓝图
admin_orders_list_bp = Blueprint("admin_orders_list", __name__)


@admin_orders_list_bp.route("/admin/orders")
@login_required
@admin_required
def admin_orders():
    """订单管理页面"""
    models = get_models(["Order", "FranchiseeAccount", "db"])
    if not models:
        flash("系统未初始化", "error")
        return redirect(url_for("auth.login"))

    Order = models["Order"]
    FranchiseeAccount = models["FranchiseeAccount"]
    db = models["db"]

    # 获取筛选参数
    franchisee_id = request.args.get("franchisee_id", "")
    status = request.args.get("status", "")
    order_mode = request.args.get("order_mode", "")
    search = request.args.get("search", "").strip()  # 订单搜索
    page = request.args.get("page", 1, type=int)  # 分页参数
    per_page = 10  # 每页显示10条

    # 构建查询 - 过滤掉未支付订单（除非专门查unpaid状态）
    if status == "unpaid":
        query = Order.query
    else:
        query = Order.query.filter(Order.status != "unpaid")

    # 按加盟商（门店）筛选
    if franchisee_id:
        query = query.filter(Order.franchisee_id == int(franchisee_id))

    if status and status != "unpaid":
        query = query.filter(Order.status == status)
    elif status == "unpaid":
        query = query.filter(Order.status == "unpaid")

    # 按订单类型筛选
    if order_mode:
        query = query.filter(Order.order_mode == order_mode)

    # 订单搜索（按订单号、客户姓名、客户电话搜索）
    if search:
        from sqlalchemy import or_

        query = query.filter(
            or_(
                Order.order_number.like(f"%{search}%"),
                Order.customer_name.like(f"%{search}%"),
                Order.customer_phone.like(f"%{search}%"),
            )
        )

    # 优化：先获取不重复的订单号列表（数据库层面分页）
    # 1. 构建基础查询（用于统计和获取订单号）
    base_query = db.session.query(Order.order_number)

    # 应用相同的筛选条件
    if status == "unpaid":
        base_query = base_query.filter(Order.status == "unpaid")
    else:
        base_query = base_query.filter(Order.status != "unpaid")

    if franchisee_id:
        base_query = base_query.filter(Order.franchisee_id == int(franchisee_id))

    if status and status != "unpaid":
        base_query = base_query.filter(Order.status == status)

    if order_mode:
        base_query = base_query.filter(Order.order_mode == order_mode)

    if search:
        from sqlalchemy import or_

        base_query = base_query.filter(
            or_(
                Order.order_number.like(f"%{search}%"),
                Order.customer_name.like(f"%{search}%"),
                Order.customer_phone.like(f"%{search}%"),
            )
        )

    # 2. 获取不重复的订单号总数
    total_count = base_query.distinct().count()

    # 3. 获取每个订单号的最早创建时间，用于排序
    from sqlalchemy import text

    order_numbers_subquery = db.session.query(
        Order.order_number, func.min(Order.created_at).label("min_created_at")
    ).group_by(Order.order_number)

    # 应用相同的筛选条件到子查询
    if status == "unpaid":
        order_numbers_subquery = order_numbers_subquery.filter(Order.status == "unpaid")
    else:
        order_numbers_subquery = order_numbers_subquery.filter(Order.status != "unpaid")

    if franchisee_id:
        order_numbers_subquery = order_numbers_subquery.filter(
            Order.franchisee_id == int(franchisee_id)
        )

    if status and status != "unpaid":
        order_numbers_subquery = order_numbers_subquery.filter(Order.status == status)

    if order_mode:
        order_numbers_subquery = order_numbers_subquery.filter(Order.order_mode == order_mode)

    if search:
        from sqlalchemy import or_

        order_numbers_subquery = order_numbers_subquery.filter(
            or_(
                Order.order_number.like(f"%{search}%"),
                Order.customer_name.like(f"%{search}%"),
                Order.customer_phone.like(f"%{search}%"),
            )
        )

    # 排序并分页
    order_numbers_subquery = order_numbers_subquery.order_by(text("min_created_at DESC"))
    offset = (page - 1) * per_page
    paginated_order_numbers = order_numbers_subquery.offset(offset).limit(per_page).all()

    # 4. 获取这些订单号对应的所有订单记录
    order_numbers = [row[0] for row in paginated_order_numbers]
    if not order_numbers:
        paginated_orders = []
    else:
        # 查询这些订单号的所有订单记录
        orders_query = query.filter(Order.order_number.in_(order_numbers))
        all_orders = (
            orders_query.options(joinedload(Order.franchisee_account))
            .order_by(Order.created_at.desc())
            .all()
        )

        # 按订单号分组，每个订单号只显示一条记录（使用第一个订单作为主订单）
        orders_by_number = {}
        for order in all_orders:
            if order.order_number not in orders_by_number:
                orders_by_number[order.order_number] = {
                    "main_order": order,  # 主订单（用于显示基本信息）
                    "items": [],  # 所有商品列表
                    "total_price": 0.0,  # 总金额
                    "item_count": 0,  # 商品数量
                }

            # 添加商品信息
            orders_by_number[order.order_number]["items"].append(
                {
                    "id": order.id,
                    "product_name": order.product_name,
                    "price": order.price,
                    "status": order.status,
                }
            )
            orders_by_number[order.order_number]["total_price"] += float(order.price or 0)
            orders_by_number[order.order_number]["item_count"] += 1

        # 转换为列表，每个订单号一条记录，按订单号在分页列表中的顺序排序
        orders = []
        for order_number in order_numbers:
            if order_number in orders_by_number:
                order_data = orders_by_number[order_number]
                main_order = order_data["main_order"]
                item_count = order_data["item_count"]
                total_price = order_data["total_price"]

                # 创建一个类似Order对象的对象，包含合并后的信息
                # 为了兼容模板，我们创建一个简单的对象
                class MergedOrder:
                    def __init__(self, main_order, item_count, total_price, items):
                        # 复制主订单的所有属性
                        for attr in dir(main_order):
                            if not attr.startswith("_") and not callable(getattr(main_order, attr)):
                                try:
                                    setattr(self, attr, getattr(main_order, attr))
                                except Exception:
                                    pass
                        # 覆盖价格
                        self.price = total_price
                        self.item_count = item_count
                        self.items = items
                        # 如果多个商品，修改产品名称显示
                        if item_count > 1:
                            # 显示第一个商品名称 + "等X件"
                            first_product = (
                                items[0]["product_name"] if items else main_order.product_name
                            )
                            self.product_name = f"{first_product} 等{item_count}件"
                        else:
                            self.product_name = main_order.product_name

                merged_order = MergedOrder(main_order, item_count, total_price, order_data["items"])
                orders.append(merged_order)

        paginated_orders = orders

    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 1

    # 获取所有加盟商（门店）列表
    # 优化：虽然加盟商数量通常不多，但为了保持一致性，仍然支持分页
    # 但默认返回所有（因为数量通常<100）
    franchisees = (
        FranchiseeAccount.query.filter_by(status="active")
        .order_by(FranchiseeAccount.company_name)
        .all()
    )

    # 统计数据 - 按订单号统计（不重复计算）
    # 获取所有不重复的订单号数量
    today = datetime.now().date()
    total_orders = (
        db.session.query(func.count(func.distinct(Order.order_number)))
        .filter(Order.status != "unpaid")
        .scalar()
        or 0
    )

    # 计算每日订单数（今天创建的订单，按订单号去重）
    daily_orders = (
        db.session.query(func.count(func.distinct(Order.order_number)))
        .filter(func.date(Order.created_at) == today, Order.status != "unpaid")
        .scalar()
        or 0
    )

    # 计算每日业绩总额（今天完成的订单总金额，需要按订单号分组后求和）
    # 先获取今天完成的所有订单号
    completed_order_numbers = (
        db.session.query(Order.order_number)
        .filter(func.date(Order.completed_at) == today, Order.status == "completed")
        .distinct()
        .all()
    )

    daily_revenue = 0.0
    for order_number_tuple in completed_order_numbers:
        order_number = order_number_tuple[0]
        # 计算该订单号下所有订单的总金额
        order_total = (
            db.session.query(func.sum(Order.price))
            .filter(Order.order_number == order_number)
            .scalar()
            or 0.0
        )
        daily_revenue += float(order_total)

    # 计算待发货订单数（状态为completed或hd_ready但未发货的订单，按订单号去重）
    pending_shipment_order_numbers = (
        db.session.query(Order.order_number)
        .filter(
            Order.status.in_(["completed", "hd_ready"]), ~Order.status.in_(["shipped", "delivered"])
        )
        .distinct()
        .all()
    )
    pending_shipment_orders = len(pending_shipment_order_numbers)

    return render_template(
        "admin/orders.html",
        orders=paginated_orders,
        franchisees=franchisees,
        franchisee_id=franchisee_id,
        status=status,
        order_mode=order_mode,
        search=search,
        total_orders=total_orders,
        daily_orders=daily_orders,
        daily_revenue=daily_revenue,
        pending_shipment_orders=pending_shipment_orders,
        current_page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


@admin_orders_list_bp.route("/admin/orders/export", methods=["GET"])
@login_required
@admin_required
def export_orders():
    """导出所有订单数据为CSV格式（流式导出，优化内存使用）"""
    try:
        models = get_models(["Order", "FranchiseeAccount", "db"])
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        Order = models["Order"]
        FranchiseeAccount = models["FranchiseeAccount"]
        db = models["db"]

        # 获取筛选参数（支持筛选）
        status = request.args.get("status", "")
        franchisee_id = request.args.get("franchisee_id", "")
        order_mode = request.args.get("order_mode", "")
        search = request.args.get("search", "").strip()

        # 构建查询
        query = Order.query.filter(Order.status != "unpaid")

        if status and status != "unpaid":
            query = query.filter(Order.status == status)
        elif status == "unpaid":
            query = Order.query.filter(Order.status == "unpaid")

        if franchisee_id:
            query = query.filter(Order.franchisee_id == int(franchisee_id))

        if order_mode:
            query = query.filter(Order.order_mode == order_mode)

        if search:
            from sqlalchemy import or_

            query = query.filter(
                or_(
                    Order.order_number.like(f"%{search}%"),
                    Order.customer_name.like(f"%{search}%"),
                    Order.customer_phone.like(f"%{search}%"),
                )
            )

        # 获取总数（用于限制）
        total_count = query.count()
        logger.info(f"📊 导出查询统计: 符合条件的订单数量 = {total_count}")

        # 如果查询结果为空，检查原因并返回友好的错误提示
        if total_count == 0:
            # 检查数据库中是否有订单
            total_orders = Order.query.count()
            unpaid_count = Order.query.filter(Order.status == "unpaid").count()
            logger.warning(
                f"⚠️  导出查询结果为空！总订单数: {total_orders}, 未支付订单数: {unpaid_count}"
            )

            # 返回友好的错误提示
            if total_orders == 0:
                return jsonify({"success": False, "message": "数据库中没有任何订单数据。"}), 400
            elif unpaid_count == total_orders:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f'数据库中有 {total_orders} 条订单，但都是未支付状态。导出功能默认排除未支付订单。如需导出未支付订单，请使用筛选条件选择"未支付"状态。',
                        }
                    ),
                    400,
                )
            else:
                return (
                    jsonify(
                        {"success": False, "message": "没有符合条件的订单数据。请检查筛选条件。"}
                    ),
                    400,
                )

        max_export_limit = 50000  # 最多导出5万条

        if total_count > max_export_limit:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"订单数量过多（{total_count}条），超过导出限制（{max_export_limit}条）。请使用筛选条件缩小范围。",
                    }
                ),
                400,
            )

        # 来源类型中文映射
        source_type_map = {
            "miniprogram": "小程序",
            "website": "网站",
            "douyin": "抖音",
            "franchisee": "加盟商",
        }

        # 地址解析函数
        def parse_address(shipping_info_str):
            """解析地址信息"""
            try:
                shipping_info = json.loads(shipping_info_str) if shipping_info_str else {}
                receiver = shipping_info.get("receiver", "")
                full_address = shipping_info.get("fullAddress", "")

                if full_address:
                    return full_address

                # 拼接省市区
                province = shipping_info.get("province", "")
                city = shipping_info.get("city", "")
                district = shipping_info.get("district", "")
                address = shipping_info.get("address", "")

                address_parts = [receiver, province, city, district, address]
                address_parts = [p for p in address_parts if p]  # 过滤空值
                return " ".join(address_parts) if address_parts else ""
            except Exception:
                return shipping_info_str if shipping_info_str else ""

        # 状态中文映射
        status_map = {
            "unpaid": "未支付",
            "pending": "待制作",
            "processing": "处理中",
            "manufacturing": "制作中",
            "completed": "已完成",
            "shipped": "已发货",
            "delivered": "已送达",
            "cancelled": "已取消",
            "refunded": "已退款",
            "hd_ready": "高清放大",
        }

        # 在请求上下文中预先查询所有订单数据（避免在生成器中查询数据库）
        # 这样可以避免"Working outside of application context"错误
        # 分批查询订单，但预先加载所有数据到内存
        batch_size = 1000
        all_orders_data = []  # 存储订单的字典数据，而不是ORM对象
        offset = 0
        # 优化N+1查询：预先批量查询所有需要的加盟商信息
        franchisee_cache = {}
        all_franchisee_ids = set()

        # 先收集所有订单的franchisee_id（使用临时查询）
        temp_offset = 0
        while True:
            temp_batch = (
                query.order_by(Order.created_at.desc()).offset(temp_offset).limit(batch_size).all()
            )
            if not temp_batch:
                break
            for order in temp_batch:
                if order.franchisee_id:
                    all_franchisee_ids.add(order.franchisee_id)
            temp_offset += batch_size
            if len(temp_batch) < batch_size:
                break

        # 批量查询所有加盟商
        if all_franchisee_ids:
            all_franchisees = FranchiseeAccount.query.filter(
                FranchiseeAccount.id.in_(list(all_franchisee_ids))
            ).all()
            for franchisee in all_franchisees:
                franchisee_cache[franchisee.id] = f"加盟商:{franchisee.company_name}"

        # 重置offset
        offset = 0

        logger.info("📦 开始预查询订单数据...")
        while True:
            orders_batch = (
                query.order_by(Order.created_at.desc()).offset(offset).limit(batch_size).all()
            )
            if not orders_batch:
                break

            # 在请求上下文中预先访问所有需要的属性，转换为字典
            for order in orders_batch:
                # 预先访问关联对象（在请求上下文中）
                merchant_name = ""
                if hasattr(order, "merchant") and order.merchant:
                    merchant_name = order.merchant.username
                elif order.franchisee_id:
                    # 从批量查询的缓存中获取（避免N+1查询）
                    merchant_name = franchisee_cache.get(
                        order.franchisee_id, f"加盟商ID:{order.franchisee_id}"
                    )

                # 将订单数据转换为字典，避免DetachedInstanceError
                order_data = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "customer_phone": order.customer_phone,
                    "customer_address": order.customer_address,
                    "product_name": order.product_name,
                    "size": order.size,
                    "style_name": order.style_name,
                    "status": order.status,
                    "price": order.price,
                    "commission": order.commission,
                    "payment_time": order.payment_time,
                    "transaction_id": order.transaction_id,
                    "created_at": order.created_at,
                    "completed_at": order.completed_at,
                    "merchant_name": merchant_name,
                    "source_type": order.source_type,
                    "external_platform": order.external_platform,
                    "external_order_number": order.external_order_number,
                    "shipping_info": order.shipping_info,
                    "logistics_info": order.logistics_info,
                    "original_image": order.original_image,
                    "final_image": order.final_image,
                    "hd_image": order.hd_image,
                    "printer_send_status": order.printer_send_status,
                    "franchisee_id": order.franchisee_id,
                    "customer_note": order.customer_note,
                }
                all_orders_data.append(order_data)

            offset += batch_size

            if len(orders_batch) < batch_size:
                break

        logger.info(f"📦 预查询完成: 找到 {len(all_orders_data)} 条订单")

        # 使用生成器函数实现流式导出
        def generate_csv():
            """生成CSV内容的生成器 - 返回字节串"""
            # 写入CSV头部（使用utf-8-sig编码，自动添加BOM，确保Excel正确识别UTF-8）
            headers = [
                "订单ID",
                "订单号",
                "客户姓名",
                "客户手机",
                "客户地址",
                "产品名称",
                "尺寸",
                "艺术风格",
                "订单状态",
                "订单价格",
                "佣金金额",
                "支付时间",
                "交易号",
                "下单时间",
                "完成时间",
                "商家",
                "来源类型",
                "外部平台",
                "外部订单号",
                "物流信息",
                "快递公司",
                "快递单号",
                "物流状态",
                "原图路径",
                "成品图路径",
                "高清图路径",
                "冲印发送状态",
                "加盟商ID",
                "客户备注",
            ]

            # 输出头部（使用utf-8-sig编码，自动添加BOM）
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            header_content = output.getvalue()
            output.close()
            # utf-8-sig会自动添加BOM，确保Excel正确识别UTF-8
            header_bytes = header_content.encode("utf-8-sig")
            logger.info(f"📤 导出头部: {len(header_bytes)} 字节")
            yield header_bytes

            # 批量处理订单（分批处理，避免内存溢出）
            export_batch_size = 1000
            batch_num = 0

            for i in range(0, len(all_orders_data), export_batch_size):
                orders_batch = all_orders_data[i : i + export_batch_size]
                batch_num += 1

                logger.info(f"📦 导出批次 {batch_num}: 处理 {len(orders_batch)} 条订单")

                # 为这一批创建新的StringIO
                batch_output = io.StringIO()
                batch_writer = csv.writer(batch_output)

                # 处理这一批订单
                for order_data in orders_batch:
                    # 解析物流信息
                    logistics_info = None
                    logistics_company = ""
                    tracking_number = ""
                    logistics_status = ""

                    if order_data["logistics_info"]:
                        try:
                            logistics_info = json.loads(order_data["logistics_info"])
                            logistics_company = logistics_info.get("company", "")
                            tracking_number = logistics_info.get("tracking_number", "")
                            logistics_status = logistics_info.get("status", "")
                        except Exception:
                            pass

                    # 获取商家信息（已在请求上下文中预先加载）
                    merchant_name = order_data["merchant_name"]

                    # 状态显示
                    status_display = status_map.get(
                        order_data["status"], order_data["status"] or "未知"
                    )

                    # 解析客户地址
                    customer_address_display = order_data["customer_address"] or ""
                    if not customer_address_display and order_data["shipping_info"]:
                        customer_address_display = parse_address(order_data["shipping_info"])

                    # 来源类型映射
                    source_type_display = source_type_map.get(
                        order_data["source_type"], order_data["source_type"] or "未知"
                    )

                    # 写入一行数据
                    row = [
                        order_data["id"],
                        order_data["order_number"],
                        order_data["customer_name"],
                        order_data["customer_phone"] or "",
                        customer_address_display,
                        order_data["product_name"] or "",
                        order_data["size"] or "",
                        order_data["style_name"] or "",
                        status_display,
                        order_data["price"] or 0,
                        order_data["commission"] or 0,
                        (
                            order_data["payment_time"].strftime("%Y-%m-%d %H:%M:%S")
                            if order_data["payment_time"]
                            else ""
                        ),
                        order_data["transaction_id"] or "",
                        (
                            order_data["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                            if order_data["created_at"]
                            else ""
                        ),
                        (
                            order_data["completed_at"].strftime("%Y-%m-%d %H:%M:%S")
                            if order_data["completed_at"]
                            else ""
                        ),
                        merchant_name,
                        source_type_display,
                        order_data["external_platform"] or "",
                        order_data["external_order_number"] or "",
                        order_data["shipping_info"] or "",
                        logistics_company,
                        tracking_number,
                        logistics_status,
                        order_data["original_image"] or "",
                        order_data["final_image"] or "",
                        order_data["hd_image"] or "",
                        order_data["printer_send_status"] or "",
                        order_data["franchisee_id"] or "",
                        order_data["customer_note"] or "",
                    ]
                    batch_writer.writerow(row)

                # 输出这一批的数据（编码为UTF-8）
                batch_content = batch_output.getvalue()
                batch_output.close()
                if batch_content:
                    encoded_content = batch_content.encode("utf-8-sig")
                    logger.info(
                        f"📤 导出批次 {batch_num}: 输出 {len(encoded_content)} 字节数据，包含 {len(orders_batch)} 条订单"
                    )
                    yield encoded_content
                else:
                    logger.warning(
                        f"⚠️  导出批次 {batch_num}: 批次内容为空，订单数: {len(orders_batch)}"
                    )

            logger.info(f"✅ 导出完成: 共处理 {batch_num} 个批次")

        # 创建流式响应（使用Response类以支持生成器）
        # Flask的Response可以直接处理生成器，生成器应该返回字节串
        response = Response(
            generate_csv(),
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename=orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            },
        )

        logger.info("✅ 导出响应已创建，开始流式传输")
        return response

    except Exception as e:
        logger.error(f"导出订单数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"导出失败: {str(e)}"}), 500


@admin_orders_list_bp.route("/admin/orders/export/json", methods=["GET"])
@login_required
@admin_required
def export_orders_json():
    """导出所有订单数据为JSON格式（流式导出，优化内存使用）"""
    try:
        models = get_models(["Order", "FranchiseeAccount", "db"])
        if not models:
            return jsonify({"success": False, "message": "系统未初始化"}), 500

        Order = models["Order"]
        FranchiseeAccount = models["FranchiseeAccount"]
        db = models["db"]

        # 获取筛选参数
        status = request.args.get("status", "")
        franchisee_id = request.args.get("franchisee_id", "")
        order_mode = request.args.get("order_mode", "")
        search = request.args.get("search", "").strip()

        # 构建查询
        query = Order.query.filter(Order.status != "unpaid")

        if status and status != "unpaid":
            query = query.filter(Order.status == status)
        elif status == "unpaid":
            query = Order.query.filter(Order.status == "unpaid")

        if franchisee_id:
            query = query.filter(Order.franchisee_id == int(franchisee_id))

        if order_mode:
            query = query.filter(Order.order_mode == order_mode)

        if search:
            from sqlalchemy import or_

            query = query.filter(
                or_(
                    Order.order_number.like(f"%{search}%"),
                    Order.customer_name.like(f"%{search}%"),
                    Order.customer_phone.like(f"%{search}%"),
                )
            )

        # 获取总数（用于限制）
        total_count = query.count()
        max_export_limit = 50000  # 最多导出5万条

        if total_count > max_export_limit:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"订单数量过多（{total_count}条），超过导出限制（{max_export_limit}条）。请使用筛选条件缩小范围。",
                    }
                ),
                400,
            )

        # 使用生成器函数实现流式导出
        def generate_json():
            """生成JSON内容的生成器"""
            yield '{"orders": [\n'

            batch_size = 1000
            offset = 0
            is_first = True
            # 优化N+1查询：预先批量查询所有需要的加盟商信息
            franchisee_cache = {}
            all_franchisee_ids = set()

            # 先收集所有订单的franchisee_id
            temp_offset = 0
            while True:
                temp_batch = (
                    query.order_by(Order.created_at.desc())
                    .offset(temp_offset)
                    .limit(batch_size)
                    .all()
                )
                if not temp_batch:
                    break
                for order in temp_batch:
                    if order.franchisee_id:
                        all_franchisee_ids.add(order.franchisee_id)
                temp_offset += batch_size
                if len(temp_batch) < batch_size:
                    break

            # 批量查询所有加盟商
            if all_franchisee_ids:
                all_franchisees = FranchiseeAccount.query.filter(
                    FranchiseeAccount.id.in_(list(all_franchisee_ids))
                ).all()
                for franchisee in all_franchisees:
                    franchisee_cache[franchisee.id] = f"加盟商:{franchisee.company_name}"

            # 重置offset
            offset = 0

            while True:
                # 分批查询订单
                orders_batch = (
                    query.order_by(Order.created_at.desc()).offset(offset).limit(batch_size).all()
                )

                if not orders_batch:
                    break

                # 处理这一批订单
                for order in orders_batch:
                    if not is_first:
                        yield ",\n"
                    is_first = False

                    # 获取商家信息（从批量查询的缓存中获取，避免N+1查询）
                    merchant_name = ""
                    if hasattr(order, "merchant") and order.merchant:
                        merchant_name = order.merchant.username
                    elif order.franchisee_id:
                        merchant_name = franchisee_cache.get(
                            order.franchisee_id, f"加盟商ID:{order.franchisee_id}"
                        )

                    # 解析物流信息
                    logistics_info = None
                    if order.logistics_info:
                        try:
                            logistics_info = json.loads(order.logistics_info)
                        except Exception:
                            logistics_info = order.logistics_info

                    order_dict = {
                        "id": order.id,
                        "order_number": order.order_number,
                        "customer_name": order.customer_name,
                        "customer_phone": order.customer_phone,
                        "customer_address": order.customer_address,
                        "product_name": order.product_name,
                        "size": order.size,
                        "style_name": order.style_name,
                        "status": order.status,
                        "price": float(order.price) if order.price else 0,
                        "commission": float(order.commission) if order.commission else 0,
                        "payment_time": (
                            order.payment_time.isoformat() if order.payment_time else None
                        ),
                        "transaction_id": order.transaction_id,
                        "created_at": order.created_at.isoformat() if order.created_at else None,
                        "completed_at": (
                            order.completed_at.isoformat() if order.completed_at else None
                        ),
                        "merchant_name": merchant_name,
                        "source_type": order.source_type,
                        "external_platform": order.external_platform,
                        "external_order_number": order.external_order_number,
                        "logistics_info": logistics_info,
                        "original_image": order.original_image,
                        "final_image": order.final_image,
                        "hd_image": order.hd_image,
                        "printer_send_status": order.printer_send_status,
                        "franchisee_id": order.franchisee_id,
                        "customer_note": order.customer_note,
                    }
                    yield json.dumps(order_dict, ensure_ascii=False)

                # 如果这一批少于batch_size，说明已经处理完所有数据
                if len(orders_batch) < batch_size:
                    break

                offset += batch_size

            yield "\n]}"

        # 创建流式响应
        response = make_response(generate_json())
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Content-Disposition"] = (
            f'attachment; filename=orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

        return response

    except Exception as e:
        logger.error(f"导出订单数据失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": f"导出失败: {str(e)}"}), 500
