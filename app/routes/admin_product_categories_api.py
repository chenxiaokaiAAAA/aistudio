# -*- coding: utf-8 -*-
"""
产品分类管理API
用于创建和管理产品的一级分类和二级分类
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import sys
import os
import uuid
import re

# 创建蓝图
admin_product_categories_api_bp = Blueprint('admin_product_categories_api', __name__)

def get_models():
    """获取数据库模型（延迟导入）"""
    if 'test_server' not in sys.modules:
        return None
    test_server_module = sys.modules['test_server']
    return {
        'db': test_server_module.db,
        'ProductCategory': getattr(test_server_module, 'ProductCategory', None),
        'ProductSubcategory': getattr(test_server_module, 'ProductSubcategory', None),
    }

@admin_product_categories_api_bp.route('/admin/product-categories', methods=['GET'])
@login_required
def admin_product_categories_page():
    """产品分类管理页面（已废弃，重定向到产品管理页面）"""
    from flask import redirect, url_for
    return redirect(url_for('admin_products.admin_products'))

@admin_product_categories_api_bp.route('/api/admin/product-categories', methods=['GET'])
@login_required
def admin_get_categories():
    """获取所有一级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductCategory = models['ProductCategory']
        if not ProductCategory:
            return jsonify({
                'status': 'error',
                'message': '产品分类模型未找到，请先运行数据库迁移脚本'
            }), 500
        
        categories = ProductCategory.query.order_by(ProductCategory.sort_order.asc()).all()
        result = []
        for category in categories:
            result.append({
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'icon': category.icon or '',
                'image_url': category.image_url or '',
                'sort_order': category.sort_order or 0,
                'is_active': category.is_active,
                'style_redirect_page': category.style_redirect_page if category.style_redirect_page is not None else '',  # 确保 None 转换为空字符串
                'created_at': category.created_at.isoformat() if category.created_at else ''
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取产品分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取产品分类失败'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-categories/upload-image', methods=['POST'])
@login_required
def admin_upload_category_image():
    """上传分类图片"""
    try:
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '文件名为空'}), 400
        
        from werkzeug.utils import secure_filename
        import uuid
        from flask import current_app
        
        # 处理文件名，移除所有特殊字符和空格
        original_filename = file.filename
        # 先使用secure_filename处理
        filename = secure_filename(original_filename)
        if not filename:
            # 如果secure_filename返回空，手动处理
            filename = original_filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
            # 移除所有非ASCII字符和特殊字符，只保留字母、数字、点、下划线、连字符
            filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
            if not filename:
                filename = 'category_image'
        
        # 确保文件名有扩展名
        if '.' not in filename:
            # 从原始文件名提取扩展名
            if '.' in original_filename:
                ext = original_filename.rsplit('.', 1)[1]
                # 只保留安全的扩展名
                ext = re.sub(r'[^a-zA-Z0-9]', '', ext)
                if ext:
                    filename = f"{filename}.{ext.lower()}"
            else:
                # 根据MIME类型添加扩展名
                if file.content_type:
                    ext_map = {
                        'image/png': 'png',
                        'image/jpeg': 'jpg',
                        'image/jpg': 'jpg',
                        'image/gif': 'gif',
                        'image/webp': 'webp'
                    }
                    ext = ext_map.get(file.content_type, 'png')
                    filename = f"{filename}.{ext}"
        
        # 添加时间戳和UUID确保唯一性
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
        
        # 保存到static/images/categories目录
        static_categories_dir = os.path.join(current_app.root_path, 'static', 'images', 'categories')
        os.makedirs(static_categories_dir, exist_ok=True)
        
        file_path = os.path.join(static_categories_dir, unique_filename)
        file.save(file_path)
        
        # 返回相对路径
        image_url = f"/static/images/categories/{unique_filename}"
        
        return jsonify({
            'status': 'success',
            'message': '图片上传成功',
            'data': {
                'image_url': image_url
            }
        })
        
    except Exception as e:
        print(f"上传分类图片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-categories', methods=['POST'])
@login_required
def admin_create_category():
    """创建一级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductCategory = models['ProductCategory']
        db = models['db']
        
        if not ProductCategory:
            return jsonify({
                'status': 'error',
                'message': '产品分类模型未找到'
            }), 500
        
        data = request.get_json()
        
        # 检查必填字段
        if not data.get('name'):
            return jsonify({'status': 'error', 'message': '分类名称不能为空'}), 400
        if not data.get('code'):
            return jsonify({'status': 'error', 'message': '分类代码不能为空'}), 400
        
        # 检查代码是否重复
        existing = ProductCategory.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'status': 'error', 'message': '分类代码已存在'}), 400
        
        # 创建分类
        category = ProductCategory(
            name=data['name'],
            code=data['code'],
            icon=data.get('icon', ''),
            image_url=data.get('image_url', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True),
            style_redirect_page=data.get('style_redirect_page') or None
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
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建分类失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-categories/<int:category_id>', methods=['GET'])
@login_required
def admin_get_category(category_id):
    """获取单个一级分类详情"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductCategory = models['ProductCategory']
        
        if not ProductCategory:
            return jsonify({
                'status': 'error',
                'message': '产品分类模型未找到'
            }), 500
        
        category = ProductCategory.query.get(category_id)
        if not category:
            return jsonify({
                'status': 'error',
                'message': '分类不存在'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'icon': category.icon or '',
                'image_url': category.image_url or '',
                'sort_order': category.sort_order or 0,
                'is_active': category.is_active,
                'style_redirect_page': category.style_redirect_page if category.style_redirect_page is not None else ''
            }
        })
        
    except Exception as e:
        print(f"获取分类详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-categories/<int:category_id>', methods=['PUT'])
@login_required
def admin_update_category(category_id):
    """更新一级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductCategory = models['ProductCategory']
        db = models['db']
        
        if not ProductCategory:
            return jsonify({
                'status': 'error',
                'message': '产品分类模型未找到'
            }), 500
        
        category = ProductCategory.query.get_or_404(category_id)
        data = request.get_json()
        
        print(f"更新分类 {category_id}，接收到的数据: {data}")  # 调试日志
        print(f"接收到的数据键列表: {list(data.keys()) if data else 'None'}")  # 调试日志
        print(f"是否包含 style_redirect_page: {'style_redirect_page' in data if data else False}")  # 调试日志
        if data and 'style_redirect_page' in data:
            print(f"style_redirect_page 的值: {repr(data.get('style_redirect_page'))}")  # 调试日志
        
        # 更新字段
        if 'name' in data:
            category.name = data['name']
        if 'code' in data:
            # 检查代码是否与其他分类重复
            existing = ProductCategory.query.filter_by(code=data['code']).first()
            if existing and existing.id != category_id:
                return jsonify({'status': 'error', 'message': '分类代码已存在'}), 400
            category.code = data['code']
        if 'icon' in data:
            category.icon = data['icon']
        if 'image_url' in data:
            category.image_url = data['image_url']
        if 'sort_order' in data:
            category.sort_order = data.get('sort_order', 0)
        if 'is_active' in data:
            category.is_active = data['is_active']
        if 'style_redirect_page' in data:
            style_redirect_value = data.get('style_redirect_page')
            # 处理 style_redirect_page 字段：如果值为 None、空字符串或只包含空白字符，设置为 None；否则使用原值
            if style_redirect_value is None:
                category.style_redirect_page = None
            elif isinstance(style_redirect_value, str) and style_redirect_value.strip():
                category.style_redirect_page = style_redirect_value.strip()
            else:
                category.style_redirect_page = None
            print(f"设置 style_redirect_page: {repr(style_redirect_value)} -> {repr(category.style_redirect_page)}")  # 调试日志
        else:
            # 如果没有传递该字段，保持原值不变
            print(f"未传递 style_redirect_page 字段，保持原值: {category.style_redirect_page}")  # 调试日志
        
        db.session.commit()
        
        # 验证保存后的值
        db.session.refresh(category)
        print(f"保存后的 style_redirect_page 值: {category.style_redirect_page}")  # 调试日志
        
        return jsonify({
            'status': 'success',
            'message': '分类更新成功',
            'data': {
                'id': category.id,
                'name': category.name,
                'code': category.code
            }
        })
        
    except Exception as e:
        print(f"更新分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新分类失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-categories/<int:category_id>', methods=['DELETE'])
@login_required
def admin_delete_category(category_id):
    """删除一级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductCategory = models['ProductCategory']
        db = models['db']
        
        if not ProductCategory:
            return jsonify({
                'status': 'error',
                'message': '产品分类模型未找到'
            }), 500
        
        category = ProductCategory.query.get_or_404(category_id)
        
        # 检查是否有产品使用此分类
        if hasattr(category, 'products') and category.products:
            return jsonify({
                'status': 'error',
                'message': '该分类下还有产品，无法删除'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类删除成功'
        })
        
    except Exception as e:
        print(f"删除分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除分类失败: {str(e)}'
        }), 500

# ==================== 二级分类管理 ====================

@admin_product_categories_api_bp.route('/api/admin/product-subcategories', methods=['GET'])
@login_required
def admin_get_subcategories():
    """获取所有二级分类（可按一级分类ID过滤）"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductSubcategory = models['ProductSubcategory']
        if not ProductSubcategory:
            return jsonify({
                'status': 'error',
                'message': '产品二级分类模型未找到'
            }), 500
        
        category_id = request.args.get('category_id')
        query = ProductSubcategory.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        subcategories = query.order_by(ProductSubcategory.sort_order.asc()).all()
        result = []
        for subcat in subcategories:
            result.append({
                'id': subcat.id,
                'category_id': subcat.category_id,
                'name': subcat.name,
                'code': subcat.code,
                'icon': subcat.icon or '',
                'image_url': subcat.image_url or '',
                'sort_order': subcat.sort_order or 0,
                'is_active': subcat.is_active,
                'created_at': subcat.created_at.isoformat() if subcat.created_at else ''
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取二级分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '获取二级分类失败'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-subcategories', methods=['POST'])
@login_required
def admin_create_subcategory():
    """创建二级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductCategory = models['ProductCategory']
        ProductSubcategory = models['ProductSubcategory']
        db = models['db']
        
        if not ProductSubcategory:
            return jsonify({
                'status': 'error',
                'message': '产品二级分类模型未找到'
            }), 500
        
        data = request.get_json()
        
        # 检查必填字段
        if not data.get('category_id'):
            return jsonify({'status': 'error', 'message': '一级分类ID不能为空'}), 400
        if not data.get('name'):
            return jsonify({'status': 'error', 'message': '分类名称不能为空'}), 400
        if not data.get('code'):
            return jsonify({'status': 'error', 'message': '分类代码不能为空'}), 400
        
        # 检查一级分类是否存在
        if ProductCategory:
            category = ProductCategory.query.get(data['category_id'])
            if not category:
                return jsonify({'status': 'error', 'message': '一级分类不存在'}), 400
        
        # 检查同一一级分类下代码是否重复
        existing = ProductSubcategory.query.filter_by(
            category_id=data['category_id'],
            code=data['code']
        ).first()
        if existing:
            return jsonify({'status': 'error', 'message': '该一级分类下已存在相同代码的二级分类'}), 400
        
        # 创建二级分类
        subcategory = ProductSubcategory(
            category_id=data['category_id'],
            name=data['name'],
            code=data['code'],
            icon=data.get('icon', ''),
            image_url=data.get('image_url', ''),
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
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建二级分类失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-categories/subcategories/<int:subcategory_id>', methods=['GET'])
@login_required
def admin_get_subcategory(subcategory_id):
    """获取单个二级分类详情"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductSubcategory = models['ProductSubcategory']
        
        if not ProductSubcategory:
            return jsonify({
                'status': 'error',
                'message': '产品二级分类模型未找到'
            }), 500
        
        subcategory = ProductSubcategory.query.get_or_404(subcategory_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': subcategory.id,
                'category_id': subcategory.category_id,
                'name': subcategory.name,
                'code': subcategory.code,
                'icon': subcategory.icon or '',
                'image_url': subcategory.image_url or '',
                'sort_order': subcategory.sort_order or 0,
                'is_active': subcategory.is_active,
                'created_at': subcategory.created_at.isoformat() if subcategory.created_at else ''
            }
        })
        
    except Exception as e:
        print(f"获取二级分类详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取二级分类详情失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-subcategories/<int:subcategory_id>', methods=['PUT'])
@login_required
def admin_update_subcategory(subcategory_id):
    """更新二级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductSubcategory = models['ProductSubcategory']
        db = models['db']
        
        if not ProductSubcategory:
            return jsonify({
                'status': 'error',
                'message': '产品二级分类模型未找到'
            }), 500
        
        subcategory = ProductSubcategory.query.get_or_404(subcategory_id)
        data = request.get_json()
        
        # 更新字段
        if 'name' in data:
            subcategory.name = data['name']
        if 'code' in data:
            # 检查代码是否与同一一级分类下的其他二级分类重复
            existing = ProductSubcategory.query.filter_by(
                category_id=subcategory.category_id,
                code=data['code']
            ).first()
            if existing and existing.id != subcategory_id:
                return jsonify({'status': 'error', 'message': '该一级分类下已存在相同代码的二级分类'}), 400
            subcategory.code = data['code']
        if 'icon' in data:
            subcategory.icon = data['icon']
        if 'image_url' in data:
            subcategory.image_url = data['image_url']
        if 'sort_order' in data:
            subcategory.sort_order = data.get('sort_order', 0)
        if 'is_active' in data:
            subcategory.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '二级分类更新成功',
            'data': {
                'id': subcategory.id,
                'name': subcategory.name,
                'code': subcategory.code
            }
        })
        
    except Exception as e:
        print(f"更新二级分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新二级分类失败: {str(e)}'
        }), 500

@admin_product_categories_api_bp.route('/api/admin/product-subcategories/<int:subcategory_id>', methods=['DELETE'])
@login_required
def admin_delete_subcategory(subcategory_id):
    """删除二级分类"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        ProductSubcategory = models['ProductSubcategory']
        db = models['db']
        
        if not ProductSubcategory:
            return jsonify({
                'status': 'error',
                'message': '产品二级分类模型未找到'
            }), 500
        
        subcategory = ProductSubcategory.query.get_or_404(subcategory_id)
        
        # 检查是否有产品使用此分类
        if hasattr(subcategory, 'products') and subcategory.products:
            return jsonify({
                'status': 'error',
                'message': '该分类下还有产品，无法删除'
            }), 400
        
        db.session.delete(subcategory)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '二级分类删除成功'
        })
        
    except Exception as e:
        print(f"删除二级分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除二级分类失败: {str(e)}'
        }), 500
