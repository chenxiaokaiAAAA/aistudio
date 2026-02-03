# -*- coding: utf-8 -*-
"""
管理后台小程序配置API路由模块
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import sys

# 创建蓝图
admin_miniprogram_config_api_bp = Blueprint('admin_miniprogram_config_api', __name__, url_prefix='/api/admin/miniprogram-config')

def get_models():
    """延迟导入数据库模型，避免循环导入"""
    try:
        test_server = sys.modules.get('test_server')
        if test_server:
            return {
                'AIConfig': test_server.AIConfig,
                'db': test_server.db
            }
        return None
    except Exception as e:
        print(f"⚠️ 获取数据库模型失败: {e}")
        return None

@admin_miniprogram_config_api_bp.route('', methods=['GET'])
@login_required
def get_miniprogram_config():
    """获取小程序配置（优先从数据库读取，如果数据库没有则使用test_server.py中的默认配置）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        AIConfig = models['AIConfig']
        
        # 先尝试从test_server.py获取默认配置
        default_config = {}
        try:
            test_server = sys.modules.get('test_server')
            if test_server and hasattr(test_server, 'WECHAT_PAY_CONFIG'):
                wechat_pay_config = test_server.WECHAT_PAY_CONFIG
                default_config = {
                    'appid': wechat_pay_config.get('appid', ''),
                    'app_secret': wechat_pay_config.get('app_secret', ''),
                    'pay_appid': wechat_pay_config.get('appid', ''),  # 支付AppID通常与小程序AppID相同
                    'pay_mch_id': wechat_pay_config.get('mch_id', ''),
                    'pay_api_key': wechat_pay_config.get('api_key', ''),
                    'pay_notify_url': wechat_pay_config.get('notify_url', 'https://photogooo/api/payment/notify')
                }
        except Exception as e:
            print(f"⚠️ 读取test_server.py默认配置失败: {str(e)}")
        
        # 从数据库获取配置
        configs = {}
        ai_configs = AIConfig.query.filter(
            AIConfig.config_key.in_([
                'miniprogram_appid',
                'miniprogram_app_secret',
                'wechat_pay_appid',
                'wechat_pay_mch_id',
                'wechat_pay_api_key',
                'wechat_pay_notify_url'
            ])
        ).all()
        
        for config in ai_configs:
            key = config.config_key.replace('miniprogram_', '').replace('wechat_pay_', '')
            # 如果数据库有值，使用数据库的值；否则使用默认值
            if config.config_value:
                configs[key] = config.config_value
        
        # 合并配置：数据库配置优先，如果没有则使用默认配置
        result = {}
        for key in ['appid', 'app_secret', 'pay_appid', 'pay_mch_id', 'pay_api_key', 'pay_notify_url']:
            if key in configs and configs[key]:
                result[key] = configs[key]
            elif key in default_config:
                result[key] = default_config[key]
            else:
                # 如果都没有，使用空字符串
                result[key] = ''
        
        # 如果pay_appid为空，使用appid的值
        if not result.get('pay_appid') and result.get('appid'):
            result['pay_appid'] = result['appid']
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取小程序配置失败: {str(e)}'
        }), 500

@admin_miniprogram_config_api_bp.route('', methods=['POST'])
@login_required
def save_miniprogram_config():
    """保存小程序配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '系统未初始化'}), 500
        
        db = models['db']
        AIConfig = models['AIConfig']
        
        data = request.get_json()
        
        # 配置项映射：前端字段名 -> 数据库config_key
        configs_to_save = [
            ('miniprogram_appid', data.get('appid', ''), '小程序AppID'),
            ('miniprogram_app_secret', data.get('app_secret', ''), '小程序AppSecret'),
            ('wechat_pay_appid', data.get('pay_appid', ''), '微信支付AppID'),
            ('wechat_pay_mch_id', data.get('pay_mch_id', ''), '微信支付商户号'),
            ('wechat_pay_api_key', data.get('pay_api_key', ''), '微信支付API密钥'),
            ('wechat_pay_notify_url', data.get('pay_notify_url', ''), '微信支付回调地址'),
        ]
        
        for config_key, config_value, description in configs_to_save:
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
        
        db.session.commit()
        
        print(f"✅ 小程序配置已更新")
        
        return jsonify({
            'status': 'success',
            'message': '小程序配置保存成功（需要重启服务才能生效）'
        })
    except Exception as e:
        if 'db' in locals():
            db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500
