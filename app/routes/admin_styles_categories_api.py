# -*- coding: utf-8 -*-
"""
管理后台风格分类API路由模块
提供风格分类的CRUD操作
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
import os
import shutil
from werkzeug.utils import secure_filename

from app.utils.admin_helpers import get_models, get_style_code_helpers

# 创建蓝图（不设置url_prefix，因为会注册到主蓝图下）
admin_styles_categories_bp = Blueprint('admin_styles_categories', __name__)

# ============================================================================
# 风格分类API（一级分类）
# ============================================================================

@admin_styles_categories_bp.route('/categories', methods=['GET'])
def admin_get_categories():
    """获取所有风格分类"""
    try:
        models = get_models(['StyleCategory', 'StyleSubcategory'])
        if not models or not models.get('StyleCategory'):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        StyleSubcategory = models.get('StyleSubcategory')
        categories = StyleCategory.query.order_by(StyleCategory.sort_order).all()
        result = []
        for category in categories:
            # 获取该分类下的所有二级分类
            subcategories_data = []
            if StyleSubcategory:
                subcategories = StyleSubcategory.query.filter_by(
                    category_id=category.id
                ).order_by(StyleSubcategory.sort_order).all()
                for subcategory in subcategories:
                    subcategories_data.append({
                        'id': subcategory.id,
                        'category_id': subcategory.category_id,
                        'name': subcategory.name,
                        'code': subcategory.code,
                        'icon': subcategory.icon,
                        'cover_image': subcategory.cover_image,
                        'sort_order': subcategory.sort_order,
                        'is_active': subcategory.is_active,
                        'created_at': subcategory.created_at.isoformat() if subcategory.created_at else None
                    })
            
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
                # 二级分类列表
                'subcategories': subcategories_data,
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

@admin_styles_categories_bp.route('/categories', methods=['POST'])
def admin_create_category():
    """创建风格分类"""
    try:
        models = get_models(['StyleCategory', 'db'])
        if not models or not models.get('StyleCategory'):
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

@admin_styles_categories_bp.route('/categories/<int:category_id>', methods=['PUT'])
def admin_update_category(category_id):
    """更新风格分类"""
    try:
        models = get_models(['StyleCategory', 'db'])
        if not models or not models.get('StyleCategory'):
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

@admin_styles_categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    """删除风格分类"""
    try:
        models = get_models(['StyleCategory', 'StyleImage', 'db'])
        if not models or not models.get('StyleCategory'):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleCategory = models['StyleCategory']
        StyleImage = models.get('StyleImage')
        db = models['db']
        
        category = StyleCategory.query.get_or_404(category_id)
        
        # 删除分类下的所有图片
        if StyleImage:
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
# 风格二级分类API
# ============================================================================

@admin_styles_categories_bp.route('/subcategories', methods=['GET'])
def admin_get_subcategories():
    """获取所有风格二级分类，或根据category_id获取指定一级分类下的二级分类"""
    try:
        models = get_models(['StyleSubcategory', 'StyleCategory'])
        if not models or not models.get('StyleSubcategory'):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleSubcategory = models['StyleSubcategory']
        StyleCategory = models.get('StyleCategory')
        
        category_id = request.args.get('category_id', type=int)
        
        if category_id:
            # 获取指定一级分类下的二级分类
            subcategories = StyleSubcategory.query.filter_by(category_id=category_id).order_by(StyleSubcategory.sort_order).all()
        else:
            # 获取所有二级分类
            subcategories = StyleSubcategory.query.order_by(StyleSubcategory.sort_order).all()
        
        result = []
        for subcategory in subcategories:
            subcategory_data = {
                'id': subcategory.id,
                'category_id': subcategory.category_id,
                'name': subcategory.name,
                'code': subcategory.code,
                'icon': subcategory.icon,
                'cover_image': subcategory.cover_image,
                'sort_order': subcategory.sort_order,
                'is_active': subcategory.is_active,
                'created_at': subcategory.created_at.isoformat() if subcategory.created_at else None
            }
            
            # 如果StyleCategory模型存在，加载一级分类信息
            if StyleCategory and subcategory.category:
                subcategory_data['category_name'] = subcategory.category.name
                subcategory_data['category_code'] = subcategory.category.code
            
            result.append(subcategory_data)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取二级分类失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取二级分类失败'
        }), 500

@admin_styles_categories_bp.route('/subcategories', methods=['POST'])
def admin_create_subcategory():
    """创建风格二级分类"""
    try:
        models = get_models(['StyleSubcategory', 'db'])
        if not models or not models.get('StyleSubcategory'):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleSubcategory = models['StyleSubcategory']
        db = models['db']
        
        data = request.get_json()
        
        # 检查必填字段
        required_fields = ['name', 'code', 'category_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'缺少必要字段: {field}'}), 400
        
        # 检查代码是否重复（在同一一级分类下）
        existing = StyleSubcategory.query.filter_by(
            category_id=data['category_id'],
            code=data['code']
        ).first()
        if existing:
            return jsonify({'status': 'error', 'message': '该一级分类下已存在相同代码的二级分类'}), 400
        
        # 创建二级分类
        subcategory = StyleSubcategory(
            category_id=data['category_id'],
            name=data['name'],
            code=data['code'],
            icon=data.get('icon', ''),
            cover_image=data.get('cover_image', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(subcategory)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '二级分类创建成功',
            'data': {
                'id': subcategory.id,
                'name': subcategory.name,
                'code': subcategory.code
            }
        })
        
    except Exception as e:
        print(f"创建二级分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '创建二级分类失败'
        }), 500

@admin_styles_categories_bp.route('/subcategories/<int:subcategory_id>', methods=['PUT'])
def admin_update_subcategory(subcategory_id):
    """更新风格二级分类"""
    try:
        models = get_models(['StyleSubcategory', 'db'])
        if not models or not models.get('StyleSubcategory'):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleSubcategory = models['StyleSubcategory']
        db = models['db']
        
        subcategory = StyleSubcategory.query.get_or_404(subcategory_id)
        data = request.get_json()
        
        # 检查代码是否重复（排除自己，在同一一级分类下）
        if data.get('code') and data['code'] != subcategory.code:
            existing = StyleSubcategory.query.filter_by(
                category_id=data.get('category_id', subcategory.category_id),
                code=data['code']
            ).first()
            if existing:
                return jsonify({'status': 'error', 'message': '该一级分类下已存在相同代码的二级分类'}), 400
        
        # 更新字段
        if 'category_id' in data:
            subcategory.category_id = data['category_id']
        if 'name' in data:
            subcategory.name = data['name']
        if 'code' in data:
            subcategory.code = data['code']
        if 'icon' in data:
            subcategory.icon = data['icon']
        if 'cover_image' in data:
            subcategory.cover_image = data['cover_image']
        if 'sort_order' in data:
            subcategory.sort_order = data['sort_order']
        if 'is_active' in data:
            subcategory.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '二级分类更新成功'
        })
        
    except Exception as e:
        print(f"更新二级分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新二级分类失败'
        }), 500

@admin_styles_categories_bp.route('/subcategories/<int:subcategory_id>', methods=['DELETE'])
def admin_delete_subcategory(subcategory_id):
    """删除风格二级分类"""
    try:
        models = get_models(['StyleSubcategory', 'StyleImage', 'db'])
        if not models or not models.get('StyleSubcategory'):
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        StyleSubcategory = models['StyleSubcategory']
        StyleImage = models.get('StyleImage')
        db = models['db']
        
        subcategory = StyleSubcategory.query.get_or_404(subcategory_id)
        
        # 删除二级分类下的所有图片的关联（将subcategory_id设为NULL）
        if StyleImage:
            StyleImage.query.filter_by(subcategory_id=subcategory_id).update({'subcategory_id': None})
        
        # 删除二级分类
        db.session.delete(subcategory)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '二级分类删除成功'
        })
        
    except Exception as e:
        print(f"删除二级分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '删除二级分类失败'
        }), 500

@admin_styles_categories_bp.route('/categories/upload-cover-image', methods=['POST'])
def admin_upload_category_cover_image():
    """上传一级分类封面图片（也用于二级分类）"""
    try:
        if 'file' not in request.files and 'image' not in request.files:
            return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
        
        file = request.files.get('file') or request.files.get('image')
        if not file or file.filename == '':
            return jsonify({'status': 'error', 'message': '文件名为空'}), 400
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        filename = file.filename.lower()
        if not any(filename.endswith(f'.{ext}') for ext in allowed_extensions):
            return jsonify({'status': 'error', 'message': '不支持的文件格式，仅支持 PNG、JPG、JPEG、GIF、WEBP'}), 400
        
        # 保存文件
        upload_folder = 'static/uploads/categories'
        os.makedirs(upload_folder, exist_ok=True)
        
        # 生成安全的文件名
        safe_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{safe_filename}"
        filepath = os.path.join(upload_folder, filename)
        
        file.save(filepath)
        
        # 返回相对路径
        image_url = f"/{upload_folder}/{filename}"
        
        return jsonify({
            'status': 'success',
            'message': '上传成功',
            'data': {
                'image_url': image_url,
                'url': image_url  # 兼容字段
            }
        })
        
    except Exception as e:
        print(f"上传封面图片失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '上传失败'
        }), 500
