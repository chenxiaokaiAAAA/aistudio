# -*- coding: utf-8 -*-
"""
美图API任务管理模块
"""

import json
import logging
import sys
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.utils.decorators import admin_required
from app.utils.performance_optimizer import ResponseOptimizer
from app.utils.type_hints import FlaskResponse, JsonDict

from .utils import get_table_columns

# 创建子蓝图（不设置url_prefix，使用主蓝图的前缀）
bp = Blueprint("meitu_tasks", __name__)


@bp.route("/tasks")
@login_required
@admin_required
def meitu_tasks():
    """美颜任务管理页面"""
    return render_template("admin/meitu_tasks.html")


@bp.route("/api/tasks", methods=["GET"])
@login_required
def get_meitu_tasks() -> FlaskResponse:
    """
    获取美颜任务列表（API调用记录）

    Returns:
        FlaskResponse: JSON响应，包含任务列表和分页信息
    """
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        MeituAPICallLog = test_server_module.MeituAPICallLog

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        order_number = request.args.get("order_number", "").strip()
        status = request.args.get("status", "").strip()
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()

        # 构建查询
        query = MeituAPICallLog.query

        # 筛选条件
        if order_number:
            query = query.filter(MeituAPICallLog.order_number.like(f"%{order_number}%"))

        if status:
            query = query.filter(MeituAPICallLog.status == status)

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(MeituAPICallLog.created_at >= start_dt)
            except Exception:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(MeituAPICallLog.created_at < end_dt)
            except Exception:
                pass

        # 排序：最新的在前
        query = query.order_by(MeituAPICallLog.created_at.desc())

        # 尝试使用ORM查询，如果失败（字段不存在），则使用原始SQL
        try:
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            tasks = pagination.items
        except Exception as orm_error:
            # ORM查询失败，可能是msg_id字段不存在，使用原始SQL查询
            if "no such column" in str(orm_error).lower() and "msg_id" in str(orm_error):
                logger.warning("msg_id 字段不存在，使用兼容查询模式（请重启服务以执行数据库迁移）")
                try:
                    # 使用原始SQL查询，排除msg_id字段
                    offset = (page - 1) * per_page

                    # 构建WHERE子句
                    where_clauses = []
                    params = {"limit": per_page, "offset": offset}

                    if order_number:
                        where_clauses.append("order_number LIKE :order_number")
                        params["order_number"] = f"%{order_number}%"
                    if status:
                        where_clauses.append("status = :status")
                        params["status"] = status
                    if start_date:
                        try:
                            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                            where_clauses.append("DATE(created_at) >= :start_date")
                            params["start_date"] = start_date
                        except Exception:
                            pass
                    if end_date:
                        try:
                            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                            where_clauses.append("created_at < :end_date")
                            params["end_date"] = end_dt
                        except Exception:
                            pass

                    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

                    # 查询数据
                    sql = """
                        SELECT id, order_id, order_number, product_id, preset_id,
                               request_url, request_params, response_status, response_data,
                               result_image_url, result_image_path, error_message,
                               duration_ms, status, created_at
                        FROM meitu_api_call_log
                        {where_sql}
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    result = db.session.execute(db.text(sql), params)
                    rows = result.fetchall()

                    # 创建临时任务对象
                    class TempTask:
                        def __init__(self, row):
                            self.id = row[0]
                            self.order_id = row[1]
                            self.order_number = row[2]
                            self.product_id = row[3]
                            self.preset_id = row[4]
                            self.request_url = row[5]
                            self.request_params = row[6]
                            self.response_status = row[7]
                            self.response_data = row[8]
                            self.result_image_url = row[9]
                            self.result_image_path = row[10]
                            self.error_message = row[11]
                            self.duration_ms = row[12]
                            self.status = row[13]
                            self.created_at = row[14]
                            self.msg_id = None  # 临时设置为None

                    tasks = [TempTask(row) for row in rows]

                    # 查询总数
                    count_sql = f"SELECT COUNT(*) FROM meitu_api_call_log {where_sql}"
                    count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
                    count_result = db.session.execute(db.text(count_sql), count_params)
                    total = count_result.fetchone()[0]

                    # 创建分页对象
                    class SimplePagination:
                        def __init__(self, items, total, page, per_page):
                            self.items = items
                            self.total = total
                            self.page = page
                            self.per_page = per_page
                            self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1

                    pagination = SimplePagination(tasks, total, page, per_page)
                except Exception as sql_error:
                    logger.error(f"兼容查询模式也失败: {str(sql_error)}")
                    raise orm_error
            else:
                # 其他错误，直接抛出
                raise orm_error

        task_list = []
        for task in tasks:
            # 检查任务是否有msg_id（优先从msg_id字段，否则从response_data中提取）
            msg_id_value = getattr(task, "msg_id", None)
            has_msg_id = bool(msg_id_value)

            # 如果msg_id字段为空，尝试从response_data中提取
            if not has_msg_id and task.response_data:
                try:
                    response_data = (
                        json.loads(task.response_data)
                        if isinstance(task.response_data, str)
                        else task.response_data
                    )
                    if isinstance(response_data, dict):
                        msg_id_value = response_data.get("msg_id")
                        has_msg_id = bool(msg_id_value)
                    elif isinstance(response_data, str):
                        # 如果是字符串，尝试解析
                        try:
                            parsed = json.loads(response_data)
                            msg_id_value = (
                                parsed.get("msg_id") if isinstance(parsed, dict) else None
                            )
                            has_msg_id = bool(msg_id_value)
                        except Exception:
                            pass
                except Exception:
                    pass

            task_list.append(
                {
                    "id": task.id,
                    "order_id": task.order_id,
                    "order_number": task.order_number,
                    "product_id": task.product_id,
                    "preset_id": task.preset_id,
                    "request_url": task.request_url,
                    "response_status": task.response_status,
                    "result_image_url": task.result_image_url,
                    "result_image_path": task.result_image_path,
                    "error_message": task.error_message,
                    "duration_ms": task.duration_ms,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "request_params": task.request_params,
                    "response_data": task.response_data,
                    "has_msg_id": has_msg_id,  # 标记是否有msg_id，用于前端判断是否显示查询按钮
                }
            )

        # 使用响应优化（添加缓存头，1分钟缓存，任务数据变化频繁）
        response_data: JsonDict = {
            "status": "success",
            "data": {
                "tasks": task_list,
                "total": pagination.total,
                "pages": pagination.pages,
                "page": page,
                "per_page": per_page,
            },
        }
        return ResponseOptimizer.optimize_json_response(response_data, max_age=60)

    except Exception as e:
        logger.info(f"获取美颜任务列表失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务列表失败: {str(e)}"}), 500


@bp.route("/api/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_meitu_task_detail(task_id):
    """获取美颜任务详情"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        MeituAPICallLog = test_server_module.MeituAPICallLog
        Order = test_server_module.Order

        task = MeituAPICallLog.query.get(task_id)
        if not task:
            return jsonify({"status": "error", "message": "任务不存在"}), 404

        # 获取订单信息
        order = None
        if task.order_id:
            order = Order.query.get(task.order_id)

        # 检查任务是否有msg_id（优先从msg_id字段，否则从response_data中提取）
        msg_id_value = getattr(task, "msg_id", None)
        has_msg_id = bool(msg_id_value)

        # 如果msg_id字段为空，尝试从response_data中提取
        if not has_msg_id and task.response_data:
            try:
                response_data = (
                    json.loads(task.response_data)
                    if isinstance(task.response_data, str)
                    else task.response_data
                )
                if isinstance(response_data, dict):
                    msg_id_value = response_data.get("msg_id")
                    has_msg_id = bool(msg_id_value)
            except Exception:
                pass

        task_data = {
            "id": task.id,
            "order_id": task.order_id,
            "order_number": task.order_number,
            "order": (
                {
                    "id": order.id if order else None,
                    "order_number": order.order_number if order else None,
                    "customer_name": order.customer_name if order else None,
                    "product_name": order.product_name if order else None,
                    "status": order.status if order else None,
                }
                if order
                else None
            ),
            "product_id": task.product_id,
            "preset_id": task.preset_id,
            "request_url": task.request_url,
            "request_params": task.request_params,
            "response_status": task.response_status,
            "response_data": task.response_data,
            "msg_id": msg_id_value,  # 直接返回msg_id字段
            "has_msg_id": has_msg_id,  # 标记是否有msg_id，用于前端判断是否显示查询按钮
            "result_image_url": task.result_image_url,
            "result_image_path": task.result_image_path,
            "error_message": task.error_message,
            "duration_ms": task.duration_ms,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

        return jsonify({"status": "success", "data": task_data})

    except Exception as e:
        logger.info(f"获取美颜任务详情失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": f"获取任务详情失败: {str(e)}"}), 500


@bp.route("/api/tasks/<int:task_id>/recheck", methods=["POST"])
@login_required
def recheck_meitu_task_result(task_id):
    """重新查询美图API任务结果（通过msg_id查询）"""
    try:
        if current_user.role not in ["admin", "operator"]:
            return jsonify({"status": "error", "message": "权限不足"}), 403

        if "test_server" not in sys.modules:
            return jsonify({"status": "error", "message": "数据库未初始化"}), 500

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        MeituAPICallLog = test_server_module.MeituAPICallLog
        MeituAPIConfig = test_server_module.MeituAPIConfig

        # 获取任务
        task = MeituAPICallLog.query.get(task_id)
        if not task:
            return jsonify({"status": "error", "message": "任务不存在"}), 404

        # 优先从msg_id字段获取（如果存在），否则从response_data中提取
        msg_id = getattr(task, "msg_id", None)
        if not msg_id and task.response_data:
            try:
                response_data = (
                    json.loads(task.response_data)
                    if isinstance(task.response_data, str)
                    else task.response_data
                )
                msg_id = response_data.get("msg_id")
                # 如果从response_data中提取到了msg_id，更新到msg_id字段（如果字段存在）
                if msg_id and hasattr(task, "msg_id"):
                    task.msg_id = msg_id
                    db.session.commit()
            except Exception:
                pass

        if not msg_id:
            # 检查是否是原始调用失败（没有返回msg_id）
            if task.response_status and task.response_status != 200:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"原始调用失败（HTTP {task.response_status}），没有返回msg_id，无法查询结果。请检查原始调用的错误信息。",
                        }
                    ),
                    400,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "任务没有msg_id，无法查询结果。可能是原始调用失败或响应格式不正确。",
                        }
                    ),
                    400,
                )

        # 获取API配置（使用原始SQL避免字段不存在的问题）
        config = None
        try:
            # 先检查表结构
            columns = get_table_columns(db, "meitu_api_config")

            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ["api_key", "api_secret", "api_base_url", "api_endpoint"]
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            logger.warning(f"使用SQLAlchemy查询配置失败，尝试使用原始SQL: {str(e)}")
            # 使用原始SQL查询
            result = db.session.execute(
                db.text("SELECT id FROM meitu_api_config WHERE is_active = 1 LIMIT 1")
            ).fetchone()
            if result:
                config_id = result[0] if isinstance(result, tuple) else result._mapping["id"]
                # 构建SELECT语句，只选择存在的列
                select_cols = ["id"]
                if "api_key" in columns:
                    select_cols.append("api_key")
                elif "app_id" in columns:
                    select_cols.append("app_id AS api_key")
                else:
                    select_cols.append("'' AS api_key")

                if "api_secret" in columns:
                    select_cols.append("api_secret")
                elif "secret_id" in columns:
                    select_cols.append("secret_id AS api_secret")
                else:
                    select_cols.append("'' AS api_secret")

                # 添加其他可能存在的列
                for col in ["api_base_url", "api_endpoint", "repost_url"]:
                    if col in columns:
                        select_cols.append(col)
                    elif col == "api_endpoint":
                        select_cols.append("'/openapi/realphotolocal_async' AS api_endpoint")
                    elif col == "api_base_url":
                        select_cols.append("'https://api.yunxiu.meitu.com' AS api_base_url")

                sql = (
                    f"SELECT {', '.join(select_cols)} FROM meitu_api_config WHERE id = {config_id}"
                )
                result = db.session.execute(db.text(sql)).fetchone()

                if result:
                    result_dict = (
                        dict(result._mapping)
                        if hasattr(result, "_mapping")
                        else dict(
                            zip(
                                [c.split(" AS ")[-1] if " AS " in c else c for c in select_cols],
                                result,
                            )
                        )
                    )

                    class SimpleConfig:
                        def __init__(self, data):
                            self.id = data.get("id")
                            self.api_key = data.get("api_key", "")
                            self.api_secret = data.get("api_secret", "")
                            self.api_base_url = data.get(
                                "api_base_url", "https://api.yunxiu.meitu.com"
                            )
                            self.api_endpoint = data.get(
                                "api_endpoint", "/openapi/realphotolocal_async"
                            )
                            self.repost_url = data.get("repost_url")

                    config = SimpleConfig(result_dict)

        if not config:
            return jsonify({"status": "error", "message": "未找到API配置"}), 500

        # 优先从原始调用的请求参数中获取API密钥（确保使用相同的密钥）
        api_key = None
        api_secret = None
        api_base_url = getattr(config, "api_base_url", None) or "https://api.yunxiu.meitu.com"

        if task.request_params:
            try:
                original_params = (
                    json.loads(task.request_params)
                    if isinstance(task.request_params, str)
                    else task.request_params
                )
                original_api_key = original_params.get("api_key", "")
                original_api_secret = original_params.get("api_secret", "")
                logger.info(
                    f"📋 原始调用请求参数中的API密钥: api_key={original_api_key}, api_secret={original_api_secret[:10] if original_api_secret else 'None'}..."
                )

                if original_api_key and original_api_secret:
                    api_key = original_api_key
                    api_secret = original_api_secret
                    logger.info("✅ 使用原始调用请求参数中的API密钥")
                else:
                    logger.warning("原始调用请求参数中没有API密钥或密钥为空")
            except Exception as e:
                logger.warning(f"解析原始调用请求参数失败: {str(e)}")
                import traceback

                traceback.print_exc()

        # 如果原始调用中没有，使用配置中的密钥
        if not api_key or not api_secret:
            config_api_key = getattr(config, "api_key", None) or getattr(config, "app_id", "")
            config_api_secret = getattr(config, "api_secret", None) or getattr(
                config, "secret_id", ""
            )
            logger.info(
                f"📋 配置中的API密钥: api_key={config_api_key}, api_secret={config_api_secret[:10] if config_api_secret else 'None'}..."
            )

            api_key = config_api_key
            api_secret = config_api_secret
            logger.warning("使用配置中的API密钥")

        # 验证API密钥是否获取成功
        if not api_key or not api_secret:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"API密钥获取失败: api_key={bool(api_key)}, api_secret={bool(api_secret)}。请检查配置或原始调用记录。",
                    }
                ),
                500,
            )

        logger.info(f"🔑 最终使用的API密钥: api_key={api_key}, api_secret={api_secret[:10]}...")

        # 对比原始调用和查询使用的API密钥是否一致
        if task.request_params:
            try:
                original_params = (
                    json.loads(task.request_params)
                    if isinstance(task.request_params, str)
                    else task.request_params
                )
                original_api_key = original_params.get("api_key", "")
                if original_api_key and original_api_key != api_key:
                    logger.warning("⚠️ ⚠️ 警告：查询使用的API密钥与原始调用不一致！")
                    logger.info(f"   原始调用使用的API密钥: {original_api_key}")
                    logger.info(f"   查询使用的API密钥: {api_key}")
                    logger.info("   这可能导致查询失败！")
            except Exception:
                pass

        # 查询结果（根据文档：POST https://api.yunxiu.meitu.com/openapi/query）
        query_url = f"{api_base_url.rstrip('/')}/openapi/query"

        query_data = {"api_key": api_key, "api_secret": api_secret, "msg_id": msg_id}

        logger.info(f"🔄 查询美图API结果，msg_id: {msg_id}")
        logger.info(f"📤 查询URL: {query_url}")
        logger.info(
            f"📤 查询参数: {json.dumps({**query_data, 'api_secret': '***'}, ensure_ascii=False)}"
        )  # 隐藏密钥

        # 添加请求头（确保Content-Type正确）
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            query_url,
            json=query_data,
            headers=headers,
            timeout=30,
            proxies={"http": None, "https": None},
        )

        logger.info(f"📥 响应状态码: {response.status_code}")
        logger.info(f"📥 响应内容: {response.text[:500]}")

        if response.status_code == 200:
            result = response.json()

            # 根据文档，响应格式：
            # {
            #   "code": 0,
            #   "data": {
            #     "msg_id": "...",
            #     "media_data": "https://..."  // 结果图片URL
            #   },
            #   "message": "success",
            #   "request_id": "..."
            # }

            if result.get("code") == 0 and "data" in result:
                data = result.get("data")
                result_image_url = data.get("media_data")

                if result_image_url:
                    # 更新任务状态和结果
                    task.status = "success"
                    task.result_image_url = result_image_url
                    task.response_data = json.dumps(result, ensure_ascii=False)

                    # 尝试下载图片到本地
                    from app.services.meitu_api_service import download_result_image

                    result_image_path = download_result_image(result_image_url, task.order_number)
                    if result_image_path:
                        task.result_image_path = result_image_path

                    db.session.commit()

                    logger.info(f"✅ 查询成功，结果图片URL: {result_image_url}")
                    if result_image_path:
                        logger.info(f"✅ 图片已下载到本地: {result_image_path}")

                    return jsonify(
                        {
                            "status": "success",
                            "message": "查询成功",
                            "data": {
                                "result_image_url": result_image_url,
                                "result_image_path": result_image_path,
                                "response_data": result,
                            },
                        }
                    )
                else:
                    # 可能还在处理中
                    task.response_data = json.dumps(result, ensure_ascii=False)
                    db.session.commit()
                    return jsonify(
                        {
                            "status": "pending",
                            "message": "任务仍在处理中",
                            "data": {"response_data": result},
                        }
                    )
            elif result.get("code") == 90002:
                # GATEWAY_AUTHORIZED_ERROR - 认证失败
                error_msg = f"API认证失败: {result.get('message', 'GATEWAY_AUTHORIZED_ERROR')}"
                logger.error(error_msg)
                logger.info(f"   使用的API密钥: {api_key}")
                logger.info(f"   使用的API密钥长度: {len(api_key) if api_key else 0}")
                logger.info(f"   使用的API密钥长度: {len(api_secret) if api_secret else 0}")

                # 检查是否使用了原始调用的密钥
                if task.request_params:
                    try:
                        original_params = (
                            json.loads(task.request_params)
                            if isinstance(task.request_params, str)
                            else task.request_params
                        )
                        original_api_key = original_params.get("api_key", "")
                        if original_api_key == api_key:
                            logger.info("   ✅ 已使用原始调用时的API密钥")
                        else:
                            logger.info(f"   ⚠️ 原始调用使用的API密钥: {original_api_key}")
                    except Exception:
                        pass

                task.status = "failed"
                task.error_message = error_msg
                task.response_data = json.dumps(result, ensure_ascii=False)
                db.session.commit()
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": error_msg
                            + "。请检查API密钥配置是否正确，确保查询时使用的密钥与原始调用时使用的密钥一致。",
                            "data": {
                                "response_data": result,
                                "hint": "查询接口需要使用与原始调用相同的API密钥。如果仍然失败，可能是API密钥已过期或无效。",
                            },
                        }
                    ),
                    400,
                )
            else:
                error_msg = result.get("message", "查询失败")
                task.status = "failed"
                task.error_message = error_msg
                task.response_data = json.dumps(result, ensure_ascii=False)
                db.session.commit()
                return (
                    jsonify(
                        {"status": "error", "message": error_msg, "data": {"response_data": result}}
                    ),
                    400,
                )
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            task.status = "failed"
            task.error_message = error_msg
            db.session.commit()
            return jsonify({"status": "error", "message": error_msg}), 400

    except Exception as e:
        logger.info(f"重新查询美图API任务结果失败: {str(e)}")
        import traceback

        traceback.print_exc()
        if "db" in locals():
            db.session.rollback()
        return jsonify({"status": "error", "message": f"查询失败: {str(e)}"}), 500
