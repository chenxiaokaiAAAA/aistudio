# -*- coding: utf-8 -*-
"""
分析photo_selection.py文件结构，为拆分做准备
"""
import re
from pathlib import Path

file_path = Path(__file__).parent.parent.parent / 'app' / 'routes' / 'photo_selection.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# 查找所有路由和函数
routes = []
functions = []
current_function = None
current_route = None

for i, line in enumerate(lines, 1):
    # 查找路由装饰器
    route_match = re.search(r'@photo_selection_bp\.route\([\'"]([^\'"]+)[\'"]', line)
    if route_match:
        current_route = route_match.group(1)
    
    # 查找函数定义
    func_match = re.search(r'^def\s+(\w+)\(', line)
    if func_match:
        func_name = func_match.group(1)
        if current_route:
            routes.append({
                'route': current_route,
                'function': func_name,
                'line': i
            })
            current_route = None
        else:
            functions.append({
                'function': func_name,
                'line': i
            })

print("=" * 80)
print("photo_selection.py 文件结构分析")
print("=" * 80)
print(f"\n总行数: {len(lines)}")
print(f"\n路由函数 ({len(routes)} 个):")
print("-" * 80)
for route in routes:
    print(f"  {route['line']:4d} | {route['route']:40s} | {route['function']}")

print(f"\n辅助函数 ({len(functions)} 个):")
print("-" * 80)
for func in functions:
    print(f"  {func['line']:4d} | {func['function']}")

# 按功能分组
print("\n" + "=" * 80)
print("建议的拆分方案:")
print("=" * 80)
print("""
1. photo_selection_list.py - 订单列表相关
   - photo_selection_list()
   - 相关辅助函数

2. photo_selection_detail.py - 订单详情相关
   - photo_selection_detail()
   - 相关辅助函数

3. photo_selection_submit.py - 提交选片相关
   - photo_selection_submit()
   - 相关辅助函数

4. photo_selection_confirm.py - 确认选片相关
   - photo_selection_confirm()
   - photo_selection_review()
   - 相关辅助函数

5. photo_selection_print.py - 打印相关
   - start_print()
   - 相关辅助函数

6. photo_selection_utils.py - 工具函数
   - 通用辅助函数
   - Token管理
""")
