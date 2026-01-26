"""
管理后台首页配置API路由模块
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
import json

# 创建蓝图
admin_homepage_api_bp = Blueprint('admin_homepage_api', __name__, url_prefix='/api/admin/homepage')

def get_models():
    """延迟导入数据库模型，避免循环导入"""
    try:
        test_server = sys.modules.get('test_server')
        if test_server:
            return {
                'HomepageBanner': test_server.HomepageBanner,
                'HomepageConfig': test_server.HomepageConfig,
                'db': test_server.db,
                'get_base_url': test_server.get_base_url
            }
        return None
    except Exception as e:
        print(f"⚠️ 获取数据库模型失败: {e}")
        return None

# ============================================================================
# 轮播图API
# ============================================================================

@admin_homepage_api_bp.route('/banners', methods=['GET'])
def admin_get_banners():
    """获取所有轮播图"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageBanner = models['HomepageBanner']
        get_base_url = models['get_base_url']
        
        banners = HomepageBanner.query.order_by(HomepageBanner.sort_order).all()
        result = []
        for banner in banners:
            # 确保图片URL是完整的URL
            image_url = banner.image_url
            if image_url and not image_url.startswith('http'):
                image_url = f"{get_base_url()}{image_url}"
            
            # 尝试获取新字段，如果不存在则使用默认值
            try:
                promotion_params = None
                if hasattr(banner, 'promotion_params') and banner.promotion_params:
                    try:
                        promotion_params = json.loads(banner.promotion_params)
                    except (json.JSONDecodeError, TypeError):
                        promotion_params = None
                
                banner_type = getattr(banner, 'type', 'link')
            except AttributeError:
                promotion_params = None
                banner_type = 'link'
            
            result.append({
                'id': banner.id,
                'title': banner.title,
                'subtitle': banner.subtitle,
                'image_url': image_url,
                'link': banner.link,
                'sort_order': banner.sort_order,
                'is_active': banner.is_active,
                'type': banner_type,
                'promotion_params': promotion_params,
                'created_at': banner.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取轮播图失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取轮播图失败'
        }), 500

@admin_homepage_api_bp.route('/banners', methods=['POST'])
def admin_create_banner():
    """创建轮播图"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageBanner = models['HomepageBanner']
        db = models['db']
        
        data = request.get_json()
        
        # 检查必填字段
        if not data.get('image_url'):
            return jsonify({'status': 'error', 'message': '缺少图片URL'}), 400
        
        # 创建轮播图
        banner = HomepageBanner(
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            image_url=data['image_url'],
            link=data.get('link', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        
        # 尝试设置新字段（如果数据库支持的话）
        try:
            promotion_params = data.get('promotion_params')
            if promotion_params and isinstance(promotion_params, dict):
                banner.promotion_params = json.dumps(promotion_params, ensure_ascii=False)
            banner.type = data.get('type', 'link')
        except Exception as e:
            print(f"新字段设置失败（数据库兼容性）: {e}")
            # 忽略新字段错误，使用默认值
        
        db.session.add(banner)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '轮播图创建成功',
            'data': {
                'id': banner.id,
                'title': banner.title
            }
        })
        
    except Exception as e:
        print(f"创建轮播图失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '创建轮播图失败'
        }), 500

@admin_homepage_api_bp.route('/banners/<int:banner_id>', methods=['PUT'])
def admin_update_banner(banner_id):
    """更新轮播图"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageBanner = models['HomepageBanner']
        db = models['db']
        
        banner = HomepageBanner.query.get_or_404(banner_id)
        data = request.get_json()
        
        # 更新字段
        if 'title' in data:
            banner.title = data['title']
        if 'subtitle' in data:
            banner.subtitle = data['subtitle']
        if 'image_url' in data:
            banner.image_url = data['image_url']
        if 'link' in data:
            banner.link = data['link']
        if 'sort_order' in data:
            banner.sort_order = data['sort_order']
        if 'is_active' in data:
            banner.is_active = data['is_active']
        
        # 尝试更新新字段（如果数据库支持的话）
        try:
            if 'type' in data:
                banner.type = data['type']
            if 'promotion_params' in data:
                promotion_params = data['promotion_params']
                if isinstance(promotion_params, dict):
                    banner.promotion_params = json.dumps(promotion_params, ensure_ascii=False)
                else:
                    banner.promotion_params = promotion_params
        except Exception as e:
            print(f"新字段更新失败（数据库兼容性）: {e}")
            # 忽略新字段错误
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '轮播图更新成功'
        })
        
    except Exception as e:
        print(f"更新轮播图失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新轮播图失败'
        }), 500

@admin_homepage_api_bp.route('/banners/<int:banner_id>', methods=['DELETE'])
def admin_delete_banner(banner_id):
    """删除轮播图"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageBanner = models['HomepageBanner']
        db = models['db']
        
        banner = HomepageBanner.query.get_or_404(banner_id)
        
        db.session.delete(banner)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '轮播图删除成功'
        })
        
    except Exception as e:
        print(f"删除轮播图失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '删除轮播图失败'
        }), 500

# ============================================================================
# 首页配置API
# ============================================================================

@admin_homepage_api_bp.route('/config', methods=['GET'])
def admin_get_homepage_config():
    """获取首页配置"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageConfig = models['HomepageConfig']
        db = models['db']
        
        config = HomepageConfig.query.first()
        if not config:
            # 创建默认配置
            config = HomepageConfig(
                title='AI拍照机',
                subtitle='专属定制',
                description='为您打造专属艺术品',
                enable_custom_order=True,
                enable_style_library=True,
                enable_product_gallery=True,
                enable_works_gallery=True
            )
            db.session.add(config)
            db.session.commit()
        
        result = {
            'id': config.id,
            'title': config.title,
            'subtitle': config.subtitle,
            'description': config.description,
            'enable_custom_order': config.enable_custom_order,
            'enable_style_library': config.enable_style_library,
            'enable_product_gallery': config.enable_product_gallery,
            'enable_works_gallery': config.enable_works_gallery,
            'updated_at': config.updated_at.isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取首页配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取首页配置失败'
        }), 500

@admin_homepage_api_bp.route('/config', methods=['PUT'])
def admin_update_homepage_config():
    """更新首页配置"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageConfig = models['HomepageConfig']
        db = models['db']
        
        data = request.get_json()
        
        config = HomepageConfig.query.first()
        if not config:
            config = HomepageConfig()
            db.session.add(config)
        
        # 更新字段
        if 'title' in data:
            config.title = data['title']
        if 'subtitle' in data:
            config.subtitle = data['subtitle']
        if 'description' in data:
            config.description = data['description']
        
        config.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '首页配置更新成功'
        })
        
    except Exception as e:
        print(f"更新首页配置失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新首页配置失败'
        }), 500

@admin_homepage_api_bp.route('/features', methods=['PUT'])
def admin_update_homepage_features():
    """更新功能配置"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageConfig = models['HomepageConfig']
        db = models['db']
        
        data = request.get_json()
        
        config = HomepageConfig.query.first()
        if not config:
            config = HomepageConfig()
            db.session.add(config)
        
        # 更新功能开关
        if 'enable_custom_order' in data:
            config.enable_custom_order = data['enable_custom_order']
        if 'enable_style_library' in data:
            config.enable_style_library = data['enable_style_library']
        if 'enable_product_gallery' in data:
            config.enable_product_gallery = data['enable_product_gallery']
        if 'enable_works_gallery' in data:
            config.enable_works_gallery = data['enable_works_gallery']
        
        config.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '功能配置更新成功'
        })
        
    except Exception as e:
        print(f"更新功能配置失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新功能配置失败'
        }), 500
