# -*- coding: utf-8 -*-
"""
管理后台路由模块
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
import sys
import os
import uuid
from werkzeug.utils import secure_filename

# 创建蓝图
admin_bp = Blueprint('admin', __name__)


def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'User': test_server_module.User,
        'Order': test_server_module.Order,
        'FranchiseeAccount': test_server_module.FranchiseeAccount,
        'StyleCategory': test_server_module.StyleCategory,
        'StyleImage': test_server_module.StyleImage,
        'Product': test_server_module.Product,
        'ProductSize': test_server_module.ProductSize,
        'ProductImage': test_server_module.ProductImage,
        'ProductSizePetOption': test_server_module.ProductSizePetOption,
        'ProductStyleCategory': test_server_module.ProductStyleCategory,
        'ProductCustomField': test_server_module.ProductCustomField,
        'HomepageBanner': test_server_module.HomepageBanner,
        'WorksGallery': test_server_module.WorksGallery,
        'HomepageConfig': test_server_module.HomepageConfig,
        'AIConfig': test_server_module.AIConfig,
        'ShopProduct': getattr(test_server_module, 'ShopProduct', None),
        'ShopProductSize': getattr(test_server_module, 'ShopProductSize', None),
        'ShopOrder': getattr(test_server_module, 'ShopOrder', None),
        'PrintSizeConfig': getattr(test_server_module, 'PrintSizeConfig', None),
        'SelfieMachine': getattr(test_server_module, 'SelfieMachine', None),
        'StaffUser': getattr(test_server_module, 'StaffUser', None),
    }


@admin_bp.route('/admin/styles')
@login_required
def admin_styles():
    """风格分类管理页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    return render_template('admin/styles.html')


@admin_bp.route('/admin/homepage')
@login_required
def admin_homepage():
    """首页配置管理页面"""
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/homepage.html')


# ⭐ 作品展示和预约拍照功能已删除
# @admin_bp.route('/admin/works-gallery')
# @admin_bp.route('/admin/photo-signups')


@admin_bp.route('/admin/system-config')
@login_required
def admin_system_config():
    """系统配置管理页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    return render_template('admin/system_config.html')


@admin_bp.route('/admin')
@login_required
def admin_index():
    """管理后台首页 - 重定向到仪表盘"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """管理后台仪表盘大屏"""
    if current_user.role not in ['admin', 'operator']:
        # 如果是商家，跳转到商家控制台
        if current_user.is_authenticated and current_user.role == 'merchant':
            # merchant_dashboard 还在 test_server.py 中，暂时使用完整路径
            return redirect('/merchant/dashboard')
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    db = models['db']
    Order = models['Order']
    User = models['User']
    FranchiseeAccount = models['FranchiseeAccount']
    AITask = models.get('AITask')
    MeituAPICallLog = models.get('MeituAPICallLog')
    
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)
    
    # 订单统计
    total_orders = Order.query.filter(Order.status != 'unpaid').count()
    daily_orders = Order.query.filter(
        func.date(Order.created_at) == today,
        Order.status != 'unpaid'
    ).count()
    yesterday_orders = Order.query.filter(
        func.date(Order.created_at) == yesterday,
        Order.status != 'unpaid'
    ).count()
    week_orders = Order.query.filter(
        func.date(Order.created_at) >= this_week_start,
        Order.status != 'unpaid'
    ).count()
    month_orders = Order.query.filter(
        func.date(Order.created_at) >= this_month_start,
        Order.status != 'unpaid'
    ).count()
    
    # 业绩统计
    daily_revenue = Order.query.filter(
        func.date(Order.completed_at) == today,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    yesterday_revenue = Order.query.filter(
        func.date(Order.completed_at) == yesterday,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    week_revenue = Order.query.filter(
        func.date(Order.completed_at) >= this_week_start,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    month_revenue = Order.query.filter(
        func.date(Order.completed_at) >= this_month_start,
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    total_revenue = Order.query.filter(
        Order.status == 'completed'
    ).with_entities(func.sum(Order.price)).scalar() or 0.0
    
    # 订单状态统计
    pending_orders = Order.query.filter(Order.status.in_(['pending', '已支付'])).count()
    processing_orders = Order.query.filter(Order.status == 'processing').count()
    completed_orders = Order.query.filter(Order.status == 'completed').count()
    # 异常订单：状态为failed或error，或者有printer错误信息的订单
    from sqlalchemy import or_
    error_orders = Order.query.filter(
        or_(
            Order.status.in_(['failed', 'error']),
            Order.printer_error_message.isnot(None)
        )
    ).count()
    
    # AI任务统计
    ai_task_stats = {}
    if AITask:
        ai_task_stats['total'] = AITask.query.count()
        ai_task_stats['processing'] = AITask.query.filter(AITask.status == 'processing').count()
        ai_task_stats['completed'] = AITask.query.filter(AITask.status == 'completed').count()
        ai_task_stats['failed'] = AITask.query.filter(AITask.status == 'failed').count()
    
    # 美颜任务统计
    meitu_task_stats = {}
    if MeituAPICallLog:
        meitu_task_stats['total'] = MeituAPICallLog.query.count()
        meitu_task_stats['success'] = MeituAPICallLog.query.filter(MeituAPICallLog.status == 'success').count()
        meitu_task_stats['failed'] = MeituAPICallLog.query.filter(MeituAPICallLog.status == 'failed').count()
    
    # 加盟商统计
    total_franchisees = FranchiseeAccount.query.filter_by(status='active').count()
    
    # 用户统计
    total_users = User.query.count()
    
    return render_template('admin/dashboard.html',
                         total_orders=total_orders,
                         daily_orders=daily_orders,
                         yesterday_orders=yesterday_orders,
                         week_orders=week_orders,
                         month_orders=month_orders,
                         daily_revenue=daily_revenue,
                         yesterday_revenue=yesterday_revenue,
                         week_revenue=week_revenue,
                         month_revenue=month_revenue,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders,
                         processing_orders=processing_orders,
                         completed_orders=completed_orders,
                         error_orders=error_orders,
                         ai_task_stats=ai_task_stats,
                         meitu_task_stats=meitu_task_stats,
                         total_franchisees=total_franchisees,
                         total_users=total_users)


@admin_bp.route('/api/admin/system-config', methods=['GET'])
@login_required
def api_get_system_config():
    """获取系统配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
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
        
        # 获取服务器URL配置（从server_config或数据库）
        try:
            from server_config import get_base_url, get_api_base_url, get_media_url, get_static_url
            configs['server_base_url'] = get_base_url()
            configs['server_api_url'] = get_api_base_url()
            configs['server_media_url'] = get_media_url()
            configs['server_static_url'] = get_static_url()
        except:
            # 如果server_config不可用，从数据库获取
            for config in ai_configs:
                if config.config_key == 'server_base_url':
                    configs['server_base_url'] = config.config_value
                elif config.config_key == 'server_api_url':
                    configs['server_api_url'] = config.config_value
                elif config.config_key == 'server_media_url':
                    configs['server_media_url'] = config.config_value
                elif config.config_key == 'server_static_url':
                    configs['server_static_url'] = config.config_value
        
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
        
        # 如果没有配置品牌名称，使用默认值
        if 'brand_name' not in configs:
            configs['brand_name'] = 'AI拍照机'
        
        return jsonify({
            'status': 'success',
            'data': configs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/system-config/comfyui', methods=['POST'])
@login_required
def api_save_comfyui_config():
    """保存ComfyUI配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
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


@admin_bp.route('/api/admin/system-config/server-url', methods=['POST'])
@login_required
def api_save_server_url_config():
    """保存服务器URL配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
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


@admin_bp.route('/api/admin/system-config/brand-name', methods=['POST'])
@login_required
def api_save_brand_name_config():
    """保存品牌名称配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
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


@admin_bp.route('/api/admin/system-config/concurrency', methods=['POST'])
@login_required
def api_save_concurrency_config():
    """保存并发和队列配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
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


@admin_bp.route('/api/admin/system-config/image-paths', methods=['POST'])
@login_required
def api_save_image_paths_config():
    """保存图片路径配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
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


@admin_bp.route('/api/admin/orders/latest', methods=['GET'])
@login_required
def api_get_latest_orders():
    """获取最新订单列表（用于浏览器通知）"""
    try:
        models = get_models()
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

# ============================================================================
# 管理后台页面路由
# ============================================================================

@admin_bp.route('/admin/promotion')
@login_required
def admin_promotion_management():
    """后台分佣管理页面（提现功能已删除，但基础管理功能保留）"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    return render_template('admin/promotion_management.html')

@admin_bp.route('/admin/coupons')
@login_required
def admin_coupons_management():
    """后台优惠券管理页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    return render_template('admin/coupons.html')

@admin_bp.route('/admin/users')
@login_required
def admin_all_users():
    """所有用户访问统计页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    return render_template('admin/all_users.html')


@admin_bp.route('/admin/print-config')
@login_required
def admin_print_config():
    """打印配置页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    models = get_models()
    if not models:
        flash('系统未初始化', 'error')
        return redirect(url_for('auth.login'))
    
    ShopProduct = models.get('ShopProduct')
    ShopProductSize = models.get('ShopProductSize')
    PrintSizeConfig = models.get('PrintSizeConfig')
    AIConfig = models.get('AIConfig')
    
    # 获取所有商城产品
    products = []
    if ShopProduct:
        products = ShopProduct.query.filter_by(is_active=True).order_by(ShopProduct.sort_order).all()
    
    # 获取所有打印尺寸配置
    print_configs = []
    if PrintSizeConfig:
        print_configs = PrintSizeConfig.query.order_by(PrintSizeConfig.sort_order, PrintSizeConfig.product_id).all()
    
    # 获取打印机地址配置
    printer_configs = {}
    if AIConfig:
        configs = AIConfig.query.filter(AIConfig.config_key.like('printer_%')).all()
        for config in configs:
            printer_configs[config.config_key] = config.config_value
    
    return render_template('admin/print_config.html',
                         products=products,
                         print_configs=print_configs,
                         printer_configs=printer_configs)


@admin_bp.route('/api/admin/payment-config', methods=['GET'])
@login_required
def api_get_payment_config():
    """获取支付配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        AIConfig = models['AIConfig']
        
        # 获取支付配置
        configs = {}
        ai_configs = AIConfig.query.all()
        for config in ai_configs:
            if config.config_key == 'payment_test_mode':
                configs['test_mode'] = config.config_value == 'true'
            elif config.config_key == 'payment_skip_payment':
                configs['skip_payment'] = config.config_value == 'true'
            elif config.config_key == 'payment_qrcode_url':
                configs['qrcode_url'] = config.config_value
        
        # 设置默认值
        if 'test_mode' not in configs:
            configs['test_mode'] = True  # 默认测试模式
        if 'skip_payment' not in configs:
            configs['skip_payment'] = True  # 默认允许跳过支付
        if 'qrcode_url' not in configs:
            configs['qrcode_url'] = None
        
        return jsonify({
            'status': 'success',
            'data': configs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取支付配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/payment-config', methods=['POST'])
@login_required
def api_save_payment_config():
    """保存支付配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('payment_test_mode', str(data.get('test_mode', True)).lower(), '支付测试模式'),
            ('payment_skip_payment', str(data.get('skip_payment', True)).lower(), '允许跳过支付'),
            ('payment_qrcode_url', data.get('qrcode_url', ''), '支付二维码URL'),
        ]
        
        for config_key, config_value, description in configs_to_save:
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = config_value
            else:
                config = AIConfig(config_key=config_key, config_value=config_value)
                db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '支付配置保存成功'
        })
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存支付配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/print-config/printer', methods=['GET'])
@login_required
def api_get_printer_config():
    """获取打印机地址配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        AIConfig = models['AIConfig']
        
        configs = {}
        ai_configs = AIConfig.query.filter(AIConfig.config_key.like('printer_%')).all()
        for config in ai_configs:
            key = config.config_key.replace('printer_', '')
            configs[key] = config.config_value
        
        # 获取本地打印机配置
        local_printer_config = AIConfig.query.filter_by(config_key='local_printer_path').first()
        if local_printer_config:
            configs['local_printer_path'] = local_printer_config.config_value
        else:
            configs['local_printer_path'] = ''
        
        # 获取打印代理服务配置（用于远程部署）
        proxy_url_config = AIConfig.query.filter_by(config_key='local_printer_proxy_url').first()
        if proxy_url_config:
            configs['local_printer_proxy_url'] = proxy_url_config.config_value
        else:
            configs['local_printer_proxy_url'] = ''
        
        proxy_key_config = AIConfig.query.filter_by(config_key='local_printer_proxy_api_key').first()
        if proxy_key_config:
            configs['local_printer_proxy_api_key'] = proxy_key_config.config_value
        else:
            configs['local_printer_proxy_api_key'] = ''
        
        # 设置默认值
        defaults = {
            'api_base_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate',
            'api_url': 'http://xmdmsm.xicp.cn:5995/api/ODSGate/NewOrder',
            'source_app_id': 'ZPG',
            'shop_id': 'CS',
            'shop_name': '测试',
            'auth_token': '',
            'callback_url': '',
            'file_access_base_url': 'http://moeart.cc',
            'use_oss': 'true',
            'oss_bucket_domain': '',
            'timeout': '30',
            'retry_times': '3',
            'enabled': 'true',
            'local_printer_path': '',  # 本地打印机路径，如 \\sm003\HP OfficeJet Pro 7730 series
            'local_printer_proxy_url': '',  # 打印代理服务地址（远程部署时使用）
            'local_printer_proxy_api_key': ''  # 打印代理服务API密钥（可选）
        }
        
        for key, default_value in defaults.items():
            if key not in configs:
                configs[key] = default_value
        
        return jsonify({
            'status': 'success',
            'data': configs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取打印机配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/print-config/printer', methods=['POST'])
@login_required
def api_save_printer_config():
    """保存打印机地址配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        configs_to_save = [
            ('printer_api_base_url', data.get('api_base_url', ''), '冲印系统API基础地址'),
            ('printer_api_url', data.get('api_url', ''), '新订单接口'),
            ('printer_source_app_id', data.get('source_app_id', ''), '订单来源系统代号'),
            ('printer_shop_id', data.get('shop_id', ''), '影楼编号'),
            ('printer_shop_name', data.get('shop_name', ''), '影楼名称'),
            ('printer_auth_token', data.get('auth_token', ''), '认证Token'),
            ('printer_callback_url', data.get('callback_url', ''), '快递信息回调地址'),
            ('printer_file_access_base_url', data.get('file_access_base_url', ''), '外部可访问的文件基础URL'),
            ('printer_use_oss', str(data.get('use_oss', True)).lower(), '是否使用阿里云OSS存储'),
            ('printer_oss_bucket_domain', data.get('oss_bucket_domain', ''), 'OSS存储桶域名'),
            ('printer_timeout', str(data.get('timeout', 30)), '请求超时时间（秒）'),
            ('printer_retry_times', str(data.get('retry_times', 3)), '重试次数'),
            ('printer_enabled', str(data.get('enabled', True)).lower(), '是否启用冲印系统集成'),
            ('local_printer_path', data.get('local_printer_path', ''), '本地打印机路径（用于电子照片打印，本地部署时使用）'),
            ('local_printer_proxy_url', data.get('local_printer_proxy_url', ''), '打印代理服务地址（远程部署时使用，如 http://192.168.1.100:8888）'),
            ('local_printer_proxy_api_key', data.get('local_printer_proxy_api_key', ''), '打印代理服务API密钥（可选，用于安全验证）'),
        ]
        
        for config_key, config_value, description in configs_to_save:
            config = AIConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = config_value
                config.description = description
            else:
                config = AIConfig(config_key=config_key, config_value=config_value, description=description)
                db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '打印机配置保存成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'保存打印机配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/print-config/machines', methods=['GET'])
@login_required
def api_get_machine_printer_configs():
    """获取所有自拍机的打印机配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        from app.utils.printer_config_helper import get_all_machine_printer_configs
        configs = get_all_machine_printer_configs(models)
        
        return jsonify({
            'status': 'success',
            'data': configs
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取门店打印机配置失败: {str(e)}'
        }), 500

@admin_bp.route('/api/admin/print-config/machines', methods=['POST'])
@login_required
def api_save_machine_printer_config():
    """保存指定自拍机的打印机配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        data = request.get_json()
        machine_id = data.get('machine_id')
        
        if not machine_id:
            return jsonify({'status': 'error', 'message': '自拍机ID不能为空'}), 400
        
        from app.utils.printer_config_helper import save_printer_config_for_machine
        success = save_printer_config_for_machine(
            machine_id=machine_id,
            printer_path=data.get('local_printer_path', ''),
            proxy_url=data.get('local_printer_proxy_url', ''),
            api_key=data.get('local_printer_proxy_api_key', ''),
            models=models
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'自拍机 {machine_id} 的打印机配置保存成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存失败'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'保存门店打印机配置失败: {str(e)}'
        }), 500

@admin_bp.route('/api/admin/print-config/test-print', methods=['POST'])
@login_required
def api_test_print():
    """测试打印（上传文件）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        AIConfig = models['AIConfig']
        
        # 检查是否上传了文件
        if 'file' not in request.files:
            print("❌ 错误: 请求中没有file字段")
            print(f"请求文件: {list(request.files.keys())}")
            return jsonify({'status': 'error', 'message': '请选择要打印的文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("❌ 错误: 文件名为空")
            return jsonify({'status': 'error', 'message': '请选择要打印的文件'}), 400
        
        print(f"✅ 收到文件: {file.filename}, 类型: {file.content_type}")
        
        # 获取打印份数
        try:
            copies = int(request.form.get('copies', 1))
            if copies < 1:
                copies = 1
            if copies > 10:
                copies = 10
        except (ValueError, TypeError):
            copies = 1
        
        print(f"打印份数: {copies}")
        
        # 获取打印配置
        local_printer_path = None
        local_printer_proxy_url = None
        local_printer_proxy_api_key = None
        
        local_printer_config = AIConfig.query.filter_by(config_key='local_printer_path').first()
        if local_printer_config:
            local_printer_path = local_printer_config.config_value
        
        proxy_url_config = AIConfig.query.filter_by(config_key='local_printer_proxy_url').first()
        if proxy_url_config:
            local_printer_proxy_url = proxy_url_config.config_value
        
        proxy_key_config = AIConfig.query.filter_by(config_key='local_printer_proxy_api_key').first()
        if proxy_key_config:
            local_printer_proxy_api_key = proxy_key_config.config_value
        
        # 保存上传的文件到临时目录
        import tempfile
        import os
        from werkzeug.utils import secure_filename
        
        # 获取文件扩展名
        filename = secure_filename(file.filename)
        if not filename:
            filename = file.filename  # 如果secure_filename返回空，使用原始文件名
        
        file_ext = os.path.splitext(filename)[1].lower()
        
        # 如果没有扩展名，尝试从content_type推断
        if not file_ext and file.content_type:
            content_type_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/bmp': '.bmp',
                'application/pdf': '.pdf',
                'application/msword': '.doc',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                'text/plain': '.txt'
            }
            file_ext = content_type_map.get(file.content_type, '')
        
        print(f"文件扩展名: {file_ext}")
        
        # 支持的格式
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.doc', '.docx', '.txt']
        if file_ext and file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'message': f'不支持的文件格式 "{file_ext}"。支持格式：{", ".join(allowed_extensions)}'
            }), 400
        
        # 如果没有扩展名，默认使用.txt
        if not file_ext:
            file_ext = '.txt'
            print(f"⚠️ 未检测到文件扩展名，默认使用: {file_ext}")
        
        # 保存临时文件
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            file.save(temp_file.name)
            temp_file.close()
            print(f"✅ 临时文件已保存: {temp_file.name}")
        except Exception as e:
            print(f"❌ 保存临时文件失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'保存文件失败: {str(e)}'
            }), 500
        
        try:
            # 判断使用哪种打印方式
            if local_printer_proxy_url:
                # 使用打印代理服务（远程部署）
                try:
                    from local_printer_client import LocalPrinterClient
                    import requests
                    import base64
                    
                    # 读取文件内容并转换为Base64
                    with open(temp_file.name, 'rb') as f:
                        file_content = f.read()
                        file_data_base64 = base64.b64encode(file_content).decode('utf-8')
                    
                    print(f"✅ 文件已读取: {len(file_content)} 字节, 扩展名: {file_ext}")
                    
                    client = LocalPrinterClient(local_printer_proxy_url, local_printer_proxy_api_key)
                    
                    # 发送文件数据到打印代理服务，同时传递文件扩展名
                    result = client.print_image(
                        image_data=file_data_base64,
                        file_ext=file_ext,  # 传递文件扩展名
                        copies=copies
                    )
                    
                    if result.get('success'):
                        return jsonify({
                            'status': 'success',
                            'message': f'测试打印成功！文件"{filename}"已发送到打印机',
                            'data': result
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': f'打印失败: {result.get("message", "未知错误")}'
                        }), 400
                        
                except ImportError:
                    return jsonify({
                        'status': 'error',
                        'message': '打印代理客户端模块未找到'
                    }), 500
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'打印失败: {str(e)}'
                    }), 500
            elif local_printer_path:
                # 直接使用本地打印机（本地部署）
                try:
                    from local_printer import LocalPrinter
                    
                    local_printer = LocalPrinter(local_printer_path)
                    
                    # 打印文件
                    result = local_printer.print_image(temp_file.name, copies=copies)
                    
                    if result.get('success'):
                        return jsonify({
                            'status': 'success',
                            'message': f'测试打印成功！文件"{filename}"已发送到打印机',
                            'data': result
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': f'打印失败: {result.get("message", "未知错误")}'
                        }), 400
                        
                except ImportError as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'缺少必要的库: {str(e)}。请安装: pip install pywin32 Pillow'
                    }), 500
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'打印失败: {str(e)}'
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': '未配置本地打印机或打印代理服务'
                }), 400
        finally:
            # 清理临时文件
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file.name)
                    print(f"✅ 已清理临时文件: {temp_file.name}")
                except Exception as e:
                    print(f"⚠️ 清理临时文件失败: {str(e)}")
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ 测试打印异常: {str(e)}")
        print(error_trace)
        return jsonify({
            'status': 'error',
            'message': f'测试打印失败: {str(e)}'
        }), 500
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存打印机配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/print-config/size', methods=['GET'])
@login_required
def api_get_print_size_configs():
    """获取打印尺寸配置列表"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        PrintSizeConfig = models.get('PrintSizeConfig')
        ShopProduct = models.get('ShopProduct')
        ShopProductSize = models.get('ShopProductSize')
        
        if not PrintSizeConfig:
            return jsonify({'status': 'error', 'message': '打印配置模型未找到'}), 500
        
        configs = PrintSizeConfig.query.order_by(PrintSizeConfig.sort_order, PrintSizeConfig.product_id).all()
        
        result = []
        for config in configs:
            config_data = {
                'id': config.id,
                'product_id': config.product_id,
                'product': config.product,
                'size_id': config.size_id,
                'size_name': config.size_name,
                'print_width_cm': config.print_width_cm,
                'print_height_cm': config.print_height_cm,
                'crop_x': config.crop_x,
                'crop_y': config.crop_y,
                'crop_width': config.crop_width,
                'crop_height': config.crop_height,
                'crop_mode': config.crop_mode,
                'template_name': config.template_name,
                'dpi': config.dpi,
                'color_mode': config.color_mode,
                'printer_product_id': config.printer_product_id,
                'printer_product_name': config.printer_product_name,
                'is_active': config.is_active,
                'sort_order': config.sort_order,
                'notes': config.notes
            }
            result.append(config_data)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取打印尺寸配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/print-config/size', methods=['POST'])
@login_required
def api_save_print_size_config():
    """保存打印尺寸配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        PrintSizeConfig = models.get('PrintSizeConfig')
        ShopProduct = models.get('ShopProduct')
        ShopProductSize = models.get('ShopProductSize')
        
        if not PrintSizeConfig:
            return jsonify({'status': 'error', 'message': '打印配置模型未找到'}), 500
        
        data = request.get_json()
        config_id = data.get('id')
        
        if config_id:
            # 更新现有配置
            config = PrintSizeConfig.query.get(config_id)
            if not config:
                return jsonify({'status': 'error', 'message': '配置不存在'}), 404
        else:
            # 创建新配置
            config = PrintSizeConfig()
        
        # 更新字段
        config.product_id = data.get('product_id') if data.get('product_id') else None
        config.size_id = data.get('size_id') if data.get('size_id') else None
        config.print_width_cm = float(data.get('print_width_cm', 0))
        config.print_height_cm = float(data.get('print_height_cm', 0))
        config.crop_x = float(data.get('crop_x', 0))
        config.crop_y = float(data.get('crop_y', 0))
        config.crop_width = float(data.get('crop_width')) if data.get('crop_width') else None
        config.crop_height = float(data.get('crop_height')) if data.get('crop_height') else None
        config.crop_mode = data.get('crop_mode', 'center')
        config.template_name = data.get('template_name', '')
        config.dpi = int(data.get('dpi', 300))
        config.color_mode = data.get('color_mode', 'RGB')
        config.printer_product_id = data.get('printer_product_id', '')
        config.printer_product_name = data.get('printer_product_name', '')
        config.is_active = data.get('is_active', True)
        config.sort_order = int(data.get('sort_order', 0))
        config.notes = data.get('notes', '')
        
        # 更新产品名称和规格名称
        if config.product_id and ShopProduct:
            product = ShopProduct.query.get(config.product_id)
            if product:
                config.product = product.name
        
        if config.size_id and ShopProductSize:
            size = ShopProductSize.query.get(config.size_id)
            if size:
                config.size_name = size.size_name
        
        if not config_id:
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '打印尺寸配置保存成功',
            'data': {'id': config.id}
        })
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存打印尺寸配置失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/print-config/size/<int:config_id>', methods=['DELETE'])
@login_required
def api_delete_print_size_config(config_id):
    """删除打印尺寸配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        PrintSizeConfig = models.get('PrintSizeConfig')
        
        if not PrintSizeConfig:
            return jsonify({'status': 'error', 'message': '打印配置模型未找到'}), 500
        
        config = PrintSizeConfig.query.get(config_id)
        if not config:
            return jsonify({'status': 'error', 'message': '配置不存在'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '打印尺寸配置删除成功'
        })
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除打印尺寸配置失败: {str(e)}'
        }), 500


@admin_bp.route('/admin/printer')
@login_required
def admin_printer():
    """打印机管理页面"""
    if current_user.role not in ['admin', 'operator']:
        return redirect(url_for('auth.login'))
    
    return render_template('admin/printer.html')


@admin_bp.route('/api/admin/printer/orders', methods=['GET'])
@login_required
def api_get_printer_orders():
    """获取打印任务列表"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        Order = models['Order']
        ShopOrder = models.get('ShopOrder')
        
        # 获取查询参数
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 查询商城订单（打印任务）
        query = None
        if ShopOrder:
            query = ShopOrder.query
            
            if status_filter:
                if status_filter == 'not_sent':
                    query = query.filter(ShopOrder.printer_send_status == 'not_sent')
                elif status_filter == 'sending':
                    query = query.filter(ShopOrder.printer_send_status == 'sending')
                elif status_filter == 'sent_success':
                    query = query.filter(ShopOrder.printer_send_status == 'sent_success')
                elif status_filter == 'sent_failed':
                    query = query.filter(ShopOrder.printer_send_status == 'sent_failed')
            
            query = query.order_by(ShopOrder.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            orders = []
            for shop_order in pagination.items:
                order_data = {
                    'id': shop_order.id,
                    'order_number': shop_order.order_number,
                    'customer_name': shop_order.customer_name,
                    'customer_phone': shop_order.customer_phone,
                    'product_name': shop_order.product_name or '',
                    'size_name': shop_order.size_name or '',
                    'quantity': shop_order.quantity,
                    'price': float(shop_order.price),
                    'status': shop_order.status,
                    'printer_send_status': shop_order.printer_send_status or 'not_sent',
                    'printer_send_time': shop_order.printer_send_time.isoformat() if shop_order.printer_send_time else None,
                    'printer_error_message': shop_order.printer_error_message,
                    'image_url': shop_order.image_url,
                    'created_at': shop_order.created_at.isoformat() if shop_order.created_at else None
                }
                orders.append(order_data)
            
            return jsonify({
                'status': 'success',
                'data': orders,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            })
        else:
            # 如果没有ShopOrder模型，查询Order表
            query = Order.query
            
            if status_filter:
                if status_filter == 'not_sent':
                    query = query.filter((Order.printer_send_status == None) | (Order.printer_send_status == 'not_sent'))
                elif status_filter == 'sending':
                    query = query.filter(Order.printer_send_status == 'sending')
                elif status_filter == 'sent_success':
                    query = query.filter(Order.printer_send_status == 'sent_success')
                elif status_filter == 'sent_failed':
                    query = query.filter(Order.printer_send_status == 'sent_failed')
            
            query = query.order_by(Order.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            orders = []
            for order in pagination.items:
                order_data = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'customer_phone': order.customer_phone,
                    'product_name': order.product_name or '',
                    'size_name': order.size or '',
                    'quantity': 1,
                    'price': float(order.price or 0),
                    'status': order.status,
                    'printer_send_status': order.printer_send_status or 'not_sent',
                    'printer_send_time': order.printer_send_time.isoformat() if order.printer_send_time else None,
                    'printer_error_message': order.printer_error_message,
                    'image_url': order.hd_image or order.final_image,
                    'created_at': order.created_at.isoformat() if order.created_at else None
                }
                orders.append(order_data)
            
            return jsonify({
                'status': 'success',
                'data': orders,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取打印任务列表失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/printer/resend/<int:order_id>', methods=['POST'])
@login_required
def api_resend_printer_order(order_id):
    """重新发送打印任务"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        ShopOrder = models.get('ShopOrder')
        Order = models['Order']
        
        # 尝试从ShopOrder查找
        order = None
        if ShopOrder:
            order = ShopOrder.query.get(order_id)
        
        # 如果找不到，从Order查找
        if not order:
            order = Order.query.get(order_id)
        
        if not order:
            return jsonify({'status': 'error', 'message': '订单不存在'}), 404
        
        # 检查是否启用冲印系统
        try:
            from printer_config import PRINTER_SYSTEM_CONFIG
            from printer_client import PrinterSystemClient
            
            if not PRINTER_SYSTEM_CONFIG.get('enabled', False):
                return jsonify({'status': 'error', 'message': '冲印系统未启用'}), 400
            
            printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        except ImportError:
            return jsonify({'status': 'error', 'message': '冲印系统模块未找到'}), 500
        
        # 获取图片路径
        image_path = None
        if hasattr(order, 'image_url') and order.image_url:
            image_path = order.image_url
        elif hasattr(order, 'hd_image') and order.hd_image:
            image_path = order.hd_image
        elif hasattr(order, 'final_image') and order.final_image:
            image_path = order.final_image
        
        if not image_path:
            return jsonify({'status': 'error', 'message': '订单没有图片'}), 400
        
        # 获取应用实例
        from flask import current_app
        import sys
        import os
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            app = test_server_module.app if hasattr(test_server_module, 'app') else current_app
        else:
            app = current_app
        
        # 获取高清图片文件夹
        hd_folder = app.config.get('HD_FOLDER', os.path.join(app.root_path, 'hd_images'))
        if not os.path.isabs(hd_folder):
            hd_folder = os.path.join(app.root_path, hd_folder)
        
        # 构建完整路径
        full_image_path = os.path.join(hd_folder, image_path)
        if not os.path.exists(full_image_path):
            # 尝试其他路径
            possible_paths = [
                full_image_path,
                os.path.join('hd_images', image_path),
                os.path.join('uploads', image_path),
                os.path.join('final_works', image_path),
            ]
            found = False
            for path in possible_paths:
                if os.path.exists(path):
                    full_image_path = path
                    found = True
                    break
            
            if not found:
                return jsonify({'status': 'error', 'message': f'图片文件不存在: {image_path}'}), 400
        
        # 发送到冲印系统
        result = printer_client.send_order_to_printer(order, full_image_path, order_obj=order)
        
        db.session.commit()
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': '打印任务已重新发送'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'发送失败: {result.get("message", "未知错误")}'
            })
            
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'重新发送失败: {str(e)}'
        }), 500
