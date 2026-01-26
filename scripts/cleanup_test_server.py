# -*- coding: utf-8 -*-
"""
清理 test_server.py 中的已注释代码和多余空行
"""
import re

def cleanup_test_server(input_file, output_file):
    """清理已注释的代码和多余空行"""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    skip_until_next_route = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检查是否是已注释的路由标记
        if re.match(r'^# ⭐.*已迁移|^# ⭐.*已删除|^# ⭐.*已拆分', line):
            # 保留迁移标记注释（但删除后面的函数体）
            cleaned_lines.append(line)
            i += 1
            
            # 跳过所有已注释的路由装饰器和函数体
            # 直到遇到下一个未注释的路由或函数定义
            while i < len(lines):
                next_line = lines[i]
                
                # 如果遇到未注释的路由或函数定义，停止跳过
                if (next_line.strip() and 
                    not next_line.strip().startswith('#') and
                    (next_line.strip().startswith('@app.route') or
                     (next_line.strip().startswith('def ') and not next_line.strip().startswith('def ').startswith('#')) or
                     next_line.strip().startswith('class ') or
                     next_line.strip().startswith('if __name__'))):
                    break
                
                # 如果遇到空行且下一个非空行是未注释的代码，停止跳过
                if not next_line.strip():
                    # 检查后续几行
                    j = i + 1
                    found_non_comment = False
                    while j < len(lines) and j < i + 5:
                        if lines[j].strip() and not lines[j].strip().startswith('#'):
                            if (lines[j].strip().startswith('@app.route') or
                                lines[j].strip().startswith('def ') or
                                lines[j].strip().startswith('class ') or
                                lines[j].strip().startswith('if __name__')):
                                found_non_comment = True
                                break
                        j += 1
                    if found_non_comment:
                        break
                
                # 跳过已注释的代码行
                if next_line.strip().startswith('# @app.route') or next_line.strip().startswith('# @login_required'):
                    i += 1
                    continue
                
                # 如果遇到未注释的代码（不是注释），停止跳过
                if next_line.strip() and not next_line.strip().startswith('#'):
                    # 检查是否是函数体的开始（缩进的内容）
                    if not next_line.strip().startswith('"""') and not next_line.strip().startswith("'''"):
                        # 可能是函数体，继续跳过
                        if next_line.startswith('    ') or next_line.startswith('\t'):
                            i += 1
                            continue
                        else:
                            # 不是函数体，停止跳过
                            break
                
                i += 1
            
            # 添加一个空行分隔
            if cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append('\n')
            continue
        
        # 检查是否是已注释的路由装饰器
        if re.match(r'^# @app\.route', line):
            # 跳过已注释的路由装饰器和后续的已注释函数定义
            i += 1
            while i < len(lines):
                next_line = lines[i]
                # 如果遇到未注释的代码，停止跳过
                if (next_line.strip() and 
                    not next_line.strip().startswith('#') and
                    (next_line.strip().startswith('@app.route') or
                     next_line.strip().startswith('def ') or
                     next_line.strip().startswith('class '))):
                    break
                # 跳过已注释的函数体
                if next_line.strip() and not next_line.strip().startswith('#'):
                    # 检查是否是函数体（有缩进）
                    if next_line.startswith('    ') or next_line.startswith('\t'):
                        i += 1
                        continue
                    else:
                        break
                i += 1
            continue
        
        # 清理多余的空行（连续3个以上的空行只保留2个）
        if not line.strip():
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
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"✅ 清理完成！")
    print(f"   原始行数: {len(lines)}")
    print(f"   清理后行数: {len(cleaned_lines)}")
    print(f"   删除行数: {len(lines) - len(cleaned_lines)}")

if __name__ == '__main__':
    cleanup_test_server('test_server.py', 'test_server_cleaned.py')
    print("\n⚠️  请检查 test_server_cleaned.py，确认无误后替换原文件")
