# -*- coding: utf-8 -*-
"""
统计小程序中的console语句
"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MINIPROGRAM_DIR = os.path.join(PROJECT_ROOT, 'aistudio-小程序')

def count_console_statements():
    """统计console语句"""
    files_with_console = []
    total_count = 0
    
    console_types = {
        'log': 0,
        'error': 0,
        'warn': 0,
        'info': 0,
        'debug': 0
    }
    
    for root, dirs, files in os.walk(MINIPROGRAM_DIR):
        # 跳过node_modules
        if 'node_modules' in root:
            continue
        
        for file in files:
            if file.endswith(('.js', '.wxs')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 统计各种console语句
                    log_count = len(re.findall(r'console\.log\s*\(', content))
                    error_count = len(re.findall(r'console\.error\s*\(', content))
                    warn_count = len(re.findall(r'console\.warn\s*\(', content))
                    info_count = len(re.findall(r'console\.info\s*\(', content))
                    debug_count = len(re.findall(r'console\.debug\s*\(', content))
                    
                    total = log_count + error_count + warn_count + info_count + debug_count
                    
                    if total > 0:
                        console_types['log'] += log_count
                        console_types['error'] += error_count
                        console_types['warn'] += warn_count
                        console_types['info'] += info_count
                        console_types['debug'] += debug_count
                        
                        files_with_console.append({
                            'file': filepath.replace(PROJECT_ROOT + os.sep, ''),
                            'log': log_count,
                            'error': error_count,
                            'warn': warn_count,
                            'info': info_count,
                            'debug': debug_count,
                            'total': total
                        })
                        total_count += total
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    # 按数量排序
    files_with_console.sort(key=lambda x: x['total'], reverse=True)
    
    print(f"\n找到 {len(files_with_console)} 个文件包含 console 语句，共 {total_count} 处\n")
    print("=" * 80)
    print("\n按类型统计:")
    print(f"  console.log:   {console_types['log']:4d} 处")
    print(f"  console.error: {console_types['error']:4d} 处")
    print(f"  console.warn:  {console_types['warn']:4d} 处")
    print(f"  console.info:  {console_types['info']:4d} 处")
    print(f"  console.debug: {console_types['debug']:4d} 处")
    print(f"  总计:          {total_count:4d} 处")
    
    print(f"\n【文件列表】(前30个):")
    for f in files_with_console[:30]:
        types = []
        if f['log'] > 0:
            types.append(f"log:{f['log']}")
        if f['error'] > 0:
            types.append(f"error:{f['error']}")
        if f['warn'] > 0:
            types.append(f"warn:{f['warn']}")
        if f['info'] > 0:
            types.append(f"info:{f['info']}")
        if f['debug'] > 0:
            types.append(f"debug:{f['debug']}")
        print(f"  {f['total']:3d} - {f['file']} ({', '.join(types)})")
    
    if len(files_with_console) > 30:
        print(f"  ... 还有 {len(files_with_console) - 30} 个文件")
    
    return files_with_console, console_types

if __name__ == '__main__':
    count_console_statements()
