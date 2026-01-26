#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动服务器并检查错误
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from test_server import app, db, Product
    
    print("正在启动服务器...")
    
    # 检查数据库连接
    try:
        products = Product.query.all()
        print(f"✓ 数据库连接正常，找到 {len(products)} 个产品")
    except Exception as e:
        print(f"✗ 数据库查询失败: {str(e)}")
        
    # 启动服务器
    app.run(host='0.0.0.0', port=6000, debug=True)
    
except Exception as e:
    print(f"✗ 启动失败: {str(e)}")
    import traceback
    traceback.print_exc()


