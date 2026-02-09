# -*- coding: utf-8 -*-
"""
查找剩余的N+1查询问题
"""
import os
import re
import sys
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def find_n1_queries():
    """查找潜在的N+1查询问题"""
    routes_dir = project_root / 'app' / 'routes'
    
    n1_patterns = [
        # 模式1: for循环中的查询
        (r'for\s+.*\s+in\s+.*:\s*\n.*\.query\.(get|filter|filter_by|all|first|count)\(', 
         '循环中的数据库查询'),
        
        # 模式2: 列表推导式中的查询
        (r'\[.*\.query\.(get|filter|filter_by)\(.*\)\s+for\s+.*\s+in\s+', 
         '列表推导式中的数据库查询'),
        
        # 模式3: sum/max/min等聚合函数中的查询
        (r'(sum|max|min|any|all)\(.*\.query\.(get|filter|filter_by)\(', 
         '聚合函数中的数据库查询'),
    ]
    
    issues = []
    
    for py_file in routes_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            for pattern, description in n1_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    # 获取匹配的行号
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # 获取上下文
                    start_line = max(0, line_num - 3)
                    end_line = min(len(lines), line_num + 3)
                    context = '\n'.join(lines[start_line:end_line])
                    
                    issues.append({
                        'file': str(py_file.relative_to(project_root)),
                        'line': line_num,
                        'pattern': description,
                        'context': context
                    })
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return issues

def analyze_manual_checks():
    """手动检查一些常见的N+1查询场景"""
    routes_dir = project_root / 'app' / 'routes'
    
    manual_checks = []
    
    # 检查文件
    check_files = [
        'media.py',
        'admin_orders_detail_api.py',
        'franchisee/admin.py',
        'franchisee/frontend.py',
    ]
    
    for filename in check_files:
        file_path = routes_dir / filename
        if not file_path.exists():
            # 尝试在子目录中查找
            found = list(routes_dir.rglob(filename))
            if found:
                file_path = found[0]
            else:
                continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 检查for循环中的查询
            for i, line in enumerate(lines, 1):
                if 'for' in line and 'in' in line:
                    # 检查接下来的几行是否有查询
                    for j in range(i, min(i + 10, len(lines))):
                        next_line = lines[j]
                        if re.search(r'\.query\.(get|filter|filter_by|all|first|count)\(', next_line):
                            # 检查是否已经有批量查询优化
                            if 'in_(' not in content[max(0, i-20):i] and '批量查询' not in content[max(0, i-20):i]:
                                manual_checks.append({
                                    'file': str(file_path.relative_to(project_root)),
                                    'line': i,
                                    'issue': '可能的N+1查询：循环中的数据库查询',
                                    'code': '\n'.join(lines[max(0, i-2):min(len(lines), j+2)])
                                })
                            break
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
    
    return manual_checks

if __name__ == '__main__':
    print("=" * 80)
    print("查找剩余的N+1查询问题")
    print("=" * 80)
    
    # 自动查找
    print("\n1. 自动模式匹配...")
    issues = find_n1_queries()
    
    if issues:
        print(f"\n找到 {len(issues)} 个潜在问题：")
        for issue in issues[:20]:  # 只显示前20个
            print(f"\n文件: {issue['file']}")
            print(f"行号: {issue['line']}")
            print(f"问题: {issue['pattern']}")
            print(f"上下文:\n{issue['context']}")
            print("-" * 80)
    else:
        print("未找到明显的N+1查询问题")
    
    # 手动检查
    print("\n2. 手动检查常见场景...")
    manual_checks = analyze_manual_checks()
    
    if manual_checks:
        print(f"\n找到 {len(manual_checks)} 个需要检查的场景：")
        for check in manual_checks:
            print(f"\n文件: {check['file']}")
            print(f"行号: {check['line']}")
            print(f"问题: {check['issue']}")
            print(f"代码:\n{check['code']}")
            print("-" * 80)
    else:
        print("未找到需要检查的场景")
    
    print(f"\n总计: {len(issues)} 个自动检测问题, {len(manual_checks)} 个手动检查问题")
    print("=" * 80)
