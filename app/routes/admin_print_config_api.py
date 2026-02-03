# -*- coding: utf-8 -*-
"""
管理后台打印配置API路由模块
提供打印配置的获取和保存功能
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.utils.admin_helpers import get_models
from app.utils.decorators import admin_api_required

# 创建蓝图
admin_print_config_api_bp = Blueprint('admin_print_config_api', __name__)

@admin_print_config_api_bp.route('/api/admin/payment-config', methods=['GET'])
@login_required
@admin_api_required
def api_get_payment_config():
    """获取支付配置"""
    try:
        models = get_models(['AIConfig'])
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

@admin_print_config_api_bp.route('/api/admin/payment-config', methods=['POST'])
@login_required
@admin_api_required
def api_save_payment_config():
    """保存支付配置"""
    try:
        models = get_models(['AIConfig', 'db'])
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

@admin_print_config_api_bp.route('/api/admin/print-config/printer', methods=['GET'])
@login_required
@admin_api_required
def api_get_printer_config():
    """获取打印机地址配置"""
    try:
        models = get_models(['AIConfig'])
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
            'file_access_base_url': 'http://photogooo',
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

@admin_print_config_api_bp.route('/api/admin/print-config/printer', methods=['POST'])
@login_required
@admin_api_required
def api_save_printer_config():
    """保存打印机地址配置"""
    try:
        models = get_models(['AIConfig', 'db'])
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
                if hasattr(config, 'description'):
                    config.description = description
            else:
                config = AIConfig(config_key=config_key, config_value=config_value)
                if hasattr(config, 'description'):
                    config.description = description
                db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '打印机配置保存成功'
        })
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存打印机配置失败: {str(e)}'
        }), 500

@admin_print_config_api_bp.route('/api/admin/print-config/machines', methods=['GET'])
@login_required
@admin_api_required
def api_get_machine_printer_configs():
    """获取所有自拍机的打印机配置"""
    try:
        models = get_models(['AIConfig'])
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

@admin_print_config_api_bp.route('/api/admin/print-config/machines', methods=['POST'])
@login_required
@admin_api_required
def api_save_machine_printer_config():
    """保存指定自拍机的打印机配置"""
    try:
        models = get_models(['AIConfig', 'db'])
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

@admin_print_config_api_bp.route('/api/admin/print-config/test-print', methods=['POST'])
@login_required
@admin_api_required
def api_test_print():
    """测试打印（上传文件）"""
    try:
        models = get_models(['AIConfig'])
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

@admin_print_config_api_bp.route('/api/admin/print-config/size', methods=['GET'])
@login_required
@admin_api_required
def api_get_print_size_configs():
    """获取打印尺寸配置列表"""
    try:
        models = get_models(['PrintSizeConfig', 'ShopProduct', 'ShopProductSize'])
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
                'product': config.product if hasattr(config, 'product') else None,
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
                'notes': config.notes if hasattr(config, 'notes') else None
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

@admin_print_config_api_bp.route('/api/admin/print-config/size', methods=['POST'])
@login_required
@admin_api_required
def api_save_print_size_config():
    """保存打印尺寸配置"""
    try:
        models = get_models(['PrintSizeConfig', 'ShopProduct', 'ShopProductSize', 'db'])
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
        if hasattr(config, 'notes'):
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

@admin_print_config_api_bp.route('/api/admin/print-config/size/<int:config_id>', methods=['DELETE'])
@login_required
@admin_api_required
def api_delete_print_size_config(config_id):
    """删除打印尺寸配置"""
    try:
        models = get_models(['PrintSizeConfig', 'db'])
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

@admin_print_config_api_bp.route('/api/admin/printer/orders', methods=['GET'])
@login_required
@admin_api_required
def api_get_printer_orders():
    """获取打印任务列表"""
    try:
        models = get_models(['Order', 'ShopOrder'])
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

@admin_print_config_api_bp.route('/api/admin/printer/resend/<int:order_id>', methods=['POST'])
@login_required
@admin_api_required
def api_resend_printer_order(order_id):
    """重新发送打印任务"""
    try:
        models = get_models(['Order', 'ShopOrder', 'db'])
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
