"""
管理后台风格管理API路由模块
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import sys
import os
import shutil
import json
import time
import threading
import base64
import requests
from werkzeug.utils import secure_filename

# 创建蓝图
admin_styles_api_bp = Blueprint('admin_styles_api', __name__, url_prefix='/api/admin/styles')

def get_models():
    """延迟导入数据库模型，避免循环导入"""
    try:
        test_server = sys.modules.get('test_server')
        if test_server:
            return {
                'StyleCategory': test_server.StyleCategory,
                'StyleImage': test_server.StyleImage,
                'AIConfig': test_server.AIConfig,
                'db': test_server.db
            }
        return None
    except Exception as e:
        print(f"⚠️ 获取数据库模型失败: {e}")
        return None

def get_style_code_helpers():
    """获取风格代码处理辅助函数"""
    try:
        from app.models import _sanitize_style_code, _build_style_code, _ensure_unique_style_code
        return {
            '_sanitize_style_code': _sanitize_style_code,
            '_build_style_code': _build_style_code,
            '_ensure_unique_style_code': _ensure_unique_style_code
        }
    except ImportError as e:
        print(f"⚠️ 导入风格代码辅助函数失败: {e}")
        return None

# ============================================================================
# 风格分类API
# ============================================================================

@admin_styles_api_bp.route('/categories', methods=['GET'])
def admin_get_categories():
    """获取所有风格分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        categories = StyleCategory.query.order_by(StyleCategory.sort_order).all()
        result = []
        for category in categories:
            result.append({
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'description': category.description,
                'icon': category.icon,
                'cover_image': category.cover_image,
                'sort_order': category.sort_order,
                'is_active': category.is_active,
                'created_at': category.created_at.isoformat(),
                # AI工作流配置字段
                'is_ai_enabled': category.is_ai_enabled or False,
                'workflow_name': category.workflow_name or '',
                'workflow_file': category.workflow_file or '',
                'workflow_input_ids': category.workflow_input_ids or '',
                'workflow_output_id': category.workflow_output_id or '',
                'workflow_ref_id': category.workflow_ref_id or '',
                'workflow_ref_image': category.workflow_ref_image or '',
                'workflow_custom_prompt_id': category.workflow_custom_prompt_id or '',
                'workflow_custom_prompt_content': category.workflow_custom_prompt_content or ''
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取分类失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取分类失败'
        }), 500

@admin_styles_api_bp.route('/categories', methods=['POST'])
def admin_create_category():
    """创建风格分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        db = models['db']
        
        data = request.get_json()
        
        # 检查必填字段
        required_fields = ['name', 'code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'缺少必要字段: {field}'}), 400
        
        # 检查代码是否重复
        existing = StyleCategory.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'status': 'error', 'message': '分类代码已存在'}), 400
        
        # 处理工作流文件重命名（如果提供了workflow_name和workflow_file）
        workflow_name = data.get('workflow_name') or None
        workflow_file = data.get('workflow_file') or None
        
        if workflow_file and workflow_name:
            try:
                workflows_dir = 'workflows'
                os.makedirs(workflows_dir, exist_ok=True)
                
                # 生成新的文件名（基于workflow_name）
                safe_name = secure_filename(workflow_name)
                new_filename = f"{safe_name}.json"
                new_filepath = os.path.join(workflows_dir, new_filename)
                
                # 如果文件已存在，添加时间戳避免覆盖
                if os.path.exists(new_filepath) and new_filename != workflow_file:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_filename = f"{safe_name}_{timestamp}.json"
                    new_filepath = os.path.join(workflows_dir, new_filename)
                
                # 如果旧文件存在且与新文件不同，重命名
                old_filepath = os.path.join(workflows_dir, workflow_file)
                if os.path.exists(old_filepath) and old_filepath != new_filepath:
                    shutil.move(old_filepath, new_filepath)
                    workflow_file = new_filename
                    print(f"✅ 工作流文件已重命名: {workflow_file} -> {new_filename}")
                elif os.path.exists(new_filepath):
                    workflow_file = new_filename
                    
            except Exception as e:
                print(f"⚠️ 重命名工作流文件失败: {str(e)}")
                # 失败时保持原文件名
        
        # 创建分类
        category = StyleCategory(
            name=data['name'],
            code=data['code'],
            description=data.get('description', ''),
            icon=data.get('icon', ''),
            cover_image=data.get('cover_image', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True),
            # AI工作流配置字段
            is_ai_enabled=data.get('is_ai_enabled', False),
            workflow_name=workflow_name,
            workflow_file=workflow_file,
            workflow_input_ids=data.get('workflow_input_ids') or None,
            workflow_output_id=data.get('workflow_output_id') or None,
            workflow_ref_id=data.get('workflow_ref_id') or None,
            workflow_ref_image=data.get('workflow_ref_image') or None,
            workflow_custom_prompt_id=data.get('workflow_custom_prompt_id') or None,
            workflow_custom_prompt_content=data.get('workflow_custom_prompt_content') or None
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类创建成功',
            'data': {
                'id': category.id,
                'name': category.name,
                'code': category.code
            }
        })
        
    except Exception as e:
        print(f"创建分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '创建分类失败'
        }), 500

@admin_styles_api_bp.route('/categories/<int:category_id>', methods=['PUT'])
def admin_update_category(category_id):
    """更新风格分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        db = models['db']
        
        category = StyleCategory.query.get_or_404(category_id)
        data = request.get_json()
        
        # 检查代码是否重复（排除自己）
        if data.get('code') and data['code'] != category.code:
            existing = StyleCategory.query.filter_by(code=data['code']).first()
            if existing:
                return jsonify({'status': 'error', 'message': '分类代码已存在'}), 400
        
        # 更新字段
        if 'name' in data:
            category.name = data['name']
        if 'code' in data:
            category.code = data['code']
        if 'description' in data:
            category.description = data['description']
        if 'icon' in data:
            category.icon = data['icon']
        if 'cover_image' in data:
            category.cover_image = data['cover_image']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        if 'is_active' in data:
            category.is_active = data['is_active']
        # AI工作流配置字段
        if 'is_ai_enabled' in data:
            category.is_ai_enabled = data['is_ai_enabled']
        
        # 先更新workflow_name，因为重命名文件时需要用到
        if 'workflow_name' in data:
            category.workflow_name = data['workflow_name'] or None
        
        if 'workflow_file' in data:
            old_workflow_file = category.workflow_file
            new_workflow_file = data['workflow_file'] or None
            
            # 只有在workflow_file有变化时才处理重命名
            if not new_workflow_file:
                new_workflow_file = old_workflow_file
            elif new_workflow_file == old_workflow_file:
                new_workflow_file = old_workflow_file
            elif new_workflow_file and category.workflow_name and new_workflow_file != old_workflow_file:
                try:
                    workflows_dir = 'workflows'
                    os.makedirs(workflows_dir, exist_ok=True)
                    
                    safe_name = secure_filename(category.workflow_name)
                    new_filename = f"{safe_name}.json"
                    new_filepath = os.path.join(workflows_dir, new_filename)
                    
                    if os.path.exists(new_filepath) and new_filename != new_workflow_file:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        new_filename = f"{safe_name}_{timestamp}.json"
                        new_filepath = os.path.join(workflows_dir, new_filename)
                    
                    old_filepath = os.path.join(workflows_dir, new_workflow_file)
                    if os.path.exists(old_filepath) and old_filepath != new_filepath:
                        shutil.move(old_filepath, new_filepath)
                        new_workflow_file = new_filename
                        print(f"✅ 工作流文件已重命名: {new_workflow_file} -> {new_filename}")
                    elif not os.path.exists(old_filepath):
                        if os.path.exists(new_filepath):
                            new_workflow_file = new_filename
                    else:
                        new_workflow_file = new_filename
                        
                except Exception as e:
                    print(f"⚠️ 重命名工作流文件失败: {str(e)}")
            
            category.workflow_file = new_workflow_file
        if 'workflow_input_ids' in data:
            category.workflow_input_ids = data['workflow_input_ids'] or None
        if 'workflow_output_id' in data:
            category.workflow_output_id = data['workflow_output_id'] or None
        if 'workflow_ref_id' in data:
            category.workflow_ref_id = data['workflow_ref_id'] or None
        if 'workflow_ref_image' in data:
            category.workflow_ref_image = data['workflow_ref_image'] or None
        if 'workflow_custom_prompt_id' in data:
            category.workflow_custom_prompt_id = data['workflow_custom_prompt_id'] or None
        if 'workflow_custom_prompt_content' in data:
            category.workflow_custom_prompt_content = data['workflow_custom_prompt_content'] or None
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类更新成功'
        })
        
    except Exception as e:
        print(f"更新分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新分类失败'
        }), 500

@admin_styles_api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    """删除风格分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        db = models['db']
        
        category = StyleCategory.query.get_or_404(category_id)
        
        # 删除分类下的所有图片
        StyleImage.query.filter_by(category_id=category_id).delete()
        
        # 删除分类
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类删除成功'
        })
        
    except Exception as e:
        print(f"删除分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '删除分类失败'
        }), 500

# ============================================================================
# 风格图片API
# ============================================================================

@admin_styles_api_bp.route('/images', methods=['GET'])
def admin_get_images():
    """获取所有风格图片"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleImage = models['StyleImage']
        APITemplate = models.get('APITemplate')
        APIProviderConfig = models.get('APIProviderConfig')
        
        images = StyleImage.query.order_by(StyleImage.sort_order).all()
        result = []
        for image in images:
            # 查询API模板信息
            api_template_info = None
            if APITemplate:
                api_template = APITemplate.query.filter_by(style_image_id=image.id).first()
                if api_template and api_template.api_config_id and APIProviderConfig:
                    api_config = APIProviderConfig.query.get(api_template.api_config_id)
                    if api_config:
                        api_template_info = {
                            'api_template_id': api_template.id,
                            'api_config_id': api_template.api_config_id,
                            'api_provider': api_config.provider_name or api_config.name
                        }
            
            result.append({
                'id': image.id,
                'category_id': image.category_id,
                'name': image.name,
                'code': image.code,
                'description': image.description,
                'image_url': image.image_url,
                'design_image_url': image.design_image_url or '',
                'sort_order': image.sort_order,
                'is_active': image.is_active,
                'created_at': image.created_at.isoformat(),
                # AI工作流配置字段
                'is_ai_enabled': image.is_ai_enabled,
                'workflow_name': image.workflow_name or '',
                'workflow_file': image.workflow_file or '',
                'workflow_input_ids': image.workflow_input_ids or '',
                'workflow_output_id': image.workflow_output_id or '',
                'workflow_ref_id': image.workflow_ref_id or '',
                'workflow_ref_image': image.workflow_ref_image or '',
                'workflow_custom_prompt_id': image.workflow_custom_prompt_id or '',
                'workflow_custom_prompt_content': image.workflow_custom_prompt_content or '',
                # API模板信息
                'api_template_id': api_template_info['api_template_id'] if api_template_info else None,
                'api_config_id': api_template_info['api_config_id'] if api_template_info else None,
                'api_provider': api_template_info['api_provider'] if api_template_info else None
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取图片失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取图片失败'
        }), 500

@admin_styles_api_bp.route('/images', methods=['POST'])
def admin_create_image():
    """创建风格图片"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        db = models['db']
        helpers = get_style_code_helpers()
        if not helpers:
            return jsonify({
                'status': 'error',
                'message': '风格代码辅助函数未初始化'
            }), 500
        
        _sanitize_style_code = helpers['_sanitize_style_code']
        _build_style_code = helpers['_build_style_code']
        _ensure_unique_style_code = helpers['_ensure_unique_style_code']
        
        data = request.get_json()
        
        # 检查必填字段
        required_fields = ['category_id', 'name', 'image_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'缺少必要字段: {field}'}), 400
        
        # 检查分类是否存在
        category = StyleCategory.query.get(data['category_id'])
        if not category:
            return jsonify({'status': 'error', 'message': '分类不存在'}), 400
        
        # 生成唯一风格代码
        raw_code = (data.get('code') or '').strip()
        sanitized_code = _sanitize_style_code(raw_code)
        if sanitized_code and sanitized_code == _sanitize_style_code(category.code):
            sanitized_code = ''
        if not sanitized_code:
            sanitized_code = _build_style_code(data['name'], category.code)
        final_code = _ensure_unique_style_code(sanitized_code)
        
        # 创建图片
        image = StyleImage(
            category_id=data['category_id'],
            name=data['name'],
            code=final_code,
            description=data.get('description', ''),
            image_url=data['image_url'],
            design_image_url=data.get('design_image_url') or None,
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(image)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '图片创建成功',
            'data': {
                'id': image.id,
                'name': image.name,
                'code': image.code
            }
        })
        
    except Exception as e:
        print(f"创建图片失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '创建图片失败'
        }), 500

@admin_styles_api_bp.route('/images/<int:image_id>', methods=['PUT'])
def admin_update_image(image_id):
    """更新风格图片"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        db = models['db']
        helpers = get_style_code_helpers()
        if not helpers:
            return jsonify({
                'status': 'error',
                'message': '风格代码辅助函数未初始化'
            }), 500
        
        _sanitize_style_code = helpers['_sanitize_style_code']
        _build_style_code = helpers['_build_style_code']
        _ensure_unique_style_code = helpers['_ensure_unique_style_code']
        
        image = StyleImage.query.get_or_404(image_id)
        data = request.get_json()

        # 处理分类变更
        new_category_id = data.get('category_id', image.category_id)
        category = StyleCategory.query.get(new_category_id)
        if not category:
            return jsonify({'status': 'error', 'message': '分类不存在'}), 400

        # 更新字段
        if 'category_id' in data:
            image.category_id = data['category_id']
        if 'name' in data:
            image.name = data['name']
        if 'description' in data:
            image.description = data['description']
        if 'image_url' in data:
            image.image_url = data['image_url']
        if 'design_image_url' in data:
            image.design_image_url = data['design_image_url'] or None
        if 'sort_order' in data:
            image.sort_order = data['sort_order']
        if 'is_active' in data:
            image.is_active = data['is_active']
        
        # AI工作流配置字段
        if 'is_ai_enabled' in data:
            image.is_ai_enabled = data['is_ai_enabled']
        
        if 'workflow_name' in data:
            image.workflow_name = data['workflow_name'] or None
        
        if 'workflow_file' in data:
            old_workflow_file = image.workflow_file
            new_workflow_file = data['workflow_file'] or None
            
            if not new_workflow_file:
                new_workflow_file = old_workflow_file
            elif new_workflow_file == old_workflow_file:
                new_workflow_file = old_workflow_file
            elif new_workflow_file and image.workflow_name and new_workflow_file != old_workflow_file:
                try:
                    workflows_dir = 'workflows'
                    os.makedirs(workflows_dir, exist_ok=True)
                    
                    safe_name = secure_filename(image.workflow_name)
                    new_filename = f"{safe_name}.json"
                    new_filepath = os.path.join(workflows_dir, new_filename)
                    
                    if os.path.exists(new_filepath) and new_filename != new_workflow_file:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        new_filename = f"{safe_name}_{timestamp}.json"
                        new_filepath = os.path.join(workflows_dir, new_filename)
                    
                    old_filepath = os.path.join(workflows_dir, new_workflow_file)
                    if os.path.exists(old_filepath) and old_filepath != new_filepath:
                        shutil.move(old_filepath, new_filepath)
                        new_workflow_file = new_filename
                        print(f"✅ 工作流文件已重命名: {new_workflow_file} -> {new_filename}")
                    elif not os.path.exists(old_filepath):
                        if os.path.exists(new_filepath):
                            new_workflow_file = new_filename
                    else:
                        new_workflow_file = new_filename
                        
                except Exception as e:
                    print(f"⚠️ 重命名工作流文件失败: {str(e)}")
            
            image.workflow_file = new_workflow_file
        if 'workflow_input_ids' in data:
            image.workflow_input_ids = data['workflow_input_ids'] or None
        if 'workflow_output_id' in data:
            image.workflow_output_id = data['workflow_output_id'] or None
        if 'workflow_ref_id' in data:
            image.workflow_ref_id = data['workflow_ref_id'] or None
        if 'workflow_ref_image' in data:
            image.workflow_ref_image = data['workflow_ref_image'] or None
        if 'workflow_custom_prompt_id' in data:
            image.workflow_custom_prompt_id = data['workflow_custom_prompt_id'] or None
        if 'workflow_custom_prompt_content' in data:
            image.workflow_custom_prompt_content = data['workflow_custom_prompt_content'] or None

        # 当 code 为空或与当前分类重复时自动重新生成
        requested_code = data.get('code') if 'code' in data else image.code
        sanitized_code = _sanitize_style_code(requested_code)
        if sanitized_code and sanitized_code == _sanitize_style_code(category.code):
            sanitized_code = ''
        if not sanitized_code:
            sanitized_code = _build_style_code(image.name, category.code)
        final_code = _ensure_unique_style_code(sanitized_code, image_id=image_id)
        image.code = final_code
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '图片更新成功'
        })
        
    except Exception as e:
        print(f"更新图片失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新图片失败'
        }), 500

@admin_styles_api_bp.route('/images/<int:image_id>', methods=['DELETE'])
def admin_delete_image(image_id):
    """删除风格图片"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleImage = models['StyleImage']
        db = models['db']
        
        image = StyleImage.query.get_or_404(image_id)
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '图片删除成功'
        })
        
    except Exception as e:
        print(f"删除图片失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '删除图片失败'
        }), 500

# ============================================================================
# 工作流测试API
# ============================================================================

@admin_styles_api_bp.route('/test-workflow/<int:image_id>', methods=['POST'])
@login_required
def test_workflow(image_id):
    """测试工作流API调用"""
    try:
        # 检查权限
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        StyleImage = models['StyleImage']
        AIConfig = models['AIConfig']
        db = models['db']
        
        # 获取图片配置
        image = StyleImage.query.get_or_404(image_id)
        category = StyleCategory.query.get_or_404(image.category_id)
        
        # 获取工作流配置
        from app.services.workflow_service import get_workflow_config, load_workflow_file, get_comfyui_config
        
        # 尝试从请求中获取临时配置
        data = request.get_json()
        temp_config = data.get('workflow_config') if data else None
        
        if temp_config:
            workflow_config = {
                'workflow_name': temp_config.get('workflow_name'),
                'workflow_file': temp_config.get('workflow_file'),
                'workflow_input_ids': temp_config.get('workflow_input_ids'),
                'workflow_output_id': temp_config.get('workflow_output_id'),
                'workflow_ref_id': temp_config.get('workflow_ref_id'),
                'workflow_ref_image': temp_config.get('workflow_ref_image'),
                'workflow_custom_prompt_id': temp_config.get('workflow_custom_prompt_id'),
                'workflow_custom_prompt_content': temp_config.get('workflow_custom_prompt_content'),
            }
            if not workflow_config.get('workflow_file'):
                return jsonify({
                    'status': 'error',
                    'message': '工作流文件未配置，请先上传工作流文件'
                }), 400
            if not workflow_config.get('workflow_input_ids'):
                return jsonify({
                    'status': 'error',
                    'message': '输入节点ID未配置'
                }), 400
            if not workflow_config.get('workflow_output_id'):
                return jsonify({
                    'status': 'error',
                    'message': '输出节点ID未配置'
                }), 400
            # 处理workflow_input_ids（如果是字符串，转换为数组）
            if isinstance(workflow_config['workflow_input_ids'], str):
                try:
                    workflow_config['workflow_input_ids'] = json.loads(workflow_config['workflow_input_ids'])
                except:
                    workflow_config['workflow_input_ids'] = [id.strip() for id in workflow_config['workflow_input_ids'].split(',') if id.strip()]
        else:
            workflow_config = get_workflow_config(category.id, image.id, db=db, StyleCategory=StyleCategory, StyleImage=StyleImage)
            
            if not workflow_config:
                return jsonify({
                    'status': 'error',
                    'message': '工作流未启用或配置不存在。请确保：\n1. 分类已启用AI工作流\n2. 或图片已启用独立AI工作流\n3. 工作流文件、输入节点ID、输出节点ID已配置'
                }), 400
        
        # 获取请求数据（支持多图）
        if not data or 'image_data' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少图片数据'
            }), 400
        
        # 处理base64图片数据（支持数组或单个）
        image_data_list = data['image_data']
        if not isinstance(image_data_list, list):
            # 向后兼容：如果是单个图片，转换为数组
            image_data_list = [image_data_list]
        
        if len(image_data_list) == 0:
            return jsonify({
                'status': 'error',
                'message': '请至少上传一张图片'
            }), 400
        
        # 保存所有图片文件
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        temp_filepaths = []
        
        try:
            for idx, image_data in enumerate(image_data_list):
                # 处理base64数据
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',', 1)[1]
                
                temp_filename = f"test_workflow_{image_id}_{int(time.time())}_{idx}.jpg"
                temp_filepath = os.path.join(uploads_dir, temp_filename)
                
                with open(temp_filepath, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                temp_filepaths.append(temp_filepath)
                print(f"✅ 测试图片 {idx + 1} 已保存: {temp_filepath}")
        except Exception as e:
            # 清理已保存的文件
            for fp in temp_filepaths:
                try:
                    if os.path.exists(fp):
                        os.remove(fp)
                except:
                    pass
            return jsonify({
                'status': 'error',
                'message': f'图片数据解析失败: {str(e)}'
            }), 400
        
        # 使用第一张图片进行工作流测试
        temp_filepath = temp_filepaths[0]
        
        # 获取ComfyUI配置
        comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)
        comfyui_url = f"{comfyui_config['base_url']}{comfyui_config['api_endpoint']}"
        
        print(f"🔗 使用ComfyUI地址: {comfyui_url}")
        
        # 加载工作流文件
        try:
            workflow_data = load_workflow_file(workflow_config['workflow_file'])
        except Exception as e:
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except:
                pass
            return jsonify({
                'status': 'error',
                'message': f'加载工作流文件失败: {str(e)}'
            }), 400
        
        # 替换工作流参数（需要先上传图片到ComfyUI）
        input_ids = workflow_config['workflow_input_ids']
        if input_ids and len(input_ids) > 0:
            if isinstance(workflow_data, dict) and input_ids[0] in workflow_data:
                # 上传图片到ComfyUI服务器
                comfyui_base_url = comfyui_config.get('base_url', 'http://127.0.0.1:8188')
                comfyui_upload_url = f"{comfyui_base_url.rstrip('/')}/upload/image"
                
                comfyui_image_filename = None
                try:
                    print(f"📤 开始上传图片到ComfyUI: {comfyui_upload_url}")
                    print(f"   本地图片路径: {temp_filepath}")
                    
                    # 读取图片文件
                    with open(temp_filepath, 'rb') as f:
                        # 生成唯一的文件名（避免冲突）
                        original_filename = os.path.basename(temp_filepath)
                        name, ext = os.path.splitext(original_filename)
                        upload_filename = f"{name}{ext}"
                        
                        # 上传文件（ComfyUI的/upload/image API）
                        files = {
                            'image': (upload_filename, f, 'image/jpeg' if ext.lower() in ['.jpg', '.jpeg'] else 'image/png')
                        }
                        
                        upload_response = requests.post(
                            comfyui_upload_url,
                            files=files,
                            timeout=60,
                            proxies={'http': None, 'https': None}  # 禁用代理
                        )
                        
                        if upload_response.status_code == 200:
                            upload_result = upload_response.json()
                            # ComfyUI返回格式通常是: {"name": "filename.jpg", "subfolder": "", "type": "input"}
                            comfyui_image_filename = upload_result.get('name', upload_filename)
                            print(f"✅ 图片已上传到ComfyUI: {comfyui_image_filename}")
                        else:
                            error_msg = f"上传图片到ComfyUI失败: HTTP {upload_response.status_code}, {upload_response.text}"
                            print(f"❌ {error_msg}")
                            # 如果上传失败，尝试使用原始文件名（可能文件已存在）
                            comfyui_image_filename = upload_filename
                            print(f"⚠️ 使用文件名作为后备方案: {comfyui_image_filename}")
                            
                except Exception as e:
                    error_msg = f"上传图片到ComfyUI异常: {str(e)}"
                    print(f"❌ {error_msg}")
                    import traceback
                    traceback.print_exc()
                    # 如果上传失败，使用原始文件名作为后备
                    comfyui_image_filename = os.path.basename(temp_filepath)
                    print(f"⚠️ 使用原始文件名作为后备方案: {comfyui_image_filename}")
                
                # 在工作流中使用上传后的文件名
                workflow_data[input_ids[0]]['inputs']['image'] = comfyui_image_filename
                print(f"📸 设置ComfyUI图片路径: {comfyui_image_filename}")
        
        if workflow_config.get('workflow_ref_id') and workflow_config.get('workflow_ref_image'):
            ref_id = workflow_config['workflow_ref_id']
            if isinstance(workflow_data, dict) and ref_id in workflow_data:
                workflow_data[ref_id]['inputs']['image'] = workflow_config['workflow_ref_image']
        
        if workflow_config.get('workflow_custom_prompt_id') and workflow_config.get('workflow_custom_prompt_content'):
            prompt_id = workflow_config['workflow_custom_prompt_id']
            if isinstance(workflow_data, dict) and prompt_id in workflow_data:
                workflow_data[prompt_id]['inputs']['text'] = workflow_config['workflow_custom_prompt_content']
        
        # 创建正式测试订单（保存所有上传的图片）
        # 获取Order和OrderImage模型
        import sys
        if 'test_server' in sys.modules:
            test_server_module = sys.modules['test_server']
            Order = getattr(test_server_module, 'Order', None)
            OrderImage = getattr(test_server_module, 'OrderImage', None)
            AITask = getattr(test_server_module, 'AITask', None)
        else:
            Order = None
            OrderImage = None
            AITask = None
        
        if not all([Order, OrderImage, AITask]):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        try:
            import uuid
            import random
            from datetime import datetime
            
            # 生成测试订单号
            order_number = f"TEST_{int(time.time() * 1000)}{random.randint(1000, 9999)}"
            
            # 获取风格图片信息
            style_image_name = image.name if image else '测试风格'
            style_category_name = category.name if category else '测试分类'
            
            # 创建Order记录
            test_order = Order(
                order_number=order_number,
                customer_name='测试用户',
                customer_phone='00000000000',
                style_name=style_image_name,
                product_name=f'{style_category_name} - {style_image_name}',
                price=0.0,  # 测试订单价格为0
                status='ai_processing',  # 测试订单状态为AI任务处理中
                source_type='admin_test',  # 标记为后台测试
                original_image=f"/uploads/{os.path.basename(temp_filepaths[0])}" if temp_filepaths else '',  # 使用第一张图片作为原图
                created_at=datetime.now()
            )
            db.session.add(test_order)
            db.session.flush()  # 获取order.id
            
            # 创建OrderImage记录（保存所有上传的图片）
            order_images = []
            for idx, temp_filepath in enumerate(temp_filepaths):
                img_filename = os.path.basename(temp_filepath)
                order_image = OrderImage(
                    order_id=test_order.id,
                    path=img_filename,
                    is_main=(idx == 0)  # 第一张图片设为主图
                )
                db.session.add(order_image)
                order_images.append(order_image)
            
            db.session.commit()
            print(f"✅ 创建测试订单成功: order_id={test_order.id}, order_number={order_number}, 图片数量={len(temp_filepaths)}")
            
            # 为每张图片创建AI任务
            from app.services.workflow_service import create_ai_task
            created_tasks = []
            task_errors = []
            
            # 准备工作流配置（使用前面已经获取的workflow_config）
            # workflow_config 已经在函数前面部分获取了，直接使用
            if not workflow_config:
                return jsonify({
                    'status': 'error',
                    'message': '工作流配置不存在，请先配置工作流'
                }), 400
            
            for idx, order_image in enumerate(order_images):
                try:
                    print(f"📸 为图片 {idx + 1}/{len(order_images)} 创建AI任务: order_image_id={order_image.id}")
                    success, ai_task, error_message = create_ai_task(
                        order_id=test_order.id,
                        style_category_id=category.id,
                        style_image_id=image_id,
                        order_image_id=order_image.id,  # 为每张图片创建独立任务
                        db=db,
                        Order=Order,
                        AITask=AITask,
                        StyleCategory=StyleCategory,
                        StyleImage=StyleImage,
                        OrderImage=OrderImage,
                        workflow_config=workflow_config  # 传入工作流配置（已在前面获取）
                    )
                    
                    if success and ai_task:
                        created_tasks.append({
                            'task_id': ai_task.id,
                            'comfyui_prompt_id': ai_task.comfyui_prompt_id,
                            'status': ai_task.status,
                            'order_image_id': order_image.id
                        })
                        print(f"✅ 图片 {idx + 1} 的AI任务创建成功: task_id={ai_task.id}, prompt_id={ai_task.comfyui_prompt_id}")
                    else:
                        error_msg = error_message or '未知错误'
                        task_errors.append(f"图片 {idx + 1}: {error_msg}")
                        print(f"❌ 图片 {idx + 1} 的AI任务创建失败: {error_msg}")
                except Exception as e:
                    error_msg = f"创建AI任务异常: {str(e)}"
                    task_errors.append(f"图片 {idx + 1}: {error_msg}")
                    print(f"❌ 图片 {idx + 1} 的AI任务创建异常: {error_msg}")
                    import traceback
                    traceback.print_exc()
            
            # 返回结果
            if len(created_tasks) > 0:
                return jsonify({
                    'status': 'success',
                    'message': f'工作流测试成功，已为 {len(created_tasks)} 张图片创建AI任务',
                    'data': {
                        'order_id': test_order.id,
                        'order_number': order_number,
                        'tasks': created_tasks,
                        'errors': task_errors if task_errors else None,
                        'total_images': len(temp_filepaths),
                        'success_count': len(created_tasks),
                        'failed_count': len(task_errors)
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '所有图片的AI任务创建失败',
                    'errors': task_errors
                }), 500
                
        except Exception as e:
            print(f"⚠️ 创建测试订单或AI任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
            if 'db' in locals():
                db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'创建测试订单失败: {str(e)}',
                'error': str(e)
            }), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'测试失败: {str(e)}',
            'error': str(e)
        }), 500

@admin_styles_api_bp.route('/test-workflow-category/<int:category_id>', methods=['POST'])
@login_required
def test_workflow_category(category_id):
    """测试工作流API调用（使用分类配置）"""
    try:
        # 检查权限
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        AIConfig = models['AIConfig']
        db = models['db']
        
        # 获取分类配置
        category = StyleCategory.query.get_or_404(category_id)
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'image_data' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少图片数据'
            }), 400
        
        # 获取工作流配置
        from app.services.workflow_service import load_workflow_file, get_comfyui_config
        temp_config = data.get('workflow_config')
        
        if temp_config:
            workflow_config = temp_config
            if isinstance(workflow_config.get('workflow_input_ids'), str):
                try:
                    workflow_config['workflow_input_ids'] = json.loads(workflow_config['workflow_input_ids'])
                except:
                    workflow_config['workflow_input_ids'] = [id.strip() for id in workflow_config['workflow_input_ids'].split(',') if id.strip()]
        else:
            if not category.is_ai_enabled:
                return jsonify({
                    'status': 'error',
                    'message': '分类未启用AI工作流'
                }), 400
            
            workflow_config = {
                'workflow_name': category.workflow_name,
                'workflow_file': category.workflow_file,
                'workflow_input_ids': json.loads(category.workflow_input_ids) if category.workflow_input_ids else [],
                'workflow_output_id': category.workflow_output_id,
                'workflow_ref_id': category.workflow_ref_id,
                'workflow_ref_image': category.workflow_ref_image,
                'workflow_custom_prompt_id': category.workflow_custom_prompt_id,
                'workflow_custom_prompt_content': category.workflow_custom_prompt_content,
            }
        
        # 验证必要字段
        if not workflow_config.get('workflow_file'):
            return jsonify({
                'status': 'error',
                'message': '工作流文件未配置'
            }), 400
        if not workflow_config.get('workflow_input_ids'):
            return jsonify({
                'status': 'error',
                'message': '输入节点ID未配置'
            }), 400
        if not workflow_config.get('workflow_output_id'):
            return jsonify({
                'status': 'error',
                'message': '输出节点ID未配置'
            }), 400
        
        # 处理base64图片数据
        image_data = data['image_data']
        if image_data.startswith('data:image'):
            image_data = image_data.split(',', 1)[1]
        
        # 保存临时图片文件
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        temp_filename = f"test_workflow_cat_{category_id}_{int(time.time())}.jpg"
        temp_filepath = os.path.join(uploads_dir, temp_filename)
        
        try:
            with open(temp_filepath, 'wb') as f:
                f.write(base64.b64decode(image_data))
            print(f"✅ 测试图片已保存: {temp_filepath}")
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'图片数据解析失败: {str(e)}'
            }), 400
        
        # 加载工作流文件
        try:
            workflow_data = load_workflow_file(workflow_config['workflow_file'])
        except Exception as e:
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except:
                pass
            return jsonify({
                'status': 'error',
                'message': f'加载工作流文件失败: {str(e)}'
            }), 400
        
        # 替换工作流参数（需要先上传图片到ComfyUI）
        input_ids = workflow_config['workflow_input_ids']
        if input_ids and len(input_ids) > 0:
            if isinstance(workflow_data, dict) and input_ids[0] in workflow_data:
                # 获取ComfyUI配置
                comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)
                comfyui_base_url = comfyui_config.get('base_url', 'http://127.0.0.1:8188')
                comfyui_upload_url = f"{comfyui_base_url.rstrip('/')}/upload/image"
                
                comfyui_image_filename = None
                try:
                    print(f"📤 开始上传图片到ComfyUI: {comfyui_upload_url}")
                    print(f"   本地图片路径: {temp_filepath}")
                    
                    # 读取图片文件
                    with open(temp_filepath, 'rb') as f:
                        # 生成唯一的文件名（避免冲突）
                        original_filename = os.path.basename(temp_filepath)
                        name, ext = os.path.splitext(original_filename)
                        upload_filename = f"{name}{ext}"
                        
                        # 上传文件（ComfyUI的/upload/image API）
                        files = {
                            'image': (upload_filename, f, 'image/jpeg' if ext.lower() in ['.jpg', '.jpeg'] else 'image/png')
                        }
                        
                        upload_response = requests.post(
                            comfyui_upload_url,
                            files=files,
                            timeout=60,
                            proxies={'http': None, 'https': None}  # 禁用代理
                        )
                        
                        if upload_response.status_code == 200:
                            upload_result = upload_response.json()
                            # ComfyUI返回格式通常是: {"name": "filename.jpg", "subfolder": "", "type": "input"}
                            comfyui_image_filename = upload_result.get('name', upload_filename)
                            print(f"✅ 图片已上传到ComfyUI: {comfyui_image_filename}")
                        else:
                            error_msg = f"上传图片到ComfyUI失败: HTTP {upload_response.status_code}, {upload_response.text}"
                            print(f"❌ {error_msg}")
                            # 如果上传失败，尝试使用原始文件名（可能文件已存在）
                            comfyui_image_filename = upload_filename
                            print(f"⚠️ 使用文件名作为后备方案: {comfyui_image_filename}")
                            
                except Exception as e:
                    error_msg = f"上传图片到ComfyUI异常: {str(e)}"
                    print(f"❌ {error_msg}")
                    import traceback
                    traceback.print_exc()
                    # 如果上传失败，使用原始文件名作为后备
                    comfyui_image_filename = os.path.basename(temp_filepath)
                    print(f"⚠️ 使用原始文件名作为后备方案: {comfyui_image_filename}")
                
                # 在工作流中使用上传后的文件名
                workflow_data[input_ids[0]]['inputs']['image'] = comfyui_image_filename
                print(f"📸 设置ComfyUI图片路径: {comfyui_image_filename}")
        
        if workflow_config.get('workflow_ref_id') and workflow_config.get('workflow_ref_image'):
            ref_id = workflow_config['workflow_ref_id']
            if isinstance(workflow_data, dict) and ref_id in workflow_data:
                workflow_data[ref_id]['inputs']['image'] = workflow_config['workflow_ref_image']
        
        if workflow_config.get('workflow_custom_prompt_id') and workflow_config.get('workflow_custom_prompt_content'):
            prompt_id = workflow_config['workflow_custom_prompt_id']
            if isinstance(workflow_data, dict) and prompt_id in workflow_data:
                workflow_data[prompt_id]['inputs']['text'] = workflow_config['workflow_custom_prompt_content']
        
        # 获取ComfyUI配置
        comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)
        comfyui_url = f"{comfyui_config['base_url']}{comfyui_config['api_endpoint']}"
        
        print(f"🔗 使用ComfyUI地址: {comfyui_url}")
        
        # 提交到ComfyUI
        request_body = {
            "prompt": workflow_data,
            "client_id": f"test_category_{category_id}_{int(time.time())}"
        }
        
        try:
            response = requests.post(
                comfyui_url,
                json=request_body,
                timeout=int(comfyui_config.get('timeout', 300)),
                proxies={'http': None, 'https': None}
            )
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get('prompt_id')
                
                return jsonify({
                    'status': 'success',
                    'message': '工作流测试成功，已提交到ComfyUI',
                    'data': {
                        'task_id': f"test_cat_{category_id}_{int(time.time())}",
                        'status': 'processing',
                        'comfyui_prompt_id': prompt_id,
                        'comfyui_response': result,
                        'output_id': workflow_config['workflow_output_id']
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'ComfyUI返回错误: HTTP {response.status_code}',
                    'error': response.text[:500]
                }), 400
                
        except requests.exceptions.RequestException as e:
            return jsonify({
                'status': 'error',
                'message': f'连接ComfyUI失败: {str(e)}',
                'error': str(e)
            }), 500
        finally:
            # 清理临时文件
            def cleanup_temp_file():
                import time as time_module
                time_module.sleep(5)
                try:
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                        print(f"✅ 临时测试图片已清理: {temp_filepath}")
                except:
                    pass
            
            threading.Thread(target=cleanup_temp_file, daemon=True).start()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'测试失败: {str(e)}',
            'error': str(e)
        }), 500

@admin_styles_api_bp.route('/test-workflow-result/<prompt_id>', methods=['GET'])
@login_required
def api_get_test_workflow_result(prompt_id):
    """查询ComfyUI测试结果"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        AIConfig = models['AIConfig']
        db = models['db']
        
        output_id = request.args.get('output_id')
        if not output_id:
            return jsonify({'status': 'error', 'message': '缺少输出节点ID'}), 400
        
        # 获取ComfyUI配置
        from app.services.workflow_service import get_comfyui_config
        comfyui_config = get_comfyui_config(db=db, AIConfig=AIConfig)
        
        # 查询ComfyUI历史记录
        history_url = f"{comfyui_config['base_url']}/history/{prompt_id}"
        
        try:
            response = requests.get(
                history_url,
                timeout=10,
                proxies={'http': None, 'https': None}
            )
            
            if response.status_code == 200:
                history_data = response.json()
                
                # 检查是否有结果
                if prompt_id in history_data:
                    outputs = history_data[prompt_id].get('outputs', {})
                    if output_id in outputs:
                        output_images = outputs[output_id].get('images', [])
                        if output_images and len(output_images) > 0:
                            image_info = output_images[0]
                            image_filename = image_info.get('filename')
                            image_subfolder = image_info.get('subfolder', '')
                            image_type = image_info.get('type', 'output')
                            
                            # 构建图片URL
                            if image_subfolder:
                                image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&subfolder={image_subfolder}&type={image_type}"
                            else:
                                image_url = f"{comfyui_config['base_url']}/view?filename={image_filename}&type={image_type}"
                            
                            return jsonify({
                                'status': 'success',
                                'message': '处理完成',
                                'data': {
                                    'image_url': image_url,
                                    'image_filename': image_filename,
                                    'image_subfolder': image_subfolder,
                                    'image_type': image_type
                                }
                            })
                        else:
                            return jsonify({
                                'status': 'processing',
                                'message': '处理中，暂无输出图片'
                            })
                    else:
                        return jsonify({
                            'status': 'processing',
                            'message': '处理中，输出节点尚未完成'
                        })
                else:
                    return jsonify({
                        'status': 'processing',
                        'message': '处理中，任务尚未完成'
                    })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'查询ComfyUI历史失败: HTTP {response.status_code}'
                }), 500
                
        except requests.exceptions.RequestException as e:
            return jsonify({
                'status': 'error',
                'message': f'连接ComfyUI失败: {str(e)}'
            }), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500

# ============================================================================
# 工作流文件上传API
# ============================================================================

@admin_styles_api_bp.route('/workflow/upload', methods=['POST'])
@login_required
def admin_upload_workflow():
    """上传ComfyUI工作流JSON文件"""
    try:
        # 检查权限
        if current_user.role not in ['admin', 'operator']:
            return jsonify({
                'status': 'error',
                'message': '权限不足'
            }), 403
        
        # 检查是否有文件
        if 'workflow' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '没有上传文件'
            }), 400
        
        file = request.files['workflow']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '文件名为空'
            }), 400
        
        # 检查文件扩展名
        if not file.filename.lower().endswith('.json'):
            return jsonify({
                'status': 'error',
                'message': '只支持JSON格式文件'
            }), 400
        
        # 读取文件内容并验证JSON格式
        try:
            file_content = file.read()
            workflow_data = json.loads(file_content.decode('utf-8'))
            
            # 验证是否是有效的JSON对象
            if not isinstance(workflow_data, dict):
                return jsonify({
                    'status': 'error',
                    'message': '无效的工作流格式：必须是JSON对象'
                }), 400
            
            if len(workflow_data) == 0:
                return jsonify({
                    'status': 'error',
                    'message': '无效的工作流格式：工作流文件不能为空'
                }), 400
            
        except json.JSONDecodeError as e:
            return jsonify({
                'status': 'error',
                'message': f'JSON格式错误: {str(e)}'
            }), 400
        except UnicodeDecodeError:
            return jsonify({
                'status': 'error',
                'message': '文件编码错误：必须是UTF-8格式'
            }), 400
        
        # 确保workflows目录存在
        workflows_dir = 'workflows'
        os.makedirs(workflows_dir, exist_ok=True)
        
        # 获取原始文件名
        original_filename = file.filename
        safe_filename = secure_filename(original_filename)
        
        # 如果secure_filename处理后文件名无效，使用时间戳作为文件名
        if not safe_filename or safe_filename == '.json' or (safe_filename.startswith('.') and len(safe_filename) <= 5):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}.json"
        else:
            # 确保文件名以.json结尾
            if not safe_filename.lower().endswith('.json'):
                safe_filename = safe_filename + '.json'
            # 如果文件已存在，添加时间戳避免覆盖
            filepath = os.path.join(workflows_dir, safe_filename)
            if os.path.exists(filepath):
                name, ext = os.path.splitext(safe_filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{name}_{timestamp}{ext}"
        
        filename = safe_filename
        filepath = os.path.join(workflows_dir, filename)
        
        # 保存文件
        file.seek(0)  # 重置文件指针
        file.save(filepath)
        
        print(f"✅ 工作流文件上传成功: {filename} (原始文件名: {original_filename})")
        
        return jsonify({
            'status': 'success',
            'message': '工作流文件上传成功',
            'filename': filename,
            'original_filename': original_filename
        })
        
    except Exception as e:
        print(f"❌ 上传工作流文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500

# ============================================================================
# API模板管理API
# ============================================================================

@admin_styles_api_bp.route('/images/<int:image_id>/api-template', methods=['GET'])
@login_required
def get_api_template(image_id):
    """获取风格图片的API模板配置"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '数据库模型未初始化'}), 500
        
        # 获取APITemplate模型
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        APITemplate = test_server_module.APITemplate
        StyleImage = models['StyleImage']
        
        # 检查图片是否存在
        image = StyleImage.query.get(image_id)
        if not image:
            return jsonify({'status': 'error', 'message': '风格图片不存在'}), 404
        
        # 获取API模板（图片级别优先）
        # 注意：编辑时查询所有模板（包括 is_active=False），以便正确显示禁用状态
        api_template = APITemplate.query.filter_by(
            style_image_id=image_id
        ).first()
        
        if api_template:
            template_dict = api_template.to_dict()
            print(f"📥 返回API模板数据: api_config_id={template_dict.get('api_config_id')}, request_body_template={'存在' if template_dict.get('request_body_template') else '不存在'}")
            return jsonify({
                'status': 'success',
                'data': template_dict
            })
        else:
            print(f"⚠️ 未找到API模板，image_id={image_id}")
            return jsonify({
                'status': 'success',
                'data': None
            })
    
    except Exception as e:
        print(f"获取API模板失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取API模板失败: {str(e)}'}), 500


@admin_styles_api_bp.route('/images/<int:image_id>/api-template', methods=['POST'])
@login_required
def save_api_template(image_id):
    """保存风格图片的API模板配置"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '数据库模型未初始化'}), 500
        
        # 获取APITemplate模型
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APITemplate = test_server_module.APITemplate
        APIProviderConfig = test_server_module.APIProviderConfig
        StyleImage = models['StyleImage']
        
        # 检查图片是否存在
        image = StyleImage.query.get(image_id)
        if not image:
            return jsonify({'status': 'error', 'message': '风格图片不存在'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据为空'}), 400
        
        # 检查是否启用API模板
        enabled = data.get('enabled', False)
        # 注意：如果 request_body_template 存在（无论是请求中还是数据库中），说明是 API-ComfyUI 工作流配置，即使 enabled 为 false 也不删除
        if not enabled and not data.get('request_body_template'):
            # 如果禁用且请求中没有 request_body_template，检查数据库中是否已有 request_body_template
            existing_template = APITemplate.query.filter_by(style_image_id=image_id).first()
            if existing_template:
                # 如果数据库中已有 request_body_template，说明是 API-ComfyUI 工作流配置，不应该删除
                if existing_template.request_body_template:
                    print(f"⚠️ 检测到 request_body_template 存在，不删除API模板（API-ComfyUI工作流配置）")
                    # 只设置 is_active=False，不删除
                    existing_template.is_active = False
                    db.session.commit()
                    return jsonify({
                        'status': 'success',
                        'message': 'API模板已禁用（但保留API-ComfyUI工作流配置）'
                    })
                # 如果数据库中没有 request_body_template，可以删除
                db.session.delete(existing_template)
                db.session.commit()
                print(f"✅ 已删除API模板（因为 enabled=false 且没有 request_body_template）")
            return jsonify({
                'status': 'success',
                'message': 'API模板已禁用'
            })
        
        # 验证API配置是否存在（如果指定了）
        api_config_id = data.get('api_config_id')
        if api_config_id:
            api_config = APIProviderConfig.query.get(api_config_id)
            if not api_config:
                return jsonify({'status': 'error', 'message': 'API配置不存在'}), 400
        
        # 获取或创建API模板
        api_template = APITemplate.query.filter_by(style_image_id=image_id).first()
        if not api_template:
            api_template = APITemplate(style_image_id=image_id)
            db.session.add(api_template)
        
        # 更新字段
        if 'api_config_id' in data:
            api_template.api_config_id = data['api_config_id'] if data['api_config_id'] else None
        if 'model_name' in data:
            api_template.model_name = data['model_name'].strip() if data.get('model_name') else None
        if 'default_prompt' in data:
            api_template.default_prompt = data['default_prompt'].strip() if data.get('default_prompt') else None
        if 'prompts_json' in data:
            # 批量提示词（JSON格式）
            prompts_json = data.get('prompts_json')
            if prompts_json:
                if isinstance(prompts_json, str):
                    api_template.prompts_json = prompts_json
                else:
                    import json
                    api_template.prompts_json = json.dumps(prompts_json, ensure_ascii=False)
            else:
                api_template.prompts_json = None
        if 'default_size' in data:
            api_template.default_size = data['default_size']
        if 'default_aspect_ratio' in data:
            api_template.default_aspect_ratio = data['default_aspect_ratio']
        if 'points_cost' in data:
            api_template.points_cost = int(data['points_cost']) if data.get('points_cost') else 0
        if 'prompt_editable' in data:
            api_template.prompt_editable = data['prompt_editable']
        if 'size_editable' in data:
            api_template.size_editable = data['size_editable']
        if 'aspect_ratio_editable' in data:
            api_template.aspect_ratio_editable = data['aspect_ratio_editable']
        if 'enhance_prompt' in data:
            api_template.enhance_prompt = data['enhance_prompt']
        if 'upload_config' in data:
            # upload_config 可能是字符串（JSON）或对象
            upload_config = data.get('upload_config')
            if upload_config:
                if isinstance(upload_config, str):
                    api_template.upload_config = upload_config
                else:
                    import json
                    api_template.upload_config = json.dumps(upload_config, ensure_ascii=False)
            else:
                api_template.upload_config = None
        if 'request_body_template' in data:
            # request_body_template 可能是字符串（JSON）或对象
            request_body_template = data.get('request_body_template')
            if request_body_template:
                if isinstance(request_body_template, str):
                    api_template.request_body_template = request_body_template
                else:
                    api_template.request_body_template = json.dumps(request_body_template, ensure_ascii=False)
                print(f"✅ 保存 request_body_template: {api_template.request_body_template[:200]}...")  # 调试日志
            else:
                api_template.request_body_template = None
                print("⚠️ request_body_template 为空，设置为 None")
        
        # 更新 is_active 字段（根据 enabled 参数）
        if 'enabled' in data:
            api_template.is_active = data.get('enabled', False)
            print(f"✅ 更新API模板 is_active={api_template.is_active}")
        else:
            # 如果没有传递 enabled，默认设置为 True（向后兼容）
            api_template.is_active = True
        
        api_template.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'API模板保存成功',
            'data': api_template.to_dict()
        })
    
    except Exception as e:
        print(f"保存API模板失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'保存API模板失败: {str(e)}'}), 500


@admin_styles_api_bp.route('/images/<int:image_id>/api-template', methods=['DELETE'])
@login_required
def delete_api_template(image_id):
    """删除风格图片的API模板配置"""
    try:
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APITemplate = test_server_module.APITemplate
        
        api_template = APITemplate.query.filter_by(style_image_id=image_id).first()
        if api_template:
            db.session.delete(api_template)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'API模板删除成功'
        })
    
    except Exception as e:
        print(f"删除API模板失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.session.rollback()
        return jsonify({'status': 'error', 'message': f'删除API模板失败: {str(e)}'}), 500


@admin_styles_api_bp.route('/images/<int:image_id>/test-api', methods=['POST'])
@login_required
def test_api_template(image_id):
    """测试API模板"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '数据库模型未初始化'}), 500
        
        # 获取模型
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APITemplate = test_server_module.APITemplate
        APIProviderConfig = test_server_module.APIProviderConfig
        AITask = test_server_module.AITask
        StyleImage = models['StyleImage']
        
        # 检查图片是否存在
        image = StyleImage.query.get(image_id)
        if not image:
            return jsonify({'status': 'error', 'message': '风格图片不存在'}), 404
        
        # 获取API模板
        api_template = APITemplate.query.filter_by(style_image_id=image_id, is_active=True).first()
        if not api_template:
            return jsonify({'status': 'error', 'message': '未配置API模板'}), 400
        
        # 获取API配置
        api_config = None
        if api_template.api_config_id:
            api_config = APIProviderConfig.query.filter_by(id=api_template.api_config_id, is_active=True).first()
        
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
            if not api_config:
                api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config:
            return jsonify({'status': 'error', 'message': '未找到可用的API配置'}), 400
        
        # 处理上传的图片（支持多个上传入口）
        uploaded_images = []
        upload_config = None
        
        # 检查是否有upload_config
        upload_config_str = request.form.get('upload_config')
        if upload_config_str:
            try:
                upload_config = json.loads(upload_config_str)
                print(f"📋 检测到上传配置: {json.dumps(upload_config, ensure_ascii=False)}")
            except:
                pass
        
        if upload_config and upload_config.get('uploads'):
            # 多个上传入口：按key获取图片
            for upload_item in upload_config['uploads']:
                key = upload_item.get('key', 'default')
                cloud_url_key = f'cloud_image_url_{key}'
                image_key = f'image_{key}'
                
                if cloud_url_key in request.form:
                    # 使用云端URL
                    uploaded_images.append(request.form[cloud_url_key])
                    print(f"✅ 使用云端URL ({key}): {request.form[cloud_url_key]}")
                elif image_key in request.files:
                    # 使用上传的文件
                    file = request.files[image_key]
                    if file.filename:
                        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                        os.makedirs(uploads_dir, exist_ok=True)
                        temp_filename = f"test_api_{image_id}_{key}_{int(time.time())}.jpg"
                        temp_filepath = os.path.join(uploads_dir, temp_filename)
                        file.save(temp_filepath)
                        image_url = f"/uploads/{temp_filename}"
                        uploaded_images.append(image_url)
                        print(f"✅ 使用本地临时文件 ({key}): {image_url}")
        else:
            # 单个默认上传入口（向后兼容）
            cloud_image_url = request.form.get('cloud_image_url')
            
            if cloud_image_url:
                uploaded_images.append(cloud_image_url)
                print(f"✅ 使用前端已上传的云端URL: {cloud_image_url}")
            elif 'image' in request.files:
                file = request.files['image']
                if file.filename == '':
                    return jsonify({'status': 'error', 'message': '请上传测试图片'}), 400
                
                uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                temp_filename = f"test_api_{image_id}_{int(time.time())}.jpg"
                temp_filepath = os.path.join(uploads_dir, temp_filename)
                file.save(temp_filepath)
                image_url = f"/uploads/{temp_filename}"
                uploaded_images.append(image_url)
                print(f"✅ 使用本地临时文件: {image_url}")
        
        if not uploaded_images:
            return jsonify({'status': 'error', 'message': '请上传测试图片'}), 400
        
        # 获取提示词（API测试时，如果为空则使用批量提示词）
        prompt = request.form.get('prompt', '').strip()
        # 注意：如果prompt为空，create_api_task会优先使用批量提示词（prompts_json）
        
        # 创建常规订单信息
        import uuid
        import random
        from datetime import datetime
        
        Order = test_server_module.Order
        OrderImage = test_server_module.OrderImage
        
        # 生成测试订单号
        test_task_id = str(uuid.uuid4())
        order_number = f"TEST_{int(time.time() * 1000)}{random.randint(1000, 9999)}"
        
        # 获取风格图片信息
        style_image_name = image.name if image else '测试风格'
        style_category_name = image.category.name if image and image.category else '测试分类'
        
        # 创建Order记录
        test_order = Order(
            order_number=order_number,
            customer_name='测试用户',
            customer_phone='00000000000',
            style_name=style_image_name,
            product_name=f'{style_category_name} - {style_image_name}',
            price=0.0,  # 测试订单价格为0
            status='ai_processing',  # 测试订单状态为AI任务处理中（创建任务后会自动更新）
            source_type='admin_test',  # 标记为后台测试
            original_image=uploaded_images[0] if uploaded_images else '',  # 使用第一张上传的图片作为原图
            created_at=datetime.now()
        )
        db.session.add(test_order)
        db.session.flush()  # 获取order.id
        
        # 创建OrderImage记录（保存所有上传的图片）
        for idx, img_url in enumerate(uploaded_images):
            # 如果是本地路径，提取文件名
            if img_url.startswith('/uploads/'):
                img_path = img_url.replace('/uploads/', '')
            else:
                # 云端URL，保存完整URL
                img_path = img_url
            
            order_image = OrderImage(
                order_id=test_order.id,
                path=img_path,
                is_main=(idx == 0)  # 第一张图片设为主图
            )
            db.session.add(order_image)
        
        db.session.commit()
        print(f"✅ 创建测试订单成功: order_id={test_order.id}, order_number={order_number}")
        
        # 调用API服务
        from app.services.ai_provider_service import create_api_task
        
        # 使用真实订单ID和订单号
        create_api_task._test_order_id = test_order.id
        create_api_task._test_order_number = order_number
        
        success, task, error_message = create_api_task(
            style_image_id=image_id,
            prompt=prompt,
            image_size=api_template.default_size or '1K',
            aspect_ratio=api_template.default_aspect_ratio or 'auto',
            uploaded_images=uploaded_images,
            upload_config=upload_config,  # 传递upload_config
            api_config_id=api_config.id,
            db=db,
            AITask=AITask,
            APITemplate=APITemplate,
            APIProviderConfig=APIProviderConfig,
            StyleImage=StyleImage
        )
        
        if not success:
            # 如果任务创建失败，删除已创建的测试订单（可选，也可以保留用于调试）
            try:
                # 可以选择删除测试订单，或者保留用于调试
                # db.session.delete(test_order)
                # db.session.commit()
                print(f"⚠️ 测试任务创建失败，但保留测试订单用于调试: order_id={test_order.id}")
            except Exception as e:
                print(f"⚠️ 删除测试订单失败: {str(e)}")
            
            try:
                if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except:
                pass
            return jsonify({'status': 'error', 'message': error_message or '创建测试任务失败'}), 500
        
        # 从processing_log中获取API信息
        api_info = {}
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
            except:
                pass
        
        # 获取task_id（从comfyui_prompt_id或processing_log中）
        task_id = task.comfyui_prompt_id or api_info.get('task_id')
        
        # 检查是否是同步API
        is_sync_api = api_config.is_sync_api if hasattr(api_config, 'is_sync_api') else False
        
        # 如果是同步API且任务已完成，直接返回结果
        # 注意：不要删除temp_filepath，因为已经保存到OrderImage中了
        if is_sync_api and task.status == 'success' and task.output_image_path:
            # 不删除临时文件，因为已经保存到OrderImage中了
            pass
            return jsonify({
                'status': 'success',
                'message': '测试成功',
                'data': {
                    'task_id': task_id,
                    'is_sync_api': True,
                    'status': 'completed',
                    'result_image_url': task.output_image_path
                }
            })
        
        # 异步API，返回任务ID用于轮询
        return jsonify({
            'status': 'success',
            'message': '测试任务已创建',
            'data': {
                'task_id': task_id,
                'is_sync_api': False,
                'status': task.status
            }
        })
    
    except Exception as e:
        print(f"测试API模板失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'测试失败: {str(e)}'}), 500


@admin_styles_api_bp.route('/images/<int:image_id>/test-api-comfyui', methods=['POST'])
@login_required
def test_api_comfyui_template(image_id):
    """测试API-ComfyUI工作流模板"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '数据库模型未初始化'}), 500
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APITemplate = test_server_module.APITemplate
        APIProviderConfig = test_server_module.APIProviderConfig
        AITask = test_server_module.AITask
        StyleImage = models['StyleImage']
        
        # 检查图片是否存在
        image = StyleImage.query.get(image_id)
        if not image:
            return jsonify({'status': 'error', 'message': '风格图片不存在'}), 404
        
        # 获取API模板配置
        api_template = APITemplate.query.filter_by(style_image_id=image_id, is_active=True).first()
        if not api_template:
            return jsonify({'status': 'error', 'message': '未配置API-ComfyUI工作流模板'}), 400
        
        # 获取API配置
        api_config = None
        if api_template.api_config_id:
            api_config = APIProviderConfig.query.filter_by(id=api_template.api_config_id, is_active=True).first()
        
        if not api_config:
            return jsonify({'status': 'error', 'message': '未找到可用的API配置'}), 400
        
        # 检查是否是 runninghub-comfyui-workflow 类型
        if api_config.api_type != 'runninghub-comfyui-workflow':
            return jsonify({'status': 'error', 'message': '当前API配置不是 runninghub-comfyui-workflow 类型'}), 400
        
        # 处理上传的图片（支持多图）
        uploaded_images = []
        # 获取所有cloud_image_url（支持多图）
        cloud_image_urls = request.form.getlist('cloud_image_url')
        if not cloud_image_urls or len(cloud_image_urls) == 0:
            return jsonify({'status': 'error', 'message': '请上传测试图片'}), 400
        
        uploaded_images = cloud_image_urls
        
        # 获取提示词（API测试时，如果为空则使用批量提示词）
        prompt = request.form.get('prompt', '').strip()
        # 注意：如果prompt为空，create_api_task会优先使用批量提示词（prompts_json）
        
        # 创建常规订单信息
        import uuid
        import random
        from datetime import datetime
        
        Order = test_server_module.Order
        OrderImage = test_server_module.OrderImage
        
        # 生成测试订单号
        test_task_id = str(uuid.uuid4())
        order_number = f"TEST_{int(time.time() * 1000)}{random.randint(1000, 9999)}"
        
        # 获取风格图片信息
        style_image_name = image.name if image else '测试风格'
        style_category_name = image.category.name if image and image.category else '测试分类'
        
        # 创建Order记录
        test_order = Order(
            order_number=order_number,
            customer_name='测试用户',
            customer_phone='00000000000',
            style_name=style_image_name,
            product_name=f'{style_category_name} - {style_image_name}',
            price=0.0,  # 测试订单价格为0
            status='ai_processing',  # 测试订单状态为AI任务处理中（创建任务后会自动更新）
            source_type='admin_test',  # 标记为后台测试
            original_image=uploaded_images[0] if uploaded_images else '',  # 使用第一张上传的图片作为原图
            created_at=datetime.now()
        )
        db.session.add(test_order)
        db.session.flush()  # 获取order.id
        
        # 创建OrderImage记录（保存所有上传的图片）
        for idx, img_url in enumerate(uploaded_images):
            # 如果是本地路径，提取文件名
            if img_url.startswith('/uploads/'):
                img_path = img_url.replace('/uploads/', '')
            else:
                # 云端URL，保存完整URL
                img_path = img_url
            
            order_image = OrderImage(
                order_id=test_order.id,
                path=img_path,
                is_main=(idx == 0)  # 第一张图片设为主图
            )
            db.session.add(order_image)
        
        db.session.commit()
        print(f"✅ 创建测试订单成功: order_id={test_order.id}, order_number={order_number}")
        
        # 调用API服务
        from app.services.ai_provider_service import create_api_task
        
        # 使用真实订单ID和订单号
        create_api_task._test_order_id = test_order.id
        create_api_task._test_order_number = order_number
        
        success, task, error_message = create_api_task(
            style_image_id=image_id,
            prompt=prompt,
            image_size=None,  # RunningHub ComfyUI 工作流不使用 size
            aspect_ratio=None,  # RunningHub ComfyUI 工作流不使用 aspect_ratio
            uploaded_images=uploaded_images,
            upload_config=None,
            api_config_id=api_config.id,
            db=db,
            AITask=AITask,
            APITemplate=APITemplate,
            APIProviderConfig=APIProviderConfig,
            StyleImage=StyleImage
        )
        
        if not success:
            # 如果任务创建失败，删除已创建的测试订单（可选，也可以保留用于调试）
            try:
                # 可以选择删除测试订单，或者保留用于调试
                # db.session.delete(test_order)
                # db.session.commit()
                print(f"⚠️ 测试任务创建失败，但保留测试订单用于调试: order_id={test_order.id}")
            except Exception as e:
                print(f"⚠️ 删除测试订单失败: {str(e)}")
            return jsonify({'status': 'error', 'message': error_message or '创建测试任务失败'}), 500
        
        # 从processing_log中获取API信息
        api_info = {}
        if task.processing_log:
            try:
                api_info = json.loads(task.processing_log)
            except:
                pass
        
        # 获取task_id
        task_id = task.comfyui_prompt_id or api_info.get('api_task_id') or api_info.get('task_id')
        
        # 检查是否是同步API
        is_sync_api = api_config.is_sync_api if hasattr(api_config, 'is_sync_api') else False
        
        # 如果是同步API且任务已完成，直接返回结果
        if is_sync_api and task.status == 'success' and task.output_image_path:
            return jsonify({
                'status': 'success',
                'message': '测试成功',
                'data': {
                    'task_id': task_id,
                    'is_sync_api': True,
                    'status': 'completed',
                    'result_image_url': task.output_image_path
                }
            })
        
        # 异步API，返回任务ID用于轮询
        return jsonify({
            'status': 'success',
            'message': '测试任务已创建',
            'data': {
                'task_id': task_id,
                'is_sync_api': False,
                'status': task.status
            }
        })
    
    except Exception as e:
        print(f"测试API-ComfyUI工作流失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'测试失败: {str(e)}'}), 500


@admin_styles_api_bp.route('/images/test-api-comfyui/task/<task_id>', methods=['GET'])
@login_required
def get_test_api_comfyui_task_status(task_id):
    """获取API-ComfyUI工作流测试任务状态"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '数据库模型未初始化'}), 500
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        APIProviderConfig = test_server_module.APIProviderConfig
        
        # 查找任务（通过 comfyui_prompt_id 或 notes 中的 T8_API_TASK_ID）
        task = None
        if task_id.startswith('TEST_'):
            # 测试任务，通过 order_number 查找
            task = AITask.query.filter_by(order_number=task_id).first()
        else:
            # 通过 comfyui_prompt_id 查找
            task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
            if not task:
                # 通过 notes 中的 T8_API_TASK_ID 查找
                task = AITask.query.filter(AITask.notes.like(f'%T8_API_TASK_ID:{task_id}%')).first()
        
        if not task:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404
        
        # 获取API配置
        api_config = None
        if task.notes and 'T8_API_TASK_ID:' in task.notes:
            # RunningHub API，需要查询结果
            api_task_id = task.notes.split('T8_API_TASK_ID:')[1].split('|')[0].strip()
            
            # 从 processing_log 中获取 API 配置信息
            api_info = {}
            if task.processing_log:
                try:
                    api_info = json.loads(task.processing_log)
                except:
                    pass
            
            # 获取API配置（从任务关联的配置或默认配置）
            api_config_id = api_info.get('api_config_id')
            if api_config_id:
                api_config = APIProviderConfig.query.get(api_config_id)
            
            if not api_config:
                api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
            
            if api_config and api_config.api_type in ['runninghub-rhart-edit', 'runninghub-comfyui-workflow']:
                # RunningHub API，查询任务结果
                host = api_config.host_domestic or api_config.host_overseas
                result_endpoint = api_config.result_endpoint or '/openapi/v2/task/outputs'
                result_url = f"{host.rstrip('/')}{result_endpoint}"
                
                headers = {
                    'Authorization': f'Bearer {api_config.api_key}',
                    'Content-Type': 'application/json'
                }
                
                try:
                    response = requests.get(result_url, params={'taskId': api_task_id}, headers=headers, timeout=(10, 30))
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get('status', '')
                        
                        if status == 'SUCCESS' and result.get('results'):
                            # 任务完成，更新任务状态
                            task.status = 'success'
                            if result['results'] and len(result['results']) > 0:
                                image_url = result['results'][0].get('url')
                                if image_url:
                                    task.output_image_path = image_url
                                    task.completed_at = datetime.now()
                                    db.session.commit()
                            
                            return jsonify({
                                'status': 'success',
                                'data': {
                                    'task_id': api_task_id,
                                    'status': 'completed',
                                    'result_image_url': task.output_image_path
                                }
                            })
                        elif status == 'FAILED':
                            task.status = 'failed'
                            task.error_message = result.get('errorMessage', '任务执行失败')
                            db.session.commit()
                            
                            return jsonify({
                                'status': 'success',
                                'data': {
                                    'task_id': api_task_id,
                                    'status': 'failed',
                                    'error_message': result.get('errorMessage', '任务执行失败')
                                }
                            })
                        else:
                            return jsonify({
                                'status': 'success',
                                'data': {
                                    'task_id': api_task_id,
                                    'status': 'processing',
                                    'api_status': status
                                }
                            })
                    else:
                        return jsonify({
                            'status': 'success',
                            'data': {
                                'task_id': api_task_id,
                                'status': 'processing',
                                'message': f'查询API状态失败: HTTP {response.status_code}'
                            }
                        })
                except Exception as e:
                    print(f"查询RunningHub API结果失败: {str(e)}")
                    return jsonify({
                        'status': 'success',
                        'data': {
                            'task_id': api_task_id,
                            'status': task.status,
                            'message': f'查询失败: {str(e)}'
                        }
                    })
        
        # 返回任务状态
        return jsonify({
            'status': 'success',
            'data': {
                'task_id': task.comfyui_prompt_id or task_id,
                'status': task.status,
                'result_image_url': task.output_image_path if task.status == 'success' else None,
                'error_message': task.error_message if task.status == 'failed' else None
            }
        })
    
    except Exception as e:
        print(f"获取API-ComfyUI工作流测试任务状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取任务状态失败: {str(e)}'}), 500


@admin_styles_api_bp.route('/images/upload-to-grsai', methods=['POST'])
@login_required
def upload_image_to_grsai():
    """上传图片到grsai文件服务器（用于API测试）"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': '请上传图片'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '请选择图片文件'}), 400
        
        # 获取文件扩展名
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return jsonify({'status': 'error', 'message': '不支持的图片格式'}), 400
        
        # 获取API配置（用于获取api_key）
        models = get_models()
        if not models:
            return jsonify({'status': 'error', 'message': '数据库模型未初始化'}), 500
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        APIProviderConfig = test_server_module.APIProviderConfig
        
        # 获取API配置（优先使用默认配置）
        api_config = APIProviderConfig.query.filter_by(is_active=True, is_default=True).first()
        if not api_config:
            api_config = APIProviderConfig.query.filter_by(is_active=True).first()
        
        if not api_config or not api_config.api_key:
            return jsonify({
                'status': 'error',
                'message': '未找到可用的API配置或API Key，请先在API服务商配置中设置API Key'
            }), 400
        
        print(f"第一步：获取上传token（文件扩展名: {ext})")
        
        # 第一步：获取上传token（使用POST方法，需要Authorization header和JSON数据）
        token_url = "https://grsai.dakka.com.cn/client/resource/newUploadTokenZH"
        print(f"📤 请求上传token URL: {token_url}")
        
        # 禁用代理（grsai是国内服务器，直连速度更快）
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        has_proxy = any(os.environ.get(var) for var in proxy_env_vars)
        proxies = {'http': None, 'https': None}  # 强制禁用代理
        if has_proxy:
            print(f"📤 代理设置: 已强制禁用（grsai是国内服务器，直连速度更快）")
        
        # 使用POST方法，添加Authorization header和JSON数据
        headers = {
            "Authorization": f"Bearer {api_config.api_key}",
            "Content-Type": "application/json"
        }
        data = {"sux": ext}
        
        token_response = requests.post(
            url=token_url,
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=30
        )
        print(f"📤 Token请求响应状态码: {token_response.status_code}")
        
        if token_response.status_code != 200:
            error_text = token_response.text[:500] if hasattr(token_response, 'text') else str(token_response.content[:500])
            return jsonify({
                'status': 'error',
                'message': f'获取上传token失败: HTTP {token_response.status_code}',
                'error': error_text
            }), 500
        
        token_result = token_response.json()
        print(f"📤 Token响应内容: {token_result}")
        
        if token_result.get('code') != 0:
            return jsonify({
                'status': 'error',
                'message': f"获取上传token失败: {token_result.get('msg', '未知错误')}"
            }), 500
        
        upload_info = token_result.get('data', {})
        upload_url = upload_info.get('url')  # https://up-z2.qiniup.com
        token = upload_info.get('token')
        key = upload_info.get('key')  # 文件key
        domain = upload_info.get('domain')  # https://grsai-file.dakka.com.cn
        
        if not all([upload_url, token, key, domain]):
            return jsonify({
                'status': 'error',
                'message': '上传token响应数据不完整'
            }), 500
        
        print(f"✅ 获取上传token成功")
        print(f"第二步：上传文件到 {upload_url}")
        
        # 第二步：上传文件到七牛云
        print(f"📤 上传文件到: {upload_url}")
        print(f"📤 代理设置: 已强制禁用（grsai是国内服务器，直连速度更快）")
        
        # 读取文件内容
        file_content = file.read()
        file_size = len(file_content)
        print(f"📤 文件大小: {file_size / 1024 / 1024:.2f} MB")
        
        # 准备上传数据（参考bk-photo-v4的实现）
        # 注意：token和key应该放在data中，file放在files中
        upload_data = {
            'token': token,
            'key': key
        }
        upload_files = {
            'file': (filename, file_content, f'image/{ext}')
        }
        
        upload_response = requests.post(
            url=upload_url,
            data=upload_data,
            files=upload_files,
            proxies=proxies,
            timeout=120
        )
        print(f"📤 上传响应状态码: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            error_text = upload_response.text[:500] if hasattr(upload_response, 'text') else str(upload_response.content[:500])
            return jsonify({
                'status': 'error',
                'message': f'文件上传失败: HTTP {upload_response.status_code}',
                'error': error_text
            }), 500
        
        # 构建文件URL
        file_url = f"{domain}/{key}"
        print(f"文件上传到grsai成功: {file_url}")
        
        return jsonify({
            'status': 'success',
            'message': '图片上传成功',
            'data': {
                'url': file_url,
                'key': key,
                'domain': domain
            }
        })
    
    except Exception as e:
        print(f"上传图片到grsai失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500


@admin_styles_api_bp.route('/images/test-api/task/<task_id>', methods=['GET'])
@login_required
def get_api_test_task_status(task_id):
    """获取API测试任务状态"""
    try:
        if current_user.role not in ['admin', 'operator']:
            return jsonify({'status': 'error', 'message': '权限不足'}), 403
        
        import sys
        if 'test_server' not in sys.modules:
            return jsonify({'status': 'error', 'message': '数据库未初始化'}), 500
        
        test_server_module = sys.modules['test_server']
        db = test_server_module.db
        AITask = test_server_module.AITask
        
        # 获取任务（使用comfyui_prompt_id存储task_id）
        task = AITask.query.filter_by(comfyui_prompt_id=task_id).first()
        if not task:
            return jsonify({'status': 'error', 'message': '任务不存在'}), 404
        
        # 检查任务状态
        if task.status == 'success' and task.output_image_path:
            return jsonify({
                'status': 'success',
                'data': {
                    'status': 'completed',
                    'result_image_url': task.output_image_path
                }
            })
        elif task.status == 'failed':
            return jsonify({
                'status': 'success',
                'data': {
                    'status': 'failed',
                    'error_message': task.error_message or '任务失败'
                }
            })
        else:
            return jsonify({
                'status': 'success',
                'data': {
                    'status': 'processing',
                    'message': '任务处理中...'
                }
            })
    
    except Exception as e:
        print(f"获取测试任务状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'获取任务状态失败: {str(e)}'}), 500