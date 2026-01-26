# -*- coding: utf-8 -*-
"""
API服务商配置管理路由
"""
from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
import json

ai_provider_bp = Blueprint('ai_provider', __name__, url_prefix='/admin/ai-provider')


@ai_provider_bp.route('/config')
@login_required
def api_provider_config():
    """API服务商配置管理页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/api_provider_config.html')


@ai_provider_bp.route('/api/configs', methods=['GET'])
@login_required
def get_api_configs():
    """获取所有API服务商配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APIProviderConfig = test_server_module.APIProviderConfig
        
        # 先检查字段是否存在，如果不存在则先执行迁移
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('api_provider_configs')]
            
            if 'is_sync_api' not in columns:
                print("检测到 is_sync_api 字段不存在，执行数据库迁移...")
                try:
                    db.session.execute(text("ALTER TABLE api_provider_configs ADD COLUMN is_sync_api BOOLEAN DEFAULT 0 NOT NULL"))
                    db.session.commit()
                    print("is_sync_api 字段添加成功")
                    
                    # 根据 api_type 自动设置 is_sync_api 的值
                    db.session.execute(text("UPDATE api_provider_configs SET is_sync_api = 1 WHERE api_type = 'gemini-native'"))
                    db.session.commit()
                    print("已根据 api_type 自动设置 is_sync_api 的值")
                except Exception as e:
                    print(f"添加字段失败: {e}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()
        except Exception as e:
            print(f"检查字段时出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 尝试查询，如果失败则可能是字段问题，尝试修复后重试
        try:
            configs = APIProviderConfig.query.order_by(
                APIProviderConfig.priority.desc(),
                APIProviderConfig.is_default.desc(),
                APIProviderConfig.id
            ).all()
        except Exception as query_error:
            # 如果查询失败，可能是字段不存在，尝试修复
            if 'is_sync_api' in str(query_error):
                print("查询失败，检测到 is_sync_api 字段缺失，尝试修复...")
                try:
                    from sqlalchemy import text
                    db.session.execute(text("ALTER TABLE api_provider_configs ADD COLUMN is_sync_api BOOLEAN DEFAULT 0 NOT NULL"))
                    db.session.commit()
                    db.session.execute(text("UPDATE api_provider_configs SET is_sync_api = 1 WHERE api_type = 'gemini-native'"))
                    db.session.commit()
                    print("字段修复成功，重新查询...")
                    # 重新查询
                    configs = APIProviderConfig.query.order_by(
                        APIProviderConfig.priority.desc(),
                        APIProviderConfig.is_default.desc(),
                        APIProviderConfig.id
                    ).all()
                except Exception as fix_error:
                    print(f"修复失败: {fix_error}")
                    raise query_error
            else:
                raise query_error
        
        return jsonify({
            'status': 'success',
            'data': [config.to_dict() for config in configs]
        })
    
    except Exception as e:
        print(f"获取API配置列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取配置列表失败: {str(e)}'}), 500


@ai_provider_bp.route('/api/configs/<int:config_id>', methods=['GET'])
@login_required
def get_api_config(config_id):
    """获取单个API服务商配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APIProviderConfig = test_server_module.APIProviderConfig
        
        config = APIProviderConfig.query.get(config_id)
        if not config:
            return jsonify({'status': 'error', 'message': '配置不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': config.to_dict()
        })
    
    except Exception as e:
        print(f"获取API配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取配置失败: {str(e)}'}), 500


@ai_provider_bp.route('/api/configs', methods=['POST'])
@login_required
def create_api_config():
    """创建API服务商配置"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据为空'}), 400
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APIProviderConfig = test_server_module.APIProviderConfig
        
        # 如果设置为默认配置，先取消其他默认配置
        if data.get('is_default'):
            existing_default = APIProviderConfig.query.filter_by(is_default=True).first()
            if existing_default:
                existing_default.is_default = False
        
        # 安全处理可能为None的字符串字段
        def safe_strip(value, default=None):
            """安全地处理字符串，如果为None则返回默认值"""
            if value is None:
                return default
            if isinstance(value, str):
                stripped = value.strip()
                return stripped if stripped else default
            return str(value).strip() if str(value).strip() else default
        
        config = APIProviderConfig(
            name=safe_strip(data.get('name'), None) or '',
            api_type=data.get('api_type', 'nano-banana'),
            host_overseas=safe_strip(data.get('host_overseas'), None),
            host_domestic=safe_strip(data.get('host_domestic'), None),
            api_key=safe_strip(data.get('api_key'), None),
            draw_endpoint=data.get('draw_endpoint', '/v1/draw/nano-banana'),
            result_endpoint=data.get('result_endpoint', '/v1/draw/result'),
            file_upload_endpoint=data.get('file_upload_endpoint', '/v1/file/upload'),
            model_name=safe_strip(data.get('model_name'), None),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
            is_sync_api=data.get('is_sync_api', False),
            enable_retry=data.get('enable_retry', True),
            priority=data.get('priority', 0),
            description=safe_strip(data.get('description'), None)
        )
        
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '配置创建成功',
            'data': config.to_dict()
        })
    
    except Exception as e:
        print(f"创建API配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'创建配置失败: {str(e)}'}), 500


@ai_provider_bp.route('/api/configs/<int:config_id>', methods=['PUT'])
@login_required
def update_api_config(config_id):
    """更新API服务商配置"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据为空'}), 400
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APIProviderConfig = test_server_module.APIProviderConfig
        
        config = APIProviderConfig.query.get(config_id)
        if not config:
            return jsonify({'status': 'error', 'message': '配置不存在'}), 404
        
        # 如果设置为默认配置，先取消其他默认配置
        if data.get('is_default') and not config.is_default:
            existing_default = APIProviderConfig.query.filter_by(is_default=True).first()
            if existing_default and existing_default.id != config_id:
                existing_default.is_default = False
        
        # 安全处理可能为None的字符串字段
        def safe_strip(value, default=None):
            """安全地处理字符串，如果为None则返回默认值"""
            if value is None:
                return default
            if isinstance(value, str):
                stripped = value.strip()
                return stripped if stripped else default
            return str(value).strip() if str(value).strip() else default
        
        # 更新字段
        if 'name' in data:
            config.name = safe_strip(data.get('name'), None) or ''
        if 'api_type' in data:
            config.api_type = data['api_type']
        if 'host_overseas' in data:
            config.host_overseas = safe_strip(data.get('host_overseas'), None)
        if 'host_domestic' in data:
            config.host_domestic = safe_strip(data.get('host_domestic'), None)
        if 'api_key' in data:
            config.api_key = safe_strip(data.get('api_key'), None)
        if 'draw_endpoint' in data:
            config.draw_endpoint = data['draw_endpoint']
        if 'result_endpoint' in data:
            config.result_endpoint = data['result_endpoint']
        if 'file_upload_endpoint' in data:
            config.file_upload_endpoint = data['file_upload_endpoint']
        if 'model_name' in data:
            config.model_name = safe_strip(data.get('model_name'), None)
        if 'is_active' in data:
            config.is_active = data['is_active']
        if 'is_default' in data:
            config.is_default = data['is_default']
        if 'is_sync_api' in data:
            config.is_sync_api = data['is_sync_api']
        if 'enable_retry' in data:
            config.enable_retry = data['enable_retry']
        if 'priority' in data:
            config.priority = data['priority']
        if 'description' in data:
            config.description = safe_strip(data.get('description'), None)
        
        config.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '配置更新成功',
            'data': config.to_dict()
        })
    
    except Exception as e:
        print(f"更新API配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'更新配置失败: {str(e)}'}), 500


@ai_provider_bp.route('/api/configs/<int:config_id>', methods=['DELETE'])
@login_required
def delete_api_config(config_id):
    """删除API服务商配置"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APIProviderConfig = test_server_module.APIProviderConfig
        
        config = APIProviderConfig.query.get(config_id)
        if not config:
            return jsonify({'status': 'error', 'message': '配置不存在'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '配置删除成功'
        })
    
    except Exception as e:
        print(f"删除API配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'删除配置失败: {str(e)}'}), 500
