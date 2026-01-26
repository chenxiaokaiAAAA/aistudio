# -*- coding: utf-8 -*-
"""
RunningHub rhart-image-n-pro/edit 服务商实现
全能图片PRO-图生图 API
"""
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseAPIProvider


class RunningHubRhartEditProvider(BaseAPIProvider):
    """RunningHub 全能图片PRO-图生图 服务商实现"""
    
    def get_draw_endpoint(self) -> str:
        """获取绘画接口端点"""
        return self.api_config.draw_endpoint or '/openapi/v2/rhart-image-n-pro/edit'
    
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
        构建请求体（RunningHub 格式）
        
        Args:
            prompt: 提示词
            model_name: 模型名称（RunningHub 不使用此参数，但保留以兼容接口）
            uploaded_images: 图片URL数组（最多10张）
            aspect_ratio: 图片比例（3:4, 16:9, auto 等）
            image_size: 图片尺寸（1K, 2K, 4K 等）
            **kwargs: 其他参数
        
        Returns:
            请求体字典
        """
        # 处理图片URL：RunningHub 使用 imageUrls 数组（最多10项）
        image_urls_to_process = uploaded_images or []
        
        # 限制最多10张图片
        if len(image_urls_to_process) > 10:
            image_urls_to_process = image_urls_to_process[:10]
            print(f"⚠️ RunningHub API 最多支持10张图片，已截取前10张")
        
        if not image_urls_to_process:
            raise Exception("RunningHub API 需要至少一张图片URL")
        
        # 构建请求体（RunningHub 格式）
        payload = {
            "prompt": prompt,
            "resolution": image_size if image_size else "1K",  # 1K, 2K, 4K 等
            "aspectRatio": aspect_ratio if aspect_ratio != 'auto' else "auto",  # 3:4, 16:9, auto 等
            "imageUrls": image_urls_to_process  # 图片URL数组
        }
        
        print(f"📸 [RunningHub] 请求包含 {len(image_urls_to_process)} 张图片")
        
        return payload
    
    def call_api(self, draw_url: str, request_data: Dict[str, Any],
                 timeout: int = 30, proxies: Optional[Dict] = None) -> requests.Response:
        """
        调用API
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
        
        # 超时设置：连接10秒，读取30秒（RunningHub 通常快速返回 taskId）
        print(f"📤 调用 RunningHub rhart-image-n-pro/edit API: {draw_url}")
        print(f"📤 请求参数: {json.dumps(request_data, ensure_ascii=False)}")
        print(f"📤 图片数量: {len(request_data.get('imageUrls', []))}")
        
        response = session.post(
            draw_url,
            json=request_data,
            headers=headers,
            timeout=(10, 30),
            proxies=proxies
        )
        
        print(f"✅ RunningHub API响应状态码: {response.status_code}")
        return response
    
    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应（RunningHub 格式）
        """
        if response.status_code == 200:
            try:
                data = response.json()
                # RunningHub API响应格式：{"taskId": "xxx"} 或 {"code": 0, "data": {"taskId": "xxx"}}
                task_id = data.get('taskId') or data.get('data', {}).get('taskId')
                if task_id:
                    return {
                        "success": True,
                        "task_id": task_id,
                        "data": data
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get('msg', 'API调用失败，未返回taskId')
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
    
    def get_polling_endpoint(self, task_id: str) -> str:
        """
        获取轮询接口端点（支持新旧两种格式）
        """
        endpoint = self.api_config.result_endpoint
        if endpoint and '/openapi/v2/query' in endpoint:
            # 新格式：/openapi/v2/query
            return endpoint
        elif endpoint and '/task/openapi/outputs' in endpoint:
            # 旧格式：/task/openapi/outputs
            return endpoint
        else:
            # 默认使用新格式
            return '/openapi/v2/query'
    
    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求（RunningHub 使用 POST 方法）
        """
        endpoint = self.get_polling_endpoint(task_id)
        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = f"{self.host.rstrip('/')}{endpoint}"
        
        headers = self.build_request_headers()
        
        # 判断使用哪种格式
        use_new_query_format = '/openapi/v2/query' in endpoint
        
        if use_new_query_format:
            # 新格式：/openapi/v2/query，请求体只需要 taskId
            request_body = {
                "taskId": task_id
            }
        else:
            # 旧格式：/task/openapi/outputs，请求体需要 apiKey 和 taskId
            request_body = {
                "apiKey": self.api_key,
                "taskId": task_id
            }
        
        return url, request_body, headers
    
    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应（RunningHub 格式）
        """
        if response.status_code != 200:
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}"
            }
        
        try:
            result_data = response.json()
            
            # RunningHub API响应格式：
            # 新格式：{"status": "SUCCESS/RUNNING/QUEUED/FAILED", "results": [{"url": "..."}], "errorMessage": "..."}
            # 旧格式：{"code": 0, "data": {"status": "...", "url": "..."}}
            
            status = None
            image_url = None
            error_msg = None
            
            # 检查新格式
            if 'status' in result_data:
                status = result_data.get('status', '').upper()
                if status == 'SUCCESS':
                    results = result_data.get('results', [])
                    if results and len(results) > 0:
                        image_url = results[0].get('url')
                elif status == 'FAILED':
                    error_msg = result_data.get('errorMessage', '任务失败')
            # 检查旧格式
            elif result_data.get('code') == 0 and 'data' in result_data:
                data = result_data.get('data', {})
                status_str = data.get('status', '').upper()
                if status_str == 'SUCCESS':
                    status = 'SUCCESS'
                    image_url = data.get('url')
                elif status_str in ['RUNNING', 'PROCESSING', 'QUEUED']:
                    status = 'RUNNING'
                elif status_str == 'FAILED':
                    status = 'FAILED'
                    error_msg = data.get('errorMessage', '任务失败')
            
            # 如果没有找到status，尝试从其他字段推断
            if not status:
                # 检查是否有错误信息
                if result_data.get('errorCode') or result_data.get('errorMessage'):
                    status = 'FAILED'
                    error_msg = result_data.get('errorMessage', f"API错误 (errorCode={result_data.get('errorCode')})")
                else:
                    # 默认认为正在处理中
                    status = 'RUNNING'
            
            # 返回结果
            if status == 'SUCCESS' and image_url:
                return {
                    "status": "completed",
                    "image_url": image_url
                }
            elif status in ['RUNNING', 'QUEUED']:
                return {
                    "status": "processing"
                }
            elif status == 'FAILED':
                return {
                    "status": "failed",
                    "error": error_msg or '任务失败'
                }
            else:
                return {
                    "status": "processing"
                }
        except Exception as e:
            print(f"⚠️ 轮询响应解析失败: {str(e)}")
            return {
                "status": "failed",
                "error": f"响应解析失败: {str(e)}"
            }
