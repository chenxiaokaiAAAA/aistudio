#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API性能分析工具
分析API接口的性能问题，包括：
1. 缺少分页的接口
2. 返回大量数据的接口
3. 可能存在的N+1查询问题
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_ROUTES_DIR = PROJECT_ROOT / 'app' / 'routes'

def analyze_file(file_path):
    """分析单个文件的性能问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = {
            'no_pagination': [],
            'large_result_set': [],
            'n_plus_one': [],
            'no_field_filtering': []
        }
        
        # 解析AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        # 查找路由定义
        for node in ast.walk(tree):
            # 查找 @route 装饰器
            if isinstance(node, ast.FunctionDef):
                # 检查函数是否有分页
                has_pagination = False
                has_limit = False
                returns_all = False
                
                # 检查函数体
                for stmt in ast.walk(node):
                    # 检查是否有 paginate 调用
                    if isinstance(stmt, ast.Call):
                        if isinstance(stmt.func, ast.Attribute):
                            if stmt.func.attr == 'paginate':
                                has_pagination = True
                        # 检查是否有 limit
                        if isinstance(stmt.func, ast.Attribute):
                            if stmt.func.attr == 'limit':
                                has_limit = True
                    
                    # 检查是否有 .all() 调用
                    if isinstance(stmt, ast.Call):
                        if isinstance(stmt.func, ast.Attribute):
                            if stmt.func.attr == 'all':
                                returns_all = True
                
                # 如果返回所有数据且没有分页，标记为问题
                if returns_all and not has_pagination and not has_limit:
                    # 检查是否返回jsonify
                    for stmt in node.body:
                        if isinstance(stmt, ast.Return):
                            if isinstance(stmt.value, ast.Call):
                                if isinstance(stmt.value.func, ast.Name):
                                    if stmt.value.func.id == 'jsonify':
                                        issues['no_pagination'].append({
                                            'function': node.name,
                                            'line': node.lineno
                                        })
        
        return issues
        
    except Exception as e:
        return {'error': str(e)}

def find_large_queries():
    """查找可能返回大量数据的查询"""
    large_queries = []
    
    for root, dirs, files in os.walk(APP_ROUTES_DIR):
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        # 查找 .all() 调用
                        if '.all()' in line and 'paginate' not in line.lower():
                            # 检查上下文，看是否有分页
                            context = ''.join(lines[max(0, i-5):min(len(lines), i+5)])
                            if 'paginate' not in context.lower() and 'limit' not in context.lower():
                                large_queries.append({
                                    'file': str(file_path.relative_to(PROJECT_ROOT)),
                                    'line': i,
                                    'code': line.strip()
                                })
                except Exception:
                    pass
    
    return large_queries

def find_n_plus_one_queries():
    """查找可能的N+1查询问题"""
    n_plus_one = []
    
    for root, dirs, files in os.walk(APP_ROUTES_DIR):
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    # 查找循环中的查询
                    in_loop = False
                    loop_start = 0
                    
                    for i, line in enumerate(lines, 1):
                        # 检测循环开始
                        if re.match(r'^\s*(for|while)\s+', line):
                            in_loop = True
                            loop_start = i
                        
                        # 检测循环结束
                        if in_loop and line.strip() and not line.strip().startswith('#') and not line.strip().startswith('for') and not line.strip().startswith('while'):
                            indent = len(line) - len(line.lstrip())
                            if indent == 0 or (i > loop_start and indent <= len(lines[loop_start-1]) - len(lines[loop_start-1].lstrip())):
                                in_loop = False
                        
                        # 在循环中查找查询
                        if in_loop and ('.query.' in line or '.filter(' in line or '.get(' in line):
                            if 'joinedload' not in content[max(0, i-20):i+20] and 'selectinload' not in content[max(0, i-20):i+20]:
                                n_plus_one.append({
                                    'file': str(file_path.relative_to(PROJECT_ROOT)),
                                    'line': i,
                                    'code': line.strip()
                                })
                except Exception:
                    pass
    
    return n_plus_one

def main():
    """主函数"""
    print("=" * 60)
    print("API性能分析工具")
    print("=" * 60)
    print()
    
    # 1. 查找缺少分页的接口
    print("1. 查找缺少分页的接口...")
    large_queries = find_large_queries()
    print(f"   找到 {len(large_queries)} 个可能返回大量数据的查询")
    
    # 2. 查找N+1查询问题
    print("2. 查找N+1查询问题...")
    n_plus_one = find_n_plus_one_queries()
    print(f"   找到 {len(n_plus_one)} 个可能的N+1查询")
    
    # 保存结果
    import json
    output_file = PROJECT_ROOT / 'docs' / 'optimization' / 'api_performance_analysis.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        'large_queries': large_queries[:50],  # 只保存前50个
        'n_plus_one_queries': n_plus_one[:50],  # 只保存前50个
        'summary': {
            'total_large_queries': len(large_queries),
            'total_n_plus_one': len(n_plus_one)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 60)
    print("分析完成")
    print("=" * 60)
    print(f"结果已保存到: {output_file}")
    print()
    print("主要问题:")
    print(f"  - 缺少分页的查询: {len(large_queries)} 个")
    print(f"  - 可能的N+1查询: {len(n_plus_one)} 个")
    print()
    print("建议:")
    print("  1. 为返回列表的接口添加分页")
    print("  2. 使用 joinedload 或 selectinload 优化关联查询")
    print("  3. 添加字段筛选，只返回需要的字段")

if __name__ == '__main__':
    main()
