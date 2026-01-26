#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询任务状态
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入应用
from start import app
from app.models import db, AITask, APIProviderConfig

def query_task_status(task_id_str):
    """查询任务状态"""
    with app.app_context():
        print(f"=== 查询任务状态: {task_id_str} ===\n")
        
        # 尝试多种方式查找任务
        task = None
        
        # 1. 尝试作为comfyui_prompt_id查找
        task = AITask.query.filter_by(comfyui_prompt_id=task_id_str).first()
        if task:
            print(f"✅ 通过comfyui_prompt_id找到任务")
        
        # 2. 尝试在notes中查找（T8_API_TASK_ID格式）
        if not task:
            tasks = AITask.query.filter(AITask.notes.contains(f"T8_API_TASK_ID:{task_id_str}")).all()
            if tasks:
                task = tasks[0]
                print(f"✅ 通过notes找到任务")
        
        # 3. 尝试在processing_log中查找
        if not task:
            all_tasks = AITask.query.filter(AITask.processing_log.isnot(None)).all()
            for t in all_tasks:
                try:
                    api_info = json.loads(t.processing_log)
                    stored_task_id = api_info.get('api_task_id') or api_info.get('task_id') or api_info.get('taskId')
                    if stored_task_id and str(stored_task_id) == str(task_id_str):
                        task = t
                        print(f"✅ 在processing_log中找到任务")
                        break
                except:
                    continue
        
        # 4. 尝试作为数据库ID查找（如果全是数字）
        if not task:
            try:
                db_id = int(task_id_str)
                task = AITask.query.get(db_id)
                if task:
                    print(f"✅ 通过数据库ID找到任务: {db_id}")
            except ValueError:
                pass
        
        if not task:
            print(f"❌ 未找到任务: {task_id_str}")
            print("\n最近10个任务:")
            recent_tasks = AITask.query.order_by(AITask.created_at.desc()).limit(10).all()
            for t in recent_tasks:
                print(f"  - ID: {t.id}, comfyui_prompt_id: {t.comfyui_prompt_id}, status: {t.status}, order_number: {t.order_number}")
            return
        
        # 显示任务基本信息
        print(f"\n📋 任务基本信息:")
        print(f"  - 数据库ID: {task.id}")
        print(f"  - 任务状态: {task.status}")
        print(f"  - 订单号: {task.order_number}")
        print(f"  - 创建时间: {task.created_at}")
        print(f"  - 开始时间: {task.started_at}")
        print(f"  - 完成时间: {task.completed_at}")
        print(f"  - 预计完成时间: {task.estimated_completion_time}")
        print(f"  - comfyui_prompt_id: {task.comfyui_prompt_id}")
        print(f"  - 错误信息: {task.error_message}")
        print(f"  - 错误代码: {task.error_code}")
        print(f"  - 重试次数: {task.retry_count}")
        print(f"  - 输入图片: {task.input_image_path}")
        print(f"  - 输出图片: {task.output_image_path}")
        print(f"  - notes: {task.notes}")
        
        # 解析processing_log
        print(f"\n📝 处理日志 (processing_log):")
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                print(f"  - API配置ID: {api_info.get('api_config_id')}")
                print(f"  - API配置名称: {api_info.get('api_config_name')}")
                print(f"  - API任务ID: {api_info.get('api_task_id')}")
                print(f"  - 模型名称: {api_info.get('model_name')}")
                print(f"  - 提示词: {api_info.get('prompt', '')[:100]}")
                print(f"  - 图片尺寸: {api_info.get('image_size')}")
                print(f"  - 图片比例: {api_info.get('aspect_ratio')}")
                print(f"  - 重试次数: {api_info.get('retry_count', 0)}")
                print(f"  - 已尝试的配置ID: {api_info.get('retried_api_config_ids', [])}")
                if api_info.get('retry_error'):
                    print(f"  - 重试错误: {api_info.get('retry_error')}")
                if api_info.get('retry_at'):
                    print(f"  - 重试时间: {api_info.get('retry_at')}")
                if api_info.get('response_status'):
                    print(f"  - 响应状态码: {api_info.get('response_status')}")
                if api_info.get('api_call_error'):
                    print(f"  - API调用错误: {api_info.get('api_call_error')}")
                if api_info.get('connection_closed_but_request_sent'):
                    print(f"  - 连接断开但请求可能已发送: {api_info.get('connection_closed_but_request_sent')}")
                if api_info.get('should_not_retry'):
                    print(f"  - 不应重试标记: {api_info.get('should_not_retry')}")
                
                # 显示完整的processing_log（格式化）
                print(f"\n完整processing_log (JSON):")
                print(json.dumps(api_info, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"  ⚠️ 解析processing_log失败: {str(e)}")
                print(f"  原始内容: {task.processing_log[:500]}")
        else:
            print("  - 无processing_log")
        
        # 获取API配置信息
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                api_config_id = api_info.get('api_config_id')
                if api_config_id:
                    api_config = APIProviderConfig.query.get(api_config_id)
                    if api_config:
                        print(f"\n🔧 API配置信息:")
                        print(f"  - 配置名称: {api_config.name}")
                        print(f"  - API类型: {api_config.api_type}")
                        print(f"  - 是否启用: {api_config.is_active}")
                        print(f"  - 是否启用重试: {api_config.enable_retry}")
                        print(f"  - 是否同步API: {api_config.is_sync_api}")
                        print(f"  - 优先级: {api_config.priority}")
            except:
                pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
    else:
        task_id = 'cef1a065'
    
    query_task_status(task_id)
