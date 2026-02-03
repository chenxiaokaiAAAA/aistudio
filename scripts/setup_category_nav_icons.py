# -*- coding: utf-8 -*-
"""
根据产品分类自动创建分类导航项，并使用本地图标
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 先导入并初始化数据库
from test_server import init_db
init_db()

from app.models import db, ProductCategory, HomepageCategoryNav
from datetime import datetime

# 图标映射表（根据分类名称或code匹配图标）
ICON_MAPPING = {
    # 可以根据实际分类名称调整
    '证件照': '/images/category-nav/群组 1@1x.png',
    'idphoto': '/images/category-nav/群组 1@1x.png',
    '结婚登记照': '/images/category-nav/群组 2@1x.png',
    'wedding': '/images/category-nav/群组 2@1x.png',
    # 可以继续添加其他分类的映射
}

def setup_category_navs():
    """设置分类导航"""
    # 获取所有激活的产品分类
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.sort_order).all()
    
    print(f'找到 {len(categories)} 个产品分类')
    
    # 图标文件列表（按顺序使用）
    icon_files = [
        '/images/category-nav/群组 1@1x.png',
        '/images/category-nav/群组 2@1x.png',
        '/images/category-nav/群组 3@1x.png',
        '/images/category-nav/群组 4@1x.png',
        '/images/category-nav/群组 7@1x.png',
        '/images/category-nav/群组 8@1x.png',
        '/images/category-nav/群组 9@1x.png',
        '/images/category-nav/群组 10@1x.png',
        '/images/category-nav/群组 11@1x.png',
        '/images/category-nav/群组 12@1x.png',
        '/images/category-nav/群组 13@1x.png',
        '/images/category-nav/群组 14@1x.png',
        '/images/category-nav/群组 15@1x.png',
        '/images/category-nav/群组 16@1x.png',
        '/images/category-nav/群组 17@1x.png',
    ]
    
    icon_index = 0
    created_count = 0
    updated_count = 0
    
    for category in categories:
        # 检查是否已存在该分类的导航项
        existing_nav = HomepageCategoryNav.query.filter_by(category_id=category.id).first()
        
        # 确定使用的图标
        icon_url = None
        category_name_lower = category.name.lower()
        category_code_lower = category.code.lower() if category.code else ''
        
        # 先尝试从映射表查找
        for key, icon_path in ICON_MAPPING.items():
            if key.lower() in category_name_lower or key.lower() == category_code_lower:
                icon_url = icon_path
                break
        
        # 如果没找到，按顺序使用图标
        if not icon_url:
            if icon_index < len(icon_files):
                icon_url = icon_files[icon_index]
                icon_index += 1
            else:
                # 如果图标用完了，使用分类自带的图标或emoji
                icon_url = category.image_url if category.image_url else None
        
        if existing_nav:
            # 更新现有导航项
            if not existing_nav.image_url or existing_nav.image_url.startswith('http'):
                existing_nav.image_url = icon_url
                existing_nav.name = category.name
                existing_nav.icon = category.icon
                existing_nav.link_value = str(category.id)
                existing_nav.updated_at = datetime.now()
                updated_count += 1
                print(f'更新: {category.name} -> {icon_url}')
        else:
            # 创建新的导航项
            nav = HomepageCategoryNav(
                category_id=category.id,
                name=category.name,
                icon=category.icon,
                image_url=icon_url,
                link_type='category',
                link_value=str(category.id),
                sort_order=category.sort_order,
                is_active=True
            )
            db.session.add(nav)
            created_count += 1
            print(f'创建: {category.name} -> {icon_url}')
    
    # 提交更改
    db.session.commit()
    
    print(f'\n完成！')
    print(f'创建了 {created_count} 个分类导航项')
    print(f'更新了 {updated_count} 个分类导航项')
    print(f'\n现在可以在小程序首页看到所有分类导航图标了！')

if __name__ == '__main__':
    setup_category_navs()
