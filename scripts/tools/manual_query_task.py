#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动查询GRSAI任务并下载图片
用于修复失败状态的任务
"""
import sys
import os
import json
import requests
from datetime import datetime

# 将项目根目录添加到Python路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 导入Flask应用和数据库模型
try:
    from test_server import app, db, AITask, APIProviderConfig
except ImportError:
    print("无法从test_server导入app, db, AITask, APIProviderConfig。请确保在项目根目录运行此脚本。")
    sys.exit(1)

# 配置要查询的任务ID
TASK_ID_TO_QUERY = "14-575b6c05-4c0d-4e10-95fc-821216ebc4da"

def manual_query_and_download(task_id):
    """手动查询任务并下载图片"""
    with app.app_context():
        print(f"=== 手动查询GRSAI任务: {task_id} ===\n")
        
        # 1. 查找任务（通过comfyui_prompt_id）
        task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
        if not task:
            # 尝试通过notes查找
            tasks = AITask.query.filter(AITask.notes.contains(f"T8_API_TASK_ID:{task_id}")).all()
            if tasks:
                task = tasks[0]
                print(f"✅ 通过notes找到任务: ID={task.id}")
            else:
                print(f"❌ 未找到任务，task_id: {task_id}")
                # 列出所有任务的comfyui_prompt_id
                all_tasks = AITask.query.order_by(AITask.created_at.desc()).limit(10).all()
                print(f"\n最近10个任务的comfyui_prompt_id:")
                for t in all_tasks:
                    print(f"  - 任务ID: {t.id}, comfyui_prompt_id: {t.comfyui_prompt_id}, notes: {t.notes[:50] if t.notes else 'None'}")
                return
        else:
            print(f"✅ 通过comfyui_prompt_id找到任务: ID={task.id}")
        
        print(f"   - 任务状态: {task.status}")
        print(f"   - 订单号: {task.order_number}")
        print(f"   - 创建时间: {task.created_at}")
        print(f"   - notes: {task.notes}")
        
        # 2. 获取API配置
        api_config = None
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                api_config_id = api_info.get('api_config_id')
                if api_config_id:
                    api_config = APIProviderConfig.query.get(api_config_id)
                    print(f"✅ 从processing_log获取到API配置ID: {api_config_id}")
            except Exception as e:
                print(f"⚠️ 解析processing_log失败: {str(e)}")
        
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config:
            print("❌ 未找到API配置，请在后台配置API服务商。")
            return
        
        print(f"✅ 使用API配置: {api_config.name}")
        
        # 3. 构建查询URL
        host = api_config.host_domestic or api_config.host_overseas
        if not host:
            print("❌ API Host未配置。")
            return
        
        result_endpoint = api_config.result_endpoint
        if not result_endpoint:
            # 根据draw_endpoint推断
            draw_endpoint = api_config.draw_endpoint or '/v1/draw/nano-banana'
            if '/v1/images/generations' in draw_endpoint or '/v1/images/tasks/' in draw_endpoint:
                result_endpoint = f'/v1/images/tasks/{task_id}'
            elif draw_endpoint.endswith('/edits'):
                result_endpoint = draw_endpoint + '/result'
            else:
                result_endpoint = '/v1/draw/result'
        
        result_url = host.rstrip('/') + result_endpoint
        print(f"\n📋 查询配置:")
        print(f"   - Host: {host}")
        print(f"   - Result Endpoint: {result_endpoint}")
        print(f"   - 完整URL: {result_url}")
        
        # 4. 设置请求头和代理
        headers = {
            "Authorization": f"Bearer {api_config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 禁用代理（国内服务商）
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        is_known_domestic_domain = host and any(domain in host.lower() for domain in [
            'grsai.dakka.com.cn', 'grsai-file.dakka.com.cn', 't8star.cn', 'ai.t8star.cn'
        ])
        
        if is_known_domestic_domain or api_config.host_domestic:
            proxies = {'http': None, 'https': None}
            print(f"✅ 禁用代理（国内服务商）")
        else:
            proxies = None
            print(f"ℹ️ 使用系统代理设置")
        
        # 5. 尝试多种查询格式
        print(f"\n🔄 开始查询任务状态...")
        
        # 判断是GET还是POST请求
        use_get_method = '/v1/images/tasks/' in result_endpoint
        
        response = None
        result_data = None
        
        if use_get_method:
            # GET请求
            print(f"📤 使用GET请求: {result_url}")
            try:
                response = requests.get(result_url, headers=headers, timeout=30, proxies=proxies)
                print(f"📥 响应状态码: {response.status_code}")
                if response.status_code == 200:
                    result_data = response.json()
                    print(f"✅ GET请求成功")
            except Exception as e:
                print(f"❌ GET请求失败: {str(e)}")
        else:
            # POST请求：尝试多种格式
            request_payloads = [
                {"Id": task_id},  # 参考bk-photo-v4：通用异步API格式（大写Id）
                {"task_id": task_id},  # nano-banana-edits格式（虽然不用了，但保留作为备选）
                {"id": task_id},  # 小写id格式
            ]
            
            for payload in request_payloads:
                try:
                    print(f"\n📤 尝试POST请求:")
                    print(f"   - URL: {result_url}")
                    print(f"   - 参数: {json.dumps(payload, ensure_ascii=False)}")
                    print(f"   - Headers: Authorization=Bearer {api_config.api_key[:20]}...")
                    
                    response = requests.post(result_url, json=payload, headers=headers, timeout=30, proxies=proxies)
                    
                    print(f"📥 响应状态码: {response.status_code}")
                    if response.status_code == 200:
                        result_data = response.json()
                        print(f"📥 响应内容（完整）:")
                        print(json.dumps(result_data, ensure_ascii=False, indent=2))
                        
                        # 检查是否成功
                        if isinstance(result_data, dict):
                            if result_data.get('code') == -22:
                                print(f"⚠️ 返回code=-22（任务不存在），尝试下一个格式")
                                continue
                            else:
                                print(f"✅ 使用参数 {payload} 查询成功")
                                break
                    else:
                        print(f"⚠️ HTTP错误: {response.status_code}，尝试下一个格式")
                        continue
                except Exception as e:
                    print(f"⚠️ 请求异常: {str(e)}，尝试下一个格式")
                    continue
        
        if not result_data:
            print(f"\n❌ 所有查询方式均失败")
            return
        
        # 6. 解析响应
        print(f"\n📊 解析响应结果...")
        status = None
        image_url = None
        progress = None
        
        if isinstance(result_data, dict):
            # 格式1: {"code": 0, "data": {"status": "succeeded", "results": [{"url": "..."}]}}
            if 'code' in result_data:
                if result_data.get('code') == 0 and 'data' in result_data:
                    data = result_data.get('data')
                    if isinstance(data, dict):
                        status = data.get('status')
                        # 优先从results数组获取URL（参考bk-photo-v4）
                        results = data.get('results', [])
                        if isinstance(results, list) and len(results) > 0:
                            image_url = results[0].get('url') or results[0].get('image_url')
                        else:
                            # 如果没有results数组，从data直接获取
                            image_url = data.get('url') or data.get('image_url') or data.get('result_url')
                        progress = data.get('progress')
            # 格式2: 根级别有status和results
            elif 'status' in result_data and 'results' in result_data:
                status = result_data.get('status')
                results = result_data.get('results', [])
                if isinstance(results, list) and len(results) > 0:
                    image_url = results[0].get('url') or results[0].get('image_url')
                progress = result_data.get('progress')
            # 格式3: 直接有status字段
            elif 'status' in result_data:
                status = result_data.get('status')
                image_url = result_data.get('url') or result_data.get('image_url')
                progress = result_data.get('progress')
        
        print(f"   - 状态: {status}")
        print(f"   - 进度: {progress}")
        print(f"   - 图片URL: {image_url}")
        
        # 7. 更新任务状态并下载图片
        if status in ['succeeded', 'completed', 'success'] and image_url:
            print(f"\n✅ 任务已完成，开始更新状态和下载图片...")
            
            # 更新任务状态
            task.status = 'completed'
            task.output_image_path = image_url
            task.error_message = None
            task.completed_at = datetime.now()
            
            # 更新processing_log
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                    api_info['result_image'] = image_url
                    api_info['result_data'] = result_data
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
                except:
                    pass
            
            db.session.commit()
            print(f"✅ 任务状态已更新为completed")
            
            # 下载图片
            try:
                from app.routes.ai import download_api_result_image
                local_path = download_api_result_image(image_url, task.comfyui_prompt_id or str(task.id), app)
                if local_path:
                    task.output_image_path = local_path
                    db.session.commit()
                    print(f"✅ 图片已下载到本地: {local_path}")
                else:
                    print(f"⚠️ 图片下载失败，但云端URL已保存: {image_url}")
            except Exception as download_error:
                print(f"⚠️ 下载图片异常: {str(download_error)}")
                import traceback
                traceback.print_exc()
        elif status in ['failed', 'error']:
            error_msg = result_data.get('error', {}).get('message') if isinstance(result_data, dict) else '任务失败'
            print(f"\n❌ 任务状态为失败: {error_msg}")
            # 不更新任务状态，保持原样
        elif status in ['running', 'processing', 'pending']:
            print(f"\n⏳ 任务仍在处理中，状态: {status}")
            # 只更新processing_log，不改变任务状态
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                    api_info['progress'] = progress
                    api_info['result_data'] = result_data
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    db.session.commit()
                except:
                    pass
        else:
            print(f"\n⚠️ 未知的任务状态: {status}")
        
        print(f"\n=== 查询完成 ===")

if __name__ == '__main__':
    manual_query_and_download(TASK_ID_TO_QUERY)
