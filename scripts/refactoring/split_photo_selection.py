# -*- coding: utf-8 -*-
"""
拆分photo_selection.py文件
"""
import re
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
source_file = project_root / 'app' / 'routes' / 'photo_selection.py'
output_dir = project_root / 'app' / 'routes' / 'photo_selection'

# 读取源文件
with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# 定义每个模块的路由和函数
modules = {
    'detail': {
        'route': '/admin/photo-selection/<int:order_id>',
        'function': 'photo_selection_detail',
        'start_line': 198,
        'end_line': 547
    },
    'submit': {
        'route': '/admin/photo-selection/<int:order_id>/submit',
        'function': 'photo_selection_submit',
        'start_line': 549,
        'end_line': 984
    },
    'confirm': {
        'functions': ['photo_selection_confirm', 'photo_selection_review', 'check_payment_status', 'skip_payment'],
        'start_line': 985,
        'end_line': 1370
    },
    'print_module': {
        'route': '/admin/photo-selection/<int:order_id>/start-print',
        'function': 'start_print',
        'start_line': 1371,
        'end_line': 1672
    },
    'qrcode': {
        'functions': ['generate_selection_qrcode', 'verify_selection_token'],
        'start_line': 1673,
        'end_line': 1947
    },
    'search': {
        'route': '/api/photo-selection/search-orders',
        'function': 'search_orders_for_selection',
        'start_line': 1948,
        'end_line': 2018
    }
}

# 提取公共导入和配置
header_lines = []
for i, line in enumerate(lines[:30]):
    if line.strip() and not line.strip().startswith('@photo_selection_bp'):
        header_lines.append(line)
    if i >= 30:
        break

print("公共头部:")
for line in header_lines:
    print(line)
