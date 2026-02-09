# -*- coding: utf-8 -*-
"""
任务锁和并发控制工具
"""

import logging

logger = logging.getLogger(__name__)
import time
from functools import wraps

from sqlalchemy import select, update


def safe_update_task_status(task_id, new_status, db, AITask, check_status=None):
    """
    安全更新任务状态（使用数据库锁）

    Args:
        task_id: 任务ID
        new_status: 新状态
        db: 数据库实例
        AITask: AITask模型类
        check_status: 检查当前状态是否在允许列表中（防止状态回退）

    Returns:
        bool: 是否更新成功
    """
    try:
        # 使用悲观锁查询任务
        try:
            task = db.session.execute(
                select(AITask).where(AITask.id == task_id).with_for_update()
            ).scalar_one_or_none()
        except Exception:
            # 如果with_for_update不支持，使用普通查询
            task = AITask.query.get(task_id)

        if not task:
            return False

        # 检查状态转换是否合法
        if check_status and task.status not in check_status:
            # 当前状态不在允许列表中，不更新
            return False

        # 如果任务已完成或失败，不再更新
        if task.status in ["completed", "success", "failed", "cancelled"]:
            return False

        # 更新状态
        task.status = new_status
        db.session.commit()
        return True

    except Exception as e:
        logger.info(f"更新任务状态失败: {str(e)}")
        db.session.rollback()
        return False


def safe_get_task_with_lock(task_id, db, AITask):
    """
    安全获取任务（使用数据库锁）

    Args:
        task_id: 任务ID
        db: 数据库实例
        AITask: AITask模型类

    Returns:
        AITask对象或None
    """
    try:
        try:
            task = db.session.execute(
                select(AITask).where(AITask.id == task_id).with_for_update()
            ).scalar_one_or_none()
        except Exception:
            task = AITask.query.get(task_id)
        return task
    except Exception as e:
        logger.info(f"获取任务失败: {str(e)}")
        return None
