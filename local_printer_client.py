# -*- coding: utf-8 -*-
"""
本地打印客户端（通过HTTP API调用打印代理服务）
用于从阿里云服务器调用本地打印机
"""
import requests
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalPrinterClient:
    """本地打印客户端（通过HTTP API）"""
    
    def __init__(self, proxy_url, api_key=None):
        """
        初始化打印客户端
        
        Args:
            proxy_url: 打印代理服务地址，如 'http://localhost:8888' 或 'http://192.168.1.100:8888'
            api_key: API密钥（可选）
        """
        self.proxy_url = proxy_url.rstrip('/')
        self.api_key = api_key
        self.print_endpoint = f"{self.proxy_url}/print"
        self.health_endpoint = f"{self.proxy_url}/health"
    
    def print_image(self, image_path=None, image_url=None, image_data=None, file_ext=None, copies=1):
        """
        打印图片或文件
        
        Args:
            image_path: 本地图片路径（仅当客户端和代理在同一台机器时可用）
            image_url: 图片URL（推荐，从阿里云服务器访问）
            image_data: Base64编码的图片数据
            file_ext: 文件扩展名（如 .txt, .jpg, .pdf），用于正确识别文件类型
            copies: 打印份数
            
        Returns:
            dict: 打印结果
        """
        try:
            # 准备请求数据
            payload = {
                'copies': copies
            }
            
            # 添加API密钥
            if self.api_key:
                payload['api_key'] = self.api_key
            
            # 添加文件扩展名（如果提供）
            if file_ext:
                payload['file_ext'] = file_ext
            
            # 选择图片数据源
            if image_url:
                payload['image_url'] = image_url
            elif image_data:
                payload['image_data'] = image_data
            elif image_path:
                payload['image_path'] = image_path
            else:
                return {
                    'success': False,
                    'message': '请提供图片路径、URL或数据'
                }
            
            # 发送请求
            headers = {}
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            logger.info(f"发送打印请求到: {self.print_endpoint}")
            response = requests.post(
                self.print_endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.info(f"✅ 打印任务发送成功")
            else:
                logger.error(f"❌ 打印任务失败: {result.get('message')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f'打印请求失败: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error_type': 'network_error'
            }
        except Exception as e:
            error_msg = f'打印失败: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error_type': 'unknown_error'
            }
    
    def test_connection(self):
        """测试打印代理服务连接"""
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            response.raise_for_status()
            result = response.json()
            return {
                'success': True,
                'message': '打印代理服务连接正常',
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'无法连接到打印代理服务: {str(e)}'
            }
