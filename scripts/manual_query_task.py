#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动查询grsai任务结果
"""

import sys
import os
import json
import requests

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 任务ID
task_id = "14-575b6c05-4c0d-4e10-95fc-821216ebc4da"

print("=" * 80)
print("手动查询grsai任务结果")
print("=" * 80)
print(f"任务ID: {task_id}")
print()

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
        
        print(f"📋 API配置:")
        print(f"   - 名称: {api_config.name}")
        print(f"   - Host: {api_config.host_domestic or api_config.host_overseas}")
        print(f"   - Draw Endpoint: {api_config.draw_endpoint}")
        print(f"   - Result Endpoint: {api_config.result_endpoint}")
        print(f"   - API Key: {api_config.api_key[:30]}...")
        print()
        
        # 构建查询URL
        host = api_config.host_domestic or api_config.host_overseas
        result_endpoint = api_config.result_endpoint or '/v1/draw/result'
        result_url = host.rstrip('/') + result_endpoint
        
        headers = {
            "Authorization": f"Bearer {api_config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 禁用代理
        proxies = {'http': None, 'https': None}
        
        print(f"🔍 查询信息:")
        print(f"   - URL: {result_url}")
        print(f"   - 方法: POST")
        print(f"   - Headers: Authorization=Bearer {api_config.api_key[:30]}...")
        print()
        
        # 尝试多种task_id格式
        task_id_variants = [
            task_id,  # 完整格式
            task_id.split('-', 1)[1] if '-' in task_id else task_id,  # 去掉"14-"前缀
        ]
        
        print(f"📋 将尝试以下task_id变体: {task_id_variants}")
        print()
        
        # 依次尝试每个变体
        for i, current_task_id in enumerate(task_id_variants, 1):
            print(f"{'='*80}")
            print(f"尝试 {i}/{len(task_id_variants)}: task_id = {current_task_id}")
            print(f"{'='*80}")
            
            try:
                request_payload = {"task_id": current_task_id}
                print(f"📤 请求参数: {json.dumps(request_payload, ensure_ascii=False)}")
                print(f"📤 请求URL: {result_url}")
                print()
                
                response = requests.post(result_url, json=request_payload, headers=headers, timeout=30, proxies=proxies)
                
                print(f"📥 响应状态码: {response.status_code}")
                print(f"📥 响应Headers: {dict(response.headers)}")
                print()
                
                if response.status_code == 200:
                    try:
                        result_data = response.json()
                        print(f"📥 响应内容（JSON）:")
                        print(json.dumps(result_data, ensure_ascii=False, indent=2))
                        print()
                        
                        # 解析结果
                        if isinstance(result_data, dict):
                            # 检查格式
                            if 'status' in result_data and 'results' in result_data:
                                print(f"✅ 检测到grsai根级别格式（status和results在根级别）")
                                status = result_data.get('status')
                                results = result_data.get('results', [])
                                print(f"   - 状态: {status}")
                                print(f"   - 结果数量: {len(results)}")
                                if results and len(results) > 0:
                                    url = results[0].get('url') or results[0].get('image_url')
                                    print(f"   - 图片URL: {url}")
                            elif 'code' in result_data:
                                code = result_data.get('code')
                                msg = result_data.get('msg', '')
                                print(f"   - Code: {code}")
                                print(f"   - Message: {msg}")
                                
                                if code == 0 and 'data' in result_data:
                                    data = result_data.get('data')
                                    if isinstance(data, dict):
                                        status = data.get('status')
                                        results = data.get('results', [])
                                        print(f"   - 状态: {status}")
                                        if results:
                                            url = results[0].get('url') if isinstance(results, list) else results.get('url')
                                            print(f"   - 图片URL: {url}")
                                elif code == -22:
                                    print(f"   ❌ 任务不存在 (code=-22)")
                            else:
                                print(f"   ⚠️ 未知格式")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析失败: {str(e)}")
                        print(f"   响应文本: {response.text[:500]}")
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    print(f"   响应文本: {response.text[:500]}")
                
                print()
                
            except Exception as e:
                print(f"❌ 查询异常: {str(e)}")
                import traceback
                traceback.print_exc()
                print()
        
        print("=" * 80)
        print("✅ 查询完成")
        
except Exception as e:
    print(f"❌ 脚本执行失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
