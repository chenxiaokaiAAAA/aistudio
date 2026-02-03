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
                'HomepageCategoryNav': test_server.HomepageCategoryNav,
                'HomepageProductSection': test_server.HomepageProductSection,
                'HomepageActivityBanner': test_server.HomepageActivityBanner,
                'ProductCategory': test_server.ProductCategory,
                'Product': test_server.Product,
                'ProductImage': test_server.ProductImage,
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

# ============================================================================
# 首页分类导航API
# ============================================================================

@admin_homepage_api_bp.route('/category-navs', methods=['GET'])
def admin_get_category_navs():
    """获取所有分类导航配置"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageCategoryNav = models['HomepageCategoryNav']
        get_base_url = models['get_base_url']
        
        navs = HomepageCategoryNav.query.order_by(HomepageCategoryNav.sort_order).all()
        result = []
        for nav in navs:
            # 保存原始路径，用于编辑时显示
            image_url_original = nav.image_url or ''
            # 生成完整URL用于预览
            image_url_preview = image_url_original
            if image_url_original and not image_url_original.startswith('http'):
                image_url_preview = f"{get_base_url()}{image_url_original}"
            
            result.append({
                'id': nav.id,
                'category_id': nav.category_id,
                'name': nav.name,
                'icon': nav.icon,
                'image_url': image_url_original,  # 返回原始路径
                'image_url_preview': image_url_preview,  # 完整URL用于预览
                'link_type': nav.link_type,
                'link_value': nav.link_value,
                'sort_order': nav.sort_order,
                'is_active': nav.is_active,
                'created_at': nav.created_at.isoformat(),
                'updated_at': nav.updated_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取分类导航失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取分类导航失败'
        }), 500

@admin_homepage_api_bp.route('/category-navs', methods=['POST'])
def admin_create_category_nav():
    """创建分类导航"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageCategoryNav = models['HomepageCategoryNav']
        db = models['db']
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'status': 'error', 'message': '缺少名称'}), 400
        
        nav = HomepageCategoryNav(
            category_id=data.get('category_id'),
            name=data['name'],
            icon=data.get('icon'),
            image_url=data.get('image_url', ''),
            link_type=data.get('link_type', 'category'),
            link_value=data.get('link_value', ''),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(nav)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类导航创建成功',
            'data': {'id': nav.id, 'name': nav.name}
        })
        
    except Exception as e:
        print(f"创建分类导航失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '创建分类导航失败'
        }), 500

@admin_homepage_api_bp.route('/category-navs/<int:nav_id>', methods=['PUT'])
def admin_update_category_nav(nav_id):
    """更新分类导航"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageCategoryNav = models['HomepageCategoryNav']
        db = models['db']
        
        nav = HomepageCategoryNav.query.get_or_404(nav_id)
        data = request.get_json()
        
        if 'name' in data:
            nav.name = data['name']
        if 'category_id' in data:
            nav.category_id = data['category_id']
        if 'icon' in data:
            nav.icon = data['icon']
        if 'image_url' in data:
            nav.image_url = data['image_url']
        if 'link_type' in data:
            nav.link_type = data['link_type']
        if 'link_value' in data:
            nav.link_value = data['link_value']
        if 'sort_order' in data:
            nav.sort_order = data['sort_order']
        if 'is_active' in data:
            nav.is_active = data['is_active']
        
        nav.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类导航更新成功'
        })
        
    except Exception as e:
        print(f"更新分类导航失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新分类导航失败'
        }), 500

@admin_homepage_api_bp.route('/category-navs/<int:nav_id>', methods=['DELETE'])
def admin_delete_category_nav(nav_id):
    """删除分类导航"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageCategoryNav = models['HomepageCategoryNav']
        db = models['db']
        
        nav = HomepageCategoryNav.query.get_or_404(nav_id)
        db.session.delete(nav)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '分类导航删除成功'
        })
        
    except Exception as e:
        print(f"删除分类导航失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '删除分类导航失败'
        }), 500

# ============================================================================
# 首页产品推荐模块API
# ============================================================================

@admin_homepage_api_bp.route('/product-sections', methods=['GET'])
def admin_get_product_sections():
    """获取所有产品推荐模块"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageProductSection = models['HomepageProductSection']
        
        sections = HomepageProductSection.query.order_by(HomepageProductSection.sort_order).all()
        result = []
        for section in sections:
            product_ids = []
            if section.product_ids:
                try:
                    product_ids = json.loads(section.product_ids)
                except:
                    product_ids = []
            
            # 解析config字段
            config_data = {}
            if hasattr(section, 'config') and section.config:
                try:
                    config_data = json.loads(section.config)
                except (json.JSONDecodeError, TypeError):
                    config_data = {}
            
            result.append({
                'id': section.id,
                'section_type': section.section_type,
                'title': section.title,
                'subtitle': section.subtitle,
                'show_more_button': section.show_more_button,
                'more_link': section.more_link,
                'layout_type': section.layout_type,
                'product_ids': product_ids,
                'category_id': section.category_id,
                'limit': section.limit,
                'sort_order': section.sort_order,
                'is_active': section.is_active,
                'config': config_data,  # 返回解析后的config对象
                'created_at': section.created_at.isoformat(),
                'updated_at': section.updated_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取产品推荐模块失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取产品推荐模块失败'
        }), 500

@admin_homepage_api_bp.route('/product-sections', methods=['POST'])
def admin_create_product_section():
    """创建产品推荐模块"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageProductSection = models['HomepageProductSection']
        db = models['db']
        
        data = request.get_json()
        
        if not data.get('title') or not data.get('section_type'):
            return jsonify({'status': 'error', 'message': '缺少标题或模块类型'}), 400
        
        product_ids_str = ''
        if data.get('product_ids'):
            if isinstance(data['product_ids'], list):
                product_ids_str = json.dumps(data['product_ids'], ensure_ascii=False)
            else:
                product_ids_str = str(data['product_ids'])
        
        # 处理config字段（用于当季主推、时光旅程、IP联名、作品展示等模块）
        config_str = ''
        if data.get('config'):
            if isinstance(data['config'], dict):
                config_str = json.dumps(data['config'], ensure_ascii=False)
            else:
                config_str = str(data['config'])
        
        section = HomepageProductSection(
            section_type=data['section_type'],
            title=data['title'],
            subtitle=data.get('subtitle'),
            show_more_button=data.get('show_more_button', True),
            more_link=data.get('more_link', ''),
            layout_type=data.get('layout_type', 'grid'),
            product_ids=product_ids_str,
            category_id=data.get('category_id'),
            limit=data.get('limit', 6),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True),
            config=config_str
        )
        
        db.session.add(section)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '产品推荐模块创建成功',
            'data': {'id': section.id, 'title': section.title}
        })
        
    except Exception as e:
        print(f"创建产品推荐模块失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '创建产品推荐模块失败'
        }), 500

@admin_homepage_api_bp.route('/product-sections/<int:section_id>', methods=['PUT'])
def admin_update_product_section(section_id):
    """更新产品推荐模块"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageProductSection = models['HomepageProductSection']
        db = models['db']
        
        section = HomepageProductSection.query.get_or_404(section_id)
        data = request.get_json()
        
        if 'section_type' in data:
            section.section_type = data['section_type']
        if 'title' in data:
            section.title = data['title']
        if 'subtitle' in data:
            section.subtitle = data['subtitle']
        if 'show_more_button' in data:
            section.show_more_button = data['show_more_button']
        if 'more_link' in data:
            section.more_link = data['more_link']
        if 'layout_type' in data:
            section.layout_type = data['layout_type']
        if 'product_ids' in data:
            if isinstance(data['product_ids'], list):
                section.product_ids = json.dumps(data['product_ids'], ensure_ascii=False)
            else:
                section.product_ids = str(data['product_ids'])
        if 'category_id' in data:
            section.category_id = data['category_id']
        if 'limit' in data:
            section.limit = data['limit']
        if 'sort_order' in data:
            section.sort_order = data['sort_order']
        if 'is_active' in data:
            section.is_active = data['is_active']
        if 'config' in data:
            # 处理config字段（用于当季主推、时光旅程、IP联名、作品展示等模块）
            if isinstance(data['config'], dict):
                section.config = json.dumps(data['config'], ensure_ascii=False)
            else:
                section.config = str(data['config'])
        
        section.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '产品推荐模块更新成功'
        })
        
    except Exception as e:
        print(f"更新产品推荐模块失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '更新产品推荐模块失败'
        }), 500

@admin_homepage_api_bp.route('/product-sections/<int:section_id>', methods=['DELETE'])
def admin_delete_product_section(section_id):
    """删除产品推荐模块"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        HomepageProductSection = models['HomepageProductSection']
        db = models['db']
        
        section = HomepageProductSection.query.get_or_404(section_id)
        db.session.delete(section)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '产品推荐模块删除成功'
        })
        
    except Exception as e:
        print(f"删除产品推荐模块失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': '删除产品推荐模块失败'
        }), 500

@admin_homepage_api_bp.route('/products', methods=['GET'])
def admin_get_products_for_selection():
    """获取产品列表（用于产品选择器）"""
    try:
        models = get_models()
        if not models:
            return jsonify({
                'status': 'error',
                'message': '数据库模型未初始化'
            }), 500
        
        Product = models['Product']
        ProductImage = models.get('ProductImage')
        ProductCategory = models.get('ProductCategory')
        get_base_url = models['get_base_url']
        
        # 获取所有激活的产品
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order.asc(), Product.id.asc()).all()
        
        result = []
        for product in products:
            # 获取产品主图
            product_image_url = None
            if ProductImage:
                product_image = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.sort_order.asc()).first()
                if product_image:
                    product_image_url = product_image.image_url
                    if product_image_url and not product_image_url.startswith('http'):
                        product_image_url = f"{get_base_url()}{product_image_url}"
            
            # 如果没有产品图片，尝试使用产品的images字段
            if not product_image_url and hasattr(product, 'images') and product.images:
                try:
                    import json
                    images = json.loads(product.images) if isinstance(product.images, str) else product.images
                    if images and len(images) > 0:
                        product_image_url = images[0]
                        if product_image_url and not product_image_url.startswith('http'):
                            product_image_url = f"{get_base_url()}{product_image_url}"
                except:
                    pass
            
            # 获取分类名称
            category_name = ''
            if ProductCategory and hasattr(product, 'category_id') and product.category_id:
                category = ProductCategory.query.get(product.category_id)
                if category:
                    category_name = category.name
            
            result.append({
                'id': product.id,
                'name': product.name,
                'code': product.code,
                'image_url': product_image_url,
                'category_name': category_name,
                'category_id': getattr(product, 'category_id', None)
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"获取产品列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '获取产品列表失败'
        }), 500
