# -*- coding: utf-8 -*-
"""
管理后台系统配置API路由模块
提供系统配置的获取和保存功能
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_api_required

# 创建蓝图
admin_system_api_bp = Blueprint('admin_system_api', __name__)

@admin_system_api_bp.route('/api/admin/system-config', methods=['GET'])
@login_required
@admin_api_required
def api_get_system_config():
    """获取系统配置"""
    try:
        models = get_models(['AIConfig'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        AIConfig = models['AIConfig']
        
        configs = {}
        
        # 获取ComfyUI配置
        ai_configs = AIConfig.query.all()
        for config in ai_configs:
            if config.config_key == 'comfyui_base_url':
                configs['comfyui_base_url'] = config.config_value
            elif config.config_key == 'comfyui_api_endpoint':
                configs['comfyui_api_endpoint'] = config.config_value
            elif config.config_key == 'comfyui_timeout':
                configs['comfyui_timeout'] = config.config_value
        
        # 获取服务器URL配置（优先从数据库读取，如果数据库没有则从server_config读取）
        # 先尝试从数据库获取
        db_url_configs = {}
        for config in ai_configs:
            if config.config_key == 'server_base_url':
                db_url_configs['server_base_url'] = config.config_value
            elif config.config_key == 'server_api_url':
                db_url_configs['server_api_url'] = config.config_value
            elif config.config_key == 'server_media_url':
                db_url_configs['server_media_url'] = config.config_value
            elif config.config_key == 'server_static_url':
                db_url_configs['server_static_url'] = config.config_value
        
        # 如果数据库有配置，使用数据库的；否则使用server_config的
        if db_url_configs:
            configs.update(db_url_configs)
        else:
            # 如果数据库没有配置，从server_config读取
            try:
                from server_config import get_base_url, get_api_base_url, get_media_url, get_static_url
                configs['server_base_url'] = get_base_url()
                configs['server_api_url'] = get_api_base_url()
                configs['server_media_url'] = get_media_url()
                configs['server_static_url'] = get_static_url()
            except:
                # 如果server_config也不可用，使用默认值
                pass
        
        # 获取并发和队列配置
        for config in ai_configs:
            if config.config_key == 'comfyui_max_concurrency':
                configs['comfyui_max_concurrency'] = config.config_value
            elif config.config_key == 'api_max_concurrency':
                configs['api_max_concurrency'] = config.config_value
            elif config.config_key == 'task_queue_max_size':
                configs['task_queue_max_size'] = config.config_value
            elif config.config_key == 'task_queue_workers':
                configs['task_queue_workers'] = config.config_value
            elif config.config_key == 'brand_name':
                configs['brand_name'] = config.config_value
            # 支付配置
            elif config.config_key == 'payment_test_mode':
                configs['payment_test_mode'] = config.config_value
            elif config.config_key == 'payment_skip_payment':
                configs['payment_skip_payment'] = config.config_value
            elif config.config_key == 'payment_qrcode_url':
                configs['payment_qrcode_url'] = config.config_value
            # 图片路径配置
            elif config.config_key == 'image_path_upload_folder':
                configs['image_path_upload_folder'] = config.config_value
            elif config.config_key == 'image_path_final_folder':
                configs['image_path_final_folder'] = config.config_value
            elif config.config_key == 'image_path_hd_folder':
                configs['image_path_hd_folder'] = config.config_value
            elif config.config_key == 'image_path_watermark_folder':
                configs['image_path_watermark_folder'] = config.config_value
            elif config.config_key == 'image_path_static_folder':
                configs['image_path_static_folder'] = config.config_value
            elif config.config_key == 'image_storage_type':
                configs['image_storage_type'] = config.config_value
            elif config.config_key == 'image_oss_bucket':
                configs['image_oss_bucket'] = config.config_value
            elif config.config_key == 'image_oss_endpoint':
                configs['image_oss_endpoint'] = config.config_value
            elif config.config_key == 'image_oss_domain':
                configs['image_oss_domain'] = config.config_value
            # 图片上传配置
            elif config.config_key == 'image_upload_strategy':
                configs['image_upload_strategy'] = config.config_value
            elif config.config_key == 'image_upload_environment':
                configs['image_upload_environment'] = config.config_value
        
        # 如果没有配置品牌名称，使用默认值
        if 'brand_name' not in configs:
            configs['brand_name'] = 'AI拍照机'
        
        # 如果没有配置图片上传策略，使用默认值（本地测试环境，上传到GRSAI）
        if 'image_upload_strategy' not in configs:
            configs['image_upload_strategy'] = 'grsai'
        if 'image_upload_environment' not in configs:
            configs['image_upload_environment'] = 'local'
        
        return jsonify({
            'status': 'success',
            'data': configs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取配置失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/system-config/comfyui', methods=['POST'])
@login_required
@admin_api_required
def api_save_comfyui_config():
    """保存ComfyUI配置"""
    try:
        models = get_models(['AIConfig', 'db'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('comfyui_base_url', data.get('comfyui_base_url'), 'ComfyUI服务器地址'),
            ('comfyui_api_endpoint', data.get('comfyui_api_endpoint'), 'ComfyUI API端点'),
            ('comfyui_timeout', data.get('comfyui_timeout'), 'ComfyUI请求超时时间（秒）')
        ]
        
        for config_key, config_value, description in configs_to_save:
            if config_value:
                config = AIConfig.query.filter_by(config_key=config_key).first()
                if config:
                    config.config_value = str(config_value)
                    config.description = description
                    config.updated_at = datetime.now()
                else:
                    config = AIConfig(
                        config_key=config_key,
                        config_value=str(config_value),
                        description=description
                    )
                    db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ ComfyUI配置已更新: {data.get('comfyui_base_url')}")
        
        return jsonify({
            'status': 'success',
            'message': 'ComfyUI配置保存成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/system-config/server-url', methods=['POST'])
@login_required
@admin_api_required
def api_save_server_url_config():
    """保存服务器URL配置"""
    try:
        models = get_models(['AIConfig', 'db'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('server_base_url', data.get('server_base_url'), '服务器基础URL'),
            ('server_api_url', data.get('server_api_url'), 'API基础URL'),
            ('server_media_url', data.get('server_media_url'), '媒体文件URL'),
            ('server_static_url', data.get('server_static_url'), '静态文件URL')
        ]
        
        for config_key, config_value, description in configs_to_save:
            if config_value:
                config = AIConfig.query.filter_by(config_key=config_key).first()
                if config:
                    config.config_value = str(config_value)
                    config.description = description
                    config.updated_at = datetime.now()
                else:
                    config = AIConfig(
                        config_key=config_key,
                        config_value=str(config_value),
                        description=description
                    )
                    db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ 服务器URL配置已更新")
        
        return jsonify({
            'status': 'success',
            'message': '服务器URL配置保存成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/system-config/brand-name', methods=['POST'])
@login_required
@admin_api_required
def api_save_brand_name_config():
    """保存品牌名称配置"""
    try:
        models = get_models(['AIConfig', 'db'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        brand_name = data.get('brand_name', '').strip()
        
        if not brand_name:
            return jsonify({'status': 'error', 'message': '品牌名称不能为空'}), 400
        
        config = AIConfig.query.filter_by(config_key='brand_name').first()
        if config:
            config.config_value = brand_name
            config.description = '系统品牌名称'
            config.updated_at = datetime.now()
        else:
            config = AIConfig(
                config_key='brand_name',
                config_value=brand_name,
                description='系统品牌名称'
            )
            db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ 品牌名称配置已更新: {brand_name}")
        
        return jsonify({
            'status': 'success',
            'message': '品牌名称配置保存成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/system-config/concurrency', methods=['POST'])
@login_required
@admin_api_required
def api_save_concurrency_config():
    """保存并发和队列配置"""
    try:
        models = get_models(['AIConfig', 'db'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('comfyui_max_concurrency', data.get('comfyui_max_concurrency'), 'ComfyUI最大并发数'),
            ('api_max_concurrency', data.get('api_max_concurrency'), 'API最大并发数'),
            ('task_queue_max_size', data.get('task_queue_max_size'), '任务队列最大大小'),
            ('task_queue_workers', data.get('task_queue_workers'), '任务队列工作线程数')
        ]
        
        for config_key, config_value, description in configs_to_save:
            if config_value is not None:
                config = AIConfig.query.filter_by(config_key=config_key).first()
                if config:
                    config.config_value = str(config_value)
                    config.description = description
                    config.updated_at = datetime.now()
                else:
                    config = AIConfig(
                        config_key=config_key,
                        config_value=str(config_value),
                        description=description
                    )
                    db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ 并发和队列配置已更新: ComfyUI={data.get('comfyui_max_concurrency')}, API={data.get('api_max_concurrency')}, 队列大小={data.get('task_queue_max_size')}, 工作线程={data.get('task_queue_workers')}")
        
        return jsonify({
            'status': 'success',
            'message': '并发和队列配置保存成功（需要重启服务才能生效）'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/system-config/image-upload', methods=['POST'])
@login_required
@admin_api_required
def api_save_image_upload_config():
    """保存图片上传配置"""
    try:
        models = get_models(['AIConfig', 'db'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('image_upload_strategy', data.get('image_upload_strategy'), '图片上传策略：grsai=上传到GRSAI服务器，direct=直接使用云端URL'),
            ('image_upload_environment', data.get('image_upload_environment'), '运行环境：local=本地测试环境，production=云端生产环境')
        ]
        
        for config_key, config_value, description in configs_to_save:
            if config_value:
                config = AIConfig.query.filter_by(config_key=config_key).first()
                if config:
                    config.config_value = str(config_value)
                    config.description = description
                    config.updated_at = datetime.now()
                else:
                    config = AIConfig(
                        config_key=config_key,
                        config_value=str(config_value),
                        description=description
                    )
                    db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ 图片上传配置已更新: strategy={data.get('image_upload_strategy')}, environment={data.get('image_upload_environment')}")
        
        return jsonify({
            'status': 'success',
            'message': '图片上传配置保存成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/system-config/image-paths', methods=['POST'])
@login_required
@admin_api_required
def api_save_image_paths_config():
    """保存图片路径配置"""
    try:
        models = get_models(['AIConfig', 'db'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('image_path_upload_folder', data.get('upload_folder'), '用户上传原图文件夹路径'),
            ('image_path_final_folder', data.get('final_folder'), '完成效果图文件夹路径'),
            ('image_path_hd_folder', data.get('hd_folder'), '高清图文件夹路径'),
            ('image_path_watermark_folder', data.get('watermark_folder'), '水印文件夹路径'),
            ('image_path_static_folder', data.get('static_folder'), '静态文件文件夹路径'),
            ('image_storage_type', data.get('storage_type', 'local'), '存储类型：local或oss'),
            ('image_oss_bucket', data.get('oss_bucket'), 'OSS存储桶名称'),
            ('image_oss_endpoint', data.get('oss_endpoint'), 'OSS端点地址'),
            ('image_oss_domain', data.get('oss_domain'), 'OSS自定义域名'),
        ]
        
        for config_key, config_value, description in configs_to_save:
            if config_value is not None:
                config = AIConfig.query.filter_by(config_key=config_key).first()
                if config:
                    config.config_value = str(config_value) if config_value else ''
                    config.description = description
                    config.updated_at = datetime.now()
                else:
                    config = AIConfig(
                        config_key=config_key,
                        config_value=str(config_value) if config_value else '',
                        description=description
                    )
                    db.session.add(config)
        
        # OSS密钥单独处理（敏感信息）
        if data.get('oss_access_key'):
            config_key = 'image_oss_access_key'
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = data.get('oss_access_key')
                config.description = 'OSS访问密钥ID'
                config.updated_at = datetime.now()
            else:
                config = AIConfig(
                    config_key=config_key,
                    config_value=data.get('oss_access_key'),
                    description='OSS访问密钥ID'
                )
                db.session.add(config)
        
        if data.get('oss_secret_key'):
            config_key = 'image_oss_secret_key'
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = data.get('oss_secret_key')
                config.description = 'OSS访问密钥Secret'
                config.updated_at = datetime.now()
            else:
                config = AIConfig(
                    config_key=config_key,
                    config_value=data.get('oss_secret_key'),
                    description='OSS访问密钥Secret'
                )
                db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ 图片路径配置已更新: 存储类型={data.get('storage_type', 'local')}")
        
        return jsonify({
            'status': 'success',
            'message': '图片路径配置保存成功（需要重启服务才能生效）'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@admin_system_api_bp.route('/api/admin/orders/latest', methods=['GET'])
@login_required
@admin_api_required
def api_get_latest_orders():
    """获取最新订单列表（用于浏览器通知）"""
    try:
        models = get_models(['Order'])
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        
        # 获取时间参数
        after_time = request.args.get('after')
        
        # 构建查询
        query = Order.query.filter(Order.status != 'unpaid')
        
        # 如果提供了时间参数，只返回该时间之后的订单
        if after_time:
            try:
                after_datetime = datetime.fromisoformat(after_time)
                query = query.filter(Order.created_at > after_datetime)
            except ValueError:
                pass
        
        # 获取订单列表（只取最近10条）
        orders = query.order_by(Order.created_at.desc()).limit(10).all()
        
        # 构建响应数据
        order_list = []
        latest_time = after_time if after_time else datetime.now().isoformat()
        
        for order in orders:
            # 确定订单来源
            if order.franchisee_id:
                source = '加盟商'
            elif order.source_type == 'miniprogram':
                source = '小程序'
            elif order.source_type == 'website':
                source = '网页版'
            else:
                source = '未知'
            
            order_list.append({
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'total_price': f"{order.price:.2f}" if order.price else "0.00",
                'source': source
            })
            
            # 更新最新时间
            if order.created_at:
                latest_time = order.created_at.isoformat()
        
        return jsonify({
            'success': True,
            'orders': order_list,
            'latest_time': latest_time
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取订单列表失败: {str(e)}'
        }), 500
