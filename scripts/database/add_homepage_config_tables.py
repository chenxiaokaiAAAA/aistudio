#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加首页配置相关数据库表
创建 HomepageCategoryNav 和 HomepageProductSection 表
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_server import app, db

def add_homepage_config_tables():
    """添加首页配置相关表"""
    with app.app_context():
        try:
            # 导入新模型
            from app.models import HomepageCategoryNav, HomepageProductSection
            
            # 创建表（如果不存在）
            db.create_all()
            
            print('✅ 首页配置表创建完成')
            print('   - HomepageCategoryNav (分类导航表)')
            print('   - HomepageProductSection (产品推荐模块表)')
            
        except Exception as e:
            print(f'❌ 创建表失败: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    add_homepage_config_tables()
