#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from test_server import app
    print("✅ 成功导入test_server模块")
    print("🚀 启动服务器在端口6000...")
    app.run(host='0.0.0.0', port=6000, debug=True)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()

