# -*- coding: utf-8 -*-
"""
创建团购套餐配置表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from test_server import app, db
    from app.models import GrouponPackage
    
    print("开始创建团购套餐配置表...")
    
    with app.app_context():
        # 创建表
        db.create_all()
        print("[OK] 团购套餐配置表创建成功！")
        print("已创建的表：")
        print("  - groupon_packages (团购套餐配置表)")
        
except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    print("请确保已正确安装所有依赖，并且数据库已初始化")
except Exception as e:
    print(f"[ERROR] 创建表失败: {e}")
    import traceback
    traceback.print_exc()
