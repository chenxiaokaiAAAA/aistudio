# -*- coding: utf-8 -*-
"""
根据产品分类自动创建分类导航项，并使用本地图标（简化版，直接操作数据库）
"""
import sys
import os
import sqlite3
from datetime import datetime

# 获取数据库路径
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(script_dir, 'instance', 'pet_painting.db')

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    sys.exit(1)

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

# 图标映射表（根据分类名称或code匹配图标）
icon_mapping = {
    '证件照': '/images/category-nav/群组 1@1x.png',
    'idphoto': '/images/category-nav/群组 1@1x.png',
    '结婚登记照': '/images/category-nav/群组 2@1x.png',
    'wedding': '/images/category-nav/群组 2@1x.png',
}

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有激活的产品分类
    cursor.execute("""
        SELECT id, name, code, icon, sort_order 
        FROM product_categories 
        WHERE is_active = 1 
        ORDER BY sort_order
    """)
    categories = cursor.fetchall()
    
    print(f'找到 {len(categories)} 个产品分类')
    
    # 获取现有的分类导航
    cursor.execute("SELECT category_id FROM homepage_category_nav")
    existing_category_ids = {row[0] for row in cursor.fetchall() if row[0]}
    
    icon_index = 0
    created_count = 0
    updated_count = 0
    
    for cat_id, cat_name, cat_code, cat_icon, cat_sort_order in categories:
        # 确定使用的图标
        icon_url = None
        cat_name_lower = (cat_name or '').lower()
        cat_code_lower = (cat_code or '').lower()
        
        # 先尝试从映射表查找
        for key, icon_path in icon_mapping.items():
            if key.lower() in cat_name_lower or key.lower() == cat_code_lower:
                icon_url = icon_path
                break
        
        # 如果没找到，按顺序使用图标
        if not icon_url:
            if icon_index < len(icon_files):
                icon_url = icon_files[icon_index]
                icon_index += 1
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM homepage_category_nav WHERE category_id = ?", (cat_id,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有导航项
            nav_id = existing[0]
            cursor.execute("""
                UPDATE homepage_category_nav 
                SET name = ?, icon = ?, image_url = ?, link_value = ?, updated_at = ?
                WHERE id = ?
            """, (cat_name, cat_icon, icon_url, str(cat_id), datetime.now(), nav_id))
            updated_count += 1
            print(f'更新: {cat_name} -> {icon_url}')
        else:
            # 创建新的导航项
            cursor.execute("""
                INSERT INTO homepage_category_nav 
                (category_id, name, icon, image_url, link_type, link_value, sort_order, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'category', ?, ?, 1, ?, ?)
            """, (cat_id, cat_name, cat_icon, icon_url, str(cat_id), cat_sort_order, datetime.now(), datetime.now()))
            created_count += 1
            print(f'创建: {cat_name} -> {icon_url}')
    
    conn.commit()
    conn.close()
    
    print(f'\n完成！')
    print(f'创建了 {created_count} 个分类导航项')
    print(f'更新了 {updated_count} 个分类导航项')
    print(f'\n现在可以在小程序首页看到所有分类导航图标了！')
    
except sqlite3.Error as e:
    print(f"数据库错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
