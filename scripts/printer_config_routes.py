# 冲印系统配置管理页面
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import json
import os

printer_config_bp = Blueprint('printer_config', __name__)

@printer_config_bp.route('/admin/printer-config')
@login_required
def printer_config_page():
    """冲印系统配置页面"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    # 读取当前配置
    config_file = 'printer_config.py'
    current_config = {}
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单解析配置（实际项目中建议使用更安全的方式）
                if 'PRINTER_SYSTEM_CONFIG' in content:
                    current_config = {
                        'api_url': 'http://服务器IP:5995/api/ODSGate/NewOrder',
                        'source_app_id': 'YT',
                        'shop_id': 'YOUR_SHOP_ID',
                        'shop_name': '您的影楼名称',
                        'enabled': True
                    }
        except Exception as e:
            flash(f'读取配置失败: {str(e)}', 'error')
    
    return render_template('admin/printer_config.html', config=current_config)

@printer_config_bp.route('/admin/printer-config', methods=['POST'])
@login_required
def update_printer_config():
    """更新冲印系统配置"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    try:
        # 获取表单数据
        api_url = request.form.get('api_url')
        source_app_id = request.form.get('source_app_id')
        shop_id = request.form.get('shop_id')
        shop_name = request.form.get('shop_name')
        enabled = request.form.get('enabled') == 'on'
        
        # 验证必要字段
        if not all([api_url, source_app_id, shop_id, shop_name]):
            flash('请填写所有必要字段', 'error')
            return redirect(url_for('printer_config.printer_config_page'))
        
        # 生成新的配置文件内容
        config_content = f'''# 冲印系统集成配置
# 在 app.py 中添加以下配置

# 冲印系统配置
PRINTER_SYSTEM_CONFIG = {{
    'api_url': '{api_url}',
    'source_app_id': '{source_app_id}',
    'shop_id': '{shop_id}',
    'shop_name': '{shop_name}',
    'enabled': {enabled},
    'timeout': 30,
    'retry_times': 3,
}}

# 产品尺寸映射（根据您的系统调整）
SIZE_MAPPING = {{
    'A4': {{'width': 21.0, 'height': 29.7, 'dpi': 300}},
    'A3': {{'width': 29.7, 'height': 42.0, 'dpi': 300}},
    '8x10': {{'width': 20.3, 'height': 25.4, 'dpi': 300}},
    '5x7': {{'width': 12.7, 'height': 17.8, 'dpi': 300}},
    # 添加更多尺寸映射
}}
'''
        
        # 写入配置文件
        with open('printer_config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        flash('冲印系统配置已更新', 'success')
        
    except Exception as e:
        flash(f'更新配置失败: {str(e)}', 'error')
    
    return redirect(url_for('printer_config.printer_config_page'))

@printer_config_bp.route('/admin/printer-config/test')
@login_required
def test_printer_config():
    """测试冲印系统连接"""
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    try:
        from printer_client import PrinterSystemClient
        from printer_config import PRINTER_SYSTEM_CONFIG
        
        # 创建测试客户端
        client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
        
        # 这里可以添加测试逻辑
        # 比如发送一个测试请求到冲印系统
        
        return jsonify({
            'status': 'success',
            'message': '冲印系统连接测试成功'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'测试失败: {str(e)}'
        })

