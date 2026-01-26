# -*- coding: utf-8 -*-
"""
清理 test_server.py 中已注释的代码和多余空行
"""
import re
import os

def cleanup_test_server():
    """清理已注释的代码和多余空行"""
    # 获取脚本所在目录的父目录（AI-studio目录）
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
    skip_function_body = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检查是否是迁移标记
        if re.match(r'^# ⭐.*已迁移|^# ⭐.*已删除|^# ⭐.*已拆分', stripped):
            # 保留迁移标记
            cleaned_lines.append(line)
            i += 1
            skip_function_body = True
            
            # 跳过已注释的路由装饰器和函数体
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # 如果遇到已注释的路由装饰器，跳过
                if next_stripped.startswith('# @app.route') or next_stripped.startswith('# @login_required'):
                    i += 1
                    continue
                
                # 如果遇到未注释的路由或函数定义，停止跳过
                if (next_stripped and 
                    not next_stripped.startswith('#') and
                    (next_stripped.startswith('@app.route') or
                     (next_stripped.startswith('def ') and not next_stripped.startswith('def get_') and not next_stripped.startswith('def check_')) or
                     next_stripped.startswith('class ') or
                     next_stripped.startswith('if __name__'))):
                    skip_function_body = False
                    break
                
                # 如果遇到下一个迁移标记，停止跳过
                if re.match(r'^# ⭐.*已迁移|^# ⭐.*已删除|^# ⭐.*已拆分', next_stripped):
                    skip_function_body = False
                    break
                
                # 跳过函数体（有缩进的代码）
                if next_stripped and not next_stripped.startswith('#'):
                    # 检查是否是函数体（有缩进）
                    if (next_line.startswith('    ') or next_line.startswith('\t')) and not next_stripped.startswith('"""') and not next_stripped.startswith("'''"):
                        i += 1
                        continue
                    # 如果遇到未缩进的代码，可能是下一个函数或路由
                    elif not next_line.startswith(' ') and not next_line.startswith('\t'):
                        skip_function_body = False
                        break
                
                i += 1
            
            # 添加一个空行分隔（如果上一个不是空行）
            if cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append('\n')
            continue
        
        # 如果正在跳过函数体
        if skip_function_body:
            # 检查是否是下一个未注释的路由或函数
            if (stripped and 
                not stripped.startswith('#') and
                (stripped.startswith('@app.route') or
                 (stripped.startswith('def ') and not stripped.startswith('def get_') and not stripped.startswith('def check_')) or
                 stripped.startswith('class ') or
                 stripped.startswith('if __name__'))):
                skip_function_body = False
            else:
                i += 1
                continue
        
        # 检查是否是已注释的路由装饰器（没有迁移标记的）
        if stripped.startswith('# @app.route'):
            # 跳过已注释的路由装饰器和后续的已注释函数定义
            i += 1
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # 如果遇到未注释的代码，停止跳过
                if (next_stripped and 
                    not next_stripped.startswith('#') and
                    (next_stripped.startswith('@app.route') or
                     next_stripped.startswith('def ') or
                     next_stripped.startswith('class '))):
                    break
                
                # 跳过已注释的函数体
                if next_stripped and not next_stripped.startswith('#'):
                    # 检查是否是函数体（有缩进）
                    if next_line.startswith('    ') or next_line.startswith('\t'):
                        i += 1
                        continue
                    else:
                        break
                
                i += 1
            continue
        
        # 清理多余的空行（连续3个以上的空行只保留2个）
        if not stripped:
            empty_count = 1
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                empty_count += 1
                j += 1
            
            if empty_count > 2:
                # 只保留2个空行
                cleaned_lines.append('\n')
                cleaned_lines.append('\n')
                i = j
                continue
        
        cleaned_lines.append(line)
        i += 1
    
    # 写入清理后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"✅ 清理完成！")
    print(f"   原始行数: {original_count}")
    print(f"   清理后行数: {len(cleaned_lines)}")
    print(f"   删除行数: {original_count - len(cleaned_lines)}")
    print(f"   减少比例: {(original_count - len(cleaned_lines)) / original_count * 100:.1f}%")

if __name__ == '__main__':
    cleanup_test_server()
