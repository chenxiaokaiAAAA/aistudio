#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析已完成任务的base64图片并保存到本地
"""
import os
import sys
import json
import base64
import time
from datetime import datetime

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # AI-studio目录
sys.path.insert(0, project_root)

# 切换到项目根目录
os.chdir(project_root)

from test_server import app, db, AITask

def parse_base64_image_from_task(task_id):
    """解析任务中的base64图片并保存到本地"""
    with app.app_context():
        # 查找任务
        task = AITask.query.filter_by(id=task_id).first()
        if not task:
            # 尝试通过comfyui_prompt_id查找
            task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
        
        if not task:
            print(f"❌ 未找到任务: {task_id}")
            return False
        
        print(f"✅ 找到任务: {task.id}")
        print(f"   订单号: {task.order_number}")
        print(f"   状态: {task.status}")
        print(f"   创建时间: {task.created_at}")
        
        # 从processing_log中获取响应数据
        if not task.processing_log:
            print(f"❌ 任务没有processing_log数据")
            return False
        
        try:
            api_info = json.loads(task.processing_log) if isinstance(task.processing_log, str) else task.processing_log
        except:
            print(f"❌ 解析processing_log失败")
            return False
        
        # 获取响应数据
        response_data = api_info.get('response_data')
        if not response_data:
            print(f"❌ 响应数据为空")
            return False
        
        # 如果response_data是字符串，尝试解析为JSON
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except:
                print(f"❌ 响应数据不是有效的JSON")
                return False
        
        print(f"📦 开始解析响应数据...")
        print(f"   响应数据类型: {type(response_data)}")
        
        # 查找base64图片数据
        image_data_base64 = None
        mime_type = 'image/png'
        
        # 方式1: 标准Gemini格式 (candidates -> content -> parts)
        if isinstance(response_data, dict) and 'candidates' in response_data:
            candidates = response_data.get('candidates', [])
            if candidates:
                candidate = candidates[0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    for idx, part in enumerate(parts):
                        if isinstance(part, dict):
                            if 'inlineData' in part:
                                inline_data = part['inlineData']
                                if isinstance(inline_data, dict) and 'data' in inline_data:
                                    image_data_base64 = inline_data['data']
                                    mime_type = inline_data.get('mimeType', 'image/png')
                                    print(f"✅ 在candidates[0].content.parts[{idx}]中找到图片数据（inlineData）")
                                    break
                            elif 'inline_data' in part:
                                inline_data = part['inline_data']
                                if isinstance(inline_data, dict) and 'data' in inline_data:
                                    image_data_base64 = inline_data['data']
                                    mime_type = inline_data.get('mime_type', 'image/png')
                                    print(f"✅ 在candidates[0].content.parts[{idx}]中找到图片数据（inline_data）")
                                    break
        
        # 方式2: T8Star格式 (直接是parts数组)
        if not image_data_base64 and isinstance(response_data, list):
            print(f"📦 检测到响应为数组格式，尝试解析parts...")
            for idx, part in enumerate(response_data):
                if isinstance(part, dict):
                    if 'inlineData' in part:
                        inline_data = part['inlineData']
                        if isinstance(inline_data, dict) and 'data' in inline_data:
                            image_data_base64 = inline_data['data']
                            mime_type = inline_data.get('mimeType', 'image/png')
                            print(f"✅ 在parts[{idx}]中找到图片数据（inlineData）")
                            break
                    elif 'inline_data' in part:
                        inline_data = part['inline_data']
                        if isinstance(inline_data, dict) and 'data' in inline_data:
                            image_data_base64 = inline_data['data']
                            mime_type = inline_data.get('mime_type', 'image/png')
                            print(f"✅ 在parts[{idx}]中找到图片数据（inline_data）")
                            break
        
        # 方式3: 响应中有parts字段
        if not image_data_base64 and isinstance(response_data, dict) and 'parts' in response_data:
            parts = response_data['parts']
            for idx, part in enumerate(parts):
                if isinstance(part, dict):
                    if 'inlineData' in part:
                        inline_data = part['inlineData']
                        if isinstance(inline_data, dict) and 'data' in inline_data:
                            image_data_base64 = inline_data['data']
                            mime_type = inline_data.get('mimeType', 'image/png')
                            print(f"✅ 在response.parts[{idx}]中找到图片数据（inlineData）")
                            break
        
        if not image_data_base64:
            print(f"❌ 未找到base64图片数据")
            print(f"   响应数据键: {list(response_data.keys()) if isinstance(response_data, dict) else 'N/A'}")
            print(f"   响应数据前500字符: {json.dumps(response_data, ensure_ascii=False)[:500]}")
            return False
        
        print(f"✅ 找到base64图片数据")
        print(f"   MIME类型: {mime_type}")
        print(f"   数据长度: {len(image_data_base64)} 字符")
        
        # 解码base64图片
        try:
            image_data = base64.b64decode(image_data_base64)
            print(f"✅ base64解码成功，图片大小: {len(image_data)} bytes")
        except Exception as e:
            print(f"❌ base64解码失败: {str(e)}")
            return False
        
        # 保存到final_works目录
        final_folder = 'final_works'
        os.makedirs(final_folder, exist_ok=True)
        
        # 确定文件扩展名
        if 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
            suffix = '.jpg'
        elif 'png' in mime_type.lower():
            suffix = '.png'
        elif 'gif' in mime_type.lower():
            suffix = '.gif'
        elif 'webp' in mime_type.lower():
            suffix = '.webp'
        else:
            suffix = '.png'  # 默认PNG
        
        # 生成文件名
        timestamp = int(time.time())
        task_id_short = str(task.id)[:8] if task.id else 'unknown'
        filename = f"final_{task_id_short}_{timestamp}{suffix}"
        local_path = os.path.join(final_folder, filename)
        
        # 保存文件
        try:
            with open(local_path, 'wb') as f:
                f.write(image_data)
            print(f"✅ 图片已保存到: {local_path}")
            print(f"   文件大小: {len(image_data)} bytes")
        except Exception as e:
            print(f"❌ 保存文件失败: {str(e)}")
            return False
        
        # 更新任务记录
        try:
            # 使用相对路径（用于存储到数据库）
            result_image_path = os.path.join(final_folder, filename).replace('\\', '/')
            task.output_image_path = result_image_path
            task.completed_at = datetime.now()
            
            # 更新processing_log中的result_image
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log) if isinstance(task.processing_log, str) else task.processing_log
                    api_info['result_image'] = result_image_path
                    api_info['result_image_local_path'] = local_path
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
                except:
                    pass
            
            db.session.commit()
            print(f"✅ 任务记录已更新")
            print(f"   output_image_path: {result_image_path}")
            return True
        except Exception as e:
            print(f"❌ 更新任务记录失败: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python parse_base64_image.py <task_id>")
        print("示例: python parse_base64_image.py 91820667-c0c3-4f73-a83a-bb215a21dc0c")
        sys.exit(1)
    
    task_id = sys.argv[1]
    print(f"🔍 开始解析任务: {task_id}")
    print("=" * 60)
    
    success = parse_base64_image_from_task(task_id)
    
    print("=" * 60)
    if success:
        print("✅ 解析完成！")
    else:
        print("❌ 解析失败！")
        sys.exit(1)
