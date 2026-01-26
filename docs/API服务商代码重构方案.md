# API服务商代码重构方案

## 当前问题分析

### 1. 代码集中度过高
- `ai_provider_service.py`: 1974行，包含所有服务商的API调用逻辑
- `ai_task_polling_service.py`: 1422行，包含所有服务商的轮询逻辑
- 有20+个 `api_type ==` 的判断分支

### 2. 维护困难
- 添加新服务商需要修改大文件，容易出错
- 不同服务商的逻辑混杂，难以定位问题
- 代码可读性差，if-elif链很长

### 3. 当前支持的服务商
- nano-banana
- nano-banana-edits
- gemini-native
- veo-video
- runninghub-rhart-edit
- runninghub-comfyui-workflow

## 重构方案：按服务商模块化

### 方案1：完全模块化（推荐）

```
aistudio/app/services/api_providers/
├── __init__.py                    # 统一接口和注册机制
├── base.py                        # 基础抽象类
├── nano_banana.py                 # nano-banana服务商
├── nano_banana_edits.py           # nano-banana-edits服务商
├── gemini_native.py               # gemini-native服务商
├── veo_video.py                   # veo-video服务商
├── runninghub_rhart_edit.py       # RunningHub全能图片PRO
└── runninghub_comfyui_workflow.py # RunningHub ComfyUI工作流
```

**优点：**
- 每个服务商独立文件，职责清晰
- 易于添加新服务商（只需新建文件）
- 便于单元测试
- 代码可读性强

**缺点：**
- 需要重构现有代码
- 需要定义统一的接口规范

### 方案2：混合方案（渐进式重构）

保持现有文件结构，但按服务商拆分逻辑：

```
aistudio/app/services/
├── ai_provider_service.py         # 保留，作为统一入口
├── api_providers/                 # 新增目录
│   ├── __init__.py
│   ├── base.py                    # 基础抽象类
│   ├── nano_banana_provider.py
│   ├── gemini_provider.py
│   ├── runninghub_provider.py
│   └── ...
```

**优点：**
- 渐进式重构，不影响现有功能
- 可以逐步迁移代码
- 保持向后兼容

**缺点：**
- 过渡期会有两套代码
- 需要维护兼容层

## 推荐实现：方案1（完全模块化）

### 1. 基础抽象类设计

```python
# app/services/api_providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseAPIProvider(ABC):
    """API服务商基础抽象类"""
    
    def __init__(self, api_config):
        self.api_config = api_config
        self.api_key = api_config.api_key
        self.host = api_config.host_domestic or api_config.host_overseas
    
    @abstractmethod
    def build_request_headers(self) -> Dict[str, str]:
        """构建请求头"""
        pass
    
    @abstractmethod
    def build_request_body(self, prompt: str, model_name: str, 
                          uploaded_images: List[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """构建请求体"""
        pass
    
    @abstractmethod
    def get_draw_endpoint(self) -> str:
        """获取绘画接口端点"""
        pass
    
    @abstractmethod
    def call_api(self, draw_url: str, request_data: Dict[str, Any]) -> Any:
        """调用API"""
        pass
    
    @abstractmethod
    def parse_response(self, response: Any) -> Dict[str, Any]:
        """解析API响应"""
        pass
    
    @abstractmethod
    def get_polling_endpoint(self, task_id: str) -> str:
        """获取轮询接口端点"""
        pass
    
    @abstractmethod
    def build_polling_request(self, task_id: str) -> tuple[str, Dict[str, Any], Dict[str, str]]:
        """构建轮询请求（返回URL、请求体、请求头）"""
        pass
    
    @abstractmethod
    def parse_polling_response(self, response: Any) -> Dict[str, Any]:
        """解析轮询响应"""
        pass
```

### 2. 具体服务商实现示例

```python
# app/services/api_providers/nano_banana_provider.py
from .base import BaseAPIProvider
import requests
import json

class NanoBananaProvider(BaseAPIProvider):
    """nano-banana服务商实现"""
    
    def build_request_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def build_request_body(self, prompt: str, model_name: str,
                          uploaded_images: List[str] = None,
                          aspect_ratio: str = '1:1',
                          image_size: str = '1K',
                          **kwargs) -> Dict[str, Any]:
        return {
            "model": model_name,
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "imageSize": image_size,
            # ... 其他参数
        }
    
    def get_draw_endpoint(self) -> str:
        return self.api_config.draw_endpoint or '/v1/draw/nano-banana'
    
    def call_api(self, draw_url: str, request_data: Dict[str, Any]) -> Any:
        headers = self.build_request_headers()
        response = requests.post(draw_url, json=request_data, headers=headers, timeout=30)
        return response
    
    def parse_response(self, response: Any) -> Dict[str, Any]:
        if response.status_code == 200:
            return response.json()
        return {"error": f"API调用失败: {response.status_code}"}
    
    def get_polling_endpoint(self, task_id: str) -> str:
        return self.api_config.result_endpoint or '/v1/draw/result'
    
    def build_polling_request(self, task_id: str) -> tuple[str, Dict[str, Any], Dict[str, str]]:
        url = f"{self.host.rstrip('/')}{self.get_polling_endpoint(task_id)}"
        request_body = {"Id": task_id}  # 或 {"task_id": task_id}，根据服务商而定
        headers = self.build_request_headers()
        return url, request_body, headers
    
    def parse_polling_response(self, response: Any) -> Dict[str, Any]:
        if response.status_code == 200:
            data = response.json()
            # 解析不同服务商的响应格式
            if data.get('code') == 0:
                return {
                    "status": "completed",
                    "image_url": data.get('data', {}).get('url')
                }
        return {"status": "processing"}
```

### 3. 统一注册和调用机制

```python
# app/services/api_providers/__init__.py
from .base import BaseAPIProvider
from .nano_banana_provider import NanoBananaProvider
from .nano_banana_edits_provider import NanoBananaEditsProvider
from .gemini_native_provider import GeminiNativeProvider
from .veo_video_provider import VeoVideoProvider
from .runninghub_rhart_edit_provider import RunningHubRhartEditProvider
from .runninghub_comfyui_workflow_provider import RunningHubComfyUIWorkflowProvider

# 服务商注册表
PROVIDER_REGISTRY = {
    'nano-banana': NanoBananaProvider,
    'nano-banana-edits': NanoBananaEditsProvider,
    'gemini-native': GeminiNativeProvider,
    'veo-video': VeoVideoProvider,
    'runninghub-rhart-edit': RunningHubRhartEditProvider,
    'runninghub-comfyui-workflow': RunningHubComfyUIWorkflowProvider,
}

def get_provider(api_config) -> BaseAPIProvider:
    """根据API配置获取对应的服务商实例"""
    provider_class = PROVIDER_REGISTRY.get(api_config.api_type)
    if not provider_class:
        raise ValueError(f"不支持的服务商类型: {api_config.api_type}")
    return provider_class(api_config)
```

### 4. 重构后的调用方式

```python
# app/services/ai_provider_service.py (重构后)
from app.services.api_providers import get_provider

def call_api_with_config(api_config, draw_url, request_data, ...):
    """统一API调用入口"""
    provider = get_provider(api_config)
    
    # 使用服务商特定的方法
    headers = provider.build_request_headers()
    request_body = provider.build_request_body(
        prompt=prompt,
        model_name=model_name,
        uploaded_images=uploaded_images,
        aspect_ratio=aspect_ratio,
        image_size=image_size
    )
    
    response = provider.call_api(draw_url, request_body)
    return provider.parse_response(response)
```

### 5. 轮询服务重构

```python
# app/services/ai_task_polling_service.py (重构后)
from app.services.api_providers import get_provider

def poll_processing_tasks():
    """轮询处理中的任务"""
    for task in processing_tasks:
        api_config = get_api_config(task)
        provider = get_provider(api_config)
        
        # 使用服务商特定的轮询方法
        url, request_body, headers = provider.build_polling_request(task_id)
        
        if provider.use_get_method():
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, json=request_body, headers=headers, timeout=30)
        
        result = provider.parse_polling_response(response)
        # 处理结果...
```

## 重构步骤

### 阶段1：创建基础架构（1-2天）
1. 创建 `api_providers` 目录和基础抽象类
2. 实现注册机制
3. 创建第一个服务商实现（如 nano-banana）作为示例

### 阶段2：逐步迁移（3-5天）
1. 逐个迁移服务商代码
2. 保持向后兼容，新旧代码并存
3. 添加单元测试

### 阶段3：清理和优化（1-2天）
1. 移除旧代码
2. 优化统一接口
3. 更新文档

## 优势总结

1. **可维护性**：每个服务商独立文件，职责清晰
2. **可扩展性**：添加新服务商只需新建文件，无需修改现有代码
3. **可测试性**：每个服务商可以独立测试
4. **可读性**：代码结构清晰，易于理解
5. **团队协作**：不同开发者可以并行开发不同服务商

## 建议

**强烈建议采用方案1（完全模块化）**，因为：
- 当前代码已经比较复杂，重构收益大
- 未来还会添加更多服务商，模块化是必然趋势
- 重构后代码质量会显著提升

如果担心影响现有功能，可以采用渐进式重构：
1. 先创建新架构
2. 逐步迁移服务商代码
3. 保持新旧代码并存一段时间
4. 完全迁移后删除旧代码
