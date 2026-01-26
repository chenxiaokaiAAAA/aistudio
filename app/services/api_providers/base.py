# -*- coding: utf-8 -*-
"""
API服务商基础抽象类
定义所有服务商必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import requests


class BaseAPIProvider(ABC):
    """API服务商基础抽象类"""
    
    def __init__(self, api_config):
        """
        初始化服务商
        
        Args:
            api_config: APIProviderConfig对象
        """
        self.api_config = api_config
        self.api_key = api_config.api_key
        self.host = api_config.host_domestic or api_config.host_overseas
        self.api_type = api_config.api_type
    
    @abstractmethod
    def build_request_headers(self, **kwargs) -> Dict[str, str]:
        """
        构建请求头
        
        Returns:
            请求头字典
        """
        pass
    
    @abstractmethod
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
            **kwargs: 其他参数
        
        Returns:
            请求体字典
        """
        pass
    
    def get_draw_endpoint(self) -> str:
        """
        获取绘画接口端点
        
        Returns:
            端点路径
        """
        return self.api_config.draw_endpoint or '/v1/draw/nano-banana'
    
    def get_draw_url(self) -> str:
        """
        获取完整的绘画接口URL
        
        Returns:
            完整的URL
        """
        endpoint = self.get_draw_endpoint()
        if endpoint.startswith('http'):
            return endpoint
        return f"{self.host.rstrip('/')}{endpoint}"
    
    def call_api(self, draw_url: str, request_data: Dict[str, Any],
                 timeout: int = 30, proxies: Optional[Dict] = None) -> requests.Response:
        """
        调用API（默认实现，子类可以重写）
        
        Args:
            draw_url: 完整的API URL
            request_data: 请求数据
            timeout: 超时时间（秒）
            proxies: 代理设置
        
        Returns:
            Response对象
        """
        headers = self.build_request_headers()
        response = requests.post(
            draw_url,
            json=request_data,
            headers=headers,
            timeout=timeout,
            proxies=proxies
        )
        return response
    
    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应（默认实现，子类可以重写）
        
        Args:
            response: Response对象
        
        Returns:
            解析后的数据字典，包含：
            - success: bool, 是否成功
            - task_id: str, 任务ID（异步API）
            - image_url: str, 图片URL（同步API）
            - error: str, 错误信息
        """
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    "success": True,
                    "data": data
                }
            except:
                return {
                    "success": False,
                    "error": "响应解析失败"
                }
        return {
            "success": False,
            "error": f"API调用失败: HTTP {response.status_code}"
        }
    
    def get_polling_endpoint(self, task_id: str) -> str:
        """
        获取轮询接口端点
        
        Args:
            task_id: 任务ID
        
        Returns:
            端点路径
        """
        return self.api_config.result_endpoint or '/v1/draw/result'
    
    def use_get_method_for_polling(self) -> bool:
        """
        轮询时是否使用GET方法（默认False，使用POST）
        
        Returns:
            True表示使用GET，False表示使用POST
        """
        return False
    
    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求
        
        Args:
            task_id: 任务ID
        
        Returns:
            (url, request_body, headers) 元组
        """
        endpoint = self.get_polling_endpoint(task_id)
        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = f"{self.host.rstrip('/')}{endpoint}"
        
        # 默认POST请求
        request_body = {"Id": task_id}  # 默认格式，子类可以重写
        headers = self.build_request_headers()
        
        return url, request_body, headers
    
    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应
        
        Args:
            response: Response对象
        
        Returns:
            解析后的数据字典，包含：
            - status: str, 任务状态（completed/processing/failed）
            - image_url: str, 图片URL（如果完成）
            - error: str, 错误信息（如果失败）
        """
        if response.status_code != 200:
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}"
            }
        
        try:
            data = response.json()
            # 默认解析逻辑，子类可以重写
            if data.get('code') == 0:
                image_url = data.get('data', {}).get('url')
                if image_url:
                    return {
                        "status": "completed",
                        "image_url": image_url
                    }
                return {
                    "status": "processing"
                }
            return {
                "status": "failed",
                "error": data.get('msg', '未知错误')
            }
        except:
            return {
                "status": "failed",
                "error": "响应解析失败"
            }
    
    def get_proxy_settings(self) -> Optional[Dict[str, str]]:
        """
        获取代理设置（默认实现，子类可以重写）
        
        Returns:
            代理字典或None
        """
        import os
        # 检查是否是国内服务商，如果是则禁用代理
        is_domestic = self.api_config.host_domestic and self.host == self.api_config.host_domestic
        is_known_domestic_domain = self.host and any(domain in self.host.lower() for domain in [
            'grsai.dakka.com.cn', 'grsai-file.dakka.com.cn', 't8star.cn', 'ai.t8star.cn'
        ])
        
        if is_domestic or is_known_domestic_domain:
            return {'http': None, 'https': None}
        
        # 检查环境变量
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        if has_proxy:
            # 返回None表示使用环境变量中的代理
            return None
        
        return None
