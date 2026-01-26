# -*- coding: utf-8 -*-
"""
美图API配置管理路由
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime

meitu_bp = Blueprint('meitu', __name__, url_prefix='/admin/meitu')


@meitu_bp.route('/config')
@login_required
def meitu_config():
    """美图API配置页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/meitu_api_config.html')


@meitu_bp.route('/tasks')
@login_required
def meitu_tasks():
    """美颜任务管理页面"""
    if current_user.role not in ['admin', 'operator']:
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    return render_template('admin/meitu_tasks.html')


# ============================================================================
# API接口
# ============================================================================

@meitu_bp.route('/api/config', methods=['GET'])
@login_required
def get_meitu_config():
    """获取美图API配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        MeituAPIConfig = test_server_module.MeituAPIConfig
        
        # 优先使用原始SQL查询，避免SQLAlchemy自动访问不存在的列
        config = None
        try:
            # 先检查表结构，判断是否可以直接使用ORM
            result = db.session.execute(
                db.text("PRAGMA table_info(meitu_api_config)")
            ).fetchall()
            columns = {row[1]: row for row in result}
            
            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ['api_key', 'api_secret', 'api_base_url', 'api_endpoint']
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            # 如果查询失败（可能是列不存在），使用原始SQL
            print(f"⚠️ 使用SQLAlchemy查询失败，尝试使用原始SQL: {str(e)}")
            try:
                # 先检查表结构
                result = db.session.execute(
                    db.text("PRAGMA table_info(meitu_api_config)")
                ).fetchall()
                columns = {row[1]: row for row in result}
                
                # 构建SELECT语句，只选择存在的列
                select_cols = []
                if 'api_key' in columns:
                    select_cols.append('api_key')
                elif 'app_id' in columns:
                    select_cols.append('app_id AS api_key')
                else:
                    select_cols.append("'' AS api_key")
                
                if 'api_secret' in columns:
                    select_cols.append('api_secret')
                elif 'secret_id' in columns:
                    select_cols.append('secret_id AS api_secret')
                else:
                    select_cols.append("'' AS api_secret")
                
                # 添加其他可能存在的列
                for col in ['id', 'api_base_url', 'api_endpoint', 'repost_url', 'is_active', 'enable_in_workflow', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                    elif col == 'api_endpoint':
                        select_cols.append("'/openapi/realphotolocal_async' AS api_endpoint")
                    elif col == 'api_base_url':
                        select_cols.append("'https://api.yunxiu.meitu.com' AS api_base_url")
                    elif col == 'is_active':
                        select_cols.append('1 AS is_active')
                    elif col == 'enable_in_workflow':
                        select_cols.append('0 AS enable_in_workflow')
                
                sql = f"SELECT {', '.join(select_cols)} FROM meitu_api_config WHERE is_active = 1 LIMIT 1"
                result = db.session.execute(db.text(sql)).fetchone()
                
                if result:
                    # 手动构建配置对象
                    result_dict = dict(result._mapping) if hasattr(result, '_mapping') else dict(zip([c.split(' AS ')[-1] if ' AS ' in c else c for c in select_cols], result))
                    
                    class SimpleConfig:
                        def __init__(self, data):
                            self.id = data.get('id')
                            self.api_key = data.get('api_key', '')
                            self.api_secret = data.get('api_secret', '')
                            self.api_base_url = data.get('api_base_url', 'https://api.yunxiu.meitu.com')
                            self.api_endpoint = data.get('api_endpoint', '/openapi/realphotolocal_async')
                            self.repost_url = data.get('repost_url')
                            self.is_active = data.get('is_active', True)
                            self.enable_in_workflow = data.get('enable_in_workflow', False)
                            self.created_at = data.get('created_at')
                            self.updated_at = data.get('updated_at')
                        
                        @property
                        def app_id(self):
                            return self.api_key
                        
                        @property
                        def app_key(self):
                            return self.api_key
                        
                        @property
                        def secret_id(self):
                            return self.api_secret
                    
                    config = SimpleConfig(result_dict)
                else:
                    config = None
            except Exception as sql_error:
                print(f"❌ 使用原始SQL查询也失败: {str(sql_error)}")
                config = None
        if not config:
            return jsonify({
                'status': 'success',
                'data': {
                    'app_id': '',
                    'app_key': '',
                    'secret_id': '',
                    'api_base_url': 'https://api.yunxiu.meitu.com',  # 修复：使用正确的官方API地址
                    'is_active': False
                }
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': config.id,
                'app_id': config.app_id or '',
                'app_key': config.app_key or '',
                'secret_id': config.secret_id or '',
                'api_base_url': config.api_base_url or 'https://api.yunxiu.meitu.com',  # 修复：使用正确的官方API地址
                'api_endpoint': config.api_endpoint if hasattr(config, 'api_endpoint') else '/api/v1/image/retouch',
                'is_active': config.is_active,
                'enable_in_workflow': getattr(config, 'enable_in_workflow', False)
            }
        })
    
    except Exception as e:
        print(f"获取美图API配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取配置失败: {str(e)}'}), 500


@meitu_bp.route('/api/config', methods=['POST'])
@login_required
def save_meitu_config():
    """保存美图API配置"""
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
        MeituAPIConfig = test_server_module.MeituAPIConfig
        
        # 查找现有配置（优先使用原始SQL，避免列不存在的问题）
        config = None
        try:
            # 先检查表结构
            result = db.session.execute(
                db.text("PRAGMA table_info(meitu_api_config)")
            ).fetchall()
            columns = {row[1]: row for row in result}
            
            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ['api_key', 'api_secret', 'api_base_url', 'api_endpoint']
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            print(f"⚠️ 查询配置失败，尝试使用原始SQL: {str(e)}")
            # 如果查询失败，使用原始SQL查找
            result = db.session.execute(
                db.text("SELECT id FROM meitu_api_config WHERE is_active = 1 LIMIT 1")
            ).fetchone()
            if result:
                # SQLAlchemy 2.0 的 Row 对象需要用索引访问，或者转换为字典
                if hasattr(result, '_mapping'):
                    config_id = result._mapping['id']
                elif isinstance(result, tuple):
                    config_id = result[0]
                else:
                    config_id = result[0]  # 默认使用索引0
                config = MeituAPIConfig.query.get(config_id)
            else:
                config = None
        
        app_id_value = data.get('app_id', '')
        api_key_value = data.get('api_key', '')
        api_secret_value = data.get('api_secret') or data.get('secret_id', '')
        
        if config:
            # 更新现有配置（使用setattr避免列不存在的问题）
            # 先检查列是否存在，如果不存在则使用原始SQL更新
            try:
                # 尝试使用属性设置（如果列存在）
                if hasattr(config, 'app_id'):
                    config.app_id = app_id_value
                if hasattr(config, 'api_key'):
                    config.api_key = api_key_value
                
                if hasattr(config, 'api_secret'):
                    config.api_secret = api_secret_value
                elif hasattr(config, 'secret_id'):
                    config.secret_id = api_secret_value
                
                config.api_base_url = data.get('api_base_url', 'https://api.yunxiu.meitu.com')
                if hasattr(config, 'api_endpoint'):
                    config.api_endpoint = data.get('api_endpoint', '/openapi/realphotolocal_async')
                if hasattr(config, 'repost_url'):
                    config.repost_url = data.get('repost_url') or None
                config.is_active = data.get('is_active', True)
                if hasattr(config, 'enable_in_workflow'):
                    config.enable_in_workflow = data.get('enable_in_workflow', False)
                if hasattr(config, 'updated_at'):
                    config.updated_at = datetime.now()
            except Exception as update_error:
                # 如果属性设置失败，使用原始SQL更新
                print(f"⚠️ 使用属性更新失败，尝试使用原始SQL: {str(update_error)}")
                # 检查表结构，确定使用哪个字段名
                result = db.session.execute(
                    db.text("PRAGMA table_info(meitu_api_config)")
                ).fetchall()
                columns = {row[1]: row for row in result}
                
                # 构建UPDATE语句
                update_parts = []
                if 'app_id' in columns:
                    update_parts.append(f"app_id = '{app_id_value.replace(chr(39), chr(39)+chr(39))}'")
                if 'api_key' in columns:
                    update_parts.append(f"api_key = '{api_key_value.replace(chr(39), chr(39)+chr(39))}'")
                
                if 'api_secret' in columns:
                    update_parts.append(f"api_secret = '{api_secret_value.replace(chr(39), chr(39)+chr(39))}'")
                elif 'secret_id' in columns:
                    update_parts.append(f"secret_id = '{api_secret_value.replace(chr(39), chr(39)+chr(39))}'")
                
                if 'api_base_url' in columns:
                    update_parts.append(f"api_base_url = '{data.get('api_base_url', 'https://api.yunxiu.meitu.com').replace(chr(39), chr(39)+chr(39))}'")
                if 'api_endpoint' in columns:
                    update_parts.append(f"api_endpoint = '{data.get('api_endpoint', '/openapi/realphotolocal_async').replace(chr(39), chr(39)+chr(39))}'")
                if 'repost_url' in columns:
                    repost_url = data.get('repost_url') or ''
                    if repost_url:
                        update_parts.append(f"repost_url = '{repost_url.replace(chr(39), chr(39)+chr(39))}'")
                    else:
                        update_parts.append("repost_url = NULL")
                if 'is_active' in columns:
                    update_parts.append(f"is_active = {1 if data.get('is_active', True) else 0}")
                if 'enable_in_workflow' in columns:
                    update_parts.append(f"enable_in_workflow = {1 if data.get('enable_in_workflow', False) else 0}")
                if 'updated_at' in columns:
                    update_parts.append(f"updated_at = datetime('now')")
                
                if update_parts:
                    sql = f"UPDATE meitu_api_config SET {', '.join(update_parts)} WHERE id = {config.id}"
                    db.session.execute(db.text(sql))
        else:
            # 创建新配置（使用原始SQL，避免列不存在的问题）
            try:
                # 先检查表结构
                result = db.session.execute(
                    db.text("PRAGMA table_info(meitu_api_config)")
                ).fetchall()
                columns = {row[1]: row for row in result}
                
                # 确定字段名
                key_field = 'api_key' if 'api_key' in columns else ('app_id' if 'app_id' in columns else None)
                secret_field = 'api_secret' if 'api_secret' in columns else ('secret_id' if 'secret_id' in columns else None)
                
                if not key_field or not secret_field:
                    return jsonify({
                        'status': 'error',
                        'message': '数据库表结构不完整，请运行迁移脚本添加 api_key 和 api_secret 字段'
                    }), 500
                
                # 构建INSERT语句
                insert_cols = [key_field, secret_field]
                insert_vals = [f"'{api_key_value.replace(chr(39), chr(39)+chr(39))}'", f"'{api_secret_value.replace(chr(39), chr(39)+chr(39))}'"]
                
                # 如果存在 app_id 字段，添加到INSERT语句
                if 'app_id' in columns:
                    insert_cols.append('app_id')
                    insert_vals.append(f"'{app_id_value.replace(chr(39), chr(39)+chr(39))}'")
                
                if 'api_base_url' in columns:
                    insert_cols.append('api_base_url')
                    insert_vals.append(f"'{data.get('api_base_url', 'https://api.yunxiu.meitu.com').replace(chr(39), chr(39)+chr(39))}'")
                if 'api_endpoint' in columns:
                    insert_cols.append('api_endpoint')
                    insert_vals.append(f"'{data.get('api_endpoint', '/openapi/realphotolocal_async').replace(chr(39), chr(39)+chr(39))}'")
                if 'repost_url' in columns:
                    insert_cols.append('repost_url')
                    repost_url = data.get('repost_url') or ''
                    if repost_url:
                        insert_vals.append(f"'{repost_url.replace(chr(39), chr(39)+chr(39))}'")
                    else:
                        insert_vals.append('NULL')
                if 'is_active' in columns:
                    insert_cols.append('is_active')
                    insert_vals.append(str(1 if data.get('is_active', True) else 0))
                if 'enable_in_workflow' in columns:
                    insert_cols.append('enable_in_workflow')
                    insert_vals.append(str(1 if data.get('enable_in_workflow', False) else 0))
                
                sql = f"INSERT INTO meitu_api_config ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})"
                db.session.execute(db.text(sql))
                db.session.commit()
                
                # 获取新创建的配置ID
                result = db.session.execute(
                    db.text("SELECT id FROM meitu_api_config WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
                ).fetchone()
                # SQLAlchemy 2.0 的 Row 对象需要用索引访问，或者转换为字典
                if hasattr(result, '_mapping'):
                    config_id = result._mapping['id']
                elif isinstance(result, tuple):
                    config_id = result[0]
                else:
                    config_id = result[0]  # 默认使用索引0
                config = MeituAPIConfig.query.get(config_id)
            except Exception as create_error:
                # 如果原始SQL也失败，尝试使用模型创建（可能会失败，但至少尝试一下）
                print(f"⚠️ 使用原始SQL创建失败，尝试使用模型: {str(create_error)}")
                config = MeituAPIConfig(
                    api_key=api_key_value,
                    api_secret=api_secret_value,
                    api_base_url=data.get('api_base_url', 'https://api.yunxiu.meitu.com'),
                    api_endpoint=data.get('api_endpoint', '/openapi/realphotolocal_async'),
                    repost_url=data.get('repost_url') or None,
                    is_active=data.get('is_active', True),
                    enable_in_workflow=data.get('enable_in_workflow', False)
                )
                db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '配置保存成功',
            'data': {
                'id': config.id
            }
        })
    
    except Exception as e:
        print(f"保存美图API配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'保存配置失败: {str(e)}'}), 500


@meitu_bp.route('/api/presets', methods=['GET'])
@login_required
def get_meitu_presets():
    """获取美图API预设列表"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        MeituAPIPreset = test_server_module.MeituAPIPreset
        
        presets = MeituAPIPreset.query.all()
        preset_list = []
        
        for preset in presets:
            if preset.style_category_id:
                # 映射到整个分类
                mapping_type = 'category'
                category_name = preset.style_category.name if preset.style_category else 'N/A'
                image_name = None
            else:
                # 映射到单个图片
                mapping_type = 'image'
                category_name = preset.style_image.category.name if preset.style_image and preset.style_image.category else 'N/A'
                image_name = preset.style_image.name if preset.style_image else 'N/A'
            
            preset_list.append({
                'id': preset.id,
                'style_category_id': preset.style_category_id,
                'style_image_id': preset.style_image_id,
                'mapping_type': mapping_type,
                'category_name': category_name,
                'image_name': image_name,
                'preset_id': preset.preset_id,
                'preset_name': preset.preset_name,
                'description': preset.description,
                'is_active': preset.is_active
            })
        
        return jsonify({
            'status': 'success',
            'data': preset_list
        })
    
    except Exception as e:
        print(f"获取预设列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取预设列表失败: {str(e)}'}), 500


@meitu_bp.route('/api/presets/<int:preset_id>', methods=['GET'])
@login_required
def get_meitu_preset(preset_id):
    """获取单个预设详情"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        MeituAPIPreset = test_server_module.MeituAPIPreset
        
        preset = MeituAPIPreset.query.get(preset_id)
        if not preset:
            return jsonify({'status': 'error', 'message': '预设不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': preset.id,
                'style_category_id': preset.style_category_id,
                'style_image_id': preset.style_image_id,
                'mapping_type': 'category' if preset.style_category_id else 'image',
                'preset_id': preset.preset_id,
                'preset_name': preset.preset_name,
                'description': preset.description,
                'is_active': preset.is_active
            }
        })
    
    except Exception as e:
        print(f"获取预设详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取预设详情失败: {str(e)}'}), 500


@meitu_bp.route('/api/presets', methods=['POST'])
@login_required
def create_meitu_preset():
    """创建美图API预设"""
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
        MeituAPIPreset = test_server_module.MeituAPIPreset
        
        # 验证：必须指定分类或图片之一，但不能同时指定
        style_category_id = data.get('style_category_id')
        style_image_id = data.get('style_image_id')
        
        if not style_category_id and not style_image_id:
            return jsonify({'status': 'error', 'message': '必须指定风格分类或风格图片'}), 400
        
        if style_category_id and style_image_id:
            return jsonify({'status': 'error', 'message': '不能同时指定风格分类和风格图片，请选择其一'}), 400
        
        preset = MeituAPIPreset(
            style_category_id=style_category_id if style_category_id else None,
            style_image_id=style_image_id if style_image_id else None,
            preset_id=data.get('preset_id', ''),
            preset_name=data.get('preset_name', ''),
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(preset)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '预设创建成功',
            'data': {
                'id': preset.id
            }
        })
    
    except Exception as e:
        print(f"创建预设失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'创建预设失败: {str(e)}'}), 500


@meitu_bp.route('/api/presets/<int:preset_id>', methods=['PUT'])
@login_required
def update_meitu_preset(preset_id):
    """更新美图API预设"""
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
        MeituAPIPreset = test_server_module.MeituAPIPreset
        
        preset = MeituAPIPreset.query.get(preset_id)
        if not preset:
            return jsonify({'status': 'error', 'message': '预设不存在'}), 404
        
        # 验证：必须指定分类或图片之一，但不能同时指定
        style_category_id = data.get('style_category_id')
        style_image_id = data.get('style_image_id')
        
        if not style_category_id and not style_image_id:
            return jsonify({'status': 'error', 'message': '必须指定风格分类或风格图片'}), 400
        
        if style_category_id and style_image_id:
            return jsonify({'status': 'error', 'message': '不能同时指定风格分类和风格图片，请选择其一'}), 400
        
        preset.style_category_id = style_category_id if style_category_id else None
        preset.style_image_id = style_image_id if style_image_id else None
        preset.preset_id = data.get('preset_id', preset.preset_id)
        preset.preset_name = data.get('preset_name', preset.preset_name)
        preset.description = data.get('description', preset.description)
        preset.is_active = data.get('is_active', preset.is_active)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '预设更新成功',
            'data': {
                'id': preset.id
            }
        })
    
    except Exception as e:
        print(f"更新预设失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'更新预设失败: {str(e)}'}), 500


@meitu_bp.route('/api/style-categories', methods=['GET'])
@login_required
def get_style_categories():
    """获取风格分类列表（用于预设配置）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        StyleCategory = test_server_module.StyleCategory
        
        categories = StyleCategory.query.filter_by(is_active=True).all()
        category_list = [{'id': cat.id, 'name': cat.name} for cat in categories]
        
        return jsonify({
            'status': 'success',
            'data': category_list
        })
    
    except Exception as e:
        print(f"获取风格分类列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取风格分类列表失败: {str(e)}'}), 500


@meitu_bp.route('/api/style-images', methods=['GET'])
@login_required
def get_style_images():
    """获取风格图片列表（用于预设配置）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        StyleImage = test_server_module.StyleImage
        StyleCategory = test_server_module.StyleCategory
        
        style_images = StyleImage.query.filter_by(is_active=True).all()
        image_list = []
        
        for img in style_images:
            category = StyleCategory.query.get(img.category_id) if img.category_id else None
            image_list.append({
                'id': img.id,
                'name': img.name,
                'category_id': img.category_id,
                'category_name': category.name if category else 'N/A'
            })
        
        return jsonify({
            'status': 'success',
            'data': image_list
        })
    
    except Exception as e:
        print(f"获取风格图片列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取风格图片列表失败: {str(e)}'}), 500


@meitu_bp.route('/api/presets/<int:preset_id>', methods=['DELETE'])
@login_required
def delete_meitu_preset(preset_id):
    """删除美图API预设"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        MeituAPIPreset = test_server_module.MeituAPIPreset
        
        preset = MeituAPIPreset.query.get(preset_id)
        if not preset:
            return jsonify({'status': 'error', 'message': '预设不存在'}), 404
        
        db.session.delete(preset)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '预设删除成功'
        })
    
    except Exception as e:
        print(f"删除预设失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'删除预设失败: {str(e)}'}), 500


# ============================================================================
# 美颜任务管理API
# ============================================================================

@meitu_bp.route('/api/tasks', methods=['GET'])
@login_required
def get_meitu_tasks():
    """获取美颜任务列表（API调用记录）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        MeituAPICallLog = test_server_module.MeituAPICallLog
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        order_number = request.args.get('order_number', '').strip()
        status = request.args.get('status', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # 构建查询
        query = MeituAPICallLog.query
        
        # 筛选条件
        if order_number:
            query = query.filter(MeituAPICallLog.order_number.like(f'%{order_number}%'))
        
        if status:
            query = query.filter(MeituAPICallLog.status == status)
        
        if start_date:
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(MeituAPICallLog.created_at >= start_dt)
            except:
                pass
        
        if end_date:
            try:
                from datetime import datetime, timedelta
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(MeituAPICallLog.created_at < end_dt)
            except:
                pass
        
        # 排序：最新的在前
        query = query.order_by(MeituAPICallLog.created_at.desc())
        
        # 尝试使用ORM查询，如果失败（字段不存在），则使用原始SQL
        try:
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            tasks = pagination.items
        except Exception as orm_error:
            # ORM查询失败，可能是msg_id字段不存在，使用原始SQL查询
            if 'no such column' in str(orm_error).lower() and 'msg_id' in str(orm_error):
                print("⚠️ msg_id 字段不存在，使用兼容查询模式（请重启服务以执行数据库迁移）")
                try:
                    # 使用原始SQL查询，排除msg_id字段
                    offset = (page - 1) * per_page
                    
                    # 构建WHERE子句
                    where_clauses = []
                    params = {'limit': per_page, 'offset': offset}
                    
                    if order_number:
                        where_clauses.append("order_number LIKE :order_number")
                        params['order_number'] = f'%{order_number}%'
                    if status:
                        where_clauses.append("status = :status")
                        params['status'] = status
                    if start_date:
                        try:
                            from datetime import datetime
                            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                            where_clauses.append("DATE(created_at) >= :start_date")
                            params['start_date'] = start_date
                        except:
                            pass
                    if end_date:
                        try:
                            from datetime import datetime, timedelta
                            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                            where_clauses.append("created_at < :end_date")
                            params['end_date'] = end_dt
                        except:
                            pass
                    
                    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
                    
                    # 查询数据
                    sql = f"""
                        SELECT id, order_id, order_number, product_id, preset_id, 
                               request_url, request_params, response_status, response_data,
                               result_image_url, result_image_path, error_message, 
                               duration_ms, status, created_at
                        FROM meitu_api_call_log
                        {where_sql}
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    result = db.session.execute(db.text(sql), params)
                    rows = result.fetchall()
                    
                    # 创建临时任务对象
                    class TempTask:
                        def __init__(self, row):
                            self.id = row[0]
                            self.order_id = row[1]
                            self.order_number = row[2]
                            self.product_id = row[3]
                            self.preset_id = row[4]
                            self.request_url = row[5]
                            self.request_params = row[6]
                            self.response_status = row[7]
                            self.response_data = row[8]
                            self.result_image_url = row[9]
                            self.result_image_path = row[10]
                            self.error_message = row[11]
                            self.duration_ms = row[12]
                            self.status = row[13]
                            self.created_at = row[14]
                            self.msg_id = None  # 临时设置为None
                    
                    tasks = [TempTask(row) for row in rows]
                    
                    # 查询总数
                    count_sql = f"SELECT COUNT(*) FROM meitu_api_call_log {where_sql}"
                    count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
                    count_result = db.session.execute(db.text(count_sql), count_params)
                    total = count_result.fetchone()[0]
                    
                    # 创建分页对象
                    class SimplePagination:
                        def __init__(self, items, total, page, per_page):
                            self.items = items
                            self.total = total
                            self.page = page
                            self.per_page = per_page
                            self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                    
                    pagination = SimplePagination(tasks, total, page, per_page)
                except Exception as sql_error:
                    print(f"❌ 兼容查询模式也失败: {str(sql_error)}")
                    raise orm_error
            else:
                # 其他错误，直接抛出
                raise orm_error
        
        task_list = []
        for task in tasks:
            # 检查任务是否有msg_id（优先从msg_id字段，否则从response_data中提取）
            msg_id_value = getattr(task, 'msg_id', None)
            has_msg_id = bool(msg_id_value)
            
            # 如果msg_id字段为空，尝试从response_data中提取
            if not has_msg_id and task.response_data:
                try:
                    response_data = json.loads(task.response_data) if isinstance(task.response_data, str) else task.response_data
                    if isinstance(response_data, dict):
                        msg_id_value = response_data.get('msg_id')
                        has_msg_id = bool(msg_id_value)
                    elif isinstance(response_data, str):
                        # 如果是字符串，尝试解析
                        try:
                            parsed = json.loads(response_data)
                            msg_id_value = parsed.get('msg_id') if isinstance(parsed, dict) else None
                            has_msg_id = bool(msg_id_value)
                        except:
                            pass
                except:
                    pass
            
            task_list.append({
                'id': task.id,
                'order_id': task.order_id,
                'order_number': task.order_number,
                'product_id': task.product_id,
                'preset_id': task.preset_id,
                'request_url': task.request_url,
                'response_status': task.response_status,
                'result_image_url': task.result_image_url,
                'result_image_path': task.result_image_path,
                'error_message': task.error_message,
                'duration_ms': task.duration_ms,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'request_params': task.request_params,
                'response_data': task.response_data,
                'has_msg_id': has_msg_id  # 标记是否有msg_id，用于前端判断是否显示查询按钮
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'tasks': task_list,
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page
            }
        })
    
    except Exception as e:
        print(f"获取美颜任务列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取任务列表失败: {str(e)}'}), 500


@meitu_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_meitu_task_detail(task_id):
    """获取美颜任务详情"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        MeituAPICallLog = test_server_module.MeituAPICallLog
        Order = test_server_module.Order
        
        task = MeituAPICallLog.query.get(task_id)
        if not task:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404
        
        # 获取订单信息
        order = None
        if task.order_id:
            order = Order.query.get(task.order_id)
        
        # 检查任务是否有msg_id（优先从msg_id字段，否则从response_data中提取）
        msg_id_value = getattr(task, 'msg_id', None)
        has_msg_id = bool(msg_id_value)
        
        # 如果msg_id字段为空，尝试从response_data中提取
        if not has_msg_id and task.response_data:
            try:
                response_data = json.loads(task.response_data) if isinstance(task.response_data, str) else task.response_data
                if isinstance(response_data, dict):
                    msg_id_value = response_data.get('msg_id')
                    has_msg_id = bool(msg_id_value)
            except:
                pass
        
        task_data = {
            'id': task.id,
            'order_id': task.order_id,
            'order_number': task.order_number,
            'order': {
                'id': order.id if order else None,
                'order_number': order.order_number if order else None,
                'customer_name': order.customer_name if order else None,
                'product_name': order.product_name if order else None,
                'status': order.status if order else None
            } if order else None,
            'product_id': task.product_id,
            'preset_id': task.preset_id,
            'request_url': task.request_url,
            'request_params': task.request_params,
            'response_status': task.response_status,
            'response_data': task.response_data,
            'msg_id': msg_id_value,  # 直接返回msg_id字段
            'has_msg_id': has_msg_id,  # 标记是否有msg_id，用于前端判断是否显示查询按钮
            'result_image_url': task.result_image_url,
            'result_image_path': task.result_image_path,
            'error_message': task.error_message,
            'duration_ms': task.duration_ms,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None
        }
        
        return jsonify({
            'status': 'success',
            'data': task_data
        })
    
    except Exception as e:
        print(f"获取美颜任务详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取任务详情失败: {str(e)}'}), 500


@meitu_bp.route('/api/tasks/<int:task_id>/recheck', methods=['POST'])
@login_required
def recheck_meitu_task_result(task_id):
    """重新查询美图API任务结果（通过msg_id查询）"""
    import json
    import sys
    import requests
    
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        MeituAPICallLog = test_server_module.MeituAPICallLog
        MeituAPIConfig = test_server_module.MeituAPIConfig
        
        # 获取任务
        task = MeituAPICallLog.query.get(task_id)
        if not task:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404
        
        # 优先从msg_id字段获取（如果存在），否则从response_data中提取
        msg_id = getattr(task, 'msg_id', None)
        if not msg_id and task.response_data:
            try:
                response_data = json.loads(task.response_data) if isinstance(task.response_data, str) else task.response_data
                msg_id = response_data.get('msg_id')
                # 如果从response_data中提取到了msg_id，更新到msg_id字段（如果字段存在）
                if msg_id and hasattr(task, 'msg_id'):
                    task.msg_id = msg_id
                    db.session.commit()
            except:
                pass
        
        if not msg_id:
            # 检查是否是原始调用失败（没有返回msg_id）
            if task.response_status and task.response_status != 200:
                return jsonify({
                    'status': 'error', 
                    'message': f'原始调用失败（HTTP {task.response_status}），没有返回msg_id，无法查询结果。请检查原始调用的错误信息。'
                }), 400
            else:
                return jsonify({
                    'status': 'error', 
                    'message': '任务没有msg_id，无法查询结果。可能是原始调用失败或响应格式不正确。'
                }), 400
        
        # 获取API配置（使用原始SQL避免字段不存在的问题）
        config = None
        try:
            # 先检查表结构
            result = db.session.execute(
                db.text("PRAGMA table_info(meitu_api_config)")
            ).fetchall()
            columns = {row[1]: row for row in result}
            
            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ['api_key', 'api_secret', 'api_base_url', 'api_endpoint']
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            print(f"⚠️ 使用SQLAlchemy查询配置失败，尝试使用原始SQL: {str(e)}")
            # 使用原始SQL查询
            result = db.session.execute(
                db.text("SELECT id FROM meitu_api_config WHERE is_active = 1 LIMIT 1")
            ).fetchone()
            if result:
                config_id = result[0] if isinstance(result, tuple) else result._mapping['id']
                # 构建SELECT语句，只选择存在的列
                select_cols = ['id']
                if 'api_key' in columns:
                    select_cols.append('api_key')
                elif 'app_id' in columns:
                    select_cols.append('app_id AS api_key')
                else:
                    select_cols.append("'' AS api_key")
                
                if 'api_secret' in columns:
                    select_cols.append('api_secret')
                elif 'secret_id' in columns:
                    select_cols.append('secret_id AS api_secret')
                else:
                    select_cols.append("'' AS api_secret")
                
                # 添加其他可能存在的列
                for col in ['api_base_url', 'api_endpoint', 'repost_url']:
                    if col in columns:
                        select_cols.append(col)
                    elif col == 'api_endpoint':
                        select_cols.append("'/openapi/realphotolocal_async' AS api_endpoint")
                    elif col == 'api_base_url':
                        select_cols.append("'https://api.yunxiu.meitu.com' AS api_base_url")
                
                sql = f"SELECT {', '.join(select_cols)} FROM meitu_api_config WHERE id = {config_id}"
                result = db.session.execute(db.text(sql)).fetchone()
                
                if result:
                    result_dict = dict(result._mapping) if hasattr(result, '_mapping') else dict(zip([c.split(' AS ')[-1] if ' AS ' in c else c for c in select_cols], result))
                    
                    class SimpleConfig:
                        def __init__(self, data):
                            self.id = data.get('id')
                            self.api_key = data.get('api_key', '')
                            self.api_secret = data.get('api_secret', '')
                            self.api_base_url = data.get('api_base_url', 'https://api.yunxiu.meitu.com')
                            self.api_endpoint = data.get('api_endpoint', '/openapi/realphotolocal_async')
                            self.repost_url = data.get('repost_url')
                    
                    config = SimpleConfig(result_dict)
        
        if not config:
            return jsonify({'status': 'error', 'message': '未找到API配置'}), 500
        
        # 优先从原始调用的请求参数中获取API密钥（确保使用相同的密钥）
        api_key = None
        api_secret = None
        api_base_url = getattr(config, 'api_base_url', None) or 'https://api.yunxiu.meitu.com'
        
        if task.request_params:
            try:
                original_params = json.loads(task.request_params) if isinstance(task.request_params, str) else task.request_params
                original_api_key = original_params.get('api_key', '')
                original_api_secret = original_params.get('api_secret', '')
                print(f"📋 原始调用请求参数中的API密钥: api_key={original_api_key}, api_secret={original_api_secret[:10] if original_api_secret else 'None'}...")
                
                if original_api_key and original_api_secret:
                    api_key = original_api_key
                    api_secret = original_api_secret
                    print(f"✅ 使用原始调用请求参数中的API密钥")
                else:
                    print(f"⚠️ 原始调用请求参数中没有API密钥或密钥为空")
            except Exception as e:
                print(f"⚠️ 解析原始调用请求参数失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 如果原始调用中没有，使用配置中的密钥
        if not api_key or not api_secret:
            config_api_key = getattr(config, 'api_key', None) or getattr(config, 'app_id', '')
            config_api_secret = getattr(config, 'api_secret', None) or getattr(config, 'secret_id', '')
            print(f"📋 配置中的API密钥: api_key={config_api_key}, api_secret={config_api_secret[:10] if config_api_secret else 'None'}...")
            
            api_key = config_api_key
            api_secret = config_api_secret
            print(f"⚠️ 使用配置中的API密钥")
        
        # 验证API密钥是否获取成功
        if not api_key or not api_secret:
            return jsonify({
                'status': 'error',
                'message': f'API密钥获取失败: api_key={bool(api_key)}, api_secret={bool(api_secret)}。请检查配置或原始调用记录。'
            }), 500
        
        print(f"🔑 最终使用的API密钥: api_key={api_key}, api_secret={api_secret[:10]}...")
        
        # 对比原始调用和查询使用的API密钥是否一致
        if task.request_params:
            try:
                original_params = json.loads(task.request_params) if isinstance(task.request_params, str) else task.request_params
                original_api_key = original_params.get('api_key', '')
                if original_api_key and original_api_key != api_key:
                    print(f"⚠️ ⚠️ ⚠️ 警告：查询使用的API密钥与原始调用不一致！")
                    print(f"   原始调用使用的API密钥: {original_api_key}")
                    print(f"   查询使用的API密钥: {api_key}")
                    print(f"   这可能导致查询失败！")
            except:
                pass
        
        # 查询结果（根据文档：POST https://api.yunxiu.meitu.com/openapi/query）
        import requests
        query_url = f"{api_base_url.rstrip('/')}/openapi/query"
        
        query_data = {
            'api_key': api_key,
            'api_secret': api_secret,
            'msg_id': msg_id
        }
        
        print(f"🔄 查询美图API结果，msg_id: {msg_id}")
        print(f"📤 查询URL: {query_url}")
        print(f"📤 查询参数: {json.dumps({**query_data, 'api_secret': '***'}, ensure_ascii=False)}")  # 隐藏密钥
        
        # 添加请求头（确保Content-Type正确）
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(query_url, json=query_data, headers=headers, timeout=30, proxies={'http': None, 'https': None})
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 根据文档，响应格式：
            # {
            #   "code": 0,
            #   "data": {
            #     "msg_id": "...",
            #     "media_data": "https://..."  // 结果图片URL
            #   },
            #   "message": "success",
            #   "request_id": "..."
            # }
            
            if result.get('code') == 0 and 'data' in result:
                data = result.get('data')
                result_image_url = data.get('media_data')
                
                if result_image_url:
                    # 更新任务状态和结果
                    task.status = 'success'
                    task.result_image_url = result_image_url
                    task.response_data = json.dumps(result, ensure_ascii=False)
                    
                    # 尝试下载图片到本地
                    from app.services.meitu_api_service import download_result_image
                    result_image_path = download_result_image(result_image_url, task.order_number)
                    if result_image_path:
                        task.result_image_path = result_image_path
                    
                    db.session.commit()
                    
                    print(f"✅ 查询成功，结果图片URL: {result_image_url}")
                    if result_image_path:
                        print(f"✅ 图片已下载到本地: {result_image_path}")
                    
                    return jsonify({
                        'status': 'success',
                        'message': '查询成功',
                        'data': {
                            'result_image_url': result_image_url,
                            'result_image_path': result_image_path,
                            'response_data': result
                        }
                    })
                else:
                    # 可能还在处理中
                    task.response_data = json.dumps(result, ensure_ascii=False)
                    db.session.commit()
                    return jsonify({
                        'status': 'pending',
                        'message': '任务仍在处理中',
                        'data': {
                            'response_data': result
                        }
                    })
            elif result.get('code') == 90002:
                # GATEWAY_AUTHORIZED_ERROR - 认证失败
                error_msg = f"API认证失败: {result.get('message', 'GATEWAY_AUTHORIZED_ERROR')}"
                print(f"❌ {error_msg}")
                print(f"   使用的API密钥: {api_key}")
                print(f"   使用的API密钥长度: {len(api_key) if api_key else 0}")
                print(f"   使用的API密钥长度: {len(api_secret) if api_secret else 0}")
                
                # 检查是否使用了原始调用的密钥
                if task.request_params:
                    try:
                        original_params = json.loads(task.request_params) if isinstance(task.request_params, str) else task.request_params
                        original_api_key = original_params.get('api_key', '')
                        if original_api_key == api_key:
                            print(f"   ✅ 已使用原始调用时的API密钥")
                        else:
                            print(f"   ⚠️ 原始调用使用的API密钥: {original_api_key}")
                    except:
                        pass
                
                task.status = 'failed'
                task.error_message = error_msg
                task.response_data = json.dumps(result, ensure_ascii=False)
                db.session.commit()
                return jsonify({
                    'status': 'error',
                    'message': error_msg + '。请检查API密钥配置是否正确，确保查询时使用的密钥与原始调用时使用的密钥一致。',
                    'data': {
                        'response_data': result,
                        'hint': '查询接口需要使用与原始调用相同的API密钥。如果仍然失败，可能是API密钥已过期或无效。'
                    }
                }), 400
            else:
                error_msg = result.get('message', '查询失败')
                task.status = 'failed'
                task.error_message = error_msg
                task.response_data = json.dumps(result, ensure_ascii=False)
                db.session.commit()
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'data': {
                        'response_data': result
                    }
                }), 400
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            task.status = 'failed'
            task.error_message = error_msg
            db.session.commit()
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
    
    except Exception as e:
        print(f"重新查询美图API任务结果失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'查询失败: {str(e)}'}), 500


@meitu_bp.route('/api/test', methods=['POST'])
@login_required
def test_meitu_api():
    """测试美图API调用"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        MeituAPIConfig = test_server_module.MeituAPIConfig
        MeituAPICallLog = test_server_module.MeituAPICallLog
        
        # 获取预设ID
        preset_id = request.form.get('preset_id', '').strip()
        if not preset_id:
            return jsonify({'status': 'error', 'message': '请输入预设ID'}), 400
        
        # 获取API配置（优先使用原始SQL，避免列不存在的问题）
        config = None
        try:
            # 先检查表结构
            result = db.session.execute(
                db.text("PRAGMA table_info(meitu_api_config)")
            ).fetchall()
            columns = {row[1]: row for row in result}
            
            # 如果所有必需字段都存在，才使用ORM查询
            required_fields = ['api_key', 'api_secret', 'api_base_url', 'api_endpoint']
            if all(field in columns for field in required_fields):
                config = MeituAPIConfig.query.filter_by(is_active=True).first()
            else:
                raise Exception("缺少必需字段，使用原始SQL查询")
        except Exception as e:
            print(f"⚠️ 查询配置失败，尝试使用原始SQL: {str(e)}")
            # 如果查询失败，使用原始SQL查找
            result = db.session.execute(
                db.text("SELECT id FROM meitu_api_config WHERE is_active = 1 LIMIT 1")
            ).fetchone()
            if result:
                # SQLAlchemy 2.0 的 Row 对象需要用索引访问，或者转换为字典
                if hasattr(result, '_mapping'):
                    config_id = result._mapping['id']
                elif isinstance(result, tuple):
                    config_id = result[0]
                else:
                    config_id = result[0]  # 默认使用索引0
                try:
                    config = MeituAPIConfig.query.get(config_id)
                except:
                    # 如果还是失败，使用原始SQL构建配置对象
                    result = db.session.execute(
                        db.text("PRAGMA table_info(meitu_api_config)")
                    ).fetchall()
                    columns = {row[1]: row for row in result}
                    
                    # 构建SELECT语句，只选择存在的列
                    select_cols = ['id']
                    if 'api_key' in columns:
                        select_cols.append('api_key')
                    elif 'app_id' in columns:
                        select_cols.append('app_id AS api_key')
                    else:
                        select_cols.append("'' AS api_key")
                    
                    if 'api_secret' in columns:
                        select_cols.append('api_secret')
                    elif 'secret_id' in columns:
                        select_cols.append('secret_id AS api_secret')
                    else:
                        select_cols.append("'' AS api_secret")
                    
                    # 添加其他可能存在的列
                    for col in ['api_base_url', 'api_endpoint', 'repost_url', 'is_active', 'enable_in_workflow']:
                        if col in columns:
                            select_cols.append(col)
                        elif col == 'api_endpoint':
                            select_cols.append("'/openapi/realphotolocal_async' AS api_endpoint")
                        elif col == 'api_base_url':
                            select_cols.append("'https://api.yunxiu.meitu.com' AS api_base_url")
                        elif col == 'is_active':
                            select_cols.append('1 AS is_active')
                        elif col == 'enable_in_workflow':
                            select_cols.append('0 AS enable_in_workflow')
                    
                    sql = f"SELECT {', '.join(select_cols)} FROM meitu_api_config WHERE id = {config_id}"
                    result = db.session.execute(db.text(sql)).fetchone()
                    
                    if result:
                        result_dict = dict(result._mapping) if hasattr(result, '_mapping') else dict(zip([c.split(' AS ')[-1] if ' AS ' in c else c for c in select_cols], result))
                        
                        class SimpleConfig:
                            def __init__(self, data):
                                self.id = data.get('id')
                                self.api_key = data.get('api_key', '')
                                self.api_secret = data.get('api_secret', '')
                                self.api_base_url = data.get('api_base_url', 'https://api.yunxiu.meitu.com')
                                self.api_endpoint = data.get('api_endpoint', '/openapi/realphotolocal_async')
                                self.repost_url = data.get('repost_url')
                                self.is_active = data.get('is_active', True)
                                self.enable_in_workflow = data.get('enable_in_workflow', False)
                            
                            @property
                            def app_id(self):
                                return self.api_key
                            
                            @property
                            def app_key(self):
                                return self.api_key
                            
                            @property
                            def secret_id(self):
                                return self.api_secret
                        
                        config = SimpleConfig(result_dict)
                    else:
                        config = None
            else:
                config = None
        
        if not config:
            return jsonify({'status': 'error', 'message': '请先配置美图API密钥'}), 400
        
        # 生成测试订单号
        from datetime import datetime
        test_order_number = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 检查是否提供了云端URL（如果前端开启了"先上传到云服务器"开关）
        cloud_image_url = request.form.get('cloud_image_url', '').strip()
        image_url = None
        
        if cloud_image_url:
            # 如果提供了云端URL，直接使用
            image_url = cloud_image_url
            print(f"✅ 使用云端URL（已上传到云服务器）: {image_url}")
        else:
            # 否则使用原来的逻辑：上传到本地，然后获取公网URL
            if 'image' not in request.files:
                return jsonify({'status': 'error', 'message': '请上传测试图片'}), 400
            
            image_file = request.files['image']
            if image_file.filename == '':
                return jsonify({'status': 'error', 'message': '请选择图片文件'}), 400
            
            # 保存上传的图片到临时目录
            import os
            from werkzeug.utils import secure_filename
            
            uploads_dir = 'uploads'
            test_dir = os.path.join(uploads_dir, 'meitu_test')
            os.makedirs(test_dir, exist_ok=True)
            
            filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(image_file.filename)}"
            test_image_path = os.path.join(test_dir, filename)
            image_file.save(test_image_path)
            
            # 调用美图API
            from app.services.meitu_api_service import call_meitu_api, get_public_image_url
            
            # 获取图片的公开URL（美图API需要图片URL）
            # 测试环境：自动上传到OSS获取公网URL
            # 如果OSS未配置，会返回错误提示
            print(f"📤 开始获取图片公网URL: {test_image_path}")
            image_url = get_public_image_url(
                test_image_path,
                use_oss=True,  # 测试环境使用OSS
                order_number=test_order_number
            )
            
            if not image_url:
                return jsonify({
                    'status': 'error',
                    'message': '无法获取图片的公网URL。请配置OSS（scripts/oss_config.py）或开启"先上传到云服务器"开关',
                    'hint': '测试环境需要将图片上传到OSS/CDN等公网可访问的存储服务，或开启"先上传到云服务器"开关'
                }), 400
        
        # 调用美图API
        from app.services.meitu_api_service import call_meitu_api
        
        # 获取API密钥（根据美图API文档：api_key对应APIKEY，api_secret对应SECRETID）
        # 注意：不要使用app_id，应该直接使用api_key和api_secret
        api_key_value = getattr(config, 'api_key', None) or ''
        api_secret_value = getattr(config, 'api_secret', None) or ''
        
        # 如果api_key或api_secret为空，尝试从旧字段获取（兼容旧数据）
        if not api_key_value:
            api_key_value = getattr(config, 'app_id', '') or ''
        if not api_secret_value:
            api_secret_value = getattr(config, 'secret_id', '') or ''
        
        # 获取API基础URL和端点（确保使用正确的默认值）
        api_base_url = getattr(config, 'api_base_url', None) or 'https://api.yunxiu.meitu.com'
        api_endpoint = getattr(config, 'api_endpoint', None) or '/openapi/realphotolocal_async'
        
        print(f"📋 美图API配置:")
        print(f"   - API Key (api_key): {api_key_value[:10] if api_key_value else 'None'}...")
        print(f"   - API Secret (api_secret): {api_secret_value[:10] if api_secret_value else 'None'}...")
        print(f"   - API Base URL: {api_base_url}")
        print(f"   - API Endpoint: {api_endpoint}")
        print(f"   - 预设ID: {preset_id}")
        print(f"   - 图片URL: {image_url}")
        
        # 验证API密钥
        if not api_key_value or not api_secret_value:
            return jsonify({
                'status': 'error',
                'message': f'API密钥配置不完整：api_key={bool(api_key_value)}, api_secret={bool(api_secret_value)}。请检查配置页面，确保填写了正确的APIKEY和SECRETID。'
            }), 400
        
        success, result_image_path, error_message, call_log = call_meitu_api(
            image_path=image_url,  # 传递图片URL而不是本地路径
            preset_id=preset_id,
            api_key=api_key_value,
            api_secret=api_secret_value,
            api_base_url=api_base_url,
            api_endpoint=api_endpoint,
            repost_url=config.repost_url if hasattr(config, 'repost_url') else None,
            db=db,
            MeituAPICallLog=MeituAPICallLog,
            order_id=None,
            order_number=test_order_number,
            product_id=None
        )
        
        # 提交数据库更改
        db.session.commit()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '测试成功',
                'data': {
                    'task_id': call_log.id if call_log else None,
                    'order_number': test_order_number,
                    'result_image_url': call_log.result_image_url if call_log else None,
                    'result_image_path': result_image_path,
                    'duration_ms': call_log.duration_ms if call_log else None,
                    'response_status': call_log.response_status if call_log else None
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': error_message or '测试失败',
                'data': {
                    'task_id': call_log.id if call_log else None,
                    'order_number': test_order_number,
                    'error_message': error_message
                }
            }), 400
    
    except Exception as e:
        print(f"测试美图API失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'测试失败: {str(e)}'}), 500
