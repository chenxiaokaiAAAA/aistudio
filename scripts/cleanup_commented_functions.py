# -*- coding: utf-8 -*-
"""
清理 test_server.py 中已注释的函数体
删除所有已注释的路由装饰器和对应的函数体
"""
import re
import os

def cleanup_commented_functions():
    """清理已注释的函数体"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    file_path = os.path.join(parent_dir, 'test_server.py')
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_count = len(lines)
    cleaned_lines = []
    i = 0
    in_commented_function = False
    comment_indent = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检查是否是已注释的路由装饰器
        if re.match(r'^#\s*@app\.route', stripped):
            # 跳过已注释的路由装饰器
            i += 1
            continue
        
        # 检查是否是已注释的函数定义
        if re.match(r'^#\s*def\s+\w+\(', stripped):
            # 开始跳过函数体
            in_commented_function = True
            # 计算注释的缩进（通常是4个空格）
            comment_indent = len(line) - len(line.lstrip())
            i += 1
            continue
        
        # 如果在已注释的函数体中
        if in_commented_function:
            # 检查是否是空行
            if not stripped:
                i += 1
                continue
            
            # 检查是否到达函数结束（下一个未注释的函数定义、路由装饰器或类定义）
            if (not line.startswith('#') and 
                (stripped.startswith('def ') or 
                 stripped.startswith('@app.route') or 
                 stripped.startswith('class ') or
                 stripped.startswith('if __name__') or
                 (stripped.startswith('# ⚠️') and '已迁移' in stripped))):
                in_commented_function = False
                # 不跳过这一行，继续处理
                continue
            
            # 检查是否是下一个迁移标记
            if stripped.startswith('# ⚠️') or stripped.startswith('# ====='):
                in_commented_function = False
                # 保留迁移标记
                cleaned_lines.append(line)
                i += 1
                continue
            
            # 跳过函数体内的所有行（包括注释和代码）
            i += 1
            continue
        
        # 保留其他行
        cleaned_lines.append(line)
        i += 1
    
    # 清理多余的空行（连续3个以上只保留2个）
    final_lines = []
    empty_count = 0
    for line in cleaned_lines:
        if not line.strip():
            empty_count += 1
            if empty_count <= 2:
                final_lines.append(line)
        else:
            empty_count = 0
            final_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    
    removed = original_count - len(final_lines)
    print(f"✅ 清理完成！")
    print(f"   原始行数: {original_count}")
    print(f"   清理后行数: {len(final_lines)}")
    print(f"   删除行数: {removed}")

if __name__ == '__main__':
    cleanup_commented_functions()
