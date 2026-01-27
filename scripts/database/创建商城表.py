# -*- coding: utf-8 -*-
"""
创建商城相关数据表的脚本
运行此脚本以创建商城功能所需的数据表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from test_server import app, db
    from app.models import ShopProduct, ShopProductImage, ShopProductSize, ShopOrder
    
    print("开始创建商城数据表...")
    
    # 创建所有表
    with app.app_context():
        db.create_all()
        print("✅ 商城数据表创建成功！")
        print("已创建的表：")
        print("  - shop_products (商城产品表)")
        print("  - shop_product_images (商城产品图片表)")
        print("  - shop_product_sizes (商城产品规格表)")
        print("  - shop_orders (商城订单表)")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保已正确安装所有依赖，并且数据库已初始化")
except Exception as e:
    print(f"❌ 创建表失败: {e}")
    import traceback
    traceback.print_exc()
