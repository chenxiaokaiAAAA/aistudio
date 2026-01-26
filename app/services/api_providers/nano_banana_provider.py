# -*- coding: utf-8 -*-
"""
nano-banana 服务商实现
"""
import json
import os
import requests
from typing import Dict, Any, Optional, List, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseAPIProvider


class NanoBananaProvider(BaseAPIProvider):
    """nano-banana 服务商实现"""
    
    def build_request_headers(self, **kwargs) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def build_request_body(self, prompt: str, model_name: str,
                          uploaded_images: Optional[List[str]] = None,
                          aspect_ratio: str = '1:1',
                          image_size: str = '1K',
                          **kwargs) -> Dict[str, Any]:
        """
        构建请求体
        
        Args:
            prompt: 提示词
            model_name: 模型名称
            uploaded_images: 上传的图片URL列表
            aspect_ratio: 图片比例
            image_size: 图片尺寸
            **kwargs: 其他参数（如 shutProgress, webHook 等）
        
        Returns:
            请求体字典
        """
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "imageSize": image_size,
            "shutProgress": kwargs.get('shutProgress', False),
            "webHook": kwargs.get('webHook', "-1")
        }
        
        # 处理图片URL（需要先上传本地图片到文件服务器）
        if uploaded_images:
            image_urls_for_request = []
            for img_url in uploaded_images:
                if not img_url:
                    continue
                
                # 检查是否是本地URL
                is_local_url = (
                    img_url.startswith('/') or
                    '127.0.0.1' in img_url or 
                    'localhost' in img_url or 
                    '192.168.' in img_url or 
                    img_url.startswith('http://10.') or 
                    img_url.startswith('https://10.')
                )
                
                if is_local_url:
                    # 本地URL：必须先上传到文件服务器获取云端URL
                    cloud_url = self._upload_local_image(img_url)
                    if cloud_url:
                        image_urls_for_request.append(cloud_url)
                else:
                    # 已经是云端URL，直接使用
                    image_urls_for_request.append(img_url)
            
            if image_urls_for_request:
                # nano-banana API使用urls数组格式
                request_data['urls'] = image_urls_for_request
        
        return request_data
    
    def _upload_local_image(self, local_url: str) -> Optional[str]:
        """
        上传本地图片到文件服务器
        
        Args:
            local_url: 本地图片URL
        
        Returns:
            云端URL，如果上传失败返回None
        """
        if not self.api_config.file_upload_endpoint or not self.host:
            raise Exception("本地图片必须上传到文件服务器，但未配置 file_upload_endpoint 或 host")
        
        try:
            # 提取本地文件路径
            if '/uploads/' in local_url:
                filename = local_url.split('/uploads/')[-1]
                local_file_path = os.path.join('uploads', filename)
            elif '/media/original/' in local_url:
                filename = local_url.split('/media/original/')[-1]
                local_file_path = os.path.join('uploads', filename)
            else:
                local_file_path = local_url.lstrip('/')
            
            if not os.path.exists(local_file_path):
                raise Exception(f"本地文件不存在: {local_file_path}")
            
            # 上传到文件服务器
            upload_url = f"{self.host.rstrip('/')}{self.api_config.file_upload_endpoint}"
            print(f"📤 开始上传图片到文件服务器: {upload_url}")
            
            with open(local_file_path, 'rb') as f:
                upload_files = {'file': (os.path.basename(local_file_path), f, 'image/jpeg')}
                upload_response = requests.post(
                    upload_url,
                    files=upload_files,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30
                )
                
                if upload_response.status_code == 200:
                    upload_result = upload_response.json()
                    cloud_url = upload_result.get('url') or upload_result.get('data', {}).get('url') or upload_result.get('file_url')
                    if cloud_url:
                        print(f"✅ 图片已上传到服务器: {cloud_url}")
                        return cloud_url
                    else:
                        raise Exception(f"文件上传成功但响应中未包含文件URL")
                else:
                    error_text = upload_response.text[:500] if hasattr(upload_response, 'text') else str(upload_response.content[:500])
                    raise Exception(f"文件上传失败 (HTTP {upload_response.status_code}): {error_text}")
        except Exception as e:
            print(f"❌ 上传本地图片失败: {str(e)}")
            raise
    
    def call_api(self, draw_url: str, request_data: Dict[str, Any],
                 timeout: int = 30, proxies: Optional[Dict] = None) -> requests.Response:
        """
        调用API（重写以支持代理和超时设置）
        """
        headers = self.build_request_headers()
        
        # 创建带重试机制的Session
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 代理设置
        if proxies is None:
            proxies = self.get_proxy_settings()
        
        # 超时设置
        is_laozhang = 'api.laozhang.ai' in draw_url.lower()
        connect_timeout = 60 if is_laozhang else 10
        read_timeout = 600 if is_laozhang else 120
        
        print(f"📤 发送请求到: {draw_url}")
        print(f"📤 请求参数: {json.dumps(request_data, ensure_ascii=False)}")
        
        response = session.post(
            draw_url,
            json=request_data,
            headers=headers,
            timeout=(connect_timeout, read_timeout),
            proxies=proxies
        )
        
        print(f"✅ nano-banana API响应状态码: {response.status_code}")
        return response
    
    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应
        """
        if response.status_code == 200:
            try:
                data = response.json()
                # nano-banana API响应格式：{"code": 0, "data": {"id": "task_id"}, "msg": "success"}
                if data.get('code') == 0:
                    task_id = data.get('data', {}).get('id')
                    return {
                        "success": True,
                        "task_id": task_id,
                        "data": data
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get('msg', 'API调用失败')
                    }
            except:
                return {
                    "success": False,
                    "error": "响应解析失败"
                }
        else:
            error_text = response.text[:1000] if hasattr(response, 'text') else '无法读取响应'
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {error_text}"
            }
    
    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求（nano-banana使用POST方法）
        """
        endpoint = self.get_polling_endpoint(task_id)
        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = f"{self.host.rstrip('/')}{endpoint}"
        
        # nano-banana API轮询使用POST，请求体格式：{"Id": task_id} 或 {"task_id": task_id}
        # 尝试多种格式以提高兼容性
        request_body = {"Id": task_id}
        headers = self.build_request_headers()
        
        return url, request_body, headers
    
    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应
        """
        if response.status_code != 200:
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}"
            }
        
        try:
            data = response.json()
            # nano-banana API响应格式：{"code": 0, "data": {"status": "succeeded", "url": "..."}}
            if data.get('code') == 0:
                result_data = data.get('data', {})
                status = result_data.get('status', '').lower()
                image_url = result_data.get('url')
                
                if status in ['succeeded', 'completed', 'success'] and image_url:
                    return {
                        "status": "completed",
                        "image_url": image_url
                    }
                elif status in ['running', 'processing', 'pending']:
                    return {
                        "status": "processing"
                    }
                elif status in ['failed', 'error']:
                    return {
                        "status": "failed",
                        "error": result_data.get('error', '任务失败')
                    }
            
            return {
                "status": "processing"
            }
        except:
            return {
                "status": "failed",
                "error": "响应解析失败"
            }
