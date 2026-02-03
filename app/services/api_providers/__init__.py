# -*- coding: utf-8 -*-
"""
API服务商模块
提供统一的服务商注册和获取机制
"""
from typing import Dict, Type, Optional
from .base import BaseAPIProvider

# 服务商注册表（延迟导入，避免循环依赖）
_PROVIDER_REGISTRY: Dict[str, Type[BaseAPIProvider]] = {}

def register_provider(api_type: str, provider_class: Type[BaseAPIProvider]):
    """注册服务商类"""
    _PROVIDER_REGISTRY[api_type] = provider_class
    print(f"✅ 注册服务商: {api_type} -> {provider_class.__name__}")

def get_provider(api_config) -> Optional[BaseAPIProvider]:
    """
    根据API配置获取对应的服务商实例
    
    Args:
        api_config: APIProviderConfig对象
    
    Returns:
        BaseAPIProvider实例，如果不支持则返回None
    """
    api_type = api_config.api_type if hasattr(api_config, 'api_type') else None
    if not api_type:
        return None
    
    provider_class = _PROVIDER_REGISTRY.get(api_type)
    if not provider_class:
        return None
    
    try:
        return provider_class(api_config)
    except Exception as e:
        print(f"⚠️ 创建服务商实例失败 ({api_type}): {str(e)}")
        return None

def is_provider_supported(api_type: str) -> bool:
    """检查是否支持指定的服务商类型"""
    return api_type in _PROVIDER_REGISTRY

def get_supported_providers() -> list:
    """获取所有已注册的服务商类型"""
    return list(_PROVIDER_REGISTRY.keys())

# 延迟导入服务商实现（避免循环依赖）
def _lazy_import_providers():
    """延迟导入所有服务商实现"""
    try:
        from . import nano_banana_provider
        # 注册 nano-banana 服务商
        if hasattr(nano_banana_provider, 'NanoBananaProvider'):
            register_provider('nano-banana', nano_banana_provider.NanoBananaProvider)
    except ImportError as e:
        print(f"⚠️ 导入 nano-banana 服务商实现失败: {str(e)}")
    
    try:
        from . import nano_banana_edits_provider
        # 注册 nano-banana-edits 服务商
        if hasattr(nano_banana_edits_provider, 'NanoBananaEditsProvider'):
            register_provider('nano-banana-edits', nano_banana_edits_provider.NanoBananaEditsProvider)
    except ImportError as e:
        print(f"⚠️ 导入 nano-banana-edits 服务商实现失败: {str(e)}")
    
    try:
        from . import gemini_native_provider
        # 注册 gemini-native 服务商
        if hasattr(gemini_native_provider, 'GeminiNativeProvider'):
            register_provider('gemini-native', gemini_native_provider.GeminiNativeProvider)
    except ImportError as e:
        print(f"⚠️ 导入 gemini-native 服务商实现失败: {str(e)}")
    
    try:
        from . import runninghub_rhart_edit_provider
        # 注册 runninghub-rhart-edit 服务商
        if hasattr(runninghub_rhart_edit_provider, 'RunningHubRhartEditProvider'):
            register_provider('runninghub-rhart-edit', runninghub_rhart_edit_provider.RunningHubRhartEditProvider)
    except ImportError as e:
        print(f"⚠️ 导入 runninghub-rhart-edit 服务商实现失败: {str(e)}")
    
    try:
        from . import veo_video_provider
        # 注册 veo-video 服务商
        if hasattr(veo_video_provider, 'VeoVideoProvider'):
            register_provider('veo-video', veo_video_provider.VeoVideoProvider)
    except ImportError as e:
        print(f"⚠️ 导入 veo-video 服务商实现失败: {str(e)}")
    
    try:
        from . import runninghub_comfyui_workflow_provider
        # 注册 runninghub-comfyui-workflow 服务商
        if hasattr(runninghub_comfyui_workflow_provider, 'RunningHubComfyUIWorkflowProvider'):
            register_provider('runninghub-comfyui-workflow', runninghub_comfyui_workflow_provider.RunningHubComfyUIWorkflowProvider)
    except ImportError as e:
        print(f"⚠️ 导入 runninghub-comfyui-workflow 服务商实现失败: {str(e)}")

# 自动导入（首次使用时）
_lazy_import_providers()
