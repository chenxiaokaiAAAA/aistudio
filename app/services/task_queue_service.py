# -*- coding: utf-8 -*-
"""
任务队列服务 - 管理任务排队和处理
适用于10台设备、40-50个排队任务的场景
"""

import logging

logger = logging.getLogger(__name__)
import queue
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

# 任务队列配置（从数据库读取）
from app.utils.config_loader import get_int_config

# 全局变量
TASK_QUEUE = None  # 队列实例（会在启动时初始化）
WORKER_THREADS = []  # 工作线程列表
MAX_WORKERS = None  # 工作线程数（从数据库读取）
QUEUE_RUNNING = False  # 队列是否运行中


def _init_queue():
    """初始化队列（从数据库读取配置）"""
    global TASK_QUEUE, MAX_WORKERS
    if TASK_QUEUE is None:
        max_size = get_int_config("task_queue_max_size", 100)
        TASK_QUEUE = queue.Queue(maxsize=max_size)
        MAX_WORKERS = get_int_config("task_queue_workers", 3)
        logger.info(f"✅ 任务队列已初始化: 最大大小={max_size}, 工作线程数={MAX_WORKERS}")
    return TASK_QUEUE


# 任务处理统计
QUEUE_STATS = {
    "total_submitted": 0,
    "total_processed": 0,
    "total_failed": 0,
    "current_queue_size": 0,
    "last_processed_time": None,
}


def submit_task(task_type: str, task_data: Dict[str, Any], priority: int = 0) -> bool:
    """
    提交任务到队列

    Args:
        task_type: 任务类型 ('comfyui' 或 'api')
        task_data: 任务数据
        priority: 优先级（0=普通，1=高优先级）

    Returns:
        bool: 是否提交成功
    """
    # 检查队列是否运行，如果未运行则返回False，让调用方回退到直接调用模式
    if not QUEUE_RUNNING:
        logger.warning(
            "任务队列未启动（QUEUE_RUNNING=False），无法提交任务到队列，将回退到直接调用模式"
        )
        return False

    try:
        queue_instance = _init_queue()
        if queue_instance.full():
            logger.warning("任务队列已满（{queue_instance.qsize()}个任务），无法提交新任务")
            return False

        task_item = {
            "type": task_type,
            "data": task_data,
            "priority": priority,
            "submitted_at": datetime.now(),
            "task_id": task_data.get("task_id") or f"{task_type}_{int(time.time())}",
        }

        # 如果是高优先级任务，使用特殊标记（实际实现中可以使用PriorityQueue）
        queue_instance.put(task_item, block=False)
        QUEUE_STATS["total_submitted"] += 1
        QUEUE_STATS["current_queue_size"] = queue_instance.qsize()

        logger.info(f"✅ 任务已提交到队列: {task_item['task_id']} (队列大小: {TASK_QUEUE.qsize()})")
        return True

    except queue.Full:
        logger.error("任务队列已满，无法提交任务")
        return False
    except Exception as e:
        logger.error("提交任务到队列失败: {str(e)}")
        return False


def process_task_worker(worker_id: int):
    """
    任务处理工作线程

    Args:
        worker_id: 工作线程ID
    """
    logger.info(f"🚀 任务处理工作线程 {worker_id} 已启动")

    while QUEUE_RUNNING:
        try:
            # 从队列获取任务（超时1秒，避免阻塞）
            queue_instance = _init_queue()
            try:
                task_item = queue_instance.get(timeout=1)
            except queue.Empty:
                continue

            task_type = task_item["type"]
            task_data = task_item["data"]
            task_id = task_item["task_id"]

            logger.info(f"📦 工作线程 {worker_id} 开始处理任务: {task_id} (类型: {task_type})")

            try:
                # 根据任务类型调用不同的处理函数
                if task_type == "comfyui":
                    success = process_comfyui_task(task_data)
                elif task_type == "api":
                    success = process_api_task(task_data)
                else:
                    logger.warning("未知任务类型: {task_type}")
                    success = False

                if success:
                    QUEUE_STATS["total_processed"] += 1
                    logger.info(f"✅ 任务处理成功: {task_id}")
                else:
                    QUEUE_STATS["total_failed"] += 1
                    logger.error("任务处理失败: {task_id}")

            except Exception as e:
                QUEUE_STATS["total_failed"] += 1
                logger.error("处理任务异常: {task_id}, 错误: {str(e)}")
                import traceback

                traceback.print_exc()

            finally:
                # 标记任务完成
                queue_instance.task_done()
                QUEUE_STATS["current_queue_size"] = queue_instance.qsize()
                QUEUE_STATS["last_processed_time"] = datetime.now()

        except Exception as e:
            logger.error("工作线程 {worker_id} 异常: {str(e)}")
            time.sleep(1)  # 出错后等待1秒再继续

    logger.info(f"🛑 任务处理工作线程 {worker_id} 已停止")


def process_comfyui_task(task_data: Dict[str, Any]) -> bool:
    """
    处理ComfyUI任务

    Args:
        task_data: 任务数据

    Returns:
        bool: 是否处理成功
    """
    try:
        from app.services.workflow_service import create_ai_task

        order_id = task_data.get("order_id")
        logger.info(f"📦 开始处理ComfyUI任务，订单ID: {order_id}")

        # 获取应用实例（从test_server模块）
        app_instance = None
        import sys

        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            if hasattr(test_server_module, "app"):
                app_instance = test_server_module.app

        if not app_instance:
            logger.error("无法获取应用实例，无法处理ComfyUI任务，订单ID: {order_id}")
            return False

        # 在应用上下文中调用create_ai_task
        with app_instance.app_context():
            # 调用create_ai_task（内部已有防重复提交和限流机制）
            success, task, error_message = create_ai_task(
                order_id=order_id,
                style_category_id=task_data.get("style_category_id"),
                style_image_id=task_data.get("style_image_id"),
                order_image_id=task_data.get("order_image_id"),  # 支持指定处理哪张图片
                **task_data.get("kwargs", {}),
            )

            if success and task:
                logger.info(f"✅ ComfyUI任务处理成功，任务ID: {task.id}, 订单ID: {order_id}")
            elif success and not task:
                logger.warning("ComfyUI任务处理返回成功但任务对象为空，订单ID: {order_id}")
            else:
                logger.error("ComfyUI任务处理失败: {error_message}, 订单ID: {order_id}")

            return success and task is not None

    except Exception as e:
        logger.error("处理ComfyUI任务异常: {str(e)}, 订单ID: {task_data.get('order_id')}")
        import traceback

        traceback.print_exc()
        return False


def process_api_task(task_data: Dict[str, Any]) -> bool:
    """
    处理API任务

    Args:
        task_data: 任务数据

    Returns:
        bool: 是否处理成功
    """
    try:
        from app.services.ai_provider_service import create_api_task

        # 获取应用实例（从test_server模块）
        app_instance = None
        import sys

        if "test_server" in sys.modules:
            test_server_module = sys.modules["test_server"]
            if hasattr(test_server_module, "app"):
                app_instance = test_server_module.app

        if not app_instance:
            logger.error("无法获取应用实例，无法处理API任务")
            return False

        # 在应用上下文中调用create_api_task
        with app_instance.app_context():
            # 调用create_api_task（内部已有限流机制）
            success, task, error_message = create_api_task(
                style_image_id=task_data.get("style_image_id"),
                prompt=task_data.get("prompt"),
                image_size=task_data.get("image_size", "1K"),
                aspect_ratio=task_data.get("aspect_ratio", "auto"),
                uploaded_images=task_data.get("uploaded_images"),
                api_config_id=task_data.get("api_config_id"),
                **task_data.get("kwargs", {}),
            )

            return success

    except Exception as e:
        logger.error("处理API任务异常: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def start_task_queue():
    """启动任务队列服务"""
    global QUEUE_RUNNING, MAX_WORKERS

    if QUEUE_RUNNING:
        logger.warning("任务队列服务已在运行")
        return

    # 初始化队列和配置
    _init_queue()

    if MAX_WORKERS is None:
        MAX_WORKERS = get_int_config("task_queue_workers", 3)

    QUEUE_RUNNING = True

    # 启动工作线程
    for i in range(MAX_WORKERS):
        worker = threading.Thread(
            target=process_task_worker, args=(i + 1,), daemon=True, name=f"TaskWorker-{i + 1}"
        )
        worker.start()
        WORKER_THREADS.append(worker)
        logger.info(f"✅ 任务处理工作线程 {i + 1} 已启动")

    logger.info(f"🚀 任务队列服务已启动，工作线程数: {MAX_WORKERS}")


def stop_task_queue():
    """停止任务队列服务"""
    global QUEUE_RUNNING

    QUEUE_RUNNING = False

    # 等待所有任务完成
    queue_instance = _init_queue()
    queue_instance.join()

    logger.info("🛑 任务队列服务已停止")


def get_queue_stats() -> Dict[str, Any]:
    """
    获取队列统计信息

    Returns:
        dict: 队列统计信息
    """
    queue_instance = _init_queue()
    return {
        **QUEUE_STATS,
        "queue_size": queue_instance.qsize(),
        "queue_maxsize": queue_instance.maxsize,
        "is_running": QUEUE_RUNNING,
        "worker_count": len(WORKER_THREADS),
    }


def clear_queue():
    """清空任务队列（谨慎使用）"""
    queue_instance = _init_queue()
    while not queue_instance.empty():
        try:
            queue_instance.get_nowait()
            queue_instance.task_done()
        except queue.Empty:
            break

    logger.info("🗑️ 任务队列已清空")
