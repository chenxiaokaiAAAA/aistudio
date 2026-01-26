# -*- coding: utf-8 -*-
"""
gemini-native 服务商实现
使用 Google Gemini 原生格式（JSON，图片base64编码）
"""
import json
import os
import base64
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .base import BaseAPIProvider


class GeminiNativeProvider(BaseAPIProvider):
    """gemini-native 服务商实现（Google Gemini 原生格式）"""
    
    def __init__(self, api_config):
        """初始化"""
        super().__init__(api_config)
        # 检查服务商类型
        self.is_google_direct = self.host and 'generativelanguage.googleapis.com' in self.host
        self.is_proxy_server = self.host and '/api/gemini/generate' in (self.api_config.draw_endpoint or '')
        self.is_t8star = self.host and 't8star.cn' in self.host.lower()
        self.is_sync_api = api_config.is_sync_api if hasattr(api_config, 'is_sync_api') else False
    
    def build_request_headers(self, **kwargs) -> Dict[str, str]:
        """
        构建请求头（根据不同的服务商使用不同的认证方式）
        """
        headers = {"Content-Type": "application/json"}
        
        if self.is_google_direct:
            if self.is_proxy_server:
                # 代理服务器：不需要API Key（在URL中）
                pass
            else:
                # Google直接调用：使用 x-goog-api-key
                headers["x-goog-api-key"] = self.api_key
        else:
            # 其他服务商：使用 Bearer token
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def build_request_body(self, prompt: str, model_name: str,
                          uploaded_images: Optional[List[str]] = None,
                          aspect_ratio: str = '1:1',
                          image_size: str = '1K',
                          **kwargs) -> Dict[str, Any]:
        """
        构建请求体（Google Gemini 格式，图片转换为base64）
        """
        parts = []
        
        # 处理图片：下载并转换为base64
        if uploaded_images:
            for img_url in uploaded_images:
                try:
                    # 检查是否是本地URL
                    is_local_url = (
                        '127.0.0.1' in img_url or 
                        'localhost' in img_url or 
                        '192.168.' in img_url or 
                        img_url.startswith('http://10.') or 
                        img_url.startswith('https://10.')
                    )
                    
                    img_data = None
                    if is_local_url:
                        # 本地URL：直接读取文件
                        try:
                            if '/media/original/' in img_url:
                                filename = img_url.split('/media/original/')[-1]
                                local_file_path = os.path.join('uploads', filename)
                            elif '/uploads/' in img_url:
                                filename = img_url.split('/uploads/')[-1]
                                local_file_path = os.path.join('uploads', filename)
                            else:
                                parsed_url = urlparse(img_url)
                                path = parsed_url.path
                                if path.startswith('/'):
                                    path = path[1:]
                                local_file_path = path
                            
                            if local_file_path and os.path.exists(local_file_path):
                                with open(local_file_path, 'rb') as f:
                                    img_data = f.read()
                        except Exception as e:
                            print(f"读取本地文件失败: {str(e)}，尝试HTTP下载")
                            is_local_url = False
                    
                    if not is_local_url or img_data is None:
                        # 云端URL：使用HTTP下载
                        proxies = {'http': None, 'https': None}  # 禁用代理
                        response_img = requests.get(img_url, proxies=proxies, timeout=30)
                        if response_img.status_code == 200:
                            img_data = response_img.content
                        else:
                            raise Exception(f"下载图片失败: HTTP {response_img.status_code}")
                    
                    # 转换为base64
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    # 检测图片格式
                    if img_data.startswith(b'\xff\xd8\xff'):
                        mime_type = 'image/jpeg'
                    elif img_data.startswith(b'\x89PNG'):
                        mime_type = 'image/png'
                    elif img_data.startswith(b'GIF'):
                        mime_type = 'image/gif'
                    elif img_data.startswith(b'WEBP'):
                        mime_type = 'image/webp'
                    else:
                        mime_type = 'image/jpeg'  # 默认
                    
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": img_base64
                        }
                    })
                except Exception as e:
                    print(f"处理图片失败: {str(e)}")
                    raise
        
        # 添加文本提示词
        if prompt:
            parts.append({"text": prompt})
        
        # 构建请求体
        payload = {
            "contents": [{
                "parts": parts
            }]
        }
        
        # 如果是T8Star服务商，可能需要额外的参数
        if self.is_t8star and model_name:
            payload["model"] = model_name
        
        # 创建用于日志记录的request_data（包含图片URL信息，用于前端显示）
        request_data_for_log = {
            "model": model_name,
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "imageSize": image_size,
            "shutProgress": False,
            "webHook": "-1"
        }
        
        if uploaded_images:
            request_data_for_log["image_urls"] = uploaded_images
            request_data_for_log["image_count"] = len(uploaded_images)
            request_data_for_log["image_format"] = "base64_encoded_in_payload"
            print(f"📸 [gemini-native] 请求中包含 {len(uploaded_images)} 张图片（已转换为base64，包含在payload中）")
        else:
            print(f"⚠️ [gemini-native] 警告: 没有图片URL，API调用可能失败")
        
        # 将 request_data_for_log 附加到 payload 中，用于后续提取
        payload['_request_data_for_log'] = request_data_for_log
        
        return payload
    
    def call_api(self, draw_url: str, request_data: Dict[str, Any],
                 timeout: int = 30, proxies: Optional[Dict] = None) -> requests.Response:
        """
        调用API（同步API，需要特殊处理超时和重试）
        """
        # 提取 request_data_for_log（如果存在）
        request_data_for_log = request_data.pop('_request_data_for_log', None)
        
        headers = self.build_request_headers()
        
        # 创建Session
        session = requests.Session()
        
        # 关键修复：同步API不应该重试，避免重复请求导致后端重复制作
        if self.is_sync_api:
            print(f"⚠️ [同步API] 检测到同步API，禁用自动重试机制（避免重复请求）")
            retry_strategy = Retry(
                total=0,  # 不重试
                backoff_factor=0,
                status_forcelist=[],
                allowed_methods=[],
                raise_on_status=False
            )
        else:
            # 异步API：允许重试（仅对特定状态码）
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"],
                raise_on_status=False
            )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 代理设置
        if proxies is None:
            proxies = self.get_proxy_settings()
        
        # 超时设置
        if self.is_t8star:
            # T8Star同步API：使用与bk-photo-v4完全相同的超时设置
            connect_timeout = 150  # 2.5分钟：连接建立 + 请求发送超时
            read_timeout = 480     # 8分钟：等待响应超时
            print(f"📊 [T8Star同步API] 超时设置: 连接/发送={connect_timeout}秒（2.5分钟），等待响应={read_timeout}秒（8分钟）")
            print(f"   ⚠️ 注意：如果使用代理，请确保代理服务器的proxy-timeout > {read_timeout}秒（建议900秒）")
        else:
            # 其他服务商：使用较短的超时时间
            connect_timeout = 60
            read_timeout = 300  # 5分钟
        
        print(f"📤 [gemini-native] 发送请求到: {draw_url}")
        print(f"📤 [gemini-native] 超时设置: connect={connect_timeout}s, read={read_timeout}s")
        
        # 关键修复：同步API如果连接断开，不应该重试（避免重复请求导致后端重复制作）
        request_start_time = time.time()
        try:
            response = session.post(
                draw_url,
                json=request_data,
                headers=headers,
                timeout=(connect_timeout, read_timeout),
                proxies=proxies
            )
            # 关键修复：将包含图片信息的request_data附加到response对象上，用于前端显示
            if request_data_for_log:
                response.request_data_for_log = request_data_for_log
            return response
        except requests.exceptions.ProxyError as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            print(f"❌ [同步API] 代理错误: {error_str}")
            print(f"   请求耗时: {elapsed_time:.2f}秒")
            if elapsed_time > 5:
                raise Exception(f"连接被远程关闭，但请求可能已发送到后端（耗时{elapsed_time:.2f}秒）。代理服务器可能在{elapsed_time:.0f}秒后超时。如果后台已经成功生成，请检查代理服务器超时设置或手动检查结果。错误详情: {error_str}")
            else:
                raise Exception(f"同步API代理连接失败。请检查代理服务器是否正常运行。错误: {error_str}")
        except requests.exceptions.ConnectionError as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            if 'RemoteDisconnected' in error_str or 'Remote end closed connection' in error_str:
                print(f"⚠️ [同步API] 连接被远程关闭，未收到响应")
                print(f"   请求耗时: {elapsed_time:.2f}秒")
                raise Exception(f"连接被远程关闭，但请求可能已发送到后端（耗时{elapsed_time:.2f}秒）。如果后台已经成功生成，请稍后手动检查结果。错误详情: {error_str}")
            else:
                raise Exception(f"同步API连接失败: {error_str}")
        except requests.exceptions.Timeout as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            print(f"❌ [同步API] 请求超时: {error_str}")
            print(f"   请求耗时: {elapsed_time:.2f}秒")
            if elapsed_time < connect_timeout:
                raise Exception(f"同步API连接建立超时（{elapsed_time:.2f}秒）。请检查网络连接或代理设置。错误详情: {error_str}")
            else:
                raise Exception(f"连接被远程关闭，但请求可能已发送到后端（耗时{elapsed_time:.2f}秒）。如果后台已经成功生成，请稍后手动检查结果。错误详情: {error_str}")
        except Exception as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            print(f"❌ [同步API] 请求异常: {error_str}")
            print(f"   请求耗时: {elapsed_time:.2f}秒")
            raise Exception(f"同步API请求失败: {error_str}")
    
    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应（Google Gemini 格式）
        """
        if response.status_code == 200:
            try:
                data = response.json()
                # Gemini API响应格式：{"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        # 查找文本响应
                        for part in parts:
                            if 'text' in part:
                                return {
                                    "success": True,
                                    "text": part['text'],
                                    "data": data
                                }
                return {
                    "success": True,
                    "data": data
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
    
    def get_proxy_settings(self) -> Optional[Dict[str, str]]:
        """
        获取代理设置（重写以支持T8Star的特殊需求）
        """
        import os
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        proxy_url = None
        if has_proxy:
            proxy_url = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY') or os.environ.get('http_proxy') or os.environ.get('https_proxy')
        
        if self.is_t8star:
            # T8star服务商：如果检测到代理环境变量，就使用代理
            if has_proxy and proxy_url:
                print(f"✅ [gemini-native] 检测到代理环境变量: {proxy_url}，T8star将通过代理连接")
                return None  # None表示使用系统环境变量中的代理
            else:
                print(f"ℹ️ [gemini-native] 未检测到代理环境变量，T8star将直连")
                return {'http': None, 'https': None}  # 禁用代理，直连
        elif self.is_google_direct:
            # 对于 Google API，如果检测到代理设置，使用代理
            if has_proxy:
                return None
            else:
                return {'http': None, 'https': None}
        else:
            # 其他服务商
            if has_proxy:
                return None
            else:
                return {'http': None, 'https': None}
    
    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求（gemini-native通常是同步API，不需要轮询）
        """
        # gemini-native通常是同步API，直接返回结果，不需要轮询
        # 如果确实需要轮询，使用默认实现
        return super().build_polling_request(task_id)
    
    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应（gemini-native通常是同步API，不需要轮询）
        """
        # gemini-native通常是同步API，直接返回结果，不需要轮询
        # 如果确实需要轮询，使用默认实现
        return super().parse_polling_response(response)
