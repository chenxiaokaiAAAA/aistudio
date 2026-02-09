# -*- coding: utf-8 -*-
"""
RunningHub ComfyUI 工作流 服务商实现
"""

import logging

logger = logging.getLogger(__name__)
import json
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseAPIProvider


class RunningHubComfyUIWorkflowProvider(BaseAPIProvider):
    """RunningHub ComfyUI 工作流 服务商实现"""

    def get_draw_endpoint(self) -> str:
        """获取绘画接口端点"""
        return "/task/openapi/create"

    def build_request_headers(self, **kwargs) -> Dict[str, str]:
        """
        构建请求头（RunningHub ComfyUI 工作流不需要 Authorization，API Key 在请求体中）
        """
        headers = {"Content-Type": "application/json", "Host": "www.runninghub.cn"}
        # 注意：不包含 Authorization，API Key 在请求体的 apiKey 字段中
        return headers

    def build_request_body(
        self,
        prompt: str,
        model_name: str,
        uploaded_images: Optional[List[str]] = None,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        request_body_template: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        构建请求体（RunningHub ComfyUI 工作流格式）

        Args:
            prompt: 提示词
            model_name: 模型名称（RunningHub ComfyUI 工作流不使用）
            uploaded_images: 图片URL列表
            aspect_ratio: 图片比例（RunningHub ComfyUI 工作流不使用）
            image_size: 图片尺寸（RunningHub ComfyUI 工作流不使用）
            request_body_template: 从 APITemplate.request_body_template 解析的JSON对象
            **kwargs: 其他参数（可能包含已构建好的 request_data）

        Returns:
            请求体字典，包含 apiKey, workflowId, nodeInfoList 等
        """
        # 关键修复：如果 request_data 已经构建好（从 create_api_task 传递），直接使用
        # 这样可以避免重复构建，保持与旧代码的兼容性
        if kwargs.get("request_data") and isinstance(kwargs.get("request_data"), dict):
            request_data = kwargs.get("request_data")
            # 检查是否已经包含完整的请求体
            if (
                "apiKey" in request_data
                and "workflowId" in request_data
                and "nodeInfoList" in request_data
            ):
                logger.info("✅ RunningHub ComfyUI 工作流：使用已构建的请求体")
                return request_data

        # 否则，从 request_body_template 重新构建
        if not request_body_template or not request_body_template.get("workflow_id"):
            raise Exception("RunningHub ComfyUI 工作流未配置 workflow_id")

        workflow_id = request_body_template.get("workflow_id")
        node_info_list_raw = request_body_template.get("nodeInfoList", [])

        # 处理图片和提示词：将实际值替换占位符
        image_urls_to_process = uploaded_images or []
        final_prompt = prompt or ""

        logger.info("📸 RunningHub ComfyUI 工作流：准备转换 nodeInfoList 格式")
        logger.info(f"   - 工作流ID: {workflow_id}")
        logger.info(f"   - 图片数量: {len(image_urls_to_process)}")
        logger.info(f"   - 提示词: {final_prompt[:50] if final_prompt else 'None'}...")

        # 转换 nodeInfoList 格式
        node_info_list = []
        image_index = 0

        for node_info in node_info_list_raw:
            node_id = node_info.get("nodeId")
            if not node_id:
                continue

            # 如果已经是正确的格式（fieldName/fieldValue），直接使用
            if "fieldName" in node_info and "fieldValue" in node_info:
                field_name = node_info["fieldName"]
                field_value = node_info["fieldValue"]

                # 替换占位符
                if field_name in ["image", "imageUrls"]:
                    if (
                        field_value == "{{image_url}}"
                        or field_value == ""
                        or field_value == "{{ref_image_url}}"
                    ) and image_index < len(image_urls_to_process):
                        field_value = image_urls_to_process[image_index]
                        logger.info(
                            f"   ✅ 替换节点 {node_id} 的 {field_name}: {image_urls_to_process[image_index]}"
                        )
                        image_index += 1
                elif field_name == "text":
                    if field_value == "{{prompt}}" and final_prompt:
                        field_value = final_prompt
                        logger.info(
                            f"   ✅ 替换节点 {node_id} 的 {field_name}: {final_prompt[:50]}..."
                        )

                node_info_list.append(
                    {
                        "nodeId": str(node_id),
                        "fieldName": field_name,
                        "fieldValue": str(field_value) if field_value is not None else "",
                    }
                )
            # 如果是旧格式（inputs 对象），转换为新格式
            elif "inputs" in node_info:
                inputs = node_info["inputs"]
                for field_name, field_value in inputs.items():
                    # 替换占位符
                    if field_name in ["image", "imageUrls"]:
                        if (
                            field_value == "{{image_url}}"
                            or field_value == ""
                            or field_value == "{{ref_image_url}}"
                        ) and image_index < len(image_urls_to_process):
                            field_value = image_urls_to_process[image_index]
                            logger.info(
                                f"   ✅ 替换节点 {node_id} 的 {field_name}: {image_urls_to_process[image_index]}"
                            )
                            image_index += 1
                    elif field_name == "text":
                        if field_value == "{{prompt}}" and final_prompt:
                            field_value = final_prompt
                            logger.info(
                                f"   ✅ 替换节点 {node_id} 的 {field_name}: {final_prompt[:50]}..."
                            )

                    # 如果 field_value 是列表或字典，转换为 JSON 字符串
                    if isinstance(field_value, (list, dict)):
                        field_value = json.dumps(field_value, ensure_ascii=False)
                    else:
                        field_value = str(field_value) if field_value is not None else ""

                    node_info_list.append(
                        {"nodeId": str(node_id), "fieldName": field_name, "fieldValue": field_value}
                    )

        # 构建 RunningHub ComfyUI 工作流请求体
        request_data = {
            "apiKey": self.api_key,  # API Key 必须在请求体中
            "workflowId": workflow_id,  # workflowId 在请求体中，不在 URL 路径中
            "nodeInfoList": node_info_list,
        }

        # 可选参数：如果配置中有，使用配置的值；否则使用默认值
        if request_body_template:
            request_data["addMetadata"] = request_body_template.get("addMetadata", False)
            request_data["instanceType"] = request_body_template.get("instanceType", "default")
            request_data["usePersonalQueue"] = request_body_template.get("usePersonalQueue", False)
        else:
            request_data["addMetadata"] = False
            request_data["instanceType"] = "default"
            request_data["usePersonalQueue"] = False

        logger.info("📸 RunningHub ComfyUI 工作流：格式转换完成")
        logger.info(
            f"   - nodeInfoList 转换后数据: {json.dumps(node_info_list, ensure_ascii=False, indent=2)}"
        )

        return request_data

    def call_api(
        self,
        draw_url: str,
        request_data: Dict[str, Any],
        timeout: int = 30,
        proxies: Optional[Dict] = None,
    ) -> requests.Response:
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
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 代理设置
        if proxies is None:
            proxies = self.get_proxy_settings()

        # 超时设置：连接10秒，读取30秒（RunningHub 通常快速返回 taskId）
        logger.info(f"📤 调用 RunningHub ComfyUI 工作流 API: {draw_url}")
        logger.info(
            f"📤 请求头: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, ensure_ascii=False)}"
        )
        logger.info(f"📤 请求参数: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        logger.info(f"📤 API Key 长度: {len(self.api_key) if self.api_key else 0} 字符")

        response = session.post(
            draw_url, json=request_data, headers=headers, timeout=(10, 30), proxies=proxies
        )

        logger.info(f"✅ RunningHub ComfyUI 工作流 API响应状态码: {response.status_code}")

        # 如果是 401 错误，提供更详细的诊断信息
        if response.status_code == 401:
            logger.warning("401 未授权错误，可能的原因：")
            logger.info("   1. API Key 不正确或已过期")
            logger.info("   2. API Key 没有权限访问该工作流")
            logger.info("   3. API Key 需要在 RunningHub 控制台中绑定到工作流")
            logger.info("   4. 请求头或请求体中的 API Key 格式不正确")
            logger.info(
                f"   当前使用的 API Key 长度: {len(self.api_key) if self.api_key else 0} 字符"
            )
            logger.info("   当前使用的认证方式: apiKey (请求体)")

        return response

    def parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析API响应（RunningHub ComfyUI 工作流格式）
        """
        if response.status_code == 200:
            try:
                data = response.json()
                # RunningHub ComfyUI 工作流响应格式：
                # 成功：{"code": 0, "data": {"taskId": "xxx"}, "msg": "success"}
                # 失败：{"code": 433, "msg": "工作流验证失败...", "data": {...}}

                code = data.get("code", 0)

                # 关键修复：即使 code != 0，如果返回了 taskId，也应该标记为成功（任务已创建）
                task_id = None
                if "data" in data and isinstance(data.get("data"), dict):
                    task_id = data.get("data", {}).get("taskId")
                elif "taskId" in data:
                    task_id = data.get("taskId")

                if task_id:
                    # 有 taskId，说明任务已创建，即使有错误也应该标记为 processing
                    result = {"success": True, "task_id": task_id, "data": data}

                    # 如果有错误（code != 0），保存错误信息作为警告
                    if code != 0:
                        error_msg = data.get("msg", "")
                        # 尝试解析 node_errors（如果存在）
                        if "node_errors" in error_msg or "nodeErrors" in str(data):
                            try:
                                # msg 可能是 JSON 字符串
                                if isinstance(error_msg, str) and error_msg.startswith("{"):
                                    msg_data = json.loads(error_msg)
                                    node_errors = msg_data.get("node_errors", {})
                                    if node_errors:
                                        error_details = []
                                        for node_id, error in node_errors.items():
                                            error_details.append(f"节点 {node_id}: {error}")
                                        error_msg = "工作流验证失败:\n" + "\n".join(error_details)
                            except Exception:
                                pass
                        result["warning"] = error_msg
                        logger.warning("RunningHub ComfyUI 工作流任务已创建，但有警告: {error_msg}")

                    return result
                elif code == 0:
                    # code == 0 但没有 taskId，可能是其他格式
                    return {"success": True, "data": data}
                else:
                    # code != 0 且没有 taskId，说明任务创建失败
                    error_msg = data.get("msg", "任务创建失败")
                    # 尝试解析 node_errors
                    if "node_errors" in error_msg or "nodeErrors" in str(data):
                        try:
                            if isinstance(error_msg, str) and error_msg.startswith("{"):
                                msg_data = json.loads(error_msg)
                                node_errors = msg_data.get("node_errors", {})
                                if node_errors:
                                    error_details = []
                                    for node_id, error in node_errors.items():
                                        error_details.append(f"节点 {node_id}: {error}")
                                    error_msg = "工作流验证失败:\n" + "\n".join(error_details)
                        except Exception:
                            pass
                    return {"success": False, "error": error_msg}
            except Exception:
                return {"success": False, "error": "响应解析失败"}
        else:
            error_text = response.text[:1000] if hasattr(response, "text") else "无法读取响应"
            return {"success": False, "error": f"HTTP {response.status_code}: {error_text}"}

    def get_polling_endpoint(self, task_id: str) -> str:
        """
        获取轮询接口端点（与 runninghub-rhart-edit 相同）
        """
        endpoint = self.api_config.result_endpoint
        if endpoint and "/openapi/v2/query" in endpoint:
            return endpoint
        elif endpoint and "/task/openapi/outputs" in endpoint:
            return endpoint
        else:
            # 默认使用新格式
            return "/openapi/v2/query"

    def build_polling_request(self, task_id: str) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        构建轮询请求（与 runninghub-rhart-edit 相同）
        """
        endpoint = self.get_polling_endpoint(task_id)
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.host.rstrip('/')}{endpoint}"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # 判断使用哪种格式
        use_new_query_format = "/openapi/v2/query" in endpoint

        if use_new_query_format:
            # 新格式：/openapi/v2/query，请求体只需要 taskId
            request_body = {"taskId": task_id}
        else:
            # 旧格式：/task/openapi/outputs，请求体需要 apiKey 和 taskId
            request_body = {"apiKey": self.api_key, "taskId": task_id}

        return url, request_body, headers

    def parse_polling_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析轮询响应（与 runninghub-rhart-edit 相同）
        """
        if response.status_code != 200:
            return {"status": "failed", "error": f"HTTP {response.status_code}"}

        try:
            result_data = response.json()

            # RunningHub API响应格式：
            # 新格式：{"status": "SUCCESS/RUNNING/QUEUED/FAILED", "results": [{"url": "..."}], "errorMessage": "..."}
            # 旧格式：{"code": 0, "data": {"status": "...", "url": "..."}}

            status = None
            image_url = None
            error_msg = None

            # 检查新格式
            if "status" in result_data:
                status = result_data.get("status", "").upper()
                if status == "SUCCESS":
                    results = result_data.get("results", [])
                    if results and len(results) > 0:
                        image_url = results[0].get("url")
                elif status == "FAILED":
                    error_msg = result_data.get("errorMessage", "任务失败")
            # 检查旧格式
            elif result_data.get("code") == 0 and "data" in result_data:
                data = result_data.get("data", {})
                status_str = data.get("status", "").upper()
                if status_str == "SUCCESS":
                    status = "SUCCESS"
                    image_url = data.get("url")
                elif status_str in ["RUNNING", "PROCESSING", "QUEUED"]:
                    status = "RUNNING"
                elif status_str == "FAILED":
                    status = "FAILED"
                    error_msg = data.get("errorMessage", "任务失败")

            # 如果没有找到status，尝试从其他字段推断
            if not status:
                # 检查是否有错误信息
                if result_data.get("errorCode") or result_data.get("errorMessage"):
                    status = "FAILED"
                    error_msg = result_data.get(
                        "errorMessage", f"API错误 (errorCode={result_data.get('errorCode')})"
                    )
                else:
                    # 默认认为正在处理中
                    status = "RUNNING"

            # 返回结果
            if status == "SUCCESS" and image_url:
                return {"status": "completed", "image_url": image_url}
            elif status in ["RUNNING", "QUEUED"]:
                return {"status": "processing"}
            elif status == "FAILED":
                return {"status": "failed", "error": error_msg or "任务失败"}
            else:
                return {"status": "processing"}
        except Exception as e:
            logger.warning("轮询响应解析失败: {str(e)}")
            return {"status": "failed", "error": f"响应解析失败: {str(e)}"}
