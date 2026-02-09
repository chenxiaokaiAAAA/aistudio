#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 get_models() 函数使用情况
找出所有需要重构的文件
"""

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_ROUTES_DIR = PROJECT_ROOT / 'app' / 'routes'

def analyze_file(file_path):
    """分析单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有本地定义的 get_models
        has_local_get_models = bool(re.search(r'^def get_models\(', content, re.MULTILINE))
        
        # 检查是否从公共模块导入
        has_import_from_helpers = bool(re.search(
            r'from app\.utils\.admin_helpers import.*get_models', content
        ))
        has_import_from_common = bool(re.search(
            r'from app\.routes\.miniprogram\.common import.*get_models', content
        ))
        
        # 检查是否使用 get_models
        uses_get_models = 'get_models()' in content
        
        return {
            'file': str(file_path.relative_to(PROJECT_ROOT)),
            'has_local_definition': has_local_get_models,
            'has_import_from_helpers': has_import_from_helpers,
            'has_import_from_common': has_import_from_common,
            'uses_get_models': uses_get_models,
            'needs_refactor': has_local_get_models and not (has_import_from_helpers or has_import_from_common)
        }
    except Exception as e:
        return {
            'file': str(file_path.relative_to(PROJECT_ROOT)),
            'error': str(e)
        }

def main():
    """主函数"""
    print("=" * 60)
    print("分析 get_models() 函数使用情况")
    print("=" * 60)
    print()
    
    files_to_analyze = []
    for root, dirs, files in os.walk(APP_ROUTES_DIR):
        # 跳过 __pycache__
        if '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                files_to_analyze.append(Path(root) / file)
    
    results = []
    for file_path in files_to_analyze:
        result = analyze_file(file_path)
        results.append(result)
    
    # 分类统计
    needs_refactor = [r for r in results if r.get('needs_refactor')]
    already_using_helpers = [r for r in results if r.get('has_import_from_helpers')]
    already_using_common = [r for r in results if r.get('has_import_from_common')]
    has_local_but_also_import = [r for r in results if r.get('has_local_definition') and (r.get('has_import_from_helpers') or r.get('has_import_from_common'))]
    
    print("统计结果:")
    print(f"  总文件数: {len(results)}")
    print(f"  需要重构: {len(needs_refactor)}")
    print(f"  已使用 admin_helpers: {len(already_using_helpers)}")
    print(f"  已使用 miniprogram/common: {len(already_using_common)}")
    print(f"  有本地定义但已导入: {len(has_local_but_also_import)}")
    print()
    
    if needs_refactor:
        print("=" * 60)
        print("需要重构的文件:")
        print("=" * 60)
        for i, result in enumerate(needs_refactor, 1):
            print(f"{i}. {result['file']}")
        print()
    
    # 保存结果到文件
    output_file = PROJECT_ROOT / 'docs' / 'refactoring' / 'get_models_analysis.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_files': len(results),
                'needs_refactor': len(needs_refactor),
                'already_using_helpers': len(already_using_helpers),
                'already_using_common': len(already_using_common)
            },
            'files_needing_refactor': [r['file'] for r in needs_refactor],
            'all_results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"详细分析结果已保存到: {output_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()
