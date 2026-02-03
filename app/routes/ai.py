# -*- coding: utf-8 -*-
"""
AI任务管理路由模块（主文件）
整合所有AI管理相关的子模块
"""
import os
import time
import requests
from flask import Blueprint

# 创建主蓝图
ai_bp = Blueprint('ai', __name__, url_prefix='/admin/ai')

# 导入并注册所有子模块
from app.routes.ai_routes import ai_routes_bp
from app.routes.ai_tasks_api import ai_tasks_api_bp
from app.routes.ai_config_api import ai_config_api_bp
from app.routes.ai_debug_api import ai_debug_api_bp

# 注册子蓝图到主蓝图
ai_bp.register_blueprint(ai_routes_bp)
ai_bp.register_blueprint(ai_tasks_api_bp)
ai_bp.register_blueprint(ai_config_api_bp)
ai_bp.register_blueprint(ai_debug_api_bp)


def download_api_result_image(image_url, task_id, app_instance=None):
    """
    下载API返回的结果图片到本地
    
    Args:
        image_url: 图片URL（可以是HTTP URL或本地路径）
        task_id: 任务ID（用于生成文件名）
        app_instance: Flask应用实例（可选，用于获取配置）
    
    Returns:
        str: 本地保存的图片路径（相对路径），如果失败返回None
    """
    try:
        # 如果已经是本地路径，直接返回
        if image_url and not image_url.startswith('http'):
            if os.path.exists(image_url):
                return image_url
            # 尝试相对路径
            if os.path.exists(os.path.join('final_works', os.path.basename(image_url))):
                return os.path.join('final_works', os.path.basename(image_url)).replace('\\', '/')
        
        # 如果是HTTP URL，下载图片
        if image_url and image_url.startswith('http'):
            # 处理 ComfyUI 的 view URL，转换为实际的图片URL
            # ComfyUI view URL格式: http://host:port/view?filename=xxx.png&type=output
            # 需要转换为: http://host:port/view?filename=xxx.png&type=output&format=png (或直接访问)
            download_url = image_url
            if '/view?' in image_url:
                # ComfyUI view URL，直接使用（ComfyUI会自动返回图片）
                download_url = image_url
                print(f"📥 下载ComfyUI图片: {download_url}")
            
            response = requests.get(download_url, timeout=60, proxies={'http': None, 'https': None})
            if response.status_code == 200:
                # 保存到final_works目录
                final_folder = 'final_works'
                os.makedirs(final_folder, exist_ok=True)
                
                # 生成文件名
                timestamp = int(time.time())
                task_id_str = str(task_id)[:8] if task_id else 'unknown'
                
                # 根据Content-Type确定文件扩展名
                content_type = response.headers.get('Content-Type', '')
                if 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
                    suffix = '.jpg'
                elif 'png' in content_type.lower():
                    suffix = '.png'
                elif 'webp' in content_type.lower():
                    suffix = '.webp'
                else:
                    # 尝试从URL推断
                    if image_url.lower().endswith('.jpg') or image_url.lower().endswith('.jpeg'):
                        suffix = '.jpg'
                    elif image_url.lower().endswith('.png'):
                        suffix = '.png'
                    elif image_url.lower().endswith('.webp'):
                        suffix = '.webp'
                    else:
                        suffix = '.jpg'  # 默认JPG
                
                filename = f"final_{task_id_str}_{timestamp}{suffix}"
                local_path = os.path.join(final_folder, filename)
                
                # 保存文件
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                # 返回相对路径（用于存储到数据库）
                relative_path = os.path.join(final_folder, filename).replace('\\', '/')
                print(f"✅ API结果图片已下载到本地: {local_path}")
                return relative_path
            else:
                print(f"❌ 下载API结果图片失败: HTTP {response.status_code}")
                return None
        else:
            print(f"⚠️ 无效的图片URL: {image_url}")
            return None
            
    except Exception as e:
        print(f"❌ 下载API结果图片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# 导出主蓝图和下载函数（供其他模块使用）
__all__ = ['ai_bp', 'download_api_result_image']
