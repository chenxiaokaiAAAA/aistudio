#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询任务详细信息
用于调试任务失败原因
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_server import app, db, AITask, APIProviderConfig, APITemplate

def query_task(task_id_str):
    """查询任务详细信息"""
    with app.app_context():
        print(f"=== 查询任务: {task_id_str} ===\n")
        
        # 尝试多种方式查找任务
        task = None
        
        # 1. 如果包含 "-"，可能是 "数据库ID-UUID" 格式
        if '-' in task_id_str:
            parts = task_id_str.split('-', 1)
            if len(parts) == 2:
                try:
                    db_id = int(parts[0])
                    uuid_part = parts[1]
                    task = AITask.query.get(db_id)
                    if task:
                        print(f"✅ 通过数据库ID找到任务: {db_id}")
                        # 验证UUID部分是否匹配
                        if task.comfyui_prompt_id and uuid_part in task.comfyui_prompt_id:
                            print(f"✅ UUID部分匹配: {uuid_part}")
                        elif task.notes and uuid_part in task.notes:
                            print(f"✅ UUID在notes中: {uuid_part}")
                except ValueError:
                    pass
        
        # 2. 尝试作为完整的comfyui_prompt_id查找
        if not task:
            task = AITask.query.filter_by(comfyui_prompt_id=task_id_str).first()
            if task:
                print(f"✅ 通过comfyui_prompt_id找到任务")
        
        # 3. 尝试在notes中查找
        if not task:
            task = AITask.query.filter(AITask.notes.contains(task_id_str)).first()
            if task:
                print(f"✅ 通过notes找到任务")
        
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
                print(f"  - ID: {t.id}, comfyui_prompt_id: {t.comfyui_prompt_id}, status: {t.status}, notes: {t.notes[:50] if t.notes else 'None'}")
            return
        
        # 显示任务基本信息
        print(f"\n📋 任务基本信息:")
        print(f"  - 数据库ID: {task.id}")
        print(f"  - 任务状态: {task.status}")
        print(f"  - 订单号: {task.order_number}")
        print(f"  - 创建时间: {task.created_at}")
        print(f"  - 开始时间: {task.started_at}")
        print(f"  - 完成时间: {task.completed_at}")
        print(f"  - comfyui_prompt_id: {task.comfyui_prompt_id}")
        print(f"  - 错误信息: {task.error_message}")
        print(f"  - 错误代码: {task.error_code}")
        print(f"  - 重试次数: {task.retry_count}")
        print(f"  - notes: {task.notes}")
        
        # 解析processing_log
        print(f"\n📝 处理日志 (processing_log):")
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                print(json.dumps(api_info, ensure_ascii=False, indent=2))
                
                # 提取关键信息
                api_config_id = api_info.get('api_config_id')
                if api_config_id:
                    api_config = APIProviderConfig.query.get(api_config_id)
                    if api_config:
                        print(f"\n🔧 API配置信息:")
                        print(f"  - 配置名称: {api_config.name}")
                        print(f"  - API类型: {api_config.api_type}")
                        print(f"  - 主机地址: {api_config.hosts}")
                        print(f"  - 是否同步: {api_config.is_sync_api}")
                
                # 显示请求参数
                request_params = api_info.get('request_params')
                if request_params:
                    print(f"\n📤 请求参数:")
                    print(json.dumps(request_params, ensure_ascii=False, indent=2))
                
                # 显示响应数据
                response_data = api_info.get('response_data')
                if response_data:
                    print(f"\n📥 响应数据:")
                    if isinstance(response_data, str):
                        try:
                            response_data = json.loads(response_data)
                        except:
                            pass
                    print(json.dumps(response_data, ensure_ascii=False, indent=2))
                
            except Exception as e:
                print(f"⚠️ 解析processing_log失败: {str(e)}")
                print(f"原始内容: {task.processing_log[:500]}")
        else:
            print("  (无处理日志)")
        
        # 显示comfyui_response
        print(f"\n🎨 ComfyUI响应 (comfyui_response):")
        if task.comfyui_response:
            try:
                comfyui_data = json.loads(task.comfyui_response)
                print(json.dumps(comfyui_data, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"⚠️ 解析comfyui_response失败: {str(e)}")
                print(f"原始内容: {task.comfyui_response[:500]}")
        else:
            print("  (无ComfyUI响应)")
        
        # 分析失败原因
        print(f"\n🔍 失败原因分析:")
        if task.status == 'failed':
            if task.error_message:
                print(f"  - 错误信息: {task.error_message}")
            if task.error_code:
                print(f"  - 错误代码: {task.error_code}")
            
            # 检查是否有响应数据
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                    response_data = api_info.get('response_data')
                    if response_data:
                        if isinstance(response_data, str):
                            try:
                                response_data = json.loads(response_data)
                            except:
                                pass
                        
                        # RunningHub API 特殊处理
                        if isinstance(response_data, dict):
                            code = response_data.get('code')
                            msg = response_data.get('msg')
                            if code is not None:
                                print(f"  - API返回码: {code}")
                                if code != 0:
                                    print(f"  - API错误信息: {msg}")
                                    
                                    # 检查是否有节点错误
                                    if code == 433:  # 工作流验证失败
                                        print(f"  - 这是工作流验证失败，可能的原因:")
                                        print(f"    1. 节点参数配置错误")
                                        print(f"    2. 图片URL无效")
                                        print(f"    3. 工作流ID不存在")
                                        
                                        # 尝试解析node_errors
                                        if isinstance(msg, str):
                                            try:
                                                error_details = json.loads(msg)
                                                node_errors = error_details.get('node_errors', {})
                                                if node_errors:
                                                    print(f"  - 节点错误详情:")
                                                    for node_id, errors in node_errors.items():
                                                        print(f"    节点 {node_id}: {errors}")
                                            except:
                                                pass
                except:
                    pass
            
            # 检查是否有请求参数
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                    request_params = api_info.get('request_params')
                    if not request_params or (isinstance(request_params, dict) and len(request_params) == 0):
                        print(f"  ⚠️ 请求参数为空，可能是:")
                        print(f"    1. 任务创建时未正确设置参数")
                        print(f"    2. API模板配置有问题")
                        print(f"    3. 图片上传失败")
                except:
                    pass
        
        print(f"\n{'='*60}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python query_task_by_id.py <task_id>")
        print("示例: python query_task_by_id.py 15-655d1c4e-b6c6-4812-9d9d-69729b6664a7")
        sys.exit(1)
    
    task_id = sys.argv[1]
    query_task(task_id)
