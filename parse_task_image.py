#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过API解析任务的base64图片
"""
import requests
import json

task_id = "91820667-c0c3-4f73-a83a-bb215a21dc0c"
url = f"http://127.0.0.1:8000/api/admin/ai/tasks/parse-base64/{task_id}"

print(f"🔍 开始解析任务: {task_id}")
print(f"📤 请求URL: {url}")

try:
    # 注意：这里需要登录，所以可能需要先获取session
    # 或者使用管理员账号的session
    response = requests.post(url, timeout=30)
    
    print(f"📥 响应状态码: {response.status_code}")
    result = response.json()
    
    if result.get('status') == 'success':
        print("✅ 解析成功！")
        print(f"   图片路径: {result['data']['image_path']}")
        print(f"   本地路径: {result['data']['local_path']}")
        print(f"   文件大小: {result['data']['file_size']} bytes")
    else:
        print(f"❌ 解析失败: {result.get('message', '未知错误')}")
        if 'debug' in result:
            print(f"   调试信息: {json.dumps(result['debug'], ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"❌ 请求失败: {str(e)}")
