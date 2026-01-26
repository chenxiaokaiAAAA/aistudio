#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复任务notes字段中的T8_API_TASK_ID
用于修复重试后notes字段未正确更新的问题
"""

import os
import sys
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from start import app
from app.models import db, AITask

def fix_task_notes(task_id, new_api_task_id):
    """修复指定任务的notes字段"""
    with app.app_context():
        task = AITask.query.get(task_id)
        if not task:
            print(f"❌ 未找到任务: {task_id}")
            return False
        
        print(f"📋 任务信息:")
        print(f"  - 任务ID: {task.id}")
        print(f"  - 订单号: {task.order_number}")
        print(f"  - 当前状态: {task.status}")
        print(f"  - 当前comfyui_prompt_id: {task.comfyui_prompt_id}")
        print(f"  - 当前notes: {task.notes}")
        
        # 更新notes字段
        if task.notes and 'T8_API_TASK_ID:' in task.notes:
            # 替换旧的T8_API_TASK_ID
            old_notes = task.notes
            task.notes = re.sub(r'T8_API_TASK_ID:[^\s|]+', f'T8_API_TASK_ID:{new_api_task_id}', task.notes)
            print(f"✅ 已更新notes: {old_notes} -> {task.notes}")
        else:
            # 添加新的T8_API_TASK_ID
            if task.notes:
                task.notes = f"T8_API_TASK_ID:{new_api_task_id} | {task.notes}"
            else:
                task.notes = f"T8_API_TASK_ID:{new_api_task_id}"
            print(f"✅ 已添加notes: {task.notes}")
        
        # 更新comfyui_prompt_id
        if task.comfyui_prompt_id != new_api_task_id:
            print(f"✅ 已更新comfyui_prompt_id: {task.comfyui_prompt_id} -> {new_api_task_id}")
            task.comfyui_prompt_id = new_api_task_id
        
        # 更新processing_log中的api_task_id
        if task.processing_log:
            import json
            try:
                api_info = json.loads(task.processing_log)
                api_info['api_task_id'] = new_api_task_id
                api_info['task_id'] = new_api_task_id
                api_info['id'] = new_api_task_id
                task.processing_log = json.dumps(api_info, ensure_ascii=False)
                print(f"✅ 已更新processing_log中的api_task_id")
            except Exception as e:
                print(f"⚠️ 更新processing_log失败: {str(e)}")
        
        db.session.commit()
        print(f"✅ 任务 {task_id} 已修复完成")
        return True

def cleanup_old_tasks(minutes=15):
    """清理超过指定分钟数的无效任务"""
    from datetime import datetime, timedelta
    
    with app.app_context():
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        old_tasks = AITask.query.filter(
            AITask.status.in_(['pending', 'processing']),
            AITask.created_at < cutoff_time
        ).all()
        
        if not old_tasks:
            print(f"✅ 没有发现超过{minutes}分钟的无效任务")
            return 0
        
        print(f"⚠️ 发现 {len(old_tasks)} 个超过{minutes}分钟的无效任务，开始清理...")
        
        cleaned_count = 0
        for task in old_tasks:
            age_minutes = (datetime.now() - task.created_at).total_seconds() / 60 if task.created_at else 0
            print(f"  - 任务 {task.id} (order: {task.order_number}): 状态={task.status}, 创建于{age_minutes:.1f}分钟前")
            
            # 标记为失败
            task.status = 'failed'
            task.error_message = f"任务超时：超过{minutes}分钟仍未完成，已自动清理"
            task.completed_at = datetime.now()
            cleaned_count += 1
        
        db.session.commit()
        print(f"✅ 已清理 {cleaned_count} 个无效任务")
        return cleaned_count

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  修复任务notes: python scripts/fix_task_notes.py fix <task_id> <new_api_task_id>")
        print("  清理历史任务: python scripts/fix_task_notes.py cleanup [minutes=15]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'fix':
        if len(sys.argv) < 4:
            print("❌ 缺少参数: python scripts/fix_task_notes.py fix <task_id> <new_api_task_id>")
            sys.exit(1)
        task_id = int(sys.argv[2])
        new_api_task_id = sys.argv[3]
        fix_task_notes(task_id, new_api_task_id)
    elif command == 'cleanup':
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        cleanup_old_tasks(minutes)
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)
