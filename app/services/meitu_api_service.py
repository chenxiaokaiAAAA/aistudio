# -*- coding: utf-8 -*-
"""
美图API服务
"""
import logging

logger = logging.getLogger(__name__)
import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from urllib.parse import urlencode

import requests


def upload_image_to_oss(image_path, order_number=None):
    """
    将本地图片上传到OSS获取公网URL（用于测试环境）

    Args:
        image_path: 本地图片路径
        order_number: 订单号（用于生成OSS路径）

    Returns:
        tuple: (success: bool, public_url: str, error_message: str)
    """
    try:
        # 尝试导入OSS配置
        try:
            from scripts.oss_config import OSSUploader
            uploader = OSSUploader()

            # 上传图片到OSS
            if order_number:
                # 优先使用测试图片上传方法
                if hasattr(uploader, 'upload_test_image'):
                    result = uploader.upload_test_image(image_path, order_number)
                else:
                    result = uploader.upload_hd_image(image_path, order_number)
            else:
                # 如果没有订单号，使用测试图片上传方法
                if hasattr(uploader, 'upload_test_image'):
                    result = uploader.upload_test_image(image_path)
                elif hasattr(uploader, 'upload_file'):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = os.path.basename(image_path)
                    oss_path = f"meitu_test/{timestamp}_{filename}"
                    result = uploader.upload_file(image_path, oss_path)
                else:
                    result = uploader.upload_hd_image(image_path, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            if result.get('success'):
                logger.info(f"✅ 图片已上传到OSS: {result['url']}")
                return True, result['url'], None
            else:
                error_msg = result.get('message', 'OSS上传失败')
                logger.error("OSS上传失败: {error_msg}")
                return False, None, error_msg
        except ImportError:
            logger.warning("OSS配置未找到，跳过OSS上传")
            return False, None, "OSS配置未找到"
        except Exception as e:
            error_msg = f"OSS上传异常: {str(e)}"
            logger.error("{error_msg}")
            return False, None, error_msg
    except Exception as e:
        error_msg = f"上传图片到OSS失败: {str(e)}"
        logger.error("{error_msg}")
        return False, None, error_msg


def get_public_image_url(image_path, use_oss=True, order_number=None, base_url='http://localhost:8000'):
    """
    获取图片的公网可访问URL

    Args:
        image_path: 本地图片路径或已有URL
        use_oss: 是否使用OSS上传（测试环境建议True）
        order_number: 订单号（用于OSS路径）
        base_url: 服务器基础URL（如果不用OSS，用于构建本地URL）

    Returns:
        str: 图片的公开URL，如果失败返回None
    """
    try:
        # 如果已经是URL，直接返回
        if image_path.startswith('http://') or image_path.startswith('https://'):
            return image_path

        # 如果使用OSS，上传到OSS获取公网URL
        if use_oss:
            success, public_url, error_msg = upload_image_to_oss(image_path, order_number)
            if success:
                return public_url
            else:
                logger.warning("OSS上传失败，尝试使用本地URL: {error_msg}")
                # OSS上传失败，fallback到本地URL（仅用于开发测试）

        # 如果图片路径是相对路径，转换为绝对URL（仅用于开发测试，生产环境不推荐）
        if image_path.startswith('/'):
            # 假设图片在static或uploads目录下
            if '/static/' in image_path or '/media/' in image_path:
                return f"{base_url.rstrip('/')}{image_path}"
            else:
                # 尝试从uploads目录访问
                return f"{base_url.rstrip('/')}/media/uploads/{os.path.basename(image_path)}"
        else:
            # 相对路径，尝试构建URL
            filename = os.path.basename(image_path)
            return f"{base_url.rstrip('/')}/media/uploads/{filename}"
    except Exception as e:
        logger.error("获取图片URL失败: {str(e)}")
        return None


def call_meitu_api(image_path, preset_id, api_key, api_secret, api_base_url='https://api.yunxiu.meitu.com', api_endpoint='/openapi/realphotolocal_async', repost_url=None, db=None, MeituAPICallLog=None, order_id=None, order_number=None, product_id=None):
    """
    调用美图API进行图片精修（异步接口）

    Args:
        image_path: 图片本地路径（需要先上传到可访问的URL，或直接传入图片URL）
        preset_id: 预设ID（media_code）
        api_key: API密钥
        api_secret: API密钥
        api_base_url: API基础URL，默认：https://api.yunxiu.meitu.com
        api_endpoint: API接口路径，默认：/openapi/realphotolocal_async
        repost_url: 回调URL（可选）
        db: 数据库实例
        MeituAPICallLog: MeituAPICallLog模型类
        order_id: 订单ID（可选）
        order_number: 订单号（可选）
        product_id: 产品ID（可选）

    Returns:
        tuple: (success: bool, result_image_path: str, error_message: str, call_log: MeituAPICallLog)

    Note:
        这是异步接口，返回的msg_id需要通过回调或轮询获取最终结果
"""
    start_time = time.time()
    call_log = None

    try:
        # 1. 获取图片的公开URL（美图API需要图片URL，不是文件上传）
        # 如果image_path已经是URL，直接使用；否则需要检查文件是否存在并上传到可访问的URL
        if image_path.startswith('http://') or image_path.startswith('https://'):
            # 已经是URL，直接使用
            media_data_url = image_path
            logger.info(f"✅ 使用提供的图片URL: {media_data_url}")
        else:
            # 是本地文件路径，需要检查文件是否存在
            if not os.path.exists(image_path):
                error_msg = f"图片文件不存在: {image_path}"
                if db and MeituAPICallLog:
                    call_log = MeituAPICallLog(
                        order_id=order_id,
                        order_number=order_number,
                        product_id=product_id,
                        preset_id=preset_id,
                        error_message=error_msg,
                        status='failed',
                        duration_ms=int((time.time() - start_time) * 1000)
                    )
                    db.session.add(call_log)
                    db.session.commit()
                return False, None, error_msg, call_log

            # 需要将本地图片转换为可访问的URL
            # 这里假设图片已经可以通过某个URL访问，或者需要先上传
            # 暂时使用本地路径，实际使用时需要先上传到OSS或CDN
            media_data_url = get_public_image_url(image_path, order_number=order_number)
            if not media_data_url:
                error_msg = f"无法获取图片的公开URL: {image_path}"
                if db and MeituAPICallLog:
                    call_log = MeituAPICallLog(
                        order_id=order_id,
                        order_number=order_number,
                        product_id=product_id,
                        preset_id=preset_id,
                        error_message=error_msg,
                        status='failed',
                        duration_ms=int((time.time() - start_time) * 1000)
                    )
                    db.session.add(call_log)
                    db.session.commit()
                return False, None, error_msg, call_log

        # 3. 构建请求参数（根据美图API文档）
        request_data = {
            'api_key': api_key,
            'api_secret': api_secret,
            'media_code': preset_id,  # preset_id对应media_code
            'media_data': media_data_url  # 图片URL
        }

        # 如果有回调URL，添加到请求中
        if repost_url:
            request_data['repost_url'] = repost_url

        # 4. 构建请求URL
        if not api_endpoint:
            api_endpoint = '/openapi/realphotolocal_async'  # 默认异步接口

        # 确保 endpoint 以 / 开头
        if not api_endpoint.startswith('/'):
            api_endpoint = '/' + api_endpoint

        request_url = f"{api_base_url.rstrip('/')}{api_endpoint}"
        logger.info(f"📤 美图API请求URL: {request_url}")
        logger.info(f"📤 美图API请求参数: {json.dumps(request_data, ensure_ascii=False)}")

        # 5. 发送JSON请求
        try:
            response = requests.post(
                request_url,
                json=request_data,  # 使用json参数发送JSON数据
                headers={'Content-Type': 'application/json'},
                timeout=60,
                proxies={'http': None, 'https': None}
            )

            logger.info(f"📥 美图API响应状态码: {response.status_code}")
            logger.info(f"📥 美图API响应内容: {response.text[:500]}")

            duration_ms = int((time.time() - start_time) * 1000)

            # 6. 记录调用日志
            if db and MeituAPICallLog:
                call_log = MeituAPICallLog(
                    order_id=order_id,
                    order_number=order_number,
                    product_id=product_id,
                    preset_id=preset_id,
                    request_url=request_url,
                    request_params=json.dumps(request_data, ensure_ascii=False),
                    response_status=response.status_code,
                    response_data=response.text[:5000] if response.text else None,  # 限制长度
                    duration_ms=duration_ms,
                    status='pending',  # 异步接口，初始状态为pending
                    error_message=None
                )
                db.session.add(call_log)

            # 7. 处理响应（异步接口返回msg_id）
            if response.status_code == 200:
                result = response.json()

                # 根据美图API文档，响应格式：
                # {
                #   "code": 0,
                #   "data": {"msg_id": "..."},
                #   "message": "success",
                #   "request_id": "..."
                # }
                if result.get('code') == 0 and 'data' in result and 'msg_id' in result['data']:
                    msg_id = result['data']['msg_id']
                    request_id = result.get('request_id', '')

                    # 更新调用日志，保存msg_id用于后续查询
                    if call_log:
                        call_log.status = 'pending'  # 异步处理中
                        call_log.msg_id = msg_id  # 直接保存msg_id到独立字段
                        # 将msg_id和request_id保存到response_data中（保留完整响应）
                        call_log.response_data = json.dumps({
                            'msg_id': msg_id,
                            'request_id': request_id,
                            'original_response': result
                        }, ensure_ascii=False)
                        db.session.commit()

                    logger.info(f"✅ 美图API调用成功，收到msg_id: {msg_id}")
                    # 异步接口，不立即返回结果图片
                    # 需要通过回调或轮询获取最终结果
                    return True, None, None, call_log
                else:
                    error_msg = f"API响应格式错误或业务失败: {result}"
                    if call_log:
                        call_log.status = 'failed'
                        call_log.error_message = error_msg
                        db.session.commit()
                    return False, None, error_msg, call_log
            else:
                error_msg = f"API调用失败: HTTP {response.status_code} - {response.text[:500]}"
                if call_log:
                    call_log.status = 'failed'
                    call_log.error_message = error_msg
                    db.session.commit()
                return False, None, error_msg, call_log

        except requests.exceptions.RequestException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"网络请求失败: {str(e)}"

            if db and MeituAPICallLog:
                call_log = MeituAPICallLog(
                    order_id=order_id,
                    order_number=order_number,
                    product_id=product_id,
                    preset_id=preset_id,
                    request_url=request_url if 'request_url' in locals() else None,
                    request_params=json.dumps(request_data, ensure_ascii=False) if 'request_data' in locals() else None,
                    error_message=error_msg,
                    duration_ms=duration_ms,
                    status='failed'
                )
                db.session.add(call_log)
                db.session.commit()

            return False, None, error_msg, call_log

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = f"调用美图API异常: {str(e)}"

        if db and MeituAPICallLog:
            call_log = MeituAPICallLog(
                order_id=order_id,
                order_number=order_number,
                product_id=product_id,
                preset_id=preset_id,
                error_message=error_msg,
                duration_ms=duration_ms,
                status='failed'
            )
            db.session.add(call_log)
            db.session.commit()

        return False, None, error_msg, call_log


def download_result_image(image_url, order_number=None):
    """
    下载美图API返回的结果图片

    Args:
        image_url: 图片URL
        order_number: 订单号（用于生成文件名）

    Returns:
        str: 本地保存的图片路径
    """
    try:
        response = requests.get(image_url, timeout=60, proxies={'http': None, 'https': None})
        if response.status_code == 200:
            # 保存到uploads/meitu_results目录
            uploads_dir = 'uploads'
            results_dir = os.path.join(uploads_dir, 'meitu_results')
            os.makedirs(results_dir, exist_ok=True)

            # 生成文件名
            if order_number:
                filename = f"{order_number}_{int(time.time())}.jpg"
            else:
                filename = f"meitu_{int(time.time())}.jpg"

            filepath = os.path.join(results_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"✅ 美图结果图片已保存: {filepath}")
            return filepath
        else:
            logger.error("下载美图结果图片失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error("下载美图结果图片异常: {str(e)}")
        return None


def get_meitu_config(db=None, MeituAPIConfig=None):
    """
    获取美图API配置

    Returns:
        dict: 配置信息，如果未配置则返回None
    """
    if not db or not MeituAPIConfig:
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'MeituAPIConfig'):
                MeituAPIConfig = test_server_module.MeituAPIConfig

    if not db or not MeituAPIConfig:
        return None

    config = MeituAPIConfig.query.filter_by(is_active=True).first()
    if config:
        return {
            'app_id': config.app_id,
            'app_key': config.app_key,
            'secret_id': config.secret_id,
            'api_base_url': config.api_base_url
        }

    return None


def get_preset_id_by_product(product_id, db=None, MeituAPIPreset=None):
    """
    根据产品ID获取预设ID

    Args:
        product_id: 产品ID

    Returns:
        str: 预设ID，如果未配置则返回None
    """
    if not db or not MeituAPIPreset:
        # 尝试从test_server获取
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            if hasattr(test_server_module, 'db'):
                db = test_server_module.db
            if hasattr(test_server_module, 'MeituAPIPreset'):
                MeituAPIPreset = test_server_module.MeituAPIPreset

    if not db or not MeituAPIPreset:
        return None

    preset = MeituAPIPreset.query.filter_by(product_id=product_id, is_active=True).first()
    if preset:
        return preset.preset_id

    return None
