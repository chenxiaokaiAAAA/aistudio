# -*- coding: utf-8 -*-
"""
云端API服务商调用服务
处理不同服务商的API调用（nano-banana, gemini-native, veo-video等）
"""
import json
import os
import time
import requests
import base64
import shutil
from datetime import datetime
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Semaphore
from app.utils.config_loader import get_int_config

# 限流机制：限制API并发调用数（从数据库读取配置）
# 全局信号量（会在首次使用时初始化）
API_SEMAPHORE = None

def _get_api_semaphore():
    """获取或创建API信号量"""
    global API_SEMAPHORE
    if API_SEMAPHORE is None:
        max_concurrency = get_int_config('api_max_concurrency', 5)
        API_SEMAPHORE = Semaphore(max_concurrency)
        print(f"✅ API并发信号量已初始化: {max_concurrency}")
    return API_SEMAPHORE


def call_api_with_config(api_config, draw_url, request_data, uploaded_image_url=None, uploaded_image_urls=None, 
                         upload_config=None, model_name='nano-banana', prompt='', aspect_ratio='1:1', image_size='1K', enhance_prompt=False):
    """
    根据API配置类型调用不同的API
    
    Args:
        api_config: APIProviderConfig对象
        draw_url: 完整的API URL
        request_data: 请求数据（用于nano-banana类型）
        uploaded_image_url: 上传的图片URL（单图，向后兼容）
        uploaded_image_urls: 上传的图片URL列表（多图）
        model_name: 模型名称
        prompt: 提示词
        aspect_ratio: 图片比例
        image_size: 图片尺寸
        enhance_prompt: 是否优化提示词（VEO模型：中文自动转英文）
    
    Returns:
        response对象
    """
    # 尝试使用新的模块化服务商实现（渐进式重构）
    try:
        from app.services.api_providers import get_provider, is_provider_supported
        
        if is_provider_supported(api_config.api_type):
            provider = get_provider(api_config)
            if provider:
                print(f"✅ 使用模块化服务商实现: {api_config.api_type}")
                # 使用新的模块化实现
                uploaded_images = uploaded_image_urls if uploaded_image_urls else ([uploaded_image_url] if uploaded_image_url else None)
                
                # 构建请求体（不同服务商可能有不同的格式）
                request_body_kwargs = {
                    'prompt': prompt,
                    'model_name': model_name,
                    'uploaded_images': uploaded_images,
                    'aspect_ratio': aspect_ratio,
                    'image_size': image_size
                }
                
                # 添加额外的参数（如果request_data存在）
                if request_data and isinstance(request_data, dict):
                    request_body_kwargs.update({
                        'shutProgress': request_data.get('shutProgress', False),
                        'webHook': request_data.get('webHook', "-1")
                    })
                    
                    # RunningHub ComfyUI 工作流特殊处理
                    if api_config.api_type == 'runninghub-comfyui-workflow':
                        # 关键修复：如果 request_data 已经包含完整的请求体（从 create_api_task 构建），直接传递
                        if request_data and isinstance(request_data, dict) and 'apiKey' in request_data and 'workflowId' in request_data:
                            # request_data 已经构建好，直接使用
                            request_body_kwargs['request_data'] = request_data
                        elif 'request_body_template' in request_data:
                            # 从 request_data 中提取 request_body_template
                            request_body_kwargs['request_body_template'] = request_data.get('request_body_template')
                        # 或者 request_data 本身就是 request_body_template
                        elif 'workflow_id' in request_data or 'nodeInfoList' in request_data:
                            request_body_kwargs['request_body_template'] = request_data
                
                request_body = provider.build_request_body(**request_body_kwargs)
                proxies = provider.get_proxy_settings()
                
                # 获取正确的draw_url（某些服务商可能需要特殊处理）
                if hasattr(provider, 'get_draw_url'):
                    draw_url = provider.get_draw_url()
                
                response = provider.call_api(draw_url, request_body, proxies=proxies)
                return response
    except Exception as e:
        print(f"⚠️ 使用模块化服务商实现失败，回退到旧实现: {str(e)}")
        import traceback
        traceback.print_exc()
        # 如果新实现失败，继续使用旧代码
    
    # 旧代码实现（保持向后兼容）
    # 根据API类型选择不同的调用方式
    if api_config.api_type == 'gemini-native':
        # gemini-native 类型会在后面单独处理 headers
        headers = {}
    else:
        # 其他类型使用标准的 Authorization Bearer
        headers = {
            "Authorization": f"Bearer {api_config.api_key}"
        }
    
    # 根据API类型选择不同的调用方式
    if api_config.api_type == 'veo-video':
        # VEO视频生成API（使用JSON格式，图片使用URL数组）
        headers["Content-Type"] = "application/json"
        
        # 构建请求体
        payload = {
            "prompt": prompt,
            "model": model_name
        }
        
        # 处理图片（必需参数，使用URL数组）
        image_urls_to_process = uploaded_image_urls if uploaded_image_urls else ([uploaded_image_url] if uploaded_image_url else None)
        if image_urls_to_process and len(image_urls_to_process) > 0:
            # 根据模型限制图片数量
            max_images = 3  # 默认最多3张
            if model_name == 'veo3-pro-frames':
                max_images = 1
            elif model_name in ['veo2-fast-frames', 'veo3.1', 'veo3.1-pro']:
                max_images = 2
            elif model_name in ['veo2-fast-components', 'veo3.1-components']:
                max_images = 3
            
            images_to_send = image_urls_to_process[:max_images]
            payload["images"] = images_to_send
        
        # VEO只支持9:16和16:9比例
        if aspect_ratio and aspect_ratio != 'auto':
            if aspect_ratio in ['16:9', '9:16']:
                payload["aspect_ratio"] = aspect_ratio
        
        payload["enhance_prompt"] = enhance_prompt if enhance_prompt else False
        
        # T8Star服务商的VEO API支持异步模式
        host = api_config.host_domestic or api_config.host_overseas
        if host and 't8star.cn' in host.lower():
            payload["async"] = "true"
        
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
        
        # VEO视频生成可能需要更长的超时时间（30-300秒）
        response = session.post(draw_url, json=payload, headers=headers, timeout=(30, 300))
        
    elif api_config.api_type == 'gemini-native':
        # 使用Google Gemini原生格式（JSON，图片base64编码）
        # 检查是否是直接调用 Google API
        host = api_config.host_domestic or api_config.host_overseas
        is_google_direct = host and 'generativelanguage.googleapis.com' in host
        is_proxy_server = host and '/api/gemini/generate' in (api_config.draw_endpoint or '')
        is_t8star = host and 't8star.cn' in host.lower()
        
        # 根据不同的服务商设置不同的认证方式
        if is_google_direct:
            if is_proxy_server:
                headers = {"Content-Type": "application/json"}
            else:
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_config.api_key
                }
        else:
            headers = {
                "Authorization": f"Bearer {api_config.api_key}",
                "Content-Type": "application/json"
            }
        
        # 构建parts（包含提示词和图片）
        parts = []
        
        # 处理图片：下载并转换为base64
        image_urls_to_process = uploaded_image_urls if uploaded_image_urls else ([uploaded_image_url] if uploaded_image_url else None)
        
        if image_urls_to_process:
            for img_url in image_urls_to_process:
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
        if is_t8star:
            # T8Star可能需要model参数
            if model_name:
                payload["model"] = model_name
        
        # 关键修复：为了在请求参数中显示图片信息，创建一个包含图片URL的request_data用于记录
        # gemini-native类型的实际请求体是payload（包含base64图片），但为了前端显示，我们需要记录图片URL
        request_data_for_log = {
            "model": model_name,
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "imageSize": image_size,
            "shutProgress": False,
            "webHook": "-1"
        }
        
        # 添加图片信息（用于前端显示）
        if image_urls_to_process:
            # 记录图片URL（用于前端显示）
            request_data_for_log["image_urls"] = image_urls_to_process
            request_data_for_log["image_count"] = len(image_urls_to_process)
            request_data_for_log["image_format"] = "base64_encoded_in_payload"
            print(f"📸 [gemini-native] 请求中包含 {len(image_urls_to_process)} 张图片（已转换为base64，包含在payload中）")
        else:
            print(f"⚠️ [gemini-native] 警告: 没有图片URL，API调用可能失败")
        
        # 发送请求
        session = requests.Session()
        
        # 关键修复：同步API（gemini-native）不应该重试，避免重复请求导致后端重复制作
        # 如果是同步API，禁用重试机制
        is_sync_api = api_config.is_sync_api if hasattr(api_config, 'is_sync_api') else False
        if is_sync_api:
            # 同步API：不重试，避免连接断开后重复请求导致后端重复制作
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
        
        # 代理设置：T8Star需要代理
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        proxy_url = None
        if has_proxy:
            proxy_url = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY') or os.environ.get('http_proxy') or os.environ.get('https_proxy')
        
        # 根据不同的服务商设置代理策略
        if is_t8star:
            # T8star服务商：如果检测到代理环境变量，就使用代理
            # 参考bk-photo-v4：使用proxies=None让requests自动使用环境变量中的代理（更稳定）
            if has_proxy and proxy_url:
                print(f"✅ [gemini-native] 检测到代理环境变量: {proxy_url}，T8star将通过代理连接")
                # 使用proxies=None让requests自动使用环境变量中的代理（更稳定，与bk-photo-v4一致）
                proxies = None  # None表示使用系统环境变量中的代理
            else:
                print(f"ℹ️ [gemini-native] 未检测到代理环境变量，T8star将直连")
                print(f"   提示：如果您的启动脚本设置了代理，请确保代理环境变量已正确设置")
                proxies = {'http': None, 'https': None}  # 禁用代理，直连
        elif is_google_direct:
            # 对于 Google API，如果检测到代理设置，使用代理
            if has_proxy and proxy_available:
                print(f"✅ [gemini-native] 检测到可用代理，Google API将通过代理连接")
                proxies = None
            else:
                print(f"ℹ️ [gemini-native] 未检测到可用代理，Google API将直连")
                proxies = {'http': None, 'https': None}
        else:
            # 其他服务商，根据域名判断
            if has_proxy and proxy_available:
                print(f"✅ [gemini-native] 检测到可用代理，将通过代理连接")
                proxies = None
            else:
                print(f"ℹ️ [gemini-native] 未检测到可用代理，将直连")
                proxies = {'http': None, 'https': None}
        
        # 超时设置：参考bk-photo-v4的实现
        # 关键说明：
        # 1. connect_timeout：连接建立 + 请求发送的超时（包含发送base64图片数据的时间）
        # 2. read_timeout：等待响应的超时（同步API的关键超时时间）
        # 3. 这两个超时是分开计算的，不是累加的
        # 4. 重要：如果使用代理，代理服务器（如Clash Verge）的proxy-timeout必须大于read_timeout
        #    否则代理会在proxy-timeout时间后关闭连接，导致请求失败
        #    建议Clash Verge设置：proxy-timeout: 900（15分钟）> read_timeout（8分钟）
        if is_t8star:
            # T8Star同步API：使用与bk-photo-v4完全相同的超时设置
            connect_timeout = 150  # 2.5分钟：连接建立 + 请求发送超时（包含发送base64图片数据的时间）
            read_timeout = 480     # 8分钟：等待响应超时（同步API的关键超时时间）
            print(f"📊 [T8Star同步API] 超时设置: 连接/发送={connect_timeout}秒（2.5分钟），等待响应={read_timeout}秒（8分钟）")
            print(f"   ⚠️ 注意：如果使用代理，请确保代理服务器的proxy-timeout > {read_timeout}秒（建议900秒）")
        else:
            # 其他服务商：使用较短的超时时间
            connect_timeout = 60
            read_timeout = 300  # 5分钟
        
        # 打印代理设置信息
        print(f"📤 [gemini-native] 发送请求到: {draw_url}")
        if proxies is None:
            # proxies=None表示使用系统环境变量中的代理
            if has_proxy and proxy_url:
                print(f"📤 [gemini-native] 代理设置: 使用系统代理 ({proxy_url})")
            else:
                print(f"📤 [gemini-native] 代理设置: 未使用代理")
        elif isinstance(proxies, dict):
            # proxies是字典，检查是否禁用了代理
            if proxies.get('http') is None and proxies.get('https') is None:
                print(f"📤 [gemini-native] 代理设置: 已禁用代理（直连）")
            else:
                # 显式设置了代理URL
                proxy_http = proxies.get('http', 'None')
                proxy_https = proxies.get('https', 'None')
                print(f"📤 [gemini-native] 代理设置: 使用显式代理 (http={proxy_http}, https={proxy_https})")
        else:
            print(f"📤 [gemini-native] 代理设置: {proxies}")
        print(f"📤 [gemini-native] 超时设置: connect={connect_timeout}s, read={read_timeout}s")
        
        # 关键修复：同步API如果连接断开，不应该重试（避免重复请求导致后端重复制作）
        # 但如果请求已发送成功（连接建立后），连接断开可能是代理超时，请求可能仍在处理中
        # 改进：更精确地判断错误类型，区分"连接建立前失败"和"连接建立后但响应超时"
        request_start_time = time.time()
        try:
            response = session.post(draw_url, json=payload, headers=headers, timeout=(connect_timeout, read_timeout), proxies=proxies)
            # 关键修复：将包含图片信息的request_data附加到response对象上，用于前端显示
            if 'request_data_for_log' in locals():
                response.request_data_for_log = request_data_for_log
        except requests.exceptions.ProxyError as e:
            # 代理错误：需要判断是连接建立前失败还是连接建立后失败
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            print(f"❌ [同步API] 代理错误: {error_str}")
            print(f"   代理URL: {proxy_url}")
            print(f"   请求耗时: {elapsed_time:.2f}秒")
            
            # 如果耗时很短（<5秒），可能是连接建立前失败
            # 如果耗时较长（>5秒），可能是连接建立后，请求已发送，但代理在等待响应时出错
            if elapsed_time > 5:
                print(f"⚠️ [同步API] 请求已发送（耗时{elapsed_time:.2f}秒），但代理在等待响应时出错")
                print(f"   提示: 请求可能已到达后端，后端可能正在处理或已完成")
                print(f"   问题分析: 代理服务器可能在{elapsed_time:.0f}秒后超时关闭了连接")
                print(f"   建议: 1) 检查代理服务器（Clash Verge）的超时设置，建议设置为10-15分钟")
                print(f"         2) 任务将保持'处理中'状态，请稍后手动检查后端结果")
                print(f"         3) 如果后端已完成，可能需要手动重新提交请求（注意避免重复制作）")
                raise Exception(f"连接被远程关闭，但请求可能已发送到后端（耗时{elapsed_time:.2f}秒）。代理服务器可能在{elapsed_time:.0f}秒后超时。如果后台已经成功生成，请检查代理服务器超时设置或手动检查结果。错误详情: {error_str}")
            else:
                print(f"❌ [同步API] 代理连接建立失败（耗时{elapsed_time:.2f}秒）")
                print(f"   建议: 请检查代理服务器是否正常运行（端口 {proxy_url.split(':')[-1] if proxy_url and ':' in proxy_url else 'N/A'}）")
                raise Exception(f"同步API代理连接失败。请检查代理服务器是否正常运行。代理: {proxy_url}，错误: {error_str}")
        except requests.exceptions.ConnectionError as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            # 检查是否是RemoteDisconnected错误（连接被远程关闭，没有收到响应）
            if 'RemoteDisconnected' in error_str or 'Remote end closed connection' in error_str:
                # 关键修复：RemoteDisconnected通常发生在请求已发送后，等待响应时连接被关闭
                # 此时请求可能已经到达后端并正在处理，不应该立即标记为失败
                print(f"⚠️ [同步API] 连接被远程关闭，未收到响应")
                print(f"   错误详情: {error_str}")
                print(f"   请求耗时: {elapsed_time:.2f}秒")
                print(f"   代理URL: {proxy_url if has_proxy else '未使用代理'}")
                print(f"   提示: 请求可能已发送到后端（耗时{elapsed_time:.2f}秒），后端可能正在处理或已完成")
                print(f"   建议: 任务将保持'处理中'状态，请稍后手动检查结果或等待轮询服务检查")
                # 使用一个特殊的异常消息，让调用方知道这是"连接断开但请求可能已发送"
                raise Exception(f"连接被远程关闭，但请求可能已发送到后端（耗时{elapsed_time:.2f}秒）。如果后台已经成功生成，请稍后手动检查结果。错误详情: {error_str}")
            else:
                # 其他连接错误（可能是连接建立前失败）
                print(f"❌ [同步API] 连接失败: {error_str}")
                print(f"   请求耗时: {elapsed_time:.2f}秒")
                raise Exception(f"同步API连接失败: {error_str}")
        except requests.exceptions.Timeout as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            print(f"❌ [同步API] 请求超时: {error_str}")
            print(f"   请求耗时: {elapsed_time:.2f}秒")
            print(f"   超时设置: 连接={connect_timeout}秒，读取={read_timeout}秒")
            
            # 判断是连接超时还是读取超时
            if elapsed_time < connect_timeout:
                print(f"⚠️ [同步API] 连接建立超时（耗时{elapsed_time:.2f}秒 < {connect_timeout}秒）")
                raise Exception(f"同步API连接建立超时（{elapsed_time:.2f}秒）。请检查网络连接或代理设置。错误详情: {error_str}")
            else:
                print(f"⚠️ [同步API] 读取响应超时（耗时{elapsed_time:.2f}秒，已超过连接超时{connect_timeout}秒）")
                print(f"   提示: 连接已建立，请求可能已发送，但等待响应超时")
                print(f"   建议: 任务将保持'处理中'状态，请稍后手动检查结果")
                raise Exception(f"连接被远程关闭，但请求可能已发送到后端（耗时{elapsed_time:.2f}秒）。如果后台已经成功生成，请稍后手动检查结果。错误详情: {error_str}")
        except Exception as e:
            error_str = str(e)
            elapsed_time = time.time() - request_start_time
            print(f"❌ [同步API] 请求异常: {error_str}")
            print(f"   请求耗时: {elapsed_time:.2f}秒")
            import traceback
            traceback.print_exc()
            raise Exception(f"同步API请求失败: {error_str}")
    
    elif api_config.api_type == 'nano-banana-edits':
        # nano-banana-edits统一使用multipart/form-data格式
        # T8Star的/v1/images/edits端点也使用multipart/form-data格式
        
        # T8Star API异步模式：检查是否是T8Star服务商
        host = api_config.host_domestic or api_config.host_overseas
        is_t8star = host and 't8star.cn' in host.lower()
        
        # T8Star的nano-banana-edits API必须使用/v1/images/edits端点
        if is_t8star:
            correct_endpoint = '/v1/images/edits'
            # 检查draw_url是否包含错误的endpoint
            if '/v1/images/edits' not in draw_url or '/v1/draw/' in draw_url:
                print(f"⚠️ 检测到T8Star服务商的nano-banana-edits API，但URL不正确，自动修正")
                print(f"   原URL: {draw_url}")
                print(f"   原endpoint: {api_config.draw_endpoint}")
                draw_url = host.rstrip('/') + correct_endpoint
                print(f"   修正后URL: {draw_url}")
            else:
                print(f"✅ T8Star nano-banana-edits API使用正确的endpoint: {draw_url}")
        
        files = None
        data = {
            'model': model_name,
            'prompt': prompt,
            'response_format': 'url',
            'aspect_ratio': aspect_ratio,
            'image_size': image_size
        }
        
        # async参数应该作为查询参数（query parameter）
        params = {}
        if is_t8star:
            # T8Star nano-banana-edits API支持异步模式
            params['async'] = 'true'  # 启用异步模式，立即返回task_id
            print(f"📝 T8Star nano-banana-edits API：启用异步模式（async=true，作为查询参数）")
        
        # 处理图片：下载并作为文件上传（支持多图）
        image_urls_to_process = uploaded_image_urls if uploaded_image_urls else ([uploaded_image_url] if uploaded_image_url else None)
        
        # 如果image_urls_to_process为空，尝试从request_data中读取urls字段
        if not image_urls_to_process and request_data and isinstance(request_data, dict):
            if 'urls' in request_data:
                urls_from_request = request_data.get('urls')
                if isinstance(urls_from_request, list) and len(urls_from_request) > 0:
                    image_urls_to_process = urls_from_request
                elif isinstance(urls_from_request, str) and urls_from_request.strip():
                    try:
                        parsed_urls = json.loads(urls_from_request)
                        if isinstance(parsed_urls, list) and len(parsed_urls) > 0:
                            image_urls_to_process = parsed_urls
                    except:
                        image_urls_to_process = [urls_from_request]
        
        if image_urls_to_process:
            files = []
            try:
                # 处理多张图片
                if isinstance(image_urls_to_process, list):
                    for idx, img_url in enumerate(image_urls_to_process):
                        try:
                            # 下载图片
                            print(f"📥 正在下载图片 {idx+1}/{len(image_urls_to_process)}: {img_url}")
                            
                            # 检查是否是本地URL
                            is_local_url = (
                                img_url.startswith('/') or
                                '127.0.0.1' in img_url or 
                                'localhost' in img_url or 
                                '192.168.' in img_url
                            )
                            
                            if is_local_url:
                                # 本地URL：直接读取文件
                                if '/uploads/' in img_url:
                                    filename = img_url.split('/uploads/')[-1]
                                    local_file_path = os.path.join('uploads', filename)
                                elif '/media/original/' in img_url:
                                    filename = img_url.split('/media/original/')[-1]
                                    local_file_path = os.path.join('uploads', filename)
                                else:
                                    local_file_path = img_url.lstrip('/')
                                
                                if os.path.exists(local_file_path):
                                    with open(local_file_path, 'rb') as f:
                                        img_content = f.read()
                                else:
                                    raise Exception(f"本地文件不存在: {local_file_path}")
                            else:
                                # 云端URL：使用HTTP下载
                                proxies = {'http': None, 'https': None}  # 禁用代理
                                img_response = requests.get(img_url, proxies=proxies, timeout=30)
                                img_response.raise_for_status()
                                img_content = img_response.content
                            
                            # 获取文件名
                            filename = os.path.basename(urlparse(img_url).path) or f'image_{idx}.jpg'
                            
                            # 准备文件（nano-banana-edits支持多图，使用image格式，多图时使用image[]）
                            if len(image_urls_to_process) > 1:
                                files.append(('image[]', (filename, img_content, 'image/jpeg')))
                            else:
                                files.append(('image', (filename, img_content, 'image/jpeg')))
                            
                            print(f"✅ 已下载图片 {idx+1}/{len(image_urls_to_process)}: {filename}, 大小: {len(img_content)} bytes")
                        except Exception as e:
                            print(f"❌ 下载图片 {idx+1} 失败: {str(e)}")
                            import traceback
                            traceback.print_exc()
                
                if not files:
                    print(f"⚠️ 所有图片下载失败")
                    raise Exception("所有图片下载失败，无法调用API")
            except Exception as e:
                print(f"处理图片失败: {str(e)}")
                raise
        
        print(f"调用 nano-banana-edits API (multipart): {draw_url}")
        print(f"请求参数: {data}")
        print(f"上传文件数量: {len(files) if files else 0}")
        
        # 如果所有图片下载失败，files为空，不应该继续调用API
        if not files:
            raise Exception("所有图片下载失败，无法调用API")
        
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
        
        # 增加超时时间到300秒（5分钟）
        print(f"⏳ 开始调用API，超时时间: 300秒（5分钟）")
        try:
            response = session.post(draw_url, data=data, files=files, params=params, headers=headers, timeout=(10, 300))
            print(f"✅ nano-banana-edits API响应状态码: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"❌ API调用超时（超过300秒）")
            raise
        except requests.exceptions.ConnectionError as e:
            error_msg = f"❌ nano-banana-edits API连接失败: {str(e)}"
            print(error_msg)
            raise Exception(f"无法连接到API服务器，请检查网络连接。错误详情: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"❌ API请求异常: {str(e)}")
            raise
        
        # 打印响应信息
        if response.status_code != 200:
            print(f"❌ API调用失败，状态码: {response.status_code}")
            try:
                error_text = response.text
                print(f"❌ API错误响应内容: {error_text}")
            except:
                pass
        else:
            try:
                response_text = response.text
                print(f"📄 API完整响应内容: {response_text}")
            except:
                pass
    
    elif api_config.api_type == 'runninghub-comfyui-workflow':
        # RunningHub ComfyUI 工作流 API
        # 接口：/task/openapi/create
        # 请求格式：application/json
        # 参考文档：https://www.runninghub.cn/runninghub-api-doc-cn/doc-7534195
        
        # 注意：request_data 应该已经在 create_api_task 中构建完成
        # 包含：apiKey, workflowId, nodeInfoList（格式：{"nodeId": "x", "fieldName": "y", "fieldValue": "z"}）
        
        headers["Content-Type"] = "application/json"
        headers["Host"] = "www.runninghub.cn"
        
        # 根据文档，API Key 在请求体中（apiKey 字段），不需要在请求头中
        # 移除 Authorization Bearer，只使用请求体中的 apiKey
        if "Authorization" in headers:
            del headers["Authorization"]
        if "X-API-Key" in headers:
            del headers["X-API-Key"]
        
        # request_data 应该已经包含 nodeInfoList 等参数（在 create_api_task 中构建）
        print(f"调用 RunningHub ComfyUI 工作流 API: {draw_url}")
        print(f"请求头: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, ensure_ascii=False)}")
        print(f"请求参数: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        print(f"API Key 长度: {len(api_config.api_key) if api_config.api_key else 0} 字符")
        
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
        
        # 超时设置：连接10秒，读取30秒（RunningHub 通常快速返回 taskId）
        print(f"⏳ 开始调用 RunningHub ComfyUI 工作流 API，超时时间: 连接10秒, 读取30秒")
        try:
            response = session.post(draw_url, json=request_data, headers=headers, timeout=(10, 30))
            print(f"✅ RunningHub ComfyUI 工作流 API响应状态码: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"❌ RunningHub ComfyUI 工作流 API调用超时")
            raise
        except requests.exceptions.ConnectionError as e:
            error_msg = f"❌ RunningHub ComfyUI 工作流 API连接失败: {str(e)}"
            print(error_msg)
            raise Exception(f"无法连接到 RunningHub API 服务器，请检查网络连接。错误详情: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"❌ RunningHub ComfyUI 工作流 API请求异常: {str(e)}")
            raise
        
        # 打印响应信息
        if response.status_code != 200:
            print(f"❌ RunningHub ComfyUI 工作流 API调用失败，状态码: {response.status_code}")
            try:
                error_text = response.text
                print(f"❌ RunningHub ComfyUI 工作流 API错误响应内容: {error_text}")
                # 尝试解析错误信息
                try:
                    error_json = response.json()
                    print(f"❌ 错误详情: {json.dumps(error_json, ensure_ascii=False, indent=2)}")
                except:
                    pass
            except:
                pass
            
            # 如果是 401 错误，提供更详细的诊断信息
            if response.status_code == 401:
                print(f"⚠️ 401 未授权错误，可能的原因：")
                print(f"   1. API Key 不正确或已过期")
                print(f"   2. API Key 没有权限访问该工作流")
                print(f"   3. API Key 需要在 RunningHub 控制台中绑定到工作流")
                print(f"   4. 请求头或请求体中的 API Key 格式不正确")
                print(f"   当前使用的 API Key 长度: {len(api_config.api_key) if api_config.api_key else 0} 字符")
                print(f"   当前使用的认证方式: Authorization Bearer (请求头) + apiKey (请求体)")
        else:
            try:
                response_text = response.text
                print(f"📄 RunningHub ComfyUI 工作流 API完整响应内容: {response_text}")
            except:
                pass
        
    elif api_config.api_type == 'runninghub-rhart-edit':
        # RunningHub 全能图片PRO-图生图 API
        # 接口：/openapi/v2/rhart-image-n-pro/edit
        # 请求格式：application/json
        # 参考文档：https://www.runninghub.cn/call-api/api-detail/2004543527918551041?apiType=1
        
        host = api_config.host_domestic or api_config.host_overseas
        if not host:
            raise Exception("RunningHub API 未配置 Host")
        
        # RunningHub 的完整接口路径
        if '/openapi/v2/rhart-image-n-pro/edit' not in draw_url:
            # 如果 draw_url 不包含完整路径，自动构建
            if api_config.draw_endpoint:
                draw_url = f"{host.rstrip('/')}{api_config.draw_endpoint}"
            else:
                draw_url = f"{host.rstrip('/')}/openapi/v2/rhart-image-n-pro/edit"
        
        headers["Content-Type"] = "application/json"
        
        # 处理图片URL：RunningHub 使用 imageUrls 数组（最多10项）
        image_urls_to_process = uploaded_image_urls if uploaded_image_urls else ([uploaded_image_url] if uploaded_image_url else None)
        
        # 如果 image_urls_to_process 为空，尝试从 request_data 中读取
        if not image_urls_to_process and request_data and isinstance(request_data, dict):
            if 'urls' in request_data:
                urls_from_request = request_data.get('urls')
                if isinstance(urls_from_request, list) and len(urls_from_request) > 0:
                    image_urls_to_process = urls_from_request
                elif isinstance(urls_from_request, str) and urls_from_request.strip():
                    try:
                        parsed_urls = json.loads(urls_from_request)
                        if isinstance(parsed_urls, list) and len(parsed_urls) > 0:
                            image_urls_to_process = parsed_urls
                    except:
                        image_urls_to_process = [urls_from_request]
        
        # 限制最多10张图片
        if image_urls_to_process and len(image_urls_to_process) > 10:
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
        
        print(f"调用 RunningHub rhart-image-n-pro/edit API: {draw_url}")
        print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
        print(f"图片数量: {len(image_urls_to_process)}")
        
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
        
        # 超时设置：连接10秒，读取30秒（RunningHub 通常快速返回 taskId）
        print(f"⏳ 开始调用 RunningHub API，超时时间: 连接10秒, 读取30秒")
        try:
            response = session.post(draw_url, json=payload, headers=headers, timeout=(10, 30))
            print(f"✅ RunningHub API响应状态码: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"❌ RunningHub API调用超时")
            raise
        except requests.exceptions.ConnectionError as e:
            error_msg = f"❌ RunningHub API连接失败: {str(e)}"
            print(error_msg)
            raise Exception(f"无法连接到 RunningHub API 服务器，请检查网络连接。错误详情: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"❌ RunningHub API请求异常: {str(e)}")
            raise
        
        # 打印响应信息
        if response.status_code != 200:
            print(f"❌ RunningHub API调用失败，状态码: {response.status_code}")
            try:
                error_text = response.text
                print(f"❌ RunningHub API错误响应内容: {error_text}")
            except:
                pass
        else:
            try:
                response_text = response.text
                print(f"📄 RunningHub API完整响应内容: {response_text}")
            except:
                pass
        
    else:
        # 默认：nano-banana类型（使用JSON格式，图片通过urls字段传递云端URL）
        # 参考 bk-photo-v4 的实现逻辑
        headers["Content-Type"] = "application/json"
        
        # 获取host（用于文件上传）
        host = api_config.host_domestic or api_config.host_overseas
        
        # 处理图片：需要将本地图片上传到文件服务器，获取云端URL
        image_urls_for_request = []
        
        if uploaded_image_url or uploaded_image_urls:
            image_urls_to_process = uploaded_image_urls if uploaded_image_urls else [uploaded_image_url]
            
            for img_url in image_urls_to_process:
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
                    try:
                        # 提取本地文件路径
                        if '/uploads/' in img_url:
                            filename = img_url.split('/uploads/')[-1]
                            local_file_path = os.path.join('uploads', filename)
                        elif '/media/original/' in img_url:
                            filename = img_url.split('/media/original/')[-1]
                            local_file_path = os.path.join('uploads', filename)
                        else:
                            # 相对路径
                            local_file_path = img_url.lstrip('/')
                        
                        if os.path.exists(local_file_path):
                            # 必须上传到文件服务器（nano-banana API需要云端URL）
                            if api_config.file_upload_endpoint and host:
                                upload_url = f"{host.rstrip('/')}{api_config.file_upload_endpoint}"
                                print(f"📤 开始上传图片到文件服务器: {upload_url}")
                                try:
                                    with open(local_file_path, 'rb') as f:
                                        upload_files = {'file': (os.path.basename(local_file_path), f, 'image/jpeg')}
                                        upload_response = requests.post(
                                            upload_url,
                                            files=upload_files,
                                            headers={"Authorization": f"Bearer {api_config.api_key}"},
                                            timeout=30
                                        )
                                        print(f"📊 文件上传响应: 状态码={upload_response.status_code}")
                                        if upload_response.status_code == 200:
                                            upload_result = upload_response.json()
                                            print(f"📋 文件上传响应内容: {json.dumps(upload_result, ensure_ascii=False)[:500]}")
                                            # 从响应中提取文件URL
                                            cloud_url = upload_result.get('url') or upload_result.get('data', {}).get('url') or upload_result.get('file_url')
                                            if cloud_url:
                                                image_urls_for_request.append(cloud_url)
                                                print(f"✅ 图片已上传到服务器: {cloud_url}")
                                                continue
                                            else:
                                                print(f"⚠️ 上传响应中未找到文件URL，响应内容: {json.dumps(upload_result, ensure_ascii=False)}")
                                                raise Exception(f"文件上传成功但响应中未包含文件URL。请检查文件上传接口的响应格式。上传URL: {upload_url}")
                                        else:
                                            error_text = upload_response.text[:500] if hasattr(upload_response, 'text') else str(upload_response.content[:500])
                                            print(f"❌ 上传到文件服务器失败: HTTP {upload_response.status_code}, {error_text}")
                                            raise Exception(f"文件上传失败 (HTTP {upload_response.status_code})。请检查：\n1. 文件上传接口路径是否正确: {api_config.file_upload_endpoint}\n2. API Key是否正确\n3. 服务器是否支持文件上传\n错误详情: {error_text}")
                                except requests.exceptions.RequestException as upload_error:
                                    error_msg = str(upload_error)
                                    print(f"❌ 上传到文件服务器失败: {error_msg}")
                                    raise Exception(f"文件上传请求失败。请检查：\n1. 网络连接是否正常\n2. 文件上传接口URL是否正确: {upload_url}\n3. 服务器是否可访问\n错误详情: {error_msg}")
                                except Exception as upload_error:
                                    error_msg = str(upload_error)
                                    print(f"❌ 上传到文件服务器失败: {error_msg}")
                                    raise Exception(f"文件上传失败: {error_msg}")
                            else:
                                missing_config = []
                                if not api_config.file_upload_endpoint:
                                    missing_config.append("file_upload_endpoint（文件上传接口）")
                                if not host:
                                    missing_config.append("host（服务器地址）")
                                raise Exception(f"本地图片必须上传到文件服务器，但未配置: {', '.join(missing_config)}。请在API服务商配置中设置这些参数。")
                        else:
                            raise Exception(f"本地文件不存在: {local_file_path}")
                    except Exception as e:
                        print(f"❌ 处理本地图片失败: {str(e)}")
                        raise
                else:
                    # 已经是云端URL，直接使用
                    image_urls_for_request.append(img_url)
                    print(f"✅ 使用云端URL: {img_url}")
        
        # 将图片URL添加到请求数据中（nano-banana API使用urls字段，参考bk-photo-v4）
        # 注意：nano-banana API应该使用urls数组，而不是单个url字段
        if image_urls_for_request:
            # 始终使用urls数组格式（即使只有一张图片）
            request_data['urls'] = image_urls_for_request
            print(f"📸 最终使用的图片URL: {image_urls_for_request}")
            print(f"📸 请求数据中的urls字段: {request_data.get('urls')}")
        else:
            print(f"⚠️ 警告: 没有图片URL，API调用可能失败")
        
        # 使用JSON格式发送请求（参考 bk-photo-v4）
        print(f"调用 nano-banana API: {draw_url}")
        print(f"请求参数: {json.dumps(request_data, ensure_ascii=False)}")
        
        try:
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
            
            # 代理设置：根据不同的服务商决定是否使用代理
            proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
            proxy_info = []
            for var in proxy_env_vars:
                if os.environ.get(var):
                    proxy_info.append(f"{var}={os.environ.get(var)}")
            
            print(f"📤 API调用URL: {draw_url}")
            if proxy_info:
                print(f"📤 检测到代理环境变量: {', '.join(proxy_info)}")
            else:
                print(f"📤 未检测到代理环境变量")
            
            # 判断是否需要代理
            proxies = None
            is_grsai_domain = any(domain in draw_url.lower() for domain in [
                'grsai.dakka.com.cn', 'grsai-file.dakka.com.cn'
            ])
            is_t8star_domain = any(domain in draw_url.lower() for domain in [
                't8star.cn', 'ai.t8star.cn'
            ])
            is_laozhang_domain = 'api.laozhang.ai' in draw_url.lower()
            
            if is_grsai_domain:
                # GRSAI服务商：禁用代理（保持现有逻辑）
                print(f"📤 代理设置: 已强制禁用（GRSAI是国内服务器，直连速度更快）")
                proxies = {'http': None, 'https': None}
            elif is_t8star_domain:
                # T8star服务商：启用代理（同步API，gemini-native格式，需要代理才能快速请求和回传）
                if has_proxy:
                    print(f"📤 代理设置: 使用系统代理（T8star需要代理以提升请求和回传速度）")
                    proxies = None  # None表示使用系统环境变量中的代理设置
                else:
                    print(f"⚠️ 代理设置: T8star建议使用代理，但未检测到代理环境变量")
                    proxies = None
            elif is_laozhang_domain:
                # api.laozhang.ai：启用代理
                if has_proxy:
                    print(f"📤 代理设置: 使用系统代理（api.laozhang.ai需要代理）")
                    proxies = None  # None表示使用系统环境变量中的代理设置
                else:
                    print(f"⚠️ 代理设置: api.laozhang.ai建议使用代理，但未检测到代理环境变量")
                    proxies = None
            elif has_proxy:
                # 其他服务器，使用系统代理设置
                print(f"📤 代理设置: 使用系统代理（检测到代理环境变量）")
                proxies = None  # None表示使用系统环境变量中的代理设置
            else:
                print(f"📤 代理设置: 未使用代理（未检测到代理环境变量）")
                proxies = None
            
            # 增加超时时间
            connect_timeout = 60 if 'api.laozhang.ai' in draw_url else 10
            read_timeout = 600 if 'api.laozhang.ai' in draw_url else 120
            
            # 使用JSON格式发送请求
            print(f"📤 发送请求到: {draw_url}")
            print(f"📤 代理设置: {proxies}")
            print(f"📤 超时设置: connect={connect_timeout}s, read={read_timeout}s")
            response = session.post(
                draw_url, 
                json=request_data, 
                headers=headers, 
                timeout=(connect_timeout, read_timeout),
                proxies=proxies
            )
            
            print(f"✅ nano-banana API响应状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ nano-banana API错误响应: {response.text[:1000] if hasattr(response, 'text') else '无法读取响应'}")
        except requests.exceptions.Timeout as e:
            error_msg = f"❌ nano-banana API调用超时: {str(e)}"
            print(error_msg)
            raise Exception(f"API调用超时，请检查网络连接或稍后重试。错误详情: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            error_msg = f"❌ nano-banana API连接失败: {str(e)}"
            print(error_msg)
            if 'Max retries exceeded' in str(e) or 'HTTPSConnectionPool' in str(e):
                raise Exception(f"无法连接到API服务器，请检查网络连接。错误详情: {str(e)}")
            raise Exception(f"API连接失败: {str(e)}")
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ nano-banana API请求异常: {str(e)}"
            print(error_msg)
            raise Exception(f"API请求失败: {str(e)}")
    
    return response


def get_next_retry_api_config(current_api_config_id, retried_ids, db=None, APIProviderConfig=None):
    """
    获取下一个可用于重试的API配置
    
    Args:
        current_api_config_id: 当前使用的API配置ID
        retried_ids: 已尝试的API配置ID列表
        db: 数据库实例
        APIProviderConfig: APIProviderConfig模型类
    
    Returns:
        APIProviderConfig对象，如果没有可用的返回None
    """
    if not all([db, APIProviderConfig]):
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'APIProviderConfig'):
                APIProviderConfig = test_server_module.APIProviderConfig
    
    if not all([db, APIProviderConfig]):
        return None
    
    # 解析已尝试的ID列表
    if isinstance(retried_ids, str):
        try:
            retried_ids = json.loads(retried_ids) if retried_ids else []
        except:
            retried_ids = []
    elif retried_ids is None:
        retried_ids = []
    
    # 添加当前配置ID到已尝试列表
    if current_api_config_id and current_api_config_id not in retried_ids:
        retried_ids.append(current_api_config_id)
    
    # 查询所有启用的、支持重试的配置，按优先级排序
    # 关键修复：禁止SSL和UNIR级别的重试
    query = APIProviderConfig.query.filter_by(
        is_active=True,
        enable_retry=True
    ).filter(
        ~APIProviderConfig.id.in_(retried_ids)
    )
    
    # 过滤掉SSL和UNIR级别的配置（通过名称判断）
    all_configs = query.all()
    filtered_configs = []
    for config in all_configs:
        config_name_upper = config.name.upper() if config.name else ''
        # 禁止SSL和UNIR级别的重试
        if 'SSL' in config_name_upper or 'UNIR' in config_name_upper:
            print(f"⚠️ [重试] 跳过SSL/UNIR级别配置: {config.name} (ID: {config.id})")
            continue
        filtered_configs.append(config)
    
    # 按优先级排序
    filtered_configs.sort(key=lambda x: (
        x.priority if x.priority else 0,
        x.is_default if x.is_default else False,
        x.id
    ), reverse=True)
    
    next_config = filtered_configs[0] if filtered_configs else None
    return next_config


def create_api_task(style_image_id, prompt, image_size='1K', aspect_ratio='auto', uploaded_images=None,
                    upload_config=None, api_config_id=None, db=None, AITask=None, APITemplate=None, APIProviderConfig=None,
                    StyleImage=None, StyleCategory=None):
    """
    创建API调用任务
    
    Args:
        style_image_id: 风格图片ID
        prompt: 提示词
        image_size: 图片尺寸
        aspect_ratio: 图片比例
        uploaded_images: 上传的图片URL列表
        api_config_id: API配置ID（可选，如果不提供则从模板配置获取）
        db: 数据库实例
        AITask: AITask模型类
        APITemplate: APITemplate模型类
        APIProviderConfig: APIProviderConfig模型类
        StyleImage: StyleImage模型类
        StyleCategory: StyleCategory模型类
    
    Returns:
        tuple: (success: bool, task: AITask, error_message: str)
    """
    try:
        # 获取数据库模型
        if not all([db, AITask, APITemplate, APIProviderConfig, StyleImage]):
            import sys
            if 'test_server' in sys.modules:
                test_server_module = sys.modules['test_server']
                db = test_server_module.db
                AITask = test_server_module.AITask
                APITemplate = test_server_module.APITemplate
                APIProviderConfig = test_server_module.APIProviderConfig
                StyleImage = test_server_module.StyleImage
                StyleCategory = test_server_module.StyleCategory
        
        if not all([db, AITask, APITemplate, APIProviderConfig, StyleImage]):
            return False, None, "数据库模型未初始化"
        
        # 获取风格图片
        style_image = StyleImage.query.get(style_image_id)
        if not style_image:
            return False, None, "风格图片不存在"
        
        # 防重复提交检查（如果有关联订单，检查是否已有任务）
        # 注意：API任务可能没有order_id，这里主要检查相同参数的重复提交
        # 可以根据业务需求调整检查逻辑
        
        # 获取API模板配置（图片级别 > 分类级别）
        api_template = APITemplate.query.filter_by(style_image_id=style_image_id, is_active=True).first()
        if not api_template:
            # 尝试从分类级别获取
            api_template = APITemplate.query.filter_by(
                style_category_id=style_image.category_id,
                style_image_id=None,
                is_active=True
            ).first()
        
        if not api_template:
            return False, None, "未配置API调用模板"
        
        # 获取API配置
        if api_config_id:
            api_config = APIProviderConfig.query.filter_by(id=api_config_id, is_active=True).first()
        else:
            # 从模板配置获取
            if api_template.api_config_id:
                api_config = APIProviderConfig.query.filter_by(
                    id=api_template.api_config_id,
                    is_active=True
                ).first()
            else:
                # 使用默认配置
                api_config = APIProviderConfig.query.filter_by(
                    is_active=True,
                    is_default=True
                ).first()
                if not api_config:
                    api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config:
            return False, None, "未配置API服务商"
        
        # 检查是否有批量提示词配置（优先级最高）
        prompts_list = None
        if api_template.prompts_json:
            try:
                # json 已在文件顶部导入，无需重复导入
                prompts_list = json.loads(api_template.prompts_json) if isinstance(api_template.prompts_json, str) else api_template.prompts_json
                if prompts_list and isinstance(prompts_list, list) and len(prompts_list) > 0:
                    # 过滤掉空字符串和None值
                    prompts_list = [p.strip() if isinstance(p, str) else str(p) if p else '' for p in prompts_list]
                    prompts_list = [p for p in prompts_list if p and p.strip()]  # 移除空字符串
                    
                    if len(prompts_list) > 0:
                        print(f"📝 检测到批量提示词配置，共 {len(prompts_list)} 个有效提示词")
                        # 如果用户提供了prompt，将其作为第一个提示词（如果用户有输入）
                        if prompt and prompt.strip():
                            prompts_list[0] = prompt.strip()
                            print(f"📝 使用用户输入的提示词替换第一个: {prompt[:50]}...")
                    else:
                        print(f"⚠️ 批量提示词配置中所有提示词都为空，忽略批量配置")
                        prompts_list = None
            except Exception as e:
                print(f"⚠️ 解析批量提示词失败: {str(e)}")
                prompts_list = None
        
        # 如果没有批量提示词，且用户也没有提供提示词，尝试使用默认提示词（向后兼容）
        if not prompts_list and (not prompt or not prompt.strip()):
            if api_template and api_template.default_prompt:
                prompt = api_template.default_prompt.strip()
                print(f"📝 使用默认提示词: {prompt[:50]}...")
        
        # 如果配置了批量提示词，使用批量创建函数
        if prompts_list and len(prompts_list) > 0:
            print(f"🔄 使用批量提示词创建任务，共 {len(prompts_list)} 个提示词")
            # 获取order_id和order_number（如果设置了）
            order_id = getattr(create_api_task, '_test_order_id', None)
            order_number = getattr(create_api_task, '_test_order_number', None)
            
            # 先确定最终的size和aspect_ratio（用于批量创建）
            if api_config.api_type == 'runninghub-comfyui-workflow':
                final_size = None
                final_aspect_ratio = None
            else:
                final_size = image_size or api_template.default_size or '1K'
                final_aspect_ratio = aspect_ratio or api_template.default_aspect_ratio or 'auto'
            
            # 调用批量创建函数（需要在文件末尾定义）
            # 注意：这里需要先定义函数，或者使用延迟导入
            # 为了简化，我们在这里直接实现批量创建逻辑
            created_tasks = []
            errors = []
            
            for idx, batch_prompt in enumerate(prompts_list):
                # 验证提示词不为空
                if not batch_prompt or not batch_prompt.strip():
                    error_msg = f"提示词 {idx + 1} 为空，跳过"
                    errors.append(error_msg)
                    print(f"⚠️ {error_msg}")
                    continue
                
                try:
                    # 为每个提示词创建任务
                    # 临时设置order_id和order_number
                    original_order_id = getattr(create_api_task, '_test_order_id', None)
                    original_order_number = getattr(create_api_task, '_test_order_number', None)
                    
                    if order_id:
                        create_api_task._test_order_id = order_id
                        if order_number:
                            create_api_task._test_order_number = order_number
                    
                    # 递归调用create_api_task（但跳过批量提示词检查，避免无限循环）
                    # 临时清空prompts_json，避免递归
                    original_prompts_json = api_template.prompts_json
                    api_template.prompts_json = None
                    
                    try:
                        success, task, error_message = create_api_task(
                            style_image_id=style_image_id,
                            prompt=batch_prompt.strip(),  # 确保去除首尾空格
                            image_size=final_size if final_size else image_size,
                            aspect_ratio=final_aspect_ratio if final_aspect_ratio else aspect_ratio,
                            uploaded_images=uploaded_images,
                            upload_config=upload_config,
                            api_config_id=api_config_id or api_config.id,
                            db=db,
                            AITask=AITask,
                            APITemplate=APITemplate,
                            APIProviderConfig=APIProviderConfig,
                            StyleImage=StyleImage,
                            StyleCategory=StyleCategory
                        )
                        
                        if success and task:
                            created_tasks.append(task)
                            print(f"✅ 批量任务 {idx + 1}/{len(prompts_list)} 创建成功: task_id={task.id}, prompt={batch_prompt[:50]}...")
                        else:
                            errors.append(f"提示词 {idx + 1} ({batch_prompt[:50]}...): {error_message}")
                            print(f"❌ 批量任务 {idx + 1}/{len(prompts_list)} 创建失败: {error_message}")
                    finally:
                        # 恢复prompts_json
                        api_template.prompts_json = original_prompts_json
                        # 恢复order_id和order_number
                        create_api_task._test_order_id = original_order_id
                        create_api_task._test_order_number = original_order_number
                        
                except Exception as e:
                    error_msg = f"提示词 {idx + 1} ({batch_prompt[:50]}...): {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ 批量任务 {idx + 1}/{len(prompts_list)} 创建异常: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 如果至少有一个任务创建成功，返回成功
            if len(created_tasks) > 0:
                error_message = f"成功创建 {len(created_tasks)}/{len(prompts_list)} 个任务" + (f"，失败: {', '.join(errors)}" if errors else "")
                # 返回第一个任务（保持向后兼容）
                return True, created_tasks[0], error_message if errors else None
            else:
                return False, None, f"所有任务创建失败: {', '.join(errors)}"
        
        # 验证提示词不为空（在非批量提示词的情况下）
        # 注意：如果配置了批量提示词，这里不会执行（因为已经在上面处理了）
        if not prompts_list and (not prompt or not prompt.strip()):
            return False, None, "提示词不能为空，请配置批量提示词或提供提示词"
        
        # RunningHub ComfyUI 工作流：使用 request_body_template 构建请求体（不需要 model_name）
        if api_config.api_type == 'runninghub-comfyui-workflow':
            # RunningHub ComfyUI 工作流不需要 model_name，跳过标准参数构建
            model_name = None  # RunningHub ComfyUI 工作流不使用 model_name
            final_prompt = prompt.strip() if prompt else ""
            final_size = None  # RunningHub ComfyUI 工作流不使用 size
            final_aspect_ratio = None  # RunningHub ComfyUI 工作流不使用 aspect_ratio
        else:
            # 标准API：构建标准请求参数（参考bk-photo-v4：优先使用api_config.model_name）
            # 注意：如果api_template.model_name为空，应该使用api_config.model_name
            model_name = api_config.model_name or api_template.model_name or 'nano-banana-pro'
            print(f"📝 模型名称: api_config.model_name={api_config.model_name}, api_template.model_name={api_template.model_name}, 最终使用={model_name}")
            final_prompt = prompt or api_template.default_prompt or ""
            final_size = image_size or api_template.default_size or '1K'
            final_aspect_ratio = aspect_ratio or api_template.default_aspect_ratio or 'auto'
        
        # RunningHub ComfyUI 工作流：使用 request_body_template 构建请求体
        if api_config.api_type == 'runninghub-comfyui-workflow':
            # 从 request_body_template 中获取工作流配置
            request_body_template = None
            if api_template.request_body_template:
                try:
                    request_body_template = json.loads(api_template.request_body_template) if isinstance(api_template.request_body_template, str) else api_template.request_body_template
                except:
                    print(f"⚠️ 解析 request_body_template 失败: {api_template.request_body_template}")
            
            if not request_body_template or not request_body_template.get('workflow_id'):
                return False, None, "RunningHub ComfyUI 工作流未配置 workflow_id"
            
            workflow_id = request_body_template.get('workflow_id')
            node_info_list_raw = request_body_template.get('nodeInfoList', [])
            
            # 处理图片和提示词：将实际值替换占位符
            image_urls_to_process = uploaded_images if uploaded_images else []
            final_prompt = prompt or api_template.default_prompt or ""
            
            print(f"📸 RunningHub ComfyUI 工作流：准备转换 nodeInfoList 格式")
            print(f"   - 工作流ID: {workflow_id}")
            print(f"   - 图片URL数量: {len(image_urls_to_process)}")
            print(f"   - 图片URL列表: {image_urls_to_process}")
            print(f"   - 提示词: {final_prompt}")
            print(f"   - nodeInfoList 原始数据: {json.dumps(node_info_list_raw, ensure_ascii=False)}")
            
            # 根据 RunningHub API 文档，nodeInfoList 格式应该是：
            # [{"nodeId": "x", "fieldName": "y", "fieldValue": "z"}]
            # 而不是 {"nodeId": "x", "inputs": {"y": "z"}}
            node_info_list = []
            image_index = 0
            
            for node_info in node_info_list_raw:
                node_id = node_info.get('nodeId')
                if not node_id:
                    continue
                
                # 如果已经是正确的格式（fieldName/fieldValue），直接使用
                if 'fieldName' in node_info and 'fieldValue' in node_info:
                    field_name = node_info['fieldName']
                    field_value = node_info['fieldValue']
                    
                    # 替换占位符
                    if field_name in ['image', 'imageUrls']:
                        if (field_value == '{{image_url}}' or field_value == '' or field_value == '{{ref_image_url}}') and image_index < len(image_urls_to_process):
                            field_value = image_urls_to_process[image_index]
                            print(f"   ✅ 替换节点 {node_id} 的 {field_name}: {field_value}")
                            image_index += 1
                    elif field_name == 'text':
                        if field_value == '{{prompt}}' and final_prompt:
                            field_value = final_prompt
                            print(f"   ✅ 替换节点 {node_id} 的 {field_name}: {field_value}")
                    
                    node_info_list.append({
                        "nodeId": str(node_id),
                        "fieldName": field_name,
                        "fieldValue": str(field_value) if field_value is not None else ""
                    })
                # 如果是旧格式（inputs 对象），转换为新格式
                elif 'inputs' in node_info:
                    inputs = node_info['inputs']
                    for field_name, field_value in inputs.items():
                        # 替换占位符
                        if field_name in ['image', 'imageUrls']:
                            if (field_value == '{{image_url}}' or field_value == '' or field_value == '{{ref_image_url}}') and image_index < len(image_urls_to_process):
                                field_value = image_urls_to_process[image_index]
                                print(f"   ✅ 替换节点 {node_id} 的 {field_name}: {field_value}")
                                image_index += 1
                        elif field_name == 'text':
                            if field_value == '{{prompt}}' and final_prompt:
                                field_value = final_prompt
                                print(f"   ✅ 替换节点 {node_id} 的 {field_name}: {field_value}")
                        
                        # 如果 field_value 是列表或字典，转换为 JSON 字符串
                        if isinstance(field_value, (list, dict)):
                            field_value = json.dumps(field_value, ensure_ascii=False)
                        else:
                            field_value = str(field_value) if field_value is not None else ""
                        
                        node_info_list.append({
                            "nodeId": str(node_id),
                            "fieldName": field_name,
                            "fieldValue": field_value
                        })
            
            # 构建 RunningHub ComfyUI 工作流请求体
            # 根据 RunningHub API 文档：https://www.runninghub.cn/runninghub-api-doc-cn/doc-7534195
            # 使用 /task/openapi/create 端点，请求体包含 apiKey, workflowId, nodeInfoList
            request_data = {
                "apiKey": api_config.api_key,  # API Key 必须在请求体中
                "workflowId": workflow_id,  # workflowId 在请求体中，不在 URL 路径中
                "nodeInfoList": node_info_list
            }
            
            # 可选参数：如果配置中有，使用配置的值；否则使用默认值
            if 'addMetadata' in request_body_template:
                request_data['addMetadata'] = request_body_template.get('addMetadata', False)
            else:
                request_data['addMetadata'] = False  # 默认值
            
            if 'instanceType' in request_body_template:
                request_data['instanceType'] = request_body_template.get('instanceType', 'default')
            else:
                request_data['instanceType'] = 'default'  # 默认值：24G显存
            
            if 'usePersonalQueue' in request_body_template:
                request_data['usePersonalQueue'] = request_body_template.get('usePersonalQueue', False)
            else:
                request_data['usePersonalQueue'] = False  # 默认值
            
            print(f"📸 RunningHub ComfyUI 工作流：格式转换完成")
            print(f"   - nodeInfoList 转换后数据: {json.dumps(node_info_list, ensure_ascii=False, indent=2)}")
            print(f"📋 RunningHub ComfyUI 工作流请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        elif api_config.api_type == 'runninghub-rhart-edit':
            # RunningHub 全能图片PRO-图生图 API：构建请求数据
            # 注意：imageUrls 会在 call_api_with_config 中从 uploaded_images 参数添加
            request_data = {
                "model": model_name,
                "prompt": final_prompt,
                "aspectRatio": final_aspect_ratio,
                "imageSize": final_size,
                "webHook": "-1",  # 立即返回id，然后轮询获取结果
                "shutProgress": False
            }
            # 关键修复：在 request_data 中添加 imageUrls，用于任务详情显示
            if uploaded_images:
                request_data["imageUrls"] = uploaded_images
                print(f"📸 [RunningHub] 在 request_data 中添加 imageUrls: {uploaded_images}")
        else:
            # 标准API：构建标准请求数据
            request_data = {
                "model": model_name,
                "prompt": final_prompt,
                "aspectRatio": final_aspect_ratio,
                "imageSize": final_size,
                "webHook": "-1",  # 立即返回id，然后轮询获取结果
                "shutProgress": False
            }
        
        # 构建API URL
        host = api_config.host_domestic or api_config.host_overseas
        if not host:
            return False, None, "API服务商未配置Host"
        
        # 对于T8Star的gemini-native类型（同步API），需要根据模型名称动态构建endpoint
        if api_config.api_type == 'gemini-native':
            is_t8star = host and 't8star.cn' in host.lower()
            if is_t8star:
                # T8Star的gemini-native应该使用 /v1/models/{model}:generateContent 格式
                # 如果endpoint是 /v1/draw/nano-banana 或其他错误格式，需要修正
                if api_config.draw_endpoint and ('/v1/draw/' in api_config.draw_endpoint or '/v1/images/' in api_config.draw_endpoint):
                    # 错误的endpoint，需要根据model_name构建正确的endpoint
                    model_endpoint = model_name.replace('_', '-') if model_name else 'gemini-3-pro-image-preview'
                    correct_endpoint = f"/v1/models/{model_endpoint}:generateContent"
                    print(f"⚠️ 检测到T8Star服务商的gemini-native API（同步API），但endpoint不正确，自动修正")
                    print(f"   原endpoint: {api_config.draw_endpoint}")
                    print(f"   修正后endpoint: {correct_endpoint}")
                    draw_url = host.rstrip('/') + correct_endpoint
                elif api_config.draw_endpoint and ':generateContent' in api_config.draw_endpoint:
                    # endpoint已经正确，直接使用
                    draw_url = api_config.draw_endpoint if api_config.draw_endpoint.startswith('http') else host.rstrip('/') + api_config.draw_endpoint
                else:
                    # endpoint不完整，需要根据model_name构建
                    model_endpoint = model_name.replace('_', '-') if model_name else 'gemini-3-pro-image-preview'
                    correct_endpoint = f"/v1/models/{model_endpoint}:generateContent"
                    print(f"⚠️ T8Star gemini-native API endpoint不完整（同步API），自动构建: {correct_endpoint}")
                    draw_url = host.rstrip('/') + correct_endpoint
            else:
                # 非T8Star服务商，使用原有逻辑
                draw_url = api_config.draw_endpoint if api_config.draw_endpoint.startswith('http') else host.rstrip('/') + api_config.draw_endpoint
        elif api_config.api_type == 'nano-banana-edits':
            # nano-banana-edits类型，使用/v1/images/edits端点
            is_t8star = host and 't8star.cn' in host.lower()
            if is_t8star:
                # T8Star必须使用/v1/images/edits端点
                correct_endpoint = '/v1/images/edits'
                if api_config.draw_endpoint != correct_endpoint:
                    print(f"⚠️ T8Star nano-banana-edits API endpoint不正确，自动修正为: {correct_endpoint}")
                draw_url = host.rstrip('/') + correct_endpoint
            else:
                # 其他服务商，使用配置的endpoint
                draw_url = f"{host.rstrip('/')}{api_config.draw_endpoint}"
        elif api_config.api_type == 'runninghub-comfyui-workflow':
            # RunningHub ComfyUI 工作流 API
            # 根据文档：https://www.runninghub.cn/runninghub-api-doc-cn/doc-7534195
            # 使用 /task/openapi/create 端点，workflowId 在请求体中，不在 URL 路径中
            draw_url = f"{host.rstrip('/')}/task/openapi/create"
        else:
            # 其他API类型，直接使用配置的endpoint
            draw_url = f"{host.rstrip('/')}{api_config.draw_endpoint}"
        
        # 输出详细的API配置信息（用于调试）
        print(f"📋 API配置信息:")
        print(f"   - 服务商: {api_config.name}")
        print(f"   - API类型: {api_config.api_type}")
        print(f"   - Host: {host}")
        print(f"   - Draw Endpoint: {api_config.draw_endpoint}")
        print(f"   - 模型名称: {model_name}")
        print(f"   - 完整URL: {draw_url}")
        
        # 关键修复：先创建任务记录，即使API调用失败也要创建（这样用户才能在任务管理页面看到）
        import uuid
        task_id = str(uuid.uuid4())
        
        # 对于测试任务，order_id 和 order_number 可以为测试值
        # 检查是否有传入的 order_id（用于实际订单）或使用测试值
        order_id = getattr(create_api_task, '_test_order_id', 0)  # 默认测试订单ID为0
        order_number = getattr(create_api_task, '_test_order_number', f"TEST_{task_id[:8]}")
        
        # 调用API（使用信号量限制并发数）
        response = None
        api_call_error = None
        connection_closed_but_request_sent = False  # 标记连接断开但请求可能已发送
        try:
            semaphore = _get_api_semaphore()
            semaphore.acquire()
            try:
                # 关键修复：RunningHub ComfyUI 工作流需要传递 request_body_template
                if api_config.api_type == 'runninghub-comfyui-workflow' and api_template and api_template.request_body_template:
                    # 将 request_body_template 添加到 request_data 中，供模块化实现使用
                    try:
                        request_body_template = json.loads(api_template.request_body_template) if isinstance(api_template.request_body_template, str) else api_template.request_body_template
                        request_data['request_body_template'] = request_body_template
                    except Exception as e:
                        print(f"⚠️ 解析 request_body_template 失败: {str(e)}")
                
                response = call_api_with_config(
                    api_config=api_config,
                    draw_url=draw_url,
                    request_data=request_data,
                    uploaded_image_urls=uploaded_images,
                    upload_config=upload_config,  # 传递upload_config
                    model_name=model_name,
                    prompt=final_prompt,
                    aspect_ratio=final_aspect_ratio,
                    image_size=final_size,
                    enhance_prompt=api_template.enhance_prompt if api_template else False
                )
            finally:
                semaphore.release()
        except Exception as e:
            error_str = str(e)
            # 检查是否是"连接断开但请求可能已发送"的特殊异常
            if 'ConnectionClosedButRequestSent' in str(type(e)) or '连接被远程关闭，但请求可能已发送' in error_str:
                connection_closed_but_request_sent = True
                print(f"⚠️ 连接断开但请求可能已发送，任务将保持'处理中'状态，等待结果")
            else:
                # 其他API调用失败，但也要创建任务记录（标记为失败状态）
                api_call_error = error_str
                print(f"❌ API调用失败，但会创建失败状态的任务记录: {api_call_error}")
        
        # 关键修复：对于gemini-native类型，request_data可能不包含图片信息（因为图片在payload中）
        # 需要从response对象中获取包含图片信息的request_data_for_log
        request_params_for_log = request_data.copy() if isinstance(request_data, dict) else request_data
        
        # 确保 request_params_for_log 包含所有图片URL（用于前端显示）
        # 对于 nano-banana 类型，urls 字段在 call_api_with_config 中已添加到 request_data
        # 但为了确保完整性，我们再次检查并添加
        if api_config.api_type in ['nano-banana', 'nano-banana-edits'] and uploaded_images:
            if isinstance(request_params_for_log, dict):
                # 确保 urls 字段存在且包含所有图片
                if 'urls' not in request_params_for_log or not request_params_for_log.get('urls'):
                    request_params_for_log['urls'] = uploaded_images
                else:
                    # 如果已有 urls，确保包含所有图片（合并去重）
                    existing_urls = request_params_for_log.get('urls', [])
                    if not isinstance(existing_urls, list):
                        existing_urls = [existing_urls] if existing_urls else []
                    all_urls = list(dict.fromkeys(existing_urls + uploaded_images))  # 保持顺序并去重
                    request_params_for_log['urls'] = all_urls
                print(f"✅ [nano-banana] 确保 request_params 包含所有图片URL: {len(request_params_for_log.get('urls', []))} 张")
        
        if response and hasattr(response, 'request_data_for_log'):
            request_params_for_log = response.request_data_for_log
            print(f"✅ [gemini-native] 使用包含图片信息的request_params（从response获取）")
        elif api_config.api_type == 'gemini-native' and uploaded_images:
            # 如果response没有request_data_for_log，手动创建一个包含图片信息的request_data
            request_params_for_log = {
                "model": model_name,
                "prompt": final_prompt,
                "aspectRatio": final_aspect_ratio,
                "imageSize": final_size,
                "shutProgress": False,
                "webHook": "-1",
                "image_urls": uploaded_images,
                "image_count": len(uploaded_images),
                "image_format": "base64_encoded_in_payload"
            }
            print(f"✅ [gemini-native] 手动创建包含图片信息的request_params")
        
        # 将API相关信息存储在 processing_log 中（JSON格式）
        api_info = {
            'task_id': task_id,
            'api_config_id': api_config.id,
            'api_config_name': api_config.name,
            'model_name': model_name,
            'prompt': final_prompt,
            'image_size': final_size,
            'aspect_ratio': final_aspect_ratio,
            'uploaded_images': uploaded_images,
            'points_cost': api_template.points_cost or 0,
            'request_params': request_params_for_log,  # 使用包含图片信息的request_params
        }
        
        # 如果有响应，保存响应数据
        if response:
            api_info['response_data'] = response.text[:5000] if response.text else None
            api_info['response_status'] = response.status_code
            # 关键修复：对于同步API，保存完整的JSON响应（用于后续解析base64图片）
            if response.status_code == 200 and response.text:
                try:
                    api_info['original_response'] = response.json()
                except:
                    pass
        elif api_call_error:
            # API调用失败，保存错误信息
            api_info['api_call_error'] = api_call_error
            api_info['response_status'] = None
        
        # 关键修复：同步API任务应该在创建时就确定状态，不应该使用pending状态
        # 先判断是否为同步API，如果是同步API，初始状态应该是processing（等待响应），而不是pending
        is_sync_api = api_config.is_sync_api if hasattr(api_config, 'is_sync_api') else False
        
        # 如果连接断开但请求可能已发送，保持处理中状态，不标记为失败
        # 关键修复：对于同步API，如果连接断开，请求可能已发送，不应该重试（避免重复请求）
        if connection_closed_but_request_sent:
            initial_status = 'processing'  # 保持处理中状态，等待结果
            api_info['connection_closed_but_request_sent'] = True
            api_info['should_not_retry'] = True  # 标记为不应重试（避免重复请求）
            api_info['connection_error'] = '连接被远程关闭，但请求可能已发送到后端，后端可能正在处理或已完成'
            print(f"⚠️ 任务 {task_id} 连接断开但请求可能已发送，保持'处理中'状态，标记为不应重试")
        elif api_call_error:
            initial_status = 'failed'  # API调用失败，标记为失败状态
        else:
            initial_status = 'processing' if is_sync_api else 'pending'
        
        task = AITask(
            order_id=order_id,  # 测试任务使用0
            order_number=order_number,  # 测试任务使用TEST_前缀
            style_image_id=style_image_id,
            comfyui_prompt_id=task_id,  # 使用comfyui_prompt_id存储task_id（用于查询）
            status=initial_status,  # 同步API使用processing，异步API使用pending，失败时使用failed
            processing_log=json.dumps(api_info, ensure_ascii=False),  # 存储API信息
            error_message=api_call_error if api_call_error else None  # 保存错误信息（连接断开的情况不保存错误信息，保持处理中状态）
        )
        
        db.session.add(task)
        db.session.flush()  # 确保task.id已生成
        
        # 更新订单状态为"AI任务处理中"（如果order_id > 0，说明是真实订单）
        if order_id and order_id > 0:
            try:
                import sys
                if 'test_server' in sys.modules:
                    test_server_module = sys.modules['test_server']
                    Order = getattr(test_server_module, 'Order', None)
                    AITask = getattr(test_server_module, 'AITask', None)
                    if Order and AITask:
                        order = Order.query.get(order_id)
                        if order:
                            # 如果订单状态是处理中或其他前置状态，更新为ai_processing
                            if order.status in ['retouching', 'shooting', 'paid', 'processing', 'ai_processing']:
                                if order.status != 'ai_processing':
                                    order.status = 'ai_processing'  # AI任务处理中
                                    print(f"✅ 订单 {order.order_number} 状态已更新为: ai_processing (从 {order.status} 更新)")
                                else:
                                    print(f"ℹ️ 订单 {order.order_number} 状态已经是: ai_processing")
            except Exception as e:
                print(f"⚠️ 更新订单状态失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 如果API调用失败（非连接断开），直接返回失败的任务
        if api_call_error and not connection_closed_but_request_sent:
            db.session.commit()  # 提交时包含订单状态更新
            return True, task, None  # 返回True表示任务已创建（虽然是失败状态）
        
        # 如果连接断开但请求可能已发送，也返回任务（保持处理中状态）
        if connection_closed_but_request_sent:
            db.session.commit()  # 提交时包含订单状态更新
            return True, task, None  # 返回True表示任务已创建（保持处理中状态，等待结果）
        
        # 处理响应
        if response.status_code == 200:
            result = response.json()
            
            # 对于 RunningHub ComfyUI 工作流，打印完整响应以便调试
            if api_config.api_type == 'runninghub-comfyui-workflow':
                print(f"🔍 [RunningHub ComfyUI] 完整响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                print(f"🔍 [RunningHub ComfyUI] 响应字段: {list(result.keys())}")
                # 检查所有可能包含 taskId 的字段
                for key in result.keys():
                    value = result.get(key)
                    if isinstance(value, str) and value.strip().isdigit() and len(value) > 10:
                        print(f"🔍 [RunningHub ComfyUI] 发现可能的 taskId 在字段 '{key}': {value}")
                    elif isinstance(value, dict) and ('taskId' in value or 'task_id' in value or 'id' in value):
                        print(f"🔍 [RunningHub ComfyUI] 发现可能的 taskId 在字段 '{key}' 中: {value.get('taskId') or value.get('task_id') or value.get('id')}")
            
            # 根据is_sync_api字段决定处理方式（is_sync_api已在上面定义）
            if is_sync_api:
                # 同步API：直接返回结果，不需要轮询
                result_image_url = None
                image_data_base64 = None
                mime_type = 'image/png'
                
                # 根据不同的API类型解析响应
                if api_config.api_type == 'gemini-native':
                    # Gemini API响应格式（参考bk-photo-v4的实现）
                    print(f"📦 [同步API] 解析Gemini响应数据...")
                    print(f"📦 [同步API] 响应数据结构: {json.dumps(result, ensure_ascii=False)[:500]}...")
                    
                    # 关键修复：T8Star的响应格式可能是直接的parts数组，而不是candidates结构
                    parts_to_check = None
                    
                    # 方式1：标准Gemini格式（candidates -> content -> parts）
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        
                        # 检查 finishReason
                        finish_reason = candidate.get('finishReason', '')
                        print(f"🔍 [同步API] Gemini finishReason: {finish_reason}")
                        
                        if 'content' in candidate and 'parts' in candidate['content']:
                            parts_to_check = candidate['content']['parts']
                    
                    # 方式2：T8Star可能直接返回parts数组（根据用户提供的响应格式）
                    elif isinstance(result, list):
                        # 如果响应本身就是parts数组
                        parts_to_check = result
                        print(f"🔍 [同步API] 检测到响应为parts数组格式（T8Star格式）")
                    elif 'parts' in result:
                        # 如果响应有parts字段
                        parts_to_check = result['parts']
                        print(f"🔍 [同步API] 检测到响应包含parts字段")
                    
                    if parts_to_check:
                        print(f"🔍 [同步API] 检查 {len(parts_to_check)} 个parts，查找图片数据...")
                        for idx, part in enumerate(parts_to_check):
                            if not isinstance(part, dict):
                                continue
                            
                            print(f"  part[{idx}] 键: {list(part.keys())}")
                            
                            # 检查inlineData字段（大写，标准格式）
                            if 'inlineData' in part:
                                inline_data = part['inlineData']
                                if isinstance(inline_data, dict) and 'data' in inline_data:
                                    image_data_base64 = inline_data['data']
                                    mime_type = inline_data.get('mimeType', 'image/png')
                                    print(f"✅ [同步API] 在part[{idx}]中找到图片数据（inlineData），MIME类型: {mime_type}, 数据长度: {len(image_data_base64) if image_data_base64 else 0}")
                                    break
                            # 检查inline_data字段（小写，兼容格式）
                            elif 'inline_data' in part:
                                inline_data = part['inline_data']
                                if isinstance(inline_data, dict) and 'data' in inline_data:
                                    image_data_base64 = inline_data['data']
                                    mime_type = inline_data.get('mime_type', 'image/png')
                                    print(f"✅ [同步API] 在part[{idx}]中找到图片数据（inline_data），MIME类型: {mime_type}, 数据长度: {len(image_data_base64) if image_data_base64 else 0}")
                                    break
                            # 检查text字段中是否有图片URL（markdown格式）
                            elif 'text' in part:
                                text = part.get('text', '')
                                if text:
                                    import re
                                    # 提取markdown格式的图片URL: ![alt](url)
                                    markdown_pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
                                    matches = re.findall(markdown_pattern, text)
                                    if matches:
                                        result_image_url = matches[0]
                                        print(f"✅ [同步API] 从text字段中提取到图片URL: {result_image_url}")
                                        break
                    else:
                        print(f"⚠️ [同步API] 未找到candidates或parts结构，尝试其他格式...")
                        print(f"   响应类型: {type(result)}")
                        print(f"   响应键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                elif api_config.api_type == 'nano-banana-edits':
                    # nano-banana-edits API响应格式（OpenAI DALL-E格式）
                    print(f"📦 [nano-banana-edits] 解析响应数据...")
                    print(f"📦 [nano-banana-edits] 响应数据结构: {json.dumps(result, ensure_ascii=False)[:500]}...")
                    
                    # 检查多种可能的响应格式
                    # 格式1: OpenAI DALL-E格式 {"created": 1234567890, "data": [{"url": "..."}]}
                    if 'data' in result and isinstance(result['data'], list) and len(result['data']) > 0:
                        result_image_url = result['data'][0].get('url')
                        print(f"✅ [nano-banana-edits] 找到图片URL (格式1): {result_image_url}")
                    # 格式2: 直接返回URL字符串
                    elif isinstance(result, str) and (result.startswith('http://') or result.startswith('https://')):
                        result_image_url = result
                        print(f"✅ [nano-banana-edits] 找到图片URL (格式2): {result_image_url}")
                    # 格式3: {"url": "..."}
                    elif 'url' in result:
                        result_image_url = result.get('url')
                        print(f"✅ [nano-banana-edits] 找到图片URL (格式3): {result_image_url}")
                    # 格式4: {"image_url": "..."} 或 {"result_url": "..."}
                    elif 'image_url' in result:
                        result_image_url = result.get('image_url')
                        print(f"✅ [nano-banana-edits] 找到图片URL (格式4): {result_image_url}")
                    elif 'result_url' in result:
                        result_image_url = result.get('result_url')
                        print(f"✅ [nano-banana-edits] 找到图片URL (格式5): {result_image_url}")
                    # 格式5: {"data": {"url": "..."}}
                    elif 'data' in result and isinstance(result['data'], dict):
                        result_image_url = result['data'].get('url') or result['data'].get('image_url')
                        print(f"✅ [nano-banana-edits] 找到图片URL (格式6): {result_image_url}")
                    else:
                        print(f"⚠️ [nano-banana-edits] 未找到图片URL，响应格式: {json.dumps(result, ensure_ascii=False)[:200]}")
                elif api_config.api_type == 'runninghub-rhart-edit':
                    # RunningHub API响应格式
                    # 响应格式：{"taskId": "...", "status": "QUEUED", "results": null, ...}
                    # RunningHub 是异步API，返回 taskId，需要轮询查询结果
                    # 这里不处理同步响应，因为 RunningHub 总是返回 taskId
                    print(f"📦 [RunningHub] 解析响应数据...")
                    print(f"📦 [RunningHub] 响应数据结构: {json.dumps(result, ensure_ascii=False)[:500]}...")
                    # RunningHub 的响应会在异步处理部分处理（返回 taskId）
                    # 这里不需要提取图片URL，因为 RunningHub 是异步API
                else:
                    # 其他同步API格式（如果有直接返回结果的）
                    # 尝试从响应中提取结果图片
                    if result.get('code') == 0 and 'data' in result:
                        result_image_url = result['data'].get('image_url') or result['data'].get('result_image') or result['data'].get('url')
                
                # 如果找到base64图片数据，需要解码并上传到云端
                if image_data_base64:
                    try:
                        print(f"📤 [同步API] 开始处理base64图片数据...")
                        # 解码base64图片
                        image_data = base64.b64decode(image_data_base64)
                        
                        # 保存到本地final_works目录（同步API直接返回结果，保存到本地即可）
                        # 关键修复：直接在项目目录创建文件，避免跨磁盘移动问题
                        final_folder = 'final_works'
                        os.makedirs(final_folder, exist_ok=True)
                        timestamp = int(time.time())
                        suffix = '.jpg' if 'jpeg' in mime_type.lower() else '.png'
                        # 使用task_id的前8位和完整task_id生成文件名（参考错误日志中的格式）
                        filename = f"final_{task_id[:8]}_{timestamp}{suffix}"
                        local_path = os.path.join(final_folder, filename)
                        
                        # 直接写入到目标位置（避免跨磁盘移动）
                        if os.path.exists(local_path):
                            os.remove(local_path)
                        
                        # 直接写入文件到目标位置
                        with open(local_path, 'wb') as f:
                            f.write(image_data)
                        
                        # 使用相对路径（用于存储到数据库）
                        result_image_url = os.path.join(final_folder, filename).replace('\\', '/')
                        print(f"✅ [同步API] 图片已保存到本地: {local_path}")
                        print(f"✅ [同步API] 图片路径（数据库）: {result_image_url}")
                    except Exception as e:
                        print(f"❌ [同步API] 处理base64图片失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # 如果找到图片URL，更新任务状态
                if result_image_url:
                    task.status = 'success'
                    task.output_image_path = result_image_url
                    task.completed_at = datetime.now()
                    
                    # 更新processing_log中的result_image
                    api_info = json.loads(task.processing_log) if task.processing_log else {}
                    api_info['result_image'] = result_image_url
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    
                    print(f"✅ [同步API] 任务 {task.id} 已完成，图片URL: {result_image_url}")
                else:
                    task.status = 'failed'
                    task.error_message = "同步API响应中未找到结果图片"
                    print(f"❌ [同步API] 任务 {task.id} 失败：未找到结果图片")
                    # 保存完整响应以便调试
                    api_info = json.loads(task.processing_log) if task.processing_log else {}
                    api_info['full_response'] = result
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
            else:
                # 异步API：返回task_id，需要轮询查询结果（参考bk-photo-v4）
                # nano-banana等标准格式：{"code": 0, "data": {"id": "xxx"}}
                api_task_id = None
                if result.get('code') == 0 and 'data' in result:
                    data = result.get('data')
                    if isinstance(data, dict):
                        # 格式1: {"code": 0, "data": {"id": "xxx"}}
                        api_task_id = data.get('id') or data.get('task_id')
                    elif isinstance(data, str):
                        # 格式2: {"code": 0, "data": "task_id字符串"}
                        api_task_id = data.strip() if data.strip() else None
                
                # RunningHub 格式：{"taskId": "xxx", "status": "QUEUED", ...} 或 {"code": 0, "data": {"taskId": "xxx"}}
                # 关键修复：对于 RunningHub API，优先提取 taskId（无论是否有错误码，RunningHub 都会返回 taskId）
                if api_config.api_type == 'runninghub-rhart-edit' or api_config.api_type == 'runninghub-comfyui-workflow':
                    api_type_name = 'RunningHub ComfyUI' if api_config.api_type == 'runninghub-comfyui-workflow' else 'RunningHub'
                    
                    # 关键修复：优先从顶层提取 taskId（RunningHub 响应格式：{"taskId": "xxx", "status": "RUNNING", ...}）
                    # 即使有错误码（如 code: 433），RunningHub 也可能返回 taskId
                    if not api_task_id:
                        api_task_id = result.get('taskId')
                        if api_task_id:
                            print(f"✅ [{api_type_name}] 从响应顶层提取到 taskId: {api_task_id}")
                    
                    # 如果顶层没有，检查 data 字段
                    if not api_task_id and result.get('data'):
                        if isinstance(result.get('data'), dict):
                            api_task_id = result.get('data', {}).get('taskId')
                            if api_task_id:
                                print(f"✅ [{api_type_name}] 从 data 字段提取到 taskId: {api_task_id}")
                        elif isinstance(result.get('data'), str):
                            # data 可能是 taskId 字符串
                            try:
                                # 尝试解析为数字（taskId 通常是数字字符串）
                                if result.get('data').strip().isdigit():
                                    api_task_id = result.get('data').strip()
                                    if api_task_id:
                                        print(f"✅ [{api_type_name}] 从 data 字符串提取到 taskId: {api_task_id}")
                            except:
                                pass
                    
                    # 如果还没找到，尝试从 msg 字段的 JSON 中提取（某些错误响应可能包含 taskId）
                    if not api_task_id and result.get('msg'):
                        try:
                            msg_json = json.loads(result.get('msg')) if isinstance(result.get('msg'), str) else result.get('msg')
                            if isinstance(msg_json, dict):
                                api_task_id = msg_json.get('taskId') or msg_json.get('task_id') or msg_json.get('id')
                                if api_task_id:
                                    print(f"✅ [{api_type_name}] 从 msg 字段提取到 taskId: {api_task_id}")
                        except:
                            pass
                
                # 如果上面没找到，尝试其他格式（非 RunningHub API）
                if not api_task_id:
                    # 格式3: {"task_id": "xxx"} 或 {"id": "xxx"}
                    api_task_id = result.get('task_id') or result.get('id')
                
                # 继续处理 RunningHub 的错误码（如果有）
                if api_config.api_type == 'runninghub-rhart-edit' or api_config.api_type == 'runninghub-comfyui-workflow':
                    # 检查是否有错误码（非0表示错误）
                    if result.get('code') and result.get('code') != 0:
                        error_code = result.get('code')
                        error_msg = result.get('msg', '')
                        
                        print(f"⚠️ [{api_type_name}] API返回错误码: {error_code}")
                        if api_task_id:
                            print(f"⚠️ [{api_type_name}] 但检测到 taskId: {api_task_id}，任务可能已创建，将继续处理")
                        
                        # 尝试解析错误信息（msg 可能是 JSON 字符串）
                        error_details = {}
                        if error_msg:
                            try:
                                error_details = json.loads(error_msg) if isinstance(error_msg, str) else error_msg
                            except:
                                error_details = {'raw_message': error_msg}
                        
                        # 提取节点错误信息
                        node_errors = error_details.get('node_errors', {})
                        error_summary = []
                        
                        if node_errors:
                            print(f"⚠️ [{api_type_name}] 工作流节点验证警告:")
                            for node_id, node_error in node_errors.items():
                                errors = node_error.get('errors', [])
                                node_name = node_error.get('node_name', '未知节点')
                                for err in errors:
                                    error_type = err.get('type', '')
                                    error_message = err.get('message', '')
                                    error_details_str = err.get('details', '')
                                    input_name = err.get('extra_info', {}).get('input_name', '')
                                    received_value = err.get('extra_info', {}).get('received_value', '')
                                    
                                    error_text = f"节点 {node_id} ({node_name})"
                                    if input_name:
                                        error_text += f" 字段 '{input_name}'"
                                    if error_message:
                                        error_text += f": {error_message}"
                                    if error_details_str:
                                        error_text += f" ({error_details_str})"
                                    if received_value:
                                        error_text += f" [当前值: {received_value}]"
                                    
                                    error_summary.append(error_text)
                                    print(f"   - {error_text}")
                        
                        # 构建警告消息
                        if error_summary:
                            warning_message = f"工作流验证警告（任务可能仍会执行）:\n" + "\n".join(f"  • {err}" for err in error_summary)
                        else:
                            warning_message = f"工作流验证警告 (错误码: {error_code})"
                            if error_msg:
                                warning_message += f": {error_msg[:200]}"
                        
                        # 保存警告信息到 processing_log，但不标记为失败
                        api_info = json.loads(task.processing_log) if task.processing_log else {}
                        api_info['warning_response'] = result
                        api_info['warning_details'] = error_details
                        api_info['warning_message'] = warning_message
                        task.processing_log = json.dumps(api_info, ensure_ascii=False)
                        
                        # 如果有 taskId，继续处理；如果没有 taskId，检查是否可以从其他地方提取
                        if not api_task_id:
                            # 尝试从 errorMessages 或其他字段提取 taskId
                            error_messages = result.get('errorMessages')
                            if error_messages:
                                if isinstance(error_messages, list) and len(error_messages) > 0:
                                    # 尝试从错误消息中提取 taskId（如果包含）
                                    for err_msg in error_messages:
                                        if isinstance(err_msg, str) and err_msg.strip().isdigit() and len(err_msg.strip()) > 10:
                                            api_task_id = err_msg.strip()
                                            print(f"🔍 [{api_type_name}] 从 errorMessages 中提取到可能的 taskId: {api_task_id}")
                                            break
                            
                            # 如果仍然没有 taskId，检查响应中的所有字段
                            if not api_task_id:
                                print(f"🔍 [{api_type_name}] 尝试从响应中搜索 taskId...")
                                for key, value in result.items():
                                    if key.lower() in ['taskid', 'task_id', 'id'] and value:
                                        if isinstance(value, str) and value.strip().isdigit() and len(value.strip()) > 10:
                                            api_task_id = value.strip()
                                            print(f"🔍 [{api_type_name}] 从字段 '{key}' 中找到可能的 taskId: {api_task_id}")
                                            break
                                        elif isinstance(value, (int, str)) and str(value).strip().isdigit() and len(str(value).strip()) > 10:
                                            api_task_id = str(value).strip()
                                            print(f"🔍 [{api_type_name}] 从字段 '{key}' 中找到可能的 taskId: {api_task_id}")
                                            break
                            
                            # 如果仍然没有 taskId，标记为失败，但提示用户可以手动输入
                            if not api_task_id:
                                task.status = 'failed'
                                error_msg = warning_message.replace("警告（任务可能仍会执行）", "失败")
                                error_msg += "\n\n💡 提示：如果 RunningHub 后台已创建任务，可以在任务管理页面手动输入 taskId 进行查询。"
                                task.error_message = error_msg
                                print(f"❌ [{api_type_name}] 任务已标记为失败（无 taskId）: {warning_message[:200]}")
                                print(f"💡 [{api_type_name}] 提示：如果 RunningHub 后台已创建任务，请手动输入 taskId 进行查询")
                                return False, task, warning_message
                            else:
                                # 找到了 taskId，继续处理
                                print(f"✅ [{api_type_name}] 从响应中提取到 taskId: {api_task_id}，任务将继续处理")
                        else:
                            # 有 taskId，保存警告信息但继续处理
                            print(f"⚠️ [{api_type_name}] 任务将继续处理（有 taskId），但存在验证警告")
                    
                    # 成功响应或虽有警告但有 taskId：提取并处理 taskId
                    if api_task_id:
                        print(f"✅ [{api_type_name}] 找到 taskId: {api_task_id}")
                        # RunningHub 的状态：QUEUED, RUNNING, SUCCESS, FAILED 等
                        status = result.get('status', '')
                        if not status and result.get('data'):
                            status = result.get('data', {}).get('status', '')
                        print(f"📊 [{api_type_name}] 任务状态: {status}")
                        # 如果状态是 FAILED，检查错误信息
                        if status == 'FAILED':
                            error_code = result.get('errorCode', '')
                            error_message = result.get('errorMessage', '')
                            if error_code or error_message:
                                print(f"❌ [{api_type_name}] 任务失败: {error_code} - {error_message}")
                
                if api_task_id:
                    task.status = 'processing'
                    # 保存API返回的task_id到comfyui_prompt_id字段（用于轮询查询，参考bk-photo-v4）
                    task.comfyui_prompt_id = api_task_id
                    # 同时保存到processing_log中
                    api_info = json.loads(task.processing_log) if task.processing_log else {}
                    api_info['api_task_id'] = api_task_id
                    api_info['original_response'] = result
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    # 关键修复：保存API返回的task_id到notes字段（格式：T8_API_TASK_ID:xxx），用于轮询时优先提取（参考bk-photo-v4）
                    if task.notes:
                        task.notes = f"T8_API_TASK_ID:{api_task_id} | {task.notes}"
                    else:
                        task.notes = f"T8_API_TASK_ID:{api_task_id}"
                    # 同时保存完整响应到processing_log的result_data（用于轮询时提取，参考bk-photo-v4）
                    # 注意：AITask模型没有result_data字段，所以保存到processing_log中
                    api_info['result_data'] = result  # 保存完整响应对象（不是字符串）
                    task.processing_log = json.dumps(api_info, ensure_ascii=False)
                    
                    # 从API响应中提取预计完成时间（如果API返回了该字段）
                    if api_config.api_type in ['runninghub-rhart-edit', 'runninghub-comfyui-workflow']:
                        estimated_time_from_api = None
                        
                        # 检查响应中可能包含预计完成时间的字段
                        for field_name in ['estimatedTime', 'estimated_time', 'eta', 'ETA', 'estimatedCompletionTime', 'finishTime', 'finish_time']:
                            if field_name in result:
                                estimated_time_from_api = result.get(field_name)
                                break
                        
                        # 检查 data 字段中
                        if not estimated_time_from_api and result.get('data'):
                            data = result.get('data')
                            if isinstance(data, dict):
                                for field_name in ['estimatedTime', 'estimated_time', 'eta', 'ETA', 'estimatedCompletionTime', 'finishTime', 'finish_time']:
                                    if field_name in data:
                                        estimated_time_from_api = data.get(field_name)
                                        break
                        
                        # 如果API返回了预计完成时间，使用API的值
                        if estimated_time_from_api:
                            try:
                                # 尝试解析为时间戳（秒或毫秒）
                                if isinstance(estimated_time_from_api, (int, float)):
                                    # 判断是秒还是毫秒（通常大于1000000000的是秒，否则可能是毫秒）
                                    if estimated_time_from_api > 1000000000000:  # 毫秒
                                        estimated_time_from_api = estimated_time_from_api / 1000
                                    estimated_time = datetime.fromtimestamp(estimated_time_from_api)
                                elif isinstance(estimated_time_from_api, str):
                                    # 尝试解析ISO格式字符串
                                    try:
                                        estimated_time = datetime.fromisoformat(estimated_time_from_api.replace('Z', '+00:00'))
                                    except:
                                        # 尝试解析时间戳字符串
                                        try:
                                            timestamp = float(estimated_time_from_api)
                                            if timestamp > 1000000000000:  # 毫秒
                                                timestamp = timestamp / 1000
                                            estimated_time = datetime.fromtimestamp(timestamp)
                                        except:
                                            estimated_time = None
                                else:
                                    estimated_time = None
                                
                                if estimated_time:
                                    task.estimated_completion_time = estimated_time
                                    print(f"📅 [创建任务] RunningHub 任务预计完成时间（来自API）: {estimated_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            except Exception as e:
                                print(f"⚠️ [创建任务] 解析API返回的预计完成时间失败: {str(e)}")
                        else:
                            # 如果API没有返回预计完成时间，打印调试信息
                            print(f"🔍 [创建任务] RunningHub API响应中未找到预计完成时间字段，响应字段: {list(result.keys())}")
                            if result.get('data') and isinstance(result.get('data'), dict):
                                print(f"🔍 [创建任务] data字段中的键: {list(result.get('data').keys())}")
                    
                    print(f"✅ 已保存API返回的task_id: {api_task_id} 到 comfyui_prompt_id、notes 和 processing_log")
                else:
                    task.status = 'failed'
                    task.error_message = f"异步API响应中未找到任务ID，响应: {json.dumps(result, ensure_ascii=False)[:500]}"
                    print(f"❌ 异步API响应中未找到任务ID，完整响应: {json.dumps(result, ensure_ascii=False)}")
        else:
            task.status = 'failed'
            task.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
        
        db.session.commit()
        
        return True, task, None
        
    except Exception as e:
        import traceback
        error_msg = f"创建API任务失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        if db:
            db.session.rollback()
        return False, None, error_msg


def create_api_tasks_batch(style_image_id, prompts, image_size='1K', aspect_ratio='auto', uploaded_images=None,
                          upload_config=None, api_config_id=None, order_id=None, order_number=None,
                          db=None, AITask=None, APITemplate=None, APIProviderConfig=None,
                          StyleImage=None, StyleCategory=None):
    """
    批量创建API调用任务（根据多个提示词创建多个任务）
    
    Args:
        style_image_id: 风格图片ID
        prompts: 提示词列表（字符串数组）
        image_size: 图片尺寸
        aspect_ratio: 图片比例
        uploaded_images: 上传的图片URL列表
        upload_config: 上传配置
        api_config_id: API配置ID（可选）
        order_id: 订单ID（可选，如果提供，所有任务将关联到该订单）
        order_number: 订单号（可选）
        db: 数据库实例
        AITask: AITask模型类
        APITemplate: APITemplate模型类
        APIProviderConfig: APIProviderConfig模型类
        StyleImage: StyleImage模型类
        StyleCategory: StyleCategory模型类
    
    Returns:
        tuple: (success: bool, tasks: list[AITask], error_message: str)
    """
    try:
        # 验证提示词列表
        if not prompts or not isinstance(prompts, list) or len(prompts) == 0:
            return False, [], "提示词列表不能为空"
        
        # 过滤空提示词
        valid_prompts = [p.strip() for p in prompts if p and p.strip()]
        if len(valid_prompts) == 0:
            return False, [], "没有有效的提示词"
        
        # 如果设置了order_id，为所有任务设置相同的order_id和order_number
        if order_id:
            create_api_task._test_order_id = order_id
            if order_number:
                create_api_task._test_order_number = order_number
        
        # 批量创建任务
        created_tasks = []
        errors = []
        
        for idx, prompt in enumerate(valid_prompts):
            try:
                success, task, error_message = create_api_task(
                    style_image_id=style_image_id,
                    prompt=prompt,
                    image_size=image_size,
                    aspect_ratio=aspect_ratio,
                    uploaded_images=uploaded_images,
                    upload_config=upload_config,
                    api_config_id=api_config_id,
                    db=db,
                    AITask=AITask,
                    APITemplate=APITemplate,
                    APIProviderConfig=APIProviderConfig,
                    StyleImage=StyleImage,
                    StyleCategory=StyleCategory
                )
                
                if success and task:
                    created_tasks.append(task)
                    print(f"✅ 批量任务 {idx + 1}/{len(valid_prompts)} 创建成功: task_id={task.id}, prompt={prompt[:50]}...")
                else:
                    errors.append(f"提示词 {idx + 1} ({prompt[:50]}...): {error_message}")
                    print(f"❌ 批量任务 {idx + 1}/{len(valid_prompts)} 创建失败: {error_message}")
            except Exception as e:
                error_msg = f"提示词 {idx + 1} ({prompt[:50]}...): {str(e)}"
                errors.append(error_msg)
                print(f"❌ 批量任务 {idx + 1}/{len(valid_prompts)} 创建异常: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 如果至少有一个任务创建成功，返回成功
        if len(created_tasks) > 0:
            error_message = f"成功创建 {len(created_tasks)}/{len(valid_prompts)} 个任务" + (f"，失败: {', '.join(errors)}" if errors else "")
            return True, created_tasks, error_message if errors else None
        else:
            return False, [], f"所有任务创建失败: {', '.join(errors)}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, [], f"批量创建任务失败: {str(e)}"
