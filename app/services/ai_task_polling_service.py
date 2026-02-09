# -*- coding: utf-8 -*-
"""
AI任务状态自动轮询服务
定期检查处理中的任务并更新状态
"""

import logging

logger = logging.getLogger(__name__)
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta

import requests


def poll_meitu_api_tasks():
    """轮询美图API任务状态"""
    try:
        import sys

        if "test_server" not in sys.modules:
            logger.warning("[美图轮询] test_server模块未加载，无法轮询")
            return 0

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        MeituAPICallLog = test_server_module.MeituAPICallLog
        MeituAPIConfig = test_server_module.MeituAPIConfig

        if not db or not MeituAPICallLog:
            logger.warning("[美图轮询] 数据库或模型未初始化")
            return 0

        with test_server_module.app.app_context():
            # 查找所有pending状态的美图API任务
            # 注意：不限制创建时间，因为美图API可能很快完成，我们需要及时轮询
            # 但为了避免频繁查询刚创建的任务，只轮询创建时间超过30秒的任务
            cutoff_time = datetime.now() - timedelta(seconds=30)

            # 先查询所有pending任务（用于调试）
            all_pending = MeituAPICallLog.query.filter(MeituAPICallLog.status == "pending").all()

            # 再查询满足时间条件的任务
            pending_tasks = MeituAPICallLog.query.filter(
                MeituAPICallLog.status == "pending", MeituAPICallLog.created_at <= cutoff_time
            ).all()

            # 只在有待处理任务时才输出调试信息（避免无任务时产生过多日志）
            if pending_tasks:
                logger.info(
                    f"🔍 [美图轮询] 发现 {len(all_pending)} 个pending任务，其中 {len(pending_tasks)} 个满足轮询条件（创建时间超过30秒）"
                )
                for task in pending_tasks[:3]:  # 只显示前3个待轮询任务的详情
                    age_seconds = (
                        (datetime.now() - task.created_at).total_seconds() if task.created_at else 0
                    )
                    msg_id = getattr(task, "msg_id", None)
                    if not msg_id and task.response_data:
                        try:
                            response_data = (
                                json.loads(task.response_data)
                                if isinstance(task.response_data, str)
                                else task.response_data
                            )
                            if isinstance(response_data, dict):
                                msg_id = response_data.get("msg_id")
                        except Exception:
                            pass
                    msg_id_str = msg_id[:20] if msg_id else "无"
                    logger.info(
                        f"   - 任务 {task.id}: 创建于 {age_seconds:.1f}秒前, msg_id={msg_id_str}, 状态={task.status}"
                    )

            if not pending_tasks:
                return 0

            logger.info(f"🔄 [美图轮询] 开始轮询 {len(pending_tasks)} 个待处理任务...")

            updated_count = 0

            for task in pending_tasks:
                try:
                    # 获取msg_id（优先从msg_id字段，否则从response_data中提取）
                    msg_id = getattr(task, "msg_id", None)
                    if not msg_id and task.response_data:
                        try:
                            response_data = (
                                json.loads(task.response_data)
                                if isinstance(task.response_data, str)
                                else task.response_data
                            )
                            if isinstance(response_data, dict):
                                msg_id = response_data.get("msg_id")
                        except Exception:
                            pass

                    if not msg_id:
                        logger.warning("[美图轮询] 任务 {task.id} 没有msg_id，跳过轮询")
                        continue

                    logger.info(f"🔄 [美图轮询] 开始轮询任务 {task.id}，msg_id={msg_id}")

                    # 获取API配置（从任务关联的配置或默认配置）
                    config = None
                    if task.preset_id:
                        # 尝试从预设ID关联的配置获取（如果有的话）
                        config = MeituAPIConfig.query.filter_by(is_active=True).first()

                    if not config:
                        config = MeituAPIConfig.query.filter_by(is_active=True).first()

                    if not config:
                        continue

                    # 从原始调用请求参数中获取API密钥（确保使用相同的密钥）
                    api_key = None
                    api_secret = None
                    api_base_url = (
                        getattr(config, "api_base_url", None) or "https://api.yunxiu.meitu.com"
                    )

                    if task.request_params:
                        try:
                            original_params = (
                                json.loads(task.request_params)
                                if isinstance(task.request_params, str)
                                else task.request_params
                            )
                            original_api_key = original_params.get("api_key", "")
                            original_api_secret = original_params.get("api_secret", "")
                            if original_api_key and original_api_secret:
                                api_key = original_api_key
                                api_secret = original_api_secret
                        except Exception:
                            pass

                    # 如果原始调用中没有，使用配置中的密钥
                    if not api_key or not api_secret:
                        api_key = getattr(config, "api_key", None) or getattr(config, "app_id", "")
                        api_secret = getattr(config, "api_secret", None) or getattr(
                            config, "secret_id", ""
                        )

                    if not api_key or not api_secret:
                        continue

                    # 查询美图API结果
                    query_url = f"{api_base_url.rstrip('/')}/openapi/query"
                    query_data = {"api_key": api_key, "api_secret": api_secret, "msg_id": msg_id}

                    headers = {"Content-Type": "application/json"}

                    # 禁用代理（国内服务商）
                    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
                    has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
                    is_known_domestic_domain = "yunxiu.meitu.com" in api_base_url.lower()

                    if is_known_domestic_domain:
                        proxies = {"http": None, "https": None}
                    else:
                        proxies = None

                    logger.info(f"📤 [美图轮询] 查询任务 {task.id}，URL: {query_url}")
                    response = requests.post(
                        query_url, json=query_data, headers=headers, timeout=30, proxies=proxies
                    )
                    logger.info(
                        f"📥 [美图轮询] 任务 {task.id} 查询响应: HTTP {response.status_code}"
                    )

                    if response.status_code == 200:
                        result = response.json()
                        logger.info(
                            f"📋 [美图轮询] 任务 {task.id} 查询响应内容: {json.dumps(result, ensure_ascii=False)[:300]}"
                        )

                        # 根据美图API文档，查询接口响应格式：
                        # {
                        #   "code": 0,
                        #   "data": {
                        #     "status": "success" 或 "processing",
                        #     "media_data": "..." 或 "result_url": "..." 或 "result_image": "..."
                        #   },
                        #   "message": "..."
                        # }
                        if result.get("code") == 0 and "data" in result:
                            data = result.get("data", {})

                            # 根据手动查询代码，美图API查询接口直接返回media_data（没有status字段）
                            # 如果data中有media_data，说明任务已完成
                            result_url = data.get("media_data")

                            # 如果没有media_data，检查是否有status字段（兼容不同格式）
                            if not result_url:
                                status = data.get("status", "")
                                logger.info(f"📊 [美图轮询] 任务 {task.id} 解析状态: {status}")

                                if status == "success":
                                    # 从其他字段获取结果URL
                                    result_url = (
                                        data.get("result_url")
                                        or data.get("result_image")
                                        or data.get("url")
                                    )

                            if result_url:
                                logger.info(
                                    f"📊 [美图轮询] 任务 {task.id} 找到结果URL: {result_url}"
                                )
                                task.status = "success"
                                task.result_image_url = result_url
                                # 更新response_data为完整的查询响应
                                if task.response_data:
                                    try:
                                        original_response = (
                                            json.loads(task.response_data)
                                            if isinstance(task.response_data, str)
                                            else task.response_data
                                        )
                                        if isinstance(original_response, dict):
                                            original_response["query_response"] = result
                                            task.response_data = json.dumps(
                                                original_response, ensure_ascii=False
                                            )
                                        else:
                                            task.response_data = json.dumps(
                                                result, ensure_ascii=False
                                            )
                                    except Exception:
                                        task.response_data = json.dumps(result, ensure_ascii=False)
                                else:
                                    task.response_data = json.dumps(result, ensure_ascii=False)

                                # 计算从任务创建到完成的总耗时（精确记录美图API处理时间）
                                if task.created_at:
                                    now = datetime.now()
                                    total_duration_seconds = (now - task.created_at).total_seconds()
                                    total_duration_ms = int(total_duration_seconds * 1000)

                                    # 更新duration_ms为总处理时间（从提交到完成）
                                    task.duration_ms = total_duration_ms

                                    logger.info(
                                        f"⏱️ [美图轮询] 任务 {task.id} 总处理时间: {total_duration_ms}ms ({total_duration_seconds:.2f}秒)"
                                    )

                                task.completed_at = datetime.now()

                                # 自动下载图片
                                try:
                                    from app.services.meitu_api_service import download_result_image

                                    local_path = download_result_image(result_url, task.id)
                                    if local_path:
                                        task.result_image_path = local_path
                                        logger.info(
                                            f"✅ [美图轮询] 任务 {task.id} 结果图已下载到本地: {local_path}"
                                        )
                                except Exception as download_error:
                                    logger.warning("[美图轮询] 下载图片失败: {str(download_error)}")

                                db.session.commit()
                                updated_count += 1
                                logger.info(
                                    f"✅ [美图轮询] 任务 {task.id} 状态已更新为成功，图片URL: {result_url}"
                                )
                            else:
                                # 没有找到结果URL，可能仍在处理中
                                # 检查是否有status字段
                                status = data.get("status", "")
                                if status == "processing":
                                    # 仍在处理中，不更新状态，等待下次轮询
                                    age_seconds = (
                                        (datetime.now() - task.created_at).total_seconds()
                                        if task.created_at
                                        else 0
                                    )
                                    logger.info(
                                        f"🔄 [美图轮询] 任务 {task.id} 仍在处理中 (已等待 {age_seconds:.1f}秒)"
                                    )
                                elif status == "failed" or status == "error":
                                    # 任务失败
                                    error_msg = (
                                        data.get("message") or data.get("error") or "任务失败"
                                    )
                                    task.status = "failed"
                                    task.error_message = str(error_msg)[:500]
                                    task.response_data = json.dumps(result, ensure_ascii=False)

                                    # 计算从任务创建到失败的总耗时
                                    if task.created_at:
                                        now = datetime.now()
                                        total_duration_seconds = (
                                            now - task.created_at
                                        ).total_seconds()
                                        total_duration_ms = int(total_duration_seconds * 1000)
                                        task.duration_ms = total_duration_ms
                                        logger.info(
                                            f"⏱️ [美图轮询] 任务 {task.id} 失败前总耗时: {total_duration_ms}ms ({total_duration_seconds:.2f}秒)"
                                        )

                                    task.completed_at = datetime.now()
                                    db.session.commit()
                                    updated_count += 1
                                    logger.info(
                                        f"✅ [美图轮询] 任务 {task.id} 状态已更新为失败: {error_msg}"
                                    )
                                else:
                                    # 未知状态，输出详细信息用于调试
                                    logger.warning(
                                        "[美图轮询] 任务 {task.id} 未找到结果URL，状态: {status if status else '无status字段'}, 完整响应: {json.dumps(result, ensure_ascii=False)[:300]}"
                                    )
                        else:
                            # API返回错误
                            error_msg = result.get("message", "查询失败")
                            logger.warning("[美图轮询] 任务 {task.id} 查询失败: {error_msg}")
                    else:
                        logger.warning(
                            "[美图轮询] 任务 {task.id} 查询请求失败: HTTP {response.status_code}"
                        )

                except Exception as e:
                    logger.warning("[美图轮询] 处理任务 {task.id} 时出错: {str(e)}")
                    import traceback

                    traceback.print_exc()
                    continue

            return updated_count

    except Exception as e:
        logger.error("[美图轮询] 轮询美图API任务失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return 0


def poll_processing_tasks():
    """轮询处理中的任务状态"""
    try:
        import sys

        if "test_server" not in sys.modules:
            logger.warning("[轮询] test_server模块未加载，无法轮询")
            return 0

        test_server_module = sys.modules["test_server"]
        db = test_server_module.db
        AITask = test_server_module.AITask
        APIProviderConfig = test_server_module.APIProviderConfig

        if not db or not AITask:
            logger.warning("[轮询] 数据库或模型未初始化")
            return 0

        with test_server_module.app.app_context():
            # 查找所有处理中的任务
            # 关键修复：排除同步API任务，同步API不应该轮询（应该一次性返回结果）
            Order = test_server_module.Order if hasattr(test_server_module, "Order") else None
            PollingConfig = (
                test_server_module.PollingConfig
                if hasattr(test_server_module, "PollingConfig")
                else None
            )

            # 从数据库读取轮询配置（工作流任务）
            wait_before_polling = 30  # 默认值：正常订单等待30秒
            wait_before_polling_test = 0  # 默认值：测试任务立即轮询
            polling_interval_with_tasks = 5  # 默认值：有活跃任务时每5秒轮询一次

            if PollingConfig:
                try:
                    workflow_config = PollingConfig.query.filter_by(
                        task_type="workflow_task", is_active=True
                    ).first()
                    if workflow_config:
                        wait_before_polling = workflow_config.wait_before_polling or 30
                        wait_before_polling_test = workflow_config.wait_before_polling_test or 0
                        polling_interval_with_tasks = (
                            workflow_config.polling_interval_with_tasks or 5
                        )
                        logger.info(
                            f"📋 [轮询] 使用轮询配置: 正常任务等待={wait_before_polling}秒, 测试任务等待={wait_before_polling_test}秒, 轮询间隔={polling_interval_with_tasks}秒"
                        )
                    else:
                        logger.warning("[轮询] 未找到启用的工作流任务轮询配置，使用默认值")
                except Exception as e:
                    logger.warning("[轮询] 读取轮询配置失败: {str(e)}，使用默认值")

            # 先查询所有处理中的任务
            all_processing_tasks = AITask.query.filter(
                AITask.status.in_(["pending", "processing"])
            ).all()

            # 根据任务类型和配置设置不同的等待时间
            cutoff_time_normal = datetime.now() - timedelta(seconds=wait_before_polling)
            cutoff_time_test = datetime.now() - timedelta(seconds=wait_before_polling_test)

            # 分离测试任务和正常任务
            test_tasks = []
            normal_tasks = []

            for task in all_processing_tasks:
                is_test_task = False
                if Order and task.order_id:
                    try:
                        order = Order.query.get(task.order_id)
                        if order:
                            source_type = getattr(order, "source_type", None)
                            # 判断是否为测试任务：admin_test 或 playground_test
                            if source_type in ["admin_test", "playground_test"]:
                                is_test_task = True
                            # 或者通过订单号判断（PLAY_开头的是Playground测试任务）
                            elif task.order_number and task.order_number.startswith("PLAY_"):
                                is_test_task = True
                    except Exception:
                        pass

                if is_test_task:
                    # 测试任务：立即开始轮询（wait_before_polling_test秒后）
                    if task.created_at and task.created_at <= cutoff_time_test:
                        test_tasks.append(task)
                else:
                    # 正常任务：wait_before_polling秒后开始轮询
                    if task.created_at and task.created_at <= cutoff_time_normal:
                        normal_tasks.append(task)

            # 合并任务列表
            processing_tasks = test_tasks + normal_tasks

            # 使用统一的cutoff_time用于后续查询（兼容旧代码）
            cutoff_time = cutoff_time_normal
            # 关键修复：排除创建时间过久的无效任务（超过20分钟的任务视为无效，避免占用资源）
            # 注意：延长到20分钟，给重试任务更多时间完成
            max_age_minutes = 20
            max_age_cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

            # 过滤掉过旧的任务（超过20分钟）
            processing_tasks = [
                t for t in processing_tasks if t.created_at and t.created_at >= max_age_cutoff
            ]

            # 添加调试日志：显示找到的任务数量
            if processing_tasks:
                logger.info(
                    f"🔍 [轮询] 找到 {len(processing_tasks)} 个待轮询任务（状态为pending或processing，创建时间超过30秒且不超过20分钟）"
                )
                for t in processing_tasks[:5]:  # 只显示前5个
                    age_seconds = (
                        (datetime.now() - t.created_at).total_seconds() if t.created_at else 0
                    )
                    age_minutes = age_seconds / 60
                    notes_preview = t.notes[:80] if t.notes else "None"
                    logger.info(
                        f"   - 任务 {t.id} (order: {t.order_number}): 状态={t.status}, 创建于{age_minutes:.1f}分钟前, comfyui_prompt_id={t.comfyui_prompt_id}, notes={notes_preview}"
                    )

            # 检查是否有过旧的任务需要清理（超过15分钟仍为processing状态）
            old_tasks = AITask.query.filter(
                AITask.status.in_(["pending", "processing"]), AITask.created_at < max_age_cutoff
            ).all()
            if old_tasks:
                logger.warning(
                    "[轮询] 发现 {len(old_tasks)} 个过旧的任务（超过20分钟仍为processing/pending），自动清理..."
                )
                for t in old_tasks:
                    age_minutes = (
                        (datetime.now() - t.created_at).total_seconds() / 60 if t.created_at else 0
                    )
                    logger.info(
                        f"   - 任务 {t.id} (order: {t.order_number}): 状态={t.status}, 创建于{age_minutes:.1f}分钟前，标记为失败"
                    )
                    # 自动标记为失败
                    t.status = "failed"
                    t.error_message = f"任务超时：超过{max_age_minutes}分钟仍未完成，已自动清理"
                    t.completed_at = datetime.now()
                db.session.commit()
                logger.info(f"✅ [轮询] 已自动清理 {len(old_tasks)} 个过旧任务")

            # 关键修复：过滤掉同步API任务（同步API不应该轮询，应该一次性返回结果）
            # 同步API如果连接断开，不应该通过轮询来获取结果，应该标记为失败
            filtered_tasks = []
            for task in processing_tasks:
                is_sync = False
                # 从processing_log中检查是否为同步API
                if task.processing_log:
                    try:
                        parsed_log = json.loads(task.processing_log)
                        # 检查是否是字典类型
                        if isinstance(parsed_log, dict):
                            api_info = parsed_log
                            api_config_id = api_info.get("api_config_id")
                            if api_config_id:
                                api_config = APIProviderConfig.query.get(api_config_id)
                                if (
                                    api_config
                                    and hasattr(api_config, "is_sync_api")
                                    and api_config.is_sync_api
                                ):
                                    is_sync = True
                                    # 同步API任务如果长时间处于processing状态，可能是连接断开导致
                                    # 检查任务创建时间，如果超过10分钟还是processing，标记为失败
                                    # 注意：同步API的read_timeout是8分钟（480秒），加上2分钟缓冲，总共10分钟
                                    task_age = (
                                        (datetime.now() - task.created_at).total_seconds()
                                        if task.created_at
                                        else 0
                                    )
                                    if (
                                        task_age > 600
                                    ):  # 10分钟（与read_timeout 8分钟 + 2分钟缓冲一致）
                                        logger.warning(
                                            "[轮询] 任务 {task.id} 是同步API任务，已超过10分钟仍为processing状态，可能是连接断开，标记为失败"
                                        )
                                        task.status = "failed"
                                        task.error_message = "同步API任务超时：可能连接断开，未收到响应（已等待10分钟）"
                                        db.session.commit()
                                    else:
                                        logger.warning(
                                            "[轮询] 任务 {task.id} 是同步API任务，跳过轮询（同步API应该一次性返回结果，当前已等待{task_age:.1f}秒，最多等待10分钟）"
                                        )
                        elif isinstance(parsed_log, list):
                            logger.warning(
                                "[轮询] 任务 {task.id} 的 processing_log 是 list 类型，跳过同步API检查"
                            )
                    except Exception as e:
                        logger.warning("[轮询] 检查任务 {task.id} 是否为同步API时出错: {str(e)}")

                if not is_sync:
                    filtered_tasks.append(task)

            processing_tasks = filtered_tasks

            # 添加调试日志：显示过滤后的任务数量
            if filtered_tasks:
                logger.info(
                    f"🔍 [轮询] 过滤后剩余 {len(filtered_tasks)} 个异步任务（已排除同步API任务）"
                )

            if not processing_tasks:
                return 0

            updated_count = 0

            for task in processing_tasks:
                try:
                    # 获取API配置
                    api_config = None
                    if task.processing_log:
                        try:
                            parsed_log = json.loads(task.processing_log)
                            # 检查是否是字典类型
                            if isinstance(parsed_log, dict):
                                api_info = parsed_log
                                api_config_id = api_info.get("api_config_id")
                                if api_config_id:
                                    api_config = APIProviderConfig.query.get(api_config_id)
                        except Exception:
                            pass

                    if not api_config:
                        api_config = APIProviderConfig.query.filter_by(
                            is_active=True, is_default=True
                        ).first()
                    if not api_config:
                        api_config = APIProviderConfig.query.filter_by(is_active=True).first()

                    # 检查是否是本地ComfyUI任务（有comfyui_prompt_id但没有api_config_id）
                    is_local_comfyui_task = False
                    # 优化：更宽松的判断条件，只要有comfyui_prompt_id和workflow_file就认为是ComfyUI任务
                    if task.comfyui_prompt_id and task.workflow_file:
                        # 检查是否有api_config_id（如果有，说明是API服务商的ComfyUI任务）
                        has_api_config = False
                        if task.processing_log:
                            try:
                                parsed_log = json.loads(task.processing_log)
                                if isinstance(parsed_log, dict) and parsed_log.get("api_config_id"):
                                    has_api_config = True
                            except Exception:
                                pass

                        # 如果没有api_config_id，说明是本地ComfyUI任务
                        if not has_api_config:
                            is_local_comfyui_task = True
                            logger.info(
                                f"🔍 [轮询] 任务 {task.id} 是本地ComfyUI任务（prompt_id={task.comfyui_prompt_id}, workflow_file={task.workflow_file}），将查询ComfyUI history API"
                            )

                    if not api_config and not is_local_comfyui_task:
                        continue

                    # 如果是本地ComfyUI任务，直接处理
                    if is_local_comfyui_task:
                        try:
                            from app.services.workflow_service import get_comfyui_config

                            comfyui_config = get_comfyui_config(db=db, AIConfig=None)
                            prompt_id = task.comfyui_prompt_id
                            output_id = task.comfyui_node_id

                            if not prompt_id or not output_id:
                                logger.warning(
                                    "[轮询] 任务 {task.id} 缺少 prompt_id 或 output_id，跳过"
                                )
                                continue

                            # 查询ComfyUI history API
                            history_url = f"{comfyui_config['base_url']}/history/{prompt_id}"
                            logger.info(f"🔄 [轮询] 查询ComfyUI任务状态: {history_url}")
                            logger.info(f"   - prompt_id: {prompt_id}")
                            logger.info(f"   - output_id: {output_id}")

                            response = requests.get(
                                history_url, timeout=10, proxies={"http": None, "https": None}
                            )

                            if response.status_code == 200:
                                history_data = response.json()
                                logger.info(
                                    f"   - history响应: {json.dumps(history_data, ensure_ascii=False)[:200]}..."
                                )

                                # 查找对应的输出节点
                                if prompt_id in history_data:
                                    outputs = history_data[prompt_id].get("outputs", {})
                                    if output_id in outputs:
                                        output_node = outputs[output_id]
                                        images = output_node.get("images", [])

                                        if images and len(images) > 0:
                                            # 任务已完成，获取结果图片
                                            image_info = images[0]
                                            image_filename = image_info.get("filename")
                                            image_subfolder = image_info.get("subfolder", "")
                                            image_type = image_info.get("type", "output")

                                            # 构建图片URL
                                            if image_subfolder:
                                                image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&subfolder={image_subfolder}&type={image_type}"
                                            else:
                                                image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&type={image_type}"

                                            # 更新任务状态
                                            task.status = "completed"
                                            task.output_image_path = image_url
                                            task.completed_at = datetime.now()

                                            # 下载图片到本地
                                            try:
                                                from app.routes.ai import download_api_result_image

                                                local_path = download_api_result_image(
                                                    image_url, prompt_id, test_server_module.app
                                                )
                                                if local_path:
                                                    task.output_image_path = local_path
                                                    logger.info(
                                                        f"✅ [轮询] ComfyUI任务 {task.id} 结果图已下载到本地: {local_path}"
                                                    )

                                                    # 生成缩略图（长边1920px的JPG）
                                                    try:
                                                        from app.utils.image_thumbnail import (
                                                            generate_thumbnail,
                                                        )

                                                        thumbnail_path = generate_thumbnail(
                                                            local_path, max_size=1920, quality=85
                                                        )
                                                        if thumbnail_path:
                                                            logger.info(
                                                                f"✅ [轮询] ComfyUI任务 {task.id} 缩略图生成成功: {thumbnail_path}"
                                                            )
                                                    except Exception as thumb_error:
                                                        logger.warning(
                                                            "[轮询] ComfyUI任务 {task.id} 生成缩略图失败: {str(thumb_error)}"
                                                        )
                                            except Exception as download_error:
                                                logger.warning(
                                                    "[轮询] 下载ComfyUI结果图失败: {str(download_error)}"
                                                )

                                            # 检查该订单的所有AI任务是否都已完成
                                            if task.order_id and task.order_id > 0:
                                                try:
                                                    Order = (
                                                        test_server_module.Order
                                                        if hasattr(test_server_module, "Order")
                                                        else None
                                                    )
                                                    if Order:
                                                        # 查询该订单的所有AI任务
                                                        all_tasks = AITask.query.filter_by(
                                                            order_id=task.order_id
                                                        ).all()
                                                        # 过滤掉失败和取消的任务，只统计有效任务
                                                        valid_tasks = [
                                                            t
                                                            for t in all_tasks
                                                            if t.status
                                                            not in ["failed", "cancelled"]
                                                        ]
                                                        completed_tasks = [
                                                            t
                                                            for t in valid_tasks
                                                            if t.status == "completed"
                                                            and t.output_image_path
                                                        ]

                                                        # 如果所有有效任务都已完成，更新订单状态为"待选片"
                                                        if len(valid_tasks) > 0 and len(
                                                            completed_tasks
                                                        ) == len(valid_tasks):
                                                            order = Order.query.get(task.order_id)
                                                            if order and order.status in [
                                                                "ai_processing",
                                                                "retouching",
                                                                "shooting",
                                                                "processing",
                                                            ]:
                                                                old_status = order.status
                                                                order.status = (
                                                                    "pending_selection"  # 待选片
                                                                )
                                                                logger.info(
                                                                    f"✅ [轮询] 订单 {order.order_number} 所有AI任务已完成 ({len(completed_tasks)}/{len(valid_tasks)})，状态已更新为: pending_selection (从 {old_status} 更新)"
                                                                )
                                                            elif order:
                                                                logger.info(
                                                                    f"ℹ️ [轮询] 订单 {order.order_number} 所有AI任务已完成，但当前状态是 {order.status}，不更新"
                                                                )
                                                except Exception as e:
                                                    logger.warning(
                                                        "[轮询] 检查订单状态失败: {str(e)}"
                                                    )
                                                    import traceback

                                                    traceback.print_exc()

                                            db.session.commit()
                                            updated_count += 1
                                            logger.info(
                                                f"✅ [轮询] ComfyUI任务 {task.id} 已完成，图片URL: {image_url}"
                                            )
                                            continue
                                        else:
                                            # 任务仍在处理中
                                            logger.info(
                                                f"⏳ [轮询] ComfyUI任务 {task.id} 仍在处理中（输出节点 {output_id} 还没有图片）"
                                            )
                                            continue
                                    else:
                                        # 输出节点还没有结果
                                        logger.info(
                                            f"⏳ [轮询] ComfyUI任务 {task.id} 仍在处理中（输出节点 {output_id} 不存在）"
                                        )
                                        continue
                                else:
                                    # prompt_id不在history中，可能任务还在队列中
                                    logger.info(
                                        f"⏳ [轮询] ComfyUI任务 {task.id} 仍在队列中（history中未找到）"
                                    )
                                    continue
                            else:
                                logger.warning(
                                    "[轮询] 查询ComfyUI history失败: HTTP {response.status_code}"
                                )
                                continue
                        except Exception as e:
                            logger.warning("[轮询] 处理ComfyUI任务 {task.id} 时出错: {str(e)}")
                            import traceback

                            traceback.print_exc()
                            continue

                    # 获取API任务ID（参考bk-photo-v4：优先从notes提取T8_API_TASK_ID，其次从processing_log提取）
                    api_task_id = None

                    # 关键修复：优先从notes中提取T8_API_TASK_ID（参考bk-photo-v4）
                    if task.notes and "T8_API_TASK_ID:" in task.notes:
                        try:
                            notes_task_id = (
                                task.notes.split("T8_API_TASK_ID:")[1]
                                .split("|")[0]
                                .split()[0]
                                .strip()
                            )
                            if notes_task_id:
                                # 关键修复：如果notes中的ID与comfyui_prompt_id不一致，且comfyui_prompt_id看起来更新（更长或包含特定前缀），使用comfyui_prompt_id
                                if (
                                    task.comfyui_prompt_id
                                    and task.comfyui_prompt_id != notes_task_id
                                ):
                                    # 如果comfyui_prompt_id更新了但notes没更新，使用comfyui_prompt_id
                                    # 检查comfyui_prompt_id是否看起来是新的（更长或包含特定前缀如b1f3b4f8）
                                    if len(task.comfyui_prompt_id) > len(
                                        notes_task_id
                                    ) or task.comfyui_prompt_id.startswith("b1f3b4f8"):
                                        logger.warning(
                                            "[轮询] 任务 {task.id} notes中的ID({notes_task_id})与comfyui_prompt_id({task.comfyui_prompt_id})不一致，使用comfyui_prompt_id（可能重试后未更新notes）"
                                        )
                                        api_task_id = task.comfyui_prompt_id
                                    else:
                                        api_task_id = notes_task_id
                                        logger.info(
                                            f"✅ [轮询] 从notes中提取到T8_API_TASK_ID: {api_task_id}（优先使用notes中的）"
                                        )
                                else:
                                    api_task_id = notes_task_id
                                    logger.info(
                                        f"✅ [轮询] 从notes中提取到T8_API_TASK_ID: {api_task_id}（优先使用notes中的）"
                                    )
                        except Exception as e:
                            logger.warning(
                                "解析任务 {task.id} 的notes中的T8_API_TASK_ID失败: {str(e)}"
                            )

                    # 如果notes中没有，从comfyui_prompt_id获取
                    if not api_task_id:
                        api_task_id = task.comfyui_prompt_id

                    # 从processing_log中提取（作为备选）
                    if not api_task_id and task.processing_log:
                        try:
                            parsed_log = json.loads(task.processing_log)
                            # 检查是否是字典类型
                            if isinstance(parsed_log, dict):
                                api_info = parsed_log
                                api_task_id = (
                                    api_info.get("task_id")
                                    or api_info.get("api_task_id")
                                    or api_info.get("id")
                                )
                        except Exception:
                            pass

                    if not api_task_id:
                        logger.warning(
                            "[轮询] 任务 {task.id} (order_number: {task.order_number}) 没有API任务ID，跳过轮询"
                        )
                        logger.info(f"   - comfyui_prompt_id: {task.comfyui_prompt_id}")
                        logger.info(f"   - notes: {task.notes[:100] if task.notes else 'None'}")
                        if task.processing_log:
                            try:
                                parsed_log = json.loads(task.processing_log)
                                # 检查是否是字典类型
                                if isinstance(parsed_log, dict):
                                    api_info = parsed_log
                                    logger.info(
                                        f"   - processing_log中的api_task_id: {api_info.get('api_task_id')}"
                                    )
                                    logger.info(
                                        f"   - processing_log中的task_id: {api_info.get('task_id')}"
                                    )
                                    logger.info(
                                        f"   - processing_log中的api_config_id: {api_info.get('api_config_id')}"
                                    )
                                elif isinstance(parsed_log, list):
                                    logger.info("   - processing_log是list类型，无法提取信息")
                            except Exception:
                                pass
                        continue

                    logger.info(
                        f"🔄 [轮询] 开始轮询任务 {task.id} (order: {task.order_number}), API任务ID: {api_task_id}"
                    )

                    # 构建查询URL
                    host = api_config.host_domestic or api_config.host_overseas
                    if not host:
                        continue

                    # 根据API类型构建查询端点
                    result_endpoint = api_config.result_endpoint

                    # 关键修复：检查是否是T8Star服务商（通过host判断）
                    is_t8star = host and "t8star.cn" in host.lower()

                    # 关键修复：如果result_endpoint中包含{task_id}占位符，需要替换为实际的task_id
                    if result_endpoint and "{task_id}" in result_endpoint:
                        result_endpoint = result_endpoint.replace("{task_id}", api_task_id)
                        logger.info(
                            f"📝 [轮询] 替换result_endpoint中的{{task_id}}占位符: {result_endpoint}",
                            flush=True,
                        )

                    # 关键修复：如果result_endpoint已配置但格式不正确（T8Star应该使用/v1/images/tasks/{task_id}），自动修正
                    if result_endpoint and is_t8star and api_config.api_type == "nano-banana-edits":
                        # T8Star的nano-banana-edits应该使用GET /v1/images/tasks/{task_id}格式
                        if (
                            "/v1/images/edits/result" in result_endpoint
                            or result_endpoint.endswith("/edits/result")
                        ):
                            # 错误的格式，自动修正为正确的格式
                            result_endpoint = f"/v1/images/tasks/{api_task_id}"
                            logger.info(
                                f"📝 [轮询] T8Star result_endpoint格式不正确，自动修正为: {result_endpoint}",
                                flush=True,
                            )
                        elif "/v1/images/tasks/" not in result_endpoint:
                            # 如果result_endpoint不是/v1/images/tasks/格式，也修正
                            result_endpoint = f"/v1/images/tasks/{api_task_id}"
                            logger.info(
                                f"📝 [轮询] T8Star result_endpoint不是OpenAPI格式，自动修正为: {result_endpoint}",
                                flush=True,
                            )

                    # RunningHub API 特殊处理
                    if api_config.api_type in [
                        "runninghub-rhart-edit",
                        "runninghub-comfyui-workflow",
                    ]:
                        # 关键修复：支持两种查询接口格式
                        # 1. /openapi/v2/query (新格式，请求体只需要 taskId，响应格式: {"status": "...", "results": [...]})
                        # 2. /task/openapi/outputs (旧格式，请求体需要 apiKey 和 taskId，响应格式: {"code": 0, "data": [...]})
                        if not result_endpoint:
                            # 默认使用新格式 /openapi/v2/query
                            result_endpoint = "/openapi/v2/query"
                        elif result_endpoint == "/openapi/v2/task/outputs":
                            # 兼容旧配置，使用旧格式
                            result_endpoint = "/task/openapi/outputs"

                        result_url = f"{host.rstrip('/')}{result_endpoint}"

                        # 判断使用哪种格式
                        use_new_query_format = "/openapi/v2/query" in result_endpoint

                        if use_new_query_format:
                            # 新格式：/openapi/v2/query，请求体只需要 taskId，使用 Bearer 认证
                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {api_config.api_key}",
                            }
                            use_get_method = False
                        else:
                            # 旧格式：/task/openapi/outputs，请求体需要 apiKey 和 taskId
                            headers = {
                                "Content-Type": "application/json",
                                "Host": "www.runninghub.cn",
                            }
                            use_get_method = False
                    else:
                        # 其他API类型：根据draw_endpoint推断查询端点
                        if not result_endpoint:
                            draw_endpoint = api_config.draw_endpoint or "/v1/draw/nano-banana"
                            # 关键修复：检查是否是T8Star服务商（通过host判断）
                            is_t8star = host and "t8star.cn" in host.lower()

                            if (
                                "/v1/images/generations" in draw_endpoint
                                or "/v1/images/tasks/" in draw_endpoint
                            ):
                                result_endpoint = f"/v1/images/tasks/{api_task_id}"
                            elif draw_endpoint.endswith("/edits") and is_t8star:
                                # T8Star的/v1/images/edits异步模式使用OpenAPI格式：GET /v1/images/tasks/{task_id}
                                # 参考bk-photo-v8：https://gpt-best.apifox.cn/api-339685644
                                result_endpoint = (
                                    f"/v1/images/tasks/{api_task_id}"  # GET请求，task_id在URL中
                                )
                                logger.info(
                                    f"📝 [轮询] T8Star nano-banana-edits异步模式：使用OpenAPI格式查询端点 GET /v1/images/tasks/{api_task_id}",
                                    flush=True,
                                )
                            elif draw_endpoint.endswith("/edits"):
                                # 其他服务商的/v1/images/edits使用POST格式
                                result_endpoint = draw_endpoint + "/result"
                            else:
                                result_endpoint = "/v1/draw/result"

                        # 判断是GET还是POST请求
                        # OpenAPI格式：GET /v1/images/tasks/{task_id}（T8Star使用此格式）
                        # 其他格式：POST /v1/images/edits/result 或 POST /v1/draw/result
                        use_get_method = "/v1/images/tasks/" in result_endpoint

                        if use_get_method:
                            result_url = host.rstrip("/") + result_endpoint
                        else:
                            result_url = host.rstrip("/") + result_endpoint

                        headers = {"Authorization": f"Bearer {api_config.api_key}"}

                    # 禁用代理（国内服务商）
                    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
                    has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
                    is_known_domestic_domain = host and any(
                        domain in host.lower()
                        for domain in [
                            "grsai.dakka.com.cn",
                            "grsai-file.dakka.com.cn",
                            "t8star.cn",
                            "ai.t8star.cn",
                        ]
                    )

                    if is_known_domestic_domain or api_config.host_domestic:
                        proxies = {"http": None, "https": None}
                    else:
                        proxies = None

                    # 查询任务状态
                    result_data = None  # 初始化 result_data，避免未定义错误
                    try:
                        if api_config.api_type in [
                            "runninghub-rhart-edit",
                            "runninghub-comfyui-workflow",
                        ]:
                            # RunningHub API：使用 POST 请求
                            # 关键修复：支持两种查询接口格式
                            # 判断使用哪种格式（基于 result_endpoint）
                            use_new_query_format = (
                                result_endpoint and "/openapi/v2/query" in result_endpoint
                            )

                            if use_new_query_format:
                                # 新格式：/openapi/v2/query，请求体只需要 taskId
                                # 参考用户提供的示例：https://www.runninghub.cn/call-api/api-detail/2004543527918551041
                                request_payload = {"taskId": api_task_id}
                                logger.info(
                                    f"📤 [轮询] RunningHub 使用新格式查询接口 /openapi/v2/query，请求体: {json.dumps(request_payload, ensure_ascii=False)}"
                                )
                            else:
                                # 旧格式：/task/openapi/outputs，请求体需要 apiKey 和 taskId
                                request_payload = {
                                    "apiKey": api_config.api_key,
                                    "taskId": api_task_id,
                                }
                                logger.info(
                                    f"📤 [轮询] RunningHub 使用旧格式查询接口 /task/openapi/outputs，请求体: {json.dumps(request_payload, ensure_ascii=False)}"
                                )

                            response = requests.post(
                                result_url,
                                json=request_payload,
                                headers=headers,
                                timeout=30,
                                proxies=proxies,
                            )

                            # 关键修复：解析 RunningHub API 的 POST 响应
                            logger.info(
                                f"📥 [轮询] RunningHub API 响应状态码: {response.status_code}"
                            )
                            if response.status_code == 200:
                                try:
                                    result_data = response.json()
                                    logger.info(
                                        f"📥 [轮询] RunningHub API 响应内容: {json.dumps(result_data, ensure_ascii=False)[:500]}"
                                    )
                                except Exception as e:
                                    logger.warning("[轮询] RunningHub API 响应解析失败: {str(e)}")
                                    result_data = None
                            else:
                                logger.warning(
                                    "[轮询] RunningHub API 请求失败，状态码: {response.status_code}"
                                )
                                try:
                                    result_data = (
                                        response.json()
                                    )  # 即使状态码不是200，也尝试解析响应
                                    logger.info(
                                        f"📥 [轮询] RunningHub API 错误响应内容: {json.dumps(result_data, ensure_ascii=False)[:500]}"
                                    )
                                except Exception:
                                    result_data = None
                        elif use_get_method:
                            response = requests.get(
                                result_url, headers=headers, timeout=30, proxies=proxies
                            )
                            result_data = None  # 初始化 result_data
                            if response.status_code == 200:
                                try:
                                    result_data = response.json()
                                except Exception as e:
                                    logger.warning("[轮询] GET请求响应解析失败: {str(e)}")
                                    result_data = None
                            else:
                                logger.warning("[轮询] GET请求失败，状态码: {response.status_code}")
                                try:
                                    result_data = (
                                        response.json()
                                    )  # 即使状态码不是200，也尝试解析响应
                                except Exception:
                                    result_data = None
                        else:
                            # 关键修复：尝试多种请求体格式（与手动查询逻辑保持一致）
                            # T8服务商的/v1/images/edits/result可能需要{"task_id": ...}格式
                            request_payloads = [
                                {
                                    "Id": api_task_id
                                },  # 参考bk-photo-v4：通用异步API格式（大写Id，优先）
                                {"task_id": api_task_id},  # nano-banana-edits/T8格式（备选）
                                {"id": api_task_id},  # 小写id格式（备选）
                            ]

                            response = None
                            result_data = None
                            payload_used = None

                            for payload in request_payloads:
                                try:
                                    logger.info(
                                        f"📤 [轮询] POST请求，尝试参数格式: {list(payload.keys())[0]}"
                                    )
                                    response = requests.post(
                                        result_url,
                                        json=payload,
                                        headers=headers,
                                        timeout=30,
                                        proxies=proxies,
                                    )

                                    if response.status_code == 200:
                                        result_data = response.json()
                                        # 检查是否成功获取到结果
                                        if isinstance(result_data, dict):
                                            # 检查是否有status字段或code=0
                                            if (
                                                "status" in result_data
                                                or result_data.get("code") == 0
                                            ):
                                                payload_used = payload
                                                logger.info(
                                                    f"✅ [轮询] 使用参数格式 {list(payload.keys())[0]} 查询成功"
                                                )
                                                break
                                            elif result_data.get("code") == -22:
                                                # 任务不存在，尝试下一个格式
                                                logger.warning(
                                                    "[轮询] 参数格式 {list(payload.keys())[0]} 返回code=-22，尝试下一个格式"
                                                )
                                                continue
                                        else:
                                            # 非字典格式，视为成功
                                            payload_used = payload
                                            logger.info(
                                                f"✅ [轮询] 使用参数格式 {list(payload.keys())[0]} 查询成功（非字典格式）"
                                            )
                                            break
                                    else:
                                        logger.warning(
                                            "[轮询] HTTP错误: {response.status_code}，尝试下一个参数格式"
                                        )
                                        continue
                                except Exception as e:
                                    logger.warning("[轮询] 请求异常: {str(e)}，尝试下一个参数格式")
                                    continue

                            # 如果所有格式都失败，使用最后一个响应（如果有）
                            if not result_data and response:
                                try:
                                    result_data = response.json()
                                except Exception:
                                    pass

                            # 如果仍然没有result_data，说明所有格式都失败了
                            if not result_data:
                                logger.error(
                                    "[轮询] 任务 {task.id} 所有请求体格式都失败，无法获取结果"
                                )
                                continue

                        # 关键修复：只有在result_data存在时才继续解析
                        if result_data:
                            # 解析响应
                            status = None
                            image_url = None
                            error_msg = None  # 初始化 error_msg，用于保存失败时的错误信息

                            # RunningHub API 特殊处理
                            if api_config.api_type in [
                                "runninghub-rhart-edit",
                                "runninghub-comfyui-workflow",
                            ]:
                                # 关键修复：支持两种响应格式
                                # 判断使用哪种格式（基于 result_endpoint）
                                use_new_query_format = (
                                    result_endpoint and "/openapi/v2/query" in result_endpoint
                                )

                                if use_new_query_format:
                                    # 新格式：/openapi/v2/query 响应格式
                                    # 参考用户提供的示例：{"status": "SUCCESS/RUNNING/QUEUED/FAILED", "results": [{"url": "..."}], "errorMessage": "..."}
                                    status = (
                                        result_data.get("status", "").upper()
                                        if result_data.get("status")
                                        else ""
                                    )

                                    # 关键修复：如果 status 为空但 errorCode 或 errorMessage 存在，应该识别为失败状态
                                    if not status or status == "":
                                        error_code = result_data.get("errorCode")
                                        error_message = result_data.get("errorMessage")
                                        if error_code or error_message:
                                            # RunningHub API 返回了错误码或错误信息，但 status 为空，应该识别为失败
                                            status = "FAILED"
                                            error_msg = (
                                                error_message or f"API错误 (errorCode={error_code})"
                                                if error_code
                                                else "任务失败"
                                            )
                                            logger.warning(
                                                "[轮询] RunningHub API 返回错误但 status 为空，识别为失败: errorCode={error_code}, errorMessage={error_message}"
                                            )

                                    if status == "SUCCESS":
                                        # 成功：从 results 数组提取图片URL
                                        results = result_data.get("results", [])
                                        if isinstance(results, list) and len(results) > 0:
                                            image_url = results[0].get("url")
                                            logger.info(
                                                f"✅ [轮询] RunningHub 任务 {api_task_id} 成功，图片URL: {image_url}"
                                            )
                                        else:
                                            logger.warning(
                                                "[轮询] RunningHub 任务 {api_task_id} 状态为SUCCESS但没有results"
                                            )
                                    elif status in ["RUNNING", "QUEUED"]:
                                        # 处理中或排队中
                                        logger.info(
                                            f"🔄 [轮询] RunningHub 任务 {api_task_id} 状态: {status}"
                                        )
                                    elif status == "FAILED":
                                        # 失败：提取错误信息
                                        error_msg = result_data.get("errorMessage", "任务失败")
                                        if not error_msg:
                                            error_code = result_data.get("errorCode")
                                            error_msg = (
                                                f"API错误 (errorCode={error_code})"
                                                if error_code
                                                else "任务失败"
                                            )
                                        status = "failed"  # 关键修复：确保 status 设置为 'failed'，以便后续逻辑正确处理
                                        logger.error(
                                            "[轮询] RunningHub 任务 {api_task_id} 失败: {error_msg}"
                                        )
                                        # 关键修复：不立即更新任务状态，让后续的重试逻辑处理
                                        # 保存错误信息到 error_msg 变量，供后续逻辑使用（在 elif status in ['failed', 'error']: 块中处理）
                                    else:
                                        logger.warning(
                                            "[轮询] RunningHub 任务 {api_task_id} 未知状态: {status}"
                                        )
                                else:
                                    # 旧格式：/task/openapi/outputs 响应格式
                                    # 根据文档：https://www.runninghub.cn/runninghub-api-doc-cn/api-276613253
                                    # code: 0 - 成功，返回 data 数组，包含 fileUrl
                                    # code: 804 - 运行中 (APIKEY_TASK_IS_RUNNING)
                                    # code: 813 - 排队中 (APIKEY_TASK_IS_QUEUED)
                                    # code: 805 - 失败，返回失败原因
                                    response_code = result_data.get("code")

                                    if response_code == 0:
                                        # 成功：返回结果数组
                                        data = result_data.get("data")
                                        if isinstance(data, list) and len(data) > 0:
                                            # data 是结果数组，包含 fileUrl
                                            image_url = data[0].get("fileUrl") or data[0].get("url")
                                            status = "SUCCESS"  # 有结果说明成功
                                        elif isinstance(data, dict):
                                            # data 是对象，包含 taskId, status, results 等
                                            status = data.get("status", "")
                                            results = data.get("results", [])
                                            if isinstance(results, list) and len(results) > 0:
                                                image_url = results[0].get("url") or results[0].get(
                                                    "fileUrl"
                                                )
                                        elif isinstance(data, str):
                                            # data 是状态字符串：QUEUED, RUNNING, SUCCESS, FAILED
                                            status = data
                                    elif response_code == 804:
                                        # 运行中 (APIKEY_TASK_IS_RUNNING)
                                        status = "RUNNING"
                                        logger.info(
                                            f"🔄 [轮询] RunningHub 任务 {api_task_id} 正在运行中"
                                        )
                                    elif response_code == 813:
                                        # 排队中 (APIKEY_TASK_IS_QUEUED)
                                        status = "QUEUED"
                                        logger.info(
                                            f"⏳ [轮询] RunningHub 任务 {api_task_id} 正在排队中"
                                        )
                                    elif response_code == 805:
                                        # 失败，返回失败原因
                                        status = "FAILED"
                                        error_msg = result_data.get("msg", "")
                                        failed_reason = result_data.get("data", {}).get(
                                            "failedReason", {}
                                        )
                                        error_details = f"任务失败: {error_msg}"
                                        if failed_reason:
                                            node_name = failed_reason.get("node_name", "")
                                            exception_type = failed_reason.get("exception_type", "")
                                            exception_message = failed_reason.get(
                                                "exception_message", ""
                                            )
                                            if node_name or exception_type:
                                                error_details += f" | 节点: {node_name}, 错误类型: {exception_type}"
                                            if exception_message:
                                                error_details += (
                                                    f" | 错误信息: {exception_message[:200]}"
                                                )
                                        logger.error(
                                            "[轮询] RunningHub 任务 {api_task_id} 失败: {error_details}"
                                        )
                                    else:
                                        # 其他错误响应
                                        error_code = result_data.get("code")
                                        error_msg = result_data.get("msg", "")
                                        logger.warning(
                                            "[轮询] RunningHub 查询任务 {api_task_id} 返回未知状态: code={error_code}, msg={error_msg}"
                                        )

                            elif isinstance(result_data, dict):
                                # grsai格式：{"code": 0, "data": {"status": "succeeded", "url": "..."}} 或 {"code": 0, "data": {"status": "succeeded", "results": [{"url": "..."}]}}
                                if "code" in result_data:
                                    if result_data.get("code") == 0 and "data" in result_data:
                                        data = result_data.get("data")
                                        if isinstance(data, dict):
                                            status = data.get("status")
                                            # 关键修复：即使code=0，如果status是failed，也要提取错误信息并确保status变量正确设置
                                            if status == "failed":
                                                # 提取错误信息
                                                error_msg = (
                                                    data.get("error")
                                                    or data.get("error_message")
                                                    or data.get("failure_reason")
                                                    or "任务失败"
                                                )
                                                logger.warning(
                                                    "[轮询] GRSAI任务失败（code=0但status=failed），错误信息: {error_msg}"
                                                )
                                                # 确保status变量设置为'failed'，以便后续逻辑正确处理
                                                status = "failed"
                                                # 不设置image_url，让后续逻辑处理失败状态
                                                image_url = None
                                            else:
                                                # 优先从results数组获取URL（参考bk-photo-v4）
                                                results = data.get("results", [])
                                                if isinstance(results, list) and len(results) > 0:
                                                    image_url = results[0].get("url") or results[
                                                        0
                                                    ].get("image_url")
                                                    logger.info(
                                                        f"🔍 [轮询] 从results数组提取图片URL: {image_url}"
                                                    )
                                                else:
                                                    # 如果没有results数组，从data直接获取
                                                    image_url = (
                                                        data.get("url")
                                                        or data.get("image_url")
                                                        or data.get("result_url")
                                                    )
                                                    logger.info(
                                                        f"🔍 [轮询] 从data字段提取图片URL: {image_url}"
                                                    )
                                                # 关键修复：确保status变量正确设置（GRSAI返回'succeeded'，需要映射为'completed'）
                                                if status == "succeeded":
                                                    status = "completed"  # 统一使用'completed'状态
                                                    logger.info(
                                                        "✅ [轮询] GRSAI任务状态为succeeded，映射为completed"
                                                    )
                                                # 关键修复：确保status变量正确设置（GRSAI返回'succeeded'，需要映射为'completed'）
                                                if status == "succeeded":
                                                    status = "completed"  # 统一使用'completed'状态
                                                    logger.info(
                                                        "✅ [轮询] GRSAI任务状态为succeeded，映射为completed"
                                                    )
                                # T8Star格式（实际是三层嵌套）：{"code": "success", "data": {"status": "SUCCESS", "data": {"data": [{"url": "..."}]}}}
                                # 关键修复：T8Star使用GET /v1/images/tasks/{task_id}时，响应格式是三层嵌套（data.data是对象，data.data.data是数组）
                                if is_t8star and use_get_method and "data" in result_data:
                                    data = result_data.get("data")
                                    if isinstance(data, dict):
                                        status = data.get(
                                            "status"
                                        )  # "SUCCESS", "FAILED", "PROCESSING"等
                                        # 关键修复：优先检查 data.data.data 是否是数组（三层嵌套格式，这是实际格式）
                                        if "data" in data:
                                            inner_data = data.get("data")
                                            # 优先：data.data 是对象，继续检查 data.data.data（三层嵌套格式，实际格式）
                                            if (
                                                isinstance(inner_data, dict)
                                                and "data" in inner_data
                                            ):
                                                if (
                                                    isinstance(inner_data.get("data"), list)
                                                    and len(inner_data.get("data")) > 0
                                                ):
                                                    data_list = inner_data.get("data")
                                                    first_item = data_list[0]
                                                    if isinstance(first_item, dict):
                                                        image_url = first_item.get("url")
                                                        logger.info(
                                                            f"✅ [轮询] T8Star从三层嵌套格式（data.data.data数组）提取图片URL: {image_url}"
                                                        )
                                            # 备选：data.data 是数组（两层嵌套格式，可能某些情况下存在）
                                            elif (
                                                isinstance(inner_data, list) and len(inner_data) > 0
                                            ):
                                                first_item = inner_data[0]
                                                if isinstance(first_item, dict):
                                                    image_url = first_item.get("url")
                                                    logger.info(
                                                        f"✅ [轮询] T8Star从两层嵌套格式（data.data数组）提取图片URL: {image_url}"
                                                    )
                                        # 如果还是没有，尝试从data直接获取
                                        if not image_url:
                                            image_url = data.get("url") or data.get("image_url")
                                            if image_url:
                                                logger.info(
                                                    f"✅ [轮询] T8Star从data字段提取图片URL: {image_url}"
                                                )
                                        # 状态映射：T8Star返回"SUCCESS"，需要映射为"completed"
                                        if status == "SUCCESS":
                                            status = "completed"
                                            logger.info(
                                                "✅ [轮询] T8Star任务状态为SUCCESS，映射为completed"
                                            )
                                        elif status == "FAILED":
                                            status = "failed"
                                            logger.error(
                                                "[轮询] T8Star任务状态为FAILED，映射为failed"
                                            )
                                        elif status in [
                                            "PROCESSING",
                                            "PENDING",
                                            "QUEUED",
                                            "RUNNING",
                                        ]:
                                            status = "processing"
                                            logger.info(
                                                f"🔄 [轮询] T8Star任务状态为{status}，映射为processing"
                                            )
                                # 标准格式
                                elif "status" in result_data:
                                    status = result_data.get("status")
                                    image_url = result_data.get("url") or result_data.get(
                                        "image_url"
                                    )
                                elif "data" in result_data and isinstance(
                                    result_data.get("data"), dict
                                ):
                                    data = result_data.get("data")
                                    status = data.get("status")
                                    # 优先从results数组获取
                                    results = data.get("results", [])
                                    if isinstance(results, list) and len(results) > 0:
                                        image_url = results[0].get("url") or results[0].get(
                                            "image_url"
                                        )
                                    else:
                                        image_url = data.get("url") or data.get("image_url")

                                # 提取图片URL（参考bk-photo-v4）
                                if not image_url:
                                    if "data" in result_data:
                                        data = result_data.get("data")
                                        if isinstance(data, dict):
                                            # 优先从results数组获取
                                            results = data.get("results", [])
                                            if isinstance(results, list) and len(results) > 0:
                                                image_url = results[0].get("url") or results[0].get(
                                                    "image_url"
                                                )
                                            else:
                                                image_url = data.get("url") or data.get("image_url")
                                        elif isinstance(data, list) and len(data) > 0:
                                            image_url = data[0].get("url") or data[0].get(
                                                "image_url"
                                            )
                                    elif "url" in result_data:
                                        image_url = result_data.get("url")

                            # RunningHub 状态映射和预计完成时间提取
                            if api_config.api_type in [
                                "runninghub-rhart-edit",
                                "runninghub-comfyui-workflow",
                            ]:
                                # RunningHub 状态：QUEUED, RUNNING, SUCCESS, FAILED
                                if status == "SUCCESS" and image_url:
                                    status = "completed"
                                elif status == "FAILED":
                                    status = "failed"
                                elif status in ["QUEUED", "RUNNING"]:
                                    status = "processing"

                                    # 从API响应中提取预计完成时间（如果API返回了该字段）
                                    # 检查响应中可能包含预计完成时间的字段
                                    estimated_time_from_api = None

                                    # 检查顶层字段
                                    for field_name in [
                                        "estimatedTime",
                                        "estimated_time",
                                        "eta",
                                        "ETA",
                                        "estimatedCompletionTime",
                                        "finishTime",
                                        "finish_time",
                                    ]:
                                        if field_name in result_data:
                                            estimated_time_from_api = result_data.get(field_name)
                                            break

                                    # 检查 data 字段中
                                    if not estimated_time_from_api and result_data.get("data"):
                                        data = result_data.get("data")
                                        if isinstance(data, dict):
                                            for field_name in [
                                                "estimatedTime",
                                                "estimated_time",
                                                "eta",
                                                "ETA",
                                                "estimatedCompletionTime",
                                                "finishTime",
                                                "finish_time",
                                            ]:
                                                if field_name in data:
                                                    estimated_time_from_api = data.get(field_name)
                                                    break

                                    # 如果API返回了预计完成时间，使用API的值
                                    if estimated_time_from_api:
                                        try:
                                            # 尝试解析为时间戳（秒或毫秒）
                                            if isinstance(estimated_time_from_api, (int, float)):
                                                # 判断是秒还是毫秒（通常大于1000000000的是秒，否则可能是毫秒）
                                                if estimated_time_from_api > 1000000000000:  # 毫秒
                                                    estimated_time_from_api = (
                                                        estimated_time_from_api / 1000
                                                    )
                                                estimated_time = datetime.fromtimestamp(
                                                    estimated_time_from_api
                                                )
                                            elif isinstance(estimated_time_from_api, str):
                                                # 尝试解析ISO格式字符串
                                                try:
                                                    estimated_time = datetime.fromisoformat(
                                                        estimated_time_from_api.replace(
                                                            "Z", "+00:00"
                                                        )
                                                    )
                                                except Exception:
                                                    # 尝试解析时间戳字符串
                                                    try:
                                                        timestamp = float(estimated_time_from_api)
                                                        if timestamp > 1000000000000:  # 毫秒
                                                            timestamp = timestamp / 1000
                                                        estimated_time = datetime.fromtimestamp(
                                                            timestamp
                                                        )
                                                    except Exception:
                                                        estimated_time = None
                                            else:
                                                estimated_time = None

                                            if estimated_time:
                                                task.estimated_completion_time = estimated_time
                                                logger.info(
                                                    f"📅 [轮询] RunningHub 任务 {api_task_id} 预计完成时间（来自API）: {estimated_time.strftime('%Y-%m-%d %H:%M:%S')}"
                                                )
                                                db.session.commit()
                                        except Exception as e:
                                            logger.warning(
                                                "[轮询] 解析API返回的预计完成时间失败: {str(e)}"
                                            )
                                    else:
                                        # 如果API没有返回预计完成时间，打印调试信息
                                        logger.info(
                                            f"🔍 [轮询] RunningHub 任务 {api_task_id} API响应中未找到预计完成时间字段，响应字段: {list(result_data.keys())}"
                                        )
                                        if result_data.get("data") and isinstance(
                                            result_data.get("data"), dict
                                        ):
                                            logger.info(
                                                f"🔍 [轮询] data字段中的键: {list(result_data.get('data').keys())}"
                                            )

                            # 更新任务状态
                            # 关键修复：添加调试日志，确保status变量正确传递
                            if result_data:
                                logger.info(
                                    f"🔍 [轮询] 任务 {task.id} 解析后的状态: status={status}, image_url={image_url if image_url else 'None'}, result_data keys={list(result_data.keys()) if isinstance(result_data, dict) else 'N/A'}"
                                )
                            else:
                                logger.warning(
                                    "[轮询] 任务 {task.id} result_data 为空，无法解析状态"
                                )
                                continue  # 跳过这个任务，等待下次轮询

                            # 关键修复：检查任务是否已完成但image_url为空的情况
                            if status in ["succeeded", "completed", "success"]:
                                if not image_url:
                                    # 状态是成功但没有图片URL，可能是响应格式问题，尝试重新提取
                                    logger.warning(
                                        "[轮询] 任务 {task.id} 状态为{status}但没有图片URL，尝试重新提取"
                                    )
                                    if isinstance(result_data, dict):
                                        if "data" in result_data:
                                            data = result_data.get("data")
                                            if isinstance(data, dict):
                                                # 再次尝试提取
                                                image_url = (
                                                    data.get("url")
                                                    or data.get("image_url")
                                                    or data.get("result_url")
                                                )
                                                if not image_url:
                                                    results = data.get("results", [])
                                                    if (
                                                        isinstance(results, list)
                                                        and len(results) > 0
                                                    ):
                                                        image_url = results[0].get(
                                                            "url"
                                                        ) or results[0].get("image_url")
                                                if image_url:
                                                    logger.info(
                                                        f"✅ [轮询] 重新提取到图片URL: {image_url}"
                                                    )

                            if status in ["succeeded", "completed", "success"] and image_url:
                                task.status = "completed"
                                task.output_image_path = image_url
                                task.error_message = None
                                task.completed_at = datetime.now()

                                # 更新processing_log
                                if task.processing_log:
                                    try:
                                        api_info = json.loads(task.processing_log)
                                        api_info["result_image"] = image_url
                                        api_info["result_data"] = result_data
                                        task.processing_log = json.dumps(
                                            api_info, ensure_ascii=False
                                        )
                                    except Exception:
                                        pass

                                # 清除预计完成时间（任务已完成）
                                task.estimated_completion_time = None

                                # 检查该订单的所有AI任务是否都已完成
                                if task.order_id and task.order_id > 0:
                                    try:
                                        from sqlalchemy import func

                                        Order = test_server_module.Order

                                        # 查询该订单的所有AI任务
                                        all_tasks = AITask.query.filter_by(
                                            order_id=task.order_id
                                        ).all()
                                        # 过滤掉失败和取消的任务，只统计有效任务
                                        valid_tasks = [
                                            t
                                            for t in all_tasks
                                            if t.status not in ["failed", "cancelled"]
                                        ]
                                        completed_tasks = [
                                            t
                                            for t in valid_tasks
                                            if t.status == "completed" and t.output_image_path
                                        ]

                                        # 如果所有有效任务都已完成，更新订单状态为"待选片"
                                        if len(valid_tasks) > 0 and len(completed_tasks) == len(
                                            valid_tasks
                                        ):
                                            order = Order.query.get(task.order_id)
                                            if order and order.status in [
                                                "ai_processing",
                                                "retouching",
                                                "shooting",
                                                "processing",
                                            ]:
                                                old_status = order.status
                                                order.status = "pending_selection"  # 待选片
                                                logger.info(
                                                    f"✅ 订单 {order.order_number} 所有AI任务已完成 ({len(completed_tasks)}/{len(valid_tasks)})，状态已更新为: pending_selection (从 {old_status} 更新)"
                                                )
                                            elif order:
                                                logger.info(
                                                    f"ℹ️ 订单 {order.order_number} 所有AI任务已完成，但当前状态是 {order.status}，不更新"
                                                )
                                    except Exception as e:
                                        logger.warning("检查订单状态失败: {str(e)}")
                                        import traceback

                                        traceback.print_exc()

                                db.session.commit()  # 提交时包含订单状态更新
                                updated_count += 1
                                logger.info(
                                    f"✅ 后台轮询：任务 {task.id} 状态已更新为已完成，图片URL: {image_url}"
                                )

                                # 自动下载图片（download_api_result_image内部已包含缩略图生成）
                                try:
                                    from app.routes.ai import download_api_result_image

                                    local_path = download_api_result_image(
                                        image_url,
                                        task.comfyui_prompt_id or str(task.id),
                                        test_server_module.app,
                                    )
                                    if local_path:
                                        task.output_image_path = local_path
                                        db.session.commit()
                                        logger.info(
                                            f"✅ 任务 {task.id} 结果图已下载到本地: {local_path} (缩略图已自动生成)"
                                        )
                                except Exception as download_error:
                                    logger.warning("下载图片失败: {str(download_error)}")

                            elif status in ["failed", "error"]:
                                # 关键修复：GRSAI格式错误信息提取（与recheck_api_task_result保持一致）
                                # GRSAI的错误信息在 data.error 中，如 "google gemini timeout..."
                                # RunningHub 的错误信息在 errorMessage 字段中
                                logger.info(
                                    f"🔍 [轮询] 任务 {task.id} 检测到失败状态: status={status}"
                                )
                                error_msg = None

                                # 关键修复：优先检查 RunningHub 的 errorMessage 字段
                                if isinstance(result_data, dict):
                                    # RunningHub 新格式：errorMessage 在根级别
                                    if "errorMessage" in result_data:
                                        error_msg = result_data.get("errorMessage")
                                        logger.info(
                                            f"🔍 [轮询] 从 RunningHub errorMessage 字段提取错误信息: {error_msg}"
                                        )

                                    # 检查data字段中的error（GRSAI格式，优先，因为GRSAI的错误信息在这里）
                                    if (
                                        not error_msg
                                        and "data" in result_data
                                        and isinstance(result_data.get("data"), dict)
                                    ):
                                        data = result_data.get("data")
                                        # 关键修复：即使code=0，如果status是failed，也要提取错误信息
                                        if data.get("status") == "failed":
                                            error_msg = (
                                                data.get("error")
                                                or data.get("error_message")
                                                or data.get("failure_reason")
                                            )
                                            logger.info(
                                                f"🔍 [轮询] 从data字段提取错误信息: {error_msg}"
                                            )

                                    # 检查根级别的error
                                    if not error_msg:
                                        error_obj = result_data.get("error")
                                        if isinstance(error_obj, dict):
                                            error_msg = error_obj.get("message") or error_obj.get(
                                                "error"
                                            )
                                        elif isinstance(error_obj, str):
                                            error_msg = error_obj

                                    # 如果还没有，使用msg字段（但注意：GRSAI的msg可能是"success"即使任务失败）
                                    if not error_msg:
                                        msg = result_data.get("msg") or result_data.get("message")
                                        if msg and msg.lower() != "success":
                                            error_msg = msg

                                if not error_msg:
                                    error_msg = "任务失败（未提供具体错误信息）"

                                logger.error("[轮询] 提取到的错误信息: {error_msg}")

                                # 检查是否应该自动重试
                                should_retry = False
                                next_api_config = None

                                # 从processing_log中获取API配置信息
                                api_info = {}
                                if task.processing_log:
                                    try:
                                        api_info = json.loads(task.processing_log)
                                    except Exception:
                                        pass

                                current_api_config_id = api_info.get("api_config_id")
                                if current_api_config_id:
                                    # 关键修复：检查是否标记为不应重试（避免因为网络中断等问题重复请求）
                                    if api_info.get("should_not_retry") or api_info.get(
                                        "connection_closed_but_request_sent"
                                    ):
                                        logger.warning(
                                            "[自动重试] 任务 {task.id} 标记为不应重试（连接断开但请求可能已发送），跳过自动重试"
                                        )
                                        should_retry = False
                                    else:
                                        # 检查当前API配置是否启用了重试
                                        current_api_config = APIProviderConfig.query.get(
                                            current_api_config_id
                                        )
                                        if current_api_config and current_api_config.enable_retry:
                                            # 关键修复：禁止SSL和UNIR级别的重试
                                            config_name_upper = (
                                                current_api_config.name.upper()
                                                if current_api_config.name
                                                else ""
                                            )
                                            if (
                                                "SSL" in config_name_upper
                                                or "UNIR" in config_name_upper
                                            ):
                                                logger.warning(
                                                    "[自动重试] 任务 {task.id} 当前配置是SSL/UNIR级别，禁止重试: {current_api_config.name}"
                                                )
                                                should_retry = False
                                            else:
                                                # 获取已尝试的API配置ID列表
                                                retried_ids = api_info.get(
                                                    "retried_api_config_ids", []
                                                )
                                                if not isinstance(retried_ids, list):
                                                    retried_ids = []

                                                # 关键修复：检查当前配置是否已经重试过（一个服务商仅重试一次）
                                                if current_api_config_id in retried_ids:
                                                    logger.warning(
                                                        "[自动重试] 任务 {task.id} 当前配置 {current_api_config.name} (ID: {current_api_config_id}) 已经重试过，不再重试"
                                                    )
                                                    should_retry = False
                                                else:
                                                    # 检查重试次数（最多重试3次）
                                                    max_retry_count = 3
                                                    if task.retry_count < max_retry_count:
                                                        # 获取下一个可用的API配置
                                                        from app.services.ai_provider_service import (
                                                            get_next_retry_api_config,
                                                        )

                                                        next_api_config = get_next_retry_api_config(
                                                            current_api_config_id=current_api_config_id,
                                                            retried_ids=retried_ids,
                                                            db=db,
                                                            APIProviderConfig=APIProviderConfig,
                                                        )

                                                        if next_api_config:
                                                            # 关键修复：检查下一个配置是否已经重试过（一个服务商仅重试一次）
                                                            if next_api_config.id in retried_ids:
                                                                logger.warning(
                                                                    "[自动重试] 任务 {task.id} 下一个配置 {next_api_config.name} (ID: {next_api_config.id}) 已经重试过，跳过"
                                                                )
                                                                should_retry = False
                                                            else:
                                                                should_retry = True
                                                                logger.info(
                                                                    f"🔄 [自动重试] 任务 {task.id} 失败，将使用下一个API配置重试"
                                                                )
                                                                logger.info(
                                                                    f"   - 当前配置: {current_api_config.name} (ID: {current_api_config_id})"
                                                                )
                                                                logger.info(
                                                                    f"   - 下一个配置: {next_api_config.name} (ID: {next_api_config.id})"
                                                                )
                                                                logger.info(
                                                                    f"   - 已尝试的配置: {retried_ids}"
                                                                )
                                                                logger.info(
                                                                    f"   - 当前重试次数: {task.retry_count}/{max_retry_count}"
                                                                )

                                if should_retry and next_api_config:
                                    # 自动重试：使用新的API配置重新创建任务
                                    try:
                                        # 从processing_log中提取原始任务参数
                                        original_prompt = api_info.get("prompt", "")
                                        original_image_size = api_info.get("image_size", "1K")
                                        original_aspect_ratio = api_info.get("aspect_ratio", "auto")
                                        original_uploaded_images = api_info.get(
                                            "uploaded_images", []
                                        )

                                        # 从request_params中提取upload_config（如果存在）
                                        upload_config = None
                                        request_params = api_info.get("request_params", {})
                                        if request_params and isinstance(request_params, dict):
                                            # upload_config可能保存在request_params中
                                            upload_config = request_params.get("upload_config")

                                        # 从任务中获取style_image_id
                                        style_image_id = task.style_image_id

                                        if not style_image_id:
                                            logger.warning(
                                                "[自动重试] 任务 {task.id} 没有style_image_id，无法重试"
                                            )
                                            should_retry = False
                                        else:
                                            # 更新已尝试的API配置ID列表
                                            if current_api_config_id not in retried_ids:
                                                retried_ids.append(current_api_config_id)

                                            # 关键修复：确保当前配置ID已添加到已尝试列表（一个服务商仅重试一次）
                                            if current_api_config_id not in retried_ids:
                                                retried_ids.append(current_api_config_id)

                                            # 关键修复：确保下一个配置ID也添加到已尝试列表（避免重复重试）
                                            if next_api_config.id not in retried_ids:
                                                retried_ids.append(next_api_config.id)

                                            # 更新任务的retry_count
                                            task.retry_count += 1

                                            # 更新processing_log，标记为正在重试
                                            api_info["retried_api_config_ids"] = retried_ids
                                            api_info["retry_count"] = task.retry_count
                                            api_info["retry_error"] = error_msg
                                            api_info["retry_at"] = datetime.now().isoformat()
                                            api_info["retry_api_config_id"] = next_api_config.id
                                            api_info["retry_api_config_name"] = next_api_config.name

                                            # 关键修复：在notes字段中记录重试信息
                                            # 注意：task.retry_count 已经在上面增加了1，所以这里直接使用
                                            retry_note = f"【自动重试第{task.retry_count}次】从 {current_api_config.name} 切换到 {next_api_config.name}"

                                            import re

                                            if task.notes:
                                                # 检查是否已经有重试记录
                                                if "【自动重试" in task.notes:
                                                    # 如果已有重试记录，追加新的重试记录（支持多次重试）
                                                    # 关键修复：追加而不是替换，这样可以显示所有重试历史
                                                    task.notes = f"{task.notes}\n{retry_note}"
                                                    logger.info(
                                                        f"✅ [自动重试] 已追加重试记录到notes: {retry_note}"
                                                    )
                                                else:
                                                    # 如果没有重试记录，添加新的
                                                    task.notes = f"{task.notes}\n{retry_note}"
                                                    logger.info(
                                                        f"✅ [自动重试] 已添加重试记录到notes: {retry_note}"
                                                    )
                                            else:
                                                task.notes = retry_note
                                                logger.info(
                                                    f"✅ [自动重试] 已创建notes并添加重试记录: {retry_note}"
                                                )

                                            # 打印当前notes内容用于调试
                                            logger.info(
                                                f"📝 [自动重试] 任务 {task.id} 当前notes内容: {task.notes}"
                                            )

                                            # 重置任务状态为pending，准备重试
                                            task.status = "pending"
                                            task.error_message = f"自动重试中（第{task.retry_count}次，使用{next_api_config.name}）: {error_msg[:150]}"
                                            task.completed_at = None
                                            task.comfyui_prompt_id = None  # 清除旧的API任务ID

                                            # 更新processing_log中的api_config_id为新配置
                                            api_info["api_config_id"] = next_api_config.id
                                            api_info["api_config_name"] = next_api_config.name
                                            task.processing_log = json.dumps(
                                                api_info, ensure_ascii=False
                                            )

                                            db.session.commit()

                                            logger.info(
                                                f"🔄 [自动重试] 任务 {task.id} 已重置为pending状态，准备使用新配置 {next_api_config.name} 重试"
                                            )
                                            logger.info(
                                                f"   - 原始参数: prompt={original_prompt[:50]}, size={original_image_size}, ratio={original_aspect_ratio}"
                                            )
                                            logger.info(
                                                f"   - 图片数量: {len(original_uploaded_images) if original_uploaded_images else 0}"
                                            )

                                            # 调用create_api_task重新创建任务（使用新的API配置）
                                            # 注意：这里不创建新任务，而是直接更新当前任务
                                            from app.services.ai_provider_service import (
                                                create_api_task,
                                            )

                                            # 设置测试订单信息（用于create_api_task）
                                            create_api_task._test_order_id = task.order_id
                                            create_api_task._test_order_number = task.order_number

                                            # 重新创建任务（create_api_task会自动获取StyleImage和StyleCategory等模型）
                                            retry_success, retry_task, retry_error = (
                                                create_api_task(
                                                    style_image_id=style_image_id,
                                                    prompt=original_prompt,
                                                    image_size=original_image_size,
                                                    aspect_ratio=original_aspect_ratio,
                                                    uploaded_images=original_uploaded_images,
                                                    upload_config=upload_config,
                                                    api_config_id=next_api_config.id,
                                                    db=db,
                                                    AITask=AITask,
                                                    APITemplate=None,  # 会从style_image_id自动获取
                                                    APIProviderConfig=APIProviderConfig,
                                                    StyleImage=None,  # 会从test_server自动获取
                                                    StyleCategory=None,  # 会从test_server自动获取
                                                )
                                            )

                                            if retry_success and retry_task:
                                                # 关键：不创建新任务，而是更新当前任务的信息
                                                # 将新任务的API信息合并到当前任务
                                                if retry_task.processing_log:
                                                    try:
                                                        retry_api_info = json.loads(
                                                            retry_task.processing_log
                                                        )
                                                        # 更新当前任务的API信息
                                                        new_api_task_id = (
                                                            retry_task.comfyui_prompt_id
                                                        )
                                                        task.comfyui_prompt_id = new_api_task_id
                                                        task.status = retry_task.status
                                                        task.error_message = None

                                                        # 关键修复：更新notes字段中的T8_API_TASK_ID（轮询时优先使用）
                                                        # 注意：必须保留重试记录，不能覆盖
                                                        if new_api_task_id:
                                                            import re

                                                            if (
                                                                task.notes
                                                                and "T8_API_TASK_ID:" in task.notes
                                                            ):
                                                                # 替换旧的T8_API_TASK_ID（匹配格式：T8_API_TASK_ID:xxx 或 T8_API_TASK_ID:xxx | ...）
                                                                # 关键修复：只替换T8_API_TASK_ID部分，保留所有重试记录
                                                                old_notes = task.notes
                                                                task.notes = re.sub(
                                                                    r"T8_API_TASK_ID:[^\s|]+",
                                                                    f"T8_API_TASK_ID:{new_api_task_id}",
                                                                    task.notes,
                                                                )
                                                                logger.info(
                                                                    f"✅ [自动重试] 已更新notes中的T8_API_TASK_ID（保留重试记录）: {old_notes} -> {task.notes}"
                                                                )
                                                            else:
                                                                # 如果没有notes或没有T8_API_TASK_ID，添加新的
                                                                # 关键修复：如果notes中已有重试记录，在开头添加T8_API_TASK_ID，保留重试记录
                                                                if task.notes:
                                                                    # 检查是否已有重试记录
                                                                    if "【自动重试" in task.notes:
                                                                        # 如果有重试记录，在开头添加T8_API_TASK_ID，保留重试记录
                                                                        task.notes = f"T8_API_TASK_ID:{new_api_task_id} | {task.notes}"
                                                                    else:
                                                                        task.notes = f"T8_API_TASK_ID:{new_api_task_id} | {task.notes}"
                                                                else:
                                                                    task.notes = f"T8_API_TASK_ID:{new_api_task_id}"
                                                                logger.info(
                                                                    f"✅ [自动重试] 已添加notes中的T8_API_TASK_ID: {new_api_task_id}"
                                                                )
                                                            logger.info(
                                                                f"📝 [自动重试] 任务 {task.id} 更新后的notes内容: {task.notes}"
                                                            )
                                                            # 确保立即刷新，让数据库更新生效
                                                            db.session.flush()

                                                        # 合并processing_log
                                                        api_info.update(
                                                            {
                                                                "api_task_id": retry_api_info.get(
                                                                    "api_task_id"
                                                                )
                                                                or new_api_task_id,
                                                                "task_id": retry_api_info.get(
                                                                    "task_id"
                                                                )
                                                                or new_api_task_id,
                                                                "id": retry_api_info.get("id")
                                                                or new_api_task_id,
                                                                "original_response": retry_api_info.get(
                                                                    "original_response"
                                                                ),
                                                                "response_data": retry_api_info.get(
                                                                    "response_data"
                                                                ),
                                                                "response_status": retry_api_info.get(
                                                                    "response_status"
                                                                ),
                                                            }
                                                        )
                                                        task.processing_log = json.dumps(
                                                            api_info, ensure_ascii=False
                                                        )

                                                        # 关键修复：确保notes字段更新后立即提交，让轮询能获取到新的任务ID
                                                        db.session.flush()  # 先刷新，确保notes更新到数据库

                                                        # 删除重试创建的新任务（因为我们已经更新了原任务）
                                                        db.session.delete(retry_task)

                                                        db.session.commit()

                                                        logger.info(
                                                            f"✅ [自动重试] 任务 {task.id} 已使用新配置 {next_api_config.name} 重新提交，API任务ID: {task.comfyui_prompt_id}"
                                                        )
                                                        logger.info(
                                                            f"   - notes字段: {task.notes[:100] if task.notes else 'None'}"
                                                        )
                                                        logger.info(
                                                            f"   - comfyui_prompt_id: {task.comfyui_prompt_id}"
                                                        )
                                                        updated_count += 1
                                                    except Exception as merge_error:
                                                        logger.warning(
                                                            "[自动重试] 合并任务信息失败: {str(merge_error)}"
                                                        )
                                                        # 如果合并失败，保留新任务，标记原任务为失败
                                                        task.status = "failed"
                                                        task.error_message = f"自动重试成功但合并信息失败: {str(merge_error)[:200]}"
                                                        task.completed_at = datetime.now()
                                                        db.session.commit()
                                                        updated_count += 1
                                                else:
                                                    # 新任务没有processing_log，标记原任务为失败
                                                    task.status = "failed"
                                                    task.error_message = (
                                                        "自动重试失败: 新任务没有processing_log"
                                                    )
                                                    task.completed_at = datetime.now()
                                                    db.session.commit()
                                                    logger.error(
                                                        "[自动重试] 任务 {task.id} 重试失败: 新任务没有processing_log"
                                                    )
                                                    updated_count += 1
                                            else:
                                                # 重试创建任务失败，标记原任务为最终失败
                                                task.status = "failed"
                                                task.error_message = (
                                                    f"自动重试失败: {retry_error or '未知错误'}"
                                                )
                                                task.completed_at = datetime.now()
                                                db.session.commit()
                                                logger.error(
                                                    "[自动重试] 任务 {task.id} 重试创建失败: {retry_error}"
                                                )
                                                updated_count += 1
                                    except Exception as retry_error:
                                        # 重试过程中出错，标记任务为最终失败
                                        import traceback

                                        error_trace = traceback.format_exc()
                                        logger.error(
                                            "[自动重试] 任务 {task.id} 重试过程出错: {str(retry_error)}"
                                        )
                                        logger.info(error_trace)

                                        task.status = "failed"
                                        task.error_message = (
                                            f"自动重试失败: {str(retry_error)[:200]}"
                                        )
                                        task.completed_at = datetime.now()
                                        db.session.commit()
                                        updated_count += 1

                                if not should_retry:
                                    # 不重试或无法重试，标记为最终失败
                                    task.status = "failed"
                                    task.error_message = str(error_msg)[:500]
                                    task.completed_at = datetime.now()

                                    # 更新processing_log
                                    if task.processing_log:
                                        try:
                                            api_info = json.loads(task.processing_log)
                                            api_info["result_data"] = result_data
                                            task.processing_log = json.dumps(
                                                api_info, ensure_ascii=False
                                            )
                                        except Exception:
                                            pass

                                    db.session.commit()
                                    updated_count += 1
                                    logger.info(
                                        f"✅ 后台轮询：任务 {task.id} 状态已更新为失败，错误信息: {error_msg}"
                                    )

                    except Exception as e:
                        logger.warning("轮询任务 {task.id} 状态失败: {str(e)}")
                        continue

                except Exception as e:
                    logger.warning("处理任务 {task.id} 时出错: {str(e)}")
                    continue

            return updated_count

    except Exception as e:
        logger.error("轮询处理中的任务失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return 0


def start_ai_task_polling_service():
    """启动AI任务状态轮询服务"""

    def polling_loop():
        loop_count = 0
        has_active_tasks = False  # 标记是否有活跃任务
        while True:
            try:
                loop_count += 1
                polling_interval = 10  # 默认值：无活跃任务时每10秒轮询一次
                polling_interval_with_tasks = 5  # 默认值：有活跃任务时每5秒轮询一次

                # 先检查是否有处理中的任务（用于判断是否需要轮询）
                processing_ai_tasks = 0
                processing_meitu_tasks = 0
                try:
                    import sys

                    if "test_server" in sys.modules:
                        test_server_module = sys.modules["test_server"]
                        app = test_server_module.app
                        db = test_server_module.db
                        AITask = test_server_module.AITask
                        MeituAPICallLog = test_server_module.MeituAPICallLog

                        # 必须在应用上下文中执行数据库查询
                        with app.app_context():
                            # 检查是否有处理中的AI任务
                            processing_ai_tasks = AITask.query.filter(
                                AITask.status.in_(["pending", "processing"])
                            ).count()

                            # 检查是否有处理中的美图API任务
                            processing_meitu_tasks = MeituAPICallLog.query.filter(
                                MeituAPICallLog.status == "pending"
                            ).count()

                            has_active_tasks = processing_ai_tasks > 0 or processing_meitu_tasks > 0

                            # 调试日志：每5次循环输出一次任务检测结果（更频繁，便于调试）
                            if loop_count % 5 == 0:
                                logger.info(
                                    f"🔍 [轮询检测] 检测到 {processing_ai_tasks} 个AI任务, {processing_meitu_tasks} 个美图任务, 是否有活跃任务: {has_active_tasks}"
                                )
                                if processing_ai_tasks > 0:
                                    # 显示前3个任务的详情
                                    try:
                                        from datetime import datetime

                                        recent_tasks = (
                                            AITask.query.filter(
                                                AITask.status.in_(["pending", "processing"])
                                            )
                                            .order_by(AITask.created_at.desc())
                                            .limit(3)
                                            .all()
                                        )
                                        for t in recent_tasks:
                                            age_seconds = (
                                                (datetime.now() - t.created_at).total_seconds()
                                                if t.created_at
                                                else 0
                                            )
                                            logger.info(
                                                f"   - 任务 {t.id}: 订单号={t.order_number}, 状态={t.status}, 创建于{age_seconds:.1f}秒前"
                                            )
                                    except Exception as debug_e:
                                        logger.info(f"   ⚠️ 获取任务详情失败: {debug_e}")

                        # 调试日志：每5次循环输出一次任务检测结果（更频繁，便于调试）
                        if loop_count % 5 == 0:
                            logger.info(
                                f"🔍 [轮询检测] 检测到 {processing_ai_tasks} 个AI任务, {processing_meitu_tasks} 个美图任务, 是否有活跃任务: {has_active_tasks}"
                            )
                            if processing_ai_tasks > 0:
                                # 显示前3个任务的详情
                                try:
                                    from datetime import datetime

                                    recent_tasks = (
                                        AITask.query.filter(
                                            AITask.status.in_(["pending", "processing"])
                                        )
                                        .order_by(AITask.created_at.desc())
                                        .limit(3)
                                        .all()
                                    )
                                    for t in recent_tasks:
                                        age_seconds = (
                                            (datetime.now() - t.created_at).total_seconds()
                                            if t.created_at
                                            else 0
                                        )
                                        logger.info(
                                            f"   - 任务 {t.id}: 订单号={t.order_number}, 状态={t.status}, 创建于{age_seconds:.1f}秒前"
                                        )
                                except Exception as debug_e:
                                    logger.info(f"   ⚠️ 获取任务详情失败: {debug_e}")
                except Exception as e:
                    has_active_tasks = False
                    # 输出错误信息以便调试
                    if loop_count % 5 == 0:
                        logger.warning("[轮询检测] 检测任务时出错: {e}")
                        import traceback

                        traceback.print_exc()

                # 只有在有活跃任务时才执行轮询
                if has_active_tasks:
                    # 输出轮询开始信息（每次轮询都输出，便于调试）
                    logger.info(
                        f"🔄 [轮询服务] 开始轮询... (检测到 {processing_ai_tasks} 个AI任务, {processing_meitu_tasks} 个美图任务)"
                    )

                    # 轮询AI任务（云端API服务商）
                    updated_count = poll_processing_tasks()

                    # 轮询美图API任务
                    meitu_updated_count = poll_meitu_api_tasks()

                    # 检查是否有待处理的任务
                    has_pending_tasks = updated_count > 0 or meitu_updated_count > 0

                    # 输出轮询结果
                    if updated_count > 0:
                        logger.info(
                            f"✅ [AI轮询] AI任务状态轮询完成，更新了 {updated_count} 个任务"
                        )
                    else:
                        logger.info(
                            "ℹ️ [AI轮询] 轮询完成，本次未更新任务（任务可能还在处理中或等待轮询条件）"
                        )

                    if meitu_updated_count > 0:
                        logger.info(
                            f"✅ [美图轮询] 美图API任务状态轮询完成，更新了 {meitu_updated_count} 个任务"
                        )

                    # 如果有活跃任务，每6次循环（约30秒）输出一次状态
                    if loop_count % 6 == 0:
                        logger.info(
                            f"💓 [轮询服务] 检测到活跃任务，轮询服务运行中... (已运行约 {loop_count * polling_interval_with_tasks} 秒)"
                        )
                        logger.info(
                            f"   - 当前有 {processing_ai_tasks} 个AI任务处理中, {processing_meitu_tasks} 个美图任务处理中"
                        )
                else:
                    # 没有活跃任务，不执行轮询，静默等待
                    updated_count = 0
                    meitu_updated_count = 0
                    has_pending_tasks = False
                    # 每30次循环（约5分钟）输出一次无任务状态
                    if loop_count % 30 == 0:
                        logger.info(
                            f"💤 [轮询服务] 当前无活跃任务，轮询服务等待中... (已等待约 {loop_count * polling_interval} 秒)"
                        )

                # 从数据库读取轮询配置（工作流任务）
                polling_interval = 10  # 默认值：无活跃任务时每10秒轮询一次
                polling_interval_with_tasks = 5  # 默认值：有活跃任务时每5秒轮询一次

                try:
                    import sys

                    if "test_server" in sys.modules:
                        test_server_module = sys.modules["test_server"]
                        PollingConfig = (
                            test_server_module.PollingConfig
                            if hasattr(test_server_module, "PollingConfig")
                            else None
                        )

                        if PollingConfig:
                            workflow_config = PollingConfig.query.filter_by(
                                task_type="workflow_task", is_active=True
                            ).first()
                            if workflow_config:
                                polling_interval = workflow_config.polling_interval or 10
                                polling_interval_with_tasks = (
                                    workflow_config.polling_interval_with_tasks or 5
                                )
                except Exception:
                    pass

                # 根据是否有活跃任务调整轮询间隔（使用配置的值）
                if has_active_tasks:
                    time.sleep(polling_interval_with_tasks)  # 有任务时使用配置的轮询间隔
                else:
                    time.sleep(polling_interval)  # 无任务时使用配置的轮询间隔
            except Exception as e:
                logger.error("AI任务状态轮询服务异常: {e}")
                import traceback

                traceback.print_exc()
                time.sleep(60)  # 出错后等待1分钟再重试

    # 在后台线程中运行
    polling_thread = threading.Thread(target=polling_loop, daemon=True)
    polling_thread.start()
    logger.info("🚀 AI任务状态自动轮询服务已启动")
    logger.info("   - 轮询条件：任务状态为pending或processing")
    logger.info("   - 轮询配置：从数据库PollingConfig读取（工作流任务）")
    logger.info("   - 提示：可在轮询配置页面修改轮询间隔和等待时间")


def init_ai_task_polling_service():
    """初始化AI任务状态轮询服务"""
    start_ai_task_polling_service()
