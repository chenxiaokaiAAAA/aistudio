# -*- coding: utf-8 -*-
"""
veo-video 服务商实现
VEO 视频生成 API
"""

import logging

logger = logging.getLogger(__name__)
import json
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseAPIProvider


class VeoVideoProvider(BaseAPIProvider):
    """veo-video 服务商实现（VEO 视频生成）"""

    def __init__(self, api_config):
        """初始化"""
        super().__init__(api_config)
        # 检查是否是T8Star服务商
        self.is_t8star = self.host and "t8star.cn" in self.host.lower()

    def build_request_headers(self, **kwargs) -> Dict[str, str]:
        """构建请求头"""
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def build_request_body(
        self,
        prompt: str,
        model_name: str,
        uploaded_images: Optional[List[str]] = None,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        enhance_prompt: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        构建请求体（VEO 视频生成格式）

        Args:
            prompt: 提示词
            model_name: 模型名称
            uploaded_images: 图片URL列表（必需参数）
            aspect_ratio: 图片比例（VEO只支持16:9和9:16）
            image_size: 图片尺寸（VEO不使用）
            enhance_prompt: 是否优化提示词（中文自动转英文）
            **kwargs: 其他参数

        Returns:
            请求体字典
        """
        payload = {"prompt": prompt, "model": model_name}

        # 处理图片（必需参数，使用URL数组）
        image_urls_to_process = uploaded_images or []
        if image_urls_to_process and len(image_urls_to_process) > 0:
            # 根据模型限制图片数量
            max_images = 3  # 默认最多3张
            if model_name == "veo3-pro-frames":
                max_images = 1
            elif model_name in ["veo2-fast-frames", "veo3.1", "veo3.1-pro"]:
                max_images = 2
            elif model_name in ["veo2-fast-components", "veo3.1-components"]:
                max_images = 3

            images_to_send = image_urls_to_process[:max_images]
            payload["images"] = images_to_send
            logger.info(
                f"📸 [VEO] 使用 {len(images_to_send)} 张图片（模型 {model_name} 限制最多 {max_images} 张）"
            )

        # VEO只支持9:16和16:9比例
        if aspect_ratio and aspect_ratio != "auto":
            if aspect_ratio in ["16:9", "9:16"]:
                payload["aspect_ratio"] = aspect_ratio
            else:
                logger.warning("[VEO] 不支持的比例 {aspect_ratio}，VEO只支持16:9和9:16")

        payload["enhance_prompt"] = enhance_prompt if enhance_prompt else False

        # T8Star服务商的VEO API支持异步模式
        if self.is_t8star:
            payload["async"] = "true"
            logger.info("📝 [VEO] T8Star服务商：启用异步模式（async=true）")

        return payload

    def call_api(
        self,
        draw_url: str,
        request_data: Dict[str, Any],
        timeout: int = 30,
        proxies: Optional[Dict] = None,
    ) -> requests.Response:
        """
        调用API（VEO视频生成可能需要更长的超时时间）
        """
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

        # VEO视频生成可能需要更长的超时时间（30-300秒）
        logger.info(f"📤 调用 VEO 视频生成 API: {draw_url}")
        logger.info(f"📤 请求参数: {json.dumps(request_data, ensure_ascii=False)}")
        logger.info("📤 超时设置: 连接30秒, 读取300秒（视频生成需要较长时间）")

        response = session.post(
            draw_url,
            json=request_data,
            headers=headers,
            timeout=(30, 300),  # 连接30秒，读取300秒
            proxies=proxies,
        )

        logger.info(f"✅ VEO API响应状态码: {response.status_code}")
        return response

    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应（VEO 视频生成格式）
        """
        if response.status_code == 200:
            try:
                data = response.json()
                # VEO API响应格式可能因服务商而异
                # 常见格式：{"code": 0, "data": {"task_id": "xxx"}, "msg": "success"}
                # 或：{"task_id": "xxx"}
                # 或：{"id": "xxx"}

                task_id = None
                if "data" in data and isinstance(data.get("data"), dict):
                    task_id = (
                        data.get("data", {}).get("task_id")
                        or data.get("data", {}).get("taskId")
                        or data.get("data", {}).get("id")
                    )
                elif "task_id" in data:
                    task_id = data.get("task_id")
                elif "taskId" in data:
                    task_id = data.get("taskId")
                elif "id" in data:
                    task_id = data.get("id")

                if task_id:
                    return {"success": True, "task_id": task_id, "data": data}
                elif data.get("code") == 0:
                    # code == 0 但没有 task_id，可能是其他格式
                    return {"success": True, "data": data}
                else:
                    return {"success": False, "error": data.get("msg", "API调用失败")}
            except Exception:
                return {"success": False, "error": "响应解析失败"}
        else:
            error_text = response.text[:1000] if hasattr(response, "text") else "无法读取响应"
            return {"success": False, "error": f"HTTP {response.status_code}: {error_text}"}

    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求（VEO 视频生成使用POST方法）
        """
        endpoint = self.get_polling_endpoint(task_id)
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.host.rstrip('/')}{endpoint}"

        headers = self.build_request_headers()

        # VEO API轮询使用POST，请求体格式：{"Id": task_id} 或 {"task_id": task_id}
        request_body = {"Id": task_id}  # 默认格式

        return url, request_body, headers

    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应（VEO 视频生成格式）
        """
        if response.status_code != 200:
            return {"status": "failed", "error": f"HTTP {response.status_code}"}

        try:
            data = response.json()
            # VEO API响应格式可能因服务商而异
            # 常见格式：{"code": 0, "data": {"status": "succeeded", "video_url": "..."}}
            if data.get("code") == 0:
                result_data = data.get("data", {})
                status = result_data.get("status", "").lower()
                video_url = (
                    result_data.get("video_url")
                    or result_data.get("url")
                    or result_data.get("videoUrl")
                )

                if status in ["succeeded", "completed", "success"] and video_url:
                    return {
                        "status": "completed",
                        "image_url": video_url,  # 使用 image_url 字段名保持一致性（实际是视频URL）
                        "video_url": video_url,  # 同时提供 video_url 字段
                    }
                elif status in ["running", "processing", "pending"]:
                    return {"status": "processing"}
                elif status in ["failed", "error"]:
                    return {"status": "failed", "error": result_data.get("error", "任务失败")}

            return {"status": "processing"}
        except Exception as e:
            logger.warning("轮询响应解析失败: {str(e)}")
            return {"status": "failed", "error": f"响应解析失败: {str(e)}"}
