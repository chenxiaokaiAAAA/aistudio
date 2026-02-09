# -*- coding: utf-8 -*-
"""
nano-banana-edits 服务商实现
使用 multipart/form-data 格式，支持图片文件上传
"""

import logging

logger = logging.getLogger(__name__)
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseAPIProvider


class NanoBananaEditsProvider(BaseAPIProvider):
    """nano-banana-edits 服务商实现（使用 multipart/form-data）"""

    def __init__(self, api_config):
        """初始化"""
        super().__init__(api_config)
        # 检查是否是T8Star服务商
        self.is_t8star = self.host and "t8star.cn" in self.host.lower()

    def build_request_headers(self, **kwargs) -> Dict[str, str]:
        """
        构建请求头（multipart/form-data 不需要 Content-Type，requests会自动设置）
        """
        return {
            "Authorization": f"Bearer {self.api_key}"
            # 注意：multipart/form-data 的 Content-Type 由 requests 自动设置，包含 boundary
        }

    def get_draw_endpoint(self) -> str:
        """
        获取绘画接口端点（T8Star必须使用 /v1/images/edits）
        """
        if self.is_t8star:
            return "/v1/images/edits"
        return self.api_config.draw_endpoint or "/v1/images/edits"

    def build_request_body(
        self,
        prompt: str,
        model_name: str,
        uploaded_images: Optional[List[str]] = None,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        构建请求体（multipart/form-data格式）

        注意：这个方法返回的字典会被转换为 multipart/form-data 格式
        """
        data = {
            "model": model_name,
            "prompt": prompt,
            "response_format": "url",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        }

        # T8Star 支持 async 参数（作为查询参数，不在请求体中）
        params = {}
        if self.is_t8star:
            params["async"] = "true"

        # 返回 data 和 params，以及需要上传的文件列表
        return {
            "data": data,
            "params": params,
            "files": self._prepare_image_files(uploaded_images) if uploaded_images else [],
        }

    def _prepare_image_files(
        self, image_urls: List[str]
    ) -> List[Tuple[str, Tuple[str, bytes, str]]]:
        """
        准备图片文件（下载并转换为文件元组）

        Returns:
            List of (field_name, (filename, content, content_type)) tuples
        """
        files = []

        for idx, img_url in enumerate(image_urls):
            if not img_url:
                continue

            try:
                logger.info(f"📥 正在下载图片 {idx + 1}/{len(image_urls)}: {img_url}")

                # 检查是否是本地URL
                is_local_url = (
                    img_url.startswith("/")
                    or "127.0.0.1" in img_url
                    or "localhost" in img_url
                    or "192.168." in img_url
                )

                if is_local_url:
                    # 本地URL：直接读取文件
                    if "/uploads/" in img_url:
                        filename = img_url.split("/uploads/")[-1]
                        local_file_path = os.path.join("uploads", filename)
                    elif "/media/original/" in img_url:
                        filename = img_url.split("/media/original/")[-1]
                        local_file_path = os.path.join("uploads", filename)
                    else:
                        local_file_path = img_url.lstrip("/")

                    if not os.path.exists(local_file_path):
                        raise Exception(f"本地文件不存在: {local_file_path}")

                    with open(local_file_path, "rb") as f:
                        img_content = f.read()
                else:
                    # 云端URL：使用HTTP下载
                    proxies = {"http": None, "https": None}  # 禁用代理
                    img_response = requests.get(img_url, proxies=proxies, timeout=30)
                    img_response.raise_for_status()
                    img_content = img_response.content

                # 获取文件名
                filename = os.path.basename(urlparse(img_url).path) or f"image_{idx}.jpg"

                # 准备文件（nano-banana-edits支持多图，使用image格式，多图时使用image[]）
                if len(image_urls) > 1:
                    files.append(("image[]", (filename, img_content, "image/jpeg")))
                else:
                    files.append(("image", (filename, img_content, "image/jpeg")))

                logger.info(
                    f"✅ 已下载图片 {idx + 1}/{len(image_urls)}: {filename}, 大小: {len(img_content)} bytes"
                )
            except Exception as e:
                logger.error("下载图片 {idx+1} 失败: {str(e)}")
                import traceback

                traceback.print_exc()
                raise

        if not files:
            raise Exception("所有图片下载失败，无法调用API")

        return files

    def call_api(
        self,
        draw_url: str,
        request_data: Dict[str, Any],
        timeout: int = 30,
        proxies: Optional[Dict] = None,
    ) -> requests.Response:
        """
        调用API（multipart/form-data格式）
        """
        # 从 request_data 中提取 data、params 和 files
        data = request_data.get("data", {})
        params = request_data.get("params", {})
        files = request_data.get("files", [])

        if not files:
            raise Exception("没有图片文件，无法调用API")

        headers = self.build_request_headers()

        # 创建带重试机制的Session
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 代理设置
        if proxies is None:
            proxies = self.get_proxy_settings()

        logger.info(f"调用 nano-banana-edits API (multipart): {draw_url}")
        logger.info(f"请求参数: {data}")
        logger.info(f"查询参数: {params}")
        logger.info(f"上传文件数量: {len(files)}")

        # 使用 multipart/form-data 格式发送请求
        response = session.post(
            draw_url,
            data=data,
            files=files,
            params=params,  # T8Star 的 async=true 作为查询参数
            headers=headers,
            timeout=timeout,
            proxies=proxies,
        )

        logger.info(f"✅ nano-banana-edits API响应状态码: {response.status_code}")
        return response

    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应（支持多种响应格式）
        """
        if response.status_code == 200:
            try:
                result = response.json()

                # 检查是否是异步模式（T8Star返回task_id）
                if self.is_t8star:
                    # T8Star异步模式：{"task_id": "xxx"} 或 {"id": "xxx"}
                    task_id = result.get("task_id") or result.get("id")
                    if task_id:
                        return {"success": True, "task_id": task_id, "data": result}

                # 同步模式：检查多种可能的响应格式
                # 格式1: OpenAI DALL-E格式 {"created": 1234567890, "data": [{"url": "..."}]}
                if (
                    "data" in result
                    and isinstance(result.get("data"), list)
                    and len(result["data"]) > 0
                ):
                    result_image_url = result["data"][0].get("url")
                    if result_image_url:
                        return {"success": True, "image_url": result_image_url, "data": result}

                # 格式2: 直接返回URL字符串
                if isinstance(result, str) and (
                    result.startswith("http://") or result.startswith("https://")
                ):
                    return {"success": True, "image_url": result, "data": {"url": result}}

                # 格式3: {"url": "..."}
                if "url" in result:
                    return {"success": True, "image_url": result.get("url"), "data": result}

                # 格式4: {"image_url": "..."} 或 {"result_url": "..."}
                if "image_url" in result:
                    return {"success": True, "image_url": result.get("image_url"), "data": result}
                if "result_url" in result:
                    return {"success": True, "image_url": result.get("result_url"), "data": result}

                # 格式5: {"data": {"url": "..."}}
                if "data" in result and isinstance(result.get("data"), dict):
                    data = result.get("data")
                    if "url" in data:
                        return {"success": True, "image_url": data.get("url"), "data": result}

                # 如果都没有找到，返回原始数据
                return {"success": True, "data": result}
            except Exception as e:
                logger.warning("响应解析失败: {str(e)}")
                return {"success": False, "error": f"响应解析失败: {str(e)}"}
        else:
            error_text = response.text[:1000] if hasattr(response, "text") else "无法读取响应"
            return {"success": False, "error": f"HTTP {response.status_code}: {error_text}"}

    def use_get_method_for_polling(self) -> bool:
        """
        轮询时是否使用GET方法（T8Star使用GET，其他使用POST）
        """
        return self.is_t8star

    def get_polling_endpoint(self, task_id: str) -> str:
        """
        获取轮询接口端点（T8Star使用GET /v1/images/tasks/{task_id}）
        """
        if self.is_t8star:
            return f"/v1/images/tasks/{task_id}"
        return self.api_config.result_endpoint or "/v1/images/edits/result"

    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求
        """
        endpoint = self.get_polling_endpoint(task_id)
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.host.rstrip('/')}{endpoint}"

        headers = self.build_request_headers()

        if self.is_t8star:
            # T8Star使用GET方法，task_id在URL中
            request_body = {}  # GET请求不需要请求体
        else:
            # 其他服务商使用POST方法，尝试多种格式
            request_body = {"Id": task_id}  # 默认格式

        return url, request_body, headers

    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应（T8Star有特殊的响应格式）
        """
        if response.status_code != 200:
            return {"status": "failed", "error": f"HTTP {response.status_code}"}

        try:
            result_data = response.json()

            if self.is_t8star:
                # T8Star响应格式：{"code": "success", "data": {"status": "SUCCESS", "data": [{"url": "..."}]}}
                if result_data.get("code") == "success":
                    data = result_data.get("data", {})
                    status = data.get("status", "").upper()

                    if status == "SUCCESS":
                        # 提取图片URL（三层嵌套：data.data.data[0].url）
                        image_data = data.get("data")
                        if isinstance(image_data, list) and len(image_data) > 0:
                            image_url = image_data[0].get("url")
                            if image_url:
                                return {"status": "completed", "image_url": image_url}
                        elif isinstance(image_data, dict):
                            image_url = image_data.get("url")
                            if image_url:
                                return {"status": "completed", "image_url": image_url}
                    elif status in ["RUNNING", "PROCESSING", "PENDING"]:
                        return {"status": "processing"}
                    elif status in ["FAILED", "ERROR"]:
                        return {"status": "failed", "error": data.get("fail_reason", "任务失败")}
            else:
                # 其他服务商的响应格式
                if result_data.get("code") == 0:
                    result_data_obj = result_data.get("data", {})
                    status = result_data_obj.get("status", "").lower()
                    image_url = result_data_obj.get("url")

                    if status in ["succeeded", "completed", "success"] and image_url:
                        return {"status": "completed", "image_url": image_url}
                    elif status in ["running", "processing", "pending"]:
                        return {"status": "processing"}
                    elif status in ["failed", "error"]:
                        return {
                            "status": "failed",
                            "error": result_data_obj.get("error", "任务失败"),
                        }

            return {"status": "processing"}
        except Exception as e:
            logger.warning("轮询响应解析失败: {str(e)}")
            return {"status": "failed", "error": f"响应解析失败: {str(e)}"}
