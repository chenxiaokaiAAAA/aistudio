# -*- coding: utf-8 -*-
"""
统计print语句分布
"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DIR = os.path.join(PROJECT_ROOT, 'app')

def count_print_statements():
    """统计print语句"""
    files_with_print = []
    total_count = 0
    
    for root, dirs, files in os.walk(APP_DIR):
        # 跳过缓存目录
        if '__pycache__' in root or '.git' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 统计print语句（排除注释和字符串中的print）
                    matches = re.findall(r'print\s*\(', content)
                    count = len(matches)
                    
                    if count > 0:
                        # 检查是否有logging导入
                        has_logging = 'import logging' in content or 'from logging' in content
                        has_logger = 'logger = logging.getLogger' in content
                        
                        files_with_print.append({
                            'file': filepath.replace(PROJECT_ROOT + os.sep, ''),
                            'count': count,
                            'has_logging': has_logging,
                            'has_logger': has_logger
                        })
                        total_count += count
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    # 按数量排序
    files_with_print.sort(key=lambda x: x['count'], reverse=True)
    
    print(f"\n找到 {len(files_with_print)} 个文件包含 print 语句，共 {total_count} 处\n")
    print("=" * 80)
    
    # 分类显示
    no_logging = [f for f in files_with_print if not f['has_logging']]
    has_logging_no_logger = [f for f in files_with_print if f['has_logging'] and not f['has_logger']]
    ready = [f for f in files_with_print if f['has_logging'] and f['has_logger']]
    
    print(f"\n【需要添加logging导入】({len(no_logging)} 个文件):")
    for f in no_logging[:20]:  # 只显示前20个
        print(f"  {f['count']:3d} - {f['file']}")
    if len(no_logging) > 20:
        print(f"  ... 还有 {len(no_logging) - 20} 个文件")
    
    print(f"\n【已有logging但缺少logger】({len(has_logging_no_logger)} 个文件):")
    for f in has_logging_no_logger[:20]:
        print(f"  {f['count']:3d} - {f['file']}")
    if len(has_logging_no_logger) > 20:
        print(f"  ... 还有 {len(has_logging_no_logger) - 20} 个文件")
    
    print(f"\n【可以直接替换】({len(ready)} 个文件):")
    for f in ready[:30]:
        print(f"  {f['count']:3d} - {f['file']}")
    if len(ready) > 30:
        print(f"  ... 还有 {len(ready) - 30} 个文件")
    
    return files_with_print

if __name__ == '__main__':
    count_print_statements()
