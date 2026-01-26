#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动查询grsai任务结果
用于调试任务查询问题
"""

import sys
import os
import json
import requests

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 任务ID
task_id = "14-575b6c05-4c0d-4e10-95fc-821216ebc4da"

# 从数据库获取API配置
try:
    from test_server import app, db, APIProviderConfig
    
    with app.app_context():
        # 获取API配置
        api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config:
            print("❌ 未找到API配置")
            sys.exit(1)
        
        print(f"📋 API配置信息:")
        print(f"   - 名称: {api_config.name}")
        print(f"   - Host: {api_config.host_domestic or api_config.host_overseas}")
        print(f"   - Draw Endpoint: {api_config.draw_endpoint}")
        print(f"   - Result Endpoint: {api_config.result_endpoint}")
        print(f"   - API Key: {api_config.api_key[:20]}...")
        print()
        
        # 构建查询URL
        host = api_config.host_domestic or api_config.host_overseas
        result_endpoint = api_config.result_endpoint or '/v1/draw/result'
        result_url = host.rstrip('/') + result_endpoint
        
        headers = {
            "Authorization": f"Bearer {api_config.api_key}"
        }
        
        # 禁用代理
        proxies = {'http': None, 'https': None}
        
        print(f"🔍 查询任务: {task_id}")
        print(f"   - 查询URL: {result_url}")
        print(f"   - 请求方法: POST")
        print()
        
        # 尝试多种task_id格式
        task_id_variants = [
            task_id,  # 完整ID
            task_id.split('-', 1)[1] if '-' in task_id else task_id,  # 去掉第一个前缀
        ]
        
        # 从数据库获取任务的processing_log，看看原始响应
        from test_server import AITask
        task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
        if task and task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
                original_response = api_info.get('original_response', {})
                if original_response:
                    if isinstance(original_response, dict):
                        if original_response.get('code') == 0 and 'data' in original_response:
                            data = original_response.get('data')
                            if isinstance(data, dict):
                                original_task_id = data.get('id') or data.get('task_id')
                                if original_task_id and original_task_id != task_id:
                                    task_id_variants.append(original_task_id)
                                    print(f"📋 从processing_log提取到原始task_id: {original_task_id}")
            except:
                pass
        
        print(f"📋 将尝试以下task_id变体: {task_id_variants}")
        print()
        
        # 依次尝试每个变体
        for current_task_id in task_id_variants:
            print(f"{'='*80}")
            print(f"🔄 尝试使用task_id: {current_task_id}")
            print(f"{'='*80}")
            
            try:
                request_payload = {"task_id": current_task_id}
                print(f"📤 POST请求参数: {json.dumps(request_payload, ensure_ascii=False)}")
                
                response = requests.post(result_url, json=request_payload, headers=headers, timeout=30, proxies=proxies)
                
                print(f"📥 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result_data = response.json()
                    print(f"📥 响应内容:")
                    print(json.dumps(result_data, ensure_ascii=False, indent=2))
                    print()
                    
                    # 解析结果
                    if isinstance(result_data, dict):
                        code = result_data.get('code')
                        msg = result_data.get('msg', '')
                        
                        if code == 0:
                            print(f"✅ 查询成功！")
                            data = result_data.get('data', {})
                            if isinstance(data, dict):
                                status = data.get('status')
                                print(f"   - 状态: {status}")
                                
                                # 检查results数组
                                results = data.get('results', [])
                                if isinstance(results, list) and len(results) > 0:
                                    print(f"   - 结果数量: {len(results)}")
                                    for i, result in enumerate(results):
                                        url = result.get('url') or result.get('image_url')
                                        print(f"   - 结果[{i}] URL: {url}")
                                else:
                                    # 检查直接URL
                                    url = data.get('url') or data.get('image_url') or data.get('result_url')
                                    if url:
                                        print(f"   - 图片URL: {url}")
                                    else:
                                        print(f"   ⚠️ 未找到图片URL")
                                
                                progress = data.get('progress')
                                if progress:
                                    print(f"   - 进度: {progress}%")
                            else:
                                print(f"   ⚠️ data字段格式异常: {type(data)}")
                        elif code == -22:
                            print(f"❌ 任务不存在 (code=-22)")
                        else:
                            print(f"❌ API返回错误: code={code}, msg={msg}")
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    print(f"   响应内容: {response.text[:500]}")
                
                print()
                
            except Exception as e:
                print(f"❌ 查询异常: {str(e)}")
                import traceback
                traceback.print_exc()
                print()
        
        print(f"{'='*80}")
        print("✅ 查询完成")
        
except Exception as e:
    print(f"❌ 脚本执行失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
